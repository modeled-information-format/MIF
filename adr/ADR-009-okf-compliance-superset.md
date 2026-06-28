---
title: "OKF Compliance as a Superset (Pinned OKF v0.1)"
description: "MIF achieves Open Knowledge Format compliance as a superset and pins OKF v0.1's criteria rather than tracking the upstream draft."
type: adr
category: architecture
tags:
  - okf
  - conformance
  - interoperability
  - positioning
  - governance
status: accepted
created: 2026-06-18
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - okf
  - json-ld
  - markdown
audience:
  - developers
  - architects
related:
  - ADR-010-modeled-information-format-repositioning.md
  - ADR-011-markdown-canonical-derived-jsonld.md
  - ADR-012-okf-conformance-tested-invariant.md
  - ADR-001-cognitive-triad-taxonomy.md
  - ADR-008-decay-model-rationale.md
---

# ADR-009: OKF Compliance as a Superset (Pinned OKF v0.1)

## Status

Accepted

## Context

### Background and Problem Statement

The Open Knowledge Format (OKF) defines a minimal interoperability surface — a
directory of `.md` files with YAML frontmatter, a single required `type` field,
a concept graph of standard markdown links, and the reserved filenames
`index.md` and `log.md`. OKF **deliberately refuses to define a content model**:
typed relationships, contradiction/merge semantics, trust tiers, provenance, and
stale-vs-live handling are all left as open design space.

MIF supplies exactly that missing content model. The architectural question is
*how* MIF should relate to OKF: should MIF subordinate itself to OKF (depending
on whatever OKF publishes next), or position itself as an independent
specification that remains interoperable with OKF?

### Current Limitations

- OKF is an evolving draft. A normative dependency on "OKF, latest" would make
  MIF's own conformance non-deterministic — an upstream edit could silently
  invalidate previously-conformant MIF bundles.
- Without an explicit relationship, "MIF is OKF-compatible" is an unverifiable
  marketing claim rather than a tested property.
- Consumers need to know which artifacts are OKF-legible (the `.md` concept
  files) and which are MIF-specific overlays (typed relationships, the JSON-LD
  projection), so a generic OKF reader is never confused by MIF extensions.

## Decision Drivers

### Primary Decision Drivers

1. **Determinism**: MIF conformance must be reproducible and not drift when the
   upstream OKF draft changes.
2. **Interoperability**: Every MIF bundle must be readable by a generic OKF
   consumer with no MIF-specific knowledge.
3. **Independence**: MIF must retain its own identity model, governance, and
   release cadence.

### Secondary Decision Drivers

1. **Auditability**: The OKF relationship should be machine-checkable, not
   prose-only.
2. **Forward compatibility**: Adopting a newer OKF revision should be a
   deliberate, reviewable act — never an accident.

## Considered Options

### Option 1: Subordinate MIF to OKF (normative dependency on the live draft)

**Description**: Treat the current upstream OKF document as normative; MIF
conformance is defined as "whatever OKF requires now, plus MIF additions."

**Technical Characteristics**:
- No pinned criteria; MIF defers to upstream wording.
- MIF releases would need to chase OKF revisions.

**Advantages**:
- Always "current" with OKF.
- No duplicated criteria text to maintain.

**Disadvantages**:
- Non-deterministic conformance: an upstream edit can break MIF bundles.
- MIF loses independent governance.
- Conformance cannot be pinned to a MIF version for reproducible validation.

**Risk Assessment**:
- **Technical Risk**: High. Validation results depend on an external moving
  target.
- **Schedule Risk**: High. MIF releases blocked on upstream cadence.
- **Ecosystem Risk**: Medium. Consumers cannot rely on a stable contract.

### Option 2: Fork OKF (define a MIF-only bundle shape, drop OKF legibility)

**Description**: Define MIF's own bundle shape and abandon the goal of generic
OKF readability.

**Advantages**:
- Maximum design freedom.

**Disadvantages**:
- Sacrifices the interoperability that motivates using OKF at all.
- A generic OKF consumer can no longer read MIF bundles.

**Risk Assessment**:
- **Technical Risk**: Low to build, High to the value proposition.
- **Ecosystem Risk**: High. Interoperability is the whole point; forking discards it.

### Option 3: Superset with a pinned OKF v0.1 (chosen)

**Description**: MIF is a strict superset of a conformant OKF bundle. MIF embeds
a *pinned copy* of OKF v0.1's conformance criteria (`docs/okf-conformance.md`),
normative within MIF, and takes **no** normative dependency on OKF's evolving
draft. Adopting a newer OKF revision requires an explicit MIF revision.

**Technical Characteristics**:
- Every MIF concept is a valid OKF concept; every typed MIF relationship also
  appears as a plain OKF-legible markdown link.
- The pinned criteria are frozen text, versioned with MIF.

**Advantages**:
- Deterministic, reproducible conformance tied to a MIF version.
- Generic OKF readers work unchanged.
- MIF keeps independent identity and governance.
- The relationship is testable (see ADR-012).

**Disadvantages**:
- The pinned criteria text must be deliberately updated to track future OKF.
- Slight duplication between upstream OKF and the pinned copy.

**Risk Assessment**:
- **Technical Risk**: Low. The contract is frozen and machine-checkable.
- **Schedule Risk**: Low. MIF releases are decoupled from upstream cadence.
- **Ecosystem Risk**: Low. Stable, documented contract for consumers.

## Decision

MIF achieves OKF compliance **as a superset, not by subordination**. Every MIF
bundle MUST validate as a conformant OKF bundle, but MIF remains an independent
specification with its own identity model and governance.

MIF takes **no normative dependency** on OKF's evolving draft. It pins OKF v0.1's
conformance criteria in `docs/okf-conformance.md`, which is **normative within
MIF** (SPECIFICATION.md, Invariant 5 — "No floating dependency on OKF"). A future
MIF revision MAY replace that pinned section with newer upstream text, but only
as a deliberate, reviewed act.

The superset relationship is made concrete by the MIF → OKF mapping
(`docs/okf-conformance.md §2`): concept files map to OKF concepts, the
frontmatter `type` satisfies OKF's required field, typed `relationships[]` are a
MIF overlay on plain OKF markdown-link edges, and the JSON-LD projection uses the
`.jsonld` extension so it falls outside OKF's `*.md` glob.

## Consequences

### Positive

1. **Deterministic conformance**: Validation is reproducible against a frozen
   criteria set tied to the MIF version.
2. **Generic interoperability**: A plain OKF consumer reads every MIF bundle
   without MIF-specific code.
3. **Independent governance**: MIF evolves on its own cadence; OKF adoption is
   explicit.
4. **Testable claim**: "OKF-compliant" becomes a CI-enforced invariant
   (see ADR-012), not marketing.

### Negative

1. **Maintenance of pinned text**: Tracking a future OKF version is a manual,
   deliberate revision.
2. **Apparent duplication**: The pinned criteria restate the upstream surface.

### Neutral

1. **Two artifact classes**: `.md` concepts are OKF-legible; the `.jsonld`
   projection and typed-relationship overlay are MIF-only — by design.

## Decision Outcome

The superset-with-pinned-v0.1 approach achieves the primary drivers:
determinism (frozen criteria), interoperability (generic OKF legibility), and
independence (own governance). Mitigations:

- The "no floating dependency" rule (Invariant 5) is documented at the top of
  `docs/okf-conformance.md` and in SPECIFICATION.md's Abstract.
- The relationship is enforced mechanically by `scripts/okf_validate.py` and the
  lossless round-trip, gated in CI (ADR-012).

## Related Decisions

- [ADR-010: Repositioning to Modeled Information Format](ADR-010-modeled-information-format-repositioning.md) — establishes MIF's independent identity that this superset relationship presupposes.
- [ADR-011: Markdown-Canonical with Derived JSON-LD](ADR-011-markdown-canonical-derived-jsonld.md) — the `.jsonld` projection stays outside OKF's `*.md` surface.
- [ADR-012: OKF Conformance as a Tested Invariant](ADR-012-okf-conformance-tested-invariant.md) — makes this decision machine-checkable.
- [ADR-001: Cognitive Triad Taxonomy](ADR-001-cognitive-triad-taxonomy.md) — the base-type taxonomy is MIF's answer to OKF's deliberately-absent concept-type system.
- [ADR-008: Decay Model Rationale](ADR-008-decay-model-rationale.md) — validity/freshness is MIF's answer to OKF's open "stale-vs-live" question.

## Links

- [`docs/okf-conformance.md`](../docs/okf-conformance.md) — the pinned OKF v0.1 conformance criteria, normative within MIF (the authoritative source; upstream OKF wording is reconstructed/frozen here per that document's provenance note).

## More Information

- **Date:** 2026-06-18
- **Source:** SPECIFICATION.md Abstract ("MIF answers OKF's open questions") and Invariant 5; `docs/okf-conformance.md`.
- **Related ADRs:** ADR-010, ADR-011, ADR-012, ADR-001, ADR-008

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Superset-not-subordination and "no normative dependency / pin OKF v0.1" stated normatively | `SPECIFICATION.md` | L29-L34 | compliant |
| Invariant 5 ("normative within MIF") pinned criteria document present | `docs/okf-conformance.md` | L3-L19 | compliant |
| Pinned OKF v0.1 criteria enumerated (bundle shape, required `type`, reserved filenames, concept graph, broken-links-tolerated) | `docs/okf-conformance.md` | L25-L41 | compliant |
| MIF → OKF mapping (typed relationships overlay OKF links; `.jsonld` outside `*.md` glob) | `docs/okf-conformance.md` | L52-L65 | compliant |
| "MIF answers OKF's open questions" positioning table | `SPECIFICATION.md` | L49-L57 | compliant |

**Summary:** The superset relationship, the pinned-v0.1 / no-floating-dependency
rule (Invariant 5), and the MIF→OKF mapping are all present and normative in the
specification and the pinned conformance document.

**Action Required:** None.
