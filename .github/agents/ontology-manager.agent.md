---
description: MIF Ontology Manager - Create, validate, inspect, and convert MIF ontology definition files using yq, jq, and shell scripts grounded in the MIF JSON Schema
infer: true
---

# MIF Ontology Manager

Manage MIF ontology definition files. All operations are validated
against `schema/ontology/ontology.schema.json`.

## Prerequisites

Ensure `yq` and `jq` are available. For JSON Schema validation,
`python3` with `jsonschema` is preferred.

## Available Scripts

Scripts are located at `.claude/skills/ontology-manager/scripts/`.

### Create a New Ontology

Every ontology, base and domain, is authored in the
`modeled-information-format/ontologies` repo, not here — run this from a
checkout of that repo, writing into its `ontologies/` directory:

```bash
bash <path-to-MIF-checkout>/.claude/skills/ontology-manager/scripts/scaffold_ontology.sh \
  <id> <version> [--extends mif-base,shared-traits] \
  > ontologies/<id>.ontology.yaml
```

- `id`: lowercase, hyphens only (e.g. `my-domain`)
- `version`: semver (e.g. `0.1.0`)
- `--extends`: comma-separated parent ontology IDs

### Validate an Ontology

```bash
bash .claude/skills/ontology-manager/scripts/validate_ontology.sh \
  <file.yaml> [schema/ontology/ontology.schema.json]
```

Checks: YAML syntax, required fields, ID format, semver, base types,
entity names, trait references, discovery regex, JSON Schema compliance.

### Inspect an Ontology

```bash
bash .claude/skills/ontology-manager/scripts/inspect_ontology.sh \
  <file.yaml> [--section entities|namespaces|traits|relationships|discovery] [--json]
```

### Convert Between Formats

```bash
bash .claude/skills/ontology-manager/scripts/convert_format.sh \
  <yaml2json|json2yaml|yaml2jsonld> <input> [output]
```

## Ontology Structure

Every `.ontology.yaml` file has this structure:

```yaml
ontology:
  id: my-domain         # REQUIRED: ^[a-z][a-z0-9-]*$
  version: "0.1.0"      # REQUIRED: semver
  description: "..."
  schema_url: https://mif-spec.dev/schema/ontology/ontology.schema.json
  extends: [mif-base]   # optional parent ontologies

namespaces:              # cognitive triad hierarchy
  _semantic:             # facts, concepts, relationships
  _episodic:             # events, experiences, timelines
  _procedural:           # step-by-step processes

entity_types:            # array of entity definitions
  - name: my-entity     # ^[a-z][a-z0-9-]*$
    base: semantic       # semantic|episodic|procedural
    traits: [timestamped]
    schema:
      required: [name]
      properties:
        name: {type: string}

traits:                  # reusable mixins
  my-trait:
    fields:
      my_field: {type: string}

relationships:           # typed connections
  my-rel:
    from: [entity-a]
    to: [entity-b]
    symmetric: false

discovery:               # auto-detection patterns
  enabled: true
  confidence_threshold: 0.8
  content_patterns:
    - pattern: "\\bkeyword\\b"
      namespace: _semantic/knowledge
  file_patterns:
    - pattern: "auth|login"
      namespaces: [_semantic/knowledge]
```

## Common yq Operations

```bash
# List entity names
yq -r '.entity_types[].name' ontology.yaml

# Add entity type
yq -i '.entity_types += [{"name":"x","base":"semantic"}]' ontology.yaml

# Add trait
yq -i '.traits.x = {"fields":{"f":{"type":"string"}}}' ontology.yaml

# Add relationship
yq -i '.relationships.x = {"from":[],"to":[],"symmetric":false}' ontology.yaml

# Bump version
yq -i '.ontology.version = "0.2.0"' ontology.yaml
```

## Reference Files

- Schema (this repo): `schema/ontology/ontology.schema.json`
- Base ontology, shared traits, domain ontologies, and examples: all in the
  `modeled-information-format/ontologies` repo's `ontologies/` directory
- Detailed reference: `.claude/skills/ontology-manager/references/schema-reference.md`
