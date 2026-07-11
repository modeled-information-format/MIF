#!/usr/bin/env python3
"""Validate *.corpus.json Container Profile artifacts (ADR-021).

``scripts/mif_convert.py``'s ``iter_concepts()`` only discovers ``*.md``
files, so a ``*.corpus.json`` envelope is invisible to ``okf_validate.py``
and the ``schema-validation`` CI job by construction -- this script is the
explicit, dedicated validation path ADR-021 Decision point 9 requires.

For each ``*.corpus.json`` under the given directories:

1. Validate the envelope itself against ``schema/container.schema.json``.
2. For every ``records[]`` entry with ``kind == "memory"``: ajv-validate
   ``.payload`` against ``schema/mif.schema.json`` (the same per-unit check
   ``okf_validate.py`` performs for ``.md`` concepts).
3. For every ``records[]`` entry with ``kind == "document"``: ajv-validate
   ``.payload`` against ``schema/document-reference.schema.json`` -- a
   standalone pointer onto ``mif.schema.json``'s ``DocumentReference``
   ``$defs`` entry (``ajv-cli`` cannot take a ``#/$defs/...`` fragment
   appended to ``-s`` directly).

``extensions`` content is deliberately NOT validated here: per ADR-021
Decision point 7, it is unvalidated, vendor-owned data.

Usage::

    python validate_container.py <dir> [dir ...]
    python validate_container.py            # defaults to examples/container
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path

from _ajv_common import ajv_validate, ajv_validate_batch

REPO_ROOT = Path(__file__).resolve().parent.parent
MIF_SCHEMA = REPO_ROOT / "schema" / "mif.schema.json"
CONTAINER_SCHEMA = REPO_ROOT / "schema" / "container.schema.json"
DOCUMENT_REFERENCE_SCHEMA = REPO_ROOT / "schema" / "document-reference.schema.json"
DEFS_GLOB = str(REPO_ROOT / "schema" / "definitions" / "*.schema.json")


def _ajv_validate(schema: Path, instance: object, extra_refs: tuple[Path | str, ...] = ()) -> list[str]:
    """Validate `instance` against `schema`, always resolving DEFS_GLOB in
    addition to any caller-supplied `extra_refs` (e.g. document-reference.
    schema.json's $ref onto mif.schema.json)."""
    return ajv_validate(schema, instance, extra_refs=(*extra_refs, DEFS_GLOB))


def _ajv_validate_batch(
    schema: Path, instances: Mapping[str, object], extra_refs: tuple[Path | str, ...] = ()
) -> dict[str, list[str]]:
    """Batched counterpart to `_ajv_validate`: one ajv-cli invocation for all
    `instances`, still always resolving DEFS_GLOB."""
    return ajv_validate_batch(schema, instances, extra_refs=(*extra_refs, DEFS_GLOB))


def validate_corpus(path: Path) -> list[str]:
    """Validate one *.corpus.json file. Returns a list of error strings (empty if valid)."""
    errors: list[str] = []
    try:
        corpus = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path}: invalid JSON: {e}"]

    for line in _ajv_validate(CONTAINER_SCHEMA, corpus, extra_refs=(MIF_SCHEMA,)):
        errors.append(f"{path}: envelope invalid against container.schema.json: {line}")

    # Only two kinds are ever defined (ADR-021 Decision point 3); one batched
    # ajv-cli call per kind present, instead of one call per record (#260).
    # `str(i)` keys the batch by plain record index; `kind == "..."` string
    # comparison (not a dict-membership test) so a malformed, unhashable
    # `kind` value (a list or object) is skipped like any other unrecognized
    # kind, not a crash.
    memory: dict[str, dict] = {}
    document: dict[str, dict] = {}
    order: list[tuple[int, str]] = []
    for i, record in enumerate(corpus.get("records", [])):
        if not isinstance(record, dict):
            errors.append(f"{path}: records[{i}]: expected an object, got {type(record).__name__}")
            continue
        kind = record.get("kind")
        payload = record.get("payload", {})
        if kind == "memory":
            memory[str(i)] = payload
            order.append((i, "memory"))
        elif kind == "document":
            document[str(i)] = payload
            order.append((i, "document"))

    results: dict[str, dict[str, list[str]]] = {}
    if memory:
        results["memory"] = _ajv_validate_batch(MIF_SCHEMA, memory)
    if document:
        results["document"] = _ajv_validate_batch(DOCUMENT_REFERENCE_SCHEMA, document, extra_refs=(MIF_SCHEMA,))

    # Emit in original records[] order, not grouped by kind, so error output
    # still reads top-to-bottom the way the source file does.
    for i, kind in order:
        for line in results[kind][str(i)]:
            errors.append(f"{path}: records[{i}] (kind={kind}) invalid: {line}")

    return errors


def main(argv: list[str]) -> int:
    # Anchored to REPO_ROOT, not the process CWD, so the documented no-arg
    # invocation behaves the same regardless of where it is run from.
    dirs = argv[1:] or [str(REPO_ROOT / "examples" / "container")]
    all_errors: list[str] = []
    checked = 0
    for dir_arg in dirs:
        for corpus_file in sorted(Path(dir_arg).rglob("*.corpus.json")):
            checked += 1
            all_errors.extend(validate_corpus(corpus_file))

    if all_errors:
        for e in all_errors:
            print(e, file=sys.stderr)
        print(f"Container validation: FAIL ({len(all_errors)} error(s) across {checked} file(s))")
        return 1

    if checked == 0:
        # Fail-closed: a gate that finds nothing and reports PASS is the
        # exact silent-pass failure mode this script exists to prevent
        # (ADR-021 Decision point 9) -- a typo'd path or an emptied
        # examples/container/ must not report green.
        print("Container validation: FAIL (0 file(s) found -- expected at least one *.corpus.json)", file=sys.stderr)
        return 1

    print(f"Container validation: PASS ({checked} file(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
