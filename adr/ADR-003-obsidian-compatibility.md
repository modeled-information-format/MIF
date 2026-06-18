---
title: "Obsidian Compatibility"
description: "MIF's Markdown representation adopts Obsidian-compatible conventions — YAML frontmatter, wiki-links, block references, folder-as-namespace, and plain CommonMark — so memories work seamlessly in Obsidian vaults while remaining portable plain text."
type: adr
category: architecture
tags:
  - obsidian
  - markdown
  - compatibility
  - wiki-links
status: accepted
created: 2026-01-27
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - obsidian
  - markdown
audience:
  - developers
  - architects
related:
  - ADR-002-dual-format-design.md
  - ADR-005-underscore-namespace-prefix.md
---

# ADR-003: Obsidian Compatibility

## Status

Accepted

## Context

### Background and Problem Statement

Many knowledge workers use [Obsidian](https://obsidian.md) for personal knowledge
management. MIF's Markdown representation (the human-readable half of the dual
format established in ADR-002) targets these users directly: a MIF memory store
should be openable as an ordinary Obsidian vault, with no import step and no
proprietary tooling. The architectural question is *how far* MIF should commit to
Obsidian's conventions, given that Obsidian layers several non-CommonMark
features on top of plain Markdown.

The Obsidian features MIF cares about are:

- **YAML frontmatter** for structured metadata
- **Wiki-style `[[links]]`** for cross-references between notes
- **`^block-id` references** for granular, paragraph-level linking
- **Folder-based organization**, where directory structure carries meaning
- **Local-first, plain-text files** — no database, no network dependency

MIF should work seamlessly with Obsidian while maintaining format independence:
the Markdown files must remain readable in any text editor or Markdown processor,
not just inside Obsidian.

### Current Limitations

- Wiki-links (`[[target]]`) and block references (`^block-id`) are Obsidian
  extensions, not CommonMark. Generic Markdown linters and language servers
  (e.g., Marksman) flag unresolved wiki-links as warnings even when they are
  valid relationship declarations.
- Block-id syntax adds surface complexity that plain-Markdown authors may not
  recognize.
- Obsidian-specific affordances (graph view, backlinks, Dataview) cannot be
  guaranteed to translate to every downstream MIF consumer, so they must be
  treated as enhancements rather than requirements.

## Decision Drivers

### Primary Decision Drivers

1. **Zero-friction adoption**: An existing Obsidian user must be able to point
   Obsidian at a MIF store and have it work immediately, with no conversion.
2. **Plain-text portability**: The Markdown files must remain valid, readable
   Markdown outside Obsidian — format independence is non-negotiable.
3. **Rich relationship expression**: The format must capture typed memory
   relationships in a way Obsidian can navigate (backlinks, graph view).

### Secondary Decision Drivers

1. **Local-first ownership**: No required network dependency or proprietary
   store; the user owns the files.
2. **Tooling honesty**: Where Obsidian extensions trip generic linters, that
   friction must be documented as expected rather than treated as a defect.

## Considered Options

### Option 1: Custom MIF-only Markdown syntax

**Description**: Define a bespoke link and metadata syntax tuned to MIF's
relationship model, independent of any existing editor's conventions.

**Advantages**:
- Maximum control over the relationship vocabulary.
- No dependence on a third-party tool's feature set.

**Disadvantages**:
- No existing editor understands it; users get no graph view, backlinks, or
  navigation for free.
- Every consumer must implement custom parsing.
- Abandons the zero-friction adoption that motivates Markdown at all.

**Risk Assessment**:
- **Technical Risk**: Medium. Custom parsing is straightforward but must be
  built and maintained everywhere.
- **Ecosystem Risk**: High. No off-the-shelf tooling; adoption friction is the
  whole cost.

### Option 2: Strict CommonMark with no Obsidian extensions

**Description**: Restrict the Markdown format to pure CommonMark — standard
inline links only, no wiki-links, no block references.

**Advantages**:
- Passes every generic Markdown linter cleanly, no expected-warning caveats.
- Maximum portability across plain-Markdown tools.

**Disadvantages**:
- Loses Obsidian's automatic backlink tracking and graph visualization, which
  depend on wiki-link syntax.
- No paragraph-level (`^block-id`) linking, so granular citations are lost.
- Delivers a poorer experience precisely for the target audience.

**Risk Assessment**:
- **Technical Risk**: Low.
- **Ecosystem Risk**: Medium. Portable but strips the navigation value that
  makes a knowledge vault useful.

### Option 3: Obsidian-compatible conventions (chosen)

**Description**: Adopt Obsidian's conventions as the MIF Markdown profile —
YAML frontmatter, wiki-links, block references, folder-as-namespace, and
CommonMark-compatible body content — while keeping every file readable as plain
Markdown.

**Technical Characteristics**:
- Memory metadata lives in standard YAML frontmatter (Obsidian's Properties
  panel reads/writes it).
- Relationships use `[[target]]` wiki-link syntax, including display text
  `[[Target|Display]]`, heading anchors `[[Target#Heading]]`, and block
  references `[[Note#^block-id]]`.
- Granular anchors use `^block-id` suffixes.
- A memory's namespace maps to its folder path.
- All body content is CommonMark-compatible.

**Advantages**:
- Zero-friction integration: existing Obsidian users adopt immediately, with
  bidirectional vault sync.
- Rich linking and navigation (graph view, backlinks) work out of the box.
- Compatible with the Obsidian plugin ecosystem.
- Files stay readable in any text editor.

**Disadvantages**:
- Wiki-links and block IDs are non-CommonMark; generic linters emit expected
  warnings on unresolved wiki-links.
- Some Obsidian-specific features may not translate to all MIF consumers.

**Risk Assessment**:
- **Technical Risk**: Low. The conventions are stable and widely implemented.
- **Schedule Risk**: Low. No bespoke tooling required.
- **Ecosystem Risk**: Low. Leverages an established, popular tool while
  preserving plain-text portability.

## Decision

Adopt Obsidian-compatible conventions for MIF's Markdown representation:

1. **YAML Frontmatter** — store memory metadata in standard YAML frontmatter.
2. **Wiki-links** — use `[[target]]` syntax for memory relationships.
3. **Block References** — support `^block-id` for granular citations.
4. **File Structure** — namespace maps to folder path.
5. **Plain Text** — all memories are valid Markdown files.

### Example

```markdown
---
id: abc123
type: semantic
namespace: _semantic/knowledge
---

# My Memory

This relates to [[other-memory]] and specifically to [[another#^block-id]].

Key insight here. ^important-point
```

The Markdown format MUST be valid Obsidian notes (SPECIFICATION.md §2.2),
ensuring files work in Obsidian vaults while remaining readable in any text
editor or Markdown processor.

## Consequences

### Positive

1. **Zero-friction Obsidian integration**: a MIF store opens as a vault with no
   import step.
2. **Immediate adoption**: existing Obsidian users can adopt MIF as-is.
3. **Bidirectional sync** with Obsidian vaults.
4. **Rich linking and navigation** in Obsidian (graph view, backlinks).
5. **Plugin compatibility** (graph view, backlinks, Dataview, etc.).

### Negative

1. **Wiki-link validation requires tooling**: Marksman and similar linters emit
   warnings on unresolved wiki-links — these are expected, not defects.
2. **Block IDs add syntax complexity** beyond plain CommonMark.
3. **Obsidian-specific features may not translate** to all MIF consumers.
4. **Some validation tools flag intentional wiki-links as errors**, requiring
   the documented caveat below.

### Neutral

1. **Folder-as-namespace coupling**: directory structure carries semantic
   meaning (the namespace), which is convenient in Obsidian and explicit in the
   underscore-prefix convention (ADR-005), but it ties physical layout to the
   logical model.

## Decision Outcome

The Obsidian-compatible approach achieves the primary drivers: zero-friction
adoption (vaults open as-is), plain-text portability (files remain valid
Markdown), and rich relationship expression (wiki-links drive Obsidian's
backlink and graph features). Mitigations for the known friction:

- **Expected linter warnings** are documented as intentional (see note below),
  so unresolved-wiki-link findings in example files are not mistaken for broken
  references.
- **Portability** is preserved by keeping body content CommonMark-compatible and
  confining Obsidian extensions to links and metadata.

> **Note — intentional validation warnings:** Wiki-link validation warnings from
> tools like Marksman are **intentional** in example files. They demonstrate MIF
> relationship syntax, not broken references.

## Related Decisions

- [ADR-002: Dual Format Design](ADR-002-dual-format-design.md) — Obsidian-compatible Markdown is one of the two formats MIF maintains; this ADR profiles that Markdown half.
- [ADR-005: Underscore Namespace Prefix](ADR-005-underscore-namespace-prefix.md) — the underscore-prefix convention ensures the folder-as-namespace mapping is filesystem-compatible with Obsidian vaults.

## Links

- [Obsidian](https://obsidian.md) — the personal knowledge management tool whose conventions MIF's Markdown profile targets.

## More Information

- **Date:** 2026-01-27
- **Source:** SPECIFICATION.md §2.2 "Obsidian Compatibility"; example memory `examples/semantic/rate-limit-policy.md`.
- **Related ADRs:** ADR-002, ADR-005

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Markdown MUST be valid Obsidian notes; required features = YAML frontmatter, wiki-links (incl. display text + heading anchors), block references, aliases, tags, standard CommonMark | `SPECIFICATION.md` | L112-L128 | compliant |
| Optional Obsidian extensions (callouts, embeds, Dataview) documented as enhancements, not requirements | `SPECIFICATION.md` | L130-L134 | compliant |
| Example memory carries YAML frontmatter (id, type, namespace, tags, relationships) | `examples/semantic/rate-limit-policy.md` | L1-L19 | compliant |
| Example memory's `namespace:` frontmatter maps to folder path (`_semantic/policies`) | `examples/semantic/rate-limit-policy.md` | L6 | compliant |
| Example memory uses a markdown-link `## Relationships` section for typed cross-references | `examples/semantic/rate-limit-policy.md` | L31-L34 | compliant |

**Summary:** The Obsidian-compatibility requirements (frontmatter, wiki-links,
block references, aliases, tags, CommonMark body) are stated normatively in
SPECIFICATION.md §2.2, and a shipped example memory demonstrates YAML
frontmatter, folder-as-namespace, and a typed-relationship section.

**Action Required:** None.
