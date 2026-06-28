---
diataxis_type: reference
---

# MIF Ontologies

This directory contains ontology definitions for the Modeled Information Format.

## Base Ontology

### mif-base.ontology.yaml

The base ontology defines the namespace hierarchy for the three base memory types.

**Important:** Namespace paths use an underscore prefix (`_semantic`, `_episodic`, `_procedural`) to distinguish base type namespaces from domain-specific namespaces. This convention ensures consistent namespace identification across implementations.

```text
_semantic/             # Facts, concepts, relationships
├── decisions/         # Architectural choices, rationale
├── knowledge/         # APIs, context, learnings, security
└── entities/          # Entity definitions

_episodic/             # Events, experiences, timelines
├── incidents/         # Production issues, postmortems
├── sessions/          # Debug sessions, work sessions
└── blockers/          # Impediments, issues

_procedural/           # Step-by-step processes
├── runbooks/          # Operational procedures
├── patterns/          # Code conventions, testing
└── migrations/        # Migration steps, upgrades
```

## Trait Inheritance

Ontologies can inherit traits from other ontologies using the `extends` field:

```yaml
ontology:
  id: my-domain
  version: "1.0.0"
  extends:
    - mif-base        # Core traits (timestamped, confidence, provenance)
    - shared-traits   # Cross-domain traits (lifecycle, auditable, located, etc.)
```

### Core Traits (mif-base)

The base ontology defines foundational traits:

| Trait | Description | Fields |
|-------|-------------|--------|
| `timestamped` | Creation/update timestamps | `created_at`, `updated_at` |
| `confidence` | Memory decay score | `confidence` (0.0-1.0) |
| `provenance` | Source tracking | `source`, `author` |

### Shared Traits (shared-traits)

Cross-domain reusable traits for industry ontologies:

| Category | Traits |
|----------|--------|
| Lifecycle | `lifecycle`, `renewable` |
| Compliance | `auditable`, `certified`, `regulated` |
| Geographic | `located`, `bounded` |
| Stakeholder | `owned`, `contactable` |
| Financial | `budgeted`, `transactional` |
| Temporal | `scheduled`, `seasonal` |
| Measurement | `measured`, `scored` |
| Classification | `categorized`, `tagged` |
| Asset | `inventoried`, `maintainable` |
| Quality | `reviewed`, `quality_controlled` |

Domain ontologies compose these traits into entity types:

```yaml
entity_types:
  - name: soil-profile
    base: semantic
    traits:
      - measured      # From shared-traits
      - located       # From shared-traits
      - provenance    # From mif-base
    schema:
      properties:
        organic_matter_percent: { type: number }
```

### Inheritance Semantics

When an ontology declares `extends`, the following inheritance rules apply:

1. **Traits**: All traits from parent ontologies become available to entity types in the child ontology. Traits are inherited by reference and merged additively.

2. **Relationships**: Relationship type definitions are inherited. Child ontologies can extend the `from`/`to` constraints to include additional entity types.

3. **Namespaces**: Parent namespace hierarchies are inherited. Child ontologies can:
   - Add sibling namespaces at any level
   - Add child namespaces to inherited parents
   - Override `description` or `type_hint` for inherited namespaces
   - Cannot remove or rename inherited namespaces

4. **Discovery Patterns**: Parent discovery patterns are inherited and merged with child patterns. When patterns conflict (same pattern string), the child pattern takes precedence.

5. **Entity Types**: Entity types are NOT inherited automatically. Child ontologies must explicitly define their own entity types, but can reference inherited traits.

#### Inheritance Order

When multiple ontologies are listed in `extends`, they are processed in order:

```yaml
extends:
  - mif-base        # Processed first
  - shared-traits   # Processed second (overrides mif-base on conflict)
```

Later entries override earlier entries for conflicting definitions.

## Using Ontologies

### Path Format

Memories are stored using hierarchical namespace paths:

```
# User-level (includes org and project)
${MNEMONIC_ROOT}/{org}/{project}/{namespace}/

# Project-level (namespace only)
./.claude/mnemonic/{namespace}/
```

Examples:
- `${MNEMONIC_ROOT}/zircote/mif/_semantic/decisions/`
- `./.claude/mnemonic/_procedural/patterns/`

> **Path contexts:** `${MNEMONIC_ROOT}/{org}/{project}/` is the user-level storage path
> (external to the repository). Project-level `.claude/mnemonic/` is for embedded project memories.

### Namespace Selection

Choose namespaces based on memory type:

| Memory Type | Namespace | Description |
|-------------|-----------|-------------|
| Architectural choices | `_semantic/decisions` | Why we chose X over Y |
| API/technical facts | `_semantic/knowledge` | How X works |
| Component definitions | `_semantic/entities` | What X is |
| Production issues | `_episodic/incidents` | When X broke |
| Debug sessions | `_episodic/sessions` | Work session notes |
| Blockers/impediments | `_episodic/blockers` | What's blocking progress |
| Operational procedures | `_procedural/runbooks` | How to deploy X |
| Code conventions | `_procedural/patterns` | How we write X |
| Upgrade steps | `_procedural/migrations` | How to migrate to X |

## Declaring Ontology in Memories

MIF memories can explicitly declare which ontology they conform to using the `ontology` field:

### YAML Frontmatter (Markdown)

```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
created: 2026-01-26T10:00:00Z
ontology:
  id: regenerative-agriculture
  version: "0.1.0"
  uri: https://raw.githubusercontent.com/modeled-information-format/MIF/main/ontologies/examples/regenerative-agriculture.ontology.yaml
namespace: _semantic/livestock
---
```

### JSON-LD

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:550e8400",
  "ontology": {
    "@type": "OntologyReference",
    "id": "regenerative-agriculture",
    "version": "0.1.0",
    "uri": "https://raw.githubusercontent.com/modeled-information-format/MIF/main/ontologies/examples/regenerative-agriculture.ontology.yaml"
  },
  "namespace": "_semantic/livestock",
  "content": "..."
}
```

### OntologyReference Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Ontology identifier (must match `ontology.id` in definition) |
| `version` | No | Semantic version (e.g., "1.0.0") |
| `uri` | No | URL to the ontology definition file |

## Examples

The `examples/` directory contains domain-specific ontologies:

- `software-engineering.ontology.yaml` - Software development entities
- `regenerative-agriculture.ontology.yaml` - Farm operations and carbon markets
- `k12-educational-publishing.ontology.yaml` - Educational content publishing
- `biology-research-lab.ontology.yaml` - Academic research lab operations
- `backstage.ontology.yaml` - Backstage.io developer portal entities
- `csi-5w1h.ontology.yaml` - CSI 5W1H investigative framework

The top-level `ontologies/` directory also contains:

- `shared-traits.ontology.yaml` - Reusable trait mixins

## Creating Custom Ontologies

1. Create an `ontology.yaml` file in your project:
   ```
   ./.claude/mnemonic/ontology.yaml
   ```

2. Define custom namespaces, entity types, and discovery patterns:
   ```yaml
   ontology:
     id: my-project
     version: "1.0.0"

   namespaces:
     features:
       description: "Product features"
       type_hint: semantic

   entity_types:
     - name: feature
       base: semantic
       schema:
         required: [name, status]
         properties:
           name: { type: string }
           status: { type: string, enum: [planned, active, deprecated] }
   ```

## JSON-LD Generation

Convert YAML ontologies to JSON-LD for semantic web compatibility:

```bash
python scripts/yaml2jsonld.py ontologies/mif-base.ontology.yaml
python scripts/yaml2jsonld.py --all  # Convert all
```

> **Prerequisites:** `pip install pyyaml` (PyYAML is required for YAML processing)
