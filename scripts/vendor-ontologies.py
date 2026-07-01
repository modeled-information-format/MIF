#!/usr/bin/env python3
"""Vendor the ontology corpus from a signed, attested `ontologies` release.

Replaces the hand-run `snapshot-ontology-version.py` commit step (ADR-019 /
ontologies ADR-0004): at deploy time, fetch the `ontologies` repo's signed
`ontologies-X.Y.Z.tar.gz` release tarball for a given tag, run `gh
attestation verify` fail-closed against it (the exact checks that repo's own
`release.yml` `verify` job runs), and untar the verified `ontologies/`
subtree into `public/ontologies/`. No ontology content is authored in this
repo (per ADR-018): every one of the 20 ontologies, including `mif-base` and
`shared-traits`, is vendored here, none recomputed.

The served `index.json` core (`{version, file, sha256, extends}` per
ontology) comes verbatim from the attested tarball's own `ontologies/index.json`
(built by that repo's `gen-ontology-index.sh`) -- this script only enriches
it with `aliases`, `versions`, and per-entry discovery URLs, mirroring what
`snapshot-ontology-version.py` used to compute locally.

On any verification failure, this script exits non-zero and writes nothing:
the deploy job fails before `astro build`/`deploy-pages` run, so the
previously-published Pages site stays live (keep-last-good).

Usage:
    python3 scripts/vendor-ontologies.py [ref]
        ref: an `ontologies` repo release tag (e.g. v0.2.1) or bare version
             (e.g. 0.2.1). Defaults to that repo's latest release.

Requires: `gh` (authenticated; a public repo needs no token for read access,
but `gh` must be present and logged in enough to avoid interactive prompts --
GITHUB_TOKEN in CI satisfies this).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

OWNER = "modeled-information-format"
REPO = f"{OWNER}/ontologies"
NAME = "ontologies"
FINAL_ROOT = Path(__file__).resolve().parent.parent / "public" / "ontologies"
# ROOT is reassigned in main() to a staging directory for the duration of the
# build, then atomically swapped into FINAL_ROOT only on full success -- see
# main()'s docstring note on keep-last-good. Module-level functions below
# read the current value of ROOT, not FINAL_ROOT, so they operate on
# whichever directory is currently being built.
ROOT = FINAL_ROOT
CANONICAL_BASE = "https://mif-spec.dev/ontologies/"
SEAM_WORKFLOW = f"{OWNER}/.github/.github/workflows/reusable-attest-scan.yml"
VEX_SIGNER_WORKFLOW = f"{OWNER}/.github/.github/workflows/reusable-vex.yml"

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

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


def run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"vendor-ontologies: command failed: {' '.join(args)}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(1)
    return result.stdout


def gh_json(*args: str):
    return json.loads(run("gh", *args))


def resolve_tag(ref: str | None) -> str:
    if ref:
        return ref if ref.startswith("v") else f"v{ref}"
    releases = gh_json(
        "release", "list", "--repo", REPO, "--json", "tagName,isDraft", "--limit", "1"
    )
    if not releases:
        print(f"vendor-ontologies: no releases found in {REPO}", file=sys.stderr)
        raise SystemExit(1)
    return releases[0]["tagName"]


def all_release_tags() -> list[str]:
    releases = gh_json(
        "release", "list", "--repo", REPO, "--json", "tagName,isDraft", "--limit", "100"
    )
    return [r["tagName"] for r in releases if not r["isDraft"]]


def verify_attestations(tarball: Path) -> None:
    """Fail-closed verification -- mirrors ontologies' own release.yml verify job."""
    run("gh", "attestation", "verify", str(tarball), "--repo", REPO,
        "--predicate-type", "https://slsa.dev/provenance/v1")
    run("gh", "attestation", "verify", str(tarball), "--repo", REPO,
        "--predicate-type", "https://cyclonedx.org/bom")
    for predicate in ("sast", "sca", "iac-license"):
        run("gh", "attestation", "verify", str(tarball),
            "--owner", OWNER, "--signer-workflow", SEAM_WORKFLOW,
            "--predicate-type", f"https://modeled-information-format.github.io/attestations/{predicate}/v1")
    run("gh", "attestation", "verify", str(tarball),
        "--owner", OWNER, "--signer-workflow", VEX_SIGNER_WORKFLOW,
        "--predicate-type", "https://openvex.dev/ns/v0.2.0")


def fetch_and_verify(tag: str, dest: Path) -> None:
    """Download tag's release tarball, verify it, extract ontologies/ into dest."""
    version = tag.lstrip("v")
    asset = f"{NAME}-{version}.tar.gz"
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        run("gh", "release", "download", tag, "--repo", REPO, "--pattern", asset, "-D", str(tmp))
        tarball = tmp / asset
        if not tarball.is_file():
            print(f"vendor-ontologies: expected asset {asset} not found in release {tag}", file=sys.stderr)
            raise SystemExit(1)
        verify_attestations(tarball)
        print(f"vendor-ontologies: {tag} -> {asset} verified (SLSA provenance, SBOM, sast/sca/iac-license, VEX)")

        extract_root = tmp / "extracted"
        with tarfile.open(tarball) as tf:
            tf.extractall(extract_root, filter="data")
        # git archive --prefix="ontologies-X.Y.Z/" -> one top-level dir.
        top_dirs = [p for p in extract_root.iterdir() if p.is_dir()]
        if len(top_dirs) != 1:
            print(f"vendor-ontologies: expected exactly one top-level dir in {asset}, found {len(top_dirs)}", file=sys.stderr)
            raise SystemExit(1)
        src = top_dirs[0] / NAME
        if not src.is_dir():
            print(f"vendor-ontologies: {asset} has no {NAME}/ subtree", file=sys.stderr)
            raise SystemExit(1)
        dest.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            shutil.copy2(item, dest / item.name) if item.is_file() else shutil.copytree(item, dest / item.name, dirs_exist_ok=True)


def _semver_key(v: str) -> tuple[int, int, int]:
    a, b, c = v.split(".")
    return (int(a), int(b), int(c))


def _canonical_names() -> list[str]:
    names = []
    for j in sorted(ROOT.glob("*.ontology.jsonld")):
        name = j.name[: -len(".ontology.jsonld")]
        if (ROOT / f"{name}.ontology.yaml").is_file():
            names.append(name)
    return names


def build_index(attested_core: dict, versions: list[str]) -> dict:
    """Enrich the attested {id: {version, file, sha256, extends}} core with
    discovery aliases/URLs. Never recomputes the core fields themselves --
    those come verbatim from the tarball's own index.json."""
    versions = sorted(set(versions), key=_semver_key)
    newest = versions[-1]
    majors = sorted({v.split(".")[0] for v in versions}, key=int)
    aliases = {"latest": newest}
    for m in majors:
        aliases[f"v{m}"] = max((v for v in versions if v.split(".")[0] == m), key=_semver_key)

    names = _canonical_names()
    ontologies = {}
    for name in names:
        core = attested_core.get(name, {})
        versioned = {}
        for alias in (*versions, "latest", *(f"v{m}" for m in majors)):
            if (ROOT / alias / f"{name}.ontology.jsonld").is_file():
                versioned[alias] = f"{CANONICAL_BASE}{alias}/{name}.ontology.jsonld"
        ontologies[name] = {
            **core,
            "canonical": f"{CANONICAL_BASE}{name}.ontology.jsonld",
            "yaml": f"{CANONICAL_BASE}{name}.ontology.yaml",
            "versioned": versioned,
        }

    return {**INDEX_META, "versions": versions, "aliases": aliases, "ontologies": ontologies}


def build_html(index: dict) -> str:
    """Ported from snapshot-ontology-version.py's _build_html."""
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


def _build(tag: str, all_tags: list[str]) -> dict:
    """Do the actual fetch/verify/compose work against the current ROOT
    (a staging directory during main()'s real run). Raises SystemExit on any
    failure; the caller is responsible for never letting a partial staging
    directory reach FINAL_ROOT."""
    fetched_index_by_tag: dict[str, dict] = {}
    for t in all_tags:
        version = t.lstrip("v")
        dest = ROOT / version if t != tag else ROOT
        fetch_and_verify(t, dest)
        idx_path = dest / "index.json"
        if not idx_path.is_file():
            if t == tag:
                # The target (usually latest) release is the one this script's
                # index.json contract depends on -- it must have one.
                print(f"vendor-ontologies: target release {t}'s tarball has no ontologies/index.json", file=sys.stderr)
                raise SystemExit(1)
            # An older tag predating the index.json registry (ADR-0002/#5).
            # Its raw ontology files still get mirrored under
            # public/ontologies/<version>/ above; it just can't contribute to
            # the aggregate versions/aliases list below.
            print(f"vendor-ontologies: {t} predates ontologies/index.json -- mirrored raw files, excluded from versions/aliases")
            continue
        fetched_index_by_tag[version] = json.loads(idx_path.read_text())

    # Refresh latest/ and vMAJOR/ as copies of the newest tag's canonical
    # *.ontology.{yaml,jsonld} pairs only -- NOT a copytree of ROOT itself,
    # which now also contains sibling version/alias subdirectories (copying
    # a directory into its own descendant is invalid and would recurse).
    latest_version = tag.lstrip("v")
    canonical_files = [
        p for p in ROOT.iterdir()
        if p.is_file() and (p.name.endswith(".ontology.yaml") or p.name.endswith(".ontology.jsonld"))
    ]
    for alias_dir in ("latest", f"v{latest_version.split('.')[0]}"):
        dst = ROOT / alias_dir
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        for f in canonical_files:
            shutil.copy2(f, dst / f.name)

    attested_core = fetched_index_by_tag[latest_version]["ontologies"]
    versions = list(fetched_index_by_tag.keys())
    index = build_index(attested_core, versions)
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    (ROOT / "index.html").write_text(build_html(index))
    return index


def main() -> int:
    global ROOT
    ref = sys.argv[1] if len(sys.argv) > 1 else None

    tag = resolve_tag(ref)
    all_tags = all_release_tags()
    if tag not in all_tags:
        print(f"vendor-ontologies: resolved tag {tag} not found among releases: {all_tags}", file=sys.stderr)
        return 1
    # Historical version axis: every release tag gets its own immutable
    # public/ontologies/<version>/ mirror. Cheap while the tag count is
    # small; consider actions/cache keyed by tag if this list grows large.
    print(f"vendor-ontologies: {len(all_tags)} release tag(s) to vendor: {all_tags}")

    # Build entirely in a staging directory so a failure partway through
    # (e.g. an older historical tag's attestation fails to verify after the
    # target tag already succeeded) never leaves FINAL_ROOT in a mixed state
    # -- new canonical files paired with a stale index.json, or vice versa.
    # FINAL_ROOT is touched only by the atomic-ish swap at the very end, on
    # complete success; the deploy job's own directory reads from FINAL_ROOT
    # ("public/ontologies") and never sees a half-built tree.
    staging = FINAL_ROOT.parent / ".ontologies-staging"
    if staging.exists():
        shutil.rmtree(staging)
    ROOT = staging
    try:
        index = _build(tag, all_tags)
    except SystemExit:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    except Exception as exc:  # noqa: BLE001 -- fail-closed on any unexpected error too
        print(f"vendor-ontologies: unexpected error, discarding staged build: {exc}", file=sys.stderr)
        shutil.rmtree(staging, ignore_errors=True)
        return 1

    backup = FINAL_ROOT.parent / ".ontologies-previous"
    if backup.exists():
        shutil.rmtree(backup)
    if FINAL_ROOT.exists():
        FINAL_ROOT.rename(backup)
    staging.rename(FINAL_ROOT)
    shutil.rmtree(backup, ignore_errors=True)
    ROOT = FINAL_ROOT

    versions = index["versions"]
    print(f"vendor-ontologies: vendored {len(index['ontologies'])} ontologies at {tag}, "
          f"{len(versions)} historical version(s) mirrored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
