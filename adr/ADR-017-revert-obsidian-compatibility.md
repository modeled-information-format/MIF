---
title: "Revert Obsidian Compatibility"
description: "MIF drops the Obsidian-specific Markdown conventions adopted in ADR-003 — wiki-links, @[[entity]] references, block references, and embeds — because none are supported by the canonical tooling, which already requires standard markdown-link relationships and frontmatter entity references. YAML frontmatter, plain-text/local-first storage, and folder-as-namespace are retained; they are not Obsidian-specific."
type: adr
category: architecture
tags:
  - markdown
  - relationships
  - entities
  - commonmark
  - vendor-neutral
status: accepted
created: 2026-06-29
updated: 2026-06-29
author: MIF Maintainers
project: MIF
technologies:
  - markdown
audience:
  - developers
  - architects
supersedes:
  - ADR-003-obsidian-compatibility.md
related:
  - ADR-003-obsidian-compatibility.md
  - ADR-002-dual-format-design.md
  - ADR-010-modeled-information-format-repositioning.md
  - ADR-011-markdown-canonical-derived-jsonld.md
  - ADR-012-okf-conformance-tested-invariant.md
  - ADR-014-document-reference-not-embed.md
---

# ADR-017: Revert Obsidian Compatibility

## Status

Accepted — supersedes [ADR-003](ADR-003-obsidian-compatibility.md).

## Context

### Background and Problem Statement

ADR-003 committed MIF's Markdown representation to Obsidian-specific conventions:
wiki-link relationships (`[[target]]`, `[[Target|type]]`), `@[[Name|Type]]`
entity references, block references (`^block-id`), and embeds (`![[ ]]`), framed
as making a MIF store openable as an Obsidian vault.

This conflicts with MIF's positioning as a **vendor-neutral** content model
(ADR-010), the same principle that keeps source documents out of vendor schemas
(ADR-014): binding the canonical Markdown to one editor's proprietary notation
couples every MIF bundle to that vendor. The notation is also not what the
tooling implements.

That notation was never the format the tooling actually implements:

- **Relationships.** The OKF conformance gate `scripts/okf_validate.py` matches a
  body relationship line with `REL_LINE_RE` = `^-\s+([a-z0-9-]+)\s+\[[^\]]+\]\(([^)]+)\)\s*$`
  — a standard markdown link `- <type> [Text](/path.md)`. A wiki-link line
  (`- relates-to [[Other]]`) does **not** match and would fail the gate. The
  schema defines `Relationship.target` as a bundle-relative path or `urn:mif:`
  identifier (`schema/mif.schema.json`), not a wiki-link.
- **Entities.** `scripts/mif_convert.py` carries `entities` as a frontmatter
  passthrough; it does not parse `@[[...]]`. The canonical entity model is the
  `EntityReference` object (`schema/definitions/entity-reference.schema.json`),
  declared in frontmatter `entities[]` / `author`.
- **Every shipped example** already used markdown-link `## Relationships` sections
  and frontmatter entities. ADR-003's own 2026-06-18 audit records the example as
  using "a markdown-link `## Relationships` section" — contradicting the wiki-link
  decision the same ADR asserts.

The result was a documentation-versus-implementation contradiction (issue #183):
an author following the spec literally would write wiki-link relationships that
the normative validator rejects. ADR-003's notation decision was, in practice,
never adopted.

### Decision Drivers

1. **Vendor neutrality (ADR-010, ADR-014).** MIF's canonical Markdown must not
   bind a bundle to any single vendor's tool. Wiki-links, `@[[...]]`, block
   references, and embeds are Obsidian-proprietary; plain CommonMark with
   markdown-link relationships works in any editor — Obsidian included — without
   privileging it.
2. **Spec must match the validated implementation.** The normative documents must
   describe the forms the gates accept (markdown-link relationships, frontmatter
   `EntityReference`), not a syntax the tooling rejects.
2. **No special-case linter caveats.** Removing wiki-links removes the
   "intentional unresolved-wiki-link warning" exception ADR-003 had to carve out
   for Marksman.
3. **Keep what is genuinely portable, drop what is editor-specific.** YAML
   frontmatter, plain-text/local-first files, and folder-as-namespace are
   standard and are retained; wiki-links, `@[[...]]`, block refs, and embeds are
   Obsidian extensions and are dropped.

## Decision

Revert the Obsidian-specific conventions from ADR-003. Specifically:

1. **Relationships** are authoritative in frontmatter `relationships[]` (target =
   bundle-relative path or `urn:mif:` id) and mirrored in the body as standard
   markdown links: `- <type> [Text](/path/target.md)`.
2. **Entity references** are frontmatter `entities[]` / `author` `EntityReference`
   objects (or plain text for `author`). The `@[[Name|Type]]` notation is removed.
3. **Block references (`^block-id`) and embeds (`![[ ]]`) are removed.** This
   includes deleting the `blocks` field from the schema (`mif.schema.json`,
   `context.jsonld`) and the converter passthrough (`mif_convert.py`) — block
   references are reachable only via wiki-link syntax, which is itself removed.
4. **Obsidian is no longer a named compatibility target.** MIF Markdown is plain
   CommonMark; it still opens in any Markdown editor (Obsidian included), but the
   spec makes no Obsidian-specific guarantees.

**Retained (not Obsidian-specific):** YAML frontmatter for metadata; plain-text,
local-first files; folder-as-namespace layout (per [ADR-005](ADR-005-underscore-namespace-prefix.md)).

## Consequences

### Positive

1. The spec now matches the OKF conformance gate and the schema — following it
   produces bundles that validate.
2. No more "expected wiki-link warnings" caveat; example files pass generic
   Markdown tooling cleanly.
3. One relationship form (markdown links) and one entity model
   (`EntityReference`), already exercised by every example and the round-trip
   converter.

### Negative

1. Authors relying on Obsidian's automatic backlink/graph features from
   wiki-links lose that affordance. Relationships remain fully expressed as
   markdown links; graph tooling that reads markdown links still works.

### Neutral

1. The relationship and entity forms need no code changes — the tooling already
   implements them. The only code/schema change is removing the now-orphaned
   `blocks` field (block references were reachable only via the removed wiki-link
   syntax): dropped from `mif.schema.json`, `context.jsonld`, the
   `mif_convert.py` passthrough, and the `test_temporal_and_properties.py`
   fixture. The schema `$id` is unchanged (ADR-007); `blocks` was an OPTIONAL
   field unused by any shipped example.

## Related Decisions

- [ADR-003: Obsidian Compatibility](ADR-003-obsidian-compatibility.md) — superseded by this decision.
- [ADR-002: Dual Format Design](ADR-002-dual-format-design.md) — the Markdown half this ADR re-profiles.
- [ADR-011: Markdown Canonical, JSON-LD Derived](ADR-011-markdown-canonical-derived-jsonld.md) — the canonical Markdown whose relationship/entity forms this ADR fixes.
- [ADR-012: OKF Conformance as a Tested Invariant](ADR-012-okf-conformance-tested-invariant.md) — the conformance gate (`okf_validate.py`) that defines the canonical relationship form.

## More Information

- **Date:** 2026-06-29
- **Source:** issue #183; `scripts/okf_validate.py` (`REL_LINE_RE`); `scripts/mif_convert.py` (entities passthrough); `schema/mif.schema.json` (`Relationship`, `EntityReference`).
