---
diataxis_type: explanation
---

# MIF Schema Improvements (v0.1.0)

*Technical overview of the Memory Interchange Format architecture updates*

---

## Executive Summary

The Memory Interchange Format (MIF) schema architecture has been updated with inheritance patterns, standardized URIs, and separation of concerns. These changes make MIF more practical for real-world AI memory systems while maintaining backwards compatibility.

---

## 1. Trait Inheritance Model

### The `extends` Field

Ontologies can now explicitly declare which parent ontologies they inherit from using a new `extends` field.

**Before:**
```yaml
ontology:
  id: regenerative-agriculture
  version: "0.1.0"
  # Traits were implicitly assumed, no formal inheritance chain
```

**After:**
```yaml
ontology:
  id: regenerative-agriculture
  version: "0.1.0"
  extends:
    - mif-base        # Core traits
    - shared-traits   # Cross-domain traits
```

### Three-Tier Inheritance Model

This establishes a clear inheritance hierarchy:

1. **mif-base** - foundational traits (timestamped, confidence, provenance)
2. **shared-traits** - cross-domain mixins (lifecycle, auditable, located, measured)
3. **domain ontologies** - industry-specific entity types

### Why It Matters

- **Explicit Dependencies**: Tooling can now validate that required traits are available
- **Composability**: Domain ontologies can mix traits from multiple sources
- **Discoverability**: Developers can trace where a trait originated
- **Versioning**: Each layer can evolve independently with semantic versioning

### Use Case Example

A `soil-profile` entity in the agriculture ontology inherits:
- `provenance` from mif-base (who recorded this measurement?)
- `measured` from shared-traits (what metrics were captured?)
- `located` from shared-traits (GPS coordinates, field boundaries)

---

## 2. EntityData Field for Structured Ontology Data

### What Changed

MIF memories can now include structured `entity` data that conforms to ontology-defined schemas.

**Before:**
Ontology typing was implicit in the namespace and content. There was no formal structure for entity-specific fields.

**After:**
```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
ontology:
  id: regenerative-agriculture
entity:
  name: "North Pasture Soil Profile"
  entity_type: soil-profile
  entity_id: soil-north-pasture-2026
  # Additional fields defined by ontology schema:
  organic_matter_percent: 4.2
  ph_level: 6.8
  test_date: 2026-01-15
---
```

### Purpose

Separates the **memory metadata** (id, type, created) from the **domain-specific entity data** (organic matter, pH level). This enables:

- **Schema Validation**: Entity fields can be validated against ontology-defined schemas
- **Type Safety**: Required fields are enforced per entity type
- **Query Optimization**: Structured data enables efficient filtering and aggregation
- **Interoperability**: Different systems can extract and process entity data consistently

### Why It Matters

AI memory systems often need to store domain-specific structured data (customer records, lab results, project metadata). The `entity` field provides a standardized place for this data while keeping it separate from MIF's core temporal/provenance metadata.

---

## 3. Block References Field

### What Changed

Added a `blocks` object for named block references with their text content.

```json
"blocks": {
  "key-finding": "Soil organic matter increased 2.1% over 3 years",
  "methodology": "Samples taken at 6-inch depth, 5 points per paddock"
}
```

### Purpose

Enables **granular linking** within memories using Obsidian-style block references (`^block-id`). When a memory references `[[Soil Analysis#^key-finding]]`, the `blocks` object provides the actual text content for that reference.

### Why It Matters

- **Transclusion Support**: AI systems can embed specific sections from other memories
- **Precise Citations**: Link to exactly the relevant paragraph, not the whole document
- **Content Extraction**: Tooling can index and search block-level content
- **Obsidian Compatibility**: Mirrors Obsidian's block reference feature for human editing

---

## 4. Shared EntityReference Schema

### What Changed

Extracted `EntityReference` to a standalone schema file (`schema/definitions/entity-reference.schema.json`) referenced by both MIF and Citation schemas.

**Before:**
EntityReference was defined separately in `mif.schema.json` and `citation.schema.json`, risking divergence.

**After:**
```json
// mif.schema.json
"EntityReference": {
  "$ref": "./definitions/entity-reference.schema.json"
}

// citation.schema.json
"author": {
  "$ref": "../definitions/entity-reference.schema.json"
}
```

### Purpose

**Single source of truth** for entity references. When you reference a person as a memory author or a citation author, the structure is identical and validated consistently.

### Why It Matters

- **DRY Principle**: One definition, multiple consumers
- **Consistent Validation**: Same rules everywhere
- **Easier Maintenance**: Change once, applies everywhere
- **Schema Composition**: Follows JSON Schema best practices for modular schemas

---

## 5. Discovery Pattern Restructuring

### What Changed

Split the single `patterns` array into two specialized arrays:

**Before:**
```yaml
discovery:
  patterns:
    - content_pattern: "\\b(database|postgres)\\b"
      suggest_entity: resource
    - file_pattern: "**/openapi.yaml"
      suggest_entity: api
```

**After:**
```yaml
discovery:
  content_patterns:
    - pattern: "\\b(database|postgres)\\b"
      namespace: _semantic/resources
  file_patterns:
    - pattern: "**/openapi.yaml"
      namespaces: [_semantic/apis]
      context: "API specification file"
```

### Purpose

Content patterns and file patterns serve fundamentally different purposes:

- **Content Patterns**: Match against user prompts, conversation text, memory content
- **File Patterns**: Match against file paths being edited (glob syntax)

Separating them allows:

- **Specialized Fields**: File patterns can have `context` hints; content patterns don't need glob syntax
- **Independent Processing**: Systems can run file pattern matching only when relevant
- **Clearer Semantics**: No ambiguity about which pattern type you're defining

---

## 6. Standardized Schema Identifiers

### What Changed

All schema `$id` and `schema_url` references now use a consistent URI pattern: `https://mif-spec.dev/schema/`.

**Before:**
```
https://mif-spec.dev/schema/ontology.schema.json
```

**After:**
```
https://mif-spec.dev/schema/ontology/ontology.schema.json
```

### Purpose

- **Resolvable URLs**: Schema `$id` values point to actual raw GitHub content that can be fetched
- **Version Control**: Schemas are versioned alongside the specification in the same repository
- **Consistency**: All MIF schemas share a common URL pattern
- **Accessibility**: Anyone can retrieve the actual schema definitions directly

---

## 7. VERSION.json Constants File

### What Changed

Created a centralized version constants file:

```json
{
  "specification": "0.1.0",
  "schemas": {
    "mif": "0.1.0",
    "citation": "0.1.0",
    "ontology": "0.1.0",
    "entity-reference": "0.1.0"
  },
  "ontologies": {
    "mif-base": "0.1.0",
    "shared-traits": "0.1.0"
  }
}
```

### Purpose

Single source of truth for all version numbers. Tooling, documentation, and release automation can read from one file.

### Why It Matters

- **Consistency**: No more version mismatches between files
- **Automation-Friendly**: CI/CD can read and bump versions programmatically
- **Clear Versioning Model**: Specification version vs schema versions vs ontology versions

---

## 8. Decay Model Rationale

### Scientific Background

MIF's decay model values (P7D, P14D, P30D half-lives) are **pragmatic defaults** for AI memory systems, inspired by cognitive psychology research.

The exponential decay formula `strength = e^(-t/halfLife)` models natural memory decay, drawing from Hermann Ebbinghaus's forgetting curve (1885):

| Time Elapsed | Approximate Retention |
|--------------|----------------------|
| 1 hour       | ~50% |
| 24 hours     | ~30-35% |
| 7 days       | ~25% |
| 30 days      | ~10% |

### Recommended Values

| Half-Life | Use Case | Rationale |
|-----------|----------|-----------|
| **P7D** | Short-term context | Aligns with weekly work cycles and episodic memory consolidation |
| **P14D** | Medium-term projects | Spans typical sprint/iteration boundaries |
| **P30D** | Long-term knowledge | Corresponds to monthly review cycles and hippocampal consolidation periods |
| **P90D** | Default TTL | Quarterly relevance for most organizational knowledge |

### Memory Reinforcement

The `lastAccessed` and `accessCount` fields enable implementations to model reinforcement. Each access can reset or slow decay, analogous to spaced repetition strengthening memory traces.

### References

- Ebbinghaus, H. (1885). *Memory: A Contribution to Experimental Psychology*
- Murre & Dros (2015). [Replication and Analysis of Ebbinghaus' Forgetting Curve](https://pmc.ncbi.nlm.nih.gov/articles/PMC4492928/)
- Squire & Bayley (2007). [The neuroscience of remote memory](https://pmc.ncbi.nlm.nih.gov/articles/PMC2791502/)
- Wickelgren (1972). [Trace resistance and the decay of long-term memory](https://psycnet.apa.org/record/1973-08477-007)

---

## Summary: What This Enables

These changes collectively enable:

1. **Modular Ontology Design**: Build domain ontologies by composing traits from a shared library
2. **Validated Entity Data**: Store structured domain data with schema enforcement
3. **Granular Linking**: Reference specific blocks within memories
4. **Consistent References**: Same entity reference structure everywhere
5. **Clear Discovery**: Separate content and file pattern matching
6. **Professional Standards**: Vendor-neutral URIs and centralized versioning
7. **Informed Defaults**: Research-backed temporal decay values

The MIF specification is moving toward a stable release for AI memory interoperability.

---

## Related Resources

- [MIF Specification](../SPECIFICATION.md)
- [Schema Reference](./SCHEMA-REFERENCE.md)
- [Getting Started Guide](./GETTING-STARTED.md)
- [Migration Guide](./MIGRATION-GUIDE.md)
