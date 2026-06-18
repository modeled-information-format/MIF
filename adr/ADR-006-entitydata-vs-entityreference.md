---
title: "EntityData vs EntityReference"
description: "MIF represents entities two ways: EntityReference, a lightweight closed-schema pointer for mentioned entities, and EntityData, a full ontology-typed embedded payload for memories that ARE an entity."
type: adr
category: api
tags:
  - entity
  - data-model
  - schema
  - json-ld
status: accepted
created: 2026-01-27
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - json-ld
  - json-schema
audience:
  - developers
  - architects
related:
  - ADR-004-three-tier-trait-inheritance.md
  - ADR-002-dual-format-design.md
---

# ADR-006: EntityData vs EntityReference

## Status

Accepted

## Context

### Background and Problem Statement

A MIF memory has to talk about entities — people, organizations, technologies,
concepts, files, and domain-specific things like a grazing plan or a soil
profile. But "talk about" covers two structurally different situations that a
single representation cannot serve well:

1. **The memory *mentions* an entity.** A note authored by Jane Smith, a memory
   that references a piece of equipment, a concept the memory relates to. Here
   the entity is a *pointer*: the memory needs to name it, classify it, and link
   to its canonical identity, but it does not own the entity's data.
2. **The memory *is* an entity.** The memory's whole reason for existing is to
   carry the structured data of one ontology-typed thing — a grazing plan with
   stock density and rest-period fields, a soil profile with measurements. Here
   the entity is the *payload*: the memory must hold arbitrary
   ontology-defined fields.

These two situations pull the schema in opposite directions. Mentions want a
small, fixed, validated shape so a generic consumer can read any reference
without ontology knowledge. Payloads want an open, extensible shape so a domain
ontology can attach whatever fields it defines. One representation forced to do
both would be either too loose to validate mentions or too rigid to carry
domain data.

### Current Limitations

- A single permissive entity object (open `additionalProperties`) cannot
  guarantee the shape of a mention: typos and stray fields would validate
  silently, and a generic reader could not rely on a stable contract.
- A single strict entity object (closed `additionalProperties`) cannot carry
  ontology-specific fields without amending the core schema for every domain —
  defeating the purpose of pluggable ontologies (see ADR-004).
- Without an explicit two-way split, authors have no signal for *which*
  representation a given memory should use, and the dual Markdown/JSON-LD
  projection (ADR-002) has no clean rule for where each shape lives.

## Decision Drivers

### Primary Decision Drivers

1. **Validation guarantees for mentions**: A reference to an entity must have a
   small, predictable, closed shape that a generic consumer can validate and
   read without ontology-specific knowledge.
2. **Extensibility for payloads**: A memory that *is* an entity must be able to
   carry arbitrary ontology-defined fields without changes to the core schema.
3. **Clear authoring signal**: The data model must make the choice between
   "mentions an entity" and "is an entity" obvious and structural, not a matter
   of convention.

### Secondary Decision Drivers

1. **Identity linkage**: A reference must be able to point at an entity's
   canonical URN identity so mentions across memories resolve to the same thing.
2. **Ontology alignment**: The payload shape must compose with the trait and
   `entity_type` machinery defined by ontologies (ADR-004).

## Considered Options

### Option 1: A single permissive entity object

**Description**: Represent every entity — mention or payload — with one object
type whose `additionalProperties` is open, letting callers attach whatever
fields they need in either situation.

**Technical Characteristics**:
- One `$def`, used for both `entities[]` mentions and the memory's own entity.
- No closed contract; any field validates.

**Advantages**:
- Only one shape to learn.
- Maximum flexibility for payloads.

**Disadvantages**:
- Mentions lose all validation: a misspelled field or wrong key passes silently.
- A generic consumer cannot rely on a stable reference contract.
- No structural signal distinguishing "mentions" from "is".

**Risk Assessment**:
- **Technical Risk**: High. Silent acceptance of malformed references erodes
  data quality across the corpus.
- **Schedule Risk**: Low to build.
- **Ecosystem Risk**: High. Consumers cannot depend on a fixed reference shape.

### Option 2: A single strict entity object

**Description**: Represent every entity with one closed object
(`additionalProperties: false`), enumerating all permitted fields in the core
schema.

**Advantages**:
- Strong validation everywhere.
- One shape to learn.

**Disadvantages**:
- Cannot carry domain-specific payload fields without amending the core schema
  for every ontology.
- Directly conflicts with pluggable ontologies (ADR-004): every new
  `entity_type` field would require a core-schema change.

**Risk Assessment**:
- **Technical Risk**: High to the ontology model — closing the schema breaks
  domain extensibility.
- **Ecosystem Risk**: High. Domains cannot extend MIF without forking the core
  schema.

### Option 3: Two distinct representations — EntityReference and EntityData (chosen)

**Description**: Define two purpose-built shapes. **EntityReference** is a
lightweight, *closed* pointer (`additionalProperties: false`) used in the
`entities[]` array for entities a memory mentions. **EntityData** is a full,
*open* (`additionalProperties: true`) ontology-typed payload used in the
memory's singular `entity` slot when the memory IS an entity.

**Technical Characteristics**:
- `EntityReference` requires `@type: "EntityReference"` and an `entity` object
  carrying a `urn:mif:entity:` `@id`; it offers a fixed set of fields
  (`entityType`, `name`, `role`) and rejects everything else.
- `entityType` is constrained to a closed set of core types
  (Person, Organization, Technology, Concept, File) OR a lowercase-kebab custom
  type (e.g. `grazing-plan`, `soil-profile`).
- `EntityData` requires only `name`, offers `entity_type` (lowercase-kebab) and
  `entity_id`, and leaves `additionalProperties: true` so ontology-defined
  fields validate.
- The two live in different top-level slots: `entities[]` (array of references)
  versus `entity` (single payload), which sits alongside the optional
  `ontology` reference.

**Advantages**:
- Mentions get a closed, validatable contract; a generic consumer reads any
  reference without ontology knowledge.
- Payloads get open extensibility for arbitrary ontology fields.
- The structural split (`entities[]` vs `entity`) is itself the authoring signal.
- Both can coexist in the same memory — a grazing-plan payload that also
  references the people involved.
- Composes cleanly with ontology trait inheritance (ADR-004) and the dual
  Markdown/JSON-LD projection (ADR-002).

**Disadvantages**:
- Two patterns to understand and document.
- Some apparent duplication (both carry a `name`).
- Authors can still be unsure which to use for borderline cases.

**Risk Assessment**:
- **Technical Risk**: Low. Each shape's `additionalProperties` setting matches
  its job; both are machine-checkable.
- **Schedule Risk**: Low. Both shapes ship in the v1.0 schema.
- **Ecosystem Risk**: Low. References are a stable closed contract; payloads
  extend through ontologies without touching the core schema.

## Decision

MIF defines **two distinct entity representations**, selected by whether the
memory *mentions* an entity or *is* one.

### EntityReference — lightweight pointer (closed schema)

Used in the memory's `entities[]` array to reference entities the memory
mentions:

```json
{
  "@type": "EntityReference",
  "entity": { "@id": "urn:mif:entity:person:jane-smith" },
  "entityType": "Person",
  "name": "Jane Smith",
  "role": "author"
}
```

- **Use when**: mentioning a person, organization, technology, concept, or file;
  creating a link to an external entity; basic entity metadata is sufficient.
- **Shape**: requires `@type` and an `entity` object carrying a
  `urn:mif:entity:` `@id`. Permits `entityType`, `name`, `role`.
- **Types**: closed core set — Person, Organization, Technology, Concept, File —
  OR a lowercase-kebab custom type (`grazing-plan`, `soil-profile`).
- **`additionalProperties: false`** — the reference shape is closed; unknown
  fields are rejected.

### EntityData — ontology-typed payload (open schema)

Used in the memory's singular `entity` slot when the memory IS an entity:

```json
{
  "name": "2026 Spring Grazing Plan",
  "entity_type": "grazing-plan",
  "entity_id": "grazing-plan-beef-2026",
  "herd_id": "herd-beef-main",
  "stock_density": 250000,
  "rest_period_days": 45
}
```

- **Use when**: the memory IS an entity (not just mentions one); full structured
  data per an ontology schema is needed; entity-specific fields apply.
- **Shape**: requires `name`. Offers `entity_type` (lowercase-kebab) and
  `entity_id`; the memory carries an accompanying top-level `ontology` reference
  that defines the entity's field schema.
- **`additionalProperties: true`** — ontology-defined fields (`herd_id`,
  `stock_density`, …) validate without core-schema changes.

The two shapes occupy different top-level slots: `entities[]` holds references,
while the singular `entity` holds the payload (sitting next to the optional
`ontology` reference). Both may appear in one memory.

## Consequences

### Positive

1. **Clear semantic distinction**: "mentions" and "is" map to two structurally
   different slots, so intent is explicit.
2. **Validated references**: the closed EntityReference shape gives consumers a
   stable, generic-readable contract.
3. **Extensible payloads**: the open EntityData shape carries arbitrary
   ontology fields without amending the core schema.
4. **Coexistence**: a memory can be an entity *and* reference others.

### Negative

1. **Two patterns**: authors must learn both and pick correctly.
2. **Borderline confusion**: some memories could plausibly use either shape.
3. **Minor duplication**: both shapes carry a `name`.

### Neutral

1. **Different `additionalProperties` policies by design**: closed for
   references, open for payloads — intentional asymmetry that encodes each
   shape's purpose.

## Decision Outcome

The two-representation split achieves the primary drivers: references get
closed-schema validation (a stable generic contract), payloads get open-schema
extensibility (arbitrary ontology fields), and the `entities[]`-vs-`entity`
structure is itself the authoring signal. Mitigations for the cost of two
patterns:

- The structural slot difference (`entities[]` array vs singular `entity`) makes
  the choice mechanical rather than a judgment call in the common cases.
- EntityData composes with ontology `entity_type` schemas and trait inheritance
  (ADR-004), so domain fields are governed by the ontology, not ad-hoc.
- Both shapes carry through the dual Markdown/JSON-LD projection (ADR-002)
  without special-casing.

### Authoring Guidelines

| Scenario | Use |
|----------|-----|
| Memory about a person | `entities: [EntityReference]` |
| Memory about a soil test | `entity: EntityData` with `entity_type: soil-profile` |
| Memory mentioning equipment | `entities: [EntityReference]` |
| Memory that IS a grazing plan | `entity: EntityData` with full fields |

## Related Decisions

- [ADR-004: Three-Tier Trait Inheritance](ADR-004-three-tier-trait-inheritance.md) — the trait-inheritance model governs how an ontology composes the `entity_type` schema that EntityData's open fields conform to.
- [ADR-002: Dual-Format Design](ADR-002-dual-format-design.md) — both entity representations carry through the Markdown and JSON-LD projections.

## Links

- (none)

## More Information

- **Date:** 2026-01-27
- **Source:** `schema/definitions/entity-reference.schema.json` (EntityReference); `schema/mif.schema.json` `$defs.EntityData` and the top-level `entity` / `ontology` / `entities` properties.
- **Related ADRs:** ADR-004, ADR-002

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| EntityReference is a closed schema (`additionalProperties: false`), required `["@type", "entity"]`, fields `entityType`/`name`/`role`, with an `entity.@id` matching `^urn:mif:entity:` | `schema/definitions/entity-reference.schema.json` | L7-L48 | compliant |
| EntityReference core types are the closed set Person/Organization/Technology/Concept/File, plus a lowercase-kebab custom-type pattern | `schema/definitions/entity-reference.schema.json` | L28-L37 | compliant |
| EntityData is an open schema (`additionalProperties: true`), requires only `name`, offers lowercase-kebab `entity_type` and `entity_id` | `schema/mif.schema.json` | L452-L472 | compliant |
| The two shapes occupy distinct top-level slots: singular `entity` (EntityData) alongside the `ontology` reference, and `entities[]` (array of EntityReference) | `schema/mif.schema.json` | L68-L94 | compliant |
| The main schema's `EntityReference` `$def` delegates to the dedicated definition file | `schema/mif.schema.json` | L244-L246 | compliant |

**Summary:** The two-representation model is present and enforced in the v1.0
schema exactly as described: EntityReference is closed with a fixed core-type
enum plus custom-type pattern, EntityData is open with only `name` required, and
the two live in distinct top-level slots (`entities[]` vs `entity`).

**Note:** The original ADR phrased EntityData as "Requires `ontology` reference."
At the JSON-Schema level this is a *semantic* coupling, not a hard constraint:
the top-level `required` array (`schema/mif.schema.json` L7) does not list
`ontology`, and the `EntityData` object itself requires only `name`. This ADR
therefore describes the `ontology` reference as the accompanying, EntityData-
defining artifact rather than a schema-enforced requirement.

**Action Required:** None.
