#!/usr/bin/env python3
"""Generate the mif-spec.dev specification pages from SPECIFICATION.md.

SPECIFICATION.md is the single source of the MIF specification. The Starlight
pages under src/content/docs/specification/ are build output of this script:
each page is one or more top-level (``##``) sections of the spec, with a
Starlight frontmatter block, section numbers stripped from headings, and every
intra-spec cross-reference rewritten to the page that now holds its target.

Usage:
    python scripts/build_spec_pages.py           # (re)write the pages
    python scripts/build_spec_pages.py --check   # exit 1 if committed pages drift

Rewrites applied to prose (never to fenced code or inline code spans):

- ``[text](#anchor)`` links to spec headings -> ``/specification/<slug>/#<id>``
  (or ``#<id>`` when the target is on the same page).
- Bare section references -- ``§5.3``, ``Section 5.4.3``, ``see 4.2``,
  ``defined in 10.2`` -- become links whose text is the target heading.
- Repo-relative links (``MIGRATION.md``) become GitHub blob URLs, since they
  would 404 on the site.
- ``{``/``}`` are escaped, because MDX parses them as expressions.

Everything before the first ``##`` heading (title block) and the Table of
Contents are not published; the page navigation replaces them.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "SPECIFICATION.md"
OUT_DIR = ROOT / "src" / "content" / "docs" / "specification"
REPO_BLOB = "https://github.com/modeled-information-format/MIF/blob/main/"

# slug -> (title, description, top-level sections in page order).
# A section is named by its number ("4") or, if unnumbered, its exact title.
PAGES: dict[str, tuple[str, str, list[str]]] = {
    "overview": (
        "Overview",
        "Abstract, terminology, design principles, and migration path of the Modeled Information Format.",
        ["Abstract", "1", "2", "17"],
    ),
    "file-format": (
        "File Format",
        "File extensions, encoding requirements, and YAML frontmatter structure.",
        ["3"],
    ),
    "data-model": (
        "Data Model",
        "Required and optional fields, schema definitions, and core data structures.",
        ["4"],
    ),
    "markdown-format": (
        "Markdown Format",
        "The canonical .md format specification for human-readable concept files.",
        ["5"],
    ),
    "json-ld-format": (
        "JSON-LD Format",
        "The derived .jsonld projection for machine-processable concept documents.",
        ["6"],
    ),
    "entity-types": (
        "Entity Types",
        "Person, Organization, Technology, Concept, and File entity type definitions.",
        ["7"],
    ),
    "relationship-types": (
        "Relationship Types",
        "The nine core relationship types for connecting concepts.",
        ["8"],
    ),
    "temporal-model": (
        "Temporal Model",
        "Validity windows and freshness — bi-temporal tracking and decay models.",
        ["9"],
    ),
    "namespace-model": (
        "Namespace Model",
        "Namespace hierarchy, reserved prefixes, and organizational patterns for concepts.",
        ["10"],
    ),
    "embeddings": (
        "Embeddings",
        "Embedding reference specifications for vector search integration.",
        ["11"],
    ),
    "provenance": (
        "Provenance",
        "Provenance metadata and the optional W3C PROV-aligned provenance layer.",
        ["12"],
    ),
    "conformance": (
        "Conformance Levels",
        "Level 1, 2, and 3 conformance requirements for MIF implementations.",
        ["13"],
    ),
    "json-ld-context": (
        "JSON-LD Context",
        "The MIF JSON-LD context definition and namespace mappings.",
        ["14"],
    ),
    "conversion": (
        "Conversion Rules",
        "Rules for converting between Markdown and JSON-LD formats.",
        ["15"],
    ),
    "examples": (
        "Examples",
        "Complete MIF concept examples at each conformance level.",
        ["16"],
    ),
    "security": (
        "Security",
        "Security considerations and IANA media type registrations.",
        ["18", "19"],
    ),
    "appendices": (
        "Appendices",
        "Quick references for YAML frontmatter, relationship types, entity syntax, and citations.",
        [
            "Appendix A: YAML Frontmatter Quick Reference",
            "Appendix B: Relationship Types Quick Reference",
            "Appendix C: Entity Reference Syntax",
            "Appendix D: Citations Quick Reference",
            "References",
        ],
    ),
}

# Top-level sections intentionally left off the site.
UNPUBLISHED = {"Table of Contents"}

GENERATED_NOTICE = (
    "{/* GENERATED from SPECIFICATION.md by scripts/build_spec_pages.py. "
    "Do not edit; edit SPECIFICATION.md and re-run the script. */}"
)

HEADING_RE = re.compile(r"^(#{2,6}) +(.*?)\s*#*\s*$")
NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
SEPARATOR_RE = re.compile(r"^\s*(?:---+|\*\*\*+)\s*$")
FOOTER_RE = re.compile(r"^\*This specification is open source.*\*$")


class SpecError(Exception):
    """SPECIFICATION.md does not match the page map."""


@dataclass
class Heading:
    level: int
    raw: str  # heading text as written in the spec
    number: str | None  # "5.4.3", or None for unnumbered headings
    text: str  # heading text with the section number stripped
    page: str = ""
    anchor: str = ""  # id Starlight renders for the stripped heading


@dataclass
class Section:
    heading: Heading
    lines: list[str] = field(default_factory=list)


def slugify(text: str) -> str:
    """github-slugger, as used by Astro's heading ids (on rendered text)."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    text = text.lower()
    kept = "".join(ch for ch in text if ch.isalnum() or ch in " -_")
    return kept.replace(" ", "-")


class Slugger:
    """Per-page unique ids, matching github-slugger's ``-1``, ``-2`` suffixes."""

    def __init__(self) -> None:
        self.seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        base = slugify(text)
        result = base
        while result in self.seen:
            self.seen[base] += 1
            result = f"{base}-{self.seen[base]}"
        self.seen[result] = 0
        return result


def iter_lines_with_fence(lines: list[str]):
    """Yield (line, in_code) where in_code covers fence delimiters too."""
    fence: str | None = None
    for line in lines:
        m = FENCE_RE.match(line)
        if fence is None and m:
            fence = m.group(1)
            yield line, True
        elif fence is not None:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and line.strip() == m.group(1):
                fence = None
            yield line, True
        else:
            yield line, False


def parse_heading(line: str) -> Heading | None:
    m = HEADING_RE.match(line)
    if not m:
        return None
    raw = m.group(2)
    n = NUMBER_RE.match(raw)
    if n:
        return Heading(len(m.group(1)), raw, n.group(1), n.group(2))
    return Heading(len(m.group(1)), raw, None, raw)


def split_spec(text: str) -> list[Section]:
    sections: list[Section] = []
    for line, in_code in iter_lines_with_fence(text.splitlines()):
        heading = None if in_code else parse_heading(line)
        if heading and heading.level == 2:
            sections.append(Section(heading))
        elif sections:
            sections[-1].lines.append(line)
    return sections


def section_key(section: Section) -> str:
    return section.heading.number or section.heading.text


def assign_pages(sections: list[Section]) -> dict[str, list[Section]]:
    by_key = {section_key(s): s for s in sections}
    wanted = {key for _, _, keys in PAGES.values() for key in keys}
    unmapped = [k for k in by_key if k not in wanted and k not in UNPUBLISHED]
    if unmapped:
        raise SpecError(f"top-level spec sections not mapped to any page: {unmapped}")
    pages: dict[str, list[Section]] = {}
    for slug, (_, _, keys) in PAGES.items():
        missing = [k for k in keys if k not in by_key]
        if missing:
            raise SpecError(f"page {slug!r} maps to sections missing from the spec: {missing}")
        pages[slug] = [by_key[k] for k in keys]
    return pages


def build_index(pages: dict[str, list[Section]]) -> tuple[dict[str, Heading], dict[str, Heading]]:
    """Map section numbers and original spec anchors to their new location.

    Returns (by_number, by_spec_anchor). Anchors are computed exactly as the
    page will render them: single-section pages drop their ``##`` heading.
    """
    by_number: dict[str, Heading] = {}
    by_anchor: dict[str, Heading] = {}
    spec_slugger = Slugger()  # ids the headings have in SPECIFICATION.md itself
    for slug, sections in pages.items():
        page_slugger = Slugger()
        multi = len(sections) > 1
        for section in sections:
            headings = [section.heading]
            for line, in_code in iter_lines_with_fence(section.lines):
                h = None if in_code else parse_heading(line)
                if h:
                    headings.append(h)
            for h in headings:
                h.page = slug
                rendered = h.level > 2 or multi
                h.anchor = page_slugger.slug(h.text) if rendered else ""
                if h.number:
                    by_number[h.number] = h
                by_anchor[spec_slugger.slug(h.raw)] = h
    return by_number, by_anchor


def link_to(target: Heading, page: str) -> str:
    if target.page == page:
        return f"#{target.anchor}" if target.anchor else "#"
    url = f"/specification/{target.page}/"
    return f"{url}#{target.anchor}" if target.anchor else url


INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
ANCHOR_LINK_RE = re.compile(r"\]\(#([^)\s]+)\)")
REL_LINK_RE = re.compile(r"\]\((?![a-z][a-z0-9+.-]*:|#|/|<)([^)\s]+)\)")
NUM = r"\d+(?:\.\d+)*"
SECTION_REF_RE = re.compile(rf"(§|\bSection |\b(?:see|in|and) )({NUM})(?![\d.]*\d)")
WRAPPED_REF_RE = re.compile(rf"^(\s*)({NUM})(?![\d.]*\d)")
WRAP_TRIGGER_RE = re.compile(r"\b(?:see|in|and)\s*$")


class Rewriter:
    def __init__(self, by_number: dict[str, Heading], by_anchor: dict[str, Heading]) -> None:
        self.by_number = by_number
        self.by_anchor = by_anchor
        self.errors: list[str] = []

    def _ref(self, page: str, number: str) -> str | None:
        target = self.by_number.get(number)
        if target is None:
            return None
        return f"[{target.text}]({link_to(target, page)})"

    def prose(self, segment: str, page: str, at_line_start_ref: bool) -> str:
        def anchor(m: re.Match) -> str:
            target = self.by_anchor.get(m.group(1))
            if target is None:
                self.errors.append(f"{page}: link to unknown spec anchor #{m.group(1)}")
                return m.group(0)
            return f"]({link_to(target, page)})"

        def section_ref(m: re.Match) -> str:
            prefix, number = m.group(1), m.group(2)
            link = self._ref(page, number)
            if link is None:
                if prefix in ("§", "Section "):
                    self.errors.append(f"{page}: reference to unknown section {prefix}{number}")
                return m.group(0)
            keep = "" if prefix in ("§", "Section ") else prefix
            return keep + link

        # Link passes first, so they never see the links the reference passes create.
        segment = ANCHOR_LINK_RE.sub(anchor, segment)
        segment = REL_LINK_RE.sub(lambda m: f"]({REPO_BLOB}{m.group(1)})", segment)
        if at_line_start_ref:
            m = WRAPPED_REF_RE.match(segment)
            if m and (link := self._ref(page, m.group(2))):
                segment = m.group(1) + link + segment[m.end():]
        segment = SECTION_REF_RE.sub(section_ref, segment)
        return segment.replace("{", "\\{").replace("}", "\\}")

    def line(self, line: str, page: str, prev_prose: str) -> str:
        """Rewrite one prose line, leaving inline code spans untouched."""
        wrapped = bool(WRAP_TRIGGER_RE.search(prev_prose))
        out, pos = [], 0
        for m in INLINE_CODE_RE.finditer(line):
            out.append(self.prose(line[pos:m.start()], page, wrapped and pos == 0))
            out.append(m.group(0))
            pos = m.end()
        out.append(self.prose(line[pos:], page, wrapped and pos == 0))
        return "".join(out)


def render_section(section: Section, page: str, multi: bool, rw: Rewriter) -> list[str]:
    out: list[str] = []
    if multi:
        out += [f"## {section.heading.text}", ""]
    prev = ""
    for line, in_code in iter_lines_with_fence(section.lines):
        if in_code:
            out.append(line)
            prev = ""
            continue
        heading = parse_heading(line)
        if heading:
            out.append(f"{'#' * heading.level} {rw.line(heading.text, page, '')}")
            prev = ""
            continue
        if FOOTER_RE.match(line.strip()):
            continue
        out.append(rw.line(line, page, prev))
        prev = line
    # Drop the spec's trailing "---" section separators and blank lines.
    while out and (not out[-1].strip() or SEPARATOR_RE.match(out[-1])):
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    return out


def yaml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_pages(spec_text: str) -> tuple[dict[str, str], list[str]]:
    pages = assign_pages(split_spec(spec_text))
    rw = Rewriter(*build_index(pages))
    rendered: dict[str, str] = {}
    for slug, sections in pages.items():
        title, description, _ = PAGES[slug]
        body: list[str] = []
        for section in sections:
            if body:
                body.append("")
            body += render_section(section, slug, len(sections) > 1, rw)
        rendered[f"{slug}.mdx"] = "\n".join(
            ["---", f"title: {yaml_str(title)}", f"description: {yaml_str(description)}", "---", "",
             GENERATED_NOTICE, "", *body, ""]
        )
    return rendered, rw.errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the committed pages differ from generated output")
    args = parser.parse_args(argv)

    try:
        rendered, errors = render_pages(SPEC.read_text(encoding="utf-8"))
    except SpecError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 2

    existing = {p.name for p in OUT_DIR.glob("*.mdx")}
    stale = sorted(existing - rendered.keys())
    if args.check:
        drift = False
        for name, content in rendered.items():
            path = OUT_DIR / name
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != content:
                drift = True
                sys.stdout.writelines(difflib.unified_diff(
                    current.splitlines(keepends=True), content.splitlines(keepends=True),
                    f"a/{path.relative_to(ROOT)}", f"b/{path.relative_to(ROOT)} (generated)"))
        for name in stale:
            drift = True
            print(f"{OUT_DIR.relative_to(ROOT) / name}: not generated from SPECIFICATION.md")
        if drift:
            print("\nSpec pages are out of date with SPECIFICATION.md. Edit SPECIFICATION.md, then run:\n"
                  "  python scripts/build_spec_pages.py", file=sys.stderr)
            return 1
        print(f"OK: {len(rendered)} spec pages match SPECIFICATION.md")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (OUT_DIR / name).write_text(content, encoding="utf-8")
    for name in stale:
        (OUT_DIR / name).unlink()
    print(f"wrote {len(rendered)} pages to {OUT_DIR.relative_to(ROOT)}"
          + (f"; removed {stale}" if stale else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
