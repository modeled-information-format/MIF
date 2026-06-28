---
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
with open('ontology.schema.json') as s, open('../../ontologies/mif-base.ontology.yaml') as d:
    validate(yaml.safe_load(d), json.load(s))
print('Valid')
"

# ajv validation (requires JSON conversion; npm install -g ajv-cli ajv-formats)
yq -o=json '.' ../../ontologies/mif-base.ontology.yaml | \
  npx ajv validate -s ontology.schema.json -d /dev/stdin --spec=draft2020 -c ajv-formats
```

### Converting to JSON-LD

```bash
python ../../scripts/yaml2jsonld.py ../../ontologies/mif-base.ontology.yaml
```

## Schema Evolution

- **v1.0** (current): Three-type hierarchy with nested namespaces

When updating the schema:
1. Increment version in `$id`
2. Update CHANGELOG.md
3. Regenerate JSON-LD files from YAML sources
