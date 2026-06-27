<!-- diataxis_type: explanation -->

# MIF — Modeled Information Format

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](./SPECIFICATION.md)
[![OKF Compliant](https://img.shields.io/badge/OKF-v0.1%20compliant-5c4a32.svg)](./docs/okf-conformance.md)
[![Docs](https://img.shields.io/badge/docs-mif--spec.dev-5c4a32.svg)](https://mif-spec.dev)
[![CI](https://github.com/modeled-information-format/MIF/actions/workflows/validate.yml/badge.svg)](https://github.com/modeled-information-format/MIF/actions/workflows/validate.yml)
[![JSON-LD](https://img.shields.io/badge/format-JSON--LD-orange.svg)](https://json-ld.org/)
[![PROV-aligned](https://img.shields.io/badge/provenance-PROV--aligned-green.svg)](https://www.w3.org/TR/prov-dm/)

**MIF is the opinionated, OKF-compliant content model that fills OKF's
deliberately empty envelope.** [OKF](https://github.com/google/open-knowledge-format)
defines the transport surface — a directory of markdown files with YAML
frontmatter and one required `type` field — and explicitly leaves the *content
model* open. MIF supplies the concrete type system, typed relationships,
provenance/trust, and validity/freshness semantics. **AI memory is the first
domain profile of MIF, not its identity.**

> **Brand note (v1.0.0):** The `MIF` mark is retained; the working expansion for
> this release is *Modeled Information Format*. Whether *Memory Interchange
> Format* is kept as the name of the AI Memory profile is a maintainer decision
> pending before final release.

## Overview

A MIF bundle is a directory tree of `.md` concept files — **a valid OKF
bundle**. Markdown is the canonical representation; JSON-LD is a derived,
regenerable projection.

- **Markdown** (`.md`) — canonical, human-readable, Obsidian-compatible.
- **JSON-LD** (`*.jsonld`, derived) — machine-processable, semantically linked,
  regenerated from markdown with `scripts/mif_convert.py`.

Every concept declares one of three **base knowledge types**:

- `semantic` — declarative knowledge: facts, concepts, decisions, schemas.
- `episodic` — time-bound records: events, incidents, changelog/deprecation.
- `procedural` — how-to knowledge: runbooks, processes, patterns, migrations.

## MIF answers OKF's open questions

OKF deliberately refuses to define a content model. MIF supplies opinionated
answers to exactly the questions OKF leaves open:

| OKF open design space | MIF's opinionated answer |
| --- | --- |
| No concept-type taxonomy | `semantic` / `episodic` / `procedural` base types |
| Untyped markdown-link edges | Typed relationships (overlay on OKF links) |
| No merge / contradiction semantics | `Supersedes`, `ConflictsWith` |
| No trust tiers | Provenance `sourceType` + `trustLevel` |
| Stale-vs-live left to process | Validity windows + TTL/freshness |
| No provenance | Lightweight provenance core + optional W3C-PROV-aligned layer |
| Markdown only | First-class JSON-LD projection |

OKF compliance is achieved as a **superset, not by subordination**: every MIF
bundle validates as a conformant OKF bundle, but MIF remains an independent
specification with its own identity model and governance, pinned to OKF v0.1 in
[docs/okf-conformance.md](./docs/okf-conformance.md).

## Quick Start

A minimal concept (canonical markdown):

```markdown
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
created: 2026-01-15T10:30:00Z
namespace: _semantic/preferences
---

A declarative fact stated in plain markdown.
```

A concept with typed relationships — authoritative in frontmatter, mirrored as
OKF-legible body links:

```markdown
---
id: 7b3c1e90-5a2f-4c8d-9e10-2f6a4b8c1d3e
type: semantic
created: 2026-01-15T10:30:00Z
title: API Rate Limit Policy
relationships:
  - type: derived-from
    target: /episodic/incident-2026-01-rate-spike.md
---

# API Rate Limit Policy

The gateway enforces 600 req/min per key.

## Relationships

- derived-from [Rate Spike Incident](/episodic/incident-2026-01-rate-spike.md)
```

The derived JSON-LD projection is regenerated, never hand-edited:

```bash
python scripts/mif_convert.py emit-jsonld examples --out-dir jsonld
```

## Key Features

| Feature | Description |
|---------|-------------|
| **OKF compliant** | Every bundle is a valid OKF bundle (tested invariant) |
| **Markdown canonical** | `.md` is the source of truth; JSON-LD is derived |
| **Typed Relationships** | Typed overlay on standard OKF markdown-link edges |
| **Base types** | `semantic` / `episodic` / `procedural` knowledge taxonomy |
| **Bi-Temporal** | Validity windows & freshness (when recorded AND when valid) |
| **Provenance & Trust** | Lightweight `sourceType` / `trustLevel` core + optional W3C-PROV-aligned layer |
| **Model-Agnostic Embeddings** | Store model + source text for re-embedding |
| **Stable identity** | UUID `id` survives concept relocation |
| **JSON Schema** | Automated validation for the JSON-LD projection |
| **Ontology System** | Base knowledge taxonomy with domain profiles |

## What a MIF memory can carry

A single MIF unit already models **27 top-level properties** — far more than the
six required for a minimal record. They are grouped below by
[conformance level](./SPECIFICATION.md#13-conformance-levels): **Level 1 (Core,
required to conform)**, **Level 2 (Standard, recommended)**, and **Level 3
(Full, optional)**. Level 1 is the schema's required set plus the structural
fields validated at that tier; everything in the Standard tier is Level 2; the
fields the spec marks `(Level 3)` are Level 3.

For per-field detail, types, patterns, and examples, see the
[Schema Reference](./docs/SCHEMA-REFERENCE.md). The authoritative, machine-checkable
definition of every property is [`schema/mif.schema.json`](./schema/mif.schema.json).

### Level 1 — Core (required to conform)

| Property | Purpose |
|----------|---------|
| `@context` | JSON-LD context binding terms to the MIF vocabulary |
| `@type` | Document type (`"Concept"` or `"Memory"`, or an array containing `"Concept"`); the projection emits `"Concept"` |
| `@id` | Unique identifier in `urn:mif:` URN form |
| `conceptType` | Knowledge taxonomy: `semantic` / `episodic` / `procedural` |
| `memoryType` | **Deprecated** v0.1 alias for `conceptType`, kept for back-compat |
| `content` | The memory content, in Markdown |
| `created` | Creation timestamp (ISO 8601) |

> Property names above are the JSON-LD projection. In Markdown frontmatter,
> `type` maps to `conceptType` in JSON-LD; `memoryType` is a separate deprecated
> frontmatter key passed through as `memoryType`, not an alias for `type`.
>
> The Level 1 rows omit the per-field reference links used for Level 2/3 because
> these are the core/required fields defined authoritatively in
> [`schema/mif.schema.json`](./schema/mif.schema.json) — treat that schema as the
> source of truth for required field names, types, and constraints.

### Level 2 — Standard (recommended)

| Property | Purpose | Reference |
|----------|---------|-----------|
| `title` | Human-readable title | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `description` | OKF-recommended description (mapped from MIF `summary`) | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `modified` | Last-modification timestamp (ISO 8601) | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `timestamp` | OKF-recommended mirror of `modified` (or `created`) | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `namespace` | Hierarchical scope for the memory | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `tags` | Classification tags | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `aliases` | Alternative names for the memory | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `properties` | First-class scalar key/value pairs with no concept target | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `blocks` | Named block references (`^block-id`) with their text, for granular linking | [Basic metadata](./docs/SCHEMA-REFERENCE.md#basic-metadata) |
| `ontology` | Reference to the ontology this memory conforms to | [Ontology reference](./docs/SCHEMA-REFERENCE.md#ontology-reference) |
| `entity` | Structured entity data for ontology-typed memories | [Entities](./docs/SCHEMA-REFERENCE.md#entities) |
| `entities` | Referenced entities (people, orgs, technologies, …) | [Entities](./docs/SCHEMA-REFERENCE.md#entities) |
| `relationships` | Typed relationships to other memories | [Relationships](./docs/SCHEMA-REFERENCE.md#relationships) |
| `temporal` | Temporal validity data (timestamps) | [Temporal metadata](./docs/SCHEMA-REFERENCE.md#temporal-metadata) |

> The `temporal` field enters at Level 2 for basic timestamps; its bi-temporal
> model and decay-function sub-features are Level 3.

### Level 3 — Full (optional)

| Property | Purpose | Reference |
|----------|---------|-----------|
| `provenance` | Source and trust data (W3C PROV + `sourceType` / `trustLevel`) | [Provenance](./docs/SCHEMA-REFERENCE.md#provenance) |
| `embedding` | Embedding-model reference (model + source text for re-embedding) | [Embedding reference](./docs/SCHEMA-REFERENCE.md#embedding-reference) |
| `citations` | Citation references with rich metadata | [Citations](./docs/SCHEMA-REFERENCE.md#citations) |
| `summary` | Compressed content summary (max 500 chars) | [Compression](./docs/SCHEMA-REFERENCE.md#compression-level-3) |
| `compressedAt` | When compression was applied | [Compression](./docs/SCHEMA-REFERENCE.md#compression-level-3) |
| `extensions` | Provider-specific extension data | [Extensions](./docs/SCHEMA-REFERENCE.md#extensions) |

## OKF conformance & validation

```bash
# OKF conformance + relationship sync + lossless round-trip
python scripts/okf_validate.py

# Lossless markdown -> json-ld -> markdown round trip
python scripts/mif_convert.py roundtrip examples profiles/ai-memory/examples

# JSON Schema validation of the JSON-LD projection
npx ajv validate -s schema/mif.schema.json -d your-concept.jsonld
```

See [docs/okf-conformance.md](./docs/okf-conformance.md) for the pinned OKF v0.1
criteria and the MIF → OKF mapping.

## Examples

The [examples/](./examples/) directory is a generalized (non-memory) core bundle
demonstrating the three base types with body-link relationships. Memory-flavored
examples live under [profiles/ai-memory/examples/](./profiles/ai-memory/examples/).

## AI Memory profile

Memory-specific material — forgetting-curve decay tuning, episodic *session*
framing, recall-oriented embeddings, and migration guides for Mem0, Zep, Letta,
Subcog, and Basic-Memory — lives in the AI Memory profile:
[profiles/ai-memory/](./profiles/ai-memory/).

## Migration

Upgrading a `0.1.0-draft` bundle? See [MIGRATION.md](./MIGRATION.md) and run:

```bash
python scripts/migrate_0_1_to_1_0.py <old-bundle> <new-bundle>
```

## Specification

See [SPECIFICATION.md](./SPECIFICATION.md) for the complete v1.0.0 specification,
and the [Schema Reference](./docs/SCHEMA-REFERENCE.md) for a per-field reference to
the top-level properties. The authoritative, machine-checkable definition of every
property is [`schema/mif.schema.json`](./schema/mif.schema.json).

## Contributing

This specification is open source. Contributions welcome:

1. Open an issue for discussion
2. Submit PRs for specification changes
3. Implement and share converters

## Related

- [Subcog](https://github.com/zircote/subcog) - AI memory system implementing MIF
- [Mnemonic](https://github.com/modeled-information-format/mnemonic) - Claude Code plugin using MIF ontologies

## Citing This Project

If you use MIF in your research or projects, please cite it:

```bibtex
@software{allen_mif_2026,
  author       = {Allen, Robert},
  title        = {{MIF: Modeled Information Format}},
  version      = {1.0.0},
  date         = {2026-06-18},
  url          = {https://mif-spec.dev},
  license      = {MIT}
}
```

You can also use GitHub's built-in **"Cite this repository"** button on the
repository page to get an auto-generated citation in APA or BibTeX format.

### Acknowledgments

MIF builds on the following standards:

> Manu Sporny, Dave Longley, Gregg Kellogg, Markus Lanthaler, Pierre-Antoine Champin, and Niklas Lindstrom. *JSON-LD 1.1: A JSON-based Serialization for Linked Data.* W3C Recommendation, 2020. https://www.w3.org/TR/json-ld11/

> Luc Moreau and Paolo Missier. *PROV-DM: The PROV Data Model.* W3C Recommendation, 2013. https://www.w3.org/TR/prov-dm/

## License

[MIT](./LICENSE)
