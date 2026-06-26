---
title: "Provenance: Lightweight Core + Optional W3C-PROV Layer"
description: "MIF provenance is a lightweight, always-available core (sourceType / confidence / trustLevel) plus an OPTIONAL, additive W3C-PROV-aligned layer (wasGeneratedBy / wasAttributedTo / wasDerivedFrom), so full PROV graphs are expressible but never required."
type: adr
category: schema
tags:
  - provenance
  - prov
  - trust
  - schema
  - json-ld
  - backward-compatibility
status: accepted
created: 2026-06-26
updated: 2026-06-26
author: MIF Maintainers
project: MIF
technologies:
  - json-schema
  - json-ld
  - w3c-prov
audience:
  - developers
  - architects
related:
  - ADR-009-okf-compliance-superset.md
  - ADR-011-markdown-canonical-derived-jsonld.md
  - ADR-002-dual-format-design.md
---

# ADR-013: Provenance: Lightweight Core + Optional W3C-PROV Layer

## Status

Accepted

## Context

### Background and Problem Statement

The MIF schema's `$defs.Provenance` has always been lightweight: `sourceType`,
`confidence`, `trustLevel`, with `additionalProperties: true`. The specification,
the README badge, and the OKF-comparison tables nevertheless claimed "MIF uses
W3C PROV vocabulary for provenance tracking" and presented a "W3C PROV" feature
badge. That claim was not backed by the schema — no PROV entity/activity/agent
fields existed, and the `§12.3` example mixed undefined snake_case keys
(`source_ref`, `derived_from`, `attribution`) that only survived because the
object is open.

Two things were therefore true at once: the schema under-described what real
PROV-style lineage a unit could carry, and the prose over-claimed full PROV
conformance. This decision records the resolution: deepen the schema toward
W3C PROV in an additive, backward-compatible way, and make the documentation
honest about what is required versus optional.

### Current Limitations

- The schema offered no first-class place to express a PROV
  entity/activity/agent triple or the `wasGeneratedBy` / `wasAttributedTo` /
  `wasDerivedFrom` relations, so producers either dropped lineage or smuggled it
  through `additionalProperties`.
- The docs asserted blanket "W3C PROV" support, which is unverifiable and
  misleading for a profile where provenance is entirely OPTIONAL.
- The `§12.3` example did not validate against (or even align with) the actual
  field names, so it could not be used as a copy-paste template.

## Decision Drivers

### Primary Decision Drivers

1. **Honesty**: Documentation must describe what the schema actually enforces —
   a lightweight core plus an OPTIONAL PROV-aligned layer — not full PROV
   conformance.
2. **Backward compatibility**: Existing units (which carry only the lightweight
   core, or no provenance at all) must remain valid unchanged.
3. **Expressiveness**: A unit that needs real lineage must be able to carry a
   W3C-PROV entity/activity/agent graph that projects to the `prov:` vocabulary.

### Secondary Decision Drivers

1. **Converter neutrality**: The new fields must nest under `provenance` so the
   markdown ↔ JSON-LD converter (which passes `provenance` through verbatim)
   needs no change.
2. **Clean frontmatter**: PROV keys should be plain camelCase (no `prov:`
   prefix) so YAML frontmatter stays readable; the JSON-LD context carries the
   `prov:` mapping.

## Considered Options

### Option 1: Leave the schema lightweight; soften the docs only

**Description**: Keep `$defs.Provenance` as-is and only rewrite the prose/badge
to stop claiming W3C PROV.

**Advantages**:
- Smallest change.

**Disadvantages**:
- Producers still have no first-class PROV fields; lineage stays informal and
  un-schema'd. The under-description problem is unsolved.

**Risk Assessment**:
- **Technical Risk**: Low, but the goal of deepening provenance is not met.

### Option 2: Add OPTIONAL PROV-aligned fields nested under `provenance`, keep the core, soften the docs (chosen)

**Description**: Extend `$defs.Provenance` in place with OPTIONAL
`wasGeneratedBy` / `wasAttributedTo` / `wasDerivedFrom` and
`sourceRef` / `agent` / `agentVersion`; keep `additionalProperties: true`; add
JSON-LD context terms mapping the plain keys to `prov:`; and rewrite the
spec/README to describe a lightweight core plus an optional PROV layer. The
entity/activity/agent roles are carried by the `@type` values (`prov:Entity`,
`prov:Activity`, `prov:SoftwareAgent`) on the provenance object and its nested
nodes.

**Advantages**:
- Real, schema-described PROV lineage is now expressible.
- Fully backward compatible — every new field is OPTIONAL and the object stays
  open.
- No converter change (fields nest under the passed-through `provenance` key).
- Documentation matches the schema.

**Disadvantages**:
- Slightly larger `$defs.Provenance` surface to maintain.

**Risk Assessment**:
- **Technical Risk**: Low. Additive, OPTIONAL fields; gated by the existing
  round-trip + ajv schema-validation CI.

### Option 3: Make PROV a separate top-level schema property

**Description**: Add a sibling top-level `prov` (or `lineage`) property.

**Advantages**:
- Clean separation of concerns.

**Disadvantages**:
- Requires a converter passthrough/order change and a new top-level field,
  expanding the public surface and breaking the "no converter change"
  constraint.

**Risk Assessment**:
- **Technical Risk**: Medium. Unnecessary surface and churn for no functional
  gain over nesting.

## Decision

MIF provenance is defined as two additive layers within the OPTIONAL
`provenance` object:

1. **Lightweight core** (unchanged): `sourceType`, `confidence`, `trustLevel`,
   plus OPTIONAL `sourceRef`, `agent`, `agentVersion`.
2. **Optional W3C-PROV-aligned layer**: OPTIONAL `wasGeneratedBy`,
   `wasAttributedTo`, `wasDerivedFrom`. `wasDerivedFrom` accepts a single node
   or an array of nodes. Each node is a permissive `ProvNode` — either a plain
   identifier string or an open object such as
   `{"@id": "...", "@type": "prov:Activity"}`. The entity/activity/agent roles
   are carried by the `@type` values (`prov:Entity`, `prov:Activity`,
   `prov:SoftwareAgent`) on the provenance object and its nested nodes, not by
   separate flat fields.

All new fields are OPTIONAL, `$defs.Provenance` keeps
`additionalProperties: true`, and the fields nest under `provenance` so the
converter is untouched. PROV keys are plain camelCase; the JSON-LD context
(`schema/context.jsonld`) maps `wasGeneratedBy` / `wasAttributedTo` /
`wasDerivedFrom` / `wasAssociatedWith` to the `prov:` vocabulary, while `@type`
values use the `prov:` prefix (`prov:Entity`, `prov:Activity`,
`prov:SoftwareAgent`). The `ProvNode` sub-schemas are deliberately permissive
(`additionalProperties: true`) because PROV graphs are open-ended.

Documentation is corrected to match: the spec `§12` describes the two layers,
the `§12.3` example is reconciled to the real field names, the README badge and
feature row read "PROV-aligned" / "lightweight core + optional W3C-PROV layer",
and `§13.3` lists "optional W3C-PROV-aligned provenance".

## Consequences

### Positive

1. **Expressible lineage**: Units can carry a real PROV entity/activity/agent
   graph that projects to `prov:`.
2. **Backward compatible**: All new fields OPTIONAL; existing units validate
   unchanged.
3. **Honest docs**: No more blanket "W3C PROV" claim; required vs. optional is
   explicit.
4. **No converter change**: Fields nest under the passed-through `provenance`
   key.

### Negative

1. **Larger schema surface**: `$defs.Provenance` and a new `$defs.ProvNode` to
   maintain.

### Neutral

1. **Full PROV graphs remain optional**: MIF does not require or fully validate
   a complete W3C PROV graph; it provides PROV-aligned fields and a context
   projection, leaving graph completeness to producers that need it.

## Decision Outcome

Provenance is now a lightweight core plus an additive, OPTIONAL
W3C-PROV-aligned layer. The schema describes the PROV fields, the JSON-LD
context projects them to `prov:`, and the documentation no longer over-claims
full PROV conformance. The `profiles/ai-memory/examples/level-3-full.md`
example exercises the new fields and is covered by the round-trip and
schema-validation CI gates.

## Related Decisions

- [ADR-009: OKF Compliance as a Superset](ADR-009-okf-compliance-superset.md) — provenance remains an OPTIONAL superset field over a conformant OKF bundle.
- [ADR-011: Markdown-Canonical with Derived JSON-LD](ADR-011-markdown-canonical-derived-jsonld.md) — the PROV fields ride the same lossless markdown ↔ JSON-LD projection.
- [ADR-002: Dual Format Design](ADR-002-dual-format-design.md) — the `prov:` context mapping is what makes the JSON-LD projection real linked data.

## Links

- [W3C PROV-DM: The PROV Data Model](https://www.w3.org/TR/prov-dm/) — the vocabulary the optional layer aligns to.
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) — the context mechanism mapping plain keys to `prov:`.

## More Information

- **Date:** 2026-06-26
- **Source:** `schema/mif.schema.json` (`$defs.Provenance`, `$defs.ProvNode`); `schema/context.jsonld`; `SPECIFICATION.md §12`; `profiles/ai-memory/examples/level-3-full.md`.
- **Related ADRs:** ADR-009, ADR-011, ADR-002
