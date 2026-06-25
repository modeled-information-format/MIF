#!/usr/bin/env python3
"""Tests for the temporal-consistency check, the first-class scalar ``properties``
construct, and the no-field-clobber guarantee across the full conversion chain.

Run: ``python -m pytest scripts/test_temporal_and_properties.py -q`` from the repo root.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

import mif_convert
import okf_validate

ROOT = Path(__file__).resolve().parent.parent
TEMPORAL = ROOT / "test" / "temporal"
PROPERTIES = ROOT / "test" / "properties"


# --------------------------------------------------------------------------- #
# Temporal consistency (Q-a: derived-from + supersedes + cites; Q-b: WARN,     #
# promotable to ERROR via --strict-temporal).                                  #
# --------------------------------------------------------------------------- #
def test_temporal_violation_is_warning_by_default():
    errors, warnings, count = okf_validate.validate_bundle(TEMPORAL / "bad")
    assert count == 2
    assert errors == []  # non-blocking by default — must not fail the run
    temporal = [w for w in warnings if "temporal inconsistency" in w]
    assert len(temporal) == 1
    assert "derived-from" in temporal[0]


def test_temporal_violation_promotes_to_error_in_strict_mode():
    errors, warnings, _ = okf_validate.validate_bundle(
        TEMPORAL / "bad", strict_temporal=True
    )
    temporal = [e for e in errors if "temporal inconsistency" in e]
    assert len(temporal) == 1
    assert [w for w in warnings if "temporal inconsistency" in w] == []


def test_temporal_consistent_derivation_has_no_finding():
    errors, warnings, count = okf_validate.validate_bundle(TEMPORAL / "good")
    assert count == 2
    assert errors == []
    assert [w for w in warnings if "temporal inconsistency" in w] == []


def test_non_derivation_edge_is_not_temporally_checked():
    # A "relates-to" edge to a newer target is fine — only derivation edges order time.
    fm = {
        "created": "2025-01-01T00:00:00Z",
        "relationships": [{"type": "relates-to", "target": "/session.md"}],
    }
    findings = okf_validate._temporal_findings(
        fm, TEMPORAL / "bad" / "observation.md", TEMPORAL / "bad", "x"
    )
    assert findings == []


def test_missing_created_skips_check_no_false_positive():
    fm = {"relationships": [{"type": "derived-from", "target": "/session.md"}]}
    findings = okf_validate._temporal_findings(
        fm, TEMPORAL / "bad" / "observation.md", TEMPORAL / "bad", "x"
    )
    assert findings == []


# --------------------------------------------------------------------------- #
# First-class scalar ``properties``.                                           #
# --------------------------------------------------------------------------- #
def test_properties_roundtrips_losslessly():
    assert mif_convert.roundtrip_file(PROPERTIES / "concept.md") is None


def test_properties_survive_md_to_jsonld_and_back():
    fm, body = mif_convert.parse_markdown((PROPERTIES / "concept.md").read_text())
    jsonld = json.loads(json.dumps(mif_convert.md_to_jsonld(fm, body)))
    assert jsonld["properties"] == {
        "status": "active",
        "priority": 1,
        "archived": False,
        "retired_on": None,
    }
    fm2, _ = mif_convert.jsonld_to_md(jsonld)
    assert fm2["properties"] == fm["properties"]


def _properties_subschema() -> dict:
    schema = json.loads((ROOT / "schema" / "mif.schema.json").read_text())
    return schema["properties"]["properties"]


def test_schema_accepts_scalar_properties():
    jsonschema.Draft202012Validator(_properties_subschema()).validate(
        {"status": "active", "priority": 1, "archived": False, "retired_on": None}
    )


@pytest.mark.parametrize("bad", [{"nested": {"a": 1}}, {"list": [1, 2]}])
def test_schema_rejects_non_scalar_properties(bad):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(_properties_subschema()).validate(bad)


# --------------------------------------------------------------------------- #
# No MIF field is clobbered across MIF -> OKF(JSON-LD) -> MIF -> JSON* -> MIF.  #
# --------------------------------------------------------------------------- #
FULL_FRONTMATTER = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "semantic",
    "created": "2026-01-15T10:30:00Z",
    "modified": "2026-02-01T08:00:00Z",
    "namespace": "_semantic/observations",
    "title": "Every-field concept",
    "summary": "A concept exercising every top-level frontmatter field.",
    "properties": {"status": "active", "priority": 1, "archived": False, "retired_on": None},
    "tags": ["a", "b"],
    "aliases": ["alt-name"],
    "temporal": {"validFrom": "2026-01-01T00:00:00Z", "validUntil": None},
    "provenance": {"sourceType": "agent_inferred", "confidence": 0.9},
    "embedding": {"model": "text-embed", "dimensions": 8},
    "relationships": [{"type": "derived-from", "target": "/other.md", "strength": 0.8}],
    "citations": [{"title": "Ref", "url": "https://example.com/x"}],
    "entities": [{"name": "Alice"}],
    "ontology": {"id": "mif-base", "version": "1.0.0"},
    "entity": {"name": "Alice Chen", "entity_type": "person"},
    "blocks": {"b1": "block text"},
    "extensions": {"vendor": {"k": "v"}},
}


def test_no_field_clobbered_across_full_conversion_chain():
    body = "Body content for the every-field concept."
    # MIF -> OKF (JSON-LD projection)
    jsonld = mif_convert.md_to_jsonld(FULL_FRONTMATTER, body)
    # Every MIF source field must be carried into the OKF projection (no drop/clobber).
    for key, value in FULL_FRONTMATTER.items():
        if key == "id":
            assert jsonld["@id"] == f"urn:mif:{value}"
        elif key == "type":
            assert jsonld["conceptType"] == value
        else:
            assert jsonld[key] == value, f"OKF projection clobbered {key!r}"
    # OKF -> MIF
    fm1, body1 = mif_convert.jsonld_to_md(jsonld)
    # MIF -> JSON* (serialize) -> MIF (the on-disk markdown round)
    md = mif_convert.serialize_markdown(fm1, body1)
    fm2, body2 = mif_convert.parse_markdown(md)
    # Final MIF frontmatter must equal the original, field for field.
    assert fm2 == FULL_FRONTMATTER
    for key in FULL_FRONTMATTER:
        assert fm2[key] == FULL_FRONTMATTER[key], f"chain clobbered {key!r}"
    assert body2.strip() == body.strip()
