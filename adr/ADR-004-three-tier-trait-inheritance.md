---
title: "Three-Tier Trait Inheritance"
description: "MIF composes entity fields from reusable traits through a three-tier inheritance chain — mif-base, shared-traits, then domain ontologies — declared via the `extends` field and composed via the entity `traits` array."
type: adr
category: architecture
tags:
  - ontology
  - traits
  - inheritance
  - composition
status: accepted
created: 2026-01-27
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - yaml
  - json-ld
audience:
  - developers
  - architects
related:
  - ADR-006-entitydata-vs-entityreference.md
  - ADR-001-cognitive-triad-taxonomy.md
---

# ADR-004: Three-Tier Trait Inheritance

## Status

Accepted

## Context

### Background and Problem Statement

MIF ontologies need reusable field definitions — **traits** — that can be
composed into entity types without copying field schemas from ontology to
ontology. A trait is a named bundle of fields (for example, `timestamped` adds
`created_at` and `updated_at`); entity types pull in the traits they need rather
than redeclaring those fields inline.

The architectural question is *how* traits should be organized and inherited.
Three forces shape the answer: the same handful of generic fields (timestamps,
provenance, ownership, lifecycle state) recur across every domain and should be
defined once; domains nonetheless need their own specialized traits; and the
inheritance mechanism must stay shallow enough that a reader can reason about
where a field came from and how an override resolves.

### Current Limitations

- **Duplication without a base tier.** If every ontology defines its own
  `timestamped` or `located` trait, the definitions drift and cross-ontology
  queries can no longer rely on a common field shape.
- **Inflexibility with a single fixed base.** A single base of MIF-core traits
  cannot express cross-domain-but-not-core concepts (audit trails,
  certifications, scheduling) that many — but not all — domains share.
- **Unbounded depth is hard to reason about.** Arbitrary inheritance chains make
  trait-conflict resolution and override behavior difficult to predict and
  debug.

## Decision Drivers

### Primary Decision Drivers

1. **DRY definitions**: Common fields must be defined exactly once and reused,
   so identical concepts have identical schemas across ontologies.
2. **Cross-domain interoperability**: Shared field shapes must enable queries
   that span multiple domain ontologies.
3. **Domain extensibility**: Each domain ontology must be able to add its own
   specialized traits on top of the shared foundation.

### Secondary Decision Drivers

1. **Reasoning simplicity**: The inheritance chain must be shallow enough that
   override resolution and conflict handling are straightforward to debug.
2. **Progressive enhancement**: An ontology author should be able to start with
   base traits and layer in complexity only as the domain requires it.

## Considered Options

### Option 1: Flat inheritance (every ontology defines its own traits)

**Description**: No shared trait library; each ontology declares all the traits
it uses inline.

**Advantages**:

- Trivial mental model — everything an ontology needs is local to it.

**Disadvantages**:

- Massive duplication of generic traits across ontologies.
- Definitions drift, breaking the common field shapes that cross-domain queries
  depend on.

**Risk Assessment**:

- **Technical Risk**: Low to build, High to maintain consistency.
- **Ecosystem Risk**: High. Drift between independently-defined traits
  undermines interoperability.

### Option 2: Single fixed base (one MIF-core trait set, no middle tier)

**Description**: MIF ships one base trait set; every domain ontology extends it
directly with no intermediate cross-domain layer.

**Advantages**:

- Simple two-level chain.
- One canonical place for core traits.

**Disadvantages**:

- No home for traits that are cross-domain but not MIF-core (audit, lifecycle,
  certification, geography). Each domain re-invents them, reintroducing the
  drift Option 1 suffers from.

**Risk Assessment**:

- **Technical Risk**: Low.
- **Ecosystem Risk**: Medium. Cross-domain concepts fragment across domains.

### Option 3: Unlimited inheritance depth

**Description**: Allow ontologies to extend other ontologies to arbitrary depth,
forming long inheritance chains.

**Advantages**:

- Maximum compositional flexibility.

**Disadvantages**:

- Trait-conflict resolution and override reasoning become hard to predict.
- Debugging "where did this field come from" requires walking an unbounded
  chain.

**Risk Assessment**:

- **Technical Risk**: High. Override semantics across deep chains are
  error-prone.
- **Schedule Risk**: Medium. Harder tooling and validation.

### Option 4: Three-tier model (chosen)

**Description**: A fixed three-tier chain — `mif-base` (Tier 1, MIF-core
traits) → `shared-traits` (Tier 2, cross-domain mixins) → domain ontology
(Tier 3, domain-specific traits). Tiers are declared with the ontology `extends`
field; entity types compose individual traits through a `traits` array.

**Technical Characteristics**:

- Tier 1 (`mif-base`) supplies the MIF-core traits every record can use.
- Tier 2 (`shared-traits`) extends `mif-base` and holds industry-agnostic
  mixins shared across domains.
- Tier 3 domain ontologies extend both base tiers and add domain traits.
- The depth is fixed at three, keeping override and conflict reasoning bounded.

**Advantages**:

- DRY: each trait is defined once, at the most general tier where it applies.
- Cross-domain interoperability: shared traits give multiple domains identical
  field shapes.
- Extensibility: domains add their own traits without touching the base tiers.
- Bounded depth: a three-link chain is shallow enough to reason about overrides
  and conflicts directly.

**Disadvantages**:

- The three-tier limit is a deliberate constraint; a domain that wants a fourth
  conceptual layer must fold it into Tier 3.
- Trait conflicts still require a documented resolution strategy
  (see SPECIFICATION.md Section 6.3).

**Risk Assessment**:

- **Technical Risk**: Low. Fixed depth makes override semantics predictable.
- **Schedule Risk**: Low. Simple to validate and tool.
- **Ecosystem Risk**: Low. Shared tiers anchor cross-domain consistency.

## Decision

MIF adopts a **three-tier trait inheritance** model:

- **Tier 1 — `mif-base`**: MIF-core reusable traits — `timestamped`
  (creation/update timestamps), `confidence` (freshness/validity score), and
  `provenance` (source and author tracking).
- **Tier 2 — `shared-traits`**: cross-domain mixins that extend `mif-base`,
  including `lifecycle`, `auditable`, `certified`, `regulated`, `located`,
  `bounded`, `owned`, `measured`, `scheduled`, and `transactional`, among
  others.
- **Tier 3 — domain ontologies**: domain-specific ontologies that extend both
  base tiers and add their own specialized traits and namespaces.

The inheritance chain is:

```text
mif-base → shared-traits → domain-ontology
```

An ontology declares its place in the chain with the `extends` field:

```yaml
ontology:
  id: my-domain
  extends:
    - mif-base
    - shared-traits
```

Entity types then compose individual traits through a `traits` array:

```yaml
entity_types:
  - name: my-entity
    traits:
      - timestamped
      - owned
      - domain:custom-trait
```

## Consequences

### Positive

1. **DRY definitions**: A trait such as `timestamped` is defined once in
   `mif-base` and reused everywhere, eliminating drift.
2. **Cross-domain interoperability**: Domains that share Tier 2 traits share
   identical field shapes, enabling queries that span ontologies.
3. **Extensibility**: Domain ontologies add traits at Tier 3 without modifying
   the base tiers.
4. **Progressive enhancement**: Authors can begin with base traits and add
   complexity only as the domain demands.

### Negative

1. **Fixed depth as a constraint**: A domain wanting a fourth conceptual layer
   must collapse it into Tier 3 rather than extend the chain.
2. **Conflict resolution required**: Composing traits from multiple tiers can
   surface field conflicts, which need a documented resolution strategy
   (SPECIFICATION.md Section 6.3).
3. **Chain literacy required**: Readers must understand the three-tier chain to
   know where a given field originates.

### Neutral

1. **Two declaration surfaces**: Tier membership is set with `extends` at the
   ontology level, while individual trait composition happens with the `traits`
   array at the entity level — by design, these are separate mechanisms.

## Decision Outcome

The three-tier model achieves the primary drivers: DRY trait definitions
(`mif-base` as the single source for core traits), cross-domain interoperability
(`shared-traits` as a common mixin layer), and domain extensibility (Tier 3
ontologies extending both base tiers). The fixed depth keeps the secondary
driver of reasoning simplicity intact. Mitigations:

- Trait conflicts are handled by the documented resolution strategy in
  SPECIFICATION.md Section 6.3.
- The `extends`/`traits` split is consistent across all shipped ontologies, so
  the declaration model is uniform for tooling and authors alike.

## Related Decisions

- [ADR-006: EntityData vs EntityReference](ADR-006-entitydata-vs-entityreference.md) — EntityData relies on the trait system to give structured entities their field schemas.
- [ADR-001: Cognitive Triad Taxonomy](ADR-001-cognitive-triad-taxonomy.md) — the base knowledge types that traits extend and enrich.

## Links

None.

## More Information

- **Date:** 2026-06-18
- **Source:** `ontologies/mif-base.ontology.yaml` (Tier 1), `ontologies/shared-traits.ontology.yaml` (Tier 2), `ontologies/examples/csi-5w1h.ontology.yaml` (Tier 3 example); SPECIFICATION.md Section 6.3 (Trait Conflict Resolution).
- **Related ADRs:** ADR-006, ADR-001

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Tier 1 `mif-base` defines the MIF-core reusable traits (`timestamped`, `confidence`, `provenance`) | `ontologies/mif-base.ontology.yaml` | L82-L110 | compliant |
| Tier 2 `shared-traits` extends `mif-base` via the `extends` field | `ontologies/shared-traits.ontology.yaml` | L22-L23 | compliant |
| Tier 2 cross-domain mixins present (`lifecycle`, `auditable`, `certified`, `located`, `bounded`, `owned`, `scheduled`, `transactional`, `measured`) | `ontologies/shared-traits.ontology.yaml` | L29-L355 | compliant |
| Tier 3 domain ontology extends both base tiers (`extends: [mif-base, shared-traits]`) | `ontologies/examples/csi-5w1h.ontology.yaml` | L32-L34 | compliant |

**Summary:** The three-tier chain is present and verifiable in the shipped
ontologies: `mif-base` supplies Tier 1 core traits, `shared-traits` extends it
with Tier 2 cross-domain mixins, and the `csi-5w1h` domain example extends both
base tiers as a Tier 3 ontology. Note that the original ADR's illustrative Tier 1
trait names (`identified`, `typed`, `tagged`) do not match the current
`mif-base` file, which defines `timestamped`, `confidence`, and `provenance`;
this conversion cites the file-accurate names. The three-tier *model* — the
substance of the decision — is fully compliant.

**Action Required:** None.
</content>
</invoke>
