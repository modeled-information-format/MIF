#!/usr/bin/env python3
"""
mem0_to_mif.py — reference converter: Mem0 -> MIF Container Profile.

Reads a Mem0 memory store — a Mem0 OSS installation (Qdrant vector store plus
an optional SQLite history sidecar) or a hosted Mem0 Platform tenant
(api.mem0.ai) — and emits a MIF **Container Profile** corpus (`*.corpus.json`,
see SPECIFICATION.md "Container Profile"), where each Mem0 memory becomes a
`kind: "memory"` record whose payload is a valid MIF memory unit.

This converter reads the Qdrant collection directly (the same access pattern
Mem0 itself uses), so the `mem0ai`/`mnemos`/`charon` runtimes are NOT required
for the offline path — only `qdrant-client` is needed, the same dependency Mem0
itself pulls in. The hosted-platform path uses the `mem0ai` SDK if installed.
Nothing here imports a MIF runtime: stdlib + qdrant-client (+ optional mem0ai).

Typing follows the cognitive triad (conceptType enum: semantic|episodic|
procedural):

  * A Mem0 **fact/observation memory** (a Qdrant point in the main collection,
    or a hosted-platform memory row) is durable declarative knowledge the agent
    holds, so it maps to `conceptType: semantic`. Its namespace is
    `_semantic/<tenant-or-collection>`, where the tenant is the flattened Mem0
    `user:agent:run` triple (falling back to the collection name).

  * A Mem0 **history event** (an ADD / UPDATE / DELETE row in Mem0's SQLite
    history sidecar — a time-anchored record of how a memory changed) maps to
    `conceptType: episodic`. Its namespace is `_episodic/history/<tenant>`.

Mem0's created/updated timestamps become the memory `created`. Mem0-specific
fields — Qdrant point id, user/agent/run tenancy, memory_type, hash, score,
custom metadata, and (for history) the old/new memory + event — are preserved
losslessly under the memory's `extensions.mem0` slot for round-trip.

Usage:
    # Offline: default file-mode Qdrant at /tmp/qdrant (Mem0's OSS default)
    python -m mem0_to_mif --out mem0.corpus.json

    # Offline: remote Qdrant, custom collection, with history events
    python -m mem0_to_mif --qdrant-url http://qdrant:6333 --collection mem0 \
        --emit-history --out mem0.corpus.json

    # Hosted Platform via the mem0ai SDK
    python -m mem0_to_mif --platform --api-key-mem0 $MEM0_API_KEY \
        --out mem0.corpus.json

    # Pipe to the validator
    python -m mem0_to_mif --qdrant-path /tmp/qdrant --out - | \
        python ../../scripts/okf_validate.py --stdin-corpus

Determinism: a given Qdrant snapshot + history.db produces a byte-identical
corpus modulo the `provenance.generatedAtTime` timestamp. Memory `@id`s are
UUIDv5-derived from the Mem0 record id under a fixed Mem0 namespace UUID, so
they are stable across re-exports.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

# Shared MIF-facing helpers (all converters reuse these).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _mif_common import (  # noqa: E402
    build_corpus,
    iso,
    mif_memory,
    mif_uuid,
    ns_component,
)

SOURCE_SYSTEM = "mem0"
DEFAULT_COLLECTION = "mem0"
DEFAULT_HISTORY_DB = "~/.mem0/history.db"
DEFAULT_QDRANT_PATH = "/tmp/qdrant"

# Fixed Mem0 namespace UUID for deterministic UUIDv5 derivation of memory ids —
# generated once as UUIDv5(URL-ns, "https://mif-spec.dev/converters/mem0") and
# frozen as a literal so re-exports are stable.
MEM0_NS = uuid.UUID("29ff19ab-347e-513e-8a74-4b92ad97ebd8")

# Optional import — guarded so the offline path doesn't require the hosted SDK
# and importing this module never fails just because qdrant-client is absent.
try:
    from qdrant_client import QdrantClient  # type: ignore
except Exception:  # pragma: no cover - env-dependent
    QdrantClient = None  # type: ignore


# NB: this converter is NOT named mem0.py (unlike the charon adapter), so
# `from mem0 import MemoryClient` resolves cleanly to the installed mem0ai
# package with no self-shadowing gymnastics required.
def _import_mem0_memoryclient():  # pragma: no cover - env-dependent
    try:
        import importlib

        mod = importlib.import_module("mem0")
        return getattr(mod, "MemoryClient", None)
    except Exception:
        return None


__all__ = [
    "SOURCE_SYSTEM",
    "DEFAULT_COLLECTION",
    "DEFAULT_HISTORY_DB",
    "MEM0_NS",
    "point_to_memory",
    "platform_row_to_memory",
    "history_row_to_memory",
    "iter_records",
    "build_container",
    "main",
]


# ─── tenancy ──────────────────────────────────────────────────────────────────


def _composite_tenancy(
    user_id: Optional[str],
    agent_id: Optional[str],
    run_id: Optional[str],
    *,
    fallback: str = "",
) -> str:
    """Mem0's tenancy triple flattened into a single string. Absent axes become
    '-' so the shape is stable; if the whole triple is empty, use `fallback`."""
    if not (user_id or agent_id or run_id):
        return fallback or "-"
    return ":".join((user_id or "-", agent_id or "-", run_id or "-"))


# ─── Qdrant access ────────────────────────────────────────────────────────────


def _open_qdrant(
    *,
    qdrant_path: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    qdrant_host: Optional[str] = None,
    qdrant_port: Optional[int] = None,
    qdrant_api_key: Optional[str] = None,
):
    """Open a QdrantClient in file, URL, or host/port mode.

    Precedence: url > host+port > path. Matches how Mem0's own VectorStoreConfig
    resolves Qdrant connection strings.
    """
    if QdrantClient is None:
        raise SystemExit(
            "qdrant-client is required. Install with:\n"
            "  pip install qdrant-client\n"
            "(the same dependency Mem0 itself uses.)"
        )
    if qdrant_url:
        return QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    if qdrant_host:
        return QdrantClient(host=qdrant_host, port=qdrant_port or 6333, api_key=qdrant_api_key)
    return QdrantClient(path=qdrant_path or DEFAULT_QDRANT_PATH)


def _collection_exists(client, name: str) -> bool:
    try:
        client.get_collection(name)
        return True
    except Exception:
        return False


def _scroll_collection(client, collection: str, *, batch_size: int = 512) -> Iterator[Any]:
    """Stream every point in a Qdrant collection using scroll pagination.

    Yields raw qdrant_client.models.Record (or equivalent) objects.
    """
    offset: Any = None
    while True:
        try:
            points, next_offset = client.scroll(
                collection_name=collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as e:  # pragma: no cover - env-dependent
            raise SystemExit(f"Qdrant scroll failed on collection '{collection}': {e}") from e
        if not points:
            return
        for pt in points:
            yield pt
        if next_offset is None:
            return
        offset = next_offset


# ─── Mem0 record → MIF memory unit ───────────────────────────────────────────


def _semantic_memory(
    *,
    source_id: str,
    content: str,
    tenant: str,
    created: Optional[str],
    updated: Optional[str],
    memory_type: Optional[str],
    mem_hash: Optional[str],
    user_id: Optional[str],
    agent_id: Optional[str],
    run_id: Optional[str],
    score: Optional[float],
    extra: Optional[Dict[str, Any]] = None,
    id_prefix: str = "memory",
) -> Dict[str, Any]:
    """Common shaper for a Mem0 fact/observation -> semantic MIF memory unit."""
    ext: Dict[str, Any] = {
        "source_id": source_id,
        "memory_type": memory_type,
        "hash": mem_hash,
        "user_id": user_id,
        "agent_id": agent_id,
        "run_id": run_id,
    }
    if score is not None:
        ext["score"] = score
    if updated:
        ext["updated"] = updated
    if extra:
        ext["metadata"] = extra
    # Drop keys that are None so the round-trip blob stays tidy.
    ext = {k: v for k, v in ext.items() if v is not None}

    tags: List[str] = ["mem0"]
    if memory_type:
        tags.append(str(memory_type))

    return mif_memory(
        mif_id=mif_uuid(MEM0_NS, f"{id_prefix}:{source_id}"),
        concept_type="semantic",
        content=content,
        namespace=f"_semantic/{ns_component(tenant)}",
        created=iso(created) or iso(updated),
        tags=tags,
        source=SOURCE_SYSTEM,
        extensions=ext,
    )


def point_to_memory(point: Any, *, collection: str = DEFAULT_COLLECTION) -> Dict[str, Any]:
    """Shape one Qdrant main-collection point into a semantic MIF memory unit.

    Accepts either a raw qdrant_client Record (with `.id`/`.payload` attrs) or a
    plain dict shaped like `{"id": ..., "payload": {...}}` (used by the example
    generator and any caller without a live Qdrant)."""
    if isinstance(point, dict):
        pid = str(point.get("id", "") or "")
        payload = dict(point.get("payload") or {})
        score = point.get("score")
    else:
        pid = str(getattr(point, "id", "") or "")
        payload = dict(getattr(point, "payload", {}) or {})
        score = getattr(point, "score", None)

    content = payload.pop("data", "") or ""
    memory_type = payload.pop("memory_type", None)
    created = payload.pop("created_at", None)
    updated = payload.pop("updated_at", None)
    user_id = payload.pop("user_id", None)
    agent_id = payload.pop("agent_id", None)
    run_id = payload.pop("run_id", None)
    mem_hash = payload.pop("hash", None)
    # Anything left is caller-supplied metadata Mem0 round-trips verbatim.
    extra = payload or None

    tenant = _composite_tenancy(user_id, agent_id, run_id, fallback=collection)
    return {
        "kind": "memory",
        "payload": _semantic_memory(
            source_id=pid or f"anon:{uuid.uuid4()}",
            content=content,
            tenant=tenant,
            created=created,
            updated=updated,
            memory_type=memory_type,
            mem_hash=mem_hash,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            score=score,
            extra=extra,
        ),
    }


def platform_row_to_memory(row: Dict[str, Any]) -> Dict[str, Any]:
    """Shape one hosted Mem0 Platform memory row into a semantic MIF memory."""
    pid = str(row.get("id") or "")
    content = row.get("memory") or row.get("data") or ""
    memory_type = row.get("memory_type")
    user_id = row.get("user_id")
    agent_id = row.get("agent_id")
    run_id = row.get("run_id")
    created = row.get("created_at")
    updated = row.get("updated_at")
    score = row.get("score")

    extra: Dict[str, Any] = {"platform": True}
    if row.get("categories") is not None:
        extra["categories"] = row.get("categories")
    if row.get("metadata"):
        extra["metadata"] = row.get("metadata")

    tenant = _composite_tenancy(user_id, agent_id, run_id, fallback="platform")
    return {
        "kind": "memory",
        "payload": _semantic_memory(
            source_id=pid or f"anon:{uuid.uuid4()}",
            content=content,
            tenant=tenant,
            created=created,
            updated=updated,
            memory_type=memory_type,
            mem_hash=row.get("hash"),
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            score=score,
            extra=extra,
        ),
    }


def history_row_to_memory(row: Dict[str, Any]) -> Dict[str, Any]:
    """Shape one Mem0 SQLite history row into an episodic MIF memory unit.

    A history row is a time-anchored ADD/UPDATE/DELETE event over a memory, so
    it is `conceptType: episodic` under `_episodic/history/<tenant>`.
    """
    hid = str(row.get("id") or "")
    mem_id = str(row.get("memory_id") or "")
    op = str(row.get("event") or row.get("action") or "event").lower()
    old_mem = row.get("old_memory")
    new_mem = row.get("new_memory")
    created = row.get("created_at")
    updated = row.get("updated_at")

    snippet = (new_mem or old_mem or "").strip()
    if len(snippet) > 200:
        snippet = snippet[:197] + "..."
    content = f"memory {op}: {snippet}" if snippet else f"memory {op}"

    # History rows carry no tenancy; anchor on the linked memory_id.
    tenant = ns_component(mem_id) if mem_id else "unknown"

    ext: Dict[str, Any] = {
        "history_id": hid,
        "memory_id": mem_id,
        "event": op,
        "old_memory": old_mem,
        "new_memory": new_mem,
        "is_deleted": row.get("is_deleted"),
    }
    ext = {k: v for k, v in ext.items() if v is not None}

    return {
        "kind": "memory",
        "payload": mif_memory(
            mif_id=mif_uuid(MEM0_NS, f"history:{hid}"),
            concept_type="episodic",
            content=content,
            namespace=f"_episodic/history/{tenant}",
            created=iso(created) or iso(updated),
            tags=["mem0", "history", op],
            source=SOURCE_SYSTEM,
            extensions=ext,
        ),
    }


# ─── Hosted Platform path ────────────────────────────────────────────────────


def _iter_platform_rows(api_key: str, *, page_size: int = 100) -> Iterator[Dict[str, Any]]:
    """Iterate memory rows from api.mem0.ai via the mem0ai SDK (paginated)."""
    MemoryClient = _import_mem0_memoryclient()
    if MemoryClient is None:
        raise SystemExit(
            "mem0ai is required for --platform mode. Install with:\n  pip install mem0ai"
        )
    client = MemoryClient(api_key=api_key)
    page = 1
    while True:
        try:
            batch = client.get_all(page=page, page_size=page_size)
        except TypeError:  # older SDK without pagination kwargs
            batch = client.get_all()
        if not batch:
            return
        if isinstance(batch, dict):
            rows = batch.get("results") or batch.get("memories") or []
        else:
            rows = list(batch)
        if not rows:
            return
        for row in rows:
            yield dict(row)
        if len(rows) < page_size:
            return
        page += 1


# ─── SQLite history → episodic memories (opt-in) ─────────────────────────────


def _iter_history_rows(history_db: Path) -> Iterator[Dict[str, Any]]:
    """Yield each row of Mem0's SQLite history sidecar as a plain dict.

    Schema (mem0ai 0.1.x): history(id, memory_id, old_memory, new_memory, event,
    created_at, updated_at, is_deleted, ...). Older builds may lack columns; we
    project whatever `SELECT *` returns.
    """
    if not history_db.exists():
        print(f"  history db not found at {history_db}; skipping history", file=sys.stderr)
        return
    try:
        conn = sqlite3.connect(str(history_db))
    except sqlite3.Error as e:  # pragma: no cover - env-dependent
        print(f"  WARNING opening history db {history_db}: {e}", file=sys.stderr)
        return
    conn.row_factory = sqlite3.Row
    try:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(history)").fetchall()}
        if not cols:
            print(f"  history table missing in {history_db}; skipping", file=sys.stderr)
            return
        for row in conn.execute("SELECT * FROM history").fetchall():
            yield {k: row[k] for k in row.keys()}
    finally:
        conn.close()


# ─── streaming corpus assembly ───────────────────────────────────────────────


def iter_records(
    *,
    platform: bool = False,
    api_key_mem0: Optional[str] = None,
    qdrant_path: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    qdrant_host: Optional[str] = None,
    qdrant_port: Optional[int] = None,
    qdrant_api_key: Optional[str] = None,
    collection: str = DEFAULT_COLLECTION,
    emit_history: bool = False,
    history_db: Optional[Path] = None,
) -> Iterator[Dict[str, Any]]:
    """Stream MIF Container `memory` records from a Mem0 source."""
    if platform:
        if not api_key_mem0:
            raise SystemExit("--platform requires --api-key-mem0")
        for row in _iter_platform_rows(api_key_mem0):
            yield platform_row_to_memory(row)
        return

    client = _open_qdrant(
        qdrant_path=qdrant_path,
        qdrant_url=qdrant_url,
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        qdrant_api_key=qdrant_api_key,
    )
    if not _collection_exists(client, collection):
        raise SystemExit(
            f"Qdrant collection '{collection}' not found. "
            f"Pass --collection to override (default: {DEFAULT_COLLECTION})."
        )

    # 1) Main collection → semantic memory units.
    for pt in _scroll_collection(client, collection):
        yield point_to_memory(pt, collection=collection)

    # 2) SQLite history sidecar → episodic memory units (opt-in).
    if emit_history:
        hdb = history_db or Path(os.path.expanduser(DEFAULT_HISTORY_DB))
        for row in _iter_history_rows(hdb):
            yield history_row_to_memory(row)


def build_container(
    *,
    source_instance: Optional[str] = None,
    platform: bool = False,
    api_key_mem0: Optional[str] = None,
    qdrant_path: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    qdrant_host: Optional[str] = None,
    qdrant_port: Optional[int] = None,
    qdrant_api_key: Optional[str] = None,
    collection: str = DEFAULT_COLLECTION,
    emit_history: bool = False,
    history_db: Optional[Path] = None,
) -> Dict[str, Any]:
    """Assemble a MIF Container Profile corpus from a Mem0 source."""
    records = list(
        iter_records(
            platform=platform,
            api_key_mem0=api_key_mem0,
            qdrant_path=qdrant_path,
            qdrant_url=qdrant_url,
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            qdrant_api_key=qdrant_api_key,
            collection=collection,
            emit_history=emit_history,
            history_db=history_db,
        )
    )
    return build_corpus(records, source_system=SOURCE_SYSTEM, source_instance=source_instance)


# ─── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="mem0_to_mif",
        description="Convert a Mem0 memory store to a MIF Container Profile corpus.",
    )
    # Source selection
    ap.add_argument(
        "--platform",
        action="store_true",
        help="Pull from hosted api.mem0.ai via the mem0ai SDK instead of Qdrant.",
    )
    ap.add_argument(
        "--api-key-mem0", default=None, help="Mem0 Platform API key (required with --platform)."
    )

    # Qdrant connection (offline mode)
    ap.add_argument(
        "--qdrant-path",
        default=None,
        metavar="PATH",
        help=f"File-mode Qdrant directory (default: {DEFAULT_QDRANT_PATH} — Mem0's OSS default).",
    )
    ap.add_argument(
        "--qdrant-url",
        default=None,
        metavar="URL",
        help="HTTP Qdrant endpoint (overrides --qdrant-path).",
    )
    ap.add_argument(
        "--qdrant-host", default=None, metavar="HOST", help="Qdrant host (alternative to --qdrant-url)."
    )
    ap.add_argument(
        "--qdrant-port",
        type=int,
        default=None,
        metavar="PORT",
        help="Qdrant port (default 6333; used with --qdrant-host).",
    )
    ap.add_argument(
        "--qdrant-api-key", default=None, help="Qdrant Cloud API key if the instance is secured."
    )
    ap.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        metavar="NAME",
        help=f"Main collection name (default: {DEFAULT_COLLECTION}).",
    )

    # History sidecar (opt-in → episodic)
    ap.add_argument(
        "--emit-history",
        action="store_true",
        help="Also read Mem0's SQLite history sidecar and emit one episodic "
        "memory per ADD/UPDATE/DELETE event.",
    )
    ap.add_argument(
        "--history-db",
        default=None,
        metavar="PATH",
        help=f"Path to Mem0 history.db (default: {DEFAULT_HISTORY_DB}).",
    )

    # Corpus knobs / output
    ap.add_argument(
        "--source-instance",
        default=None,
        help="Optional source instance IRI/label for corpus provenance (e.g. 'prod-mem0-us-east').",
    )
    ap.add_argument("--out", default="-", help="Output path, or '-' for stdout (default).")

    args = ap.parse_args(argv)

    if args.platform and not args.api_key_mem0:
        print("ERROR: --platform requires --api-key-mem0", file=sys.stderr)
        return 2
    if args.platform and (args.qdrant_url or args.qdrant_host or args.qdrant_path):
        print("WARNING: --platform overrides all --qdrant-* flags", file=sys.stderr)

    history_db = Path(os.path.expanduser(args.history_db)) if args.history_db else None

    corpus = build_container(
        source_instance=args.source_instance,
        platform=args.platform,
        api_key_mem0=args.api_key_mem0,
        qdrant_path=args.qdrant_path,
        qdrant_url=args.qdrant_url,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        qdrant_api_key=args.qdrant_api_key,
        collection=args.collection,
        emit_history=args.emit_history,
        history_db=history_db,
    )

    text = json.dumps(corpus, indent=2, ensure_ascii=False)
    if args.out == "-":
        sys.stdout.write(text + "\n")
    else:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        sys.stderr.write(f"wrote {len(corpus['records'])} records -> {args.out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
