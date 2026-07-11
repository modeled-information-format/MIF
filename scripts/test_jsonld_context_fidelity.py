#!/usr/bin/env python3
"""Test that `schema/context.jsonld` round-trips losslessly under a real JSON-LD
1.1 processor (pyld), independent of this repo's own mif_convert.py serializer.

Regression coverage for term-definition bugs found by direct expand/compact
testing against pyld (not by inspection):

- `extensions` (`@container: @index` with no `@index` property): index-map
  expansion only preserves scalar-valued keys; a nested object value's own
  (unregistered) keys silently vanish on expand, because they resolve against
  no vocabulary. Fixed by `@type: @json`, which carries the whole subtree as
  an opaque JSON-LD literal.
- `documentType`, `citationType`, `citationRole` (`@type: @vocab` with no
  `@vocab` default and no registered terms for their enum): unrecognized
  values fall back to document-base-relative IRI resolution, so the same
  value expands to a different, non-equal IRI depending on the document's
  base URL. Fixed by registering each property's enum values as a
  term-scoped `mif:`-namespaced term (a nested `@context` on the property's
  own term definition), mirroring the existing `documents.hash`/
  `relationships` scoped-context pattern already in this file.

  An earlier version of `documentType`'s fix registered its 13 terms at the
  TOP LEVEL of the shared context instead of scoping them to `documentType`.
  JSON-LD `@type:@vocab` resolution checks the whole active context, not
  just the property being expanded, so that flat registration silently
  redirected `Citation.citationType` values that happen to share a name with
  a `documentType` enum value (`video`, `dataset`, `other` are valid values
  of both fields) to the wrong `mif:DocumentType*` IRI. Scoping every one of
  these three properties' terms to its own `@context` keeps them from
  contaminating each other despite the overlapping enum values.
"""
import json
import sys
from pathlib import Path

from pyld import jsonld

ROOT = Path(__file__).parent.parent
CONTEXT = json.loads((ROOT / "schema" / "context.jsonld").read_text())["@context"]

# (prop, node_type, extra_fields) for every term-scoped @type:@vocab property
# this file exercises. Single source of truth: adding a fourth such property
# means adding one row here, not touching N call sites.
VOCAB_PROPERTIES = [
    ("documentType", "DocumentReference", {"url": "https://example.com/doc"}),
    ("citationType", "Citation", {}),
    ("citationRole", "Citation", {}),
]

VOCAB_VALUES = {prop: list(CONTEXT[prop]["@context"].keys()) for prop, _, _ in VOCAB_PROPERTIES}


def _compact(expanded: object, ctx: dict) -> dict:
    result = jsonld.compact(expanded, ctx)
    assert isinstance(result, dict), f"jsonld.compact returned {type(result)}, expected dict"
    return result


def check_extensions_round_trip() -> list[str]:
    errors = []
    doc = {
        "@context": CONTEXT,
        "@type": "Memory",
        "@id": "urn:mif:test",
        "conceptType": "semantic",
        "content": "x",
        "created": "2026-01-01T00:00:00Z",
        "extensions": {
            "subcog:domain": "user",
            "subcog:hash": "sha256:abc",
            "subcog:meta": {"nested": "value", "count": 3},
            "subcog:list": [1, 2, 3],
        },
    }
    expanded = jsonld.expand(doc)
    compacted = _compact(expanded, CONTEXT)
    if compacted.get("extensions") != doc["extensions"]:
        errors.append(
            f"extensions did not round-trip losslessly: "
            f"got {compacted.get('extensions')!r}, want {doc['extensions']!r}"
        )
    return errors


def _expanded_vocab_id(expanded: list, prop: str, value: str, base_label: str) -> str | None:
    prop_iri = f"https://mif-spec.dev/ns/{prop}"
    try:
        return expanded[0][prop_iri][0]["@id"]
    except (IndexError, KeyError, TypeError) as e:
        return f"<malformed expansion for {prop}={value!r} ({base_label}): {e!r}>"


def check_vocab_base_independence() -> list[str]:
    errors = []
    for prop, node_type, extra_fields in VOCAB_PROPERTIES:
        for value in VOCAB_VALUES[prop]:
            doc = {"@context": CONTEXT, "@type": node_type, **extra_fields, prop: value}
            expanded_a = jsonld.expand(doc, {"base": "https://host-a.example/"})
            expanded_b = jsonld.expand(doc, {"base": "https://host-b.example/"})
            iri_a = _expanded_vocab_id(expanded_a, prop, value, "host-a")
            iri_b = _expanded_vocab_id(expanded_b, prop, value, "host-b")
            if iri_a != iri_b:
                errors.append(
                    f"{prop}={value!r} is base-URI-dependent: {iri_a!r} (host-a) != {iri_b!r} (host-b)"
                )
            elif iri_a is None or not iri_a.startswith("https://mif-spec.dev/ns/"):
                errors.append(f"{prop}={value!r} did not expand to a stable mif: IRI: {iri_a!r}")
            compacted = _compact(expanded_a, CONTEXT)
            if compacted.get(prop) != value:
                errors.append(f"{prop}={value!r} did not round-trip: got {compacted.get(prop)!r}")
    return errors


def check_vocab_custom_namespace_still_works() -> list[str]:
    errors = []
    for prop, node_type, extra_fields in VOCAB_PROPERTIES:
        doc = {"@context": CONTEXT, "@type": node_type, **extra_fields, prop: "subcog:widget"}
        expanded = jsonld.expand(doc, {"base": "https://host-a.example/"})
        compacted = _compact(expanded, CONTEXT)
        if compacted.get(prop) != "subcog:widget":
            errors.append(f"custom-namespaced {prop} regressed: got {compacted.get(prop)!r}")
    return errors


def check_document_type_citation_type_no_cross_contamination() -> list[str]:
    """documentType and citationType share enum values (video/dataset/other);
    each must resolve within its own vocab, never the other's."""
    errors = []
    shared = set(VOCAB_VALUES["documentType"]) & set(VOCAB_VALUES["citationType"])
    if not shared:
        errors.append("expected documentType/citationType to share at least one enum value to test contamination against")
        return errors
    for value in sorted(shared):
        doc_a = {"@context": CONTEXT, "@type": "DocumentReference", "url": "https://x", "documentType": value}
        iri_a = _expanded_vocab_id(jsonld.expand(doc_a), "documentType", value, "n/a")
        if iri_a is not None and "CitationType" in iri_a:
            errors.append(f"documentType={value!r} contaminated by citationType terms: {iri_a}")
        doc_b = {"@context": CONTEXT, "@type": "Citation", "citationType": value}
        iri_b = _expanded_vocab_id(jsonld.expand(doc_b), "citationType", value, "n/a")
        if iri_b is not None and "DocumentType" in iri_b:
            errors.append(f"citationType={value!r} contaminated by documentType terms: {iri_b}")
    return errors


CHECKS = [
    ("extensions round-trips losslessly through @type:@json (#224)", check_extensions_round_trip),
    ("documentType/citationType/citationRole are base-URI-independent for all enum values (#225, #226)", check_vocab_base_independence),
    ("documentType/citationType/citationRole custom-namespaced escape hatch still resolves", check_vocab_custom_namespace_still_works),
    ("documentType and citationType don't contaminate each other's shared enum values", check_document_type_citation_type_no_cross_contamination),
]


def main() -> int:
    failed = []
    for label, check in CHECKS:
        errors = check()
        if errors:
            failed.append(label)
            print(f"FAIL: {label}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"PASS: {label}")
    if failed:
        print(f"\nJSON-LD context fidelity test FAILED: {failed}")
        return 1
    print("\nAll JSON-LD context fidelity tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
