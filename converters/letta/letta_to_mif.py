#!/usr/bin/env python3
"""
letta_to_mif.py — reference converter: Letta (letta-ai/letta, formerly MemGPT)
-> MIF Container Profile.

Reads a Letta deployment and emits a MIF **Container Profile** corpus
(`*.corpus.json`, see SPECIFICATION.md "Container Profile"), where each Letta
memory row becomes a `kind: "memory"` record whose payload is a valid MIF memory
unit.

Letta's memory model is more structured than most agent-memory systems:

    * Core memory blocks (human / persona / custom labels) — in-context,
      character-limited state the agent edits with its `core_memory_*` tools.
      These are decontextualized agent knowledge (who the user is, who the agent
      is) -> conceptType "semantic".
    * Archival passages — long-term vector-retrieved text, scoped by archive_id.
      Also decontextualized knowledge the agent retrieves on demand ->
      conceptType "semantic".
    * Recall / message history — every turn of every conversation, ordered by
      agent_id + sequence_id. This is the time-ordered record of what the agent
      lived through -> conceptType "episodic".
    * Agent state — the `agents` row (system prompt, llm_config, tool_rules).
      An agent is a *container*, not a memory; agent rows are skipped and the
      agent id is folded into the namespace path of the memories they own.

conceptType mapping (enum is exactly semantic | episodic | procedural):

    archival passage   -> semantic   namespace _semantic/archival/<agent>
    core memory block  -> semantic   namespace _semantic/blocks/<agent>
    recall message     -> episodic   namespace _episodic/messages/<agent>
    agent state        -> (skipped; agent id folded into namespace)

Letta-specific fields (row id, agent id, block label, message role, character
limits, tool calls, etc.) are preserved under `extensions.letta.*` for a
lossless reverse conversion (except embeddings — an importer regenerates those).
`created_at` on each row maps to MIF `created`.

Like the source CHARON adapter, this converter reads Letta with only the Python
standard library (sqlite3 + urllib): either the on-disk SQLite metadata DB
(default ~/.letta/sqlite.db) or a running Letta server's REST API, chosen with
--mode {sqlite,server,auto}. It does not import `letta`, `mnemos`, or `charon`,
and it does not require the MIF runtime.

Usage:
    python -m letta_to_mif --mode sqlite --db ~/.letta/sqlite.db \
        --out letta.corpus.json
    python -m letta_to_mif --mode server --base http://localhost:8283 \
        --letta-token $LETTA_KEY --out letta.corpus.json
    python -m letta_to_mif --mode auto --db ~/.letta/sqlite.db --out -

Determinism: a given Letta snapshot produces a byte-identical corpus modulo the
`provenance.generatedAtTime` timestamp. Memory `@id`s are UUIDv5-derived from the
Letta row id under a fixed Letta namespace UUID, so they are stable across
re-exports.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# Shared MIF-facing helpers (converters/_mif_common.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _mif_common import (  # noqa: E402
    build_corpus,
    iso,
    mif_memory,
    mif_uuid,
    ns_component,
)

SOURCE_SYSTEM = "letta"

# Fixed Letta namespace UUID for deterministic UUIDv5 derivation of memory ids.
LETTA_NS = uuid.UUID("6f2d1c8e-4b3a-5d9f-8e12-7a4b0c1d2e3f")

DEFAULT_SQLITE_PATH = "~/.letta/sqlite.db"
DEFAULT_SERVER_BASE = "http://localhost:8283"

# Recall (message log) is opt-in — it can dwarf everything else on a chatty
# agent. archival + core are the durable memory surfaces.
ALL_KINDS = ("archival", "core", "recall")
DEFAULT_KINDS = ("archival", "core")


# ─── SQLite read path ───────────────────────────────────────────────────────


def _open_sqlite(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(
            f"Letta SQLite DB not found at {db_path}. "
            f"Default is ~/.letta/sqlite.db; override with --db or use --mode server."
        )
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )


_SQL_ARCHIVAL = """
SELECT id, text, archive_id, organization_id, metadata_, tags,
       created_at, updated_at
  FROM archival_passages
 WHERE COALESCE(is_deleted, 0) = 0
 ORDER BY created_at, id
"""

# Left-join blocks_agents so unattached blocks (templates) still emit.
_SQL_BLOCKS = """
SELECT b.id, b.label, b.value, b."limit" AS char_limit,
       b.description, b.template_name, b.is_template, b.read_only,
       b.metadata_, b.organization_id, b.project_id,
       b.created_at, b.updated_at, ba.agent_id
  FROM block b
  LEFT JOIN blocks_agents ba ON ba.block_id = b.id
 ORDER BY b.created_at, b.id
"""

_SQL_MESSAGES = """
SELECT id, agent_id, role, text, content, model, name,
       tool_calls, tool_call_id, tool_returns, step_id, run_id,
       conversation_id, sequence_id, sender_id, group_id,
       organization_id, created_at, updated_at
  FROM messages
 ORDER BY agent_id, sequence_id
"""


def _sqlite_iter(
    conn: sqlite3.Connection, table: str, sql: str, normalize
) -> Iterator[Dict[str, Any]]:
    if not _table_exists(conn, table):
        return
    for row in conn.execute(sql):
        yield normalize(dict(row))


# ─── Server (REST) read path ────────────────────────────────────────────────


class _LettaClient:
    """Minimal Letta REST client. Letta uses optional Bearer auth
    (LETTA_SERVER_PASSWORD) plus an optional X-Organization header."""

    def __init__(
        self, base: str, token: Optional[str] = None, org: Optional[str] = None
    ):
        self.base = base.rstrip("/")
        self.token = token
        self.org = org

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.org:
            headers["X-Organization"] = self.org
        # Restrict to http(s): `url` derives from the operator-supplied Letta
        # server base (CLI --base), but guard against file://, ftp://, etc. so a
        # misconfigured base cannot turn this GET into an arbitrary-file read.
        if urllib.parse.urlparse(url).scheme not in ("http", "https"):
            raise SystemExit(f"refusing non-http(s) Letta URL: {url!r}")
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected -- url is an
            # operator-provided Letta server endpoint, scheme-restricted to http(s) just above.
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            raise SystemExit(f"Letta GET {path} -> HTTP {e.code}: {body}")

    def list_agents(self, limit: int = 500) -> List[Dict[str, Any]]:
        return self._get("/v1/agents", {"limit": limit}) or []

    def list_blocks(self, limit: int = 500) -> List[Dict[str, Any]]:
        return self._get("/v1/blocks", {"limit": limit}) or []

    def agent_archival(
        self, agent_id: str, limit: int = 1000
    ) -> List[Dict[str, Any]]:
        return (
            self._get(f"/v1/agents/{agent_id}/archival-memory", {"limit": limit})
            or []
        )

    def agent_messages(
        self, agent_id: str, limit: int = 2000
    ) -> List[Dict[str, Any]]:
        return (
            self._get(f"/v1/agents/{agent_id}/messages", {"limit": limit}) or []
        )


def _server_iter_all(
    client: _LettaClient, include: Tuple[str, ...]
) -> Iterator[Dict[str, Any]]:
    agents = client.list_agents()
    if "core" in include:
        seen: set = set()
        for b in client.list_blocks():
            if b.get("id") in seen:
                continue
            seen.add(b.get("id"))
            yield _normalize_block(b)
    if "archival" in include:
        for a in agents:
            for p in client.agent_archival(a["id"]):
                # Server passages don't always carry archive_id; fold in agent.
                p.setdefault("agent_id", a["id"])
                yield _normalize_passage(p)
    if "recall" in include:
        for a in agents:
            for m in client.agent_messages(a["id"]):
                m.setdefault("agent_id", a["id"])
                yield _normalize_message(m)


# ─── Normalization: Letta row -> MIF memory record ──────────────────────────


def _coerce_json(raw: Any) -> Any:
    """SQLite columns often store JSON as TEXT. Decode defensively."""
    if raw is None or not isinstance(raw, (str, bytes)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return raw


def _record(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"kind": "memory", "payload": payload}


def _normalize_passage(row: Dict[str, Any]) -> Dict[str, Any]:
    """Archival passage -> semantic MIF memory.

    Decontextualized long-term knowledge the agent retrieves on demand."""
    meta = _coerce_json(row.get("metadata_")) or {}
    tags_raw = _coerce_json(row.get("tags")) or []
    archive_id = row.get("archive_id")
    agent_id = row.get("agent_id")
    row_id = row.get("id") or f"letta-passage-{id(row)}"
    ns_agent = ns_component(agent_id or archive_id or "unknown")

    ext = {
        "kind": "archival_passage",
        "passage_id": row.get("id"),
        "archive_id": archive_id,
        "agent_id": agent_id,
        "organization_id": row.get("organization_id"),
        "native_metadata": meta,
        "created_at": iso(row.get("created_at")),
        "updated_at": iso(row.get("updated_at")),
    }
    tags = ["letta", "archival"]
    if isinstance(tags_raw, list):
        tags.extend(str(t) for t in tags_raw)

    payload = mif_memory(
        mif_id=mif_uuid(LETTA_NS, f"passage:{row_id}"),
        concept_type="semantic",
        content=row.get("text") or "",
        namespace=f"_semantic/archival/{ns_agent}",
        created=iso(row.get("created_at")),
        tags=tags,
        source=SOURCE_SYSTEM,
        extensions=ext,
    )
    return _record(payload)


def _normalize_block(row: Dict[str, Any]) -> Dict[str, Any]:
    """Core memory block -> semantic MIF memory.

    The label (human / persona / custom) makes a block meaningful; surface it as
    a tag and preserve it under extensions."""
    label = row.get("label") or "block"
    meta = _coerce_json(row.get("metadata_")) or {}
    block_id = row.get("id") or f"letta-block-{label}"
    agent_id = row.get("agent_id")
    ns_agent = ns_component(agent_id or "unattached")
    # Shared blocks with multiple agent attachments: derive a stable per-pairing
    # id so each (block, agent) emits distinctly.
    rec_id = f"{block_id}@{agent_id}" if agent_id else block_id

    ext = {
        "kind": "core_block",
        "block_id": block_id,
        "label": label,
        "char_limit": row.get("char_limit") or row.get("limit"),
        "template_name": row.get("template_name"),
        "is_template": bool(row.get("is_template")),
        "read_only": bool(row.get("read_only")),
        "description": row.get("description"),
        "agent_id": agent_id,
        "organization_id": row.get("organization_id"),
        "project_id": row.get("project_id"),
        "native_metadata": meta,
        "created_at": iso(row.get("created_at")),
        "updated_at": iso(row.get("updated_at")),
    }
    payload = mif_memory(
        mif_id=mif_uuid(LETTA_NS, f"block:{rec_id}"),
        concept_type="semantic",
        content=row.get("value") or "",
        namespace=f"_semantic/blocks/{ns_agent}",
        created=iso(row.get("created_at")),
        title=str(label),
        tags=["letta", "core-block", ns_component(label)],
        source=SOURCE_SYSTEM,
        extensions=ext,
    )
    return _record(payload)


def _normalize_message(row: Dict[str, Any]) -> Dict[str, Any]:
    """Recall message -> episodic MIF memory (session turn).

    Time-ordered record of a conversation the agent lived. Letta stores either
    plain text or content=[{type, text}, ...]; flatten for content."""
    content_parts = _coerce_json(row.get("content"))
    text = row.get("text")
    if not text and isinstance(content_parts, list):
        text = "\n".join(
            p.get("text") or ""
            for p in content_parts
            if isinstance(p, dict) and p.get("type") == "text"
        ).strip()
    agent_id = row.get("agent_id")
    ns_agent = ns_component(agent_id or "unknown")
    row_id = row.get("id") or f"letta-msg-{row.get('sequence_id')}"

    ext = {
        "kind": "recall_message",
        "message_id": row.get("id"),
        "agent_id": agent_id,
        "role": row.get("role"),
        "model": row.get("model"),
        "name": row.get("name"),
        "sequence_id": row.get("sequence_id"),
        "conversation_id": row.get("conversation_id"),
        "step_id": row.get("step_id"),
        "run_id": row.get("run_id"),
        "sender_id": row.get("sender_id"),
        "group_id": row.get("group_id"),
        "tool_calls": _coerce_json(row.get("tool_calls")),
        "tool_call_id": row.get("tool_call_id"),
        "tool_returns": _coerce_json(row.get("tool_returns")),
        "content_parts": content_parts
        if isinstance(content_parts, list)
        else None,
        "organization_id": row.get("organization_id"),
        "created_at": iso(row.get("created_at")),
        "updated_at": iso(row.get("updated_at")),
    }
    tags = ["letta", "message"]
    if row.get("role"):
        tags.append(ns_component(str(row.get("role"))))

    payload = mif_memory(
        mif_id=mif_uuid(LETTA_NS, f"message:{row_id}"),
        concept_type="episodic",
        content=text or "",
        namespace=f"_episodic/messages/{ns_agent}",
        created=iso(row.get("created_at")),
        tags=tags,
        source=SOURCE_SYSTEM,
        extensions=ext,
    )
    return _record(payload)


# ─── Streaming corpus assembly ──────────────────────────────────────────────


def iter_memory_records(
    *,
    mode: str,
    db_path: Optional[Path] = None,
    base: Optional[str] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    include: Tuple[str, ...] = DEFAULT_KINDS,
) -> Iterator[Dict[str, Any]]:
    """Stream Container `memory` records from either a SQLite DB or a live
    Letta server. Agent rows are containers, not memories, and are skipped."""
    if mode == "sqlite":
        if not db_path:
            raise SystemExit("--mode sqlite requires --db PATH")
        conn = _open_sqlite(db_path)
        try:
            if "core" in include:
                yield from _sqlite_iter(conn, "block", _SQL_BLOCKS, _normalize_block)
            if "archival" in include:
                yield from _sqlite_iter(
                    conn, "archival_passages", _SQL_ARCHIVAL, _normalize_passage
                )
            if "recall" in include:
                yield from _sqlite_iter(
                    conn, "messages", _SQL_MESSAGES, _normalize_message
                )
        finally:
            conn.close()
    elif mode == "server":
        if not base:
            raise SystemExit("--mode server requires --base URL")
        yield from _server_iter_all(
            _LettaClient(base, token=token, org=org), include
        )
    else:
        raise SystemExit(f"unknown mode: {mode!r} (expected sqlite/server)")


def _resolve_mode(mode: str, db_path: Optional[Path], base: Optional[str]) -> str:
    """Resolve 'auto' into a concrete mode."""
    if mode != "auto":
        return mode
    if db_path and db_path.exists():
        return "sqlite"
    if base:
        return "server"
    default = Path(os.path.expanduser(DEFAULT_SQLITE_PATH))
    if default.exists():
        return "sqlite"
    raise SystemExit(
        "--mode auto: couldn't find a Letta source. "
        f"Pass --db (default {DEFAULT_SQLITE_PATH}) or --base URL."
    )


def build_container(
    *,
    mode: str,
    db_path: Optional[Path] = None,
    base: Optional[str] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    include: Tuple[str, ...] = DEFAULT_KINDS,
    source_instance: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble a MIF Container Profile corpus from a Letta snapshot."""
    records = list(
        iter_memory_records(
            mode=mode,
            db_path=db_path,
            base=base,
            token=token,
            org=org,
            include=include,
        )
    )
    return build_corpus(
        records,
        source_system=SOURCE_SYSTEM,
        source_instance=source_instance
        or (str(db_path) if mode == "sqlite" else base),
    )


# ─── CLI ────────────────────────────────────────────────────────────────────


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="letta_to_mif",
        description=(
            "Convert a Letta deployment to a MIF Container Profile corpus. "
            "Reads archival passages, core memory blocks, and (opt-in) recall "
            "messages from a Letta SQLite DB or live server."
        ),
    )
    ap.add_argument(
        "--mode",
        choices=("auto", "sqlite", "server"),
        default="auto",
        help="Read from the SQLite DB or a running server "
        "(default: auto — prefers SQLite if present).",
    )
    ap.add_argument(
        "--db",
        default=None,
        metavar="PATH",
        help=f"Path to Letta's SQLite DB (default: {DEFAULT_SQLITE_PATH}).",
    )
    ap.add_argument(
        "--base",
        default=None,
        metavar="URL",
        help=f"Letta server base URL (default: {DEFAULT_SERVER_BASE}).",
    )
    ap.add_argument(
        "--letta-token",
        default=None,
        help="Bearer token for Letta server auth (LETTA_SERVER_PASSWORD).",
    )
    ap.add_argument(
        "--letta-org", default=None, help="Optional X-Organization header."
    )
    ap.add_argument(
        "--include",
        default=",".join(DEFAULT_KINDS),
        help=f"Comma-separated kinds ({'/'.join(ALL_KINDS)}, or 'all'). "
        f"Default: {','.join(DEFAULT_KINDS)} (recall excluded — large).",
    )
    ap.add_argument(
        "--out", default="-", help="Output path, or '-' for stdout (default)."
    )
    ap.add_argument(
        "--source-instance",
        default=None,
        help="Optional source instance IRI/label for corpus provenance.",
    )
    args = ap.parse_args(argv)

    if args.include.strip().lower() == "all":
        include = ALL_KINDS
    else:
        include = tuple(k.strip() for k in args.include.split(",") if k.strip())
        bad = [k for k in include if k not in ALL_KINDS]
        if bad:
            print(
                f"ERROR: unknown --include kinds: {bad}. "
                f"Valid: {', '.join(ALL_KINDS)} or 'all'.",
                file=sys.stderr,
            )
            return 2

    db_path = Path(os.path.expanduser(args.db or DEFAULT_SQLITE_PATH)).resolve()
    base = args.base or DEFAULT_SERVER_BASE
    mode = _resolve_mode(args.mode, db_path, args.base)
    print(
        f"letta_to_mif: mode={mode} include={','.join(include)}", file=sys.stderr
    )

    corpus = build_container(
        mode=mode,
        db_path=db_path if mode == "sqlite" else None,
        base=base if mode == "server" else None,
        token=args.letta_token,
        org=args.letta_org,
        include=include,
        source_instance=args.source_instance,
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
