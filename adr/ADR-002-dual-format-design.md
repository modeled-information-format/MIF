---
title: "Dual-Format Design (Markdown + JSON-LD)"
description: "MIF supports both Markdown and JSON-LD as first-class representations of a memory; the original co-equality framing was later refined by ADR-011 so that Markdown is canonical and JSON-LD is a derived projection."
type: adr
category: architecture
tags:
  - dual-format
  - json-ld
  - markdown
  - interoperability
status: accepted
created: 2026-01-27
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - markdown
  - json-ld
  - yaml
audience:
  - developers
  - architects
related:
  - ADR-003-obsidian-compatibility.md
  - ADR-007-github-raw-urls-for-schema-ids.md
  - ADR-011-markdown-canonical-derived-jsonld.md
---

# ADR-002: Dual-Format Design (Markdown + JSON-LD)

## Status

Accepted

Refined by ADR-011 (Markdown is canonical; JSON-LD is a derived projection).

The dual-format decision below stands: MIF retains two representations of a
memory, Markdown and JSON-LD. What ADR-011 refined is the *relationship*
between them. The original ADR framed the two formats as "semantically
equivalent" and "bidirectionally convertible" co-equals. ADR-011 makes the
Markdown `.md` concept file the **canonical source of truth** and the JSON-LD
`.jsonld` document a **derived projection** reproducible from it (SPECIFICATION.md
Invariant 2). The original co-equality reasoning is preserved below and
annotated inline where it appears; see the `## Amendment` section for the
refinement.

## Context

### Background and Problem Statement

MIF needs to serve audiences with opposed ergonomic needs from one memory model:

- Human authoring and reading of memories.
- Machine processing and validation.
- Semantic-web integration for linked data.
- Existing knowledge-management workflows (notably Obsidian vaults).

No single serialization satisfies all four well. A human-friendly format
(Markdown) lacks the structure machines want; a machine-friendly format
(JSON-LD, RDF) is hostile to hand-authoring. The architectural question is which
representation(s) MIF should adopt as first-class, and how they relate.

### Current Limitations

- A single human-readable format gives no validatable, machine-addressable
  structure and no semantic-web identity.
- A single machine format makes authoring and review painful and breaks the
  Obsidian-compatibility goal (ADR-003).
- Supporting two formats without a defined relationship risks silent divergence:
  two representations of "the same" memory that disagree, with no rule for which
  one wins. (This is exactly the gap ADR-011 later closed.)

## Decision Drivers

### Primary Decision Drivers

1. **Human authorability**: Memories must be writable and readable by people in
   a familiar, low-friction format.
2. **Machine processability**: Memories must be structured, validatable, and
   addressable for tooling and semantic-web consumers.
3. **Ecosystem fit**: The human format must work in existing knowledge-management
   tools (Obsidian, VS Code, plain text editors).

### Secondary Decision Drivers

1. **Progressive disclosure**: Simple for basic use, rich for advanced use —
   one shouldn't pay the cost of the other.
2. **Convertibility**: The two representations must be mechanically derivable
   from each other so they don't drift by hand.

## Considered Options

### Option 1: JSON-only

**Description**: Represent every memory solely as JSON (later JSON-LD).

**Advantages**:
- Fully structured and machine-processable.
- Trivial to validate and address programmatically.

**Disadvantages**:
- Poor human readability; awkward to edit by hand.
- Breaks the Obsidian / plain-text authoring workflow entirely.

**Risk Assessment**:
- **Technical Risk**: Low.
- **Ecosystem Risk**: High. Abandons the human-authoring and Obsidian goals that
  motivate MIF.

### Option 2: Markdown-only

**Description**: Represent every memory solely as Markdown with YAML frontmatter.

**Advantages**:
- Excellent human authoring and reading; native Obsidian fit.

**Disadvantages**:
- Limited semantic structure; no JSON-Schema validation surface.
- No semantic-web / linked-data identity.

**Risk Assessment**:
- **Technical Risk**: Low.
- **Ecosystem Risk**: Medium. Closes the door on machine/semantic-web consumers.

### Option 3: YAML

**Description**: Use YAML documents as the single memory format.

**Advantages**:
- Reasonable balance of human and machine legibility.

**Disadvantages**:
- No semantic-web support (no `@context`, no linked-data identity).
- Body content (prose) sits awkwardly inside a data-oriented format.

**Risk Assessment**:
- **Technical Risk**: Low.
- **Ecosystem Risk**: Medium. Lacks the linked-data integration MIF targets.

### Option 4: RDF / Turtle

**Description**: Represent memories in RDF, serialized as Turtle.

**Advantages**:
- Excellent semantics; first-class linked-data graph.

**Disadvantages**:
- Poor human authoring; steep learning curve.
- Incompatible with the Obsidian / plain-text workflow.

**Risk Assessment**:
- **Technical Risk**: Medium.
- **Ecosystem Risk**: High. Sacrifices human authorability, a primary driver.

### Option 5: Dual format — Markdown + JSON-LD (chosen)

**Description**: Support **both** Markdown (`.md`) and JSON-LD (`.jsonld`) as
first-class representations of a memory. Markdown serves human authoring and
Obsidian compatibility; JSON-LD serves machine processing and semantic-web
integration. The two are mechanically convertible.

**Technical Characteristics**:
- YAML frontmatter in the Markdown file maps directly to JSON-LD properties.
- The JSON-LD `@context` provides the RDF vocabulary mapping.
- The Markdown body is carried in the JSON-LD `content` field.

**Advantages**:
- Human authors write Markdown; machines consume JSON-LD — both first-class.
- Semantic-web compatibility via the JSON-LD `@context`.
- Works with existing tools (Obsidian, VS Code).
- Progressive disclosure: simple for basic use, rich for advanced.

**Disadvantages**:
- Dual-representation complexity.
- A relationship between the two must be defined and enforced or they drift.
  *(The original ADR assumed symmetric "format parity"; ADR-011 replaced that
  with an asymmetric canonical-source / derived-projection rule — see
  `## Amendment`.)*
- Conversion tooling is required (`scripts/mif_convert.py`).

**Risk Assessment**:
- **Technical Risk**: Low to Medium. Two serializations to keep in sync.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: Low. Satisfies both human and machine consumers.

## Decision

Support both **Markdown** and **JSON-LD** as first-class formats for a MIF memory.

### Markdown Format

```markdown
---
id: uuid
type: semantic
namespace: _semantic/knowledge
created: 2026-01-27T10:00:00Z
---

# Memory Title

Memory content in readable Markdown...
```

### JSON-LD Format

> **Historical snapshot (original 2026-01-27 decision).** The JSON-LD object
> below is the example exactly as the original ADR recorded it. It is **not**
> the current emitted schema: the v1.0 converter emits `conceptType` (not
> `memoryType`) and an `@id` of the form `urn:mif:{id}` (no `memory:` segment),
> and the canonical source is now the Markdown file (ADR-011). It is retained
> here as a record of the original decision, not as a current projection example.

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:memory:uuid",
  "memoryType": "semantic",
  "namespace": "_semantic/knowledge",
  "created": "2026-01-27T10:00:00Z",
  "content": "Memory content..."
}
```

Both formats are semantically equivalent and bidirectionally convertible.
*(Original co-equality framing. **Refined by ADR-011:** Markdown is the
canonical source of truth and JSON-LD is a derived projection reproducible from
it — the conversion is lossless on a `markdown → json-ld → markdown` round trip
for conformance-level data, but the two are no longer treated as co-equal peers.
See `## Amendment`.)*

## Consequences

### Positive

1. **Human authoring**: Authors write Markdown — familiar, readable, reviewable.
2. **Machine processing**: Machines consume structured, validatable JSON-LD.
3. **Semantic-web compatibility**: The JSON-LD `@context` gives memories a
   linked-data identity.
4. **Tool support**: Existing tools (Obsidian, VS Code) work unchanged.
5. **Progressive disclosure**: Simple for basic use, rich for advanced.

### Negative

1. **Dual-representation complexity**: Two serializations exist for one memory.
2. **Must maintain format parity**: The two representations must stay in sync.
   *(Original framing. **Refined by ADR-011:** the obligation is not symmetric
   "parity" but a one-way derivation — JSON-LD is regenerated from canonical
   Markdown, so there is one source to maintain and a reproducible projection,
   not two peers to reconcile.)*
3. **Conversion tooling required**: `scripts/mif_convert.py` performs and
   round-trip-verifies the conversion.

### Neutral

1. **Two artifact classes by design**: `.md` concept files and `.jsonld`
   projections coexist; after ADR-011 their roles are asymmetric (source vs.
   derived) rather than equivalent.

## Decision Outcome

The dual-format approach achieves the primary drivers: human authorability
(Markdown / Obsidian), machine processability (JSON-LD), and ecosystem fit. The
one gap in the original decision — an undefined relationship between the two
formats — was closed by ADR-011, which designates Markdown canonical and JSON-LD
derived. Mitigations:

- The conversion is implemented and round-trip-verified by
  `scripts/mif_convert.py` (`roundtrip` and `emit-jsonld` subcommands).
- The canonical/derived rule (ADR-011, SPECIFICATION.md Invariant 2) removes the
  silent-divergence risk inherent in treating the two formats as co-equal.

## Related Decisions

- [ADR-003: Obsidian Compatibility](ADR-003-obsidian-compatibility.md) — the Markdown format is designed to be valid Obsidian notes, which is the constraint that makes Markdown the natural human-authoring surface here.
- [ADR-007: GitHub Raw URLs for Schema IDs](ADR-007-github-raw-urls-for-schema-ids.md) — the JSON-LD projection requires resolvable schema `$id` / `@context` URIs, the scheme that ADR establishes.
- [ADR-011: Markdown-Canonical with Derived JSON-LD](ADR-011-markdown-canonical-derived-jsonld.md) — refines this decision: Markdown is the canonical source of truth and JSON-LD is a derived projection, replacing the original co-equality framing.

## Links

- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) — the linked-data serialization MIF projects to.
- [Obsidian](https://obsidian.md/) — the knowledge-management tool the Markdown format targets (ADR-003).

## More Information

- **Date:** 2026-01-27 (original); refined by ADR-011
- **Source:** SPECIFICATION.md §2.1 "Dual Representation"; `scripts/mif_convert.py` (markdown ↔ JSON-LD converter).
- **Related ADRs:** ADR-003, ADR-007, ADR-011

## Amendment

### Refined by ADR-011 — Markdown canonical, JSON-LD derived

The original decision (2026-01-27) framed Markdown and JSON-LD as **co-equal**
representations: "semantically equivalent," with "format parity" to be
maintained between two peers. ADR-011 refined this without discarding the
dual-format decision itself.

Under the refined model:

- The Markdown `.md` concept file is the **canonical source of truth**
  (SPECIFICATION.md Invariant 2).
- The JSON-LD `.jsonld` document is a **derived projection**, reproducible by
  running the converter over the canonical Markdown.
- The relationship is a one-way derivation that is **lossless on a
  `markdown → json-ld → markdown` round trip** for conformance-level data, not a
  symmetric parity obligation between two independently-authored artifacts.

**Rationale for the refinement:** Treating two serializations as co-equal leaves
no rule for which wins when they disagree, inviting silent divergence. Naming
Markdown canonical and JSON-LD derived gives a single editable source, makes the
projection reproducible and CI-verifiable, and keeps the `.jsonld` artifact
outside OKF's `*.md` legibility surface (ADR-009) without sacrificing the
machine/semantic-web consumers that motivated the dual-format decision. The
dual-format decision is therefore **intact**; only the formats' relationship
changed from peer-equivalence to source-and-projection.

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Dual representation (`.md` human-readable, `.jsonld` machine-processable) defined as first-class | `SPECIFICATION.md` | L103-L108 | compliant |
| "Both representations MUST be losslessly convertible to each other" (the convertibility claim this ADR makes) | `SPECIFICATION.md` | L110 | compliant |
| Refinement: Markdown is the source of truth (Invariant 2) and JSON-LD is a *derived* projection — basis for the ADR-011 amendment | `scripts/mif_convert.py` | L2-L9 | compliant |
| Converter implements `to-jsonld` / `to-markdown` and lossless `roundtrip` over bundles | `scripts/mif_convert.py` | L19-L22, L286-L295 | compliant |
| Derived-projection emitter (`emit-jsonld`) regenerates `.jsonld` from canonical `.md` | `scripts/mif_convert.py` | L267-L279 | compliant |

**Summary:** The dual-representation design and the lossless-convertibility
requirement are both stated normatively in SPECIFICATION.md §2.1. The
canonical-source / derived-projection refinement attributed to ADR-011 is
directly evidenced by the converter's own module docstring (".md concept file is
the source of truth (Invariant 2)"; "JSON-LD is a *derived* projection"), and
the converter implements both the round-trip verification and the derived-JSON-LD
emitter described in this ADR.

**Action Required:** None.
