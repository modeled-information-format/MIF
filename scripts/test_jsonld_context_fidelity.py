#!/usr/bin/env python3
"""Test that `schema/context.jsonld` round-trips losslessly under a real JSON-LD
1.1 processor (pyld), independent of this repo's own mif_convert.py serializer.

Regression coverage for two term-definition bugs found by direct expand/compact
testing against pyld (not by inspection):

- `extensions` (`@container: @index` with no `@index` property): index-map
  expansion only preserves scalar-valued keys; a nested object value's own
  (unregistered) keys silently vanish on expand, because they resolve against
  no vocabulary. Fixed by `@type: @json`, which carries the whole subtree as
  an opaque JSON-LD literal.
- `documentType` (`@type: @vocab` with no `@vocab` default and no registered
  terms for its enum): unrecognized values fall back to document-base-relative
  IRI resolution, so the same value expands to a different, non-equal IRI
  depending on the document's base URL. Fixed by registering each
  `DocumentReference.documentType` enum value as an explicit `mif:`-namespaced
  term, mirroring the existing `conceptType`/`semantic`|`episodic`|`procedural`
  pattern already in this file.
"""
import json
import sys
from pathlib import Path

from pyld import jsonld

ROOT = Path(__file__).parent.parent
CONTEXT = json.loads((ROOT / "schema" / "context.jsonld").read_text())["@context"]

DOCUMENT_TYPES = [
    "pdf", "html", "markdown", "text", "transcript", "dataset", "spreadsheet",
    "presentation", "image", "audio", "video", "email", "other",
]


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


def check_document_type_base_independence() -> list[str]:
    errors = []
    for value in DOCUMENT_TYPES:
        doc = {
            "@context": CONTEXT,
            "@type": "DocumentReference",
            "url": "https://example.com/doc",
            "documentType": value,
        }
        expanded_a = jsonld.expand(doc, {"base": "https://host-a.example/"})
        expanded_b = jsonld.expand(doc, {"base": "https://host-b.example/"})
        iri_a = expanded_a[0]["https://mif-spec.dev/ns/documentType"]
        iri_b = expanded_b[0]["https://mif-spec.dev/ns/documentType"]
        if iri_a != iri_b:
            errors.append(
                f"documentType={value!r} is base-URI-dependent: "
                f"{iri_a!r} (host-a) != {iri_b!r} (host-b)"
            )
        elif not iri_a[0]["@id"].startswith("https://mif-spec.dev/ns/"):
            errors.append(
                f"documentType={value!r} did not expand to a stable mif: IRI: {iri_a!r}"
            )
        compacted = _compact(expanded_a, CONTEXT)
        if compacted.get("documentType") != value:
            errors.append(
                f"documentType={value!r} did not round-trip: got {compacted.get('documentType')!r}"
            )
    return errors


def check_document_type_custom_namespace_still_works() -> list[str]:
    errors = []
    doc = {
        "@context": CONTEXT,
        "@type": "DocumentReference",
        "url": "https://example.com/x",
        "documentType": "subcog:widget",
    }
    expanded = jsonld.expand(doc, {"base": "https://host-a.example/"})
    compacted = _compact(expanded, CONTEXT)
    if compacted.get("documentType") != "subcog:widget":
        errors.append(
            f"custom-namespaced documentType regressed: got {compacted.get('documentType')!r}"
        )
    return errors


CHECKS = [
    ("extensions round-trips losslessly through @type:@json (#224)", check_extensions_round_trip),
    ("documentType is base-URI-independent for all enum values (#225)", check_document_type_base_independence),
    ("documentType custom-namespaced escape hatch still resolves", check_document_type_custom_namespace_still_works),
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
