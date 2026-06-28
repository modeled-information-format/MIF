#!/usr/bin/env python3
"""Test entity-type subsumption (`subtype_of`) integrity.

Exercises `check_subtype_of` from validate-ontologies.py against the fixtures in
test/subtype_of/, supplying the `visible` type set (own ∪ extended-ancestor types) the
production corpus would resolve. Covers: a valid local subtype, a parent resolved from
an ancestor, a parent that does NOT resolve even though the ontology `extends` something
(the bug the global resolver fixes), a dangling parent, a cycle, a self-reference, and a
substitutability-incompatible subtype (schema-valid, but missing a parent's required field).
"""
import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location(
    "validate_ontologies", ROOT / "scripts" / "validate-ontologies.py"
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def _load(name: str) -> dict:
    return yaml.safe_load((ROOT / "test" / "subtype_of" / name).read_text())


# (label, fixture, extra ancestor-visible types, should_pass)
CASES = [
    ("valid local subtype + compatible schema", "valid.ontology.yaml", {}, True),
    ("parent resolved from an ancestor", "extended.ontology.yaml",
     {"control": {"required": set(), "subtype_of": []}}, True),
    ("extends-but-parent-unresolvable is rejected", "extended.ontology.yaml", {}, False),
    ("dangling parent rejected", "dangling.ontology.yaml", {}, False),
    ("cycle rejected", "cyclic.ontology.yaml", {}, False),
    ("self-reference rejected", "self.ontology.yaml", {}, False),
    ("substitutability-incompatible subtype rejected", "incompatible.ontology.yaml", {}, False),
]


def main() -> int:
    failed = []
    for label, fname, ancestors, should_pass in CASES:
        data = _load(fname)
        visible = dict(ancestors)
        visible.update(_mod._type_info(data))
        errs = _mod.check_subtype_of(data, visible)
        ok = (len(errs) == 0) == should_pass
        verdict = "PASS" if ok else "FAIL"
        expect = "no errors" if should_pass else "errors"
        print(f"{verdict}: {label} ({fname}, expected {expect}) -> {errs or 'no errors'}")
        if not ok:
            failed.append(label)
    if failed:
        print(f"\nsubtype_of integrity test FAILED: {failed}")
        return 1
    print("\nAll subtype_of integrity tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
