#!/usr/bin/env python3
"""Test that `schema/container-context.jsonld` round-trips losslessly under a
real JSON-LD 1.1 processor (pyld) -- the container-profile counterpart to
`test_jsonld_context_fidelity.py`'s coverage of `schema/context.jsonld`.

Regression coverage for issue #257: ADR-021's `extensions` term deliberately
maps `@type: @json` instead of the `@container: @index` pattern that caused
real content-loss on JSON-LD expand elsewhere in this repo (the per-unit
`extensions` term, fixed independently as issue #224) -- index-map expansion
only preserves scalar-valued keys, silently dropping a nested object value's
own unregistered keys. Nothing until this test actually exercised a real
expand/compact against `container-context.jsonld` to confirm that choice
holds; a future edit reintroducing `@container: @index` here would have
silently regressed the exact defect this ADR exists to prevent.
"""
import json
import sys
from pathlib import Path

from pyld import jsonld

ROOT = Path(__file__).parent.parent
CONTAINER_CONTEXT = json.loads((ROOT / "schema" / "container-context.jsonld").read_text())["@context"]


def _compact(expanded: object, ctx: dict) -> dict:
    result = jsonld.compact(expanded, ctx)
    assert isinstance(result, dict), f"jsonld.compact returned {type(result)}, expected dict"
    return result


def check_extensions_round_trip() -> list[str]:
    """No `payload` key here deliberately: `payload`'s own `@context` points
    at the remote `schema/context.jsonld`, which this offline test must not
    depend on fetching -- `extensions` and `records` are envelope-level
    terms and don't need it."""
    errors = []
    doc = {
        "@context": CONTAINER_CONTEXT,
        "@type": "MemoryCorpus",
        "containerProfileVersion": "1.0",
        "records": [],
        "extensions": {
            "mnemos:compressionManifest": {"algorithm": "gzip", "level": 5, "chunks": [1, 2, 3]},
            "mnemos:tag": "nightly",
        },
    }
    expanded = jsonld.expand(doc)
    compacted = _compact(expanded, CONTAINER_CONTEXT)
    if compacted.get("extensions") != doc["extensions"]:
        errors.append(
            f"extensions did not round-trip losslessly: "
            f"got {compacted.get('extensions')!r}, want {doc['extensions']!r}"
        )
    return errors


def check_extensions_scalar_and_nested_survive_expand() -> list[str]:
    """The specific failure mode `@container: @index` produces: a nested
    object value's own keys resolve against no vocabulary and vanish on
    expand, while sibling scalar values survive -- so this checks the
    expanded form directly, not just the round-tripped compaction, to catch
    a regression even if compaction happened to mask it."""
    errors = []
    doc = {
        "@context": CONTAINER_CONTEXT,
        "@type": "MemoryCorpus",
        "records": [],
        "extensions": {"mnemos:manifest": {"deep": {"deeper": "value"}}},
    }
    expanded = jsonld.expand(doc)
    try:
        ext = expanded[0]["https://mif-spec.dev/ns/extensions"]
    except (IndexError, KeyError, TypeError) as e:
        errors.append(f"malformed expansion reaching extensions: {e!r}")
        return errors
    if not ext or "@value" not in ext[0]:
        errors.append(f"extensions did not expand as an opaque @json literal: {ext!r}")
    elif ext[0]["@value"] != doc["extensions"]:
        errors.append(
            f"extensions @json literal lost content on expand (the @container:@index "
            f"content-loss bug this test guards against): got {ext[0]['@value']!r}, "
            f"want {doc['extensions']!r}"
        )
    return errors


def check_provenance_wasderivedfrom_round_trip() -> list[str]:
    errors = []
    doc = {
        "@context": CONTAINER_CONTEXT,
        "@type": "MemoryCorpus",
        "records": [],
        "provenance": {"wasDerivedFrom": "urn:mif:corpus:previous"},
    }
    compacted = _compact(jsonld.expand(doc), CONTAINER_CONTEXT)
    if compacted.get("provenance", {}).get("wasDerivedFrom") != "urn:mif:corpus:previous":
        errors.append(f"provenance.wasDerivedFrom did not round-trip: got {compacted.get('provenance')!r}")
    return errors


CHECKS = [
    ("extensions round-trips losslessly through @type:@json (#257)", check_extensions_round_trip),
    ("extensions survives expand as an opaque @json literal, not an @container:@index map (#257)",
     check_extensions_scalar_and_nested_survive_expand),
    ("provenance.wasDerivedFrom round-trips", check_provenance_wasderivedfrom_round_trip),
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
        print(f"\ncontainer-context.jsonld fidelity test FAILED: {failed}")
        return 1
    print("\nAll container-context.jsonld fidelity tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
