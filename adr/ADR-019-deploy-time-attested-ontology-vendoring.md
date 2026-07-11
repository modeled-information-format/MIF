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
status: accepted
created: 2026-06-30
updated: 2026-07-11
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
  - ADR-007-github-raw-urls-for-schema-ids.md
  - ADR-015-attested-release-orchestration.md
  - ADR-016-versioned-schema-mirror-publication.md
  - ADR-018-ontology-corpus-dedicated-repository-and-serving.md
---

# ADR-019: Deploy-Time, Attestation-Verified Ontology Vendoring

## Status

Accepted

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
2. **Preserve every ADR-018 invariant.** The `ontologies` repo stays the
   source of record for every ontology including `mif-base`/`shared-traits`,
   the schema/context stay in MIF, and the served URL patterns and identity
   invariant are unchanged. Only propagation moves.

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
mirror). The job vendors the fetched corpus as-is — `mif-base` and
`shared-traits` fetched and verified identically to every domain ontology,
per ADR-018 — then enriches — never recomputes — the attested `index.json`
core with `latest`/version aliases. Historical versions are enumerated from
`ontologies` release tags, each an immutable signed tarball. The deploy
triggers on an `ontologies` release (`repository_dispatch`, authenticated via
the ADR-011 five-app fleet, ref carried in the payload), on this repo's own
changes, and on a fuzzily scheduled backstop; concurrency-grouped so bursts
collapse to one publish. On verification failure, the deploy keeps the
last-good published surface and signals rather than publishing unverified
bytes.

**Advantages**: Structurally removes the manual hand-off; trust root becomes
the tarball's attestation rather than a PR-merge decision; reuses
`release.yml` + `gh attestation verify` verbatim; collapses the
committed-mirror-plus-tarball duplication to a single attested artifact.

**Disadvantages**: The deploy becomes non-hermetic (a build-time network
fetch); mirror changes are no longer individually reviewable in a PR diff
before shipping — only the attestation gates them; cutover must land as
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
- **No MIF-side ontology content:** per ADR-018, every ontology — including
  `mif-base` and `shared-traits` — is authored and versioned in the
  `ontologies` repo as source of record. This repo has no canonical copy to
  check compatibility against; the fetched corpus is vendored as-is.
- **Freshness:** the deploy triggers on `ontologies` release
  (`repository_dispatch` carrying the ref, authenticated via the ADR-011 app
  fleet), on this repo's own changes, and on a fuzzily scheduled backstop.
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
4. **Collapses artifact duplication.** ADR-018's plan produced a
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
3. **Atomic cutover requirement.** The fetch/verify/untar job, the
   `repository_dispatch` wiring, and the retirement of the committed snapshot
   must land together; a partial cutover leaves the served surface broken
   between states.

### Neutral

1. The `index.json` contract is unchanged; only who materializes it and when
   changes. Per-ontology `version` semantics are unaffected.
2. `engineering-base` and `research` remain domain-side family bases in the
   `ontologies` repo, distinct from `mif-base`/`shared-traits`.
3. Every ADR-018 decision outside propagation (source of record, schema
   location, flat layout, URL patterns, identity invariant) is unchanged.

## Decision Outcome

Option 2 satisfies all three primary drivers: the manual re-vendor step is
removed by tying the refresh to a release event plus a scheduled backstop;
admission is fail-closed on `gh attestation verify` against the signed
tarball rather than on a PR merge; and the fetch reuses the existing
attested-release chain rather than introducing new signing or verification
logic. The secondary drivers are also met: the index contract is preserved
by enrichment rather than recomputation, and every other ADR-018 invariant
(source of record for every ontology including `mif-base`, schema location,
URL patterns, identity invariant) is preserved unchanged.

The residual costs are accepted: the non-hermetic build reduces to "pin the
fetched ref and verify its attestation"; the loss of PR-diff review for
mirror changes is offset because corpus content is still reviewed as PRs
upstream, in the `ontologies` repo, before a release tag is cut; and the
keep-last-good-on-failure gate means freshness is best-effort under
integrity, never at its expense.

## Implementation

Not yet implemented. This ADR records the design agreed in cross-repo
ideation with the companion decision in the `ontologies` repo. Landing
requires, as one atomic change:

1. A deploy job in this repo's workflow that fetches the dispatched
   `ontologies` tag's release tarball, runs `gh attestation verify`
   fail-closed, and untars it into `dist/ontologies/` at build time.
2. A `repository_dispatch` receiver wired to the `ontologies` repo's release
   workflow, authenticated via the ADR-011 app fleet.
3. A fuzzily scheduled workflow as the convergence backstop.
4. An enrichment step that adds `latest`/version aliases to the fetched
   `index.json` without altering its attested core fields.
5. Retirement of `scripts/snapshot-ontology-version.py`'s commit step, the
   committed `public/ontologies/` tree, and ADR-018's never-built
   PR-propagation follow-up.

## Related Decisions

- [ADR-018: Ontology Corpus: Dedicated Repository, Flat Layout, and Versioned Serving](ADR-018-ontology-corpus-dedicated-repository-and-serving.md)
  — the decision this ADR amends. Everything in ADR-018 stands except the
  propagation mechanism named in its Implementation section as a follow-up.
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
- `scripts/snapshot-ontology-version.py` (retired by this decision's
  implementation; see the 2026-07-01 implementation audit entry below) — the
  committed-snapshot generator whose commit step this decision retires, and
  whose enrichment/HTML-generation logic was ported into
  [`scripts/vendor-ontologies.py`](../scripts/vendor-ontologies.py).

## More Information

The invariant to audit once implemented: the bytes served at
`mif-spec.dev/ontologies/*` must be the verified contents of a specific
signed `ontologies` release tarball, enriched but not recomputed. If the
served core `{version, file, sha256, extends[]}` for any ontology differs
from the attested tarball's `index.json`, this decision has been violated.

## Audit

Findings cite durable anchors (module docstring, trigger key, heading text,
git-tracked status), not raw line numbers. The 2026-06-30 entry below
originally used a `Lines` column of bare numbers (`23`, `1`, `4-7`,
`315-317` — no `L` prefix at all), a different citation style from every
other ADR in this repo's audit-citation retrofit. That's exactly why the
diff-scoped guardrail (`scripts/check_adr_audit_citations.py`, added by
#243/#244) never flagged this file: its raw-line pattern only matches
`\bL\d+(?:-L\d+)?\b`. Converted below to the same durable-anchor convention
ADR-012 established and `adr/README.md`'s "Creating New ADRs" section
documents.

### 2026-06-30

**Audited revision:** `898c03bbcacf30f64013bc6abffa0fed0ab80a59` — the
commit that made the 2026-07-01 base-ownership correction below; used here
because none of this entry's four findings concern that correction and all
four verify identically at this revision or at this ADR's own original
introduction commit.

**Status:** Pending — not yet implemented.

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| Served surface is still built from a committed, hand-vendored snapshot | `scripts/snapshot-ontology-version.py` | module docstring, "Run it as a release-prep step BEFORE tagging and commit the result." | confirmed: instructs running the script and committing the result before tagging |
| `public/ontologies/index.json` is a committed file, not build output | `public/ontologies/index.json` | tracked in the git tree at this revision; no `.gitignore` entry for `public/ontologies/` existed yet | confirmed present as committed source |
| Deploy has no `repository_dispatch` trigger for `ontologies` releases | `.github/workflows/deploy.yml` | the `"on":` trigger's `push`/`workflow_dispatch` keys | confirmed: only `push`/`workflow_dispatch` triggers exist |
| ADR-018's named PR-propagation follow-up was never built | `adr/ADR-018-ontology-corpus-dedicated-repository-and-serving.md` | the `## Implementation` section's "Follow-up" bullet | confirmed absent; no propagation workflow exists anywhere under `.github/workflows/` |

**Summary:** This ADR captures the design agreed in cross-repo ideation and
amends ADR-018's unbuilt propagation follow-up. The fetch/verify/untar job,
the `repository_dispatch` wiring, and the retirement of the committed
snapshot are all open implementation work.

**Action Required:** Implement per the Implementation section above before
this ADR can move to Accepted.

### 2026-07-01

**Audited revision:** `898c03bbcacf30f64013bc6abffa0fed0ab80a59` — the
commit that made this correction.

**Status:** Correction.

The original text of this ADR stated `mif-base` and `shared-traits` remain
"canonical and authored in this repo" (MIF), with a fail-closed
base-compatibility check refusing composition onto an incompatible base. That
contradicted the already-accepted ADR-018, which put every ontology —
including `mif-base` — in the `ontologies` repo as source of record; that
repo's own `ontologies/index.json` confirms `mif-base` is an entry there, not
in MIF. Corrected throughout this ADR: MIF holds no canonical ontology
content and runs no compatibility check; it is a pure consumer of the
`ontologies` repo's attested corpus. No change to the chosen mechanism
(Option 2, deploy-time fetch/verify/untar) or to any other decision in this
ADR. The corresponding Implementation item (base-compatibility check) is
removed as no longer applicable.

### 2026-07-01 — Implemented

**Audited revision:** `19d3c5324a6bcda3aa97493c58cc0a6af85656b1` — the
squash-merge commit for MIF#203, implementing every item this entry
describes.

**Status:** Implemented (Option 2, all five Implementation items complete).

- `scripts/vendor-ontologies.py`: fetches every `ontologies` release tag,
  runs the exact fail-closed `gh attestation verify` sequence that repo's own
  `release.yml` `verify` job runs (SLSA provenance, SBOM, three seam-signed
  gate verdicts, VEX), and untars the verified `ontologies/` subtree into
  `public/ontologies/`. Builds in a staging directory and only atomically
  swaps into the served path on complete success, so a failure anywhere
  (including a historical tag's verification failing after the target tag
  already succeeded) leaves the previous vendor untouched — verified
  directly by injecting a mid-loop failure.
- `deploy.yml`: the vendor step runs before `npm run build` (Astro copies
  `public/` into `dist/` verbatim, no plugin needed); `repository_dispatch:
  [ontology-corpus-released]` receiver added, plus a fuzzy-scheduled
  convergence backstop; cross-repo `gh` calls authenticate via the `ci` App
  (not the default `GITHUB_TOKEN`), matching that App's existing
  cross-repo-read purpose.
- The companion `ontologies` repo PR adds a `notify-mif` job to that repo's
  `release.yml`, firing the `repository_dispatch` after a tag-triggered
  publish via the existing `pages` App.
- `public/ontologies/` (188 files) is removed from git tracking and
  `.gitignore`d; `scripts/snapshot-ontology-version.py` (no CI/release
  wiring referenced it) is deleted, its enrichment/HTML-generation logic
  ported into `vendor-ontologies.py`.

**Verification performed:** `vendor-ontologies.py v0.2.1` run locally
produces a `public/ontologies/index.json` whose full 20-entry
`{version, file, sha256, extends}` core matches `ontologies/index.json` on
that repo's `main` exactly (0 mismatches); `npm run build` confirms
`dist/ontologies/index.json` is identical, proving Astro's copy behavior;
`test_subtype_of.py` (fixture-based, unaffected by the corpus move),
`okf_validate.py`, and `mif_convert.py roundtrip` all pass genuinely.

**Correction found during independent review:** an initial claim here that
`validate-ontologies.py` and `validate-namespaces.py` "pass unaffected" was
wrong. Both hardcode a scan path (`repo_root / "ontologies"`) that no
longer exists in this repo, so they silently scanned zero files and
reported success on an empty check, not a real one -- the exact
false-positive-pass failure mode this ADR's own vendoring pipeline exists
to eliminate elsewhere. Fixed by adding an optional `--path <dir>` argument
to both scripts (also fixing `yaml2jsonld.py --all` the same way, which had
the identical hardcoded-path bug) and making them report an explicit error
instead of a false "all validated successfully" when zero files are found
and no `--path` is given. This restores the manual `ontologies` repo
release-runbook workflow ("run them from a MIF checkout") that also
depended on this same hardcoded path, and lets any future automation point
them at the vendored `public/ontologies/` corpus.

### 2026-07-02 — Merged and closed out

**Audited revision:** `9e78eba1b86cf558ba819e0368d6c70fc8c38b13` — the
commit (MIF#204) that recorded this ADR's status flip to Accepted and this
close-out entry.

**Status:** Merged and closed out.

modeled-information-format/MIF#203 merged alongside the companion
modeled-information-format/ontologies#25 and
modeled-information-format/.github#44. Merging pushed a normal commit to
`main`, which triggered `deploy.yml`'s existing `push` trigger without
needing the `repository_dispatch` to fire first; that run vendored the
corpus and redeployed successfully (`gh run list` confirms
`conclusion: success` at the exact merge commit). Re-verified end to end
against the live site, not just the local checkout:
`https://mif-spec.dev/ontologies/index.json` returns HTTP 200, and every
one of the 20 entries' `version`, `file`, `sha256`, and `extends` fields
match `ontologies`' current `main` exactly.
modeled-information-format/ontologies#6's own acceptance criterion, the
index "served at `https://mif-spec.dev/ontologies/index.json`", stayed
unmet until this work landed even though its local `index.json` half was
already delivered by an earlier PR; closed on this evidence.

Fixing the `--path` false-positive above (previous entry) surfaced a real
regression: `.github/workflows/validate.yml`'s "Validate Ontology Files"
required check called `validate-ontologies.py`/`validate-namespaces.py`
with no `--path`, so the newly-accurate failure mode broke that check. Fixed
by dropping both corpus-scanning steps from that job (nothing local to
check now that ontology content lives entirely in the `ontologies` repo)
and keeping only `test_subtype_of.py`. The job's `name:` was kept exactly
as `Validate Ontology Files` since it is a required branch-protection
status check; renaming it would have made that check permanently
unsatisfiable.

Running the fixed `validate-ontologies.py --path` against the `ontologies`
repo's real corpus (rather than zero files) also surfaced genuine,
pre-existing `subtype_of` substitutability violations in four ontologies
that this check had never actually run against before. Filed as
modeled-information-format/ontologies#26; out of scope for this ADR,
tracked separately.

### 2026-07-11

**Audited revision:** `0415f2a70fe6b0184acd8da7167e83184761c483`

**Status:** Compliant — static mechanism and CI wiring unchanged since
implementation; one documentation discrepancy found in ADR-018 (not this
ADR), fixed in the same PR that lands this entry.

**Scope note:** this is a static-file re-audit of the pinned worktree, not
a live-pipeline run. It re-verifies that the vendoring mechanism and its CI
wiring are unchanged from what the 2026-07-01/07-02 entries recorded. It
does not re-run `vendor-ontologies.py` or re-fetch
`https://mif-spec.dev/ontologies/index.json`, so it cannot re-confirm the
specific invariant the 2026-07-02 entry confirmed against the live site
(the served `{version, file, sha256, extends[]}` core byte-matching the
attested tarball) — that requires re-running the pipeline or re-checking
the live site, not a static read.

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| `scripts/vendor-ontologies.py` remains the sole vendoring mechanism; `scripts/snapshot-ontology-version.py` stays deleted | `scripts/vendor-ontologies.py` | module docstring, "Vendor the ontology corpus from a signed, attested `ontologies` release." | compliant |
| `public/ontologies/` stays gitignored and untracked, not committed | `.gitignore` | the "Ontology corpus (ADR-019)" comment block's `public/ontologies/` entry | compliant — confirmed empty `git ls-tree` and no directory present on disk |
| `deploy.yml` still fetches/verifies/untars via a `repository_dispatch` receiver plus a scheduled backstop, ahead of the Astro build | `.github/workflows/deploy.yml` | the `"on":` trigger's `repository_dispatch: types: [ontology-corpus-released]` and `schedule:` keys; step "Vendor the ontology corpus (ADR-019)" | compliant |
| `validate.yml`'s "Validate Ontology Files" required check still runs only `test_subtype_of.py`, no corpus-content or namespace validation | `.github/workflows/validate.yml` | job `validate-ontologies`, step "Test subtype_of integrity" | compliant — cross-checked against ADR-012's own 2026-07-11 audit entry (same finding, independently re-verified here, not copied) |
| ADR-018 ↔ ADR-019 cross-reference is bidirectional | `adr/ADR-018-ontology-corpus-dedicated-repository-and-serving.md`, `adr/ADR-019-deploy-time-attested-ontology-vendoring.md` | ADR-018 frontmatter `related:` list + `## Amendment` section; ADR-019 frontmatter `related:` list + `## Related Decisions` | compliant — the link exists in both directions |
| ADR-018's own body text (not just its `related:`/Amendment section) accurately describes the current mechanism | `adr/ADR-018-ontology-corpus-dedicated-repository-and-serving.md` | `## Status` line; `### Propagation`; `## Implementation`; `## Links` | **was a discrepancy — fixed in this same PR** (see note) |
| `adr/README.md` index rows for ADR-018 and ADR-019 reflect current status | `adr/README.md` | the ADR-018 and ADR-019 table rows | compliant |
| Companion `ontologies` repo ADR-0004 still exists and matches | `modeled-information-format/ontologies` repo, `docs/decisions/0004-build-time-attested-ontology-vendoring.md` | file present, `## Status` heading | compliant |

**Note on the ADR-018 discrepancy:** measured against this repo's own
precedent for how an amended ADR should read (ADR-012, amended
2026-07-11), ADR-018 fell short in two specific ways: its `## Status` line
still read "Accepted (amendment proposed 2026-06-30 — see Amendment
section)" — "proposed" was stale, since the Amendment section's own
"Update, 2026-07-02" note already says ADR-019 is now Accepted and
implemented, but that update never propagated back up to the Status line;
and its `### Propagation`/`## Implementation`/`## Links` sections described
the pre-ADR-019 mechanism with no inline pointer to the Amendment section
(unlike ADR-012's inline pointer at its own superseded Decision item).
Fixed in this same PR: ADR-018's Status line updated to match the
ADR-012-established pattern, and an inline pointer added at the point
those sections describe the superseded mechanism. This was a
documentation-accuracy gap, not a design or code defect — the underlying
mechanism was already correctly superseded and the Amendment section
already contained the correct, dated update.

**Corpus growth as supporting evidence, not a re-verified claim:** the
`ontologies` repo's `ontologies/index.json` currently lists more entries
than the 20 the 2026-07-02 entry's live-site check recorded, confirming
the corpus has grown and the vendoring mechanism's own logic is generic to
that growth (no count-based assertion anywhere in `vendor-ontologies.py`'s
actual fetch/verify/untar code) — but this is not a re-confirmation that
the currently-served `mif-spec.dev/ontologies/index.json` reflects that
growth correctly; that would require the live-pipeline check the Scope
note above says this entry did not perform. Separately, and fixed in this
same PR: `vendor-ontologies.py`'s own module docstring had drifted into
asserting the stale "20 ontologies" count in prose — corrected to not name
a specific count, the same class of fragile literal-value claim this whole
retrofit exists to eliminate from the ADRs themselves.

**Summary:** The vendoring mechanism, its `deploy.yml` wiring, and
`validate.yml`'s narrowed `validate-ontologies` job are all unchanged from
what the 2026-07-01/07-02 entries recorded and remain exactly as this
ADR's Decision and Implementation sections describe. `adr/README.md`'s
index rows for both ADR-018 and ADR-019 are accurate. The one real
discrepancy found — ADR-018's own body text lagging its Amendment section
— is fixed in this same PR, not deferred.

**Action Required:** None.
