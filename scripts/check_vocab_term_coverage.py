#!/usr/bin/env python3
"""Structural guard against the #225/#226/#228 bug class recurring for a
FUTURE `@type:@vocab` field.

#225 (documentType) and #226 (citationType/citationRole) were both the same
defect: a JSON-LD term definition uses `@type:@vocab` for a property whose
schema enum has no registered term, so unrecognized values silently fall
back to unstable, document-base-relative IRI resolution. Both were caught by
hand, one field at a time, only after they'd already shipped.

This script closes the gap structurally: it walks every `@type:@vocab` term
definition in `schema/context.jsonld` (at any nesting depth), finds the
matching property's `enum` in `schema/mif.schema.json` (checked at the top
level and inside every `$defs` entry), and fails if any enum value has no
registered term reachable from that property's own scope -- or if a
registered term doesn't correspond to any enum value (a stale/typo'd entry
sitting alongside correct ones, otherwise invisible since the correct values
being present would still read as "covered").

"Reachable" accounts for two safe registration shapes:
  - a term-scoped `@context` on the property's own definition (the pattern
    `documentType`/`citationType`/`citationRole`/`conceptType`/`memoryType`/
    `sourceType`/`trustLevel` all use), or
  - an inherited `@vocab` default from an enclosing scope (the pattern
    `relationships[].type` uses via the `relationships` container's own
    `"@vocab": "https://mif-spec.dev/ns/"`) -- any value resolves safely to
    a stable `mif:`-namespaced IRI by construction, so no explicit
    registration is required.

A property with `@type:@vocab` but no matching schema `enum` (e.g. the
free-form kebab-case `Relationship.type`, or a term whose schema property
uses a different name than its JSON-LD term key) has nothing to check
against and is reported as SKIPPED, not silently dropped -- so "no enum
exists" and "enum exists but wasn't found" are distinguishable in the
output. `_schema_enum` also returns the FIRST enum found for a given
property name across `$defs` entries, not the one for a specific type;
today no two `$defs` entries define different enums under the same
property name for any vocab-typed term, but this is a known limitation if
that ever changes, not disambiguated here (doing so would require knowing
which schema type each JSON-LD term corresponds to, which this repo's
context/schema pairing doesn't currently encode).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTEXT = json.loads((ROOT / "schema" / "context.jsonld").read_text())["@context"]
SCHEMA = json.loads((ROOT / "schema" / "mif.schema.json").read_text())


def _schema_enum(prop: str) -> list[str] | None:
    """Find `prop`'s enum in the schema: top-level properties first, then
    every $defs entry's properties. Handles both the plain `enum: [...]`
    shape and the `oneOf: [{enum: [...]}, {pattern: ...}]` escape-hatch
    shape used by documentType/citationType/citationRole."""
    candidates = [SCHEMA.get("properties", {})]
    candidates += [d.get("properties", {}) for d in SCHEMA.get("$defs", {}).values()]
    for props in candidates:
        spec = props.get(prop)
        if not isinstance(spec, dict):
            continue
        if "enum" in spec:
            return spec["enum"]
        for branch in spec.get("oneOf", []):
            if "enum" in branch:
                return branch["enum"]
    return None


def _walk(node: dict, ambient_vocab: bool, path: str, findings: list[dict]) -> None:
    """Recurse through a JSON-LD @context dict, tracking whether an
    ambient @vocab default is active in the current scope."""
    scope_vocab = ambient_vocab or isinstance(node.get("@vocab"), str)
    for key, value in node.items():
        if key.startswith("@"):
            continue
        if not isinstance(value, dict):
            continue
        term_path = f"{path}.{key}" if path else key
        if value.get("@type") == "@vocab":
            enum = _schema_enum(key)
            registered = set(value.get("@context", {}).keys())
            findings.append({
                "term": key,
                "path": term_path,
                "enum": enum,
                "missing": [v for v in enum if v not in registered] if enum is not None else [],
                "extra": sorted(registered - set(enum)) if enum is not None else [],
                "safe_by_ambient_vocab": scope_vocab,
            })
        nested = value.get("@context")
        if isinstance(nested, dict):
            _walk(nested, scope_vocab, term_path, findings)


def main() -> int:
    findings: list[dict] = []
    _walk(CONTEXT, False, "", findings)

    if not findings:
        print("No @type:@vocab properties found at all -- nothing to check.")
        return 1  # Suspicious: this script exists because such properties exist.

    failed = []
    checked = 0
    for f in findings:
        if f["enum"] is None:
            print(f"SKIP: {f['path']} -- no matching schema enum found for this property name")
            continue
        checked += 1
        label = f"{f['path']} ({len(f['enum'])} enum values)"
        problems = []
        if f["missing"] and not f["safe_by_ambient_vocab"]:
            problems.append(f"unregistered, no ambient @vocab fallback: {f['missing']}")
        if f["extra"]:
            problems.append(f"registered term(s) not in the schema enum (stale/typo?): {f['extra']}")
        if problems:
            print(f"FAIL: {label} -- " + "; ".join(problems))
            failed.append(f["path"])
        elif f["missing"]:
            print(
                f"PASS: {label} -- {len(f['missing'])} value(s) unregistered "
                f"but safe via inherited ambient @vocab: {f['missing']}"
            )
        else:
            print(f"PASS: {label} -- every enum value has a registered term, no extras")

    if failed:
        print(f"\nVocab term coverage FAILED for: {failed}")
        return 1
    print(f"\nAll {checked} enum-bounded @type:@vocab properties are fully and exactly covered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
