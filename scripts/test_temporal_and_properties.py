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
    # No unrelated errors should appear in the bad bundle (scope the assertion).
    assert [e for e in errors if "temporal inconsistency" not in e] == []
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


def _bundle_with_target(tmp_path, target_created):
    """A bundle whose /target.md carries ``target_created`` (or no created if None)."""
    fm = "" if target_created is None else f"created: {target_created}\n"
    (tmp_path / "target.md").write_text(
        f"---\nid: t\ntype: semantic\n{fm}---\nbody\n"
    )
    return tmp_path


def _findings_for(tmp_path, rel_type, source_created, target_created):
    bundle = _bundle_with_target(tmp_path, target_created)
    fm = {
        "created": source_created,
        "relationships": [{"type": rel_type, "target": "/target.md"}],
    }
    return okf_validate._temporal_findings(fm, bundle / "src.md", bundle, "src")


@pytest.mark.parametrize("rel_type", ["derived-from", "supersedes", "cites"])
def test_all_derivation_types_flag_future_target(tmp_path, rel_type):
    # Every member of DERIVATION_TYPES must be temporally checked, not just derived-from.
    findings = _findings_for(
        tmp_path, rel_type, "2025-01-01T00:00:00Z", "2026-01-01T00:00:00Z"
    )
    assert len(findings) == 1
    assert rel_type in findings[0]


def test_equal_timestamps_is_not_a_violation(tmp_path):
    # Boundary: target created exactly at source time is "not after" -> no finding.
    ts = "2026-01-01T00:00:00Z"
    assert _findings_for(tmp_path, "derived-from", ts, ts) == []


def test_date_only_same_day_is_not_a_false_positive(tmp_path):
    # Date-only source vs same-day finer-grained target must not flag (no midnight bias).
    findings = _findings_for(
        tmp_path, "derived-from", "2024-06-01", "2024-06-01T09:00:00Z"
    )
    assert findings == []


def test_date_only_next_day_target_is_flagged(tmp_path):
    findings = _findings_for(
        tmp_path, "derived-from", "2024-06-01", "2024-06-02T00:00:00Z"
    )
    assert len(findings) == 1


def test_naive_source_datetime_does_not_raise(tmp_path):
    # Naive (no tz) source is normalized to UTC; aware-vs-naive comparison must not raise.
    findings = _findings_for(
        tmp_path, "derived-from", "2025-01-15T10:30:00", "2026-01-01T00:00:00Z"
    )
    assert len(findings) == 1


def test_target_missing_created_skips_no_false_positive(tmp_path):
    assert _findings_for(tmp_path, "derived-from", "2025-01-01T00:00:00Z", None) == []


def test_malformed_yaml_target_is_skipped_not_crash(tmp_path):
    # A derivation target with malformed YAML frontmatter must be skipped, never crash
    # the run (the function's documented "unparseable -> skip" contract).
    (tmp_path / "target.md").write_text("---\n bad: : : yaml\n :::\n---\nbody\n")
    fm = {
        "created": "2025-01-01T00:00:00Z",
        "relationships": [{"type": "derived-from", "target": "/target.md"}],
    }
    assert okf_validate._temporal_findings(fm, tmp_path / "src.md", tmp_path, "x") == []


def test_multiple_future_targets_all_reported(tmp_path):
    # Two future-target derivation edges -> two findings (guards an early-break regression).
    (tmp_path / "a.md").write_text(
        "---\nid: a\ntype: semantic\ncreated: 2026-01-01T00:00:00Z\n---\nbody\n"
    )
    (tmp_path / "b.md").write_text(
        "---\nid: b\ntype: semantic\ncreated: 2026-06-01T00:00:00Z\n---\nbody\n"
    )
    fm = {
        "created": "2025-01-01T00:00:00Z",
        "relationships": [
            {"type": "derived-from", "target": "/a.md"},
            {"type": "supersedes", "target": "/b.md"},
        ],
    }
    findings = okf_validate._temporal_findings(fm, tmp_path / "src.md", tmp_path, "x")
    assert len(findings) == 2


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
    "memoryType": "semantic",
    "created": "2026-01-15T10:30:00Z",
    "modified": "2026-02-01T08:00:00Z",
    "namespace": "_semantic/observations",
    "title": "Every-field concept",
    "summary": "A concept exercising every top-level frontmatter field.",
    # Scalar property values that YAML would re-type on reparse if left unquoted
    # ("true"/"null"/date-/number-like strings) — pins the quoting guarantee.
    "properties": {
        "status": "active",
        "priority": 1,
        "archived": False,
        "retired_on": None,
        "flag_str": "true",
        "void_str": "null",
        "when_str": "2026-01-01",
        "ratio_str": "1.5",
    },
    "compressedAt": "2026-02-01T08:00:00Z",
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

# JSON-LD keys produced by the projection itself (not 1:1 source frontmatter
# fields); excluded when asserting that every schema-defined source field survives.
_PROJECTION_ONLY_KEYS = {
    "@context",
    "@type",
    "@id",
    "conceptType",
    "timestamp",
    "description",
    "content",
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
    # MIF -> JSON* : actually serialize through JSON, as an on-disk projection would.
    jsonld = json.loads(json.dumps(jsonld))
    # OKF -> MIF
    fm1, body1 = mif_convert.jsonld_to_md(jsonld)
    # MIF -> serialized markdown -> MIF (the on-disk markdown round)
    md = mif_convert.serialize_markdown(fm1, body1)
    fm2, body2 = mif_convert.parse_markdown(md)
    # Final MIF frontmatter must equal the original, field for field.
    assert fm2 == FULL_FRONTMATTER
    for key in FULL_FRONTMATTER:
        assert fm2[key] == FULL_FRONTMATTER[key], f"chain clobbered {key!r}"
    assert body2.strip() == body.strip()


def test_every_schema_source_field_survives_round_trip():
    """Regression guard: every top-level schema property that is a source field
    (not a projection-only key) must be present in FULL_FRONTMATTER and survive
    the full chain. A new schema field that is forgotten in the converter's
    passthrough lists fails here instead of silently dropping."""
    schema = json.loads((ROOT / "schema" / "mif.schema.json").read_text())
    source_fields = set(schema["properties"]) - _PROJECTION_ONLY_KEYS
    # memoryType maps to the same `type`/conceptType slot; one stands in for both.
    covered = set(FULL_FRONTMATTER)
    missing = source_fields - covered
    assert not missing, f"schema source field(s) not exercised by the chain: {missing}"
    jsonld = json.loads(json.dumps(mif_convert.md_to_jsonld(FULL_FRONTMATTER, "b")))
    fm2, _ = mif_convert.jsonld_to_md(jsonld)
    for field in source_fields:
        if field == "type":  # surfaced as conceptType, recovered as type
            assert fm2["type"] == FULL_FRONTMATTER["type"]
        else:
            assert fm2.get(field) == FULL_FRONTMATTER[field], f"dropped {field!r}"
