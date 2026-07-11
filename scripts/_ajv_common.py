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

_RESULT_LINE = re.compile(r"^(?P<path>.+\.json) (?:valid|invalid)$")

# npx resolves ajv-cli from node_modules relative to its working directory;
# pin it to the repo root so the lockfile-pinned install is used no matter
# where the calling process was started from.
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _parse_stream(
    text: str,
    stem_to_name: Mapping[str, str],
    results: dict[str, list[str]],
    seen: set[str],
    preamble: list[str],
) -> bool:
    """Sequentially attribute one output stream's lines to instances by
    their `<path> valid|invalid` result lines. Returns False on a result
    line whose path we never sent (caller must fail closed)."""
    current: list[str] | None = None
    for line in text.splitlines():
        m = _RESULT_LINE.match(line)
        if m:
            stem = Path(m.group("path")).stem
            name = stem_to_name.get(stem)
            if name is None:
                return False
            seen.add(name)
            current = results[name]
        elif current is not None:
            current.append(line)
        else:
            # Output before the first per-file result line (a warning, a
            # crash before validating anything) can't be attributed to
            # one instance -- surface it to all of them rather than
            # silently dropping it.
            preamble.append(line)
    return True


def ajv_validate_batch(
    schema: Path,
    instances: Mapping[str, object],
    *,
    extra_refs: tuple[Path | str, ...] = (),
    use_npx: bool = True,
) -> dict[str, list[str]]:
    """Validate several named instances against one `schema` in a single ajv
    invocation (one `-d` per instance) instead of one subprocess spawn per
    instance -- same schema compilation, same npx/node startup cost paid
    once for the whole group. Returns `{name: [error lines]}`; an empty list
    means that instance is valid. Each instance is a `Path` to an on-disk
    JSON file, or any JSON-serializable value (dict, list, str, number,
    bool, None) -- a malformed non-dict instance becomes a real ajv
    schema-validation error, not a crash. Fail-closed: a missing ajv/npx,
    output this function can't confidently attribute back to a specific
    instance, or an instance ajv exited nonzero without reporting a result
    line for (e.g. the process was killed mid-batch) all report an error for
    the affected name(s) rather than a silent pass or a guessed (possibly
    wrong) attribution.

    Attribution is by NAME, not by output-line position: each instance is
    written to a temp file named `<name>.json`, and ajv-cli's own
    `<path> valid`/`<path> invalid` result lines echo that path back, so the
    file stem recovers the instance name directly -- this does not depend on
    ajv-cli preserving `-d` argument order in its output. Names must not
    contain path separators (they become temp-file stems). stdout and stderr
    are parsed as separate streams: ajv-cli prints `valid` results to stdout
    but `invalid` results and their error details to stderr, and a merged
    pipe can interleave the two under backpressure, mis-attributing errors.
    """
    names = list(instances.keys())
    if not names:
        return {}
    for name in names:
        if "/" in name or "\\" in name:
            raise ValueError(f"instance name must not contain path separators: {name!r}")

    binary = ["npx", "--no-install", "ajv"] if use_npx else ["ajv"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        files: dict[str, Path] = {}
        for name in names:
            inst = instances[name]
            f = tmp_path / f"{name}.json"
            if isinstance(inst, Path):
                f.write_text(inst.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                # Any JSON-serializable value, not just dict -- a malformed
                # instance (a string/list/number/null payload, say) must
                # become an ajv schema-validation error, not a Path()/
                # read_text() crash on data that was never a filesystem path.
                f.write_text(json.dumps(inst), encoding="utf-8")
            files[name] = f

        cmd = binary + ["validate", "-s", str(schema)]
        for ref in extra_refs:
            cmd += ["-r", str(ref)]
        for name in names:
            cmd += ["-d", str(files[name])]
        cmd += ["--spec=draft2020", "--strict=false", "-c", "ajv-formats"]

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                cwd=_REPO_ROOT,
            )
        except FileNotFoundError:
            tool = "npx" if use_npx else "ajv"
            hint = "run: npm ci" if use_npx else "install: npm i -g ajv-cli ajv-formats"
            return {name: [f"{tool} not found on PATH ({hint})"] for name in names}

        if proc.returncode == 0:
            return {name: [] for name in names}

        stem_to_name = {f.stem: name for name, f in files.items()}
        results: dict[str, list[str]] = {name: [] for name in names}
        seen: set[str] = set()
        preamble: list[str] = []
        # stderr first (invalid results + their error details), then stdout
        # (valid confirmations); each stream is internally ordered even
        # though their interleaving in a shared pipe would not be.
        if not (
            _parse_stream(proc.stderr, stem_to_name, results, seen, preamble)
            and _parse_stream(proc.stdout, stem_to_name, results, seen, preamble)
        ):
            # ajv reported a result for a path we didn't send -- fail
            # closed rather than guess which instance it belongs to.
            raw = [ln for ln in (proc.stdout + "\n" + proc.stderr).splitlines() if ln.strip()]
            return {n: raw for n in names}

        preamble_text = [ln for ln in preamble if ln.strip()]
        out = {name: preamble_text + [ln for ln in lines if ln.strip()] for name, lines in results.items()}
        # ajv exited nonzero: any instance with no result line at all was
        # never validated (crash/kill mid-batch) -- fail closed, never
        # report it valid by silence.
        for name in names:
            if name not in seen and not out[name]:
                out[name] = preamble_text + [
                    f"ajv exited {proc.returncode} without reporting a result for this instance; treating as failed"
                ]
        return out


def ajv_validate(
    schema: Path,
    instance: object,
    *,
    extra_refs: tuple[Path | str, ...] = (),
    use_npx: bool = True,
    truncate: int | None = None,
) -> list[str]:
    """Validate `instance` against `schema` with ajv (draft2020, formats,
    strict=false). `instance` may be a `Path` to an on-disk JSON file, or any
    JSON-serializable value. `extra_refs` are additional -r schema files/
    globs ajv should resolve $ref/$id against. `truncate` caps the number of
    returned error lines (None = uncapped). A thin single-instance wrapper
    over `ajv_validate_batch`, so the two share one subprocess/error-handling
    implementation instead of drifting apart.
    """
    lines = ajv_validate_batch(schema, {"instance": instance}, extra_refs=extra_refs, use_npx=use_npx)["instance"]
    return lines[:truncate] if truncate is not None else lines
