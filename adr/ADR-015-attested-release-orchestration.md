---
title: "Attested Release and Security-Gate Orchestration"
description: "Every published MIF release attaches SLSA build provenance to two reproducible artifacts (source tarball and schema bundle) keyless via Sigstore OIDC; the source tarball additionally carries a CycloneDX SBOM; publication is fail-closed on in-run re-verification; the full quality-gate suite is wired to the org's central reusable workflows, SHA-pinned at ff8adc6b1267c272beef916af851d9506160354f."
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
updated: 2026-06-27
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

Accepted

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
the full quality-gate suite to the org's central reusable workflows, SHA-pinned
at `ff8adc6b1267c272beef916af851d9506160354f`.

**Release workflow (`release.yml`):** Triggered on `release: published` (upload
path) and `workflow_dispatch` (dry-run). Builds two artifacts:

1. `mif-<version>.tar.gz` (reproducible source tarball via `git archive |
   gzip -n`, deterministic from the commit tree).
2. `mif-schemas-<version>.tar.gz` (the consumer-facing schema bundle assembled
   from the committed versioned mirror at `public/schema/<version>/`; fails
   closed if the mirror is absent for the tagged version, per ADR-016).

Each artifact is attested with SLSA build provenance
(`actions/attest-build-provenance@a2bbfa25375fe432b6a289bc6b6cd05ecd0c4c32`,
v4.1.0) and the source tarball additionally receives a CycloneDX SBOM
(`anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610`, v0.24.0)
attested via `actions/attest-sbom@c604332985a26aa8cf1bdc465b92731239ec6b9e`
(v4.1.0). All signing is keyless via the run's OIDC id-token (Sigstore). The
signer identity (SAN) is the `release.yml` workflow itself:
`modeled-information-format/MIF/.github/workflows/release.yml`.

Publication is fail-closed: the upload step (`gh release upload`) runs only
after a dedicated verify step re-checks each artifact's SLSA provenance and
the SBOM attestation in-run, pinning `--signer-workflow` to `release.yml`. A
failure in the verify step fails the job, so the upload step never executes
unverified. On `workflow_dispatch`, the verify step runs but the upload step
is skipped (guarded by `if: github.event_name == 'release'`).

**Quality-gate suite:** Four caller workflows wire to the org central reusable
workflows at `ff8adc6b1267c272beef916af851d9506160354f`:

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

**Org reusables SHA pin:** `ff8adc6b1267c272beef916af851d9506160354f`
(all four caller workflows pin this SHA).

**Workflow files introduced:** `.github/workflows/release.yml`,
`.github/workflows/ci.yml`, `.github/workflows/sast.yml`,
`.github/workflows/scorecard.yml`, `.github/workflows/dast.yml`.

## Related Decisions

- [ADR-007: GitHub Raw URLs for Schema IDs](ADR-007-github-raw-urls-for-schema-ids.md) -- the schema `$id` URIs resolved at `mif-spec.dev` are the same artifacts the schema bundle attests.
- [ADR-012: OKF Conformance as a Tested Invariant](ADR-012-okf-conformance-tested-invariant.md) -- the CI gate suite enforces spec conformance; this ADR extends enforcement to the release artifact layer.
- [ADR-016: Versioned Schema Mirror Publication](ADR-016-versioned-schema-mirror-publication.md) -- the schema bundle artifact (`mif-schemas-<version>.tar.gz`) is the committed versioned mirror required by ADR-016; its absence fails the release workflow.

## Links

- [SLSA Build Provenance specification](https://slsa.dev/provenance/v1) -- the predicate type attested by `actions/attest-build-provenance`.
- [CycloneDX SBOM specification](https://cyclonedx.org/specification/overview/) -- the SBOM format generated by `anchore/sbom-action`.
- [OpenSSF Scorecard](https://github.com/ossf/scorecard) -- the posture-assessment tool run by `scorecard.yml`.
- [OWASP ZAP](https://www.zaproxy.org/) -- the dynamic analysis scanner run by `dast.yml`.

## More Information

- **Date:** 2026-06-27
- **Source:** `.github/workflows/release.yml`, `.github/workflows/ci.yml`, `.github/workflows/sast.yml`, `.github/workflows/scorecard.yml`, `.github/workflows/dast.yml`.
- **Related ADRs:** ADR-007, ADR-012, ADR-016

## Audit

### 2026-06-27

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| `release.yml` triggers on `release: published` (upload) and `workflow_dispatch` (dry-run); upload guarded by `if: github.event_name == 'release'` | `.github/workflows/release.yml` | L28-L37, L155-L165 | compliant |
| Source tarball built via `git archive` piped to `gzip -n` (reproducible); schema bundle assembled from `public/schema/${VERSION}/` with fail-closed check | `.github/workflows/release.yml` | L75-L109 | compliant |
| SLSA provenance attested via `actions/attest-build-provenance@a2bbfa25375fe432b6a289bc6b6cd05ecd0c4c32` over both artifacts | `.github/workflows/release.yml` | L119-L125 | compliant |
| CycloneDX SBOM generated by `anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610` and attested via `actions/attest-sbom@c604332985a26aa8cf1bdc465b92731239ec6b9e` | `.github/workflows/release.yml` | L111-L130 | compliant |
| In-run verify step re-checks SLSA provenance (`--predicate-type https://slsa.dev/provenance/v1`) for both artifacts and SBOM (`--predicate-type https://cyclonedx.org/bom`) for the source tarball only, before upload | `.github/workflows/release.yml` | L132-L153 | compliant |
| Signer identity pinned to `modeled-information-format/MIF/.github/workflows/release.yml` via `--signer-workflow` | `.github/workflows/release.yml` | L141 | compliant |
| All four caller workflows pin the org reusables at `ff8adc6b1267c272beef916af851d9506160354f` | `.github/workflows/ci.yml`, `sast.yml`, `scorecard.yml`, `dast.yml` | all `uses:` lines | compliant |
| DAST (`dast.yml`) is opt-in: `workflow_dispatch` and weekly schedule only; no push/PR trigger | `.github/workflows/dast.yml` | L7-L17 | compliant |
| `ci.yml` gates: actionlint, pin-check, SCA (OSV), Trivy (IaC), Checkov (github\_actions), secrets, ShellCheck | `.github/workflows/ci.yml` | L18-L82 | compliant |
| `sast.yml` gates: CodeQL (python,javascript-typescript), Semgrep; runs on push, PR, weekly schedule, dispatch | `.github/workflows/sast.yml` | L19-L40 | compliant |
| `scorecard.yml`: Scorecard with `publish-results: true`; runs on push to main, branch-protection-rule, weekly schedule, dispatch | `.github/workflows/scorecard.yml` | L18-L28 | compliant |

**Summary:** The attested release workflow produces two reproducible artifacts,
attests each with SLSA build provenance keyless via Sigstore (source tarball
additionally carries a CycloneDX SBOM), and gates publication on in-run
re-verification. The quality-gate
suite covers SAST, SCA, secrets, IaC/license, Checkov, ShellCheck, Scorecard,
and DAST via the org's SHA-pinned central reusable workflows. All workflow
`uses:` references are pinned to full 40-character SHAs.

**Action Required:** None.
