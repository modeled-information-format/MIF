#!/usr/bin/env python3
"""Shared ajv-cli invocation for this repo's Python JSON Schema validators
(scripts/validate_container.py, scripts/validate-ontologies.py). One place
for this subprocess/error-handling logic, so a future fix (a new flag, a
different failure mode) lands once instead of drifting between two
near-identical copies.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
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
