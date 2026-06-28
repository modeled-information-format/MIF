---
title: "Cognitive Triad Taxonomy (Semantic / Episodic / Procedural)"
description: "MIF adopts the cognitive-psychology memory triad — semantic, episodic, procedural — as its base concept-type taxonomy, supplying the concept-type system OKF deliberately leaves open."
type: adr
category: architecture
tags:
  - taxonomy
  - memory-types
  - cognitive-science
status: accepted
created: 2026-01-27
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
  - ADR-005-underscore-namespace-prefix.md
  - ADR-008-decay-model-rationale.md
  - ADR-004-three-tier-trait-inheritance.md
  - ADR-009-okf-compliance-superset.md
  - ADR-010-modeled-information-format-repositioning.md
---

# ADR-001: Cognitive Triad Taxonomy (Semantic / Episodic / Procedural)

## Status

Accepted

## Context

### Background and Problem Statement

MIF needs a memory classification system that anchors every concept in a small,
stable set of base types. That taxonomy has to satisfy four constraints at once:
it must be **universally applicable** across domains, **grounded in established
theory** rather than ad-hoc opinion, **simple enough** to be used without
specialist training, and **expressive enough** to organize the memory of AI
systems that accumulate facts, events, and procedures over time.

This requirement is sharpened by MIF's relationship to the Open Knowledge Format
(OKF). OKF defines a minimal interoperability surface and **deliberately refuses
to define a concept-type taxonomy** — it requires a `type` field on every concept
but says nothing about what the values should be. MIF's positioning thesis
(SPECIFICATION.md, "MIF answers OKF's open questions") is to supply opinionated
answers to exactly those open questions. The base concept-type taxonomy is the
first such answer: it is MIF's response to OKF's deliberately-absent concept-type
system.

### Current Limitations

Without a principled taxonomy, a memory format drifts toward one of several
failure modes:

- **Fragmentation**: Domain-specific category sets do not port between systems;
  a memory typed for one application is meaningless to another.
- **No semantic hierarchy**: Flat tagging records keywords but encodes no
  organizing structure, so consumers cannot reason about what *kind* of thing a
  memory is.
- **No interoperability**: A custom ontology invented per system cannot satisfy
  OKF's requirement that every bundle be readable by a generic consumer.
- **Unverifiable foundation**: A taxonomy invented from intuition has no external
  authority; reviewers cannot evaluate whether the categories are complete or
  well-separated.

## Decision Drivers

### Primary Decision Drivers

1. **Universality**: The base types must apply to any domain — engineering,
   operations, personal knowledge — without per-domain forks.
2. **Theoretical grounding**: The categories must rest on established research,
   not ad-hoc invention, so the boundaries between them are defensible.
3. **Answering OKF's open concept-type question**: MIF must fill the taxonomy
   OKF leaves blank while keeping each typed concept legible to a generic OKF
   reader.

### Secondary Decision Drivers

1. **Simplicity**: A small, memorable set of types lowers the cost of adoption
   for both human authors and AI systems.
2. **Extensibility**: The base set must remain small while still allowing
   domain-specific specialization without breaking interoperability.

## Considered Options

### Option 1: Domain-specific categories

**Description**: Define category sets tailored to each application domain (e.g.,
"bug", "feature", "meeting" for engineering; different sets elsewhere).

**Advantages**:

- Maximally expressive within a single domain.
- Categories map directly onto familiar local vocabulary.

**Disadvantages**:

- Fragmented: no shared taxonomy across systems, so memories do not port.
- Combinatorial growth as new domains appear.
- Fails OKF's interoperability goal — a generic consumer cannot interpret the
  types.

**Risk Assessment**:

- **Technical Risk**: Low to build, High to portability.
- **Ecosystem Risk**: High. Portability across systems is sacrificed.

### Option 2: Flat tagging

**Description**: Drop typed categories entirely; let authors attach free-form
tags to each memory.

**Advantages**:

- Zero upfront taxonomy design.
- Unlimited author flexibility.

**Disadvantages**:

- No semantic hierarchy: tags are keywords, not a classification.
- Poor organization; consumers cannot reason about a memory's kind.
- Inconsistent vocabulary across authors degrades retrieval.

**Risk Assessment**:

- **Technical Risk**: Low.
- **Ecosystem Risk**: High. Without a shared kind-system, cross-system meaning
  collapses.

### Option 3: Custom ontology per system

**Description**: Let every adopting system define its own ontology of concept
types from scratch.

**Advantages**:

- Each system is internally coherent and fully tailored.

**Disadvantages**:

- No interoperability between systems — the opposite of MIF's goal.
- High design burden duplicated by every adopter.
- No common base for tooling, decay defaults, or namespace conventions.

**Risk Assessment**:

- **Technical Risk**: Medium (each adopter re-solves the problem).
- **Ecosystem Risk**: High. Interoperability is lost.

### Option 4: Cognitive-psychology memory triad (chosen)

**Description**: Adopt the **cognitive triad** from memory research as MIF's base
concept-type taxonomy:

1. **Semantic** — facts, concepts, relationships, and knowledge (declarative
   knowledge about the world: decisions, technology choices, preferences, domain
   knowledge).
2. **Episodic** — events, experiences, sessions, and timelines (time-bound
   records of "what happened": incidents, conversations, blockers).
3. **Procedural** — step-by-step processes, runbooks, and patterns (how-to
   knowledge: migration guides, code patterns, workflows).

Domain-specific specialization is handled by **ontology-extended types** that
declare a `base` of one of the three triad members (SPECIFICATION.md §4.2.1),
keeping the base set fixed at three while permitting local vocabulary.

**Technical Characteristics**:

- Encoded as the `conceptType` enum `["semantic", "episodic", "procedural"]` in
  the JSON Schema, with `memoryType` retained as a deprecated v0.1 alias.
- Each base type carries a namespace hint (`semantic/*`, `episodic/*`,
  `procedural/*`) that downstream conventions build on.
- Each typed concept remains a valid OKF concept: the `type` value satisfies
  OKF's required field while supplying meaning OKF leaves open.

**Advantages**:

- Grounded in well-cited research — Tulving (1972) for the semantic/episodic
  distinction and Cohen & Squire (1980) for procedural memory as a distinct
  system.
- Universal: the three kinds map onto any domain's facts, events, and processes.
- Intuitive mental model for both humans and AI systems.
- Enables meaningful cross-system memory portability under a single shared
  taxonomy.
- Directly answers OKF's deliberately-absent concept-type question.

**Disadvantages**:

- Some memories span categories — mitigated by traits (see ADR-004).
- Assumes familiarity with the cognitive-psychology framing.
- Can feel constraining for narrow domain use cases — mitigated by
  ontology-extended types and namespace prefixes (see ADR-005).

**Risk Assessment**:

- **Technical Risk**: Low. Three-value enum is trivial to validate and stable.
- **Schedule Risk**: Low. The taxonomy is fixed and shipped.
- **Ecosystem Risk**: Low. A research-grounded, universal base maximizes
  portability and interoperability.

## Decision

MIF adopts the **cognitive triad** — `semantic`, `episodic`, `procedural` — as
its base concept-type taxonomy. These three base types are MIF's opinionated
answer to OKF's deliberately-absent concept-type system.

Implementation specifics:

- The triad is the normative `conceptType` enum in the schema
  (`schema/mif.schema.json`), with `memoryType` kept as a deprecated v0.1 alias
  for backward compatibility.
- SPECIFICATION.md §4.2 defines the three base types and their namespace hints;
  §4.2.1 defines how ontologies extend them via a declared `base`.
- Specialization is achieved through ontology-extended types and underscore
  namespace prefixes (ADR-005), never by enlarging the base enum.

## Consequences

### Positive

1. **Research-grounded foundation**: The category boundaries rest on Tulving
   (1972) and Cohen & Squire (1980), giving reviewers an external authority to
   evaluate against.
2. **Universal applicability**: Facts, events, and processes exist in every
   domain, so the three base types apply everywhere.
3. **Portability**: A single shared taxonomy lets memories move between systems
   with preserved meaning.
4. **OKF answer**: MIF supplies the concept-type taxonomy OKF leaves open while
   each typed concept stays OKF-legible.

### Negative

1. **Cross-category memories**: Some items legitimately span types; this is
   absorbed by traits rather than by adding base types (ADR-004).
2. **Conceptual onboarding**: Authors must understand the cognitive-psychology
   framing to type memories well.

### Neutral

1. **Fixed base, extensible edges**: The base set is deliberately frozen at
   three; all domain growth happens through ontology-extended types and
   namespaces, by design (ADR-005).

## Decision Outcome

The cognitive-triad taxonomy achieves the primary drivers: universality (facts /
events / processes appear in every domain), theoretical grounding (Tulving;
Cohen & Squire), and a concrete answer to OKF's open concept-type question.
Mitigations:

- Cross-category items are handled by the trait system (ADR-004) rather than by
  expanding the enum.
- Narrow domain needs are met by ontology-extended types and namespace prefixes
  (ADR-005), keeping the base set stable while allowing local specialization.

## Related Decisions

- [ADR-005: Underscore Namespace Prefix](ADR-005-underscore-namespace-prefix.md) — the namespace prefix convention derives from the three base memory types.
- [ADR-008: Decay Model Rationale](ADR-008-decay-model-rationale.md) — default decay half-lives vary by base memory type.
- [ADR-004: Three-Tier Trait Inheritance](ADR-004-three-tier-trait-inheritance.md) — traits absorb memories that span more than one base type.
- [ADR-009: OKF Compliance as a Superset](ADR-009-okf-compliance-superset.md) — this base-type taxonomy is MIF's answer to OKF's deliberately-absent concept-type system.

## Links

- Tulving, E. (1972). *Episodic and semantic memory.* In Organization of Memory — the semantic/episodic distinction.
- Cohen, N. J. & Squire, L. R. (1980). *Preserved learning and retention of pattern-analyzing skill in amnesia: Dissociation of knowing how and knowing that.* Science — procedural memory as a distinct system.
- Squire, L. R. (2004). *Memory systems of the brain: A brief history and current perspective.* Neurobiology of Learning and Memory.

## More Information

- **Date:** 2026-06-18
- **Source:** SPECIFICATION.md "MIF answers OKF's open questions" table and §4.2 (Memory Types); `schema/mif.schema.json` `conceptType` enum.
- **Related ADRs:** ADR-004, ADR-005, ADR-008, ADR-009, ADR-010
- **Academic references:** Tulving (1972); Cohen & Squire (1980); Squire (2004) — see Links above.

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Base concept-type enum `["semantic", "episodic", "procedural"]` is normative in the schema (`conceptType`) | `schema/mif.schema.json` | L30-L34 | compliant |
| `memoryType` retained as a deprecated v0.1 alias of `conceptType` (same triad enum) | `schema/mif.schema.json` | L35-L38 | compliant |
| Same triad enum enforced in the ontology schema | `schema/ontology/ontology.schema.json` | L122, L154 | compliant |
| Three base memory types defined with descriptions and namespace hints | `SPECIFICATION.md` | L234-L250 | compliant |
| Ontology-extended types specialize a declared `base` (keeps base set fixed at three) | `SPECIFICATION.md` | L252-L263 | compliant |
| "MIF answers OKF's open questions" table: triad is MIF's answer to OKF's absent concept-type taxonomy | `SPECIFICATION.md` | L49-L51 | compliant |

**Summary:** The cognitive triad is present and normative as the `conceptType`
enum in `schema/mif.schema.json`, mirrored in the ontology schema, defined with
namespace hints and extension rules in SPECIFICATION.md §4.2 / §4.2.1, and
positioned in the SPECIFICATION's "MIF answers OKF's open questions" table as
MIF's answer to OKF's deliberately-absent concept-type system.

**Action Required:** None.
