---
id: docs-api-reference
type: semantic
created: '2026-07-01T00:00:00Z'
diataxis_type: reference
---

# MIF API Reference

This document describes the programmatic interfaces available in MIF.

## Scripts

### yaml2jsonld.py

Converts MIF ontology YAML files to JSON-LD format for semantic web compatibility.

**Location:** `scripts/yaml2jsonld.py`

#### Usage

```bash
# Convert a single file
python scripts/yaml2jsonld.py <input.yaml> [output.jsonld]

# Convert all ontologies in ontologies/ directory
python scripts/yaml2jsonld.py --all
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input` | Yes* | Input YAML file path |
| `output` | No | Output JSON-LD file path (default: same name with `.jsonld` extension) |
| `--all` | No | Convert all `*.ontology.yaml` files in the given directory |

*Required unless `--all` is specified.

#### Examples

```bash
# Basic conversion
python scripts/yaml2jsonld.py <path-to-ontology>.yaml
# Output: <path-to-ontology>.jsonld

# Custom output path
python scripts/yaml2jsonld.py <path-to-ontology>.yaml output/<name>.jsonld

# Batch conversion
python scripts/yaml2jsonld.py --all <path-to-directory>
# Converts all *.ontology.yaml files in that directory
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (missing input, invalid YAML, etc.) |

#### Dependencies

- Python 3.8+
- PyYAML (`pip install pyyaml`)

---

## Python API

The `yaml2jsonld.py` script provides functions that can be imported and used programmatically.

### Functions

#### `convert_file(input_path, output_path=None) -> Path`

Convert a single YAML ontology file to JSON-LD.

**Parameters:**
- `input_path` (Path): Path to input YAML file
- `output_path` (Path, optional): Path for output file. Defaults to input path with `.jsonld` extension.

**Returns:** Path to created JSON-LD file

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `ValueError`: If YAML file is empty or invalid

**Example:**

```python
from pathlib import Path
from scripts.yaml2jsonld import convert_file

# Basic usage
output = convert_file(Path("ontologies/my-ontology.yaml"))
print(f"Created: {output}")

# Custom output path
output = convert_file(
    Path("ontologies/my-ontology.yaml"),
    Path("output/my-ontology.jsonld")
)
```

#### `convert_all_ontologies() -> list`

Convert all ontology YAML files in the `ontologies/` directory.

**Returns:** List of paths to created JSON-LD files

**Example:**

```python
from scripts.yaml2jsonld import convert_all_ontologies

converted = convert_all_ontologies()
print(f"Converted {len(converted)} files")
for path in converted:
    print(f"  - {path}")
```

#### `yaml_to_jsonld(yaml_data) -> dict`

Convert parsed YAML data to JSON-LD format.

**Parameters:**
- `yaml_data` (dict): Parsed YAML ontology data

**Returns:** JSON-LD document as dictionary

**Example:**

```python
import yaml
from scripts.yaml2jsonld import yaml_to_jsonld

# Load YAML manually
with open("ontologies/my-ontology.yaml") as f:
    yaml_data = yaml.safe_load(f)

# Convert to JSON-LD
jsonld = yaml_to_jsonld(yaml_data)

# Use the result
print(jsonld["@id"])
print(jsonld["namespaces"])
```

#### `load_context() -> dict`

Load the JSON-LD context file.

**Returns:** Context dictionary from `schema/ontology/ontology.context.jsonld`

**Raises:**
- `FileNotFoundError`: If context file doesn't exist

#### Transform Functions

Lower-level functions for transforming specific ontology elements:

```python
from scripts.yaml2jsonld import (
    transform_namespace,
    transform_entity_type,
    transform_trait,
    transform_relationship,
    transform_discovery_pattern
)

# Transform a namespace
ns_jsonld = transform_namespace("semantic", {
    "description": "Facts and concepts",
    "type_hint": "semantic",
    "children": {
        "decisions": {"description": "Decisions"}
    }
})

# Transform an entity type
et_jsonld = transform_entity_type({
    "name": "component",
    "base": "semantic",
    "description": "Software component",
    "traits": ["versioned"]
})

# Transform a trait
trait_jsonld = transform_trait("versioned", {
    "description": "Supports versioning",
    "fields": {
        "version": {"type": "string"}
    }
})

# Transform a relationship
rel_jsonld = transform_relationship("implements", {
    "description": "Realizes a concept",
    "from": ["component"],
    "to": ["concept"],
    "symmetric": False
})

# Transform a discovery pattern
pattern_jsonld = transform_discovery_pattern({
    "content_pattern": r"\b(PostgreSQL|MySQL)\b",
    "suggest_entity": "technology"
}, index=0)
```

---

## JSON-LD Context

The MIF JSON-LD context provides vocabulary mappings for semantic web compatibility.

**Location:** `schema/ontology/ontology.context.jsonld`

### Core Types

| Type | URI | Description |
|------|-----|-------------|
| `Memory` | `mif:Memory` | Memory document |
| `Entity` | `mif:Entity` | Named entity |
| `Relationship` | `mif:Relationship` | Entity relationship |
| `EntityReference` | `mif:EntityReference` | Reference to entity |
| `OntologyReference` | `mif:OntologyReference` | Reference to ontology |
| `Citation` | `mif:Citation` | Citation reference |
| `TemporalMetadata` | `mif:TemporalMetadata` | Temporal data |
| `EmbeddingReference` | `mif:EmbeddingReference` | Embedding reference |

### Entity Types

| Type | URI |
|------|-----|
| `Person` | `mif:Person` |
| `Organization` | `mif:Organization` |
| `Technology` | `mif:Technology` |
| `Concept` | `mif:Concept` |
| `File` | `mif:File` |

### Properties

| Property | URI | Type |
|----------|-----|------|
| `content` | `mif:content` | string |
| `memoryType` | `mif:memoryType` | string |
| `namespace` | `mif:namespace` | string |
| `created` | `dc:created` | dateTime |
| `modified` | `dc:modified` | dateTime |
| `ontology` | `mif:ontology` | OntologyReference |

### Using the Context

Reference the context in your JSON-LD documents:

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:my-memory",
  ...
}
```

Or extend with custom vocabulary:

```json
{
  "@context": [
    "https://mif-spec.dev/schema/context.jsonld",
    {
      "myns": "https://example.com/ns/",
      "customField": "myns:customField"
    }
  ],
  "@type": "Memory",
  "customField": "value"
}
```

---

## Validation API

### JSON Schema Validation

Use the JSON schemas programmatically:

```python
import json
import jsonschema
from pathlib import Path

def validate_mif_document(document: dict) -> bool:
    """Validate a MIF document against the schema."""

    schema_path = Path("schema/mif.schema.json")
    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(document, schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False


def validate_citation(citation: dict) -> bool:
    """Validate a citation object."""

    schema_path = Path("schema/citation.schema.json")
    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(citation, schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False


def validate_ontology(ontology: dict) -> bool:
    """Validate an ontology definition."""

    schema_path = Path("schema/ontology/ontology.schema.json")
    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(ontology, schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False
```

### Using ajv (JavaScript/Node.js)

```javascript
const Ajv2020 = require('ajv/dist/2020');
const addFormats = require('ajv-formats');
const fs = require('fs');
const path = require('path');

const ajv = new Ajv2020({ allErrors: true });
addFormats(ajv);

// Register the referenced definition schemas so $refs resolve
const defsDir = 'schema/definitions';
for (const file of fs.readdirSync(defsDir)) {
  if (file.endsWith('.schema.json')) {
    ajv.addSchema(JSON.parse(fs.readFileSync(path.join(defsDir, file))));
  }
}

const validateMif = ajv.compile(JSON.parse(fs.readFileSync('schema/mif.schema.json')));
const validateCitation = ajv.compile(JSON.parse(fs.readFileSync('schema/citation.schema.json')));

// Validate a derived JSON-LD projection (produced by scripts/mif_convert.py emit-jsonld).
// Node reads .jsonld directly (unlike ajv-cli, which needs a .json file).
const document = JSON.parse(fs.readFileSync('memory.jsonld'));
if (!validateMif(document)) {
  console.log('MIF validation errors:', validateMif.errors);
}

// Validate a citation object
const citation = JSON.parse(fs.readFileSync('citation.json'));
if (!validateCitation(citation)) {
  console.log('Citation validation errors:', validateCitation.errors);
}
```

---

## Integration Examples

### Python: Creating MIF Memories

```python
import json
import uuid
from datetime import datetime, timezone

def create_mif_memory(
    content: str,
    memory_type: str = "semantic",
    namespace: str = "_semantic/knowledge",
    tags: list = None,
    ontology: dict = None
) -> dict:
    """Create a valid MIF memory document.

    Args:
        content: The memory content text
        memory_type: Base memory type - "semantic", "episodic", or "procedural"
        namespace: Hierarchical scope (e.g., "_semantic/decisions", "_episodic/sessions")
        tags: Classification tags
        ontology: Optional ontology reference dict with "id" and optional "version"

    Returns:
        A valid MIF document as a dictionary
    """

    # Validate memory_type is base memory types
    valid_types = {"semantic", "episodic", "procedural"}
    if memory_type not in valid_types:
        raise ValueError(f"memory_type must be one of {valid_types}, got '{memory_type}'")

    memory_id = str(uuid.uuid4())

    mif = {
        "@context": "https://mif-spec.dev/schema/context.jsonld",
        "@type": "Memory",
        "@id": f"urn:mif:{memory_id}",
        "memoryType": memory_type,
        "content": content,
        "created": datetime.now(timezone.utc).isoformat() + "Z",
        "namespace": namespace
    }

    if tags:
        mif["tags"] = tags

    if ontology:
        mif["ontology"] = {
            "@type": "OntologyReference",
            **ontology
        }

    return mif


# Usage
memory = create_mif_memory(
    content="User prefers dark mode for all applications.",
    memory_type="semantic",  # Base memory type
    namespace="_semantic/preferences",  # Specific categorization via namespace
    tags=["ui", "accessibility"],
    ontology={"id": "mif-base", "version": "0.1.0"}
)

print(json.dumps(memory, indent=2))
```

### JavaScript: Creating MIF Memories

```javascript
function createMifMemory(content, options = {}) {
  const {
    memoryType = 'semantic',  // Base types: semantic, episodic, procedural
    namespace = '_semantic/knowledge',
    tags,
    ontology
  } = options;

  // Validate memory type
  const validTypes = ['semantic', 'episodic', 'procedural'];
  if (!validTypes.includes(memoryType)) {
    throw new Error(`memoryType must be one of ${validTypes.join(', ')}, got '${memoryType}'`);
  }

  const memoryId = crypto.randomUUID();

  const mif = {
    '@context': 'https://mif-spec.dev/schema/context.jsonld',
    '@type': 'Memory',
    '@id': `urn:mif:${memoryId}`,
    memoryType,
    content,
    created: new Date().toISOString(),
    namespace
  };

  if (tags) mif.tags = tags;
  if (ontology) {
    mif.ontology = {
      '@type': 'OntologyReference',
      ...ontology
    };
  }

  return mif;
}

// Usage
const memory = createMifMemory(
  'User prefers dark mode for all applications.',
  {
    memoryType: 'semantic',  // Base memory type
    namespace: '_semantic/preferences',  // Specific categorization via namespace
    tags: ['ui', 'accessibility'],
    ontology: { id: 'mif-base', version: '0.1.0' }
  }
);

console.log(JSON.stringify(memory, null, 2));
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError: Context file not found` | Missing `ontology.context.jsonld` | Ensure schema files are present |
| `ValueError: Empty or invalid YAML file` | Malformed YAML | Check YAML syntax |
| `ValidationError: '@id' must match pattern` | Invalid URN | Use `urn:mif:` prefix |

### Debugging

Enable verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now conversion will show detailed logs
from scripts.yaml2jsonld import convert_file
convert_file(Path("ontology.yaml"))
```

---

## Version Compatibility

| MIF Version | Python | Node.js | JSON Schema Draft |
|-------------|--------|---------|-------------------|
| 1.0.x | 3.10+ | 22+ | 2020-12 |

---

## See Also

- [Getting Started](./GETTING-STARTED.md)
- [Schema Reference](./SCHEMA-REFERENCE.md)
- [Migration Guide](./MIGRATION-GUIDE.md)
- [Specification](../SPECIFICATION.md)
