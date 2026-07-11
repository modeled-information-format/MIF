#!/usr/bin/env python3
"""Structural guard for the #230 bug class recurring: a `relationships[].type`
core term declared in `schema/context.jsonld` but never actually registered
in `public/ns/vocabulary.jsonld` (or vice versa), so it silently resolves to
nothing a JSON-LD consumer can dereference.

`check_vocab_term_coverage.py` (#231) proves every `@type:@vocab` property's
schema `enum` has a matching registered JSON-LD term, by cross-referencing
`context.jsonld` against `mif.schema.json`. `relationships[].type` has no
schema `enum` -- only a free-form kebab-case `pattern`, since
`.mif/config.yaml`'s `relationship_types` registry (#232) allows custom
namespaced types by design -- so that script correctly and structurally
SKIPs it (see its own docstring). This is a genuinely different check
shape: not schema-enum-driven, but ontology-file-driven. It is deliberately
a separate script rather than a branch inside that one, so the two checks
don't have to share one `findings` schema built around an `enum` that only
one of them actually has (see #233's discussion of the two options).

This script cross-checks the OTHER source of truth for the same 9 core
relationship types: it walks `context.jsonld`'s `relationships.type.@context`
term-scoped mapping (the kebab-case-key -> `mif:PascalCase` pairs) and
confirms every target IRI is actually declared as an `rdfs:Class` in
`vocabulary.jsonld`'s `@graph`. A term present in one file but not the
other is exactly the #230 defect shape (context.jsonld's top-level term
block was declared but never wired to anything real).

Deliberately one-directional: `vocabulary.jsonld` also declares `mif:*`
classes for document types, concept types, etc. that have nothing to do
with `relationships[].type`, so there's no reliable way to detect an
"extra" relationship-type class sitting unmapped in the ontology without
also tagging *why* a given `rdfs:Class` exists -- vocabulary.jsonld doesn't
currently encode that. Catching a declared-but-unregistered term (the
actual historical bug) doesn't need that; it's covered.

Deliberately hardcoded to `relationships.type`, not a generalized
ontology-coverage framework: today it's the only `@type:@vocab` property
`check_vocab_term_coverage.py` SKIPs for lacking a schema enum. If a
second such property shows up later, generalize both scripts' discovery
then -- building that generality now, for one property, would be solving
a problem that doesn't exist yet.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTEXT = json.loads((ROOT / "schema" / "context.jsonld").read_text())["@context"]
VOCABULARY = json.loads((ROOT / "public" / "ns" / "vocabulary.jsonld").read_text())


def _registered_class_ids() -> set[str]:
    return {
        entry["@id"]
        for entry in VOCABULARY.get("@graph", [])
        if entry.get("@type") == "rdfs:Class" and isinstance(entry.get("@id"), str)
    }


def _relationship_type_terms() -> dict[str, str]:
    """The kebab-case-key -> `mif:PascalCase` mapping term-scoped onto
    `relationships.type` in context.jsonld. Returns {} (not an error) if
    the shape has changed -- main() reports that as its own failure."""
    relationships = CONTEXT.get("relationships", {})
    type_term = relationships.get("@context", {}).get("type", {})
    return type_term.get("@context", {}) if isinstance(type_term, dict) else {}


def main() -> int:
    terms = _relationship_type_terms()
    if not terms:
        print(
            "FAIL: schema/context.jsonld's relationships.type.@context term "
            "mapping is missing or empty -- expected the 9 core relationship "
            "types (relates-to, derived-from, ...) to be registered there."
        )
        return 1

    registered = _registered_class_ids()
    missing = sorted(
        f"{kebab_key} -> {iri}" for kebab_key, iri in terms.items() if iri not in registered
    )

    if missing:
        print(
            f"FAIL: {len(missing)} of {len(terms)} relationship-type term(s) "
            f"declared in context.jsonld are not registered as an rdfs:Class "
            f"in public/ns/vocabulary.jsonld:"
        )
        for entry in missing:
            print(f"  - {entry}")
        return 1

    print(
        f"All {len(terms)} relationship-type terms declared in "
        f"context.jsonld's relationships.type.@context are registered in "
        f"public/ns/vocabulary.jsonld."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
