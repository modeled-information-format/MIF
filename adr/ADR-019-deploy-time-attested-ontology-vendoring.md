---
title: "Deploy-Time, Attestation-Verified Ontology Vendoring"
description: "Amends ADR-018's propagation mechanism: the mif-spec.dev deploy vendors the ontology corpus at build time by fetching the ontologies repo's signed release tarball and fail-closed verifying it with gh attestation verify, replacing the committed public/ontologies/ mirror and its PR-based propagation step."
type: adr
category: deployment
tags:
  - ontologies
  - vendoring
  - supply-chain
  - deployment
  - attestation
  - registry
status: proposed
created: 2026-06-30
updated: 2026-06-30
author: MIF Maintainers
project: MIF
technologies:
  - github-actions
  - gh-attestation
  - github-pages
audience:
  - developers
  - architects
related:
  - ADR-004-three-tier-trait-inheritance.md
  - ADR-007-github-raw-urls-for-schema-ids.md
  - ADR-015-attested-release-orchestration.md
  - ADR-016-versioned-schema-mirror-publication.md
  - ADR-018-ontology-corpus-dedicated-repository-and-serving.md
---

# ADR-019: Deploy-Time, Attestation-Verified Ontology Vendoring

## Status

Proposed

This ADR amends [ADR-018](ADR-018-ontology-corpus-dedicated-repository-and-serving.md).
ADR-018 is unchanged and stays Accepted for everything it decided: the
`ontologies` repo as source of record, the schema/context staying in MIF, the
flat layout, the URL patterns, and the identity invariant. This ADR replaces
only the propagation mechanism ADR-018 left as a named follow-up: "a
release-propagation job in the `ontologies` repo that, on a `vX.Y.Z` tag,
mirrors the released corpus into MIF's `public/ontologies/` and opens a PR;
MIF merges and deploys."

## Context

### Background and Problem Statement

ADR-018 chose to serve the ontology corpus from a committed mirror in this
repo's `public/ontologies/`, refreshed by `scripts/snapshot-ontology-version.py`
and, per its stated follow-up, eventually automated as a bot-opened PR on
each `ontologies` release tag. That automation was not yet built; in its
absence, the mirror has been refreshed by a maintainer running the script by
hand and committing the result.

The `ontologies` repo's own release workflow already produces a signed,
SLSA-attested `${NAME}-${VERSION}.tar.gz` per tag: build provenance
(`attest-build-provenance`), a CycloneDX SBOM (`attest-sbom`), a SAST
verdict, and a fail-closed `gh attestation verify` gate before publish. This
repo's committed mirror does not consume that artifact; it is built from a
plain checkout of the corpus, copied by hand.

### Current Limitations

- **Manual hand-off drifts silently.** With the propagation-PR automation
  unbuilt, the mirror only updates when a maintainer re-runs the snapshot
  script and commits. Two merged upstream PRs (a new domain ontology, a
  content change to an existing one) left the served `index.json` at 19 of
  20 entries with a stale `sha256`, while the upstream index itself stayed
  correct.
- **The strongest available artifact goes unused.** The signed release
  tarball is the `ontologies` repo's most trustworthy output; even ADR-018's
  planned PR-propagation would mirror a plain checkout, not the attested
  artifact, and a PR merge is a human trust decision, not a cryptographic
  verification.
- **No cross-repo freshness signal exists yet.** Nothing currently ties an
  `ontologies` release to a rebuild here, so the served surface cannot
  self-heal.
- **Base and domain ontologies share one propagation path**, despite
  different governance cadence: `mif-base` and `shared-traits` are this
  repo's normative floor (ADR-004); the domain corpus grows in the
  `ontologies` repo without touching that floor.

## Decision Drivers

### Primary Decision Drivers

1. **No manual re-vendor step.** The served surface must refresh itself from
   a release event and a scheduled backstop, not from a maintainer's memory
   or a merged PR.
2. **Fail-closed on attestation, not on PR review.** Vendored bytes are
   admitted only after `gh attestation verify` passes against the signed
   tarball for the fetched tag; verification failure must never publish
   partial or unverified content. A human-reviewed PR merge is not a
   substitute for cryptographic verification of the artifact's origin.
3. **Reuse, not reinvent.** The fetch/verify step consumes the `ontologies`
   repo's existing `release.yml` artifact and attestations as-is; this
   decision adds no bespoke signing or verification logic.

### Secondary Decision Drivers

1. **One index contract.** This repo enriches the vendored, attested
   `{version, file, sha256, extends[]}` core (aliases, versioned URLs); it
   never recomputes those attested fields.
2. **Normative floor stays authored here.** `mif-base` and `shared-traits`
   remain canonical in this repo per ADR-004; only the open-growth domain
   corpus is fetched from the external release.
3. **Preserve every ADR-018 invariant.** The `ontologies` repo stays the
   source of record, the schema/context stay in MIF, and the served URL
   patterns and identity invariant are unchanged. Only propagation moves.

## Considered Options

### Option 1: Build the ADR-018 follow-up as designed (bot-opened PR, committed mirror)

**Description**: Implement the automation ADR-018 already named: on each
`ontologies` release tag, a bot mirrors the corpus into
`public/ontologies/` and opens a PR here; a maintainer (or an automerge
policy) merges it, and the next deploy serves the new mirror.

**Advantages**: Smallest deviation from the accepted decision; keeps the
hermetic-build property (no build-time network fetch); every mirror change is
reviewable in a PR diff before it ships.

**Disadvantages**: Still introduces a committed copy with its own possible
lag between the PR opening and merging; does not eliminate the two-artifact
duplication (attested tarball vs. committed tree) that Option 2 collapses to
one; a PR merge is a human/policy trust decision, not a cryptographic one, so
it does not satisfy the "fail-closed on attestation" driver as directly as
verifying the tarball itself.

**Risk Assessment**: Low-medium technical risk, but does not fully satisfy
the primary "fail-closed on attestation, not PR review" driver — bytes are
admitted on merge, not on verified attestation.

### Option 2: Deploy-time fetch, attestation-verify, and untar of the signed tarball (chosen)

**Description**: A deploy job fetches the `ontologies` release tag's
`${NAME}-${VERSION}.tar.gz`, runs `gh attestation verify` against it
fail-closed, and untars it into build output (`dist/ontologies/`, following
the same non-committed pattern ADR-016 established for the versioned schema
mirror). The job composes the fetched domain corpus onto this repo's
canonical `mif-base`/`shared-traits`, refusing composition if the tarball
declares an incompatible base version. It then enriches — never
recomputes — the attested `index.json` core with `latest`/version aliases.
Historical versions are enumerated from `ontologies` release tags, each an
immutable signed tarball. The deploy triggers on an `ontologies` release
(`repository_dispatch`, authenticated via the ADR-011 five-app fleet, ref
carried in the payload), on this repo's own changes, and on a scattered
scheduled backstop; concurrency-grouped so bursts collapse to one publish.
On verification failure, the deploy keeps the last-good published surface and
signals rather than publishing unverified bytes.

**Advantages**: Structurally removes the manual hand-off; trust root becomes
the tarball's attestation rather than a PR-merge decision; reuses
`release.yml` + `gh attestation verify` verbatim; governance splits cleanly
along the base/domain boundary ADR-004 already draws; collapses the
committed-mirror-plus-tarball duplication to a single attested artifact.

**Disadvantages**: The deploy becomes non-hermetic (a build-time network
fetch); the `extends` graph now crosses repos at build time rather than at
PR-review time, so an `ontologies` corpus validator must resolve `mif-base`
from a pinned, verified version of this repo, and a `mif-base` change here
should run the `ontologies` corpus validators before merge (reverse
validation); mirror changes are no longer individually reviewable in a PR
diff before shipping — only the attestation gates them; cutover must land as
one atomic change (fetch job + `repository_dispatch` wiring + retirement of
the committed snapshot) or the served surface breaks mid-transition.

**Risk Assessment**: Medium technical risk (network dependency, cross-repo
coordination at cutover, loss of PR-diff review), mitigated by the
fail-closed verify gate and keep-last-good on failure.

### Option 3: Keep the status quo (manual snapshot, no propagation automation)

**Description**: Continue running `snapshot-ontology-version.py` by hand and
committing `public/ontologies/`; do not build the ADR-018 follow-up at all.

**Advantages**: No new work; no new cross-repo trigger.

**Disadvantages**: Retains the exact manual hand-off that already produced
the observed drift; the signed tarball remains unused; no self-healing path.

**Risk Assessment**: Low technical risk, but the drift risk it already
produced is accepted indefinitely.

## Decision

Adopt **Option 2**, superseding the PR-propagation mechanism ADR-018 named as
its follow-up (never built) before it was implemented. The `mif-spec.dev`
deploy assembles the served `/ontologies/*` surface at build time by
fetching, attestation-verifying, and untarring the `ontologies` repo's signed
per-version release tarball. Every other ADR-018 decision is unchanged.

- **Fetch unit:** the signed, SLSA-attested `${NAME}-${VERSION}.tar.gz` from
  an `ontologies` release tag, with its packaged `index.json` (produced by
  `gen-ontology-index.sh`) as the attested manifest. This repo enriches that
  index; it never recomputes the attested `{version, file, sha256,
  extends[]}` core.
- **Base/domain split:** `mif-base` and `shared-traits` remain canonical and
  authored in this repo (ADR-004 unchanged). The fetched tarball declares the
  `mif-base` version it validated against; the deploy refuses to compose it
  onto an incompatible base — a fail-closed compatibility check, not just an
  integrity check.
- **Freshness:** the deploy triggers on `ontologies` release
  (`repository_dispatch` carrying the ref, authenticated via the ADR-011 app
  fleet), on this repo's own changes, and on a scattered scheduled backstop.
  Concurrency-grouped. Verification failure keeps the last-good published
  surface and signals; it never publishes partial or unverified bytes.
- **No committed mirror:** `public/ontologies/` becomes build output under
  `dist/ontologies/`; `scripts/snapshot-ontology-version.py`'s commit step and
  the never-built PR-propagation follow-up are both retired.
- **Unchanged from ADR-018:** the `ontologies` repo stays source of record;
  the ontology schema and JSON-LD context stay in MIF; the served URL
  patterns (`/ontologies/<name>`, `/X.Y.Z/`, `/latest/`, `/vMAJOR/`) and the
  `id`/`version` identity invariant are unaffected.

## Consequences

### Positive

1. **Structural fix for the observed drift.** The release event drives the
   refresh, and the schedule guarantees eventual convergence even if a
   dispatch is missed.
2. **Publisher trust root becomes the project's strongest artifact.** The
   served surface is the verified bytes of a specific signed tarball,
   enriched but not altered, rather than the output of a merged PR.
3. **No new fetch/verify code to maintain.** The deploy job reuses
   `release.yml` and `gh attestation verify` exactly as they exist today.
4. **Governance matches ownership.** The normative floor stays small, slow,
   and authored here; the domain corpus grows open and additive in the
   `ontologies` repo without touching the floor.
5. **Collapses artifact duplication.** ADR-018's plan produced a
   PR-reviewed committed tree alongside an unused attested tarball; this
   decision uses the tarball as the sole trust root.

### Negative

1. **Non-hermetic build.** A build-time network fetch is introduced; the
   fetched ref is pinned by the dispatch payload and gated by sha/attestation
   verification to bound this risk.
2. **Loss of PR-diff review for mirror changes.** ADR-018's planned
   PR-propagation would have let a maintainer review each mirror change as a
   diff before merge; this decision replaces that human review step with
   cryptographic verification only. Corpus changes are still reviewed as PRs
   in the `ontologies` repo itself, upstream of the release tag.
3. **Cross-repo `extends` seam.** The `ontologies` corpus validators must
   resolve `mif-base` from a pinned, verified version of this repo; a
   `mif-base` change here should run the `ontologies` corpus validators
   before merge (reverse validation), which is new cross-repo CI coupling.
4. **Atomic cutover requirement.** The fetch/verify/untar job, the
   `repository_dispatch` wiring, and the retirement of the committed snapshot
   must land together; a partial cutover leaves the served surface broken
   between states.

### Neutral

1. The `index.json` contract is unchanged; only who materializes it and when
   changes. Per-ontology `version` semantics are unaffected.
2. `engineering-base` and `research` remain domain-side family bases in the
   `ontologies` repo, not part of this repo's canonical floor.
3. Every ADR-018 decision outside propagation (source of record, schema
   location, flat layout, URL patterns, identity invariant) is unchanged.

## Decision Outcome

Option 2 satisfies all three primary drivers: the manual re-vendor step is
removed by tying the refresh to a release event plus a scheduled backstop;
admission is fail-closed on `gh attestation verify` against the signed
tarball rather than on a PR merge; and the fetch reuses the existing
attested-release chain rather than introducing new signing or verification
logic. The secondary drivers are also met: the index contract is preserved
by enrichment rather than recomputation, the normative floor keeps its own
governance under ADR-004 while the domain corpus grows freely, and every
other ADR-018 invariant (source of record, schema location, URL patterns,
identity invariant) is preserved unchanged.

The residual costs are accepted: a non-hermetic build and a cross-repo
`extends` seam both reduce to "pin the other repo at a verified ref"; the
loss of PR-diff review for mirror changes is offset because corpus content is
still reviewed as PRs upstream, in the `ontologies` repo, before a release
tag is cut; and the keep-last-good-on-failure gate means freshness is
best-effort under integrity, never at its expense.

## Implementation

Not yet implemented. This ADR records the design agreed in cross-repo
ideation with the companion decision in the `ontologies` repo. Landing
requires, as one atomic change:

1. A deploy job in this repo's workflow that fetches the dispatched
   `ontologies` tag's release tarball, runs `gh attestation verify`
   fail-closed, and untars it into `dist/ontologies/` at build time.
2. A `repository_dispatch` receiver wired to the `ontologies` repo's release
   workflow, authenticated via the ADR-011 app fleet.
3. A scattered scheduled workflow as the convergence backstop.
4. An enrichment step that adds `latest`/version aliases to the fetched
   `index.json` without altering its attested core fields.
5. A base-compatibility check that refuses composition when the fetched
   tarball's declared `mif-base` version does not match this repo's
   canonical version.
6. Retirement of `scripts/snapshot-ontology-version.py`'s commit step, the
   committed `public/ontologies/` tree, and ADR-018's never-built
   PR-propagation follow-up.

## Related Decisions

- [ADR-018: Ontology Corpus: Dedicated Repository, Flat Layout, and Versioned Serving](ADR-018-ontology-corpus-dedicated-repository-and-serving.md)
  — the decision this ADR amends. Everything in ADR-018 stands except the
  propagation mechanism named in its Implementation section as a follow-up.
- [ADR-004: Three-Tier Trait Inheritance](ADR-004-three-tier-trait-inheritance.md)
  — defines the `mif-base` / `shared-traits` / domain-ontology layering this
  decision uses to draw the canonical-floor boundary.
- [ADR-007: GitHub Raw URLs for Schema IDs](ADR-007-github-raw-urls-for-schema-ids.md)
  — the unversioned, stable-identifier precedent this decision's versioned
  ontology URLs follow, mirroring the schema mirror's `$id` invariant.
- [ADR-015: Attested Release Orchestration](ADR-015-attested-release-orchestration.md)
  — the attested-release pattern (`attest-build-provenance`, `attest-sbom`,
  fail-closed `gh attestation verify`) this decision consumes from the
  `ontologies` repo rather than reimplementing.
- [ADR-016: Per-Version Schema Mirror Publication](ADR-016-versioned-schema-mirror-publication.md)
  — the precedent for non-committed, build-time-generated versioned output
  (`dist/schema/`) this decision follows for `dist/ontologies/`.
- **Companion decision (ontologies repo):**
  `modeled-information-format/ontologies` ADR-0004, "Build-Time,
  Attestation-Verified Ontology Vendoring" — the content-owner-side decision
  recording the same fetch/verify/untar contract from the producer's view.

## Links

- `modeled-information-format/ontologies` `.github/workflows/release.yml` —
  the build → attest → fail-closed-verify → tag-gated-publish chain producing
  the signed tarball this decision fetches.
- [`scripts/snapshot-ontology-version.py`](../scripts/snapshot-ontology-version.py)
  — the committed-snapshot generator whose commit step this decision retires.

## More Information

The invariant to audit once implemented: the bytes served at
`mif-spec.dev/ontologies/*` must be the verified contents of a specific
signed `ontologies` release tarball, enriched but not recomputed. If the
served core `{version, file, sha256, extends[]}` for any ontology differs
from the attested tarball's `index.json`, this decision has been violated.

## Audit

### 2026-06-30

**Status:** Proposed — not yet implemented.

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Served surface still built from a committed, hand-vendored snapshot | `scripts/snapshot-ontology-version.py`, `public/ontologies/` | full files | not yet implemented |
| ADR-018's named PR-propagation follow-up was never built | `adr/ADR-018-ontology-corpus-dedicated-repository-and-serving.md` | Implementation section | confirmed absent; no propagation workflow exists |
| No fetch/verify/untar deploy job exists | (none) | n/a | not yet implemented |
| No `repository_dispatch` receiver for `ontologies` releases | (none) | n/a | not yet implemented |

**Summary:** This ADR captures the design agreed in cross-repo ideation and
amends ADR-018's unbuilt propagation follow-up. The fetch/verify/untar job,
the `repository_dispatch` wiring, the base/domain compatibility check, and
the retirement of the committed snapshot are all open implementation work.

**Action Required:** Implement per the Implementation section above before
this ADR can move to Accepted.
