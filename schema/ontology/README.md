---
id: schema-ontology-readme
type: semantic
created: '2026-07-01T00:00:00Z'
diataxis_type: reference
---

# MIF Ontology Schema

This directory contains the schema definitions for MIF ontology files.

## Files

### ontology.schema.json

JSON Schema (draft 2020-12) for validating ontology YAML files. Key features:

- **Hierarchical namespaces**: Supports base type hierarchy (semantic/episodic/procedural) with nested children
- **Entity types**: Custom entity definitions with traits and JSON Schema validation
- **Discovery patterns**: Content and file pattern matching for entity suggestions
- **Relationships**: Typed relationships between entities

#### Entity-type classification fields (v1.1)

Each `entity_type` may optionally carry three string-array fields that make
embedding-based classification (for example a `suggest_type` tool ranking
candidate types for a document) trustworthy. All three are additive and
backward compatible; an ontology carrying only `description` remains valid.

| Field | Meaning | JSON-LD mapping |
| --- | --- | --- |
| `aliases` | Synonyms and label variations, distinct from `description` | `skos:altLabel` |
| `exemplars` | 2-5 curated canonical example phrases or instances | `skos:example` |
| `negative_examples` | Curated near-misses from the ontology's most confusable type pairs — texts that resemble the type but do NOT denote it | `https://mif-spec.dev/ns/ontology#negativeExample` (SKOS defines no negative-example property) |

**Embedding-document composition rule**: a classifier's positive embedding
document for an entity type concatenates `description` + `aliases` +
`exemplars`. `negative_examples` is never concatenated into the positive
document — it exists for decision-boundary sharpening between confusable
types, and must be human-curated, not auto-mined. Write `description` as
multiple descriptive statements rather than one terse line; description
quality is a first-order classification lever independent of the added
fields.

### ontology.context.jsonld

JSON-LD context for semantic web compatibility. Maps ontology concepts to:

- **Schema.org** for common properties (name, description, version)
- **SKOS** for concept hierarchies
- **OWL** for relationship semantics
- **Custom MIF vocabulary** for memory-specific concepts

## Usage

### Validating an ontology file

```bash
# Python validation (handles YAML natively - recommended)
python3 -c "
import json, sys
from jsonschema import validate
import yaml
with open('ontology.schema.json') as s, open('<path-to-ontology>.yaml') as d:
    validate(yaml.safe_load(d), json.load(s))
print('Valid')
"

# ajv validation (requires JSON conversion; npm install -g ajv-cli ajv-formats)
yq -o=json '.' <path-to-ontology>.yaml | \
  npx ajv validate -s ontology.schema.json -d /dev/stdin --spec=draft2020 -c ajv-formats
```

### Converting to JSON-LD

```bash
python ../../scripts/yaml2jsonld.py <path-to-ontology>.yaml
```

## Schema Evolution

- **v1.1** (current): Optional entity-type classification fields (`aliases`,
  `exemplars`, `negative_examples`) supporting confidence-tiered
  embedding-based classification (ADR-020)
- **v1.0**: Three-type hierarchy with nested namespaces

When updating the schema:
1. Bump `schemas.ontology` in `VERSION.json` (the `$id` stays unversioned
   and stable per ADR-007; versioned copies are release-prep mirrors per
   ADR-016)
2. Update CHANGELOG.md
3. Regenerate JSON-LD files from YAML sources
