#!/usr/bin/env python3
"""Migrate a MIF 0.1.0-draft bundle to v1.0.0.

Mechanical transform performed per concept (spec section 4, MIGRATION.md):

* ``*.memory.md`` -> ``*.md`` (drop the ``.memory`` infix so it never leaks into
  the OKF concept ID, which is the path minus ``.md``);
* ensure ``id`` is a UUID -- a non-UUID slug is rehashed to a deterministic
  UUIDv5 and the original slug is preserved as an ``alias``;
* convert body ``## Relationships`` Obsidian wiki-links
  (``- supersedes [[target-slug]]``) into OKF-legible markdown links
  (``- supersedes [Target Slug](/target-slug.md)``) and synthesize the
  authoritative frontmatter ``relationships`` array to match;
* leave all other frontmatter fields untouched (they remain valid OKF producer
  fields).

The derived ``*.memory.json`` JSON-LD files are NOT migrated -- under v1.0 the
JSON-LD projection is regenerated from markdown via ``mif_convert.py``.

Usage::

    python migrate_0_1_to_1_0.py <src-bundle> <dest-bundle>
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("Error: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
# "- <type> [[slug]]" or "- <type> [[slug|Display]]"
WIKILINK_REL_RE = re.compile(r"^-\s+([a-z0-9][a-z0-9-]*)\s+\[\[([^\]]+)\]\]\s*$")
# Stable namespace for slug -> UUIDv5 derivation.
MIF_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://mif-spec.dev")

FRONTMATTER_ORDER = [
    "id",
    "type",
    "created",
    "modified",
    "namespace",
    "title",
    "summary",
    "tags",
    "aliases",
    "relationships",
]


def stringify_datetimes(obj):
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


def titleize(slug: str) -> str:
    return " ".join(word.capitalize() for word in re.split(r"[-_\s]+", slug) if word)


def order_frontmatter(fm: dict) -> dict:
    ordered: dict = {}
    for key in FRONTMATTER_ORDER:
        if key in fm:
            ordered[key] = fm[key]
    for key, value in fm.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def convert_relationships(body: str) -> tuple[str, list[dict]]:
    """Rewrite body ## Relationships wiki-links to markdown links.

    Returns the rewritten body and the synthesized frontmatter relationships.
    """
    rels: list[dict] = []
    out_lines: list[str] = []
    in_section = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped[3:].strip().lower() == "relationships"
            out_lines.append(line)
            continue
        if in_section:
            match = WIKILINK_REL_RE.match(stripped)
            if match:
                rel_type = match.group(1)
                inner = match.group(2)
                slug, _, display = inner.partition("|")
                slug = slug.strip()
                text = display.strip() or titleize(slug)
                target = f"/{slug}.md"
                rels.append({"type": rel_type, "target": target})
                out_lines.append(f"- {rel_type} [{text}]({target})")
                continue
        out_lines.append(line)
    return "\n".join(out_lines), rels


def migrate_concept(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("No frontmatter found")
    fm = stringify_datetimes(yaml.safe_load(match.group(1)) or {})
    if not isinstance(fm, dict):
        raise ValueError("Frontmatter is not a YAML mapping")
    body = match.group(2)

    # id -> UUID
    raw_id = str(fm.get("id", "")).strip()
    if not UUID_RE.match(raw_id):
        new_id = str(uuid.uuid5(MIF_NAMESPACE, raw_id or text[:64]))
        if raw_id:
            aliases = fm.get("aliases") or []
            if raw_id not in aliases:
                aliases = [*aliases, raw_id]
            fm["aliases"] = aliases
        fm["id"] = new_id

    new_body, rels = convert_relationships(body)
    if rels:
        fm["relationships"] = rels

    fm = order_frontmatter(fm)
    yaml_text = yaml.safe_dump(
        fm, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).strip()
    new_body = new_body.lstrip("\n").rstrip() + "\n"
    return f"---\n{yaml_text}\n---\n\n{new_body}"


def migrate_bundle(src: Path, dest: Path) -> int:
    count = 0
    for md_path in sorted(src.rglob("*.memory.md")):
        rel = md_path.relative_to(src)
        out_name = rel.name.replace(".memory.md", ".md")
        out_path = dest / rel.parent / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(migrate_concept(md_path.read_text()))
        print(f"  {rel} -> {out_path.relative_to(dest)}")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate MIF 0.1.0-draft -> 1.0.0")
    parser.add_argument("src", help="Source 0.1 bundle directory")
    parser.add_argument("dest", help="Destination 1.0 bundle directory")
    args = parser.parse_args()

    src = Path(args.src)
    dest = Path(args.dest)
    if not src.exists():
        print(f"Source bundle not found: {src}", file=sys.stderr)
        sys.exit(1)
    dest.mkdir(parents=True, exist_ok=True)
    count = migrate_bundle(src, dest)
    print(f"Migrated {count} concept(s): {src} -> {dest}")


if __name__ == "__main__":
    main()
