---
title: "Ontology Corpus: Dedicated Repository, Flat Layout, and Versioned Serving"
description: "Ontologies live in the dedicated modeled-information-format/ontologies repo (source of record) while the normative schema and JSON-LD context stay in MIF; the corpus is served at mif-spec.dev/ontologies/ with canonical and immutable version-pathed mirrors, per the ADR-016 model."
type: adr
category: infrastructure
tags:
  - ontologies
  - repository-structure
  - versioning
  - distribution
  - json-ld
  - serving
status: accepted
created: 2026-06-30
updated: 2026-06-30
author: MIF Maintainers
project: MIF
technologies:
  - yaml
  - json-ld
  - json-schema
  - github-pages
  - astro
audience:
  - developers
  - architects
related:
  - ADR-004-three-tier-trait-inheritance.md
  - ADR-005-underscore-namespace-prefix.md
  - ADR-007-github-raw-urls-for-schema-ids.md
  - ADR-011-markdown-canonical-derived-jsonld.md
  - ADR-016-versioned-schema-mirror-publication.md
  - ADR-019-deploy-time-attested-ontology-vendoring.md
---

# ADR-018: Ontology Corpus: Dedicated Repository, Flat Layout, and Versioned Serving

## Status

Accepted

This ADR resolves the precursor recorded as org discussion #168
("House the Ontologies in a Dedicated modeled-information-format/ontologies
Repository", status `proposed`). It records the architecture as built and
answers that discussion's three open questions (scope, consumption, versioning).

**Amendment (2026-06-30):** [ADR-019](ADR-019-deploy-time-attested-ontology-vendoring.md)
(proposed) replaces the propagation mechanism named below as a follow-up
(bot-opened PR mirroring into `public/ontologies/`, never built) with a
deploy-time fetch of the `ontologies` repo's signed release tarball, verified
fail-closed with `gh attestation verify`. Every other decision in this ADR
(source of record, schema/context location, layout, URL patterns, identity
invariant) is unchanged.

## Context

### Background and Problem Statement

The ontology definitions (`mif-base`, `shared-traits`, and the domain
ontologies) were authored alongside the normative format in the MIF
(Modeled Information Format) specification repository. Org discussion #168
proposed moving them into the dedicated `modeled-information-format/ontologies`
repository and left three questions deliberately open:

1. **Scope** — move every ontology, or keep `mif-base`/`shared-traits` in MIF
   and move only the domain ontologies?
2. **Consumption** — how should consumers reference ontologies: a git submodule,
   released bundles, or raw URLs on a published site?
3. **Versioning** — independent versioning per ontology, or a single
   repository-wide version?

The `ontologies` repository now exists and is populated (the knowledge-triad
base, the shared-trait mixins, two intermediate bases, and the domain
ontologies), so this ADR records the chosen architecture rather than reopening
the question.

Two forces frame the decision. First, ontologies evolve faster than the
normative format and on a different cadence; coupling them to the specification
release blocks domain contributions on spec releases and inflates the spec
repo's contribution surface and gate suite. Second, the ontology **schema**
(`schema/ontology/ontology.schema.json`) and its JSON-LD context are normative —
part of the format contract — so splitting them out would fragment the contract
across two repositories.

A related gap: each ontology's identity already references a published site.
An ontology's `uri`/`@id` resolves under `https://mif-spec.dev/ontologies/`, but
nothing served that path, so those references did not resolve.

### Current Limitations (before this ADR)

- Ontologies were coupled to the spec release cadence; domain contributions
  waited on specification releases.
- The ontology `uri`/`@id` values point at `mif-spec.dev/ontologies/`, but
  nothing served them — the canonical identities did not resolve.
- No flat, predictable corpus layout and no machine-readable catalog.
- No immutable, version-pinnable ontology URLs.

## Decision Drivers

### Primary Decision Drivers

1. **Independent release cadence**: ontologies must version and ship without
   waiting on a specification release.
2. **Singular format contract**: the normative ontology schema and JSON-LD
   context stay in MIF; the corpus must not fork the contract.
3. **Resolvable identity**: the published `uri`/`@id` values must resolve at
   `https://mif-spec.dev/ontologies/`.
4. **Immutability**: a consumer that pins a version path must get the same bytes
   forever, consistent with ADR-016.

### Secondary Decision Drivers

1. **Clearer contribution surface**: domain experts contribute ontologies
   without navigating the full specification gate suite.
2. **Two readers**: every ontology, and the catalog, are served both
   human-readable and machine-readable (consistent with ADR-002/ADR-011).
3. **Stable identifiers**: ontology `id` values and namespace IRIs do not change
   (ADR-005), so existing references keep working after the move.
4. **Discoverability**: a machine-readable catalog enumerates the corpus and its
   versioned URLs without scraping the site.

## Considered Options

### Option 1: All ontologies in the dedicated repo; schema + context stay in MIF; serve versioned (chosen)

**Description**: Move every ontology (including `mif-base` and `shared-traits`)
into `modeled-information-format/ontologies` as the source of record. Keep the
normative `ontology.schema.json` and its JSON-LD context in MIF. Serve the corpus
at `mif-spec.dev/ontologies/` from MIF's `public/ontologies/`, with immutable
version mirrors (the ADR-016 model). Retain each ontology's own version; a corpus
release is an immutable snapshot of all of them.

**Advantages**:

- Cleanest separation of cadence and contribution surface; one home for every
  ontology.
- The format contract (schema + context) stays singular in MIF.
- The published `uri`/`@id` values resolve, because MIF serves
  `mif-spec.dev/ontologies/`.
- Reuses the proven schema serving and release-gate machinery (ADR-016).

**Disadvantages**:

- Foundational `mif-base` now resolves from a different repo than the schema it
  instantiates; serving + propagation wiring is required.
- Each corpus release adds committed files under `public/ontologies/`.

**Risk Assessment**:

- **Technical Risk**: Medium. Cross-repo propagation, mitigated by reusing the
  ADR-016 snapshot tooling.

### Option 2: Move only domain + example ontologies; keep mif-base + shared-traits in MIF

**Description**: Keep the foundational definitions next to the schema; move only
domain content to the dedicated repo.

**Advantages**: foundational definitions stay adjacent to the contract; lowest
resolution risk for the base.

**Disadvantages**: the corpus is split across two repos — a fuzzier boundary;
the "smaller spec repo" and "single home for ontologies" drivers are only
partially met.

**Risk Assessment**: **Technical Risk**: Low–Medium.

### Option 3: Move everything, including the ontology schema (disfavored)

**Description**: Make the `ontologies` repo fully self-contained by moving the
schema and context as well.

**Advantages**: the `ontologies` repo is self-contained.

**Disadvantages**: splits the normative format contract across two
repositories. The schema is normative and belongs with the format.

**Risk Assessment**: **Technical Risk**: Medium; **Ecosystem Risk**: Medium.

### Option 4: Keep all ontologies in MIF (do nothing)

**Description**: Leave the ontologies in the spec repo.

**Advantages**: single repository, single gate suite, one CI trust root; no
cross-repo wiring; stable `id` values mean there is no correctness pressure to
move.

**Disadvantages**: ontologies stay coupled to the spec release cadence; the
contribution surface stays heavy; consumers wanting only ontologies still clone
the spec site.

**Risk Assessment**: **Technical Risk**: Low.

**Sub-decisions (the discussion's open questions).**

- **Consumption**: raw URLs on the published site (chosen) over a git submodule
  (couples consumers to a checkout) or release-bundles-only (no canonical
  per-ontology URL). Versioned mirrors and an offline bundle are additive.
- **Versioning**: per-ontology versions **plus** corpus-release snapshots
  (chosen), over per-ontology-only (no immutable corpus pin) or repo-wide-only
  (loses each ontology's own evolution).

## Decision

Adopt **Option 1**. All ontologies — `mif-base`, `shared-traits`, the
intermediate bases (`engineering-base`, `mif-generic`), and the domain
ontologies — live in `modeled-information-format/ontologies` as the source of
record. The normative `ontology.schema.json` and its JSON-LD context remain in
MIF as the format contract. The corpus is served at
`https://mif-spec.dev/ontologies/` from MIF's `public/ontologies/`, mirroring the
schema serving model (ADR-016). Per-ontology versions are retained; corpus
releases provide immutable version paths.

### Repository split and source of record

| Concern | Home |
|---------|------|
| Ontology definitions (source of record) | `modeled-information-format/ontologies` |
| Normative ontology schema + JSON-LD context (format contract) | MIF (`schema/ontology/`) |
| Serving surface (`mif-spec.dev/ontologies/`) | MIF (`public/ontologies/`) |

The `ontologies` repo validates each ontology against the published
`ontology.schema.json`; MIF owns the contract and the served mirror.

### Flat layout

Ontologies are flat files, not per-ontology directories. In the source repo:
`ontologies/<name>.ontology.yaml` plus a committed `ontologies/<name>.ontology.jsonld`
projection. Served canonically as `public/ontologies/<name>.ontology.{yaml,jsonld}`.

### Serving and URL patterns

| Path | Mutability | Description |
|------|------------|-------------|
| `/ontologies/<name>.ontology.{yaml,jsonld}` | moves with releases | canonical; current corpus; the `uri`/`@id` target |
| `/ontologies/X.Y.Z/<name>.ontology.{yaml,jsonld}` | immutable | exact snapshot of corpus release `X.Y.Z` |
| `/ontologies/latest/<name>.ontology.{yaml,jsonld}` | moving alias | newest corpus release |
| `/ontologies/vMAJOR/<name>.ontology.{yaml,jsonld}` | moving alias | newest release in that major line |

### Identity invariant

The `id`, `version`, and `@id` inside every mirrored ontology file are unchanged
across mirrors — the version path is an access address only, not a new identity.
This is the ADR-016 `$id`-invariant principle applied to ontologies, and it
preserves ADR-005 (namespace IRIs) and ADR-007 (stable canonical URLs).

### Two readers

Each ontology is served in both forms: `<name>.ontology.yaml` (the human source)
and `<name>.ontology.jsonld` (the machine projection), per ADR-011. The catalog
is served both ways too: `index.json` (machine) and `index.html` (a human,
mif-brand-styled index). Both are generated from the canonical files so they
cannot drift.

### Versioning model

Each ontology carries its own `version` (e.g. `mif-base` 1.0.0,
`software-engineering` 0.5.0); these evolve independently. A **corpus release**
`X.Y.Z` is an immutable snapshot of every ontology at whatever individual
version it carried then. The catalog records both the corpus `versions[]`/aliases
and each ontology's own `version`. This is the direct analog of the schema
mirrors keeping their canonical `$id` (ADR-016) while pinning bytes per release.

### Propagation

The `ontologies` repo is the source of record. On a corpus release `vX.Y.Z`, the
released corpus is mirrored into MIF's `public/ontologies/`, the catalog and the
human index are regenerated, and MIF deploys `mif-spec.dev`. The
source→serve boundary stays clean; mirrors are immutable per release.

## Consequences

### Positive

1. **Independent cadence**: ontologies ship without a spec release; the spec
   repo's contribution surface shrinks.
2. **Singular contract**: the normative schema + context stay in MIF; the corpus
   does not fork them.
3. **Resolvable identity**: `uri`/`@id` values resolve at
   `mif-spec.dev/ontologies/`.
4. **Pinnable, immutable URLs**: consumers pin an exact corpus snapshot and get
   the same bytes forever.
5. **Machine + human**: the corpus and its catalog serve both readers from one
   generated source.
6. **Reused machinery**: the serving, catalog, and release gate reuse the
   ADR-016 model rather than inventing new infrastructure.

### Negative

1. **Cross-repo propagation**: a corpus release must mirror into MIF before the
   site serves it; this adds a propagation step (gated, mechanical).
2. **Growing `public/ontologies/`**: each corpus release adds committed files;
   no pruning, because immutability is the guarantee (as in ADR-016).
3. **Foundational base resolves cross-repo**: `mif-base` resolves from a
   different repo than the schema it instantiates; stable `id` values (ADR-005)
   keep references correct.

### Neutral

1. **Doc site serves mirrors automatically**: the Astro/Starlight build copies
   everything under `public/` into `dist/`; no build plugin is needed.
2. **`extends` resolution**: an ontology's `extends` references resolve by `id`
   against the corpus, which is unaffected by where the bytes are served.

## Decision Outcome

Option 1 meets all four primary drivers: ontologies gain an independent cadence
in their own repo; the normative schema + context stay singular in MIF; the
published `uri`/`@id` values resolve because MIF serves
`mif-spec.dev/ontologies/`; and corpus-release mirrors give immutable,
byte-stable URLs. The secondary drivers are satisfied by the human + machine
catalog, the dedicated contribution surface, and the unchanged identifiers. The
negatives — cross-repo propagation and a growing served directory — are accepted
and mitigated by reusing the ADR-016 snapshot tooling and its fail-closed gate.

## Implementation

- `scripts/snapshot-ontology-version.py X.Y.Z` builds the version mirror, the
  `index.json` catalog, and the human `index.html` from the canonical files;
  `--check` verifies they are present and current (the release gate, as in
  ADR-016).
- `public/ontologies/` holds the canonical pairs plus the `0.1.0/`, `latest/`,
  and `v0/` mirrors; `index.json` and `index.html` are generated.
- Follow-up: a release-propagation job in the `ontologies` repo that, on a
  `vX.Y.Z` tag, mirrors the released corpus into MIF's `public/ontologies/` and
  opens a PR; MIF merges and deploys.

## Related Decisions

- Org discussion #168 (precursor) -- the proposal and the four options this ADR resolves.
- [ADR-016: Versioned Schema Mirror Publication](ADR-016-versioned-schema-mirror-publication.md) -- the serving + release-gate model reused here for ontologies.
- [ADR-007: GitHub Raw URLs for Schema IDs](ADR-007-github-raw-urls-for-schema-ids.md) -- canonical, unversioned, stable URLs; the identity invariant applied here.
- [ADR-011: Markdown-Canonical with Derived JSON-LD](ADR-011-markdown-canonical-derived-jsonld.md) -- YAML canonical, JSON-LD derived; the two-reader serving of each ontology.
- [ADR-005: Underscore Namespace Prefix](ADR-005-underscore-namespace-prefix.md) and [ADR-004: Three-Tier Trait Inheritance](ADR-004-three-tier-trait-inheritance.md) -- the corpus model the layout serves.

## Links

- Precursor discussion: https://github.com/orgs/modeled-information-format/discussions/168
- Source of record: `modeled-information-format/ontologies`
- [`scripts/snapshot-ontology-version.py`](../scripts/snapshot-ontology-version.py) -- the release-prep tool.
- [`public/ontologies/index.json`](../public/ontologies/index.json) -- the machine-readable ontology catalog.

## More Information

- **Date:** 2026-06-30
- **Source:** org discussion #168; `public/ontologies/`; `scripts/snapshot-ontology-version.py`.
- **Related ADRs:** ADR-004, ADR-005, ADR-007, ADR-011, ADR-016

## Audit

### 2026-06-30

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Ontologies authored in the dedicated repo (source of record) | `modeled-information-format/ontologies` | repository | compliant |
| Corpus served canonically with immutable per-release mirrors | `public/ontologies/`, `public/ontologies/0.1.0/`, `latest/`, `v0/` | directory trees | compliant |
| Machine and human catalog generated from the canonical files | `public/ontologies/index.json`, `public/ontologies/index.html` | generated | compliant |
| Snapshot tool builds and verifies the mirror | `scripts/snapshot-ontology-version.py` | `--check` path | compliant |
| Normative schema and JSON-LD context stay in MIF | `schema/ontology/ontology.schema.json` | unchanged | compliant |
| Each ontology's `id`/`version` is unchanged across mirrors | `public/ontologies/*.ontology.*` | `id`/`version` | compliant |

**Summary:** The corpus is served at `mif-spec.dev/ontologies/` with canonical
files plus immutable `0.1.0/`, `latest/`, and `v0/` mirrors, a machine
`index.json`, and a human `index.html`, all generated by
`snapshot-ontology-version.py` (whose `--check` passes against the committed
mirror). The normative ontology schema and context remain in MIF, and each
ontology's `id`/`version` is unchanged across mirrors.

**Action Required:** None.
