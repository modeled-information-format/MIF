<!-- diataxis_type: explanation -->

# MIF — Modeled Information Format

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](./SPECIFICATION.md)
[![OKF Compliant](https://img.shields.io/badge/OKF-v0.1%20compliant-5c4a32.svg)](./docs/okf-conformance.md)
[![Docs](https://img.shields.io/badge/docs-mif--spec.dev-5c4a32.svg)](https://mif-spec.dev)
[![CI](https://github.com/zircote/MIF/actions/workflows/validate.yml/badge.svg)](https://github.com/zircote/MIF/actions/workflows/validate.yml)
[![JSON-LD](https://img.shields.io/badge/format-JSON--LD-orange.svg)](https://json-ld.org/)
[![W3C PROV](https://img.shields.io/badge/provenance-W3C%20PROV-green.svg)](https://www.w3.org/TR/prov-dm/)

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
| No trust tiers | Provenance `source_type` + `trust_level` |
| Stale-vs-live left to process | Validity windows + TTL/freshness |
| No provenance | W3C PROV |
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
| **Provenance & Trust** | W3C PROV + `source_type` / `trust_level` |
| **Model-Agnostic Embeddings** | Store model + source text for re-embedding |
| **Stable identity** | UUID `id` survives concept relocation |
| **JSON Schema** | Automated validation for the JSON-LD projection |
| **Ontology System** | Base knowledge taxonomy with domain profiles |

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

See [SPECIFICATION.md](./SPECIFICATION.md) for the complete v1.0.0 specification.

## Contributing

This specification is open source. Contributions welcome:

1. Open an issue for discussion
2. Submit PRs for specification changes
3. Implement and share converters

## Related

- [Subcog](https://github.com/zircote/subcog) - AI memory system implementing MIF
- [Mnemonic](https://github.com/zircote/mnemonic) - Claude Code plugin using MIF ontologies

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
