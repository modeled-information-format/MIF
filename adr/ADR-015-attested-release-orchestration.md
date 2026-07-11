---
title: "Attested Release and Security-Gate Orchestration"
description: "Every published MIF release attaches SLSA build provenance to two reproducible artifacts (source tarball and schema bundle) keyless via Sigstore OIDC; the source tarball additionally carries a CycloneDX SBOM; publication is fail-closed on in-run re-verification; the full quality-gate suite is wired to the org's central reusable workflows, each reference independently SHA-pinned."
type: adr
category: process
tags:
  - release
  - attestation
  - slsa
  - supply-chain
  - ci
  - security
status: accepted
created: 2026-06-27
updated: 2026-07-11
author: MIF Maintainers
project: MIF
technologies:
  - github-actions
  - slsa
  - sigstore
  - sbom
  - semgrep
  - codeql
audience:
  - developers
  - architects
  - maintainers
related:
  - ADR-007-github-raw-urls-for-schema-ids.md
  - ADR-012-okf-conformance-tested-invariant.md
  - ADR-016-versioned-schema-mirror-publication.md
---

# ADR-015: Attested Release and Security-Gate Orchestration

## Status

Accepted (amended 2026-07-11 — see Amendment section)

## Context

### Background and Problem Statement

MIF is a normative specification backed by JSON Schemas that consumers fetch and
pin. Without provenance, a consumer cannot distinguish a legitimate release
artifact from a tampered one, and has no machine-verifiable record of which
workflow produced what artifact at which commit. The need for provenance is not
unique to compiled binaries: a specification tarball and a schema bundle are
equally worth attesting because they are the artifacts consumers pin their
toolchains to.

At the same time, MIF's CI needed a full security-gate suite covering static
analysis, dependency auditing, secret scanning, infrastructure-as-code scanning,
and posture assessment. Building these gates from scratch in the repo would
duplicate work already done org-wide. The org already maintains a set of central
reusable workflows (in `modeled-information-format/.github`) as part of the
attested-delivery architecture adopted across the org. This ADR records the
decision to consume those reusables and to layer an attested release workflow on
top of them.

### Current Limitations Before This Decision

- MIF releases were plain GitHub Releases: no provenance, no SBOM, no
  attestation. Consumers had no machine-verifiable supply-chain signal.
- The CI suite had no SAST, SCA, secrets scanning, IaC/license scanning,
  posture assessment, or DAST coverage.
- No canonical `verify` command existed for consumers to check a downloaded
  artifact against its attested digest.

## Decision Drivers

### Primary Decision Drivers

1. **Consumer verifiability**: Consumers who pin a specific release must be able
   to verify independently that the artifact they downloaded was produced by
   `release.yml` at the tagged commit, with no trust in the transport layer.
2. **Fail-closed publication**: An artifact that fails in-run attestation
   re-verification must never reach the release. The upload step must be gated
   on a passing verify step, not just a passing build step.
3. **Supply-chain correctness for the CI suite itself**: Every Action `uses:`
   reference in every workflow must be pinned to a full 40-character SHA. Using
   the org's central reusables by SHA pin (rather than a mutable tag) enforces
   this for the reusable layer too.

### Secondary Decision Drivers

1. **Reuse over reinvention**: The org's central reusable workflows already
   implement each gate correctly. Wiring MIF's workflows to call them keeps
   gate logic in one place and avoids maintaining parallel copies.
2. **DAST opt-in**: Dynamic analysis requires a live target (`https://mif-spec.dev`),
   so it cannot be a PR gate. A weekly schedule plus `workflow_dispatch` is the
   correct model.
3. **Workflow dispatch as dry-run**: Releasing the wrong version is costly.
   `workflow_dispatch` should exercise the full build/attest/verify cycle
   without uploading, so the pipeline can be validated at any time without
   cutting a release.

## Considered Options

### Option 1: Plain unsigned GitHub Release (status quo)

**Description**: Continue publishing releases as plain tarballs attached to a
GitHub Release, with no provenance or SBOM.

**Advantages**:

- Zero additional workflow complexity.

**Disadvantages**:

- No consumer-verifiable provenance. A compromised artifact is
  indistinguishable from a legitimate one.
- No SBOM; no supply-chain transparency.

**Risk Assessment**:

- **Technical Risk**: High. The release has no integrity signal for consumers
  who pin the artifact.

### Option 2: Attest via bare git tags

**Description**: Trigger the attestation workflow on `push` to tags matching
`v*` rather than on `release: published`.

**Advantages**:

- Simpler trigger; no GitHub Release object required.

**Disadvantages**:

- `release.yml` triggers on `release: published`, which is the correct GitHub
  primitive for attaching assets to a Release object. A bare tag push bypasses
  the Release event and would require either a separate upload step or a
  different trigger, adding complexity with no benefit.
- Misaligns with the org attested-delivery architecture, which is
  release-event-driven.

**Risk Assessment**:

- **Technical Risk**: Medium. Misaligned trigger model; more fragile.

### Option 3: Copy the org's standalone `attest-release.yml` wholesale

**Description**: Copy the org's generic attested-release workflow into the MIF
repo unchanged.

**Advantages**:

- Familiar starting point.

**Disadvantages**:

- The org's generic workflow is oriented toward container images (Docker build,
  image push, image attestation). MIF has no image. Adapting it requires
  stripping the container-specific steps, which means maintaining a fork that
  diverges from the upstream and receives no updates from it.

**Risk Assessment**:

- **Technical Risk**: Medium. Maintenance burden; container assumptions do not
  apply.

### Option 4: MIF-specific attested release workflow consuming org reusables (chosen)

**Description**: Write a `release.yml` scoped to MIF's two artifact types
(source tarball via `git archive`, schema bundle from the committed versioned
mirror at `public/schema/<version>/`), attesting each with SLSA build
provenance (and the source tarball additionally with a CycloneDX SBOM),
keyless via the run's OIDC id-token. Wire
the quality-gate suite to the org's central reusable workflows by SHA pin.
DAST runs on schedule and `workflow_dispatch` only.

**Advantages**:

- Purpose-built for MIF's artifact model (no container assumptions).
- Fail-closed: upload is gated on in-run attestation re-verification.
- CI gates reuse tested org implementations; no duplicate logic.
- `workflow_dispatch` provides a safe dry-run path.

**Disadvantages**:

- Requires adding several third-party actions to the org Actions allow-list
  (`aquasecurity/trivy-action`, `ossf/scorecard-action`,
  `zaproxy/action-full-scan`,
  `redhat-plumbers-in-action/differential-shellcheck`).

**Risk Assessment**:

- **Technical Risk**: Low. Each component is independently auditable; the
  fail-closed design prevents unverified artifacts from reaching consumers.

## Decision

MIF adopts a purpose-built attested release workflow (`release.yml`) and wires
the full quality-gate suite to the org's central reusable workflows, each
reference independently pinned to a full 40-character commit SHA (see the
2026-07-11 Amendment for why this ADR no longer names a single shared value).

**Release workflow (`release.yml`):** Triggered on a `v*` tag `push` (upload
path, draft-first — see Amendment) and `workflow_dispatch` (dry-run). Builds
two artifacts:

1. `mif-<version>.tar.gz` (reproducible source tarball via `git archive |
   gzip -n`, deterministic from the commit tree).
2. `mif-schemas-<version>.tar.gz` (the consumer-facing schema bundle assembled
   from the committed versioned mirror at `public/schema/<version>/`; fails
   closed if the mirror is absent for the tagged version, per ADR-016).

Each artifact is attested with SLSA build provenance
(`actions/attest-build-provenance@0f67c3f4856b2e3261c31976d6725780e5e4c373`,
v4.1.1) and the source tarball additionally receives a CycloneDX SBOM
(`anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610`, v0.24.0)
attested via `actions/attest-sbom@c604332985a26aa8cf1bdc465b92731239ec6b9e`
(v4.1.0). All signing is keyless via the run's OIDC id-token (Sigstore). The
signer identity (SAN) is the `release.yml` workflow itself:
`modeled-information-format/MIF/.github/workflows/release.yml`.

Publication is fail-closed and, since the 2026-07-11 Amendment, draft-first:
a `changelog-check` job gates the release job on the tagged version having a
real CHANGELOG section, then the release job creates the GitHub release as a
**draft**, uploads the attested artifacts to that draft only after a
dedicated verify step re-checks each artifact's SLSA provenance and the SBOM
attestation in-run (pinning `--signer-workflow` to `release.yml`), and only
then flips the release to published. A failure in the verify step fails the
job before any public release exists. On `workflow_dispatch`, the verify
step runs but the draft-create/upload/publish steps are skipped (guarded by
`if: github.event_name == 'push'`).

**Quality-gate suite:** Four caller workflows wire to the org's central
reusable workflows, each reference independently pinned to a full
40-character commit SHA and updated via routine bump PRs (see Amendment —
these are no longer, and were never architecturally meant to be, one shared
frozen value):

- `ci.yml` (push and PR to `main` and `develop/v*`): actionlint, pin-check,
  SCA via OSV Scanner, Trivy (IaC and license), Checkov (github\_actions
  framework), secrets scanning (gitleaks and trufflehog), ShellCheck.
- `sast.yml` (push, PR, weekly schedule, `workflow_dispatch`): CodeQL for
  Python and JavaScript/TypeScript, Semgrep.
- `scorecard.yml` (push to `main`, branch-protection-rule changes, weekly
  schedule, `workflow_dispatch`): OpenSSF Scorecard posture assessment with
  `publish-results: true`.
- `dast.yml` (`workflow_dispatch` and weekly schedule only): OWASP ZAP full
  scan against `https://mif-spec.dev`, `fail-action: false` (findings are
  surfaced as reports, not hard failures, because the live target may be
  transiently unavailable).

This is Mode A consumption of the attested-delivery architecture: wiring
MIF's own CI to call the org's reusable gates, not re-implementing them.

## Consequences

### Positive

1. **Consumer-verifiable releases**: Any consumer can independently verify a
   downloaded artifact with a single command (see Implementation below). No
   trust in the transport layer is required.
2. **Fail-closed supply chain**: The upload step cannot execute unless
   in-run re-verification passes. A compromised or misattributed attestation
   fails the verify step and blocks publication.
3. **Full gate coverage with no duplicate logic**: SAST (CodeQL + Semgrep),
   SCA, secrets, IaC/license, Checkov, ShellCheck, Scorecard, and DAST are all
   wired and maintained centrally.
4. **Safe dry-run path**: `workflow_dispatch` lets the release pipeline be
   exercised at any time without cutting a version.

### Negative

1. **Allow-list additions**: The org Actions allow-list must include
   `aquasecurity/trivy-action`, `ossf/scorecard-action`,
   `zaproxy/action-full-scan`, and
   `redhat-plumbers-in-action/differential-shellcheck`. This is an org-level
   policy change with a one-time review cost.
2. **DAST is not a PR gate**: Because ZAP requires a running target, DAST
   cannot block a pull request. Regressions detectable only by dynamic
   analysis will not surface until after the site is live.

### Neutral

1. **Org pin SHA must be updated on reusable workflow changes**: Callers pin
   the org reusables to a specific commit SHA. When the org updates a reusable
   workflow, MIF must update the SHA in its caller workflows. This is the
   correct supply-chain posture (pinning over floating tags), but it requires
   a deliberate update step.
2. **Schema bundle fail-closed check**: The release workflow fails if
   `public/schema/<version>/` does not exist for the tagged version. This is
   intentional (ADR-016), but it means a tag cannot be published without the
   committed versioned mirror in place.

## Decision Outcome

Every published MIF release (`vX.Y.Z`) is attested. The source tarball and
schema bundle each carry SLSA build provenance and (for the source tarball) a
CycloneDX SBOM, keyless via Sigstore. Publication is fail-closed on in-run
re-verification. The full quality-gate suite (SAST, SCA, secrets, IaC/license,
Checkov, ShellCheck, Scorecard, DAST) runs via the org's central reusable
workflows, SHA-pinned.

### Implementation

**Verify a release artifact (consumer command):**

```bash
gh attestation verify mif-1.0.0.tar.gz \
  --repo modeled-information-format/MIF \
  --signer-workflow modeled-information-format/MIF/.github/workflows/release.yml

gh attestation verify mif-schemas-1.0.0.tar.gz \
  --repo modeled-information-format/MIF \
  --signer-workflow modeled-information-format/MIF/.github/workflows/release.yml
```

**Required-status-check contexts** (format: `<caller-job-id> / <called-job-name>`):

From `ci.yml`: `actionlint / actionlint`, `pin-check / pin-check`,
`sca / osv-scanner`, `trivy / iac-license`, `checkov / iac-policy`,
`secrets / secrets`, `shellcheck / sast-hooks`.

From `sast.yml`: `codeql / analyze`, `semgrep / sast-code`.

From `scorecard.yml`: `scorecard / analysis`.

**Org reusables SHA pin policy:** every reusable-workflow reference is
independently pinned to a full 40-character commit SHA, each updated via its
own routine bump PR as the org's central reusables release new versions —
not one shared value across the caller workflows (see the 2026-07-11
Amendment; the four caller workflows plus `release.yml`'s `changelog-check`
job currently span several distinct pinned SHAs across their combined
reusable-workflow references).

**Workflow files introduced:** `.github/workflows/release.yml`,
`.github/workflows/ci.yml`, `.github/workflows/sast.yml`,
`.github/workflows/scorecard.yml`, `.github/workflows/dast.yml`.

## Related Decisions

- [ADR-007: GitHub Raw URLs for Schema IDs](ADR-007-github-raw-urls-for-schema-ids.md) -- the schema `$id` URIs resolved at `mif-spec.dev` are the same artifacts the schema bundle attests.
- [ADR-012: OKF Conformance as a Tested Invariant](ADR-012-okf-conformance-tested-invariant.md) -- the CI gate suite enforces spec conformance; this ADR extends enforcement to the release artifact layer.
- [ADR-016: Versioned Schema Mirror Publication](ADR-016-versioned-schema-mirror-publication.md) -- the schema bundle artifact (`mif-schemas-<version>.tar.gz`) is the committed versioned mirror required by ADR-016; its absence fails the release workflow.

## Links

- [Org release runbook](https://github.com/modeled-information-format/.github/blob/main/docs/runbooks/release-runbook.md) -- the governing org release process; this ADR's mechanics fit into that broader orchestration.
- [SLSA Build Provenance specification](https://slsa.dev/provenance/v1) -- the predicate type attested by `actions/attest-build-provenance`.
- [CycloneDX SBOM specification](https://cyclonedx.org/specification/overview/) -- the SBOM format generated by `anchore/sbom-action`.
- [OpenSSF Scorecard](https://github.com/ossf/scorecard) -- the posture-assessment tool run by `scorecard.yml`.
- [OWASP ZAP](https://www.zaproxy.org/) -- the dynamic analysis scanner run by `dast.yml`.

## More Information

- **Date:** 2026-06-27
- **Source:** `.github/workflows/release.yml`, `.github/workflows/ci.yml`, `.github/workflows/sast.yml`, `.github/workflows/scorecard.yml`, `.github/workflows/dast.yml`.
- **Related ADRs:** ADR-007, ADR-012, ADR-016

## Amendment

### 2026-07-11 — draft-first publication flow + reusable-pin policy correction

**Publication mechanism (PR #212, merged 2026-07-05):** the original Decision
described `release.yml` triggering on `release: published` and uploading
attested artifacts directly to that already-published release via
`gh release upload`. This repo subsequently enabled **immutable releases**,
under which a published release's assets cannot be appended to after the
fact. The workflow was rebuilt to trigger on a `v*` tag `push` instead, gate
the release job on a new `changelog-check` job (fails closed if the tagged
version has no real CHANGELOG section), and perform draft-create →
verified-upload → publish in a single step ("Create draft release, upload
attested artifacts, publish", guarded by `if: github.event_name == 'push'`)
rather than uploading to an already-public release.

**Rationale for amendment:** the fail-closed invariant this ADR actually
decided — publication never completes ahead of in-run re-verification — is
unaffected and, if anything, strengthened: a failed run under the new flow
leaves no public release at all, where the old model could theoretically
leave a published-but-unattested release momentarily visible. The change was
forced by the immutable-releases setting, not a reconsideration of this
ADR's design; the Decision text above is updated to describe the workflow as
it now runs.

**Reusable-workflow SHA-pin language (same date, discovered during a routine
audit re-verification, not a design change):** the original Decision,
frontmatter `description`, and Implementation section all asserted that
"all four caller workflows" shared one pinned SHA
(`ff8adc6b1267c272beef916af851d9506160354f`) for the org's central reusable
workflows. That was accurate at the 2026-06-27 audit. Since then, eight
independent, ordinary bump PRs (#175, #176, #177, #188, #190, #197, #217,
#221 — two of them, #190 and #197, are each the final hop of a short chain
of superseding bumps to the same reference: shellcheck via #179→#189→#190,
scorecard via #172→#197) moved each reusable-workflow reference to its own
SHA independently — the architecturally correct behavior; this ADR's own
supply-chain concern was always that *every* reference be pinned to a full
SHA, never that they share one value. The prose above is corrected to
describe that policy rather than naming a single value doomed to go stale
on the very next routine bump.

## Audit

Findings cite durable anchors (job id / step `name:` / trigger key / field
name), not raw line numbers — line numbers across the five
`.github/workflows/*.yml` files this ADR spans (`release.yml`, `ci.yml`,
`sast.yml`, `scorecard.yml`, `dast.yml`) shift on every step added, removed,
or reordered, and `release.yml` itself was restructured twice since the
2026-06-27 audit (the SLSA action's v4.1.1 bump; the draft-first
publication rewrite, see Amendment above). `grep -n` for the quoted anchor
text (a job id or a step `name:` string) to find its current line in the
relevant workflow file.

### 2026-06-27

**Audited revision:** `53a0d8924ef292ce286b87fd07edc830f6776700`

**Status:** Compliant

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| `release.yml` triggers on `release: published` (upload) and `workflow_dispatch` (dry-run); upload guarded by `if: github.event_name == 'release'` | `.github/workflows/release.yml` | the `on:` trigger block (`release: types: [published]` + `workflow_dispatch`); step "Upload attested artifacts to the release" guarded by `if: github.event_name == 'release'` | compliant (at this revision — see Amendment for the 2026-07-05 rebuild) |
| Source tarball built via `git archive` piped to `gzip -n` (reproducible); schema bundle assembled from `public/schema/${VERSION}/` with fail-closed check | `.github/workflows/release.yml` | job `attest-release`, steps "Build reproducible source tarball" and "Build schema bundle (the consumer-facing versioned mirror)" | compliant |
| SLSA provenance attested via `actions/attest-build-provenance@a2bbfa25375fe432b6a289bc6b6cd05ecd0c4c32` over both artifacts | `.github/workflows/release.yml` | job `attest-release`, step "Attest build provenance (SLSA) for both artifacts" | compliant (at this revision — action bumped to v4.1.1 since, see Amendment) |
| CycloneDX SBOM generated by `anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610` and attested via `actions/attest-sbom@c604332985a26aa8cf1bdc465b92731239ec6b9e` | `.github/workflows/release.yml` | job `attest-release`, steps "Generate CycloneDX SBOM (source tree)" and "Attest SBOM against the source tarball" | compliant |
| In-run verify step re-checks SLSA provenance (`--predicate-type https://slsa.dev/provenance/v1`) for both artifacts and SBOM (`--predicate-type https://cyclonedx.org/bom`) for the source tarball only, before upload | `.github/workflows/release.yml` | job `attest-release`, step "Verify attestations (fail-closed, before publish)" | compliant |
| Signer identity pinned to `modeled-information-format/MIF/.github/workflows/release.yml` via `--signer-workflow` | `.github/workflows/release.yml` | job `attest-release`, step "Verify attestations (fail-closed, before publish)", the `SIGNER=` assignment | compliant |
| All four caller workflows pin the org reusables at `ff8adc6b1267c272beef916af851d9506160354f` | `.github/workflows/ci.yml`, `sast.yml`, `scorecard.yml`, `dast.yml` | every job's `uses: modeled-information-format/.github/...` reusable-workflow reference | compliant (at this revision — since diverged into multiple independent pins via routine bumps, see Amendment) |
| DAST (`dast.yml`) is opt-in: `workflow_dispatch` and weekly schedule only; no push/PR trigger | `.github/workflows/dast.yml` | the `on:` trigger block | compliant |
| `ci.yml` gates: actionlint, pin-check, SCA (OSV), Trivy (IaC), Checkov (github_actions), secrets, ShellCheck | `.github/workflows/ci.yml` | job ids `actionlint`, `pin-check`, `sca`, `trivy`, `checkov`, `secrets`, `shellcheck` | compliant |
| `sast.yml` gates: CodeQL (python,javascript-typescript), Semgrep; runs on push, PR, weekly schedule, dispatch | `.github/workflows/sast.yml` | job ids `codeql`, `semgrep`; the `on:` trigger block | compliant |
| `scorecard.yml`: Scorecard with `publish-results: true`; runs on push to main, branch-protection-rule, weekly schedule, dispatch | `.github/workflows/scorecard.yml` | job `scorecard`, the `on:` trigger block, `with: publish-results: true` | compliant |

**Summary:** The attested release workflow produces two reproducible artifacts,
attests each with SLSA build provenance keyless via Sigstore (source tarball
additionally carries a CycloneDX SBOM), and gates publication on in-run
re-verification. The quality-gate suite covers SAST, SCA, secrets,
IaC/license, Checkov, ShellCheck, Scorecard, and DAST via the org's central
reusable workflows. All workflow `uses:` references are pinned to full
40-character SHAs.

**Action Required:** None.

### 2026-07-11

**Audited revision:** `4876ac6fe675f797509e7fedf6736253b8d95dea`

**Status:** Compliant. Two of this ADR's own prose claims had drifted from
reality (release publication mechanism; single-shared-SHA claim) — both
corrected in this same PR's Amendment section and Decision-text updates
above, not deferred. Nothing found here was ever a CI defect.

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| `release.yml` trigger and publication mechanics | `.github/workflows/release.yml` | the `on:` trigger block (`push: tags: ["v*"]` + `workflow_dispatch`); step "Create draft release, upload attested artifacts, publish" guarded by `if: github.event_name == 'push'`; job `changelog-check` gating `attest-release` via `needs:` | compliant — Decision text updated to match (Amendment) |
| Source tarball / schema bundle build steps | `.github/workflows/release.yml` | job `attest-release`, steps "Verify schema mirror is present and byte-identical (fail-closed)", "Build reproducible source tarball", "Build schema bundle (the consumer-facing versioned mirror)" | compliant — a dedicated upstream fail-closed step was added; same guarantee, stronger placement |
| SLSA provenance attestation | `.github/workflows/release.yml` | job `attest-release`, step "Attest build provenance (SLSA) for both artifacts" | compliant — action bumped to `0f67c3f4856b2e3261c31976d6725780e5e4c373` (v4.1.1); Decision-text SHA updated to match |
| CycloneDX SBOM generation/attestation | `.github/workflows/release.yml` | job `attest-release`, steps "Generate CycloneDX SBOM (source tree)", "Attest SBOM against the source tarball" | compliant, unchanged |
| In-run fail-closed verify step | `.github/workflows/release.yml` | job `attest-release`, step "Verify attestations (fail-closed, before publish)" | compliant, unchanged |
| Signer identity pin | `.github/workflows/release.yml` | job `attest-release`, step "Verify attestations (fail-closed, before publish)", the `SIGNER=` assignment | compliant, unchanged |
| Org-reusable SHA pin policy across caller workflows | `.github/workflows/ci.yml`, `sast.yml`, `scorecard.yml`, `dast.yml`, `release.yml` | every job's `uses: modeled-information-format/.github/...` reusable-workflow reference | compliant — every reference remains individually pinned to a full 40-character SHA (8 distinct SHAs currently pin the 12 reusable-workflow references across these five files, via 8 independent routine bump PRs plus #212's new `changelog-check` reference); Decision/Implementation text corrected to describe the policy rather than a single shared value (Amendment) |
| DAST opt-in trigger | `.github/workflows/dast.yml` | the `on:` trigger block | compliant, unchanged |
| `ci.yml` gates (job set) | `.github/workflows/ci.yml` | job ids `actionlint`, `pin-check`, `sca`, `trivy`, `checkov`, `secrets`, `shellcheck` | compliant, unchanged |
| `sast.yml` gates (job set) | `.github/workflows/sast.yml` | job ids `codeql`, `semgrep`; the `on:` trigger block | compliant, unchanged |
| `scorecard.yml` gate | `.github/workflows/scorecard.yml` | job `scorecard`, the `on:` trigger block, `with: publish-results: true` | compliant, unchanged |

**Summary:** Re-verified every 2026-06-27 finding against the current
revision. The core invariants this ADR decided — keyless SLSA + SBOM
attestation of both artifacts, fail-closed in-run re-verification gating
publication, and full quality-gate coverage via org reusables — all still
hold and are, if anything, executed more robustly than at the original
audit (draft-first publication closes a gap the original design didn't
anticipate, forced by this repo's later adoption of immutable releases).
Two of this ADR's own prose claims had drifted: the release-trigger/
publication-mechanism description (PR #212, 2026-07-05, draft-first flow)
and the "one shared reusable-workflow SHA pin" claim (eight independent
bump PRs — #175, #176, #177, #188, #190, #197, #217, #221, two of them the
final hop of a short superseding-bump chain — since diverged it into 8
distinct SHAs across the 12 reusable-workflow references spanning all five
workflow files, counting #212's new `changelog-check` reference). Both
corrected in this same PR via a formal `## Amendment` section rather than
silently rewritten in place, per this repo's Status Values convention.
Related ADRs (ADR-007, ADR-012, ADR-016) checked: ADR-007 is amended but
its ADR-015 citation already reflects the amended state; ADR-012 was
amended the same day (2026-07-11, `validate-ontologies` narrowing) but
that amendment doesn't touch anything ADR-015 cites; ADR-016 unamended.

**Action Required:** None — both discrepancies found during this audit are
resolved in this same PR (see Amendment section).
