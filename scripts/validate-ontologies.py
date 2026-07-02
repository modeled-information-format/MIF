#!/usr/bin/env python3
"""Validate ontology YAML files: schema conformance via ajv (the repo's JSON Schema
tool, matching the JSON-LD validation job), plus entity-type subsumption integrity
(cross-ontology `subtype_of` resolution, acyclicity, substitutability) — graph checks
no JSON Schema validator can express."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

import yaml


def load_yaml(yaml_path: Path) -> dict:
    """Load YAML file."""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def _ajv_validate(data: dict, schema_path: Path) -> list[str]:
    """Validate `data` against `schema_path` with ajv (draft2020, formats). Fail-closed:
    a missing ajv is reported as an error, never a silent pass."""
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        proc = subprocess.run(
            ["ajv", "validate", "--spec=draft2020", "--strict=false",
             "-c", "ajv-formats", "-s", str(schema_path), "-d", tmp],
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            return []
        out = (proc.stderr or proc.stdout or "").strip()
        return [f"  - schema: {ln}" for ln in out.splitlines() if ln.strip()][:20]
    except FileNotFoundError:
        return ["  - schema: ajv not found on PATH (install: npm i -g ajv-cli ajv-formats)"]
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _entity_types(ontology: dict) -> list[dict]:
    """Normalize entity_types (list, or name-keyed dict) to a list of dicts. Tolerant of
    schema-invalid input (non-dict ontology, scalar entity_types) — never raises."""
    if not isinstance(ontology, dict):
        return []
    ets = ontology.get("entity_types")
    if isinstance(ets, dict):
        # The key is the authoritative name — spread first so a stray `name` in the value can't override it.
        return [{**(v if isinstance(v, dict) else {}), "name": k} for k, v in ets.items()]
    if isinstance(ets, list):
        return [et for et in ets if isinstance(et, dict)]
    return []


def _type_info(ontology: dict) -> dict[str, dict]:
    """Map entity-type name -> {'required': set, 'subtype_of': list} for one ontology."""
    info: dict[str, dict] = {}
    for et in _entity_types(ontology):
        name = et.get("name")
        if not isinstance(name, str) or not name:
            continue
        sch = et.get("schema")
        req = (sch.get("required") if isinstance(sch, dict) else None) or []
        req = req if isinstance(req, list) else []
        sub = et.get("subtype_of") or []
        sub = sub if isinstance(sub, list) else [sub]
        info[name] = {
            # string-only: hashable + fail-closed on malformed YAML (ajv reports the bad type).
            "required": {r for r in req if isinstance(r, str)},
            # Only string parents: keeps `visible.get(p)` / `p in graph` hashable and
            # fail-closed when the YAML is malformed (the schema flags the bad type separately).
            "subtype_of": [s for s in sub if isinstance(s, str)],
        }
    return info


def load_ontology_corpus(ontology_dirs: list[Path]) -> dict[str, dict]:
    """Load every ontology YAML keyed by its id: {id: {'extends': [...], 'types': {name: info}}}."""
    corpus: dict[str, dict] = {}
    for d in ontology_dirs:
        if not d.exists():
            continue
        for f in d.glob("*.ontology.yaml"):
            try:
                data = load_yaml(f)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            ob = data.get("ontology")
            if not isinstance(ob, dict):
                continue
            oid = ob.get("id")
            if not isinstance(oid, str) or not oid:
                continue
            ext = ob.get("extends") or []
            ext = ext if isinstance(ext, list) else [ext]
            corpus[oid] = {
                "extends": [e for e in ext if isinstance(e, str)],
                "types": _type_info(data),
            }
    return corpus


def visible_types(oid: str, corpus: dict[str, dict], _seen: set | None = None) -> dict[str, dict]:
    """Type infos visible to ontology `oid`: its own ∪ those of every ontology it
    transitively `extends`. Own definitions win on a name collision."""
    _seen = _seen if _seen is not None else set()
    if oid in _seen or oid not in corpus:
        return {}
    _seen.add(oid)
    merged: dict[str, dict] = {}
    for parent in corpus[oid]["extends"]:
        merged.update(visible_types(parent, corpus, _seen))
    merged.update(corpus[oid]["types"])
    return merged


def _subtype_cycles(graph: dict[str, dict]) -> list[str]:
    """Cycle detection over the subtype_of graph via graphlib.TopologicalSorter, which
    reports the ACTUAL cycle nodes (not every type that merely depends on a cycle) and is
    iterative (no recursion limit). Self-edges are handled by the caller."""
    ts: TopologicalSorter = TopologicalSorter()
    for n, info in graph.items():
        preds = [p for p in info.get("subtype_of", []) if p in graph and p != n]
        ts.add(n, *preds)
    try:
        ts.prepare()
    except CycleError as e:
        cycle = e.args[1] if len(e.args) > 1 else []
        return [f"  - subtype_of cycle: {' -> '.join(str(c) for c in cycle)}"]
    return []


def check_subtype_of(ontology: dict, visible: dict[str, dict]) -> list[str]:
    """Entity-type subsumption integrity for one ontology, resolved against `visible`
    (its own types ∪ those of every ontology it extends): every `subtype_of` parent must
    resolve to a visible type, no type may be its own subtype, a subtype's `required` set
    must include each parent's (substitutability), and the graph must be acyclic.
    """
    errors: list[str] = []
    local = _type_info(ontology)
    for name, info in local.items():
        for p in info["subtype_of"]:
            if p == name:
                errors.append(f"  - entity_type '{name}': subtype_of cannot reference itself")
                continue
            parent = visible.get(p)
            if parent is None:
                errors.append(
                    f"  - entity_type '{name}': subtype_of parent '{p}' is not a declared "
                    f"entity type in this ontology or any it extends"
                )
                continue
            missing = parent["required"] - info["required"]
            if missing:
                errors.append(
                    f"  - entity_type '{name}': subtype_of '{p}' but its required set is missing "
                    f"parent field(s) {sorted(missing)} (a subtype must require at least the parent's)"
                )
    # Cycle detection over LOCAL types only: a cycle is attributed to the ontology that
    # declares it, not re-reported by every descendant. (extends is one-way, so a cycle
    # cannot span the ancestor boundary; an ancestor-internal cycle fails when the
    # ancestor is itself validated.)
    errors.extend(_subtype_cycles(local))
    return errors


def validate_ontology(ontology_path: Path, schema_path: Path, corpus: dict[str, dict]) -> list[str]:
    """Validate a single ontology file against the schema (ajv) and subsumption integrity."""
    errors = []
    try:
        ontology = load_yaml(ontology_path)
        errors.extend(_ajv_validate(ontology, schema_path))
        ob = ontology.get("ontology") if isinstance(ontology, dict) else None
        oid = ob.get("id") if isinstance(ob, dict) else None
        visible = visible_types(oid, corpus) if isinstance(oid, str) and oid else _type_info(ontology)
        errors.extend(check_subtype_of(ontology, visible))
    except yaml.YAMLError as e:
        errors.append(f"  - YAML parse error: {e}")
    except Exception as e:
        errors.append(f"  - Unexpected error: {e}")
    return errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate ontology YAML files against the schema and subtype_of integrity."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help=(
            "Directory containing *.ontology.yaml files to validate (e.g. a checked-out "
            "ontologies repo, or MIF's own vendored public/ontologies/ after "
            "vendor-ontologies.py runs). Defaults to this repo's own ontologies/ and "
            "ontologies/examples/, which no longer exist here since ontology content "
            "moved to the ontologies repo (ADR-018) -- pass --path explicitly instead "
            "of relying on the default."
        ),
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    schema_path = repo_root / "schema" / "ontology" / "ontology.schema.json"
    if args.path:
        ontology_dirs = [args.path]
    else:
        ontology_dirs = [
            repo_root / "ontologies",
            repo_root / "ontologies" / "examples",
        ]

    if not schema_path.exists():
        print(f"ERROR: Schema not found: {schema_path}")
        sys.exit(1)

    corpus = load_ontology_corpus(ontology_dirs)
    all_errors = {}
    total_files = 0

    for ontology_dir in ontology_dirs:
        if not ontology_dir.exists():
            continue
        for ontology_file in ontology_dir.glob("*.ontology.yaml"):
            total_files += 1
            errors = validate_ontology(ontology_file, schema_path, corpus)
            if errors:
                try:
                    rel_path = ontology_file.relative_to(repo_root)
                except ValueError:
                    rel_path = ontology_file
                all_errors[str(rel_path)] = errors

    if total_files == 0:
        # Fail closed: a silent "0 files, 0 errors" pass is indistinguishable
        # from a real clean corpus and has already caused a real incident
        # (this script kept reporting success after ontologies/ was removed
        # from this repo per ADR-018, when it should have said "nothing to
        # check"). Never let an empty scan look identical to a passing one.
        searched = ", ".join(str(d) for d in ontology_dirs)
        print(f"ERROR: no *.ontology.yaml files found under: {searched}")
        print("Pass --path <dir> to point at the corpus to validate.")
        sys.exit(1)

    if all_errors:
        print("Ontology validation FAILED:")
        for file_path, errors in all_errors.items():
            print(f"\n{file_path}:")
            for error in errors:
                print(error)
        sys.exit(1)
    else:
        print("All ontology files validated successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
