---
title: "Decay Model Rationale (Configurable Temporal Freshness)"
description: "MIF models knowledge freshness with a configurable decay function — none/linear/exponential/step over an ISO-8601 half-life — as its opinionated answer to OKF's open stale-vs-live question."
type: adr
category: architecture
tags:
  - temporal
  - decay
  - freshness
  - relevance
status: accepted
created: 2026-01-27
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - iso-8601
audience:
  - developers
  - architects
related:
  - ADR-001-cognitive-triad-taxonomy.md
  - ADR-009-okf-compliance-superset.md
---

# ADR-008: Decay Model Rationale (Configurable Temporal Freshness)

## Status

Accepted

## Context

### Background and Problem Statement

A modeled-information bundle accumulates knowledge whose currency erodes at
different rates. Consumers of a MIF bundle need mechanisms to:

- Prioritize recent and relevant knowledge over aged knowledge.
- Express that some facts go stale quickly while others remain durable.
- Bound storage growth so that low-value, decayed entries can be reclaimed.
- Distinguish *freshness* (how current a fact is) from *validity* (the interval
  in which a fact is asserted to hold).

The exponential-decay curve has an established analogue in the cognitive-science
account of human memory, where retained items lose strength over time unless
reinforced. That analogue supplies an intuitive, well-understood mental model for
relevance ranking, but the *core* MIF model frames the function purely as
freshness — the cognitive-memory framing now lives in the AI Memory profile.

### Current Limitations

- OKF defines a directory of `.md` concept files but **deliberately leaves
  stale-vs-live handling to the consuming process** — it offers no freshness or
  validity model at all.
- Without a content-model answer, "is this knowledge still current?" is a
  question every consumer must re-invent, with no interoperable contract.
- A single fixed decay rate cannot serve both fast-moving episodic records and
  slow-moving semantic facts; the model must be configurable per entry and per
  kind.

## Decision Drivers

### Primary Decision Drivers

1. **Freshness semantics**: The temporal model must express how current a piece
   of knowledge is, independent of whether it is still valid.
2. **Configurability**: Decay behavior must be selectable per entry (model +
   half-life) so different knowledge kinds decay appropriately.
3. **OKF gap-filling**: Decay/validity is MIF's opinionated answer to OKF's open
   stale-vs-live question; it must be a concrete, documented contract.

### Secondary Decision Drivers

1. **Storage management**: Decayed, low-strength entries should become candidates
   for archival, compression, or deletion.
2. **Reinforcement**: Access or explicit reinforcement should be able to reset or
   slow decay, mirroring a familiar mental model.
3. **Standards alignment**: Durations use ISO-8601 so half-lives and TTLs are
   unambiguous and portable.

## Considered Options

### Option 1: No temporal model (defer stale-vs-live to the consumer, as OKF does)

**Description**: Carry no decay or freshness data; leave every consumer to decide
whether a fact is still current.

**Advantages**:

- Minimal surface; nothing to specify or validate.
- Matches OKF's bare interoperability surface exactly.

**Disadvantages**:

- Re-creates the OKF gap MIF exists to fill — no interoperable freshness contract.
- Relevance ranking and garbage collection have no shared basis.

**Risk Assessment**:

- **Technical Risk**: Low to build, but high to the value proposition — the
  content model is the reason to adopt MIF over bare OKF.
- **Ecosystem Risk**: High. Every consumer diverges on staleness handling.

### Option 2: A single fixed decay rate

**Description**: Apply one global exponential decay with a fixed half-life to all
entries.

**Advantages**:

- Simple to implement and reason about.

**Disadvantages**:

- One rate cannot fit both fast-moving events and durable facts.
- No way to mark a fact permanent or to model hard expiration.

**Risk Assessment**:

- **Technical Risk**: Low.
- **Ecosystem Risk**: Medium. Forces a single tuning onto every knowledge kind.

### Option 3: A configurable decay model (chosen)

**Description**: A per-entry decay object selects one of four models
(`none` / `linear` / `exponential` / `step`) over an ISO-8601 `halfLife`, with a
`currentStrength` in `[0,1]`. Default half-lives differ by knowledge kind, access
can reinforce an entry, and weak entries become reclamation candidates.

**Technical Characteristics**:

- Decay object lives under `temporal`, alongside `validFrom` / `validUntil` /
  `recordedAt` / `ttl`, separating freshness from the validity window.
- The freshness curve `strength = e^(-t/halfLife)` is fully current at record
  time and decays gradually toward stale.

**Advantages**:

- Per-entry and per-kind tuning; `none` supports permanent knowledge.
- Directly answers OKF's open stale-vs-live question with a concrete contract.
- Reinforcement and garbage-collection behaviors fall out naturally.

**Disadvantages**:

- Adds management complexity (background decay calculation, tuning).
- Mis-tuned half-lives can deprecate still-important knowledge.

**Risk Assessment**:

- **Technical Risk**: Low. The fields are bounded and schema-validated.
- **Schedule Risk**: Low. The model shipped in v1.0.0.
- **Ecosystem Risk**: Low. A documented, machine-checkable freshness contract.

## Decision

Implement a **configurable decay model** under the `temporal` object.

### Decay Types

```yaml
decay:
  model: "exponential"  # none | linear | exponential | step
  halfLife: "P14D"      # ISO 8601 duration
  currentStrength: 0.85 # 0.0-1.0
```

### Supported Models

1. **none** — Knowledge never decays (permanent).
2. **linear** — Strength decreases at a constant rate.
3. **exponential** — Strength follows an exponential decay curve.
4. **step** — Strength drops at a defined threshold (hard expiration).

### Default Half-Lives by Knowledge Kind

| Knowledge Kind | Default Half-Life | Rationale |
|----------------|-------------------|-----------|
| Semantic | P30D (30 days) | Facts change slowly |
| Episodic | P7D (7 days) | Events become less relevant |
| Procedural | P14D (14 days) | Processes need periodic refresh |

### Reinforcement

Accessing or explicitly reinforcing an entry resets decay:

```yaml
temporal:
  last_accessed: "2026-01-27T10:00:00Z"
  access_count: 5
  last_reinforced: "2026-01-25T15:00:00Z"
```

### Garbage Collection Threshold

Entries with `currentStrength < 0.1` are candidates for archival (move to cold
storage), compression (reduce to summary), or deletion (with user consent).

### Relationship to OKF

Decay/validity is MIF's opinionated answer to OKF's deliberately-open
stale-vs-live question. In the "MIF answers OKF's open questions" table,
"Stale-vs-live left to process" is answered by "Validity windows + TTL/freshness."
The decay function expresses freshness; the `validFrom`/`validUntil` window bounds
the interval in which a fact is asserted to hold. This is the same superset
posture ADR-009 establishes: MIF supplies the content model OKF leaves open.

## Consequences

### Positive

- Automatic relevance ranking based on recency.
- Storage management via garbage collection of weak entries.
- Mirrors a familiar mental model (decay-and-reinforce).
- Configurable per entry and per kind.
- Supports permanent knowledge via `model: none`.
- Provides the interoperable freshness contract OKF lacks.

### Negative

- Adds complexity to bundle management.
- Requires background decay calculation.
- May accidentally deprecate important knowledge if mis-tuned.
- Tuning half-lives requires experimentation.

### Neutral

- Freshness (decay) and validity (`validFrom`/`validUntil`) are separate
  concerns carried in the same `temporal` object — by design.
- The cognitive-memory origin of the exponential curve is retained as rationale
  but moved to the AI Memory profile, keeping the core framed as freshness.

## Decision Outcome

The configurable-decay approach achieves the primary drivers: freshness semantics
(the `e^(-t/halfLife)` curve), configurability (four models over a per-entry
half-life), and OKF gap-filling (a concrete stale-vs-live contract). Mitigations:

- Default half-lives are documented as **pragmatic, non-prescriptive** defaults
  that implementations SHOULD tune by knowledge kind, organizational velocity,
  and access patterns.
- Reinforcement (`lastAccessed` / `accessCount`) lets implementations slow or
  reset decay so frequently-used knowledge is not prematurely deprecated.

## Implementation Notes

### Decay Calculation

```math
currentStrength = initialStrength * (0.5 ^ (elapsed / halfLife))
```

> **Note:** The canonical half-life formula is `0.5^(t/halfLife)`. The
> specification's `e^(-t/halfLife)` is the natural exponential decay form. For
> true half-life behavior (strength = 0.5 when t = halfLife), use:
> `e^(-ln(2) * t / halfLife)` which equals `0.5^(t/halfLife)`.

### Garbage Collection Threshold

Entries with `currentStrength < 0.1` are candidates for:

- Archival (move to cold storage)
- Compression (reduce to summary)
- Deletion (with user consent)

### Reinforcement Triggers

- Direct access (read)
- Explicit reinforcement command
- Citation by other entries
- User interaction referencing the entry

## Related Decisions

- [ADR-001: Cognitive Triad Taxonomy](ADR-001-cognitive-triad-taxonomy.md) — default decay half-lives differ by base type (semantic, episodic, procedural).
- [ADR-009: OKF Compliance as a Superset](ADR-009-okf-compliance-superset.md) — decay/validity is MIF's answer to OKF's open stale-vs-live question; this ADR is one row of the "MIF answers OKF's open questions" table.

## Links

- [ISO 8601 Date and Time Format](https://www.iso.org/iso-8601-date-and-time-format.html) — the duration syntax used for `halfLife` and `ttl`.

## More Information

- **Date:** 2026-01-27
- **Source:** SPECIFICATION.md §9 (Temporal Model) and the "MIF answers OKF's open questions" table; `schema/mif.schema.json` (`temporal.decay`).
- **Related ADRs:** ADR-001, ADR-009

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Temporal Model section exists; `decay` is a temporal property alongside `validFrom`/`validUntil`/`recordedAt`/`ttl` | `SPECIFICATION.md` | L1117-L1134 | compliant |
| Four decay models enumerated (none/linear/exponential/step) with `exponential` = `e^(-t/halfLife)` | `SPECIFICATION.md` | L1136-L1143 | compliant |
| Freshness rationale: decay answers OKF's open "live vs. stale" question; defaults P7D/P14D/P30D are non-prescriptive; reinforcement via `lastAccessed`/`accessCount` | `SPECIFICATION.md` | L1145-L1172 | compliant |
| Cognitive-memory origin moved to AI Memory profile; core framed as freshness | `SPECIFICATION.md` | L1174-L1179 | compliant |
| "MIF answers OKF's open questions" table: "Stale-vs-live left to process" → "Validity windows + TTL/freshness" | `SPECIFICATION.md` | L49-L55 | compliant |
| Abstract states MIF supplies "validity/freshness semantics" as its OKF content-model fill | `SPECIFICATION.md` | L18-L22 | compliant |
| Schema `temporal.decay`: `model` enum [none, linear, exponential, step], `halfLife` (pattern `^P`), `currentStrength` (0-1), `lastReinforced` | `schema/mif.schema.json` | L297-L325 | compliant |
| JSON-LD context terms `decay`, `model`, `halfLife` (xsd:duration), `currentStrength` (xsd:decimal), `lastReinforced` | `schema/context.jsonld` | L158-L169 | compliant |
| GC threshold `currentStrength < 0.1` is an ADR-level decision; spec defines a related compression trigger at `Strength < 0.3 AND content > 100 lines`, not a 0.1 GC threshold | `SPECIFICATION.md` | L604-L605 | partial |

**Summary:** The configurable decay model, its four models, the ISO-8601
half-life, the per-kind defaults, reinforcement, and the OKF stale-vs-live
linkage are all present and normative in SPECIFICATION.md, `mif.schema.json`, and
`context.jsonld`. The `currentStrength < 0.1` garbage-collection threshold is an
ADR-level operational decision and is not stated verbatim in the specification —
the closest spec text is the `Strength < 0.3` compression trigger (a different
threshold for a different action), so that one finding is marked `partial`.

**Action Required:** None for the decision itself. If the `< 0.1` GC threshold is
intended to be normative, it should be added to SPECIFICATION.md §5.6 alongside
the existing compression criteria.
