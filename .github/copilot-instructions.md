# MIF Project - Copilot Instructions

## About This Project

MIF (Modeled Information Format) is an open standard for portable AI
memory representation with dual formats: Markdown and JSON-LD.

## Ontology Management

This project includes an ontology system for organizing memories.
When working with ontology files (`.ontology.yaml`):

- Use the ontology manager agent: `.github/agents/ontology-manager.agent.md`
- Scripts: `.claude/skills/ontology-manager/scripts/`
- Schema: `schema/ontology/ontology.schema.json`

### Quick Commands

```bash
# Validate an ontology
bash .claude/skills/ontology-manager/scripts/validate_ontology.sh <file.yaml>

# Scaffold a new ontology
bash .claude/skills/ontology-manager/scripts/scaffold_ontology.sh <id> <ver> > out.yaml

# Inspect ontology contents
bash .claude/skills/ontology-manager/scripts/inspect_ontology.sh <file.yaml>

# Convert formats
bash .claude/skills/ontology-manager/scripts/convert_format.sh yaml2json <in.yaml>
```

### Key Conventions

- Ontology IDs: lowercase with hyphens (`my-domain`)
- Entity names: lowercase with hyphens (`support-ticket`)
- Base types: `semantic`, `episodic`, `procedural`
- Namespaces follow the cognitive triad: `_semantic/`, `_episodic/`, `_procedural/`
- Version strings: semver (`0.1.0`)
- All ontologies should typically extend `mif-base`

## Project Structure

```
schema/                     # JSON Schema definitions
  ontology/                 # Ontology validation schema
ontologies/                 # Ontology definition files
  mif-base.ontology.yaml   # Base cognitive triad
  shared-traits.ontology.yaml
  examples/                 # Domain-specific examples
scripts/                    # Utility scripts
  yaml2jsonld.py            # YAML to JSON-LD converter
examples/                   # MIF memory examples
```
