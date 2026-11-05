#!/usr/bin/env python3
"""Regression suite for scripts/check_version_sync.py."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_version_sync  # noqa: E402  (local module, path set above)

FILES = {
    "VERSION.json": json.dumps({"specification": "2.1.0", "schemas": {"mif": "1.0.0"}}),
    "CHANGELOG.md": "## [Unreleased]\n\n## [2.1.0] - 2030-02-03\n\n## [2.0.1] - 2030-01-01 [YANKED]\n",
    "SPECIFICATION.md": '**Version**: 2.1.0\n**Last Updated**: 2030-02-03\n\n```yaml\nversion: "1.0.0"\n```\n',
    "README.md": (
        "[![Spec](https://img.shields.io/badge/spec-v2.1.0-blue.svg)](./SPECIFICATION.md)\n"
        "> **Brand note (v1.0.0):** historical.\n"
        "See it for the complete v2.1.0 specification.\n"
        "  version      = {2.1.0},\n"
        "  date         = {2030-02-03},\n"
    ),
    "CITATION.cff": (
        'version: "2.1.0"\n'
        'date-released: "2030-02-03"\n'
        "preferred-citation:\n"
        '  version: "2.1.0"\n'
        '  date-released: "2030-02-03"\n'
        "references:\n"
        '  - version: "1.0.0"\n'
        '    date-released: "2020-07-16"\n'
    ),
    "public/schema/index.json": json.dumps({"specVersion": "2.1.0"}),
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for name, content in FILES.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp_path


def failures(root: Path) -> list[str]:
    return [label for label, want, got in check_version_sync.build_checks(root) if want != got]


def test_consistent_repo_passes(repo: Path) -> None:
    assert failures(repo) == []


def test_this_repository_is_in_sync() -> None:
    assert failures(ROOT) == []


def test_samples_and_historical_mentions_are_ignored(repo: Path) -> None:
    """The fixture carries a 1.0.0 sample, brand note and reference on purpose."""
    assert 'version: "1.0.0"' in FILES["SPECIFICATION.md"]
    assert "(v1.0.0)" in FILES["README.md"]
    assert failures(repo) == []


@pytest.mark.parametrize(
    ("name", "old", "new", "expected"),
    [
        ("SPECIFICATION.md", "**Version**: 2.1.0", "**Version**: 2.0.0",
         "SPECIFICATION.md **Version** header"),
        ("SPECIFICATION.md", "**Last Updated**: 2030-02-03", "**Last Updated**: 2026-06-18",
         "SPECIFICATION.md **Last Updated** header"),
        ("README.md", "spec-v2.1.0-blue", "spec-v2.0.0-blue", "README.md spec badge"),
        ("README.md", "complete v2.1.0", "complete v1.0.0", "README.md specification link"),
        ("README.md", "= {2.1.0}", "= {1.0.0}", "README.md BibTeX version"),
        ("README.md", "= {2030-02-03}", "= {2026-06-18}", "README.md BibTeX date"),
        ("CITATION.cff", 'version: "2.1.0"\ndate', 'version: "1.0.0"\ndate',
         "CITATION.cff version"),
        ("CITATION.cff", 'date-released: "2030-02-03"\npreferred', 'date-released: "2026-06-18"\npreferred',
         "CITATION.cff date-released"),
        ("CITATION.cff", '  version: "2.1.0"', '  version: "1.0.0"',
         "CITATION.cff preferred-citation version"),
        ("CITATION.cff", '  date-released: "2030-02-03"', '  date-released: "2026-06-18"',
         "CITATION.cff preferred-citation date-released"),
        ("public/schema/index.json", "2.1.0", "2.0.0", "public/schema/index.json specVersion"),
    ],
)
def test_each_stale_field_is_reported(repo: Path, name: str, old: str, new: str, expected: str) -> None:
    path = repo / name
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    assert failures(repo) == [expected]


def test_removed_field_fails_rather_than_passing_unchecked(repo: Path) -> None:
    readme = repo / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace("the complete v2.1.0 specification", "the spec"))
    assert failures(repo) == ["README.md specification link"]


def test_missing_changelog_entry_fails(repo: Path) -> None:
    (repo / "CHANGELOG.md").write_text("## [Unreleased]\n", encoding="utf-8")
    assert failures(repo) == ["CHANGELOG.md has one dated [2.1.0] heading"]


def test_undated_changelog_heading_does_not_blame_correct_dates(repo: Path) -> None:
    (repo / "CHANGELOG.md").write_text("## [2.1.0]\n", encoding="utf-8")
    assert failures(repo) == ["CHANGELOG.md has one dated [2.1.0] heading"]


@pytest.mark.parametrize(
    "extra",
    ['version: "1.0.0"\n', 'date-released: "2026-06-18"\n'],
)
def test_duplicated_citation_key_fails(repo: Path, extra: str) -> None:
    path = repo / "CITATION.cff"
    path.write_text(extra + path.read_text(encoding="utf-8"), encoding="utf-8")
    assert len(failures(repo)) == 1


@pytest.mark.parametrize("content", ["", "preferred-citation:\n"])
def test_empty_citation_fails_without_crashing(repo: Path, content: str) -> None:
    (repo / "CITATION.cff").write_text(content, encoding="utf-8")
    assert len(failures(repo)) == 4
