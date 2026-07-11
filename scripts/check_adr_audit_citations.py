#!/usr/bin/env python3
"""Diff-scoped guardrail against the #241 bug class recurring: a NEW raw
`L\\d+` / `L\\d+-L\\d+` line-number citation added to an ADR's Audit table.

#238 fixed ADR-012's own Audit table to cite durable anchors (job id, step
`name:`, heading text, field name) instead of raw line numbers, because a
line number into a file that keeps changing (a CI workflow, a schema, a
script) silently drifts as the file is edited -- the citation stops
pointing at what it claims to, while still reading as authoritative.
`adr/README.md` documents the durable-anchor convention as the standard
going forward (see its "Creating New ADRs" section).

This script is deliberately NOT a repo-wide check of every ADR's existing
citations -- #241 catalogued 11 ADRs that still use the raw-line-number
style, and retrofitting them is real, separately-scoped work (tracked in
#241 itself), not something a blocking lint should demand overnight. This
script only looks at lines *added* by the diff being checked: it lets
existing citations be, and blocks only a *new* one from being introduced
the same way.

Does not (yet) catch ADR-019's bare-unlabeled-number citation style (a
number with no `L` prefix, e.g. "23" or "4-7") -- that pattern is far more
prone to false positives (any number in prose or a version string would
match) and needs a narrower, table-column-aware heuristic than this first
pass implements. See #241.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# A markdown table row: starts with `|`, and somewhere in it a raw line-number
# citation like `L46` or `L46-L58`. Word-bounded so `SLSA` or `URL` don't match.
TABLE_ROW = re.compile(r"^\s*\|")
RAW_LINE_CITATION = re.compile(r"\bL\d+(?:-L\d+)?\b")

DIFF_HEADER = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def run_diff(base: str, head: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}...{head}", "--", "adr/*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def find_violations(diff_text: str) -> list[tuple[str, int, str]]:
    """Returns (file, new_line_number, line_content) for every added line in
    an adr/*.md file that is a table row containing a raw L\\d+ citation."""
    violations: list[tuple[str, int, str]] = []
    current_file = None
    next_line = None

    for line in diff_text.splitlines():
        header_match = DIFF_HEADER.match(line)
        if header_match:
            current_file = header_match.group(1)
            next_line = None
            continue

        hunk_match = HUNK_HEADER.match(line)
        if hunk_match:
            next_line = int(hunk_match.group(1))
            continue

        if current_file is None or next_line is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            added = line[1:]
            if TABLE_ROW.match(added) and RAW_LINE_CITATION.search(added):
                violations.append((current_file, next_line, added.strip()))
            next_line += 1
        # Removed ("-") lines don't consume a new-file line number, and
        # context lines are absent entirely under --unified=0 -- both fall
        # through here with no action, which is correct.

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="base ref to diff against")
    parser.add_argument("--head", default="HEAD", help="head ref being checked")
    args = parser.parse_args()

    diff_text = run_diff(args.base, args.head)
    violations = find_violations(diff_text)

    if not violations:
        print(f"No new raw line-number citations added to adr/*.md Audit tables ({args.base}...{args.head}).")
        return 0

    print(
        f"FAIL: {len(violations)} newly-added raw line-number citation(s) in "
        f"adr/*.md Audit table(s) ({args.base}...{args.head}):\n"
    )
    for file, line_no, content in violations:
        print(f"  {file}:{line_no}: {content}")
    print(
        "\nCite a durable anchor instead (job id, step `name:`, heading text, "
        "field name -- something `grep -n` still finds after the file "
        "changes), per adr/README.md's Audit-citation guidance. Raw line "
        "numbers into a file that keeps changing silently drift; see #238 "
        "and #241 for why this is enforced."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
