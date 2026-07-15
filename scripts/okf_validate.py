#!/usr/bin/env python3
"""OKF conformance validator for MIF v1.0 bundles.

Implements the conformance test pinned in ``docs/okf-conformance.md`` (spec
section 7). A *bundle* is a directory tree of ``.md`` concept files. For every
concept the validator enforces:

1. the file has YAML frontmatter containing a ``type`` field;
2. no concept document uses a reserved filename (``index.md`` / ``log.md``);
3. every frontmatter ``relationships`` entry has a corresponding body markdown
   link in a ``## Relationships`` section, and every such body link maps back to
   a frontmatter entry (Invariant 3, section 4.4 synchronization);
4. broken bundle-relative links are tolerated -- reported as warnings, never
   failures (OKF tolerates broken links);
5. the ``markdown -> json-ld -> markdown`` projection round-trips losslessly
   (delegated to ``mif_convert.roundtrip_file``);
6. derivation edges are temporally consistent -- a ``derived-from`` / ``supersedes``
   / ``cites`` target must not be ``created`` after the concept that derives from
   it. Reported as a warning by default (non-blocking); ``--strict-temporal``
   promotes it to a hard error so a known-clean corpus can enforce it in CI.
7. every namespaced (custom) relationship type used in the bundle is declared
   in ``.mif/config.yaml``'s ``relationship_types`` (SPECIFICATION.md 8.1/8.3),
   once a bundle has that file -- opt-in: bundles without ``.mif/config.yaml``
   keep the fully-lenient behavior of (5)/(6) unchanged. Bare/core types (no
   ``namespace:`` prefix) are never gated by this check.
8. a declared custom type's relationship metadata values conform to that
   type's declared ``properties[]`` (type/enum/range), when present -- e.g. a
   property declared ``range: [0.0, 1.0]`` rejects a metadata value of ``5.0``.
   A declared property absent from a given relationship's metadata is not an
   error (properties are optional-when-present, not required). ``inverse`` and
   ``symmetric`` are declaration-only and not enforced by this validator (they
   describe a cross-relationship graph shape, not a single relationship's own
   values); a relationship whose type declares them is never checked for a
   matching reciprocal edge.

Exit code 0 means every concept in every bundle conforms.

Usage::

    python okf_validate.py <bundle-dir> [bundle-dir ...] [--strict-temporal]
    python okf_validate.py            # defaults to examples/ + profiles/*/examples/
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import yaml  # PyYAML; parse_markdown's safe_load can raise yaml.YAMLError

import mif_convert  # local module (same scripts/ directory)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Relationship types whose target is a *prior* concept the source is built on:
# the target must not be created AFTER the source. (Q-a: derived-from + supersedes
# + cites.) Stored kebab-normalized to match _kebab() output.
DERIVATION_TYPES = {"derived-from", "supersedes", "cites"}

# A body relationship line: "- <kebab-type> [Text](/path/to/target.md)".
# <kebab-type> allows an optional "namespace:" prefix (schema/mif.schema.json's
# Relationship.type pattern), so a custom relationship type's hand-written body
# mirror (e.g. "farm:breeds-with") is recognized -- without this, item (3)'s
# sync check could never match any custom-typed relationship's body link,
# since it would never be extracted here in the first place.
REL_LINE_RE = re.compile(r"^-\s+([a-z0-9][a-z0-9-]*(?::[a-z0-9][a-z0-9-]*)?)\s+\[[^\]]+\]\(([^)]+)\)\s*$")
# Any markdown link, for broken-link scanning.
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _kebab(value: str) -> str:
    """Normalize a relationship type token to kebab-case for comparison.

    A leading namespace prefix (``farm:BreedsWith``) must not grow a spurious
    hyphen right after the colon -- ``(?<!:)`` treats ':' as a word boundary
    the same way ``(?<!^)`` already treats the start of the string.
    """
    value = re.sub(r"(?<!^)(?<!:)(?=[A-Z])", "-", value)
    value = re.sub(r"[\s_]+", "-", value)
    return value.lower()


def _relationships_section(body: str) -> list[tuple[str, str]]:
    """Extract (kebab-type, target) pairs from the body ## Relationships section."""
    pairs: list[tuple[str, str]] = []
    in_section = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped[3:].strip().lower() == "relationships"
            continue
        if in_section:
            match = REL_LINE_RE.match(stripped)
            if match:
                pairs.append((_kebab(match.group(1)), match.group(2)))
    return pairs


def _frontmatter_relationships(frontmatter: dict) -> list[tuple[str, str]]:
    """Extract (kebab-type, target) pairs from frontmatter relationships array."""
    pairs: list[tuple[str, str]] = []
    for rel in frontmatter.get("relationships", []) or []:
        if not isinstance(rel, dict):
            continue
        rel_type = rel.get("type") or rel.get("relationshipType") or ""
        target = rel.get("target", "")
        if isinstance(target, dict):  # tolerate {"@id": ...}/{"path": ...}
            target = target.get("path") or target.get("@id", "")
        pairs.append((_kebab(str(rel_type)), str(target)))
    return pairs


RELATIONSHIP_TYPES_CONFIG_SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "relationship-types-config.schema.json").read_text()
)


def _validate_relationship_types_config_shape(config) -> list[str]:
    """Structural validation of a parsed .mif/config.yaml, delegated to
    schema/relationship-types-config.schema.json itself via jsonschema
    (the same pattern scripts/test_temporal_and_properties.py already uses
    against schema/mif.schema.json) rather than a hand-rolled duplicate of
    the schema's own constraints -- a hand-rolled version drifts silently
    (an earlier version of this function reproduced the 'name'/'namespace'
    patterns and the properties[].type enum by hand, but never enforced
    additionalProperties:false or the properties[].enum/range constraints,
    since nothing forced the two to stay in sync). A FormatChecker is required
    explicitly -- without it (and without the rfc3987 package it depends on
    for "uri") jsonschema's "format" keyword is a silent no-op, so
    namespaces.*'s format:uri constraint would never actually reject a
    malformed IRI."""
    validator = jsonschema.Draft202012Validator(
        RELATIONSHIP_TYPES_CONFIG_SCHEMA, format_checker=jsonschema.FormatChecker()
    )
    errors = []
    for err in validator.iter_errors(config):
        path = "".join(f"[{p!r}]" if isinstance(p, int) else f".{p}" for p in err.absolute_path)
        errors.append(f"config.yaml{path}: {err.message}")
    return errors


def _load_relationship_types_config(bundle: Path) -> tuple[dict | None, list[str]]:
    """Load bundle/.mif/config.yaml if present. Returns (config, errors);
    config is None when no such file exists (today's lenient behavior is
    unchanged for bundles that haven't opted in)."""
    config_path = bundle / ".mif" / "config.yaml"
    try:
        text = config_path.read_text()
    except FileNotFoundError:
        return None, []
    except OSError as exc:
        return None, [f"{config_path}: could not be read: {exc}"]
    try:
        config = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [f"{config_path}: invalid YAML: {exc}"]
    shape_errors = _validate_relationship_types_config_shape(config)
    if shape_errors:
        return None, shape_errors
    return config, []


def _custom_relationship_type_registry(config: dict) -> tuple[dict[str, dict], list[str]]:
    """Map 'namespace:kebab-name' -> declaration, for every namespaced
    (custom) entry in a validated relationship_types config. Returns
    (registry, errors); a repeated namespace+name pair is a config error
    (last-declaration-wins would otherwise silently discard the earlier one
    with no diagnostic)."""
    registry: dict[str, dict] = {}
    errors: list[str] = []
    for entry in config.get("relationship_types", []):
        namespace = entry.get("namespace")
        if not namespace:
            continue
        key = f"{namespace}:{_kebab(entry['name'])}"
        if key in registry:
            errors.append(
                f"config.yaml relationship_types: '{namespace}' + '{entry['name']}' "
                f"is declared more than once (resolves to '{key}')"
            )
        registry[key] = entry
    return registry, errors


def _check_property_type(value: object, expected_type: str) -> tuple[bool, str]:
    """True (and empty message) when value's runtime type/format matches a
    RelationshipTypePropertyDeclaration's `type` (schema/
    relationship-types-config.schema.json). ``bool`` is deliberately excluded
    from integer/decimal -- Python's bool is an int subclass, and a
    declaration of `type: integer` should reject a stray `true`/`false`."""
    if expected_type == "string":
        ok = isinstance(value, str)
    elif expected_type == "boolean":
        ok = isinstance(value, bool)
    elif expected_type == "integer":
        ok = isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "decimal":
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "date":
        ok = isinstance(value, str) and _is_date_only(value) and _parse_created(value) is not None
    elif expected_type == "datetime":
        ok = isinstance(value, str) and not _is_date_only(value) and _parse_created(value) is not None
    else:  # unreachable given the schema's own enum on `type`; never crash.
        ok = True
    return (True, "") if ok else (False, f"expected type '{expected_type}', got {value!r}")


def _relationship_metadata_errors(entry: dict, metadata: object) -> list[str]:
    """Check a relationship's metadata values against its declared custom
    type's `properties[]` (type/enum/range) -- SPECIFICATION.md 8.1/8.3's own
    worked example (`range: [0.0, 1.0]`, `enum: [direct, indirect, partial]`)
    presents these as real constraints, not just declaration shape. A
    declared property absent from this relationship's metadata is not
    flagged here -- properties are not required-if-declared, only checked
    when present."""
    if not isinstance(metadata, dict):
        return []
    namespace = entry.get("namespace")
    errors: list[str] = []
    for prop in entry.get("properties", []) or []:
        key = f"{namespace}:{prop.get('name')}"
        if key not in metadata:
            continue
        value = metadata[key]
        expected_type = prop.get("type")
        type_ok, type_msg = _check_property_type(value, expected_type)
        if not type_ok:
            errors.append(f"metadata['{key}']: {type_msg}")
            continue  # enum/range against a wrong-typed value would be noise

        # `enum` only applies to `type: string`, `range` only to `type:
        # integer`/`decimal` (schema's own field descriptions) -- a
        # misdeclared config (e.g. `range` on a `type: string` property) must
        # never reach `lo <= value <= hi` with a non-numeric value and crash.
        enum_values = prop.get("enum")
        if expected_type == "string" and enum_values is not None and value not in enum_values:
            errors.append(
                f"metadata['{key}']: {value!r} is not one of the declared "
                f"enum values {enum_values}"
            )
        range_bounds = prop.get("range")
        if expected_type in ("integer", "decimal") and range_bounds is not None:
            lo, hi = range_bounds
            if not (lo <= value <= hi):
                errors.append(
                    f"metadata['{key}']: {value!r} is outside the declared "
                    f"range [{lo}, {hi}]"
                )
    return errors


def _resolve(target: str, md_path: Path, bundle: Path) -> Path | None:
    """Resolve a bundle-relative or document-relative link target to a path."""
    target = target.split("#", 1)[0]
    if not target or target.startswith(("http://", "https://", "urn:", "mailto:")):
        return None
    if target.startswith("/"):
        return bundle / target.lstrip("/")
    return (md_path.parent / target).resolve()


def _parse_created(value: object) -> datetime | None:
    """Parse an ISO-8601 ``created`` value to an aware datetime (UTC if naive)."""
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _is_date_only(value: object) -> bool:
    """True when a ``created`` value carries no time-of-day (e.g. ``2024-06-01``)."""
    return isinstance(value, str) and "T" not in value and " " not in value.strip()


def _temporal_findings(
    frontmatter: dict, md_path: Path, bundle: Path, rel_name: object
) -> list[str]:
    """Findings where a derivation target is created AFTER the deriving concept.

    A ``derived-from`` / ``supersedes`` / ``cites`` edge asserts the target predates
    the source; a target with a later ``created`` is a logical impossibility the
    schema/round-trip checks cannot see. Targets that don't resolve to an existing
    in-bundle concept, or where either ``created`` is missing/unparseable, are
    skipped (no false positives).
    """
    findings: list[str] = []
    source_raw = frontmatter.get("created")
    source_created = _parse_created(source_raw)
    if source_created is None:
        return findings
    for rel_type, target in _frontmatter_relationships(frontmatter):
        if rel_type not in DERIVATION_TYPES:
            continue
        resolved = _resolve(target, md_path, bundle)
        if resolved is None or resolved.suffix != ".md" or not resolved.exists():
            continue
        # Stay inside the bundle: a target that escapes (e.g. ``../other.md``)
        # must not cause us to read an arbitrary file outside the bundle tree.
        if not resolved.resolve().is_relative_to(bundle.resolve()):
            continue
        if resolved.resolve() == md_path.resolve():
            continue
        try:
            tgt_fm, _ = mif_convert.parse_markdown(resolved.read_text())
        except (ValueError, OSError, yaml.YAMLError):
            continue
        target_raw = tgt_fm.get("created")
        target_created = _parse_created(target_raw)
        if target_created is None:
            continue
        # If either side is date-only, a finer-grained other side would otherwise
        # be compared against a manufactured midnight; downgrade both to date
        # granularity so a same-day derivation is not a false positive.
        if _is_date_only(source_raw) or _is_date_only(target_raw):
            if target_created.date() > source_created.date():
                findings.append(
                    f"{rel_name}: temporal inconsistency -> '{rel_type}' target "
                    f"{target} is created {target_raw}, after concept "
                    f"created {source_raw}"
                )
            continue
        if target_created > source_created:
            findings.append(
                f"{rel_name}: temporal inconsistency -> '{rel_type}' target "
                f"{target} is created {target_raw}, after concept "
                f"created {source_raw}"
            )
    return findings


def validate_bundle(
    bundle: Path, strict_temporal: bool = False
) -> tuple[list[str], list[str], int]:
    """Validate one bundle. Returns (errors, warnings, concept_count).

    ``strict_temporal`` promotes temporal-inconsistency findings from warnings to
    hard errors (exit 1). Default is WARN so the check never blocks real-world use
    until a corpus is known clean.
    """
    errors: list[str] = []
    warnings: list[str] = []
    count = 0

    # (7) opt-in custom relationship type registry (SPECIFICATION.md 8.1/8.3).
    # A bundle with no .mif/config.yaml keeps today's fully-lenient behavior --
    # this only activates once a bundle opts in by creating the file.
    rel_types_config, config_errors = _load_relationship_types_config(bundle)
    errors.extend(config_errors)
    if rel_types_config:
        custom_type_registry, registry_errors = _custom_relationship_type_registry(rel_types_config)
        errors.extend(registry_errors)
    else:
        custom_type_registry = {}

    for md_path in mif_convert.iter_concepts(bundle):
        count += 1
        try:
            rel_name = md_path.resolve().relative_to(REPO_ROOT)
        except ValueError:
            rel_name = md_path
        try:
            frontmatter, body = mif_convert.parse_markdown(md_path.read_text())
        except ValueError as exc:
            errors.append(f"{rel_name}: {exc}")
            continue

        # (1) frontmatter must carry a type field.
        if not frontmatter.get("type"):
            errors.append(f"{rel_name}: missing required frontmatter 'type'")

        # (3) relationship <-> body-link synchronization.
        fm_rels = sorted(_frontmatter_relationships(frontmatter))
        body_rels = sorted(_relationships_section(body))
        if fm_rels != body_rels:
            missing_body = [r for r in fm_rels if r not in body_rels]
            missing_fm = [r for r in body_rels if r not in fm_rels]
            detail = []
            if missing_body:
                detail.append(f"no body link for {missing_body}")
            if missing_fm:
                detail.append(f"no frontmatter entry for {missing_fm}")
            errors.append(f"{rel_name}: relationships out of sync ({'; '.join(detail)})")

        # (7) every namespaced (custom) relationship type must be declared in
        # .mif/config.yaml, once the bundle has one. Bare/core types (no ":")
        # are unaffected -- always allowed, matching today's behavior.
        # (8) once a type IS declared, its relationship's metadata values are
        # checked against that type's declared properties[] (type/enum/range).
        if rel_types_config is not None:
            for rel in frontmatter.get("relationships", []) or []:
                if not isinstance(rel, dict):
                    continue
                rel_type = _kebab(str(rel.get("type") or rel.get("relationshipType") or ""))
                if ":" not in rel_type:
                    continue
                entry = custom_type_registry.get(rel_type)
                if entry is None:
                    errors.append(
                        f"{rel_name}: relationship type '{rel_type}' is not declared in "
                        f".mif/config.yaml's relationship_types (bundle has opted in to "
                        f"custom-type validation by defining that file)"
                    )
                    continue
                for prop_err in _relationship_metadata_errors(entry, rel.get("metadata")):
                    errors.append(f"{rel_name}: relationship '{rel_type}' {prop_err}")

        # (4) broken links -> warnings only.
        for match in MD_LINK_RE.finditer(body):
            resolved = _resolve(match.group(1), md_path, bundle)
            if resolved is not None and resolved.suffix == ".md" and not resolved.exists():
                warnings.append(f"{rel_name}: broken link -> {match.group(1)}")

        # (5) lossless round-trip.
        rt_err = mif_convert.roundtrip_file(md_path)
        if rt_err:
            errors.append(f"{rel_name}: {rt_err}")

        # (6) temporal consistency of derivation edges (WARN unless --strict-temporal).
        temporal = _temporal_findings(frontmatter, md_path, bundle, rel_name)
        (errors if strict_temporal else warnings).extend(temporal)

    # (2) reserved-filename misuse is structural; rglob to catch any.
    for reserved in mif_convert.RESERVED_FILENAMES:
        for hit in bundle.rglob(reserved):
            # Reserved files are allowed to EXIST (index/log); they just must not
            # be treated as concepts. Presence alone is fine; nothing to flag.
            _ = hit

    return errors, warnings, count


def default_bundles() -> list[Path]:
    bundles = []
    examples = REPO_ROOT / "examples"
    if examples.exists():
        bundles.append(examples)
    for profile_examples in sorted((REPO_ROOT / "profiles").glob("*/examples")):
        bundles.append(profile_examples)
    return bundles


def main() -> None:
    args = sys.argv[1:]
    strict_temporal = False
    positional: list[str] = []
    for arg in args:
        if arg in ("--strict-temporal", "--temporal-strict"):
            strict_temporal = True
        else:
            positional.append(arg)
    bundles = [Path(a) for a in positional] if positional else default_bundles()
    if not bundles:
        print("No bundles found to validate.", file=sys.stderr)
        sys.exit(1)

    all_errors: list[str] = []
    all_warnings: list[str] = []
    total = 0
    for bundle in bundles:
        bundle = bundle.resolve()
        if not bundle.exists():
            all_errors.append(f"{bundle}: bundle directory not found")
            continue
        errors, warnings, count = validate_bundle(bundle, strict_temporal=strict_temporal)
        total += count
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        try:
            label = bundle.relative_to(REPO_ROOT)
        except ValueError:
            label = bundle
        print(f"  {label}: {count} concept(s)")

    for warning in all_warnings:
        print(f"WARN  {warning}")

    print(f"\nOKF conformance: checked {total} concept(s) in {len(bundles)} bundle(s)")
    if all_errors:
        print(f"FAILED with {len(all_errors)} error(s):")
        for error in all_errors:
            print(f"  ERROR {error}")
        sys.exit(1)
    print("OKF conformance: PASS (all concepts conform)")
    sys.exit(0)


if __name__ == "__main__":
    main()
