---
title: "OKF Conformance Enforced as a Tested CI Invariant"
description: "MIF enforces OKF conformance, lossless round-trip, schema validity, and ontology/namespace integrity as gating CI checks rather than documentation promises."
type: adr
category: process
tags:
  - okf
  - conformance
  - ci
  - validation
  - quality-gate
status: accepted
created: 2026-06-18
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - github-actions
  - python
  - ajv
  - json-ld
audience:
  - developers
  - architects
related:
  - ADR-009-okf-compliance-superset.md
  - ADR-011-markdown-canonical-derived-jsonld.md
  - ADR-002-dual-format-design.md
---

# ADR-012: OKF Conformance Enforced as a Tested CI Invariant

## Status

Accepted

## Context

### Background and Problem Statement

ADR-009 commits MIF to being a strict superset of a conformant OKF v0.1 bundle,
and ADR-011 makes Markdown canonical with the JSON-LD form a *derived*
projection. Both claims are only credible if they are mechanically verified: a
prose assertion that "every MIF bundle is a valid OKF bundle" or "the projection
is lossless" decays the moment an example drifts.

This decision records *how* those guarantees are enforced — the validation suite
and the CI gating that runs it — including the path/branch triggers that
determine whether the suite actually runs on a given pull request.

### Current Limitations

- A conformance claim that is not executed in CI silently rots as examples,
  schemas, and ontologies evolve.
- The validation workflow originally triggered only a narrow set of paths
  (`docs/okf-conformance.md`) and base branches (`main`), so changes to docs,
  the Astro site, ontologies, or PRs targeting release/development branches could
  merge without the conformance suite running.

## Decision Drivers

### Primary Decision Drivers

1. **Enforcement**: OKF conformance and lossless round-trip must be gating, not
   advisory.
2. **Coverage**: Every bundle that ships (core examples, the AI-memory profile,
   ontology example memories) must be validated.
3. **Trigger correctness**: The suite must actually run on the branches that
   v1.0.0 work targets.

### Secondary Decision Drivers

1. **Schema fidelity**: The derived JSON-LD must validate against the published
   schema.
2. **Site integrity**: The documentation site must build.

## Considered Options

### Option 1: Document conformance, verify manually

**Description**: State the conformance rules in prose; rely on contributors to
run the validators by hand.

**Advantages**:
- No CI cost.

**Disadvantages**:
- Conformance drifts undetected; the central claim of ADR-009 becomes
  unverifiable in practice.

**Risk Assessment**:
- **Technical Risk**: High. Regressions ship unnoticed.

### Option 2: Enforce conformance as gating CI checks (chosen)

**Description**: Run the conformance test, the lossless round-trip, JSON-LD
schema validation, ontology/namespace validation, and the docs build as required
CI jobs across all three relevant bundle sets, triggered on the paths and base
branches that v1.0.0 work uses.

**Advantages**:
- The ADR-009 / ADR-011 invariants become tested properties.
- Regressions block the merge.

**Disadvantages**:
- CI runtime and maintenance of the workflow.

**Risk Assessment**:
- **Technical Risk**: Low. Deterministic Python + ajv checks.
- **Schedule Risk**: Low. Seconds of CI per run.

## Decision

OKF conformance is enforced by `.github/workflows/validate.yml` as gating jobs:

1. **`okf-conformance`** — `scripts/okf_validate.py` enforces type-present, no
   reserved-filename concepts, relationship synchronization, broken-links
   tolerated; followed by the **lossless `markdown → json-ld → markdown`
   round-trip** (`scripts/mif_convert.py roundtrip`).
2. **`schema-validation`** — emits derived JSON-LD projections and validates each
   against `schema/mif.schema.json` with `ajv` (draft 2020-12, ajv-formats).
3. **`docs-build`** — builds the Astro documentation site.
4. **`validate-ontologies`** — validates ontology files and namespace
   consistency.

All bundle sets — `examples`, `profiles/ai-memory/examples`, and
`docs/examples/memories` — are passed to the conformance, round-trip, and
schema jobs.

The workflow triggers on the source paths that affect conformance
(`schema/**`, `examples/**`, `profiles/**`, `scripts/*.py`,
`docs/**`, `src/content/docs/**`, `package.json`, `astro.config.mjs`) and runs on
pull requests targeting `main`, `release/**`, and `develop/**` so v1.0.0
integration branches are gated.

## Consequences

### Positive

1. **Verified invariants**: ADR-009's superset claim and ADR-011's lossless
   projection are CI-enforced.
2. **Full bundle coverage**: Core, profile, and ontology example bundles are all
   validated.
3. **Correct gating**: PRs to development/release integration branches run the
   suite.

### Negative

1. **CI maintenance**: The workflow must track new bundle directories and
   tooling.

### Neutral

1. **Derived artifacts**: JSON-LD projections are emitted into a gitignored
   `dist/` during validation, not committed from this job.

## Decision Outcome

Conformance is now a gating property rather than a promise. A regression in any
bundle, the schema, an ontology, a namespace, or the docs site fails the merge.
Mitigation for trigger gaps: the `pull_request.branches` list explicitly includes
`develop/**` (in addition to `main` and `release/**`) so PRs retargeted onto the
v1.0.0 development branch are not silently un-gated.

## Related Decisions

- [ADR-009: OKF Compliance as a Superset](ADR-009-okf-compliance-superset.md) — the conformance contract this workflow enforces.
- [ADR-011: Markdown-Canonical with Derived JSON-LD](ADR-011-markdown-canonical-derived-jsonld.md) — the lossless round-trip job verifies its core invariant.
- [ADR-002: Dual Format Design](ADR-002-dual-format-design.md) — format parity is what the round-trip and schema jobs protect.

## Links

- [ajv JSON Schema validator](https://ajv.js.org/) — used for JSON-LD projection validation.
- [Astro](https://astro.build/) — documentation site builder gated by `docs-build`.

## More Information

- **Date:** 2026-06-18
- **Source:** `.github/workflows/validate.yml`; `docs/okf-conformance.md §3` (the conformance test).
- **Related ADRs:** ADR-009, ADR-011, ADR-002

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| PR trigger includes `main`, `release/**`, and `develop/**` | `.github/workflows/validate.yml` | L18 | compliant |
| `okf-conformance` job runs `okf_validate.py` (relationship sync) + lossless round-trip over all three bundle sets | `.github/workflows/validate.yml` | L46-L58 | compliant |
| `schema-validation` job emits projections and validates against `schema/mif.schema.json` via ajv | `.github/workflows/validate.yml` | L82-L99 | compliant |
| `docs-build` job builds the Astro site | `.github/workflows/validate.yml` | L101-L116 | compliant |
| `validate-ontologies` job validates ontology files and namespace consistency | `.github/workflows/validate.yml` | L118-L136 | compliant |
| Validator enforces type/reserved-filename/relationship-sync/round-trip | `scripts/okf_validate.py` | L7-L16 | compliant |
| Schema `$id` resolves to the published `mif-spec.dev` URI | `schema/mif.schema.json` | L3 | compliant |
| Conformance test documented (validator + round-trip, exit 0 = conform) | `docs/okf-conformance.md` | L69-L93 | compliant |

**Summary:** The conformance, round-trip, schema, ontology/namespace, and docs
jobs are present and gating; the PR branch filter covers `develop/**` so v1.0.0
integration PRs are validated. All cited anchors were opened and confirmed in
this session, and the suite was run locally to green.

**Action Required:** None.
