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
  - ADR-016-versioned-schema-mirror-publication.md
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
couples every MIF bundle to that vendor.

Critically, **the Obsidian work was never implemented in the tooling.** No MIF
tool ever parsed or emitted wiki-links, `@[[Name|Type]]` entity references, or
block references — the converter, the OKF conformance gate, and the schema only
ever supported the markdown-link and `EntityReference` forms. The Obsidian
notation existed solely in the spec prose; it was documented but never built: 

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
3. **No special-case linter caveats.** Removing wiki-links removes the
   "intentional unresolved-wiki-link warning" exception ADR-003 had to carve out
   for Marksman.
4. **Keep what is genuinely portable, drop what is editor-specific.** YAML
   frontmatter, plain-text/local-first files, and folder-as-namespace are
   standard and are retained; wiki-links, `@[[...]]`, block refs, and embeds are
   Obsidian extensions and are dropped.

## Considered Options

### Option 1: Implement the Obsidian notation in the tooling

**Description**: Keep ADR-003's wiki-link / `@[[...]]` / block-reference syntax and build parser + emitter support for it into `mif_convert.py` and `okf_validate.py`, making the documented format the implemented one.

**Advantages**:
- Preserves Obsidian's automatic backlink/graph affordances for authors.
- Honors ADR-003 as written.

**Disadvantages**:
- Couples MIF's canonical format to one vendor's proprietary syntax — contradicts the vendor-neutral positioning (ADR-010, ADR-014).
- Two parallel relationship representations to parse, round-trip, and keep consistent.
- Retains the Marksman "expected unresolved-wiki-link" caveat.

**Risk Assessment**:
- **Technical Risk**: Medium. New parsing/emitting plus round-trip and OKF-legibility guarantees for a second syntax.
- **Ecosystem Risk**: High. Entrenches the vendor coupling the project is otherwise moving away from.

### Option 2: Leave the spec as-is (documented but unimplemented)

**Description**: Make no change; keep the Obsidian notation in the prose even though no tool implements it.

**Advantages**:
- Zero immediate work.

**Disadvantages**:
- The documentation-versus-implementation contradiction (#183) persists: following the spec literally yields bundles the validator rejects.
- Misrepresents MIF's actual, vendor-neutral format.

**Risk Assessment**:
- **Technical Risk**: Low (no change), but the latent defect keeps misleading implementers.
- **Ecosystem Risk**: Medium. Erodes trust in the spec as a faithful description of the format.

### Option 3: Remove the Obsidian notation; standardize on the implemented forms (chosen)

**Description**: Drop wiki-links, `@[[...]]`, block references, and embeds from the spec; make the already-implemented markdown-link relationships and frontmatter `EntityReference`s the only documented forms; remove the orphaned `blocks` field.

**Advantages**:
- Spec matches the validated implementation; following it produces conformant bundles.
- One relationship form and one entity model, both already exercised by every example and the round-trip converter.
- Restores vendor neutrality; removes the Marksman caveat.

**Disadvantages**:
- Authors lose Obsidian's wiki-link backlink/graph affordance (markdown-link graph tooling still works).

**Risk Assessment**:
- **Technical Risk**: Low. No code path that anything used is removed — only documentation and an unused OPTIONAL schema field change.
- **Ecosystem Risk**: Low. Non-breaking (existing data still validates); aligns the spec with reality.

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

## Schema Mirror at the Next Release (ADR-016)

Removing `blocks` changes the canonical schema, but `v1.0.0` is already released,
so per [ADR-016](ADR-016-versioned-schema-mirror-publication.md) its immutable
mirror is **not** edited. The change reaches the published mirrors only when the
next version is cut. Because removing an OPTIONAL field is non-breaking (the
concept object permits additional properties, so existing `blocks`-bearing data
still validates), this ships as a **MINOR** bump, `v1.1.0`.

The mirror scheme has exactly three path kinds: exact immutable snapshots
(`X.Y.Z`, unprefixed), the global `latest` alias, and `vMAJOR` aliases only
(`v0`, `v1`; `v2` reserved) — there are no minor-level aliases. Running
`scripts/snapshot-schema-version.py 1.1.0` then yields:

| Path | After v1.1.0 | Mutability |
| --- | --- | --- |
| `/schema/1.1.0/<file>` | **new** snapshot ← tag `v1.1.0` (no `blocks`) | immutable |
| `/schema/latest/<file>` | **moves** → 1.1.0 | tracks newest |
| `/schema/v1/<file>` | **moves** 1.0.0 → 1.1.0 (newest 1.x) | major alias |
| `/schema/1.0.0/<file>` | unchanged | immutable |
| `/schema/v0/<file>` | unchanged → still 0.1.0 (newest 0.x) | major alias |
| `/schema/0.1.0/<file>` | unchanged | immutable |
| `/schema/<file>` (root, `$id`) | already 1.1.0 bytes (no `blocks`) | moves with releases |

So `v1` and `latest` advance to 1.1.0; `1.0.0`, `0.1.0`, and `v0` are untouched.
The canonical `$id` stays unversioned throughout (ADR-007). This PR changes only
the source schemas and the unversioned canonical root; the versioned mirrors are
regenerated by the snapshot script at release.

## Decision Outcome

Chose Option 3. It resolves the documentation-versus-implementation
contradiction at its root: the spec now describes only the forms the tooling
already validates, MIF's canonical Markdown is vendor-neutral CommonMark, and no
functional capability is lost because the Obsidian notation was never
implemented. The single schema change — removing the unused OPTIONAL `blocks`
field — is non-breaking and reaches the published mirrors at the next release
(`v1.1.0`) per the table above.

## Related Decisions

- [ADR-003: Obsidian Compatibility](ADR-003-obsidian-compatibility.md) — superseded by this decision.
- [ADR-002: Dual Format Design](ADR-002-dual-format-design.md) — the Markdown half this ADR re-profiles.
- [ADR-010: Modeled Information Format Repositioning](ADR-010-modeled-information-format-repositioning.md) — the vendor-neutrality positioning that motivates dropping editor-specific notation.
- [ADR-014: Document Reference, Not Embed](ADR-014-document-reference-not-embed.md) — the same keep-vendor-notation-out principle applied to source documents.
- [ADR-011: Markdown Canonical, JSON-LD Derived](ADR-011-markdown-canonical-derived-jsonld.md) — the canonical Markdown whose relationship/entity forms this ADR fixes.
- [ADR-012: OKF Conformance as a Tested Invariant](ADR-012-okf-conformance-tested-invariant.md) — the conformance gate (`okf_validate.py`) that defines the canonical relationship form.
- [ADR-016: Per-Version Schema Mirror Publication](ADR-016-versioned-schema-mirror-publication.md) — governs how the `blocks` removal reaches the versioned mirrors at the next release (see the table above).

## More Information

- **Date:** 2026-06-29
- **Source:** issue #183; `scripts/okf_validate.py` (`REL_LINE_RE`); `scripts/mif_convert.py` (entities passthrough); `schema/mif.schema.json` (`Relationship`, `EntityReference`).

## Audit

### 2026-06-29

**Status:** Compliant

**Findings:**

| Finding | Files | Assessment |
|---------|-------|------------|
| Relationships documented only as body markdown links mirroring frontmatter `relationships[]` | `SPECIFICATION.md` §5.3/§8.4; `src/content/docs/specification/markdown-format.mdx` | compliant |
| Entity references documented only as frontmatter `entities[]` / `EntityReference` | `SPECIFICATION.md` §7.5; `src/content/docs/specification/entity-types.mdx` | compliant |
| `blocks` field removed from schema, context, converter passthrough, and test fixture | `schema/mif.schema.json`, `schema/context.jsonld`, `public/schema/mif.schema.json`, `public/schema/context.jsonld`, `scripts/mif_convert.py`, `scripts/test_temporal_and_properties.py` | compliant |
| No wiki-link / `@[[...]]` / `^block-id` / embed syntax remains in spec, docs, or examples (excluding migration history and immutable mirrors) | repo-wide sweep | compliant |
| OKF conformance, lossless round-trip, JSON-LD schema validation, ontology/namespace validation, and Astro build all pass | CI gates | compliant |

**Summary:** The Obsidian-specific notation is removed across the spec, published
`.mdx`, schema source + unversioned canonical, converter, tests, examples,
positioning docs, and branding. Immutable versioned schema mirrors (ADR-016) and
genuine migration history are intentionally retained.

**Action Required:** None.
