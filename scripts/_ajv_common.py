#!/usr/bin/env python3
"""Shared ajv-cli invocation for this repo's Python JSON Schema validators
(scripts/validate_container.py, scripts/validate-ontologies.py). One place
for this subprocess/error-handling logic, so a future fix (a new flag, a
different failure mode) lands once instead of drifting between two
near-identical copies.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path


def ajv_validate(
    schema: Path,
    instance: Path | dict,
    *,
    extra_refs: tuple[Path | str, ...] = (),
    use_npx: bool = True,
    truncate: int | None = None,
) -> list[str]:
    """Validate `instance` against `schema` with ajv (draft2020, formats,
    strict=false). `instance` may be a path to an on-disk JSON file, or an
    in-memory dict (written to a temp file for the duration of the call).
    `extra_refs` are additional -r schema files/globs ajv should resolve
    $ref/$id against. `truncate` caps the number of returned error lines
    (None = uncapped). Fail-closed: a missing ajv/npx is reported as an
    error, never a silent pass.
    """
    binary = ["npx", "--no-install", "ajv"] if use_npx else ["ajv"]

    def _run(instance_path: Path) -> list[str]:
        cmd = binary + ["validate", "-s", str(schema)]
        for ref in extra_refs:
            cmd += ["-r", str(ref)]
        cmd += ["-d", str(instance_path), "--spec=draft2020", "--strict=false", "-c", "ajv-formats"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            tool = "npx" if use_npx else "ajv"
            hint = "run: npm ci" if use_npx else "install: npm i -g ajv-cli ajv-formats"
            return [f"{tool} not found on PATH ({hint})"]
        if proc.returncode == 0:
            return []
        out = (proc.stderr or proc.stdout or "").strip()
        lines = [ln for ln in out.splitlines() if ln.strip()]
        return lines[:truncate] if truncate else lines

    if isinstance(instance, dict):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
            json.dump(instance, f)
            f.flush()
            return _run(Path(f.name))
    return _run(instance)


_RESULT_MARKER = re.compile(r"^.+\.json (?:valid|invalid)$")


def ajv_validate_batch(
    schema: Path,
    instances: Mapping[str, Path | dict],
    *,
    extra_refs: tuple[Path | str, ...] = (),
    use_npx: bool = True,
) -> dict[str, list[str]]:
    """Validate several named instances against one `schema` in a single ajv
    invocation (one `-d` per instance) instead of one subprocess spawn per
    instance -- same schema compilation, same npx/node startup cost paid
    once for the whole group. Returns `{name: [error lines]}`; an empty list
    means that instance is valid. Fail-closed: a missing ajv/npx reports the
    same error for every name, never a silent pass.

    Relies on ajv-cli reporting `<path> valid`/`<path> invalid` result lines
    in the same order as the `-d` flags were given (confirmed empirically);
    if the number of result lines it prints doesn't match the number of
    instances sent, every name is returned the raw combined output rather
    than a guessed (and possibly wrong) per-instance attribution.
    """
    names = list(instances.keys())
    if not names:
        return {}

    binary = ["npx", "--no-install", "ajv"] if use_npx else ["ajv"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        files: list[Path] = []
        for name in names:
            inst = instances[name]
            f = tmp_path / f"{name}.json"
            if isinstance(inst, dict):
                f.write_text(json.dumps(inst))
            else:
                f.write_text(Path(inst).read_text())
            files.append(f)

        cmd = binary + ["validate", "-s", str(schema)]
        for ref in extra_refs:
            cmd += ["-r", str(ref)]
        for f in files:
            cmd += ["-d", str(f)]
        cmd += ["--spec=draft2020", "--strict=false", "-c", "ajv-formats"]

        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except FileNotFoundError:
            tool = "npx" if use_npx else "ajv"
            hint = "run: npm ci" if use_npx else "install: npm i -g ajv-cli ajv-formats"
            return {name: [f"{tool} not found on PATH ({hint})"] for name in names}

        if proc.returncode == 0:
            return {name: [] for name in names}

        blocks: list[list[str]] = []
        current: list[str] | None = None
        for line in proc.stdout.splitlines():
            if _RESULT_MARKER.match(line):
                current = []
                blocks.append(current)
            elif current is not None:
                current.append(line)

        if len(blocks) != len(names):
            raw = [ln for ln in proc.stdout.splitlines() if ln.strip()]
            return {name: raw for name in names}

        return {name: [ln for ln in block if ln.strip()] for name, block in zip(names, blocks)}
