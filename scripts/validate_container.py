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
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MIF_SCHEMA = REPO_ROOT / "schema" / "mif.schema.json"
CONTAINER_SCHEMA = REPO_ROOT / "schema" / "container.schema.json"
DOCUMENT_REFERENCE_SCHEMA = REPO_ROOT / "schema" / "document-reference.schema.json"
DEFS_GLOB = str(REPO_ROOT / "schema" / "definitions" / "*.schema.json")


def _ajv_validate(schema: Path, instance: Path, extra_refs: tuple[Path, ...] = ()) -> list[str]:
    """Validate `instance` against `schema` with ajv (draft2020, formats).
    `extra_refs` are additional -r schema files ajv should resolve $ref/$id
    against (e.g. document-reference.schema.json's $ref onto mif.schema.json).
    Fail-closed: a missing ajv/npx is reported as an error, never a silent pass."""
    cmd = ["npx", "--no-install", "ajv", "validate", "-s", str(schema)]
    for ref in extra_refs:
        cmd += ["-r", str(ref)]
    cmd += ["-r", DEFS_GLOB, "-d", str(instance), "--spec=draft2020", "-c", "ajv-formats"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return ["npx not found on PATH (run: npm ci)"]

    if proc.returncode == 0:
        return []
    out = (proc.stderr or proc.stdout or "").strip()
    return [ln for ln in out.splitlines() if ln.strip()]


def validate_corpus(path: Path) -> list[str]:
    """Validate one *.corpus.json file. Returns a list of error strings (empty if valid)."""
    errors: list[str] = []
    try:
        corpus = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path}: invalid JSON: {e}"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        envelope_file = tmp_path / "envelope.json"
        envelope_file.write_text(json.dumps(corpus))
        for line in _ajv_validate(CONTAINER_SCHEMA, envelope_file, extra_refs=(MIF_SCHEMA,)):
            errors.append(f"{path}: envelope invalid against container.schema.json: {line}")

        for i, record in enumerate(corpus.get("records", [])):
            if not isinstance(record, dict):
                errors.append(f"{path}: records[{i}]: expected an object, got {type(record).__name__}")
                continue
            kind = record.get("kind")
            payload_file = tmp_path / f"record-{i}.json"
            payload_file.write_text(json.dumps(record.get("payload", {})))

            if kind == "memory":
                for line in _ajv_validate(MIF_SCHEMA, payload_file):
                    errors.append(f"{path}: records[{i}] (kind=memory) invalid: {line}")
            elif kind == "document":
                for line in _ajv_validate(DOCUMENT_REFERENCE_SCHEMA, payload_file, extra_refs=(MIF_SCHEMA,)):
                    errors.append(f"{path}: records[{i}] (kind=document) invalid: {line}")

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
