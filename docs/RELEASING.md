---
diataxis_type: how-to
---

# Releasing MIF

This runbook covers cutting an attested MIF release from start to finish. Follow
the sections in order; each step has a verification checkpoint.

## Overview

MIF releases are GitHub-Release-driven. The `release.yml` workflow fires on the
`release: published` event -- a published GitHub Release named `vX.Y.Z` is the
trigger, not a bare `git push --tags`. Pushing a tag alone does not fire
attestation and does not upload artifacts.

Every published release produces two attested artifacts:

- `mif-<version>.tar.gz` -- reproducible source tarball (`git archive` of the
  tag tree, timestamp-stripped with `gzip -n`)
- `mif-schemas-<version>.tar.gz` -- consumer-facing JSON Schema bundle; the
  immutable versioned mirror published at `https://mif-spec.dev/schema/<version>/`

Both artifacts carry SLSA build provenance and a CycloneDX SBOM, signed keyless
via the run's OIDC identity token. The signer identity bound to every attestation
is the release workflow:

```
modeled-information-format/MIF/.github/workflows/release.yml
```

Publication is fail-closed: the upload step runs only after each attestation is
re-verified in-run. If verification fails the job fails and nothing is uploaded.

---

## 1. Pre-release checklist (on the develop/v\* branch)

Work on `develop/v1.0.0` (or the appropriate `develop/vX.Y.Z` branch). Do not
target `main` directly until the cutover step.

### 1a. Bump VERSION.json

Edit `VERSION.json` at the repo root. Set `specification` and each schema version
to the new release version string (bare semver, no leading `v`):

```json
{
  "specification": "X.Y.Z",
  "schemas": {
    "mif": "X.Y.Z",
    "citation": "X.Y.Z",
    "ontology": "X.Y.Z",
    "entity-reference": "X.Y.Z"
  }
}
```

### 1b. Roll CHANGELOG.md

Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Insert a
new dated header directly under `## [Unreleased]` -- do not overwrite the
Unreleased section, move its items into the new header:

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
...

### Changed
...
```

### 1c. Snapshot the schema mirror

Run the snapshot script to create the immutable per-version schema mirror under
`public/schema/X.Y.Z/` and refresh the `latest/` and `vN/` aliases. Pass the
bare version string (no leading `v`):

```bash
python3 scripts/snapshot-schema-version.py X.Y.Z
```

The script copies the files listed in `MIRRORED_FILES` from `public/schema/` into
`public/schema/X.Y.Z/`, updates `public/schema/latest/`, updates
`public/schema/vN/` (where N is the major version), and writes the updated
`public/schema/index.json`. Review the diff, then commit everything:

```bash
git add public/schema/ VERSION.json CHANGELOG.md
git commit -m "chore: release vX.Y.Z"
```

### 1d. Verify the mirror is current

After committing, confirm the snapshot check passes with no drift:

```bash
python3 scripts/snapshot-schema-version.py X.Y.Z --check
```

Expected output: `schema mirror for X.Y.Z: present and current`

If it reports drift, re-run the script without `--check` and recommit.

### 1e. Confirm CI gates are green

The following workflows must pass on your branch before tagging:

| Workflow | File | Runs on |
|---|---|---|
| Validate MIF Bundles and Schemas | `validate.yml` | push + PR to main, develop/\* |
| Schema Check | `schema-check.yml` | push + PR to main, develop/\*\* |
| CI (supply-chain, secrets, IaC) | `ci.yml` | push + PR to main, develop/v\* |
| SAST (CodeQL + Semgrep) | `sast.yml` | push + PR to main, develop/v\* |

Check branch status on GitHub or with:

```bash
gh pr checks <PR-number>
```

All four must be green before proceeding. Do not tag a failing tree.

---

## 2. Dry-run

Trigger `release.yml` via `workflow_dispatch` to verify the full build, attest,
and in-run verify pipeline without uploading anything.

```bash
gh workflow run release.yml --ref develop/vX.Y.Z
```

To test against an existing release tag (re-attestation smoke test):

```bash
gh workflow run release.yml --ref main \
  --field tag=v0.1.0
```

The `workflow_dispatch` path derives the artifact names from the supplied tag (or
a `dryrun-<sha>` placeholder when no tag is given), runs the full attest-verify
sequence, and then skips the upload step (`if: github.event_name == 'release'`
guards it). A successful dry-run confirms the pipeline is intact before you cut
the real release.

Monitor the run:

```bash
gh run watch
```

Confirm the final step `Upload attested artifacts to the release` was skipped, and
that `Verify attestations (fail-closed, before publish)` passed.

---

## 3. Cut the release

### 3a. v1.0.0 cutover: merge develop/v1.0.0 into main

For the `v1.0.0` release the normative branch is `develop/v1.0.0`. The deployed
branch is `main` -- `deploy.yml` publishes `mif-spec.dev` on every push to
`main`. Before publishing the GitHub Release, land the bump on main:

1. Open a PR from `develop/v1.0.0` targeting `main`.
2. Confirm all required CI checks pass on the PR.
3. Merge the PR (squash or merge commit, per project convention).

For subsequent releases (patch/minor on main), there is no separate cutover step;
work directly from the release branch or main.

### 3b. Publish the GitHub Release

Create the GitHub Release at the commit that carries the version bump. The release
name must be `vX.Y.Z` (with the leading `v`):

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes-file <(sed -n '/^## \[X.Y.Z\]/,/^## \[/p' CHANGELOG.md | head -n -1) \
  --target main
```

Or create it in the GitHub UI: go to Releases, click "Draft a new release", set
the tag to `vX.Y.Z`, the target branch to `main`, fill the release notes from
CHANGELOG.md, and click "Publish release" (not "Save draft" -- draft does not
trigger the workflow).

Publishing the release fires `release.yml`. The workflow:

1. Resolves the version from the tag name.
2. Checks out the repo at that tag.
3. Builds `mif-X.Y.Z.tar.gz` (reproducible `git archive`, timestamp-stripped).
4. Builds `mif-schemas-X.Y.Z.tar.gz` from `public/schema/X.Y.Z/` -- fails closed
   if the directory is absent.
5. Generates a CycloneDX SBOM (`mif-X.Y.Z.sbom.cdx.json`).
6. Attests SLSA build provenance for both tarballs.
7. Attests the SBOM against the source tarball.
8. Re-verifies every attestation in-run with `--signer-workflow` pinned to this
   workflow.
9. Uploads all three artifacts to the release.

After the workflow completes, the release page will show:

- `mif-X.Y.Z.tar.gz`
- `mif-schemas-X.Y.Z.tar.gz`
- `mif-X.Y.Z.sbom.cdx.json`

---

## 4. What gets attested

| Artifact | Contents | Attestation types |
|---|---|---|
| `mif-X.Y.Z.tar.gz` | Reproducible source tarball of the tagged tree | SLSA build provenance + CycloneDX SBOM |
| `mif-schemas-X.Y.Z.tar.gz` | JSON Schema bundle from `public/schema/X.Y.Z/` | SLSA build provenance |

The SLSA provenance predicate type is `https://slsa.dev/provenance/v1`. The SBOM
predicate type is `https://cyclonedx.org/bom`. The signer identity (certificate
SAN) for all attestations is:

```
https://github.com/modeled-information-format/MIF/.github/workflows/release.yml@refs/tags/vX.Y.Z
```

---

## 5. Verifying a release

Any consumer can verify the attestations independently using the `gh` CLI. Run
these commands after downloading the artifacts:

```bash
gh release download vX.Y.Z \
  --repo modeled-information-format/MIF \
  --pattern 'mif-*.tar.gz'
```

Verify the source tarball:

```bash
gh attestation verify mif-X.Y.Z.tar.gz \
  --repo modeled-information-format/MIF \
  --signer-workflow modeled-information-format/MIF/.github/workflows/release.yml \
  --predicate-type https://slsa.dev/provenance/v1
```

Verify the schema bundle:

```bash
gh attestation verify mif-schemas-X.Y.Z.tar.gz \
  --repo modeled-information-format/MIF \
  --signer-workflow modeled-information-format/MIF/.github/workflows/release.yml \
  --predicate-type https://slsa.dev/provenance/v1
```

Both commands exit 0 on success and print the verified predicate. A non-zero exit
means verification failed; do not use the artifact.

To also inspect the SBOM attestation on the source tarball, add
`--predicate-type https://cyclonedx.org/bom` to the source tarball verify
command.

---

## 6. Security gates

### Gate workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `validate.yml` | push + PR to `main`, `develop/**`, `release/**` | OKF conformance, schema validation, Astro build, ontology checks |
| `schema-check.yml` | push + PR to `main`, `develop/**`, `release/**` | JSON Schema 2020-12 compilation, JSON-LD parse, mirror alias consistency |
| `ci.yml` | push + PR to `main`, `develop/v*` | actionlint, SHA pin-check, SCA (OSV), Trivy IaC, Checkov, secrets scan, ShellCheck |
| `sast.yml` | push + PR to `main`, `develop/v*`; weekly schedule | CodeQL (Python + TypeScript), Semgrep |
| `scorecard.yml` | push to `main`; branch-protection changes; weekly schedule | OpenSSF Scorecard posture assessment |
| `dast.yml` | `workflow_dispatch`; weekly schedule (Tuesdays 06:23 UTC) | OWASP ZAP full scan against `https://mif-spec.dev` (opt-in, not a PR gate) |

### Required status check context naming

When registering required status checks for branch protection, use the form:

```
<caller-job-id> / <called-job-name>
```

For the reusable-workflow gates in `ci.yml`, for example:

- `actionlint / actionlint`
- `pin-check / pin-check`
- `sca / osv-scanner`

The caller job id is the key under `jobs:` in the calling workflow file; the
called job name is the `name:` field in the reusable workflow. A mismatch between
these two identifiers -- or a path filter that prevents the check from running on
a given PR -- will block all merges to that branch indefinitely.

DAST is opt-in and is not a required PR gate. Trigger it manually before a major
release:

```bash
gh workflow run dast.yml --field target-url=https://mif-spec.dev
```

---

## 7. Post-release checks

After `release.yml` completes and `deploy.yml` finishes deploying the updated
`main` branch, verify the schema mirrors resolve correctly:

```bash
# Exact version mirror (immutable)
curl -sf https://mif-spec.dev/schema/X.Y.Z/mif.schema.json | python3 -m json.tool > /dev/null

# Moving latest alias
curl -sf https://mif-spec.dev/schema/latest/mif.schema.json | python3 -m json.tool > /dev/null

# Machine-readable catalog
curl -sf https://mif-spec.dev/schema/index.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['specVersion'])"
```

The catalog should report `X.Y.Z` as `specVersion`.

Confirm the release page shows all three artifacts with no errors, then close any
release-tracking issue and back-merge any remaining changes from `main` into
active development branches as needed.
