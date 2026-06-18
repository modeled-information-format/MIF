---
title: "Repositioning to Modeled Information Format"
description: "MIF is repositioned from a memory-centric interchange format to a general OKF-compliant content model; AI memory becomes the first domain profile rather than MIF's identity."
type: adr
category: architecture
tags:
  - positioning
  - naming
  - profiles
  - okf
  - scope
status: accepted
created: 2026-06-18
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - okf
  - markdown
  - json-ld
audience:
  - developers
  - architects
  - adopters
related:
  - ADR-009-okf-compliance-superset.md
  - ADR-001-cognitive-triad-taxonomy.md
---

# ADR-010: Repositioning to Modeled Information Format

## Status

Accepted

This decision shipped in MIF v1.0.0. It is the positioning that ADR-009 (OKF
compliance as a superset) presupposes: that decision describes how MIF's
*independent identity* relates to OKF, and that independent identity is
established here.

## Context

### Background and Problem Statement

Prior to v1.0.0, MIF stood for **Memory Interchange Format**. Its identity was
memory-centric: the format existed to serialize and interchange the persistent
memory of AI agents, and its concept files carried a `.memory.md` infix with
`.memory.json` sidecars. The cognitive vocabulary (semantic / episodic /
procedural memory, the forgetting curve, decay) was the spine of the format
itself, not an application of a more general model.

In practice the mechanisms MIF defined were not memory-specific. A typed
relationship graph, provenance and trust tiers, validity windows and freshness,
contradiction and supersession semantics, and a Markdown-canonical /
JSON-LD-derived projection are all general knowledge-modeling concerns. AI
memory is one important *consumer* of those mechanisms, not their definition.
Naming the whole format after a single application understated its scope and
coupled the format's identity to one domain's vocabulary.

The architectural question for v1.0.0 was therefore one of identity and scope:
*what is MIF, fundamentally?* — a memory format that happens to be general, or a
general content model whose first worked application happens to be memory.

### Current Limitations

- The "Memory Interchange Format" name advertised a narrower scope than the
  format actually delivered, discouraging adoption for non-memory knowledge
  modeling (catalogs, documentation graphs, domain ontologies).
- Memory-specific vocabulary was woven into the core, leaving no clean seam
  between the general model and a domain's interpretation of it.
- Without a designated extension mechanism, every new domain would have had to
  fork or reinterpret the core rather than layer on top of it.
- The repositioning ADR-009 depends on — MIF as an *independent* specification
  that is OKF-compliant by superset — had no documented identity to point to.

## Decision Drivers

### Primary Decision Drivers

1. **Scope honesty**: the format's name and identity must match what it
   actually models — general agent-readable knowledge, not only memory.
2. **Extensibility seam**: there must be a clean boundary between the general
   model and any single domain's interpretation, so domains layer on rather
   than fork.
3. **Independent identity**: MIF must have a stable, domain-neutral identity that
   the OKF-superset relationship (ADR-009) can presuppose.

### Secondary Decision Drivers

1. **Adoption surface**: a general content model invites a broader set of
   adopters than a memory-only interchange format.
2. **Proof of the extension model**: the repositioning is only credible if at
   least one real domain profile demonstrates that the seam works.

## Considered Options

### Option 1: Keep "Memory Interchange Format" / memory-centric identity

**Description**: Retain the original name and keep AI memory as MIF's defining
identity. General-purpose use remains an implicit, undocumented possibility.

**Technical Characteristics**:
- Cognitive vocabulary stays in the core as first-class identity.
- No formal profile layer; domain reuse is ad hoc.

**Advantages**:
- Established name with existing recognition; no rebrand cost or churn.
- Narrow, immediately legible scope — adopters know exactly what it is for.
- No need to disentangle memory vocabulary from the core.

**Disadvantages**:
- The name understates the format's actual generality, suppressing non-memory
  adoption.
- No clean seam between general model and domain interpretation; new domains
  must reinterpret or fork the core.
- Provides no domain-neutral identity for the OKF-superset relationship to rest
  on.

**Risk Assessment**:
- **Technical Risk**: Low to keep; the format works.
- **Schedule Risk**: Low. No work required.
- **Ecosystem Risk**: Medium. Misnaming caps the addressable use cases and
  entangles core evolution with one domain's vocabulary.

### Option 2: Reposition to "Modeled Information Format" with AI memory as a profile (chosen)

**Description**: Re-expand the acronym to **Modeled Information Format**. MIF's
identity becomes a general, opinionated, OKF-compliant content model for
agent-readable knowledge. AI memory is demoted from MIF's identity to its
**first domain profile** (`profiles/ai-memory/`), which builds on the core
without changing it.

**Technical Characteristics**:
- The core specification frames mechanisms in neutral knowledge-management terms.
- A domain profile is a normative overlay: it adds entity types, traits,
  defaults, and rationale on top of the `mif-base` model, and everything in the
  core applies unchanged.
- The AI-memory profile keeps the original cognitive-memory rationale (e.g. the
  forgetting curve) as a *domain* interpretation of a neutral core mechanism
  (e.g. validity windows and freshness).

**Advantages**:
- Name matches actual scope; broadens the adoption surface beyond memory.
- Establishes a clean, reusable profile seam — domains layer on, never fork.
- Gives MIF the domain-neutral identity that ADR-009's superset relationship
  presupposes.
- Ships a worked profile that proves the extension model rather than asserting
  it.

**Disadvantages**:
- One-time rebrand cost: name, narrative, and migration of existing bundles.
- Requires disentangling memory vocabulary from the core into the profile.

**Risk Assessment**:
- **Technical Risk**: Low. The mechanisms are unchanged; this is a
  re-layering and renaming, validated by an existing profile.
- **Schedule Risk**: Low. Delivered within the v1.0.0 release.
- **Ecosystem Risk**: Low. The profile model preserves all memory use cases
  while opening the format to new domains.

### Option 3: Generic format with no reference profile

**Description**: Generalize MIF to a domain-neutral content model but ship no
worked domain profile — leave AI memory (and every other domain) as future,
externally-defined extensions.

**Technical Characteristics**:
- Core model only; the profile mechanism is described but unexercised.

**Advantages**:
- Maximally neutral core, unburdened by any single domain's vocabulary.
- Smallest core surface to maintain.

**Disadvantages**:
- No proof the extension model actually works — a profile seam that nothing
  uses is unvalidated.
- Abandons MIF's strongest, most-developed use case (AI memory) instead of
  carrying it forward as the canonical example.
- Leaves adopters without a reference to model their own profiles on.

**Risk Assessment**:
- **Technical Risk**: Medium. An unexercised extension seam may not survive
  contact with a real domain.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: High. Adoption stalls without a worked example;
  credibility of the "general model" claim is unproven.

## Decision

MIF is repositioned as the **Modeled Information Format**: a general,
opinionated, OKF-compliant content model for agent-readable knowledge. AI memory
is **not** MIF's identity; it is MIF's **first domain profile**, located at
`profiles/ai-memory/` and layered on top of the core `mif-base` model.

The core specification defines the general model — the `.md` / JSON-LD knowledge
representation, namespaces, the temporal model, embeddings, provenance, and typed
relationships — in domain-neutral terms. A domain profile is a normative overlay
that adds entity types, traits, defaults, and rationale; everything in the core
applies to the profile unchanged. The AI-memory profile re-interprets neutral
core mechanisms (e.g. validity windows and freshness) with their original
cognitive rationale (e.g. the forgetting curve), demonstrating the seam works.

This is the independent identity that ADR-009 presupposes: MIF is OKF-compliant
as a superset *because* MIF is its own specification with its own scope — a scope
this repositioning makes explicit.

## Consequences

### Positive

1. **Scope-accurate identity**: the name and abstract describe a general content
   model, matching what MIF actually delivers.
2. **Reusable profile seam**: domains extend the base without forking; the
   AI-memory profile is the reference pattern.
3. **Foundation for ADR-009**: the OKF-superset relationship now rests on a
   stated, domain-neutral identity.
4. **Preserved memory use case**: nothing about AI memory is lost — it is carried
   forward as the canonical first profile.

### Negative

1. **Rebrand churn**: the acronym expansion, narrative, and existing bundles
   required migration (handled by the v1.0.0 migration tooling).
2. **Two layers to keep coherent**: the core must stay domain-neutral while the
   profile carries the domain vocabulary, an ongoing editorial discipline.

### Neutral

1. **Cognitive vocabulary relocates, it does not disappear**: semantic /
   episodic / procedural and the forgetting-curve rationale move from the core's
   identity into the AI-memory profile's interpretation of neutral mechanisms.

## Decision Outcome

The reposition-to-general-with-a-first-profile approach achieves the primary
drivers: scope honesty (the name now matches the model), a clean extensibility
seam (`profiles/ai-memory/` layers on `mif-base`), and an independent identity
that ADR-009 builds on. Mitigations:

- The positioning is stated normatively at the top of `SPECIFICATION.md` (the
  "AI memory is the first domain profile of MIF, not its identity" callout) and
  carried into the v1.0.0 `CHANGELOG.md` entry and the migration guide.
- The extension model is *proven*, not merely asserted, by the shipped
  `profiles/ai-memory/` profile, which opens by restating that AI memory is a
  profile and not MIF's identity.

## Related Decisions

- [ADR-009: OKF Compliance as a Superset (Pinned OKF v0.1)](ADR-009-okf-compliance-superset.md) — builds on the independent, domain-neutral identity that this repositioning establishes.
- [ADR-001: Cognitive Triad Taxonomy](ADR-001-cognitive-triad-taxonomy.md) — the semantic/episodic/procedural taxonomy becomes the base content model on which the AI-memory profile sits.

## Links

- [`docs/okf-conformance.md`](../docs/okf-conformance.md) — the pinned OKF v0.1 interoperability surface that MIF's general content model fills (see ADR-009).

## More Information

- **Date:** 2026-06-18
- **Source:** `SPECIFICATION.md` L15 and the L24-L27 callout; `profiles/ai-memory/SPECIFICATION.md`; `CHANGELOG.md` v1.0.0 entry; `MIGRATION.md`.
- **Related ADRs:** ADR-009, ADR-001

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Acronym re-expanded to "Modeled Information Format" as the project identity | `SPECIFICATION.md` | L15 | compliant |
| Callout: "AI memory is the first domain profile of MIF, not its identity (see `profiles/ai-memory/`)" | `SPECIFICATION.md` | L24-L27 | compliant |
| AI-memory profile exists as a normative overlay on `mif-base` | `profiles/ai-memory/SPECIFICATION.md` | L1-L19 | compliant |
| v1.0.0 changelog records the reposition and the memory-to-profile demotion | `CHANGELOG.md` | L10-L12 | compliant |
| Migration guide states MIF is repositioned and AI memory is now a profile, not its identity | `MIGRATION.md` | L5-L6 | compliant |
| ADR index names the project "Modeled Information Format (MIF)" (remediated 2026-06-18; previously stale) | `adr/README.md` | L7 | compliant |

**Summary:** The repositioning to "Modeled Information Format" and the demotion of
AI memory to MIF's first domain profile are stated normatively across the
specification, the AI-memory profile, the changelog, and the migration guide. The
ADR index (`adr/README.md` L7), which previously still named the current project
"Memory Interchange Format (MIF)", was corrected to "Modeled Information Format
(MIF)" during this same change set. (The historical `CHANGELOG.md` 0.1.0-draft
entries that name "Memory Interchange Format" are correct in their historical
context and are not flagged.)

**Action Required:** None.
