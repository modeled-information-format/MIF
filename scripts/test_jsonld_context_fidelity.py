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
- `documentType`, `citationType`, `citationRole`, `conceptType`, `memoryType`,
  `sourceType`, `trustLevel` (`@type: @vocab` with no `@vocab` default and no
  registered terms for their enum): unrecognized values fall back to
  document-base-relative IRI resolution, so the same value expands to a
  different, non-equal IRI depending on the document's base URL. Fixed by
  registering each property's enum values as a term-scoped `mif:`-namespaced
  term (a nested `@context` on the property's own term definition),
  mirroring the existing `documents.hash`/`relationships` scoped-context
  pattern already in this file.

  An earlier version of `documentType`'s fix registered its 13 terms at the
  TOP LEVEL of the shared context instead of scoping them to `documentType`.
  JSON-LD `@type:@vocab` resolution checks the whole active context, not
  just the property being expanded, so that flat registration silently
  redirected `Citation.citationType` values that happen to share a name with
  a `documentType` enum value (`video`, `dataset`, `other` are valid values
  of both fields) to the wrong `mif:DocumentType*` IRI. Scoping every one of
  these properties' terms to its own `@context` keeps them from
  contaminating each other despite the overlapping enum values.

`scripts/check_vocab_term_coverage.py` is this file's sibling: it statically
proves every enum value has a matching registered term (and that no stale
extra term exists), for ANY current or future `@type:@vocab` property, by
cross-referencing `schema/context.jsonld` against `schema/mif.schema.json`.
This file proves the registered terms actually behave correctly under a real
JSON-LD 1.1 processor -- static presence and runtime semantics are two
different failure modes, so both checks are needed.

- `relationships[].type` (`@type: @vocab`, nested inside the `relationships`
  container's own scoped `@context`): registered the SPECIFICATION.md 8.2
  "Core Relationship Types" under their PascalCase display names
  (`RelatesTo`, `DerivedFrom`, ...) as term KEYS, but `Relationship.type`'s
  actual schema constraint is a free-form lowercase-kebab-case pattern (e.g.
  `derived-from`), and real documents use exactly that kebab-case form.
  JSON-LD term lookup is exact-string-match, so no schema-valid value ever
  matched a registered term -- unlike `documentType`/`citationType`/etc,
  this wasn't a MISSING registration, it was a registration under the wrong
  key entirely, silently doing nothing for every real document. The
  `relationships` container's own ambient `@vocab` default masked the
  symptom: unregistered values still resolved to a stable-looking `mif:`
  IRI (base-URI-independent, unlike the documentType/citationType bugs),
  so this looked fine at a glance -- the real loss was landing on the
  wrong IRI, `mif:derived-from` instead of the documented, ontology-
  registered `mif:DerivedFrom`. Fixed by re-keying the scoped `@context`
  to the real kebab-case values, mapped to the existing `mif:`-namespaced
  PascalCase IRIs already published in `public/ns/vocabulary.jsonld`.
"""
import json
import sys
from pathlib import Path

from pyld import jsonld

ROOT = Path(__file__).parent.parent
CONTEXT = json.loads((ROOT / "schema" / "context.jsonld").read_text())["@context"]

# (prop, node_type, extra_fields) for every term-scoped @type:@vocab property
# this file exercises. Single source of truth: adding another such property
# means adding one row here, not touching N call sites. sourceType/trustLevel
# are schema-nested under Provenance in practice, but "provenance" is a bare
# string term (no nested @context of its own), so it introduces no new
# resolution scope -- testing them as direct Memory properties here exercises
# the identical term-resolution mechanics as their real nested usage.
VOCAB_PROPERTIES = [
    ("documentType", "DocumentReference", {"url": "https://example.com/doc"}),
    ("citationType", "Citation", {}),
    ("citationRole", "Citation", {}),
    ("conceptType", "Memory", {}),
    ("memoryType", "Memory", {}),
    ("sourceType", "Memory", {}),
    ("trustLevel", "Memory", {}),
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


def _expanded_vocab_id(expanded: list, prop: str, value: str) -> str | None:
    prop_iri = f"https://mif-spec.dev/ns/{prop}"
    try:
        return expanded[0][prop_iri][0]["@id"]
    except (IndexError, KeyError, TypeError) as e:
        # Deliberately base-label-agnostic: two identically-malformed expansions
        # across different base URLs must produce the SAME placeholder, or the
        # base-independence check below would misdiagnose them as "base-URI-
        # dependent" (iri_a != iri_b) instead of "malformed expansion".
        return f"<malformed expansion for {prop}={value!r}: {e!r}>"


def check_vocab_base_independence() -> list[str]:
    errors = []
    for prop, node_type, extra_fields in VOCAB_PROPERTIES:
        for value in VOCAB_VALUES[prop]:
            doc = {"@context": CONTEXT, "@type": node_type, **extra_fields, prop: value}
            expanded_a = jsonld.expand(doc, {"base": "https://host-a.example/"})
            expanded_b = jsonld.expand(doc, {"base": "https://host-b.example/"})
            iri_a = _expanded_vocab_id(expanded_a, prop, value)
            iri_b = _expanded_vocab_id(expanded_b, prop, value)
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


# SPECIFICATION.md 8.2 "Core Relationship Types" -- kebab-case value (the
# schema-valid, real-world form) mapped to the documented ontology IRI's
# local name (published in public/ns/vocabulary.jsonld).
RELATIONSHIP_TYPES = {
    "relates-to": "RelatesTo",
    "derived-from": "DerivedFrom",
    "supersedes": "Supersedes",
    "conflicts-with": "ConflictsWith",
    "part-of": "PartOf",
    "implements": "Implements",
    "uses": "Uses",
    "created": "Created",
    "mentioned-in": "MentionedIn",
}


def _compacted_relationship_field(compacted: dict, field: str) -> object:
    """compacted["relationships"][0].get(field), tolerant of a context
    regression that drops or reshapes `relationships` during compaction
    (an empty/missing list, or a non-dict first element) -- returns a
    descriptive placeholder instead of raising, so callers can report a
    clear test failure rather than crashing the whole run."""
    try:
        return compacted["relationships"][0].get(field)
    except (IndexError, KeyError, TypeError) as e:
        return f"<malformed compaction reaching relationships[0].{field}: {e!r}>"


def check_relationship_type_resolves_to_documented_ontology_iri() -> list[str]:
    errors = []
    for kebab, pascal in RELATIONSHIP_TYPES.items():
        doc = {
            "@context": CONTEXT, "@type": "Memory", "@id": "urn:mif:test", "conceptType": "semantic",
            "relationships": [{"type": kebab, "target": "/foo.md"}],
        }
        expanded_a = jsonld.expand(doc, {"base": "https://host-a.example/"})
        expanded_b = jsonld.expand(doc, {"base": "https://host-b.example/"})
        try:
            iri_a = expanded_a[0]["https://mif-spec.dev/ns/relationships"][0]["https://mif-spec.dev/ns/relationshipType"][0]["@id"]
            iri_b = expanded_b[0]["https://mif-spec.dev/ns/relationships"][0]["https://mif-spec.dev/ns/relationshipType"][0]["@id"]
        except (IndexError, KeyError, TypeError) as e:
            errors.append(f"relationships[].type={kebab!r}: malformed expansion: {e!r}")
            continue
        expected = f"https://mif-spec.dev/ns/{pascal}"
        if iri_a != iri_b:
            errors.append(f"relationships[].type={kebab!r} is base-URI-dependent: {iri_a!r} != {iri_b!r}")
        elif iri_a != expected:
            errors.append(f"relationships[].type={kebab!r} resolved to {iri_a!r}, want documented ontology IRI {expected!r}")
        compacted = _compact(expanded_a, CONTEXT)
        round_tripped = _compacted_relationship_field(compacted, "type")
        if round_tripped != kebab:
            errors.append(f"relationships[].type={kebab!r} did not round-trip: got {round_tripped!r}")
    return errors


def check_relationship_type_custom_namespace_still_works() -> list[str]:
    errors = []
    doc = {
        "@context": CONTEXT, "@type": "Memory", "@id": "urn:mif:test", "conceptType": "semantic",
        "relationships": [{"type": "subcog:custom-rel", "target": "/foo.md"}],
    }
    compacted = _compact(jsonld.expand(doc), CONTEXT)
    round_tripped = _compacted_relationship_field(compacted, "type")
    if round_tripped != "subcog:custom-rel":
        errors.append(f"custom-namespaced relationships[].type regressed: got {round_tripped!r}")
    return errors


def check_strength_shared_by_relationship_and_decay() -> list[str]:
    """`strength` is a plain (non-@vocab) xsd:decimal term shared by two
    unrelated schema objects: Relationship.strength (relationships[].strength)
    and TemporalMetadata.decay.strength ("alias for currentStrength"). It must
    stay a single, shared top-level term -- an earlier version of this fix
    moved it into relationships[]'s own scoped @context exclusively, which
    silently dropped decay.strength from expansion entirely (no error), since
    that scope is inaccessible outside the relationships array. Confirmed
    against a real fixture (profiles/ai-memory/examples/level-3-citations.md's
    `decay: {model: none, strength: 1.0}`) before this test existed."""
    errors = []
    doc = {
        "@context": CONTEXT, "@type": "Memory", "@id": "urn:mif:test", "conceptType": "semantic",
        "temporal": {"decay": {"model": "none", "currentStrength": 0.8, "strength": 1.0}},
        "relationships": [{"type": "derived-from", "target": "/foo.md", "strength": 0.9}],
    }
    expanded = jsonld.expand(doc)
    try:
        decay = expanded[0]["https://mif-spec.dev/ns/temporal"][0]["https://mif-spec.dev/ns/decay"][0]
    except (IndexError, KeyError, TypeError) as e:
        errors.append(f"malformed expansion reaching temporal.decay: {e!r}")
        return errors
    if "https://mif-spec.dev/ns/strength" not in decay:
        errors.append("temporal.decay.strength was dropped from expansion entirely (no error) -- decay: " + repr(decay))
    try:
        rel_strength = expanded[0]["https://mif-spec.dev/ns/relationships"][0]["https://mif-spec.dev/ns/strength"]
    except (IndexError, KeyError, TypeError) as e:
        errors.append(f"malformed expansion reaching relationships[].strength: {e!r}")
        return errors
    if not rel_strength:
        errors.append("relationships[].strength was dropped from expansion entirely (no error)")
    compacted = _compact(expanded, CONTEXT)
    if compacted.get("temporal", {}).get("decay", {}).get("strength") != 1.0:
        errors.append(f"temporal.decay.strength did not round-trip: got {compacted.get('temporal', {}).get('decay', {})!r}")
    if compacted.get("relationships", [{}])[0].get("strength") != 0.9:
        errors.append(f"relationships[].strength did not round-trip: got {compacted.get('relationships', [{}])[0]!r}")
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
        iri_a = _expanded_vocab_id(jsonld.expand(doc_a), "documentType", value)
        if iri_a is not None and "CitationType" in iri_a:
            errors.append(f"documentType={value!r} contaminated by citationType terms: {iri_a}")
        doc_b = {"@context": CONTEXT, "@type": "Citation", "citationType": value}
        iri_b = _expanded_vocab_id(jsonld.expand(doc_b), "citationType", value)
        if iri_b is not None and "DocumentType" in iri_b:
            errors.append(f"citationType={value!r} contaminated by documentType terms: {iri_b}")
    return errors


CHECKS = [
    ("extensions round-trips losslessly through @type:@json (#224)", check_extensions_round_trip),
    ("every scoped vocab property is base-URI-independent for all enum values (#225, #226, #228)", check_vocab_base_independence),
    ("every scoped vocab property's custom-namespaced escape hatch still resolves", check_vocab_custom_namespace_still_works),
    ("documentType and citationType don't contaminate each other's shared enum values", check_document_type_citation_type_no_cross_contamination),
    ("relationships[].type resolves to its documented ontology IRI, not mif:<kebab-value> (#230)", check_relationship_type_resolves_to_documented_ontology_iri),
    ("relationships[].type custom-namespaced escape hatch still resolves", check_relationship_type_custom_namespace_still_works),
    ("strength stays shared by relationships[].strength and temporal.decay.strength", check_strength_shared_by_relationship_and_decay),
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
