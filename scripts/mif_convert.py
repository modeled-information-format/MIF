#!/usr/bin/env python3
"""MIF v1.0 Markdown <-> JSON-LD converter (markdown is canonical).

Per the v1.0 specification:

- The ``.md`` concept file is the source of truth (Invariant 2).
- JSON-LD is a *derived* projection, reproducible by running this converter
  (Invariant 2) and lossless on a ``markdown -> json-ld -> markdown`` round
  trip for all conformance-level data (Invariant 4).

A v1.0 concept file has YAML frontmatter with at least ``type``, ``id`` and
``created`` and a markdown body. Typed relationships are authoritative in the
frontmatter ``relationships`` array and mirrored in the body as OKF-legible
``## Relationships`` markdown links (Invariant 3); see ``okf_validate.py`` for
the synchronization check.

Usage::

    python mif_convert.py to-jsonld <concept.md> [out.jsonld]
    python mif_convert.py to-markdown <concept.jsonld> [out.md]
    python mif_convert.py roundtrip <bundle-dir> [bundle-dir ...]
    python mif_convert.py emit-jsonld <bundle-dir> --out-dir jsonld
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("Error: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

CONTEXT_URL = "https://mif-spec.dev/schema/context.jsonld"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
RESERVED_FILENAMES = {"index.md", "log.md"}

# Canonical frontmatter key order for deterministic, lossless serialization.
FRONTMATTER_ORDER = [
    "id",
    "type",
    "memoryType",
    "created",
    "modified",
    "namespace",
    "title",
    "summary",
    "properties",
    "compressedAt",
    "tags",
    "aliases",
    "temporal",
    "provenance",
    "embedding",
    "relationships",
    "citations",
    "documents",
    "entities",
    "ontology",
    "entity",
    "blocks",
    "extensions",
]


def stringify_datetimes(obj: Any) -> Any:
    """Recursively convert datetime/date objects to ISO 8601 strings."""
    if isinstance(obj, datetime):
        return obj.isoformat().replace("+00:00", "Z")
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: stringify_datetimes(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [stringify_datetimes(item) for item in obj]
    return obj


def parse_markdown(md_text: str) -> tuple[dict, str]:
    """Split a concept file into (frontmatter dict, body str)."""
    match = FRONTMATTER_RE.match(md_text)
    if not match:
        raise ValueError("No YAML frontmatter found")
    frontmatter = yaml.safe_load(match.group(1)) or {}
    frontmatter = stringify_datetimes(frontmatter)
    body = match.group(2)
    return frontmatter, body


def _ordered_frontmatter(frontmatter: dict) -> dict:
    """Return frontmatter with canonical key ordering (extras appended)."""
    ordered: dict[str, Any] = {}
    for key in FRONTMATTER_ORDER:
        if key in frontmatter:
            ordered[key] = frontmatter[key]
    for key, value in frontmatter.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def serialize_markdown(frontmatter: dict, body: str) -> str:
    """Serialize frontmatter + body back into a concept file (canonical form)."""
    fm = _ordered_frontmatter(stringify_datetimes(frontmatter))
    yaml_text = yaml.safe_dump(
        fm, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).strip()
    body = body.lstrip("\n").rstrip() + "\n"
    return f"---\n{yaml_text}\n---\n\n{body}"


def md_to_jsonld(frontmatter: dict, body: str) -> dict:
    """Project frontmatter + body into a derived JSON-LD document."""
    fm = stringify_datetimes(frontmatter)
    jsonld: dict[str, Any] = {
        "@context": CONTEXT_URL,
        "@type": "Concept",
    }
    if "id" in fm:
        jsonld["@id"] = f"urn:mif:{fm['id']}"
    # type is OKF required + MIF base type; surfaced as conceptType.
    if "type" in fm:
        jsonld["conceptType"] = fm["type"]

    passthrough = [
        "memoryType",
        "created",
        "modified",
        "namespace",
        "title",
        "summary",
        "properties",
        "compressedAt",
        "tags",
        "aliases",
        "temporal",
        "provenance",
        "embedding",
        "relationships",
        "citations",
        "documents",
        "entities",
        "ontology",
        "entity",
        "blocks",
        "extensions",
    ]
    for key in passthrough:
        if key in fm:
            jsonld[key] = fm[key]

    # OKF-recommended mirror fields.
    jsonld["timestamp"] = fm.get("modified", fm.get("created"))
    if "summary" in fm:
        jsonld["description"] = fm["summary"]

    jsonld["content"] = body.strip()
    return jsonld


def jsonld_to_md(jsonld: dict) -> tuple[dict, str]:
    """Recover (frontmatter, body) from a derived JSON-LD document."""
    fm: dict[str, Any] = {}
    if "@id" in jsonld:
        fm["id"] = jsonld["@id"].removeprefix("urn:mif:")
    if "conceptType" in jsonld:
        fm["type"] = jsonld["conceptType"]

    passthrough = [
        "memoryType",
        "created",
        "modified",
        "namespace",
        "title",
        "summary",
        "properties",
        "compressedAt",
        "tags",
        "aliases",
        "temporal",
        "provenance",
        "embedding",
        "relationships",
        "citations",
        "documents",
        "entities",
        "ontology",
        "entity",
        "blocks",
        "extensions",
    ]
    for key in passthrough:
        if key in jsonld:
            fm[key] = jsonld[key]

    body = jsonld.get("content", "")
    return fm, body


def normalize(md_text: str) -> str:
    """Normalize a concept file for round-trip comparison."""
    frontmatter, body = parse_markdown(md_text)
    return serialize_markdown(frontmatter, body)


def roundtrip_file(md_path: Path) -> str | None:
    """Return an error string if md -> jsonld -> md is not lossless, else None."""
    original = md_path.read_text()
    frontmatter, body = parse_markdown(original)
    jsonld = md_to_jsonld(frontmatter, body)
    # Serialize and re-parse the JSON-LD to mimic a real on-disk projection.
    jsonld = json.loads(json.dumps(jsonld))
    fm2, body2 = jsonld_to_md(jsonld)
    recovered = serialize_markdown(fm2, body2)
    expected = serialize_markdown(frontmatter, body)
    if recovered != expected:
        return f"round-trip drift in {md_path}"
    return None


def iter_concepts(bundle: Path):
    """Yield concept ``.md`` files in a bundle (excluding reserved filenames)."""
    for md_path in sorted(bundle.rglob("*.md")):
        if md_path.name in RESERVED_FILENAMES:
            continue
        yield md_path


def cmd_roundtrip(bundles: list[Path]) -> int:
    total = 0
    errors: list[str] = []
    for bundle in bundles:
        for md_path in iter_concepts(bundle):
            total += 1
            err = roundtrip_file(md_path)
            if err:
                errors.append(err)
    print(f"Round-trip: tested {total} concept(s) across {len(bundles)} bundle(s)")
    if errors:
        print("ROUND-TRIP FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Round-trip lossless: PASS")
    return 0


def cmd_to_jsonld(src: Path, out: Path | None) -> int:
    frontmatter, body = parse_markdown(src.read_text())
    jsonld = md_to_jsonld(frontmatter, body)
    text = json.dumps(jsonld, indent=2, ensure_ascii=False)
    if out:
        out.write_text(text + "\n")
        print(f"Created: {out}")
    else:
        print(text)
    return 0


def cmd_to_markdown(src: Path, out: Path | None) -> int:
    jsonld = json.loads(src.read_text())
    fm, body = jsonld_to_md(jsonld)
    text = serialize_markdown(fm, body)
    if out:
        out.write_text(text)
        print(f"Created: {out}")
    else:
        print(text)
    return 0


def cmd_emit_jsonld(bundles: list[Path], out_dir: Path) -> int:
    count = 0
    for bundle in bundles:
        for md_path in iter_concepts(bundle):
            frontmatter, body = parse_markdown(md_path.read_text())
            jsonld = md_to_jsonld(frontmatter, body)
            rel = md_path.relative_to(bundle).with_suffix(".jsonld")
            dest = out_dir / bundle.name / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(jsonld, indent=2, ensure_ascii=False) + "\n")
            count += 1
    print(f"Emitted {count} JSON-LD projection(s) to {out_dir}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="MIF v1.0 markdown <-> JSON-LD")
    sub = parser.add_subparsers(dest="command", required=True)

    p_j = sub.add_parser("to-jsonld", help="Convert one .md concept to JSON-LD")
    p_j.add_argument("input")
    p_j.add_argument("output", nargs="?")

    p_m = sub.add_parser("to-markdown", help="Convert one .jsonld back to markdown")
    p_m.add_argument("input")
    p_m.add_argument("output", nargs="?")

    p_r = sub.add_parser("roundtrip", help="Assert lossless round-trip over bundles")
    p_r.add_argument("bundles", nargs="+")

    p_e = sub.add_parser("emit-jsonld", help="Emit derived JSON-LD projections")
    p_e.add_argument("bundles", nargs="+")
    p_e.add_argument("--out-dir", default="jsonld")

    args = parser.parse_args()

    if args.command == "to-jsonld":
        sys.exit(cmd_to_jsonld(Path(args.input), Path(args.output) if args.output else None))
    if args.command == "to-markdown":
        sys.exit(cmd_to_markdown(Path(args.input), Path(args.output) if args.output else None))
    if args.command == "roundtrip":
        sys.exit(cmd_roundtrip([Path(b) for b in args.bundles]))
    if args.command == "emit-jsonld":
        sys.exit(cmd_emit_jsonld([Path(b) for b in args.bundles], Path(args.out_dir)))


if __name__ == "__main__":
    main()
