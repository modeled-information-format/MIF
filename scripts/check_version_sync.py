#!/usr/bin/env python3
"""Fail when a restated specification version disagrees with VERSION.json.

`VERSION.json`'s `specification` is the canonical version, and `release.yml`
reads it. Several human-facing files restate it by hand, and nothing compared
them: `CITATION.cff` and the README's citation block stayed on 1.0.0 through
every release up to 1.4.2, while the SPECIFICATION.md header and README badge
were bumped.

The release date is the one on the version's CHANGELOG.md heading. Only the
current specification version is checked. Ontology and schema versions run on
their own tracks, and historical mentions of a release are deliberately out of
scope, so this looks at named fields, not at every "1.0.0" in the tree.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent

Check = tuple[str, object, object]


def _read(root: Path, name: str) -> str:
    return (root / name).read_text(encoding="utf-8")


def build_checks(root: Path) -> list[Check]:
    """Return (label, expected, actual) for every restated version and date.

    Each regex must match exactly once: a missing or duplicated field is
    drift too, so a reworded line fails here instead of going unchecked.
    """
    version = json.loads(_read(root, "VERSION.json"))["specification"]
    changelog = _read(root, "CHANGELOG.md")
    heading = rf"^## \[{re.escape(version)}\] - (\d{{4}}-\d{{2}}-\d{{2}})"
    release_dates = re.findall(heading, changelog, re.MULTILINE)
    checks: list[Check] = [
        (f"CHANGELOG.md has one dated [{version}] heading", 1, len(release_dates))
    ]
    date = release_dates[0] if release_dates else None

    spec = _read(root, "SPECIFICATION.md")
    checks.append(
        ("SPECIFICATION.md **Version** header", [version],
         re.findall(r"^\*\*Version\*\*: *(\S+)", spec, re.MULTILINE))
    )

    readme = _read(root, "README.md")
    for label, pattern, expected in (
        ("README.md spec badge", r"badge/spec-v([^-/]+)-", version),
        ("README.md specification link", r"the complete v(\S+) specification", version),
        ("README.md BibTeX version", r"^\s*version\s*=\s*\{([^}]*)\}", version),
        ("README.md BibTeX date", r"^\s*date\s*=\s*\{([^}]*)\}", date),
    ):
        checks.append((label, [expected], re.findall(pattern, readme, re.MULTILINE)))

    citation = yaml.safe_load(_read(root, "CITATION.cff"))
    for label, entry in (
        ("CITATION.cff", citation),
        ("CITATION.cff preferred-citation", citation.get("preferred-citation", {})),
    ):
        checks.append((f"{label} version", version, entry.get("version")))
        checks.append((f"{label} date-released", date, str(entry.get("date-released"))))

    index = json.loads(_read(root, "public/schema/index.json"))
    checks.append(("public/schema/index.json specVersion", version, index.get("specVersion")))
    return checks


def main() -> int:
    try:
        checks = build_checks(ROOT)
    except (OSError, KeyError, json.JSONDecodeError, yaml.YAMLError) as e:
        print(f"FAIL: could not read version metadata: {e!r}")
        return 1

    failed = []
    for label, expected, actual in checks:
        if expected == actual:
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label}")
            print(f"  expected: {expected!r}")
            print(f"  found:    {actual!r}")
            failed.append(label)

    if failed:
        print(f"\nversion sync check FAILED, VERSION.json disagrees with: {failed}")
        print("See docs/RELEASING.md section 1a for the files a release bumps.")
        return 1
    print("\nAll restated specification versions match VERSION.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
