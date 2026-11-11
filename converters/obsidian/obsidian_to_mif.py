#!/usr/bin/env python3
"""
obsidian_to_mif.py — reference converter: an Obsidian vault -> MIF Container Profile.

Reads an Obsidian vault (a directory tree of Markdown notes with optional YAML
frontmatter and `[[wikilinks]]`) and emits a MIF Container Profile corpus
(`*.corpus.json`): each note becomes a `kind: "memory"` record whose payload is a
valid MIF memory unit.

This is a **converter** (Obsidian -> MIF), not an Obsidian *profile*: MIF's core
is deliberately vendor-neutral (see adr/ADR-017-revert-obsidian-compatibility.md),
so Obsidian-specific conventions live only in the source vault and are preserved
under each memory's `extensions.obsidian` for round-trip — they never leak into
the MIF unit's required shape.

Typing (cognitive triad — enum semantic|episodic|procedural):
    * A note in a journal/daily-notes folder (or a date-named note) is a
      time-anchored record -> conceptType `episodic` (namespace _episodic/journal/…).
    * Any other note is decontextualized knowledge the author keeps -> `semantic`
      (namespace _semantic/<folder-path>).
    * `[[wikilinks]]` become MIF `relationships[]` (type `links-to`, target the
      linked note's urn:mif id) so the vault's link graph survives.

No external dependency — a vault is plain files. PyYAML is used for frontmatter if
present, else a small key: value scan (no hard YAML dependency).

Usage:
    python obsidian_to_mif.py --vault ~/MyVault --out vault.corpus.json
    python obsidian_to_mif.py --vault ~/MyVault --out - | python ../../scripts/okf_validate.py --stdin-corpus
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _mif_common import (  # noqa: E402
    MIF_CONTEXT,
    build_corpus,
    iso,
    mif_memory,
    mif_uuid,
    ns_component,
)

# Fixed Obsidian namespace UUID for deterministic UUIDv5 note ids.
OBSIDIAN_NS = uuid.UUID("2f9c7a54-6b1d-5e83-9a20-3c8f4d6e1b7a")
SOURCE_SYSTEM = "obsidian"

_FRONT_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
_INLINE_TAG_RE = re.compile(r"(?:^|\s)#([A-Za-z0-9_][A-Za-z0-9_/-]*)")
_DATE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
_JOURNAL_DIRS = ("daily", "daily notes", "daily-notes", "journal", "journals", "diary")


def _parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    m = _FRONT_RE.match(text or "")
    if not m:
        return {}, text or ""
    raw, body = m.group("body"), text[m.end():]
    try:
        import yaml  # type: ignore
        parsed = yaml.safe_load(raw)
        return (parsed if isinstance(parsed, dict) else {}), body
    except Exception:
        fields: Dict[str, Any] = {}
        for line in raw.splitlines():
            if ":" in line and not line.lstrip().startswith(("-", "#")):
                k, _, v = line.partition(":")
                fields[k.strip()] = v.strip().strip("'\"")
        return fields, body


def _jsonable(obj: Any) -> Any:
    """Recursively coerce YAML-parsed values (e.g. date/datetime) into
    JSON-serializable primitives so the frontmatter round-trip blob is safe."""
    import datetime as _dt
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [t.strip() for t in re.split(r"[,\s]+", value) if t.strip()]
    if isinstance(value, (list, tuple)):
        return [str(t).strip() for t in value if str(t).strip()]
    return [str(value)]


def _is_episodic(rel_path: Path) -> bool:
    parts = [p.lower() for p in rel_path.parts[:-1]]
    if any(d in _JOURNAL_DIRS for d in parts):
        return True
    return bool(_DATE_NAME_RE.match(rel_path.stem))


def _note_to_memory(vault: Path, note: Path) -> Dict[str, Any]:
    rel = note.relative_to(vault)
    text = note.read_text(encoding="utf-8", errors="replace")
    fm, body = _parse_frontmatter(text)

    episodic = _is_episodic(rel)
    concept = "episodic" if episodic else "semantic"

    # namespace from the folder path (posix, cleaned per component)
    folder = rel.parent
    comps = [ns_component(c) for c in folder.parts] if folder.parts else []
    base = "_episodic/journal" if episodic else "_semantic"
    namespace = "/".join([base, *comps]) if comps else base

    created = iso(fm.get("created") or fm.get("date")) or _mtime_iso(note)
    title = str(fm.get("title") or rel.stem)

    tags = _as_list(fm.get("tags")) + _INLINE_TAG_RE.findall(body)
    tags.append("obsidian")

    # [[wikilinks]] -> relationships (target = urn of the linked note)
    rels: List[Dict[str, Any]] = []
    seen = set()
    for target_name in _WIKILINK_RE.findall(body):
        tn = target_name.strip()
        if not tn or tn in seen:
            continue
        seen.add(tn)
        rels.append({
            "type": "links-to",
            "target": "urn:mif:" + str(uuid.uuid5(OBSIDIAN_NS, tn)),
            "metadata": {"obsidian": {"wikilink": tn}},
        })

    mem = mif_memory(
        mif_id=mif_uuid(OBSIDIAN_NS, rel.as_posix(), restore=fm.get("id") or fm.get("uid")),
        concept_type=concept,
        content=body,
        namespace=namespace,
        created=created,
        title=title,
        tags=tags,
        relationships=rels or None,
        source=SOURCE_SYSTEM,
        extensions={
            "vault_path": rel.as_posix(),
            "frontmatter": _jsonable(fm) or None,
            "aliases": _as_list(fm.get("aliases")) or None,
        },
    )
    return {"kind": "memory", "payload": mem}


def _mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        return datetime(1970, 1, 1, tzinfo=timezone.utc).isoformat()


def iter_memory_records(vault: Path) -> Iterator[Dict[str, Any]]:
    """Stream Container `memory` records for every .md note in the vault
    (skipping the .obsidian config dir and .trash)."""
    for note in sorted(vault.rglob("*.md")):
        parts = {p.lower() for p in note.relative_to(vault).parts}
        if ".obsidian" in parts or ".trash" in parts:
            continue
        yield _note_to_memory(vault, note)


def build_container(vault: Path, *, source_instance: Optional[str] = None) -> Dict[str, Any]:
    records = list(iter_memory_records(vault))
    return build_corpus(records, source_system=SOURCE_SYSTEM, source_instance=source_instance)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Convert an Obsidian vault to a MIF Container Profile corpus.")
    ap.add_argument("--vault", required=True, type=Path, help="Path to the Obsidian vault directory.")
    ap.add_argument("--out", default="-", help="Output path, or '-' for stdout (default).")
    ap.add_argument("--source-instance", default=None, help="Optional source instance label for corpus provenance.")
    args = ap.parse_args(argv)
    if not args.vault.is_dir():
        raise SystemExit(f"vault not found: {args.vault}")
    corpus = build_container(args.vault, source_instance=args.source_instance)
    text = json.dumps(corpus, indent=2, ensure_ascii=False)
    if args.out == "-":
        sys.stdout.write(text + "\n")
    else:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        sys.stderr.write(f"wrote {len(corpus['records'])} records -> {args.out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
