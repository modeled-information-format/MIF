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
from pyld.jsonld import JsonLdError

from mif_convert import CONTEXT_URL as _CORE_CONTEXT_URL

ROOT = Path(__file__).parent.parent
CONTAINER_CONTEXT = json.loads((ROOT / "schema" / "container-context.jsonld").read_text())["@context"]

# `payload`'s own term definition in container-context.jsonld points at the
# remote schema/context.jsonld -- and JSON-LD 1.1 context processing resolves
# EVERY term-scoped @context reachable from an expanded @type's active
# context up front, not lazily only for properties actually present in the
# document. So even a test document with no `payload` key still triggers
# resolution of that URL on every expand() call. A live network fetch in a
# test is fragile (flaky, needs egress, and this repo's CI image has no
# default pyld document loader configured at all -- confirmed the hard way:
# this test failed in CI with "No default document loader configured" the
# first time it ran, despite passing locally where a document loader
# happened to be available). This loader makes the test fully hermetic by
# resolving that one known URL to the real local file, and refusing
# everything else.
# _CORE_CONTEXT_URL is imported from mif_convert (CONTEXT_URL) above, so a
# future change to the published context URL updates this loader too instead
# of leaving a stale hard-coded copy here.
_CORE_CONTEXT_DOC = json.loads((ROOT / "schema" / "context.jsonld").read_text())


def _offline_loader(url: str, _options: dict | None = None) -> dict:
    if url == _CORE_CONTEXT_URL:
        return {"contentType": "application/ld+json", "contextUrl": None, "documentUrl": url, "document": _CORE_CONTEXT_DOC}
    raise JsonLdError(
        f"unexpected remote fetch in offline test: {url}",
        "jsonld.LoadDocumentError",
        {"url": url},
        code="loading document failed",
    )


_OPTS = {"documentLoader": _offline_loader}


def _expand(doc: dict) -> list:
    return jsonld.expand(doc, _OPTS)


def _compact(expanded: object, ctx: dict) -> dict:
    result = jsonld.compact(expanded, ctx, _OPTS)
    assert isinstance(result, dict), f"jsonld.compact returned {type(result)}, expected dict"
    return result


def check_extensions_round_trip() -> list[str]:
    errors = []
    doc = {
        "@context": CONTAINER_CONTEXT,
        "@type": "MemoryCorpus",
        "containerProfileVersion": "1.0.0",
        "records": [],
        "extensions": {
            "mnemos:compressionManifest": {"algorithm": "gzip", "level": 5, "chunks": [1, 2, 3]},
            "mnemos:tag": "nightly",
        },
    }
    expanded = _expand(doc)
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
    expanded = _expand(doc)
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
    compacted = _compact(_expand(doc), CONTAINER_CONTEXT)
    if compacted.get("provenance", {}).get("wasDerivedFrom") != "urn:mif:corpus:previous":
        errors.append(f"provenance.wasDerivedFrom did not round-trip: got {compacted.get('provenance')!r}")
    return errors


def check_document_payload_hash_round_trip() -> list[str]:
    """Regression check: the core context defines `hash` only inside the
    `documents` term's scoped @context, which a bare `kind: "document"`
    DocumentReference payload never activates -- without the payload-scoped
    `hash` copy in container-context.jsonld, the ADR-014 integrity anchor
    silently vanished on expand."""
    errors = []
    hash_obj = {"algorithm": "sha256", "value": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"}
    doc = {
        "@context": CONTAINER_CONTEXT,
        "@type": "MemoryCorpus",
        "containerProfileVersion": "1.0.0",
        "records": [
            {
                "kind": "document",
                "payload": {
                    "@type": "DocumentReference",
                    "url": "https://example.com/doc.pdf",
                    "contentType": "application/pdf",
                    "hash": hash_obj,
                },
            }
        ],
    }
    compacted = _compact(_expand(doc), CONTAINER_CONTEXT)
    records = compacted.get("records")
    record = records[0] if isinstance(records, list) else records
    payload = record.get("payload", {}) if isinstance(record, dict) else {}
    if payload.get("hash") != hash_obj:
        errors.append(
            f"document payload hash did not round-trip: got {payload.get('hash')!r}, want {hash_obj!r}"
        )
    return errors


def check_provenance_provnode_forms_round_trip() -> list[str]:
    """Regression check: the `provenance` scoped context must carry the same
    latitude the schema grants (ProvNode keyed by `id`, and the other PROV
    relations context.jsonld registers) -- without the `id` alias and the
    PROV relation terms, those keys silently dropped on expand."""
    errors = []
    doc = {
        "@context": CONTAINER_CONTEXT,
        "@type": "MemoryCorpus",
        "containerProfileVersion": "1.0.0",
        "records": [],
        "provenance": {
            "@type": "prov:Entity",
            "wasDerivedFrom": {"id": "urn:mif:bundle:prev"},
            "wasGeneratedBy": "urn:mif:activity:export-run-42",
        },
    }
    compacted = _compact(_expand(doc), CONTAINER_CONTEXT)
    prov = compacted.get("provenance", {})
    if prov.get("wasDerivedFrom") not in ("urn:mif:bundle:prev", {"id": "urn:mif:bundle:prev"}):
        errors.append(f"id-keyed wasDerivedFrom ProvNode lost its identifier: got {prov.get('wasDerivedFrom')!r}")
    if prov.get("wasGeneratedBy") != "urn:mif:activity:export-run-42":
        errors.append(f"wasGeneratedBy did not round-trip: got {prov.get('wasGeneratedBy')!r}")
    return errors


CHECKS = [
    ("extensions round-trips losslessly through @type:@json (#257)", check_extensions_round_trip),
    ("extensions survives expand as an opaque @json literal, not an @container:@index map (#257)",
     check_extensions_scalar_and_nested_survive_expand),
    ("provenance.wasDerivedFrom round-trips", check_provenance_wasderivedfrom_round_trip),
    ("kind:document payload hash survives expand/compact", check_document_payload_hash_round_trip),
    ("provenance ProvNode forms (id-keyed node, other PROV relations) survive expand/compact",
     check_provenance_provnode_forms_round_trip),
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
