---
title: "Source Documents Travel by Reference, Not by Embedded Vendor Schema"
description: "MIF carries source documents alongside memories via a vendor-neutral DocumentReference (pointer + integrity metadata) rather than embedding a vendor-specific document model such as DoclingDocument."
type: adr
category: architecture
tags:
  - documents
  - vendor-neutral
  - schema
  - provenance
  - integrity
status: accepted
created: 2026-06-26
updated: 2026-06-26
author: MIF Maintainers
project: MIF
technologies:
  - json-schema
  - json-ld
audience:
  - developers
  - architects
related:
  - ADR-006-entitydata-vs-entityreference.md
  - ADR-009-okf-compliance-superset.md
  - ADR-010-modeled-information-format-repositioning.md
---

# ADR-014: Source Documents Travel by Reference, Not by Embedded Vendor Schema

## Status

Accepted

## Context

### Background and Problem Statement

Memories are frequently derived from underlying source documents — PDFs,
web pages, transcripts, datasets. Consumers need to know *which* document a
memory came from, retrieve it, and verify it has not changed. Issue #77
proposed solving this by embedding a `DoclingDocument` — IBM Docling's rich
parsed-document model — directly inside a MIF memory.

Embedding a vendor document schema conflicts with MIF's positioning (ADR-010)
as a *vendor-neutral* content model and with the EntityData/EntityReference
distinction (ADR-006), which already favors lightweight references over inline
vendor payloads. A memory that embeds `DoclingDocument` is no longer portable:
it binds the bundle to one parser's object model, inflates every memory with a
full parsed-layout tree, and forces any conformant reader to understand a
third-party schema it did not choose.

The existing `Citation` construct is close but wrong for this job: it is
`additionalProperties: false` and models bibliographic intent (`citationType`,
`citationRole`, `relevance`) — it has no place for content integrity (`hash`),
media type (`contentType`), size (`byteLength`), or a retrieval-time version
token. Extending `Citation` would overload a bibliographic type with artifact
metadata. This decision records a *new* construct instead.

### Current Limitations

- No first-class way to point at the source artifact a memory was derived from.
- No content-integrity or versioning metadata to detect that a referenced
  document drifted after the memory was created.
- Issue #77's embed-the-vendor-schema approach would couple MIF to Docling and
  break vendor neutrality and portability.

## Decision Drivers

### Primary Decision Drivers

1. **Vendor neutrality**: A document reference must not bind a bundle to any
   one parser, store, or product (ADR-010).
2. **Portability**: A referenced document must travel as a small, stable
   pointer — not a large embedded parse tree.
3. **Integrity & versioning**: Consumers must be able to verify the referenced
   bytes (`hash`) and detect drift (`version`, `byteLength`, `contentType`).

### Secondary Decision Drivers

1. **Consistency**: The construct should mirror the shape of existing
   references (`EntityReference`, `Citation`) — `@type` const,
   `additionalProperties: false`, namespaced custom-type escape hatch.
2. **Losslessness**: It must survive the Markdown ↔ JSON-LD round-trip
   (ADR-011) like every other frontmatter field.

## Considered Options

### Option 1: Embed a vendor document schema (issue #77 — DoclingDocument)

**Description**: Embed the full `DoclingDocument` object inside each memory.

**Advantages**:
- Rich parsed structure (layout, tables) available inline with zero extra
  fetch.

**Disadvantages**:
- Couples MIF to one vendor's object model; breaks vendor neutrality (ADR-010).
- Inflates every memory with a full parse tree; harms portability.
- Forces all conformant readers to understand a third-party schema.

**Risk Assessment**:
- **Technical Risk**: High. Vendor schema churn becomes MIF's problem.

### Option 2: Extend `Citation` with hash/contentType/version

**Description**: Add integrity/versioning fields to the existing `Citation`.

**Advantages**:
- Reuses an existing construct.

**Disadvantages**:
- `Citation` is `additionalProperties: false` and models bibliographic intent;
  overloading it with artifact metadata conflates two concerns.

**Risk Assessment**:
- **Technical Risk**: Medium. Semantic overload confuses producers and
  consumers.

### Option 3: Vendor-neutral `DocumentReference` carried by reference (chosen)

**Description**: Add a new `$defs.DocumentReference` and an optional top-level
`documents` array. Each entry is a small, vendor-neutral pointer: locate the
document by `url` or `id`, plus `documentType`, `contentType`, `byteLength`,
`version`, `retrievedAt`, and a `hash` `{algorithm, value}` for integrity.
`additionalProperties: false`; a namespaced custom `documentType` is the
extension escape hatch.

**Advantages**:
- Vendor-neutral and portable — a pointer, not an embedded parse tree.
- Carries integrity and drift-detection metadata `Citation` cannot.
- Mirrors existing reference constructs; round-trips losslessly.

**Disadvantages**:
- Consumers must fetch the document to access its content (by design).

**Risk Assessment**:
- **Technical Risk**: Low. Additive optional field; no vendor coupling.

## Decision

MIF carries source documents **by reference**. A new `$defs.DocumentReference`
defines a vendor-neutral pointer with `@type: "DocumentReference"`, located by
either `url` or `id` (enforced via `anyOf`), plus optional `documentType`,
`title`, `contentType`, `byteLength`, `version`, `retrievedAt`, and a `hash`
object (`{algorithm, value}`). It is `additionalProperties: false`, and
`documentType` accepts a namespaced custom value (`^[a-zA-Z][a-zA-Z0-9]*:[a-zA-Z][a-zA-Z0-9-]*$`)
as its extension point. A new optional top-level `documents` array holds these
references. MIF does **not** embed any vendor document schema (rejecting issue
#77's `DoclingDocument` embed); a producer that has a Docling parse may still
point at it as a `DocumentReference` like any other artifact.

## Consequences

### Positive

1. **Vendor neutrality preserved**: No bundle is coupled to a parser's object
   model.
2. **Integrity & drift detection**: `hash`, `version`, `byteLength`, and
   `contentType` let consumers verify and detect change.
3. **Portable & lossless**: Small pointers that survive the round-trip.

### Negative

1. **Indirection**: Document content is not inline; consumers fetch it.

### Neutral

1. **Convergence with Citation**: `documents` and `citations` can both appear;
   they model different concerns (artifact provenance vs. bibliographic intent).

## Decision Outcome

Source documents are now expressible as vendor-neutral references with
integrity metadata, without embedding any third-party schema. The construct is
additive and optional: existing bundles remain valid, and the round-trip and
schema gates (ADR-012) cover the new field.

## Related Decisions

- [ADR-006: EntityData vs EntityReference](ADR-006-entitydata-vs-entityreference.md) — the reference-over-inline preference this decision extends to documents.
- [ADR-009: OKF Compliance as a Superset](ADR-009-okf-compliance-superset.md) — `documents` is an additive MIF field over the OKF base.
- [ADR-010: Repositioning to Modeled Information Format](ADR-010-modeled-information-format-repositioning.md) — the vendor-neutral positioning that rules out an embedded vendor schema.

## Links

- [GitHub issue #77](https://github.com/modeled-information-format/MIF/issues/77) — the originating "embed DoclingDocument" proposal this ADR reframes as reference-not-embed.
- [IBM Docling](https://github.com/docling-project/docling) — the parser whose `DoclingDocument` model #77 proposed embedding; supported here as a referent, not a dependency.

## More Information

- **Date:** 2026-06-26
- **Source:** `schema/mif.schema.json` (`$defs.DocumentReference`, top-level `documents`); `schema/context.jsonld`; `scripts/mif_convert.py` (`FRONTMATTER_ORDER` + passthroughs).
- **Related ADRs:** ADR-006, ADR-009, ADR-010, ADR-012

## Audit

### 2026-06-26

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| `$defs.DocumentReference` is vendor-neutral, `@type` const, located by `url` or `id` via `anyOf`, `additionalProperties: false` | `schema/mif.schema.json` | `$defs.DocumentReference` | compliant |
| Optional top-level `documents` array references `#/$defs/DocumentReference` | `schema/mif.schema.json` | `properties.documents` | compliant |
| `documents` added to `FRONTMATTER_ORDER` and both passthrough lists | `scripts/mif_convert.py` | L64, L148, L192 | compliant |
| Context maps `documents`, `DocumentReference`, and DocumentReference fields | `schema/context.jsonld` | `documents`/`DocumentReference` block | compliant |
| Example carries a `documents:` entry that round-trips | `profiles/ai-memory/examples/level-3-citations.md` | `documents:` | compliant |

**Summary:** A vendor-neutral `DocumentReference` and optional `documents` array
were added; the converter round-trips the field; the JSON-LD context maps the
new terms. The round-trip, OKF, schema-compile, and projection gates were run
locally to green in this session.

**Action Required:** None.
