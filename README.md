# Memory Interchange Format (MIF)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec Version](https://img.shields.io/badge/spec-v0.1.0--draft-blue.svg)](./SPECIFICATION.md)
[![Docs](https://img.shields.io/badge/docs-mif--spec.dev-5c4a32.svg)](https://mif-spec.dev)
[![CI](https://github.com/modeled-information-format/MIF/actions/workflows/validate.yml/badge.svg)](https://github.com/modeled-information-format/MIF/actions/workflows/validate.yml)
[![JSON-LD](https://img.shields.io/badge/format-JSON--LD-orange.svg)](https://json-ld.org/)
[![W3C PROV](https://img.shields.io/badge/provenance-W3C%20PROV-green.svg)](https://www.w3.org/TR/prov-dm/)
[![GitHub topics](https://img.shields.io/github/topics/modeled-information-format/MIF)](https://github.com/modeled-information-format/MIF)

An open standard for portable AI memory representation.

## Overview

MIF is a proposed standard that aims to enable interoperability between AI memory providers by defining a common data model with dual representations:

- **Markdown** (`.memory.md`) - Human-readable, Obsidian-compatible
- **JSON-LD** (`.memory.json`) - Machine-processable, semantically linked

## Why MIF?

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/readme-infographic-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/readme-infographic.svg">
  <img src=".github/readme-infographic.svg" alt="How MIF Works" width="100%">
</picture>

The AI memory ecosystem is fragmented. Mem0, Zep, Letta, LangMem, Subcog, and others all use proprietary schemas. MIF solves:

- **Vendor lock-in** - Move memories between providers
- **Data ownership** - Local-first, plain text files
- **Interoperability** - Common vocabulary for relationships and entities
- **Future-proofing** - Standard formats survive provider discontinuation

## Quick Start

### Minimal Memory (Markdown)

```markdown
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
created: 2026-01-15T10:30:00Z
namespace: _semantic/preferences
---

User prefers dark mode for all applications.
```

### Minimal Memory (JSON-LD)

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:550e8400-e29b-41d4-a716-446655440000",
  "memoryType": "semantic",
  "namespace": "_semantic/preferences",
  "content": "User prefers dark mode for all applications.",
  "created": "2026-01-15T10:30:00Z"
}
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Dual Format** | Markdown AND JSON-LD representations |
| **Obsidian Native** | Valid Obsidian notes with wiki-links |
| **Typed Relationships** | 9 core relationship types (RelatesTo, DerivedFrom, Supersedes, etc.) |
| **Entity Types** | Person, Organization, Technology, Concept, File |
| **Bi-Temporal** | Track when recorded AND when facts are valid |
| **Flexible Namespaces** | `_public`, `_shared`, `{org}/{scope}+` with reserved prefixes |
| **Model-Agnostic Embeddings** | Store model + source text for re-embedding |
| **Citations** | Structured references with type/role taxonomy (Level 3) |
| **W3C PROV** | Standard provenance tracking |
| **JSON Schema** | Automated validation for MIF documents |
| **Ontology System** | Three-type hierarchy with domain extensions |

## Ontology System

MIF includes an ontology system for organizing memories into three base types:

```
semantic/              # Facts, concepts, relationships
├── decisions/         # Architectural choices, rationale
├── knowledge/         # APIs, context, learnings, security
└── entities/          # Entity definitions

episodic/              # Events, experiences, timelines
├── incidents/         # Production issues, postmortems
├── sessions/          # Debug sessions, work sessions
└── blockers/          # Impediments, issues

procedural/            # Step-by-step processes
├── runbooks/          # Operational procedures
├── patterns/          # Code conventions, testing
└── migrations/        # Migration steps, upgrades
```

### Features

- **Hierarchical namespaces** - Cognitive memory types with sub-namespaces
- **Entity types** - Define custom entities with traits and schemas
- **Discovery patterns** - Auto-detect capture opportunities from content
- **JSON-LD export** - Semantic web compatibility via `yaml2jsonld.py`
- **Extensible** - Domain-specific ontologies extend the base

See [ontologies/](./ontologies/) for base ontology and examples.

## Specification

See [SPECIFICATION.md](./SPECIFICATION.md) for the complete technical specification.

## LLM-friendly documentation

The spec site publishes [`llms.txt`](https://mif-spec.dev/llms.txt) for large
language models, following the [llms.txt convention](https://llmstxt.org/). It is
generated at build time by the `starlight-llms-txt` plugin (never hand-edited),
alongside `llms-full.txt` (full corpus) and `llms-small.txt` (condensed):

- <https://mif-spec.dev/llms.txt>
- <https://mif-spec.dev/llms-full.txt>
- <https://mif-spec.dev/llms-small.txt>

## Validation

JSON Schema files are available for automated validation:

```bash
# Validate a MIF document
npx ajv validate -s schema/mif.schema.json -d your-memory.json

# Validate citations only
npx ajv validate -s schema/citation.schema.json -d citation.json

# Validate ontology definitions
npx ajv validate -s schema/ontology/ontology.schema.json -d ontology.yaml
```

### Ontology Conversion

Convert YAML ontologies to JSON-LD for semantic web compatibility:

```bash
python scripts/yaml2jsonld.py ontologies/mif-base.ontology.yaml
python scripts/yaml2jsonld.py --all  # Convert all ontologies
```

## Examples

See the [examples/](./examples/) directory for:

- Minimal memories (Level 1)
- Standard memories with relationships (Level 2)
- Full-featured memories with temporal, provenance, and citations (Level 3)

## Conformance Levels

| Level | Requirements |
|-------|--------------|
| **Level 1: Core** | id, type, content, created |
| **Level 2: Standard** | + namespace, entities, relationships, timestamps |
| **Level 3: Full** | + bi-temporal, decay, provenance, embeddings, citations |

## Migration

MIF includes migration guides for:

- Mem0
- Zep
- Letta (Agent File)
- Subcog
- Basic Memory

## Contributing

This specification is open source. Contributions welcome:

1. Open an issue for discussion
2. Submit PRs for specification changes
3. Implement and share converters

## Related

- [Subcog](https://github.com/zircote/subcog) - AI memory system implementing MIF
- [Mnemonic](https://github.com/modeled-information-format/mnemonic) - Claude Code plugin using MIF ontologies
- [Issue #82](https://github.com/zircote/subcog/issues/82) - Original proposal

## Citing This Project

If you use MIF in your research or projects, please cite it:

```bibtex
@software{allen_mif_2026,
  author       = {Allen, Robert},
  title        = {{Memory Interchange Format (MIF)}},
  version      = {0.1.0},
  date         = {2026-01-23},
  url          = {https://mif-spec.dev},
  license      = {MIT}
}
```

You can also use GitHub's built-in **"Cite this repository"** button on the repository page to get an auto-generated citation in APA or BibTeX format.

### Acknowledgments

MIF builds on the following standards:

> Manu Sporny, Dave Longley, Gregg Kellogg, Markus Lanthaler, Pierre-Antoine Champin, and Niklas Lindstrom. *JSON-LD 1.1: A JSON-based Serialization for Linked Data.* W3C Recommendation, 2020. https://www.w3.org/TR/json-ld11/

> Luc Moreau and Paolo Missier. *PROV-DM: The PROV Data Model.* W3C Recommendation, 2013. https://www.w3.org/TR/prov-dm/

## License

[MIT](./LICENSE)
