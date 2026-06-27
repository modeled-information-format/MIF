#!/usr/bin/env python3
"""Snapshot the canonical JSON Schemas into an immutable per-version mirror.

For each release `vX.Y.Z`, MIF publishes the schemas at version-pathed mirrors
under `public/schema/` (see public/schema/VERSIONING.md and ADR-016):

    public/schema/<file>            canonical, unversioned $id (ADR-007); latest
    public/schema/X.Y.Z/<file>      immutable snapshot of this release
    public/schema/latest/<file>     moving alias -> newest release
    public/schema/vMAJOR/<file>     major alias -> newest release in that major

This script makes those mirrors for a new version from the current canonical
files, and updates the machine-readable catalog `public/schema/index.json`. The
schema bytes are copied verbatim: the internal `$id` stays canonical and
unversioned, so a mirror pins the bytes without forking the identity.

Usage:
    python3 scripts/snapshot-schema-version.py X.Y.Z
    python3 scripts/snapshot-schema-version.py X.Y.Z --check   # verify only, no writes

Run it as a release-prep step BEFORE tagging, and commit the result; the release
workflow fails closed if the mirror for the tagged version is absent.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

# Canonical schema files mirrored per version (relative to public/schema/).
# Documentation (e.g. ontology/README.md) is canonical-only and not mirrored.
MIRRORED_FILES = [
    "mif.schema.json",
    "citation.schema.json",
    "context.jsonld",
    "definitions/entity-reference.schema.json",
    "ontology/ontology.schema.json",
    "ontology/ontology.context.jsonld",
]

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SCHEMA_ROOT = Path(__file__).resolve().parent.parent / "public" / "schema"


def _semver_key(v: str) -> tuple[int, int, int]:
    a, b, c = v.split(".")
    return (int(a), int(b), int(c))


def _copy_set(dest_dir: Path, check: bool, missing: list[str]) -> None:
    for rel in MIRRORED_FILES:
        src = SCHEMA_ROOT / rel
        if not src.exists():
            missing.append(f"canonical source missing: public/schema/{rel}")
            continue
        dst = dest_dir / rel
        if check:
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                missing.append(f"out of date: {dst.relative_to(SCHEMA_ROOT.parent.parent)}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _update_index(version: str, check: bool, problems: list[str]) -> None:
    index_path = SCHEMA_ROOT / "index.json"
    index = json.loads(index_path.read_text())

    versions = sorted(set(index.get("versions", [])) | {version}, key=_semver_key)
    newest = versions[-1]
    majors = sorted({v.split(".")[0] for v in versions}, key=int)
    aliases = {"latest": newest}
    for m in majors:
        aliases[f"v{m}"] = max((v for v in versions if v.split(".")[0] == m), key=_semver_key)

    desired = {
        "specVersion": newest,
        "versions": versions,
        "aliases": aliases,
    }
    if check:
        for key, want in desired.items():
            if index.get(key) != want:
                problems.append(f"index.json {key} is {index.get(key)!r}, expected {want!r}")
        for schema in index.get("schemas", []):
            if version not in schema.get("versioned", {}):
                problems.append(f"index.json schema {schema['id']!r} missing version {version}")
        return

    index.update(desired)
    base = index["canonicalBase"].rstrip("/")
    for schema in index.get("schemas", []):
        canonical = schema["canonical"]
        rel = canonical[len(base) + 1 :]  # path under /schema/
        ver = schema.setdefault("versioned", {})
        for v in versions:
            ver[v] = f"{base}/{v}/{rel}"
        ver["latest"] = f"{base}/latest/{rel}"
        for m in majors:
            ver[f"v{m}"] = f"{base}/v{m}/{rel}"
    index_path.write_text(json.dumps(index, indent=2) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version", help="release version, e.g. 1.1.0 (no leading v)")
    ap.add_argument("--check", action="store_true", help="verify the mirror is present and current; write nothing")
    args = ap.parse_args()

    version = args.version.lstrip("v")
    if not SEMVER.match(version):
        print(f"error: '{version}' is not a bare X.Y.Z version", file=sys.stderr)
        return 2
    major = version.split(".")[0]

    problems: list[str] = []
    _copy_set(SCHEMA_ROOT / version, args.check, problems)
    _copy_set(SCHEMA_ROOT / "latest", args.check, problems)
    _copy_set(SCHEMA_ROOT / f"v{major}", args.check, problems)
    _update_index(version, args.check, problems)

    if args.check:
        if problems:
            print(f"schema mirror for {version} is NOT up to date:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 1
        print(f"schema mirror for {version}: present and current")
        return 0

    if problems:
        print("snapshot failed:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"snapshotted public/schema/{version}/, refreshed latest/ and v{major}/, updated index.json")
    print("review and commit the result before tagging the release (ADR-016)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
