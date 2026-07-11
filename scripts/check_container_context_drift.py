#!/usr/bin/env python3
"""Structural guard against issue #259: `schema/container-context.jsonld`
hand-copies a handful of prefix/term definitions that already exist
verbatim in `schema/context.jsonld`, instead of composing the two files.
Nothing enforces they stay in sync, and this has already happened once in
this branch's own history (the corpus-level and per-unit `extensions` terms
diverged until issue #224 reconciled them the same day).

This is the low-effort option (c) from #259: a CI check that fails if the
shared definitions diverge, without restructuring either file (rejected:
composing via an array `@context` would import `context.jsonld`'s unrelated
per-unit memory vocabulary into the container envelope's root active
context, cutting against ADR-021 Decision point 8's "minimal blast radius"
design driver).

Checks, by direct JSON comparison (no JSON-LD processing needed -- these are
exact-string/exact-structure duplications, not semantically-equivalent
rephrasings):

- The `mif`/`prov`/`xsd` prefix-IRI declarations.
- The `extensions` term definition (both files define it at the top level).
- The `wasDerivedFrom` term definition (top-level in `context.jsonld`;
  nested inside `container-context.jsonld`'s `provenance` term's own scoped
  `@context` -- compared by definition, not by JSON position).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CORE_CONTEXT = json.loads((ROOT / "schema" / "context.jsonld").read_text())["@context"]
CONTAINER_CONTEXT = json.loads((ROOT / "schema" / "container-context.jsonld").read_text())["@context"]

SHARED_PREFIXES = ("mif", "prov", "xsd")


def _wasderivedfrom_in_container() -> object:
    try:
        return CONTAINER_CONTEXT["provenance"]["@context"]["wasDerivedFrom"]
    except (KeyError, TypeError) as e:
        return f"<not found: {e!r}>"


CHECKS = [
    (f"prefix {p!r} matches between context.jsonld and container-context.jsonld",
     lambda p=p: (CORE_CONTEXT.get(p), CONTAINER_CONTEXT.get(p)))
    for p in SHARED_PREFIXES
] + [
    ("extensions term definition matches between context.jsonld and container-context.jsonld",
     lambda: (CORE_CONTEXT.get("extensions"), CONTAINER_CONTEXT.get("extensions"))),
    ("wasDerivedFrom term definition matches (top-level in context.jsonld, "
     "nested under provenance in container-context.jsonld)",
     lambda: (CORE_CONTEXT.get("wasDerivedFrom"), _wasderivedfrom_in_container())),
]


def main() -> int:
    failed = []
    for label, get_pair in CHECKS:
        core_val, container_val = get_pair()
        if core_val == container_val:
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label}")
            print(f"  context.jsonld:           {core_val!r}")
            print(f"  container-context.jsonld: {container_val!r}")
            failed.append(label)

    if failed:
        print(f"\ncontainer-context.jsonld drift check FAILED: {failed}")
        return 1
    print(f"\nAll {len(CHECKS)} shared context.jsonld/container-context.jsonld definitions match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
