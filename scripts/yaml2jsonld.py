#!/usr/bin/env python3
"""
YAML to JSON-LD Converter for MIF Ontologies

Converts ontology YAML files to JSON-LD format using the MIF context.
Generates semantic web compatible output for interoperability.

Usage:
    python yaml2jsonld.py <input.yaml> [output.jsonld]
    python yaml2jsonld.py --all  # Convert all ontologies in ontologies/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def get_context_path() -> Path:
    """Get path to the JSON-LD context file."""
    script_dir = Path(__file__).parent
    return script_dir.parent / "schema" / "ontology" / "ontology.context.jsonld"


def load_context() -> Dict[str, Any]:
    """Load the JSON-LD context."""
    context_path = get_context_path()
    if not context_path.exists():
        raise FileNotFoundError(f"Context file not found: {context_path}")

    with open(context_path) as f:
        return json.load(f)


def transform_namespace(ns_name: str, ns_data: Dict[str, Any], parent_path: str = "") -> Dict[str, Any]:
    """Transform a namespace to JSON-LD format."""
    full_path = f"{parent_path}/{ns_name}" if parent_path else ns_name

    result = {
        "@id": f"mif:namespace/{full_path}",
        "@type": "mif:Namespace",
        "name": ns_name,
    }

    if isinstance(ns_data, str):
        result["description"] = ns_data
    elif isinstance(ns_data, dict):
        if "description" in ns_data:
            result["description"] = ns_data["description"]
        if "type_hint" in ns_data:
            result["type_hint"] = ns_data["type_hint"]
        if "replaces" in ns_data:
            result["replaces"] = f"mif:namespace/{ns_data['replaces']}"

        # Handle children (hierarchical namespaces)
        if "children" in ns_data and isinstance(ns_data["children"], dict):
            result["children"] = {
                child_name: transform_namespace(child_name, child_data, full_path)
                for child_name, child_data in ns_data["children"].items()
            }

    return result


def transform_entity_type(et_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform an entity type to JSON-LD format."""
    name = et_data.get("name", "unknown")

    result = {
        "@id": f"mif:entityType/{name}",
        "@type": "mif:EntityType",
        "name": name,
        "base": et_data.get("base", "semantic"),
    }

    if "description" in et_data:
        result["description"] = et_data["description"]
    if "traits" in et_data:
        result["traits"] = [f"mif:trait/{t}" for t in et_data["traits"]]
    if "subtype_of" in et_data:
        sub = et_data["subtype_of"]
        sub = sub if isinstance(sub, list) else [sub]
        result["subtype_of"] = [f"mif:entityType/{s}" for s in sub if isinstance(s, str)]
    if "schema" in et_data:
        result["schema"] = et_data["schema"]

    return result


def transform_trait(trait_name: str, trait_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a trait to JSON-LD format."""
    result = {
        "@id": f"mif:trait/{trait_name}",
        "@type": "mif:Trait",
        "name": trait_name,
    }

    if "description" in trait_data:
        result["description"] = trait_data["description"]
    if "fields" in trait_data:
        result["fields"] = trait_data["fields"]
    if "requires" in trait_data:
        result["requires"] = trait_data["requires"]

    return result


def transform_relationship(rel_name: str, rel_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a relationship to JSON-LD format."""
    result = {
        "@id": f"mif:relationship/{rel_name}",
        "@type": "mif:Relationship",
        "name": rel_name,
    }

    if "description" in rel_data:
        result["description"] = rel_data["description"]
    if "from" in rel_data:
        result["from"] = [f"mif:entityType/{t}" for t in rel_data["from"]]
    if "to" in rel_data:
        result["to"] = [f"mif:entityType/{t}" for t in rel_data["to"]]
    if "symmetric" in rel_data:
        result["symmetric"] = rel_data["symmetric"]

    return result


def transform_discovery_pattern(pattern: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Transform a discovery pattern to JSON-LD format."""
    result = {
        "@id": f"mif:pattern/{index}",
        "@type": "mif:DiscoveryPattern",
    }

    if "content_pattern" in pattern:
        result["content_pattern"] = pattern["content_pattern"]
    if "file_pattern" in pattern:
        result["file_pattern"] = pattern["file_pattern"]
    if "suggest_entity" in pattern:
        result["suggest_entity"] = f"mif:entityType/{pattern['suggest_entity']}"
    if "suggest_namespace" in pattern:
        result["suggest_namespace"] = pattern["suggest_namespace"]

    return result


def yaml_to_jsonld(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert YAML ontology data to JSON-LD format."""
    context = load_context()

    # Build the JSON-LD document
    jsonld = {
        "@context": context["@context"],
    }

    # Transform ontology metadata
    ont_data = yaml_data.get("ontology", yaml_data)
    jsonld["@id"] = f"mif:ontology/{ont_data.get('id', 'unknown')}"
    jsonld["@type"] = "mif:Ontology"

    if "id" in ont_data:
        jsonld["identifier"] = ont_data["id"]
    if "version" in ont_data:
        jsonld["version"] = str(ont_data["version"])
    if "description" in ont_data:
        jsonld["description"] = ont_data["description"]
    if "schema_url" in ont_data:
        jsonld["schema_url"] = ont_data["schema_url"]

    # Transform namespaces
    if "namespaces" in yaml_data:
        jsonld["namespaces"] = {
            ns_name: transform_namespace(ns_name, ns_data)
            for ns_name, ns_data in yaml_data["namespaces"].items()
        }

    # Transform entity types
    entity_types = yaml_data.get("entity_types", [])
    if isinstance(entity_types, dict):
        entity_types = [{"name": k, **v} for k, v in entity_types.items()]
    if entity_types:
        jsonld["entity_types"] = [
            transform_entity_type(et) for et in entity_types
        ]

    # Transform traits
    if "traits" in yaml_data:
        jsonld["traits"] = {
            trait_name: transform_trait(trait_name, trait_data)
            for trait_name, trait_data in yaml_data["traits"].items()
        }

    # Transform relationships
    if "relationships" in yaml_data:
        jsonld["relationships"] = {
            rel_name: transform_relationship(rel_name, rel_data)
            for rel_name, rel_data in yaml_data["relationships"].items()
        }

    # Transform discovery config
    if "discovery" in yaml_data:
        discovery = yaml_data["discovery"]
        jsonld["discovery"] = {
            "enabled": discovery.get("enabled", False),
            "confidence_threshold": discovery.get("confidence_threshold", 0.8),
        }
        if "patterns" in discovery:
            jsonld["discovery"]["patterns"] = [
                transform_discovery_pattern(p, i)
                for i, p in enumerate(discovery["patterns"])
            ]

    return jsonld


def convert_file(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """Convert a single YAML file to JSON-LD."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Default output path
    if output_path is None:
        output_path = input_path.with_suffix(".jsonld")

    # Load YAML
    with open(input_path) as f:
        yaml_data = yaml.safe_load(f)

    if not yaml_data:
        raise ValueError(f"Empty or invalid YAML file: {input_path}")

    # Convert to JSON-LD
    jsonld_data = yaml_to_jsonld(yaml_data)

    # Write output
    with open(output_path, "w") as f:
        json.dump(jsonld_data, f, indent=2)

    return output_path


def convert_all_ontologies() -> list:
    """Convert all ontology YAML files in the ontologies directory."""
    script_dir = Path(__file__).parent
    ontologies_dir = script_dir.parent / "ontologies"

    if not ontologies_dir.exists():
        print(f"Ontologies directory not found: {ontologies_dir}", file=sys.stderr)
        return []

    converted = []

    # Find all .ontology.yaml files
    for yaml_file in ontologies_dir.rglob("*.ontology.yaml"):
        try:
            output_path = convert_file(yaml_file)
            print(f"Converted: {yaml_file.name} -> {output_path.name}")
            converted.append(output_path)
        except Exception as e:
            print(f"Error converting {yaml_file}: {e}", file=sys.stderr)

    return converted


def main():
    parser = argparse.ArgumentParser(
        description="Convert MIF ontology YAML files to JSON-LD"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input YAML file path"
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output JSON-LD file path (default: same name with .jsonld extension)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert all ontology files in ontologies/ directory"
    )

    args = parser.parse_args()

    if args.all:
        converted = convert_all_ontologies()
        print(f"\nConverted {len(converted)} files")
        sys.exit(0)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    try:
        result = convert_file(input_path, output_path)
        print(f"Created: {result}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
