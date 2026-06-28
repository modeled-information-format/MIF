---
title: "Markdown-Canonical with Derived JSON-LD Projection"
description: "The Markdown .md file is MIF's single source of truth; the JSON-LD form is a derived, emitted projection that uses the .jsonld extension and round-trips losslessly. Refines ADR-002's co-equal dual-format framing."
type: adr
category: architecture
tags:
  - markdown
  - json-ld
  - canonical
  - projection
  - lossless
status: accepted
created: 2026-06-18
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - markdown
  - json-ld
audience:
  - developers
  - architects
related:
  - ADR-002-dual-format-design.md
  - ADR-009-okf-compliance-superset.md
  - ADR-007-github-raw-urls-for-schema-ids.md
  - ADR-012-okf-conformance-tested-invariant.md
---

# ADR-011: Markdown-Canonical with Derived JSON-LD Projection

## Status

Accepted

This ADR **refines and amends ADR-002 (Dual Format Design)**. ADR-002 introduced
Markdown and JSON-LD as two first-class formats and described them as "semantically
equivalent and bidirectionally convertible" — a co-equal framing. ADR-011 narrows
that relationship: the Markdown `.md` file is the **single canonical source of
truth**, and JSON-LD is a **derived projection** emitted from it (Invariant 2).
ADR-002 is not superseded — its motivation for serving both a human-readable and a
machine-processable form still holds — but its co-equal/bidirectional-authoring
characterization is corrected here. The amendment is also recorded in
`## Related Decisions`.

## Context

### Background and Problem Statement

MIF serves two audiences from one artifact: a human reading or editing a memory in
a Markdown editor, and a machine consuming a structured, semantic-web-legible form.
ADR-002 established that MIF supports both Markdown and JSON-LD and treated them as
co-equal, bidirectionally-convertible representations of the same memory.

Co-equality leaves one question unanswered: **when the two representations
disagree, which one is correct?** If both can be authored independently, nothing
designates a winner. In practice MIF must also stay OKF-legible — OKF ingests a
directory of `.md` concept files via a `*.md` glob (see ADR-009) — so the
serialized JSON form cannot share the `.md` extension without being misread as a
concept. The architectural question is therefore: which format is canonical, how is
the other produced, and what extension does the projection use?

### Current Limitations

- **Conflict ambiguity**: Under co-equal dual authoring, a Markdown edit and a
  JSON-LD edit can diverge with no rule for which wins, producing silent drift
  between two "authoritative" copies of one memory.
- **OKF glob collision**: A JSON-LD form written as `*.md` would be swept into
  OKF's concept glob and misparsed as a concept file (ADR-009).
- **Unverifiable equivalence**: "Bidirectionally convertible" is only a safe claim
  if conversion is proven lossless; without a checked round-trip it is an
  assertion, not a guarantee.

## Decision Drivers

### Primary Decision Drivers

1. **Single source of truth**: Exactly one representation must be authoritative so
   that conflicts have a deterministic resolution.
2. **Lossless projection**: The derived form must lose nothing — the
   `markdown → json-ld → markdown` round-trip must reproduce the original.
3. **OKF legibility**: The projection must stay outside OKF's `*.md` concept glob
   so a generic OKF reader never ingests it (ADR-009).

### Secondary Decision Drivers

1. **Human authoring ergonomics**: Authors should edit the familiar, readable form,
   not hand-maintain a structured serialization.
2. **Auditability**: The canonical/derived relationship should be machine-checkable
   rather than asserted in prose (enforced as a tested invariant — see ADR-012).

## Considered Options

### Option 1: Co-equal dual authoring (the original ADR-002 framing)

**Description**: Treat Markdown and JSON-LD as two first-class, independently
authorable representations that are "semantically equivalent and bidirectionally
convertible." Either may be edited; both are authoritative.

**Technical Characteristics**:
- No designated source of truth; both forms are hand-maintainable.
- Conversion must be maintained in both directions with format parity.

**Advantages**:
- Maximum flexibility: a producer may emit whichever form it prefers.
- Matches the most literal reading of "dual format."

**Disadvantages**:
- No conflict-resolution rule: a Markdown edit and a JSON-LD edit can diverge with
  no winner, yielding silent drift between two authoritative copies.
- "Format parity" becomes a perpetual maintenance burden across two authored forms.
- Equivalence is asserted, not verified — nothing forces conversion to be lossless.

**Risk Assessment**:
- **Technical Risk**: High. Two authoritative copies drift; reconciliation is
  undefined.
- **Schedule Risk**: Medium. Maintaining bidirectional parity across two authored
  forms is ongoing cost.
- **Ecosystem Risk**: Medium. Consumers cannot know which copy to trust on conflict.

### Option 2: Markdown-canonical with a derived JSON-LD projection (chosen)

**Description**: The Markdown `.md` file is the single source of truth. The JSON-LD
form is a **derived projection**, always emitted from the `.md` source and never
hand-authored. The projection uses the `.jsonld` extension (never `.md`) so OKF's
`*.md` concept glob never ingests it. The `markdown → json-ld → markdown` round-trip
is lossless, which is what guarantees the projection drops nothing; the round-trip
is checked mechanically (ADR-012). On any disagreement, markdown wins.

**Technical Characteristics**:
- One direction of authorship: humans edit `.md`; the projection is regenerated by
  `scripts/mif_convert.py emit-jsonld`.
- The `.jsonld` extension keeps the projection outside OKF's concept surface.
- Losslessness is a checked property (`scripts/mif_convert.py roundtrip`), not an
  assumption.

**Advantages**:
- Deterministic conflict resolution: markdown is authoritative; there is no
  ambiguity about which copy wins.
- The projection is disposable and reproducible — it can always be regenerated.
- Lossless round-trip makes "convertible" a tested guarantee, not a claim.
- `.jsonld` keeps OKF legibility intact (ADR-009).

**Disadvantages**:
- The projection must be regenerated when the source changes; a stale committed
  projection would be out of date (mitigated by emitting it rather than authoring
  it, and by the CI round-trip gate).

**Risk Assessment**:
- **Technical Risk**: Low. One authoritative source; losslessness is checked.
- **Schedule Risk**: Low. The projection is generated, not separately maintained.
- **Ecosystem Risk**: Low. Stable rule (markdown wins) and a non-`.md` extension
  that OKF readers ignore.

### Option 3: JSON-LD-canonical with rendered Markdown

**Description**: Make JSON-LD the source of truth and render the Markdown `.md` file
from it for human reading.

**Technical Characteristics**:
- Authors would edit JSON-LD; Markdown becomes a generated view.
- The OKF-legible `.md` concept file would be a derived artifact.

**Advantages**:
- A structured, validatable source of truth.
- Clean mapping to semantic-web tooling at the authoritative layer.

**Disadvantages**:
- Inverts MIF's human-first ergonomics: authors would hand-edit JSON-LD rather than
  Markdown, the opposite of the workflow ADR-002 set out to support.
- The OKF-legible concept file (`.md`) becomes a derived render of a non-OKF source,
  weakening the "every concept is an authored OKF concept" story (ADR-009).
- Rendering Markdown faithfully (Obsidian-compatible notes) from JSON-LD is harder
  than emitting JSON-LD from Markdown.

**Risk Assessment**:
- **Technical Risk**: Medium. Markdown rendering fidelity is the hard direction.
- **Schedule Risk**: Medium. Reworks the authoring model away from Markdown.
- **Ecosystem Risk**: Medium. The OKF surface becomes derived rather than authored.

## Decision

The Markdown `.md` file is MIF's **single canonical source of truth**. The JSON-LD
form is a **derived projection**: it is **emitted** from the `.md` source and is
**never hand-authored** (Invariant 2). On any disagreement between the two,
**markdown wins**.

The projection MUST use the `.jsonld` extension and MUST NOT use the `.md`
extension, so OKF's `*.md` concept glob never ingests it (consistent with ADR-009).

The projection MUST round-trip losslessly: `markdown → json-ld → markdown` must
reproduce the original markdown. This lossless round-trip is precisely what
guarantees the projection loses nothing. The relationship is mechanical, not
prose-only: `scripts/mif_convert.py emit-jsonld` performs the one-directional derive
(it reads each concept `.md` and writes a `.jsonld` projection), and
`scripts/mif_convert.py roundtrip` asserts the lossless round-trip over a bundle.
That round-trip is enforced as a tested invariant in CI (see ADR-012).

This refines ADR-002: the two formats remain available, but they are no longer
co-equal — one is canonical and the other is its derived projection.

## Consequences

### Positive

1. **Deterministic conflicts**: Markdown is authoritative; "which file wins?" has a
   fixed answer.
2. **Reproducible projection**: The `.jsonld` form can always be regenerated from
   source and is safe to treat as disposable.
3. **Tested losslessness**: Lossless round-trip is a checked property, turning
   "bidirectionally convertible" into a guarantee (ADR-012).
4. **Preserved OKF legibility**: The `.jsonld` extension keeps the projection
   outside OKF's `*.md` concept surface (ADR-009).

### Negative

1. **Regeneration discipline**: The projection must be re-emitted when the source
   changes; a stale committed `.jsonld` would drift from its source (mitigated by
   emitting rather than authoring it, and by the CI round-trip gate).

### Neutral

1. **Two artifacts, one source**: Both a `.md` and a `.jsonld` form exist per
   concept, but only the `.md` is authored — the `.jsonld` is a view of it.

## Decision Outcome

Markdown-canonical with a derived JSON-LD projection satisfies the primary drivers:
a single source of truth (markdown wins), lossless projection (a checked round-trip),
and OKF legibility (the `.jsonld` extension stays outside the `*.md` glob).
Mitigations:

- The canonical rule is documented at the top of the JSON-LD section in
  SPECIFICATION.md ("Markdown is canonical (Invariant 2)... If the two disagree,
  markdown wins") and in the spec's design-goals summary (Invariant 2).
- The derive is one-directional and reproducible via
  `scripts/mif_convert.py emit-jsonld`; losslessness is asserted by
  `scripts/mif_convert.py roundtrip` and gated in CI (ADR-012).

## Related Decisions

- [ADR-002: Dual Format Design (Markdown + JSON-LD)](ADR-002-dual-format-design.md) — **refined/amended by this ADR**: ADR-002 framed Markdown and JSON-LD as co-equal and bidirectionally convertible; ADR-011 designates Markdown canonical and JSON-LD a derived projection.
- [ADR-009: OKF Compliance as a Superset](ADR-009-okf-compliance-superset.md) — the `.jsonld` extension keeps the projection outside OKF's `*.md` concept glob.
- [ADR-007: GitHub Raw URLs for Schema IDs](ADR-007-github-raw-urls-for-schema-ids.md) — the derived JSON-LD projection carries the resolvable `@context`/schema `$id` URIs.
- [ADR-012: OKF Conformance as a Tested Invariant](ADR-012-okf-conformance-tested-invariant.md) — makes the lossless round-trip a CI-enforced check rather than an assertion.

## Links

- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) — the projection format MIF derives from canonical Markdown.

## More Information

- **Date:** 2026-06-18
- **Source:** SPECIFICATION.md L38-L39 (Markdown-canonical / Invariant 2) and §6 "JSON-LD Projection (derived)" L624-L629; `scripts/mif_convert.py` (`emit-jsonld`, `roundtrip`).
- **Related ADRs:** ADR-002, ADR-009, ADR-007, ADR-012

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Markdown-canonical stated normatively: ".md file is the source of truth; JSON-LD is a derived projection (Invariant 2)" | `SPECIFICATION.md` | L38-L39 | compliant |
| JSON-LD section titled "JSON-LD Projection (derived)" and callout "Markdown is canonical (Invariant 2)... If the two disagree, markdown wins" | `SPECIFICATION.md` | L624-L629 | compliant |
| Projection MUST NOT use the `.md` extension so OKF's `*.md` glob never ingests it; MUST round-trip losslessly | `SPECIFICATION.md` | L628-L629 | compliant |
| One-directional derive: `emit-jsonld` reads each concept `.md` and writes a `.jsonld` projection (never hand-authored) | `scripts/mif_convert.py` | L267-L279 | compliant |
| Lossless `markdown → json-ld → markdown` round-trip asserted by the `roundtrip` subcommand | `scripts/mif_convert.py` | L201-L213 | compliant |
| `roundtrip` and `emit-jsonld` registered as CLI subcommands | `scripts/mif_convert.py` | L294-L297 | compliant |

**Summary:** The Markdown-canonical / derived-JSON-LD relationship (Invariant 2),
the `.jsonld` (never `.md`) extension rule, the lossless round-trip requirement, and
the one-directional `emit-jsonld` derive plus the `roundtrip` losslessness assertion
are all present and normative in the specification and the conversion tooling.

**Action Required:** None.
