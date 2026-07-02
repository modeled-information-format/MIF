# MIF Ontology Schema Reference

Source: `schema/ontology/ontology.schema.json`

## Top-Level Structure

```yaml
ontology:        # REQUIRED - metadata block
  id:            # REQUIRED - ^[a-z][a-z0-9-]*$
  version:       # REQUIRED - semver (X.Y.Z)
  description:   # optional
  schema_url:    # optional, format: uri
  extends:       # optional, array of ontology IDs

namespaces:      # Hierarchical cognitive triad
entity_types:    # Array of entity definitions
traits:          # Reusable mixin definitions
relationships:   # Relationship type definitions
discovery:       # Pattern matching configuration
```

## Namespace Definition

```yaml
namespaces:
  _semantic:                    # key = namespace name
    description: "..."
    type_hint: semantic         # semantic|episodic|procedural
    replaces: "old_namespace"   # migration hint
    children:
      decisions:                # child namespace
        description: "..."
        type_hint: semantic
```

Top-level namespaces follow the cognitive triad:
- `_semantic` - Facts, concepts, relationships
- `_episodic` - Events, experiences, timelines
- `_procedural` - Step-by-step processes

## Entity Type Definition

```yaml
entity_types:
  - name: my-entity          # REQUIRED, ^[a-z][a-z0-9-]*$
    base: semantic            # REQUIRED, semantic|episodic|procedural
    description: "..."
    traits:                   # array of trait names
      - timestamped
      - confidence
    schema:
      required:               # array of required field names
        - field_name
      properties:
        field_name:
          type: string        # string|number|integer|boolean|array|object|null
          description: "..."
          format: date-time   # optional format hint
          pattern: "^..."     # optional regex
          items: {}           # for array type
          enum: [a, b, c]     # allowed values
```

## Trait Definition

```yaml
traits:
  my-trait:
    description: "..."
    extends:                  # inherit fields from other traits
      - parent-trait
    fields:
      field_name:
        type: string
        description: "..."
    requires:                 # MIF fields this trait depends on
      - some_mif_field
```

## Relationship Definition

```yaml
relationships:
  my-relationship:
    description: "..."
    from:                     # source entity types (empty = any)
      - entity-a
    to:                       # target entity types (empty = any)
      - entity-b
    symmetric: false          # default: false
```

## Discovery Configuration

Three pattern array styles (can mix content_patterns + file_patterns, or use unified patterns):

### Content Patterns
```yaml
discovery:
  enabled: true
  confidence_threshold: 0.8   # 0.0-1.0
  content_patterns:
    - pattern: "\\bregex\\b"  # matched against content
      namespace: _semantic/decisions
      suggest_entity: my-entity
      context: "human hint"
```

### File Patterns
```yaml
  file_patterns:
    - pattern: "auth|login"   # matched against file paths
      namespaces:
        - _semantic/knowledge
        - _semantic/decisions
      context: "authentication"
      suggest_entity: my-entity
```

### Unified Patterns
```yaml
  patterns:
    - content_pattern: "\\bregex\\b"
      suggest_namespace: _semantic/decisions
      suggest_entity: my-entity
    - file_pattern: "*.test.*"
      suggest_namespace: _procedural/patterns
```

## Validation Rules Summary

| Field | Rule |
|-------|------|
| `ontology.id` | Required. `^[a-z][a-z0-9-]*$` |
| `ontology.version` | Required. Semver `^\d+\.\d+\.\d+` |
| `entity_types[].name` | Required. `^[a-z][a-z0-9-]*$` |
| `entity_types[].base` | Required. `semantic\|episodic\|procedural` |
| `namespace.type_hint` | `semantic\|episodic\|procedural` |
| `relationship.symmetric` | Boolean, default false |
| `discovery.confidence_threshold` | 0.0-1.0, default 0.8 |
| `property.type` | `string\|number\|integer\|boolean\|array\|object\|null` |

## Existing Ontologies for Reference

Every ontology (base and domain) now lives in the `modeled-information-format/ontologies`
repo, not in this repo — fetch/browse there for reference examples:

| ID | Entities | Purpose |
|----|----------|---------|
| mif-base | 0 | Base cognitive triad |
| shared-traits | 0 | Reusable traits library |
| software-engineering | 9 | Dev domain example |
| biology-research-lab | 19 | Science domain |
| k12-educational-publishing | 16 | Education domain |
| regenerative-agriculture | 19 | Agriculture domain |
