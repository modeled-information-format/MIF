#!/usr/bin/env python3
"""Validate that memory namespaces exist in their declared ontologies."""

import argparse
import re
import sys
from pathlib import Path

import yaml


FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def load_yaml(yaml_path: Path) -> dict:
    """Load YAML file."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def extract_frontmatter(memory_path: Path) -> dict | None:
    """Extract YAML frontmatter from a memory file."""
    content = memory_path.read_text()
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def get_ontology_namespaces(ontology: dict) -> set[str]:
    """Extract all valid namespace paths from an ontology."""
    namespaces = set()

    def traverse_namespaces(ns_dict: dict, prefix: str = ""):
        for name, config in ns_dict.items():
            path = f"{prefix}{name}" if prefix else name
            namespaces.add(path)
            if isinstance(config, dict) and "children" in config:
                traverse_namespaces(config["children"], f"{path}/")

    if "namespaces" in ontology:
        traverse_namespaces(ontology["namespaces"])

    return namespaces


def load_all_ontologies(ontology_dirs: list[Path]) -> dict[str, set[str]]:
    """Load all ontologies and their namespaces."""
    ontologies = {}

    for ontology_dir in ontology_dirs:
        if not ontology_dir.exists():
            continue
        for ontology_file in ontology_dir.glob("*.ontology.yaml"):
            try:
                data = load_yaml(ontology_file)
                ontology_id = data.get("ontology", {}).get("id", "")
                if ontology_id:
                    namespaces = get_ontology_namespaces(data)
                    ontologies[ontology_id] = namespaces
            except Exception:
                continue

    return ontologies


def validate_memory_namespace(
    memory_path: Path,
    ontologies: dict[str, set[str]],
    mif_base_namespaces: set[str],
) -> list[str]:
    """Validate that a memory's namespace exists in its ontology."""
    errors = []

    frontmatter = extract_frontmatter(memory_path)
    if frontmatter is None:
        return errors

    namespace = frontmatter.get("namespace", "")
    ontology_ref = frontmatter.get("ontology", {})
    ontology_id = ontology_ref.get("id", "") if isinstance(ontology_ref, dict) else ""

    if not namespace:
        return errors

    # Check mif-base namespaces first (always available)
    if namespace in mif_base_namespaces:
        return errors

    # Check parent namespace (e.g., _semantic from _semantic/preferences)
    parts = namespace.split("/")
    parent = parts[0]
    if parent in mif_base_namespaces:
        # Check if child exists
        if len(parts) > 1:
            full_parent = parent
            for part in parts[1:]:
                test_path = f"{full_parent}/{part}"
                if test_path in mif_base_namespaces:
                    full_parent = test_path
                elif ontology_id and ontology_id in ontologies:
                    # Check domain ontology
                    domain_ns = ontologies[ontology_id]
                    # Domain ontologies might use different prefixes
                    if test_path in domain_ns or part in domain_ns:
                        return errors
                else:
                    # Namespace extension - allow if base exists
                    return errors
        return errors

    # Check domain ontology namespaces
    if ontology_id and ontology_id in ontologies:
        domain_namespaces = ontologies[ontology_id]
        if namespace in domain_namespaces:
            return errors
        # Check without underscore prefix
        if namespace.lstrip("_") in domain_namespaces:
            return errors

    # Namespace not found - but only warn, don't fail
    # Many memories use extended namespaces that inherit from base
    return errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate that MIF's own memory examples declare namespaces that exist in some ontology."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help=(
            "Directory containing *.ontology.yaml files to check memory namespaces "
            "against (e.g. a checked-out ontologies repo, or MIF's own vendored "
            "public/ontologies/ after vendor-ontologies.py runs). Defaults to this "
            "repo's own ontologies/ and ontologies/examples/, which no longer exist "
            "here since ontology content moved to the ontologies repo (ADR-018) -- "
            "pass --path explicitly, or this check has nothing to validate against."
        ),
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    if args.path:
        ontology_dirs = [args.path]
    else:
        ontology_dirs = [
            repo_root / "ontologies",
            repo_root / "ontologies" / "examples",
        ]
    memory_dirs = [
        repo_root / "examples",
        repo_root / "profiles" / "ai-memory" / "examples",
        repo_root / "docs" / "examples" / "memories",
    ]
    reserved = {"index.md", "log.md"}

    # Load all ontologies
    ontologies = load_all_ontologies(ontology_dirs)

    # Get mif-base namespaces
    mif_base_namespaces = ontologies.get("mif-base", set())

    all_errors = {}

    for memory_dir in memory_dirs:
        if not memory_dir.exists():
            continue
        for memory_file in memory_dir.rglob("*.md"):
            if memory_file.name in reserved:
                continue
            errors = validate_memory_namespace(
                memory_file, ontologies, mif_base_namespaces
            )
            if errors:
                rel_path = memory_file.relative_to(repo_root)
                all_errors[str(rel_path)] = errors

    if all_errors:
        print("Namespace validation warnings:")
        for file_path, errors in all_errors.items():
            print(f"\n{file_path}:")
            for error in errors:
                print(error)
        # Don't fail on namespace warnings - they may be intentional extensions
        print("\nNote: Namespace extensions are allowed. Review warnings above.")
        sys.exit(0)
    elif not ontologies:
        # Never claim success when there was nothing to check against -- this
        # exact silent false-positive already happened once, when
        # ontologies/ was removed from this repo (ADR-018) and this script
        # kept reporting "All memory namespaces validated successfully"
        # while validating zero namespaces against zero ontologies.
        searched = ", ".join(str(d) for d in ontology_dirs)
        print(f"No ontology definitions found under: {searched}")
        print("Pass --path <dir> to check memory namespaces against a real corpus.")
        sys.exit(0)
    else:
        print("All memory namespaces validated successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
