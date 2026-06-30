#!/usr/bin/env python3
"""Snapshot the MIF ontology corpus into an immutable per-version mirror.

The corpus is served at `https://mif-spec.dev/ontologies/` from
`public/ontologies/`, mirroring the JSON-Schema serving model
(see public/schema/VERSIONING.md):

    public/ontologies/<name>.ontology.{yaml,jsonld}        canonical, latest
    public/ontologies/X.Y.Z/<name>.ontology.{yaml,jsonld}  immutable corpus snapshot
    public/ontologies/latest/<name>.ontology.{yaml,jsonld} moving alias -> newest
    public/ontologies/vMAJOR/<name>.ontology.{yaml,jsonld} major alias -> newest in major

`X.Y.Z` is a CORPUS release version: an immutable snapshot of every ontology at
whatever individual `version` it carried then. The bytes are copied verbatim, so
each ontology's own `id`/`version`/`@id` is unchanged; the version path is an
additional access location, not a new identity. The machine-readable catalog
`public/ontologies/index.json` is regenerated from the canonical files.

Usage:
    python3 scripts/snapshot-ontology-version.py X.Y.Z
    python3 scripts/snapshot-ontology-version.py X.Y.Z --check   # verify only

Run it as a release-prep step BEFORE tagging and commit the result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
ROOT = Path(__file__).resolve().parent.parent / "public" / "ontologies"
CANONICAL_BASE = "https://mif-spec.dev/ontologies/"

INDEX_META = {
    "name": "MIF ontology catalog",
    "description": (
        "Machine-readable index of the MIF (Modeled Information Format) ontology "
        "corpus served at https://mif-spec.dev/ontologies/. Each ontology's "
        "canonical URL is unversioned and tracks the latest corpus release; the "
        "version-pathed mirrors are immutable per-release snapshots. Each entry's "
        "`version` is the ontology's own version, independent of the corpus "
        "release `versions` listed here."
    ),
    "canonicalBase": CANONICAL_BASE,
    "mediaType": {
        "intended": "application/ld+json",
        "note": (
            "GitHub Pages serves .json/.jsonld as application/json and does not "
            "allow per-file Content-Type overrides; application/ld+json is the "
            "intended media type for the .ontology.jsonld files on conforming hosts."
        ),
    },
}


def _semver_key(v: str) -> tuple[int, int, int]:
    a, b, c = v.split(".")
    return (int(a), int(b), int(c))


def _canonical_names() -> list[str]:
    """Ontology base names that have BOTH a .yaml and a .jsonld canonical file."""
    names = []
    for j in sorted(ROOT.glob("*.ontology.jsonld")):
        name = j.name[: -len(".ontology.jsonld")]
        if (ROOT / f"{name}.ontology.yaml").is_file():
            names.append(name)
    return names


def _own_version(name: str) -> str:
    data = json.loads((ROOT / f"{name}.ontology.jsonld").read_text())
    return str(data.get("version", "")) or "unknown"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extends(name: str) -> list[str]:
    """The ontology's direct `extends` parents, read from its canonical YAML.

    These are the immediate parents only; the harness fetcher walks the closure.
    """
    data = yaml.safe_load((ROOT / f"{name}.ontology.yaml").read_text()) or {}
    ext = (data.get("ontology") or {}).get("extends") or []
    return [str(e) for e in ext]


def _copy_set(dest_dir: Path, names: list[str], check: bool, problems: list[str]) -> None:
    for name in names:
        for ext in ("ontology.yaml", "ontology.jsonld"):
            src = ROOT / f"{name}.{ext}"
            dst = dest_dir / f"{name}.{ext}"
            if check:
                if not dst.exists() or dst.read_bytes() != src.read_bytes():
                    problems.append(f"out of date: {dst.relative_to(ROOT.parent.parent)}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _build_index(version: str) -> dict:
    names = _canonical_names()
    index_path = ROOT / "index.json"
    prior = json.loads(index_path.read_text()) if index_path.exists() else {}
    versions = sorted(set(prior.get("versions", [])) | {version}, key=_semver_key)
    newest = versions[-1]
    majors = sorted({v.split(".")[0] for v in versions}, key=int)
    aliases = {"latest": newest}
    for m in majors:
        aliases[f"v{m}"] = max((v for v in versions if v.split(".")[0] == m), key=_semver_key)

    # ADR-0002 (ontologies): the catalog is an OBJECT keyed by id, each entry carrying
    # the on-demand fetch contract (file + sha256 of the served .ontology.yaml + extends)
    # alongside the discovery URLs. This is the shape the harness fetcher consumes
    # fail-closed and the one the ontologies repo's gen-ontology-index.sh already emits.
    ontologies = {}
    for name in names:
        versioned = {}
        for alias in (*versions, "latest", *(f"v{m}" for m in majors)):
            if (ROOT / alias / f"{name}.ontology.jsonld").is_file():
                versioned[alias] = f"{CANONICAL_BASE}{alias}/{name}.ontology.jsonld"
        ontologies[name] = {
            "version": _own_version(name),
            "file": f"{name}.ontology.yaml",
            "sha256": _sha256(ROOT / f"{name}.ontology.yaml"),
            "extends": _extends(name),
            "canonical": f"{CANONICAL_BASE}{name}.ontology.jsonld",
            "yaml": f"{CANONICAL_BASE}{name}.ontology.yaml",
            "versioned": versioned,
        }

    return {**INDEX_META, "versions": versions, "aliases": aliases, "ontologies": ontologies}


def _build_html(index: dict) -> str:
    """Human-readable, on-brand (mif-brand) static index for the corpus.

    A raw static file served at /ontologies/, so the brand tokens are inlined
    rather than inherited from the Starlight theme.
    """
    from html import escape
    rows = []
    for name_key, o in sorted(index["ontologies"].items()):
        name = escape(name_key)
        ver = escape(o["version"])
        rows.append(
            f'      <tr><th scope="row"><code>{name}</code></th>'
            f'<td class="v">{ver}</td>'
            f'<td><a href="./{name}.ontology.yaml">YAML</a></td>'
            f'<td><a href="./{name}.ontology.jsonld">JSON-LD</a></td></tr>'
        )
    aliases = ", ".join(f"<code>{escape(k)}</code>&rarr;<code>{escape(v)}</code>"
                        for k, v in index["aliases"].items())
    versions = ", ".join(f"<code>{escape(v)}</code>" for v in index["versions"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MIF Ontology Corpus</title>
<meta name="description" content="{escape(index['description'])}">
<style>
  :root {{
    --void:#0A0D13; --base:#0E121B; --elev:#151B27; --border:#222C3C;
    --text:#E8EEF6; --muted:#AEBCCF; --dim:#7C8AA0;
    --machine:#34D3E8; --human:#F5B642;
    --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono","JetBrains Mono","Fira Code",Menlo,Consolas,monospace;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:linear-gradient(160deg,var(--void),var(--base));
    color:var(--text); font-family:var(--sans); line-height:1.6;
    padding:3rem 1.5rem; }}
  main {{ max-width:880px; margin:0 auto; }}
  .mark {{ display:inline-block; vertical-align:middle; margin-right:.6rem; }}
  .word {{ font-family:var(--mono); font-weight:700; letter-spacing:.04em; font-size:1.3rem; }}
  h1 {{ font-size:2.4rem; letter-spacing:-0.02em; margin:.6rem 0 .2rem; }}
  .tag {{ font-family:var(--mono); color:var(--muted); margin:0 0 1.6rem; }}
  p {{ color:var(--muted); }}
  code {{ font-family:var(--mono); color:var(--text); }}
  a {{ color:var(--machine); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  table {{ width:100%; border-collapse:collapse; margin:1.5rem 0; font-size:.95rem; }}
  caption {{ text-align:left; color:var(--dim); font-size:.85rem; margin-bottom:.5rem; }}
  th, td {{ text-align:left; padding:.55rem .6rem; border-bottom:1px solid var(--border); }}
  thead th {{ color:var(--dim); font-weight:600; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; }}
  tbody th {{ font-weight:600; }}
  td.v {{ font-family:var(--mono); color:var(--human); }}
  td a {{ font-family:var(--mono); font-size:.85rem; }}
  .card {{ background:var(--elev); border:1px solid var(--border); border-radius:16px;
    padding:1.2rem 1.4rem; margin:1.5rem 0; }}
  .machine {{ color:var(--machine); }} .human {{ color:var(--human); }}
  footer {{ color:var(--dim); font-family:var(--mono); font-size:.85rem;
    margin-top:2.5rem; border-top:1px solid var(--border); padding-top:1rem;
    display:flex; justify-content:space-between; flex-wrap:wrap; gap:.5rem; }}
</style>
</head>
<body>
<main>
  <p>
    <svg class="mark" width="34" height="30" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path d="M6 42 L6 6 L24 29" stroke="#34D3E8" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M24 29 L42 6 L42 42" stroke="#F5B642" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M24 25.6 L27.4 29 L24 32.4 L20.6 29 Z" fill="#E8EEF6"/>
    </svg><span class="word">MIF</span>
  </p>
  <h1>Ontology Corpus</h1>
  <p class="tag">One model, read the same by a <span class="human">person</span> and a <span class="machine">parser</span>.</p>
  <p>The central corpus of ontologies for the Modeled Information Format, served here
     at <code>https://mif-spec.dev/ontologies/</code>. Every ontology is one model in
     two forms: the <span class="human">YAML</span> a person reads and the
     <span class="machine">JSON-LD</span> a parser resolves.</p>

  <table>
    <caption>{len(index['ontologies'])} ontologies &middot; canonical URLs track the latest corpus release</caption>
    <thead><tr><th>Ontology</th><th>Version</th><th>Human</th><th>Machine</th></tr></thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>

  <div class="card">
    <p style="margin:.2rem 0;color:var(--text)"><strong>Machine catalog</strong> &mdash;
       <a href="./index.json"><code>index.json</code></a> lists every ontology with its
       canonical and versioned URLs.</p>
    <p style="margin:.4rem 0 0">Pin an immutable release at
       <code>/ontologies/&lt;version&gt;/&lt;name&gt;.ontology.jsonld</code>.
       Corpus releases: {versions}. Aliases: {aliases}.</p>
  </div>

  <footer>
    <span>modeled-information-format/ontologies</span>
    <span>mif-spec.dev</span>
  </footer>
</main>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version", help="corpus release version, e.g. 0.1.0 (no leading v)")
    ap.add_argument("--check", action="store_true", help="verify the mirror is present and current; write nothing")
    args = ap.parse_args()

    version = args.version.lstrip("v")
    if not SEMVER.match(version):
        print(f"error: '{version}' is not a bare X.Y.Z version", file=sys.stderr)
        return 2
    major = version.split(".")[0]
    names = _canonical_names()
    if not names:
        print("error: no canonical *.ontology.{yaml,jsonld} pairs in public/ontologies/", file=sys.stderr)
        return 2

    problems: list[str] = []
    _copy_set(ROOT / version, names, args.check, problems)
    _copy_set(ROOT / "latest", names, args.check, problems)
    _copy_set(ROOT / f"v{major}", names, args.check, problems)

    desired_index = _build_index(version)
    desired_html = _build_html(desired_index)
    index_path = ROOT / "index.json"
    html_path = ROOT / "index.html"

    if args.check:
        actual = json.loads(index_path.read_text()) if index_path.exists() else None
        if actual != desired_index:
            problems.append("index.json is out of date (regenerate by running without --check)")
        if not html_path.exists() or html_path.read_text() != desired_html:
            problems.append("index.html is out of date (regenerate by running without --check)")
        if problems:
            print(f"ontology mirror for {version} is NOT up to date:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 1
        print(f"ontology mirror for {version}: present and current ({len(names)} ontologies)")
        return 0

    index_path.write_text(json.dumps(desired_index, indent=2) + "\n")
    html_path.write_text(desired_html)
    print(f"snapshotted public/ontologies/{version}/, refreshed latest/ and v{major}/, "
          f"updated index.json + index.html ({len(names)} ontologies)")
    print("review and commit the result before tagging the corpus release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
