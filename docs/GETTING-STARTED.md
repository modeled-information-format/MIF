---
diataxis_type: tutorial
---

# Getting Started with MIF

This guide walks you through implementing the Modeled Information Format (MIF) in your project.

## Prerequisites

- Basic understanding of JSON-LD or YAML
- A text editor or IDE
- (Optional) Python 3.8+ for tooling

## Quick Start

### Step 1: Create Your First Memory

MIF memories can be written in Markdown or JSON-LD. Start with Markdown:

```markdown
---
id: my-first-memory
type: semantic
created: 2026-01-26T10:00:00Z
---

User prefers dark mode for all applications.
```

Save this as `my-first-memory.memory.md`.

### Step 2: Add Metadata

Expand with recommended fields:

```markdown
---
id: a1b2c3d4-5678-90ab-cdef-1234567890ab
type: semantic
created: 2026-01-26T10:00:00Z
modified: 2026-01-26T10:00:00Z
namespace: _semantic/preferences
title: "Dark Mode Preference"
tags:
  - ui
  - accessibility
  - preference
---

# Dark Mode Preference

User prefers dark mode for all applications including:
- IDE and code editors
- Terminal emulators
- Web applications
- Mobile apps
```

### Step 3: Declare an Ontology (Optional)

If using a custom ontology, declare it:

```markdown
---
id: a1b2c3d4-5678-90ab-cdef-1234567890ab
type: semantic
created: 2026-01-26T10:00:00Z
ontology:
  id: regenerative-agriculture
  version: "0.1.0"
namespace: _semantic/livestock
---

Herd of 85 Angus-cross beef cattle managed with adaptive multi-paddock grazing.
```

## Memory Types

MIF uses three base memory types reflecting how human cognition organizes information:

| Type | Description | Use For |
|------|-------------|---------|
| `semantic` | Facts, concepts, and knowledge | Decisions, preferences, facts, domain knowledge |
| `episodic` | Events and experiences | Incidents, sessions, conversations, timelines |
| `procedural` | How-to processes | Runbooks, patterns, migration guides, workflows |

Specific categorization is expressed through namespaces (e.g., `_semantic/decisions`, `_episodic/incidents`).

## Conformance Levels

MIF supports three conformance levels:

### Level 1: Core (Minimal)

Required fields only:

```yaml
---
id: uuid-here
type: semantic
created: 2026-01-26T10:00:00Z
---

Memory content here.
```

### Level 2: Standard (Recommended)

Add namespaces, entities, and relationships:

```yaml
---
id: uuid-here
type: semantic
created: 2026-01-26T10:00:00Z
modified: 2026-01-26T10:00:00Z
namespace: _semantic/decisions
title: "Use PostgreSQL for Data Storage"
tags:
  - database
  - architecture
---

# Use PostgreSQL for Data Storage

## Context

We need a relational database for the new service.

## Decision

PostgreSQL for:
- Strong JSON support
- Excellent performance
- Team familiarity

## Relationships

- relates-to [[database-requirements]]
- supersedes [[sqlite-investigation]]

## Entities

- @[[PostgreSQL|Technology]]
- @[[MySQL|Technology]]
```

### Level 3: Full

Add temporal metadata, provenance, and citations:

```yaml
---
id: uuid-here
type: semantic
created: 2026-01-26T10:00:00Z
temporal:
  valid_from: 2026-01-26T00:00:00Z
  recorded_at: 2026-01-26T10:00:00Z
  ttl: P365D
  decay:
    model: exponential
    halfLife: P30D
    strength: 1.0
provenance:
  source_type: user_explicit
  agent: claude-opus-4
  confidence: 0.95
  trust_level: user_stated
citations:
  - type: documentation
    title: "PostgreSQL Documentation"
    url: https://www.postgresql.org/docs/
    role: background
    relevance: 0.9
---
```

> **Decay Values:** The `halfLife: P30D` means memory strength halves every 30 days. Common values: P7D (short-term), P14D (medium-term), P30D (long-term). These are pragmatic defaults inspired by Ebbinghaus's forgetting curve research. See [SPECIFICATION.md Section 9.3](../SPECIFICATION.md#93-decay-rationale) for details.

> **Naming Convention:** Markdown frontmatter uses `snake_case` field names (`valid_from`, `source_type`, `trust_level`). JSON-LD uses `camelCase` equivalents (`validFrom`, `sourceType`, `trustLevel`). Exception: `halfLife` uses camelCase in both formats. See the [Field Name Mapping](../examples/README.md#field-name-mapping) table for a complete reference.

## Directory Structure

Organize your MIF vault using the three base types:

```
my-project/
├── .mif/
│   ├── config.yaml           # Vault configuration
│   └── entities/             # Entity definitions
├── memories/
│   ├── semantic/             # Facts, concepts, knowledge
│   │   ├── decisions/
│   │   ├── knowledge/
│   │   └── entities/
│   ├── episodic/             # Events, experiences
│   │   ├── incidents/
│   │   └── sessions/
│   └── procedural/           # Processes, how-to
│       ├── runbooks/
│       └── patterns/
└── ontology.yaml             # Custom ontology (optional)
```

## Using Custom Ontologies

### Create an Ontology

```yaml
# ontology.yaml
ontology:
  id: my-project
  version: "0.1.0"
  description: "Custom ontology for my project"

namespaces:
  features:
    description: "Product features"
    type_hint: semantic
  sprints:
    description: "Sprint records"
    type_hint: episodic

entity_types:
  - name: feature
    base: semantic
    traits: [lifecycle]
    schema:
      required: [name, status]
      properties:
        name: { type: string }
        status: { type: string, enum: [planned, active, deprecated] }
```

### Reference in Memories

```yaml
---
id: feature-dark-mode
type: semantic
created: 2026-01-26T10:00:00Z
ontology:
  id: my-project
  version: "0.1.0"
namespace: _semantic/features
---

# Dark Mode Feature

Status: active
Priority: high
```

## JSON-LD Format

For machine processing, use JSON-LD:

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "memoryType": "semantic",
  "content": "User prefers dark mode for all applications.",
  "created": "2026-01-26T10:00:00Z",
  "ontology": {
    "@type": "OntologyReference",
    "id": "mif-base",
    "version": "0.1.0"
  },
  "namespace": "_semantic/preferences",
  "tags": ["ui", "accessibility"]
}
```

## Validation

Validate MIF documents using JSON Schema:

```bash
# Install ajv-cli
npm install -g ajv-cli

# Validate a memory
npx ajv validate -s schema/mif.schema.json -d my-memory.json

# Validate a citation
npx ajv validate -s schema/citation.schema.json -d citation.json

# Validate an ontology
npx ajv validate -s schema/ontology/ontology.schema.json -d ontology.yaml
```

## Converting Ontologies

Convert YAML ontologies to JSON-LD:

```bash
# Single file
python scripts/yaml2jsonld.py ontologies/my-ontology.ontology.yaml

# All ontologies
python scripts/yaml2jsonld.py --all
```

## Next Steps

- Read the [full specification](../SPECIFICATION.md)
- Explore [example memories](../examples/)
- Review [schema reference](./SCHEMA-REFERENCE.md)
- Check [migration guides](./MIGRATION-GUIDE.md) if converting from other systems

## Getting Help

- [GitHub Issues](https://github.com/modeled-information-format/MIF/issues)
- [Specification](../SPECIFICATION.md)
- [Contributing Guide](../CONTRIBUTING.md)
