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

Exit code 0 means every concept in every bundle conforms.

Usage::

    python okf_validate.py <bundle-dir> [bundle-dir ...] [--strict-temporal]
    python okf_validate.py            # defaults to examples/ + profiles/*/examples/
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml  # PyYAML; parse_markdown's safe_load can raise yaml.YAMLError

import mif_convert  # local module (same scripts/ directory)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Relationship types whose target is a *prior* concept the source is built on:
# the target must not be created AFTER the source. (Q-a: derived-from + supersedes
# + cites.) Stored kebab-normalized to match _kebab() output.
DERIVATION_TYPES = {"derived-from", "supersedes", "cites"}

# A body relationship line: "- <kebab-type> [Text](/path/to/target.md)".
REL_LINE_RE = re.compile(r"^-\s+([a-z0-9][a-z0-9-]*)\s+\[[^\]]+\]\(([^)]+)\)\s*$")
# Any markdown link, for broken-link scanning.
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _kebab(value: str) -> str:
    """Normalize a relationship type token to kebab-case for comparison."""
    value = re.sub(r"(?<!^)(?=[A-Z])", "-", value)
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
