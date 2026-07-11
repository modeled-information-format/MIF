#!/usr/bin/env python3
"""Regression test for `_ajv_common.ajv_validate_batch` (issue #260): a batch
of same-schema instances must validate in ONE ajv-cli subprocess spawn, not
one spawn per instance, and each instance's pass/fail result must still be
correctly attributed back to it -- not smeared across the batch or mixed up
with a neighbor's result.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from _ajv_common import ajv_validate_batch  # noqa: E402

_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["name"],
    "properties": {"name": {"type": "string", "minLength": 1}},
}


def main() -> int:
    failed: list[str] = []
    tmp_schema = ROOT / "scripts" / "_test_ajv_batch_schema.json"
    import json

    tmp_schema.write_text(json.dumps(_SCHEMA))
    try:
        # Case 1: mixed valid/invalid batch -- attribution must not cross-wire.
        instances = {
            "good-a": {"name": "alice"},
            "bad": {"not_name": "oops"},
            "good-b": {"name": "bob"},
        }
        results = ajv_validate_batch(tmp_schema, instances)
        ok = (
            results.get("good-a") == []
            and results.get("good-b") == []
            and results.get("bad")
            and any("name" in ln for ln in results["bad"])
        )
        verdict = "PASS" if ok else "FAIL"
        print(f"{verdict}: mixed-batch per-instance attribution -> {results}")
        if not ok:
            failed.append("mixed-batch attribution")

        # Case 2: N instances must cost exactly ONE subprocess spawn, not N.
        spawn_count = 0
        real_run = subprocess.run

        def _counting_run(*args, **kwargs):
            nonlocal spawn_count
            spawn_count += 1
            return real_run(*args, **kwargs)

        subprocess.run = _counting_run  # type: ignore[assignment]
        try:
            many = {f"item-{i}": {"name": f"n{i}"} for i in range(5)}
            ajv_validate_batch(tmp_schema, many)
        finally:
            subprocess.run = real_run  # type: ignore[assignment]

        ok = spawn_count == 1
        verdict = "PASS" if ok else "FAIL"
        print(f"{verdict}: 5 instances -> {spawn_count} ajv subprocess spawn(s) (expected 1)")
        if not ok:
            failed.append("subprocess spawn count")
    finally:
        tmp_schema.unlink(missing_ok=True)

    if failed:
        print(f"\najv batch validation test FAILED: {failed}")
        return 1
    print("\nAll ajv batch validation tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
