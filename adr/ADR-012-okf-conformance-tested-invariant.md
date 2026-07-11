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
updated: 2026-07-11
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

Findings cite durable anchors (job id / step `name:` / heading / field name),
not raw line numbers — line numbers in `.github/workflows/validate.yml`
shift every time a step is added or removed, which had already made four of
this section's five workflow-line citations stale by the 2026-07-11 audit
below (see that entry's Summary). `grep -n` for the quoted anchor text to
find its current line.

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| PR trigger includes `main`, `release/**`, and `develop/**` | `.github/workflows/validate.yml` | the `pull_request:` trigger's `branches:` list | compliant |
| `okf-conformance` job runs `okf_validate.py` (relationship sync) + lossless round-trip over all three bundle sets | `.github/workflows/validate.yml` | job `okf-conformance`, steps "OKF conformance test (relationship sync + round-trip)" + "Lossless markdown -> json-ld -> markdown round-trip" | compliant |
| `schema-validation` job emits projections and validates against `schema/mif.schema.json` via ajv | `.github/workflows/validate.yml` | job `schema-validation`, step "Validate every projection against schema/mif.schema.json" | compliant |
| `docs-build` job builds the Astro site | `.github/workflows/validate.yml` | job `docs-build`, step "Build Astro site" | compliant |
| `validate-ontologies` job validates ontology files and namespace consistency | `.github/workflows/validate.yml` | job `validate-ontologies`, step "Test subtype_of integrity" | compliant |
| Validator enforces type/reserved-filename/relationship-sync/round-trip | `scripts/okf_validate.py` | module docstring | compliant |
| Schema `$id` resolves to the published `mif-spec.dev` URI | `schema/mif.schema.json` | `$id` field | compliant |
| Conformance test documented (validator + round-trip, exit 0 = conform) | `docs/okf-conformance.md` | "3. The conformance test" heading | compliant |

**Summary:** The conformance, round-trip, schema, ontology/namespace, and docs
jobs are present and gating; the PR branch filter covers `develop/**` so v1.0.0
integration PRs are validated. All cited anchors were opened and confirmed in
this session, and the suite was run locally to green.

**Action Required:** None.

### 2026-07-11

**Status:** Compliant with one discrepancy (`validate-ontologies`, see note; tracked as #240)

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| PR trigger includes `main`, `release/**`, and `develop/**` | `.github/workflows/validate.yml` | the `pull_request:` trigger's `branches:` list | compliant |
| `okf-conformance` job runs `okf_validate.py` (relationship sync) and lossless round-trip over all three bundle sets, plus five bundle-independent structural/fixture checks added since 2026-06-18: JSON-LD context fidelity, vocab-term coverage (`check_vocab_term_coverage.py`, #231), relationship-type vocab coverage (`check_relationship_type_vocab_coverage.py`, #233), the `relationship_types` config registry test (#232, fixture-based, not the three bundle sets), and the temporal/properties pytest suite (#235, fixture-based) | `.github/workflows/validate.yml` | job `okf-conformance`, steps "OKF conformance test (relationship sync + round-trip)" through "Temporal consistency + properties construct regression suite" | compliant |
| `schema-validation` job emits projections and validates against `schema/mif.schema.json` via ajv | `.github/workflows/validate.yml` | job `schema-validation`, step "Validate every projection against schema/mif.schema.json" | compliant |
| `docs-build` job builds the Astro site | `.github/workflows/validate.yml` | job `docs-build`, step "Build Astro site" | compliant |
| `validate-ontologies` job validates ontology files and namespace consistency | `.github/workflows/validate.yml` | job `validate-ontologies`, step "Test subtype_of integrity" | **discrepancy** — see note |
| Validator enforces type/reserved-filename/relationship-sync/round-trip | `scripts/okf_validate.py` | module docstring | compliant |
| Schema `$id` resolves to the published `mif-spec.dev` URI | `schema/mif.schema.json` | `$id` field | compliant |
| Conformance test documented (validator + round-trip, exit 0 = conform) | `docs/okf-conformance.md` | "3. The conformance test" heading | compliant |

**Note on the `validate-ontologies` discrepancy:** as of ADR-018/ADR-019
(2026-07-01), ontology-content and namespace-consistency validation for this
repo's own content moved entirely to the `modeled-information-format/ontologies`
repo — this job's own inline comment says so explicitly ("this repo has
nothing local for those checks to run against"). The job now runs only
`scripts/test_subtype_of.py` against hardcoded fixtures: a real regression
test for the `subtype_of` resolver, but it does not validate ontology files
or namespace consistency in this repo the way this ADR's own Decision section
(item 4) still describes. That narrowing is already ratified by ADR-018/019;
this ADR's Decision text just hasn't been updated to reflect it. Filed as
#240 rather than amended here, since a formal `## Amendment` (per this repo's
`adr/README.md` Status-Values convention) is a real editorial decision about
scope and wording, not a mechanical fix.

**Summary:** Re-audit triggered by #238: the 2026-06-18 entry's raw line-number
citations had drifted for 4 of its 5 `validate.yml` rows even before this PR
(#227/#231/#232/#234 each added `okf-conformance` steps without updating this
ADR), and PR #239's two new steps (#233, #235) widened that drift further.
Re-verifying against current file state also surfaced the `validate-ontologies`
discrepancy noted above — not something #238 set out to find, but exactly the
kind of drift a real re-audit exists to catch. Re-verified every finding
against the current file state; `okf-conformance` has grown from 2 gating
checks at the 2026-06-18 audit to 7. No CI-gating regressions found; the one
discrepancy is a documentation gap (Decision text not updated for an already-
ratified narrowing), not a test that stopped running.

**Action Required:** #240 (amend ADR-012's Decision section for the
`validate-ontologies` narrowing already ratified by ADR-018/019).
