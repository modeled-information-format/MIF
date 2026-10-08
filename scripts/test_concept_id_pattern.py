#!/usr/bin/env python3
"""Regression test: a concept `@id` MUST be `urn:mif:<uuid>` (SPECIFICATION.md
§6.1), where `<uuid>` is the frontmatter `id`.

`schema/mif.schema.json` used to constrain `@id` with only `^urn:mif:`, so a
slug id such as `urn:mif:decision-react-over-vue` (once used by the spec's own
§16.2 example) validated silently. The reserved `urn:mif:` sub-namespaces
(`entity:`, `agent:`, `activity:`, `conversation:`, `vector:`) never identify a
concept, so they must not pass as a concept `@id` either.

Run: ``python -m pytest scripts/test_concept_id_pattern.py -q`` from the repo root.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
MIF_SCHEMA = json.loads((ROOT / "schema" / "mif.schema.json").read_text())

BASE = {
    "@context": "https://mif-spec.dev/schema/context.jsonld",
    "@type": "Concept",
    "conceptType": "semantic",
    "content": "User prefers dark mode.",
    "created": "2026-01-15T10:30:00Z",
}


def _errors(concept_id: str) -> list[str]:
    validator = jsonschema.Draft202012Validator(MIF_SCHEMA)
    return [e.message for e in validator.iter_errors({**BASE, "@id": concept_id})]


@pytest.mark.parametrize("concept_id", [
    "urn:mif:550e8400-e29b-41d4-a716-446655440000",
    "urn:mif:550E8400-E29B-41D4-A716-446655440000",
    "urn:mif:fc22f3bc-9415-57af-966a-592a0e626acd",  # uuid5, as migrate_0_1_to_1_0.py derives
])
def test_uuid_concept_id_is_valid(concept_id):
    assert _errors(concept_id) == []


@pytest.mark.parametrize("concept_id", [
    "urn:mif:decision-react-over-vue",
    "urn:mif:mem0_123",
    "urn:mif:550e8400",
    "urn:mif:550e8400-e29b-41d4-a716-446655440000-extra",
    "urn:mif:entity:person:jane-doe",
    "urn:mif:vector:550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440000",
])
def test_non_uuid_concept_id_is_rejected(concept_id):
    assert _errors(concept_id), f"{concept_id!r} should not validate as a concept @id"
