"""Regression suite for scripts/build_spec_pages.py (SPECIFICATION.md -> site pages)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import build_spec_pages as b  # noqa: E402


@pytest.fixture
def pages(monkeypatch):
    """A three-page map over a small synthetic spec."""
    monkeypatch.setattr(b, "PAGES", {
        "intro": ("Intro", "d", ["Abstract", "1"]),
        "format": ("Format", "d", ["2"]),
        "refs": ("Refs", "d", ["References"]),
    })


SPEC = """\
# Title

**Version**: 1.0.0

## Abstract

Abstract text ([Invariant 1](#invariants)).

### Invariants

1. Markdown is canonical (§2.1).

## Table of Contents

1. [Terminology](#1-terminology)

## 1. Terminology

Terms; see 2.1 and the `see 2.1` code span. Values are between 0.0 and 1.0.
The relationship syntax (see
2.1) is wrapped across lines. Use {braces} literally.
Read [the guide](docs/guide.md) or [RFC](https://example.org/x).

---

## 2. Format

Prelude.

### 2.1 Syntax

```markdown
## Relationships

- relates-to [X](#not-rewritten) see 2.1
```

### 2.2 Example

As in Section 2.1.

---

## References

- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119)

---

*This specification is open source and contributions are welcome.*
"""


def render(spec: str = SPEC) -> dict[str, str]:
    rendered, errors = b.render_pages(spec)
    assert errors == []
    return rendered


def test_split_is_fence_aware(pages):
    keys = [b.section_key(s) for s in b.split_spec(SPEC)]
    assert keys == ["Abstract", "Table of Contents", "1", "2", "References"]


def test_title_block_and_toc_are_not_published(pages):
    out = "\n".join(render().values())
    assert "**Version**" not in out
    assert "Table of Contents" not in out


def test_frontmatter_and_notice(pages):
    page = render()["format.mdx"]
    assert page.startswith('---\ntitle: "Format"\ndescription: "d"\n---\n\n{/* GENERATED')


def test_single_section_page_drops_its_h2_and_strips_numbers(pages):
    page = render()["format.mdx"]
    assert "## Format" not in page
    assert "### Syntax" in page and "### 2.1" not in page
    assert "Prelude." in page


def test_multi_section_page_keeps_stripped_h2(pages):
    page = render()["intro.mdx"]
    assert "## Abstract" in page and "## Terminology" in page


def test_cross_page_and_same_page_refs(pages):
    intro = render()["intro.mdx"]
    assert "[Invariant 1](#invariants)" in intro
    assert "canonical ([Syntax](/specification/format/#syntax))" in intro
    assert "see [Syntax](/specification/format/#syntax) and" in intro
    fmt = render()["format.mdx"]
    assert "As in [Syntax](#syntax)." in fmt


def test_wrapped_reference(pages):
    assert "(see\n[Syntax](/specification/format/#syntax)) is wrapped" in render()["intro.mdx"]


def test_code_is_never_rewritten(pages):
    intro, fmt = render()["intro.mdx"], render()["format.mdx"]
    assert "`see 2.1` code span" in intro
    assert "- relates-to [X](#not-rewritten) see 2.1" in fmt
    assert "## Relationships" in fmt


def test_non_section_numbers_untouched(pages):
    assert "between 0.0 and 1.0." in render()["intro.mdx"]


def test_repo_relative_links_and_braces(pages):
    intro = render()["intro.mdx"]
    assert f"[the guide]({b.REPO_BLOB}docs/guide.md)" in intro
    assert "[RFC](https://example.org/x)" in intro
    assert r"Use \{braces\} literally." in intro


def test_separators_and_footer_dropped(pages):
    refs = render()["refs.mdx"]
    assert refs.rstrip().endswith("(https://www.rfc-editor.org/rfc/rfc2119)")
    assert "open source" not in refs


def test_unknown_anchor_and_section_are_errors(pages):
    _, errors = b.render_pages(SPEC.replace("(#invariants)", "(#nope)").replace("§2.1", "§9.9"))
    assert any("#nope" in e for e in errors)
    assert any("§9.9" in e for e in errors)


def test_unmapped_section_is_an_error(pages):
    with pytest.raises(b.SpecError, match="not mapped"):
        b.render_pages(SPEC + "\n## 3. New Section\n\nText.\n")


def test_duplicate_heading_ids_get_suffixes():
    s = b.Slugger()
    assert [s.slug("Example"), s.slug("Example"), s.slug("Example")] == ["example", "example-1", "example-2"]
    assert b.slugify("Entity References in `Memories` — Notes") == "entity-references-in-memories--notes"


def test_real_spec_renders_cleanly_and_matches_committed_pages():
    """The repo's own pages are in sync (the same gate CI runs via --check)."""
    rendered, errors = b.render_pages(b.SPEC.read_text(encoding="utf-8"))
    assert errors == []
    for name, content in rendered.items():
        assert (b.OUT_DIR / name).read_text(encoding="utf-8") == content, name
