#!/usr/bin/env python3
"""
mempalace_to_mif.py — reference converter: MemPalace -> MIF Container Profile.

Reads a MemPalace palace (ChromaDB on disk) and emits a MIF **Container
Profile** corpus (`*.corpus.json`, see SPECIFICATION.md "Container Profile"),
where each MemPalace drawer becomes a `kind: "memory"` record whose payload is a
valid MIF memory unit.

Typing follows the MemPalace -> MIF AI-Memory mapping
(profiles/ai-memory/MEMPALACE-MAPPING.md): a drawer is a time-anchored record of
something the agent lived through, so it maps to the cognitive-triad
`conceptType: episodic` (the AI-memory `session` reinterpretation). Its wing/room
become the `_episodic/sessions/<wing>` namespace path, and its `filed_at` becomes
`created`.

This converter reads ChromaDB directly (the same access pattern MemPalace uses),
so the `mempalace` runtime is not required. Only `chromadb` is needed — the same
dependency MemPalace itself pulls in.

Usage:
    python -m mempalace_to_mif --palace ~/.mempalace/palace --out palace.corpus.json
    python -m mempalace_to_mif --palace ~/.mempalace/palace --out - | \
        python ../../scripts/okf_validate.py --stdin-corpus

Determinism: a given palace snapshot produces a byte-identical corpus modulo the
`provenance.generatedAtTime` timestamp. Memory `@id`s are UUIDv5-derived from the
MemPalace drawer id under a fixed MemPalace namespace UUID, so they are stable
across re-exports; a drawer whose content carries a MIF/MPF `id` in YAML front
matter keeps that id instead.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

MIF_CONTEXT = "https://mif-spec.dev/schema/context.jsonld"
MIF_VERSION = "1.2.2"
SOURCE_SYSTEM = "mempalace"

# Fixed MemPalace namespace UUID for deterministic UUIDv5 derivation of memory
# ids (matches profiles/ai-memory/MEMPALACE-MAPPING.md).
MEMPALACE_NS = uuid.UUID("b7df7f72-3631-5a73-a4f2-b085a4a3b173")

try:
    import chromadb  # type: ignore
except ImportError:
    chromadb = None  # noqa: N816

_YAML_FRONT_RE = re.compile(r"\A>?\s*---\s*\n(?P<body>.*?)\n>?\s*---\s*\n", re.DOTALL)


def _parse_yaml_front(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Best-effort parse of a leading YAML front-matter block. Returns
    (fields, body). Uses PyYAML if available, else a tiny key: value scan so the
    converter has no hard YAML dependency."""
    m = _YAML_FRONT_RE.match(content or "")
    if not m:
        return None, content or ""
    raw, body = m.group("body"), content[m.end():]
    try:
        import yaml  # type: ignore
        parsed = yaml.safe_load(raw)
        return (parsed if isinstance(parsed, dict) else None), body
    except Exception:
        fields: Dict[str, Any] = {}
        for line in raw.splitlines():
            if ":" in line and not line.lstrip().startswith(("-", "#")):
                k, _, v = line.partition(":")
                fields[k.strip()] = v.strip().strip("'\"")
        return (fields or None), body


def _mif_id(drawer_id: str, yaml_fields: Optional[Dict[str, Any]], restore: bool) -> str:
    """urn:mif:<uuid>. Reuse an original UUID from YAML front matter when present
    and restore=True; otherwise UUIDv5(MemPalace-ns, drawer_id) — deterministic."""
    if restore and yaml_fields:
        oid = str(yaml_fields.get("id") or "")
        try:
            return "urn:mif:" + str(uuid.UUID(oid))
        except (ValueError, AttributeError):
            pass
    return "urn:mif:" + str(uuid.uuid5(MEMPALACE_NS, drawer_id))


def _iso(value: Any) -> Optional[str]:
    if not value:
        return None
    s = str(value)
    # Already ISO-ish; trust it. MemPalace filed_at is ISO 8601.
    return s if "T" in s or "-" in s else None


def _clean_ns_component(text: str) -> str:
    """Coerce a wing/room label into a valid namespace path component
    (^[a-zA-Z0-9_-]+$) by replacing anything else with '-'."""
    c = re.sub(r"[^A-Za-z0-9_-]+", "-", str(text or "").strip()).strip("-")
    return c or "unknown"


def _drawer_to_memory(
    drawer_id: str,
    content: str,
    metadata: Dict[str, Any],
    *,
    restore_original_ids: bool,
) -> Dict[str, Any]:
    """Shape one ChromaDB drawer row into a MIF memory unit (conceptType
    episodic), preserving MemPalace-specific fields under `extensions.mempalace`
    for lossless round-trip."""
    wing = metadata.get("wing", "unknown")
    room = metadata.get("room", "general")

    yaml_fields, body = _parse_yaml_front(content)
    text = body.strip() if yaml_fields else (content or "")
    created = (
        _iso((yaml_fields or {}).get("created"))
        or _iso(metadata.get("filed_at"))
        or datetime(1970, 1, 1, tzinfo=timezone.utc).isoformat()
    )

    memory: Dict[str, Any] = {
        "@context": MIF_CONTEXT,
        "@type": "Memory",
        "@id": _mif_id(drawer_id, yaml_fields, restore_original_ids),
        "conceptType": "episodic",
        "namespace": f"_episodic/sessions/{_clean_ns_component(wing)}",
        "content": text or "(empty drawer)",
        "created": created,
    }
    if (yaml_fields or {}).get("title"):
        memory["title"] = str(yaml_fields["title"])

    tags: List[str] = [_clean_ns_component(room), "mempalace"]
    src = metadata.get("source_file") or metadata.get("source")
    if src:
        tags.append(_clean_ns_component(str(src)))
    memory["tags"] = sorted(set(tags))

    # Lossless MemPalace round-trip slot (provider-specific extensions).
    mp: Dict[str, Any] = {"drawer_id": drawer_id, "wing": wing, "room": room}
    for k in ("source_file", "filed_at", "added_by", "aaak", "palace_coord"):
        v = metadata.get(k)
        if v is not None:
            mp[k] = v
    memory["extensions"] = {"mempalace": mp}
    return memory


def _open_collection(palace_path: Path):
    if chromadb is None:
        raise SystemExit(
            "chromadb is required. Install with:  pip install chromadb\n"
            "(the same dependency MemPalace itself uses.)"
        )
    client = chromadb.PersistentClient(path=str(palace_path))
    for name in ("mempalace_drawers", "palace", "mempalace_palace"):
        try:
            return client.get_collection(name)
        except Exception:
            continue
    colls = client.list_collections()
    if len(colls) == 1:
        return colls[0]
    if not colls:
        raise SystemExit(f"No ChromaDB collections found at {palace_path}")
    names = ", ".join(getattr(c, "name", "?") for c in colls)
    raise SystemExit(
        f"Multiple collections at {palace_path}, none named 'mempalace_drawers'. Found: {names}."
    )


def iter_memory_records(
    palace_path: Path, *, restore_original_ids: bool = True, batch_size: int = 1000
) -> Iterator[Dict[str, Any]]:
    """Stream Container `memory` records from the palace, in ChromaDB order."""
    col = _open_collection(palace_path)
    total = col.count()
    offset = 0
    while offset < total:
        batch = col.get(limit=batch_size, offset=offset, include=["documents", "metadatas"])
        ids = batch.get("ids") or []
        if not ids:
            break
        for did, doc, meta in zip(ids, batch["documents"], batch["metadatas"]):
            yield {
                "kind": "memory",
                "payload": _drawer_to_memory(
                    did, doc or "", dict(meta or {}),
                    restore_original_ids=restore_original_ids,
                ),
            }
        offset += len(ids)


def build_container(
    palace_path: Path, *, source_instance: Optional[str] = None,
    restore_original_ids: bool = True,
) -> Dict[str, Any]:
    """Assemble a MIF Container Profile corpus from a palace snapshot."""
    records = list(iter_memory_records(palace_path, restore_original_ids=restore_original_ids))
    corpus: Dict[str, Any] = {
        "@context": MIF_CONTEXT,
        "@type": "MemoryCorpus",
        "mif_version": MIF_VERSION,
        "records": records,
        "provenance": {
            "@type": "prov:Entity",
            "prov:wasGeneratedBy": {
                "@type": "prov:Activity",
                "prov:used": SOURCE_SYSTEM,
                "prov:generatedAtTime": datetime.now(timezone.utc).isoformat(),
            },
        },
    }
    if source_instance:
        corpus["provenance"]["prov:wasDerivedFrom"] = source_instance
    return corpus


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Convert a MemPalace palace to a MIF Container Profile corpus.")
    ap.add_argument("--palace", required=True, type=Path, help="Path to the MemPalace ChromaDB palace directory.")
    ap.add_argument("--out", default="-", help="Output path, or '-' for stdout (default).")
    ap.add_argument("--source-instance", default=None, help="Optional source instance IRI/label for corpus provenance.")
    ap.add_argument("--no-restore-ids", action="store_true", help="Do not restore original ids from drawer YAML front matter.")
    args = ap.parse_args(argv)

    corpus = build_container(
        args.palace, source_instance=args.source_instance,
        restore_original_ids=not args.no_restore_ids,
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
