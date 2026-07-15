#!/usr/bin/env python3
"""Regression test for issue #274: `memoryType` is documented (README.md,
docs/SCHEMA-REFERENCE.md, ns/README.md, ADR-001's compliance audit) as a
deprecated v0.1 alias for `conceptType`, "retained for backward
compatibility" -- but `schema/mif.schema.json`'s flat `required` list only
ever accepted `conceptType`, so a document carrying just the legacy
`memoryType` field always failed validation regardless of age. Fixed by
replacing the flat `conceptType` requirement with a top-level
`anyOf: [{required: [conceptType]}, {required: [memoryType]}]`, mirroring
the same pattern `DocumentReference` already uses for its own `url`/`id`
alternative.

The same duplicate `conceptType`-required anchor exists in
`schema/container.schema.json`'s `$defs.Record` (documented at that file's
own `payload` description as needing to be "kept in sync with
mif.schema.json if its requirements ever change") -- fixed the same way,
plus the versioned/aliased mirrors under `public/schema/` that a local
`/code-review` pass found were left stale (a repeat of issue #184: canonical
schema changed, `latest`/`v1` aliases left behind), which would have failed
this repo's own required `schema-check.yml` mirror-alias gate.

Run: ``python -m pytest scripts/test_concept_type_alias.py -q`` from the repo root.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schema"
PUBLIC_SCHEMA_DIR = ROOT / "public" / "schema"

MIF_SCHEMA = json.loads((SCHEMA_DIR / "mif.schema.json").read_text())
CONTAINER_SCHEMA = json.loads((SCHEMA_DIR / "container.schema.json").read_text())
RECORD_SCHEMA = CONTAINER_SCHEMA["$defs"]["Record"]

BASE_PAYLOAD = {
    "@context": "https://mif-spec.dev/schema/context.jsonld",
    "@type": "Memory",
    "@id": "urn:mif:11111111-1111-4111-8111-111111111111",
    "content": "GB300 NVL72 compute nodes MUST meet NVQual and NVCert.",
    "created": "2026-06-25T00:00:00Z",
}


def _mif_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(MIF_SCHEMA)


def _record_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(RECORD_SCHEMA)


# --------------------------------------------------------------------------- #
# schema/mif.schema.json: the per-unit Memory payload.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "extra",
    [
        {"conceptType": "semantic"},
        {"memoryType": "semantic"},
        {"conceptType": "semantic", "memoryType": "semantic"},
    ],
    ids=["conceptType-alone", "memoryType-alone", "both-present"],
)
def test_concept_type_or_memory_type_satisfies_required(extra):
    _mif_validator().validate({**BASE_PAYLOAD, **extra})


def test_neither_concept_type_nor_memory_type_is_invalid():
    with pytest.raises(jsonschema.ValidationError):
        _mif_validator().validate(dict(BASE_PAYLOAD))


def test_memory_type_does_not_bypass_other_required_fields():
    """The anyOf only substitutes for conceptType -- it must not mask an
    unrelated missing required field (e.g. `created`)."""
    payload = {**BASE_PAYLOAD, "memoryType": "semantic"}
    del payload["created"]
    with pytest.raises(jsonschema.ValidationError):
        _mif_validator().validate(payload)


def test_memory_type_out_of_enum_is_still_rejected():
    """memoryType must still honor the triad enum -- the anyOf only changes
    which field can satisfy `required`, not what values are acceptable."""
    with pytest.raises(jsonschema.ValidationError):
        _mif_validator().validate({**BASE_PAYLOAD, "memoryType": "not-a-real-value"})


# --------------------------------------------------------------------------- #
# schema/container.schema.json: the Container Profile envelope's kind:memory
# discrimination anchor (duplicates mif.schema.json's requirement by design;
# must be kept in lockstep -- this is the path scripts/validate_container.py
# actually exercises for *.corpus.json envelopes).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "extra",
    [
        {"conceptType": "semantic"},
        {"memoryType": "semantic"},
    ],
    ids=["conceptType-alone", "memoryType-alone"],
)
def test_container_memory_record_accepts_concept_type_or_memory_type(extra):
    record = {"kind": "memory", "payload": {**BASE_PAYLOAD, **extra}}
    _record_validator().validate(record)


def test_container_memory_record_without_either_is_invalid():
    record = {"kind": "memory", "payload": dict(BASE_PAYLOAD)}
    with pytest.raises(jsonschema.ValidationError):
        _record_validator().validate(record)


# --------------------------------------------------------------------------- #
# Mirror consistency: the canonical root (schema/, public/schema/) and the
# "live" versioned mirror that public/schema/index.json's `latest`/`v1`
# aliases currently point at must be byte-identical for mif.schema.json and
# container.schema.json -- same invariant schema-check.yml's own
# mirror-alias gate enforces (see issue #184: canonical changed, `latest`
# left stale, gate caught it). A frozen, already-released version (anything
# NOT the alias target) is intentionally NOT compared here.
# --------------------------------------------------------------------------- #
def _live_mirror_version() -> str:
    index = json.loads((PUBLIC_SCHEMA_DIR / "index.json").read_text())
    return index["aliases"]["latest"]


@pytest.mark.parametrize("schema_name", ["mif.schema.json", "container.schema.json"])
def test_canonical_root_matches_public_mirror(schema_name):
    assert (SCHEMA_DIR / schema_name).read_text() == (
        PUBLIC_SCHEMA_DIR / schema_name
    ).read_text()


@pytest.mark.parametrize("schema_name", ["mif.schema.json", "container.schema.json"])
@pytest.mark.parametrize("alias", ["latest", "v1"])
def test_live_alias_mirror_matches_canonical_root(schema_name, alias):
    live_version = _live_mirror_version()
    canonical = (PUBLIC_SCHEMA_DIR / schema_name).read_text()
    assert canonical == (PUBLIC_SCHEMA_DIR / alias / schema_name).read_text()
    assert canonical == (PUBLIC_SCHEMA_DIR / live_version / schema_name).read_text()
