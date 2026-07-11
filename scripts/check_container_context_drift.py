#!/usr/bin/env python3
"""Structural guard against issue #259: `schema/container-context.jsonld`
hand-copies a handful of prefix/term definitions that already exist
verbatim in `schema/context.jsonld`, instead of composing the two files.
Nothing enforces they stay in sync, and this has already happened once in
this branch's own history (the corpus-level and per-unit `extensions` terms
diverged until issue #224 reconciled them the same day).

This is the low-effort option (c) from #259: a CI check that fails if the
shared definitions diverge, without restructuring either file (rejected:
composing via an array `@context` would import `context.jsonld`'s unrelated
per-unit memory vocabulary into the container envelope's root active
context, cutting against ADR-021 Decision point 8's "minimal blast radius"
design driver).

Checks, by direct JSON comparison (no JSON-LD processing needed -- these are
exact-string/exact-structure duplications, not semantically-equivalent
rephrasings):

- EVERY top-level term name defined in both files (computed dynamically, so
  a term later added to both is compared automatically instead of silently
  skipped), except the documented divergences in ALLOWED_DIVERGENT.
- The PROV relation terms and the `id` alias nested inside
  `container-context.jsonld`'s `provenance` term's scoped `@context`,
  compared against `context.jsonld`'s top-level definitions of the same
  terms (nested there because the corpus-level `provenance` term scopes
  them; top-level in the core context).
- The `hash` term definition nested inside `container-context.jsonld`'s
  `payload` scoped-`@context` array, compared against `context.jsonld`'s
  `documents`-scoped `hash` definition (hand-copied there because a bare
  `kind: "document"` DocumentReference payload never activates the core
  `documents` term's scope -- without the copy, `hash` silently drops on
  JSON-LD expand).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Terms defined in both files whose definitions legitimately differ.
# `provenance` in the core context is the per-unit term (a bare IRI mapping,
# its keys resolved by the core context's own top-level terms); the
# container context's corpus-level term carries a scoped @context instead,
# whose contents the nested checks below compare term-by-term.
ALLOWED_DIVERGENT = {"provenance"}

# PROV relation terms (and the `id` alias) that the container context nests
# under `provenance` but the core context defines top-level.
PROV_SCOPED_TERMS = ("id", "wasDerivedFrom", "wasGeneratedBy", "wasAttributedTo", "wasAssociatedWith")


def _load_context(path: Path) -> dict | str:
    """Return the file's @context object, or an error string."""
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return f"cannot load {path.name}: {e}"
    ctx = doc.get("@context") if isinstance(doc, dict) else None
    if not isinstance(ctx, dict):
        return f"{path.name}: expected a top-level object @context, got {type(ctx).__name__}"
    return ctx


def _nested(ctx: dict, *keys: str) -> object:
    """Walk nested dicts; a missing/malformed step returns a sentinel string."""
    cur: object = ctx
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return f"<not found: {'.'.join(keys)}>"
        cur = cur[k]
    return cur


def _payload_scoped_hash(container: dict) -> object:
    """`payload`'s scoped @context is an array [core-URL, {overrides}]; find
    the `hash` definition in its object entries."""
    scoped = _nested(container, "payload", "@context")
    if isinstance(scoped, list):
        for entry in scoped:
            if isinstance(entry, dict) and "hash" in entry:
                return entry["hash"]
    return f"<not found: payload.@context[...].hash (got {scoped!r})>"


def build_checks(core: dict, container: dict) -> list[tuple[str, object, object]]:
    checks: list[tuple[str, object, object]] = []
    shared = sorted((set(core) & set(container)) - ALLOWED_DIVERGENT)
    for term in shared:
        checks.append(
            (f"shared top-level term {term!r} matches between context.jsonld and container-context.jsonld",
             core[term], container[term])
        )
    for term in PROV_SCOPED_TERMS:
        checks.append(
            (f"{term!r} (top-level in context.jsonld, nested under provenance in container-context.jsonld) matches",
             core.get(term), _nested(container, "provenance", "@context", term))
        )
    checks.append(
        ("'hash' (documents-scoped in context.jsonld, payload-scoped in container-context.jsonld) matches",
         _nested(core, "documents", "@context", "hash"), _payload_scoped_hash(container))
    )
    return checks


def main() -> int:
    core = _load_context(ROOT / "schema" / "context.jsonld")
    container = _load_context(ROOT / "schema" / "container-context.jsonld")
    for loaded, name in ((core, "context.jsonld"), (container, "container-context.jsonld")):
        if isinstance(loaded, str):
            print(f"FAIL: {loaded}")
            print(f"\ncontainer-context.jsonld drift check FAILED: could not load {name}")
            return 1
    assert isinstance(core, dict) and isinstance(container, dict)

    failed = []
    for label, core_val, container_val in build_checks(core, container):
        if core_val == container_val:
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label}")
            print(f"  context.jsonld:           {core_val!r}")
            print(f"  container-context.jsonld: {container_val!r}")
            failed.append(label)

    if failed:
        print(f"\ncontainer-context.jsonld drift check FAILED: {failed}")
        return 1
    print("\nAll shared context.jsonld/container-context.jsonld definitions match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
