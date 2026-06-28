---
title: "Versioned Schema Mirror Publication on Every Release"
description: "On every MIF release, an immutable per-version mirror of the JSON Schemas is committed to public/schema/<version>/ and bundled into the release artifact, while canonical $id values remain unversioned and stable per ADR-007."
type: adr
category: schema
tags:
  - schema
  - versioning
  - json-schema
  - mirrors
  - release
  - json-ld
status: accepted
created: 2026-06-27
updated: 2026-06-27
author: MIF Maintainers
project: MIF
technologies:
  - json-schema
  - json-ld
  - github-pages
audience:
  - developers
  - architects
related:
  - ADR-007-github-raw-urls-for-schema-ids.md
  - ADR-015-attested-release-orchestration.md
  - ADR-011-markdown-canonical-derived-jsonld.md
---

# ADR-016: Versioned Schema Mirror Publication on Every Release

## Status

Accepted

## Context

### Background and Problem Statement

ADR-007 established that every MIF JSON Schema carries an unversioned, stable
`$id` (e.g. `https://mif-spec.dev/schema/mif.schema.json`). Those canonical
URLs resolve to the current release and are the values embedded in every
`$id` and `$ref` in the schema set. Canonical identity stays stable across
releases by design, and this ADR does not change that.

The problem addressed here is separate: a consumer that validates against the
current canonical URL cannot pin an exact, reproducible schema snapshot.
Between releases the canonical schemas can change, so a validator run today
against `https://mif-spec.dev/schema/mif.schema.json` and the same run six
months from now may use different schema bytes. There is no current way to
point at the schema set that existed at, for example, `v1.0.0`.

Additionally, the release artifact has historically had no schema bundle.
Consumers who want offline validation must reconstruct the schema set from the
git tag, which is an undocumented, manual step. A self-contained schema bundle
in each release eliminates this gap.

### Current Limitations

- No version-pinned schema URLs: consumers cannot reference an exact,
  immutable snapshot by URL.
- No machine-readable catalog of all schemas, their canonical URLs, and
  versioned mirror paths.
- Release artifacts do not include a schema bundle; offline validation
  requires manual reconstruction from a git tag.
- The `public/schema/` directory has no per-version subdirectories, so the
  Astro/Starlight doc site at `mif-spec.dev` serves only the current schemas.

## Decision Drivers

### Primary Decision Drivers

1. **Immutability**: A consumer that pins `/schema/1.0.0/mif.schema.json` must
   get the same bytes forever; the version path is a promise that cannot be
   revised.
2. **$id stability**: The canonical `$id` in every mirrored file must remain
   the unversioned URL (per ADR-007); the version path is an access address,
   not a new identity.
3. **Attestability**: The mirror must be committed source, not a build-time
   ephemeral, so the release bundle has a reviewable, attestable origin.
4. **Fail-closed release gate**: A release tag must never ship without its
   mirror; the release workflow must verify the mirror is present and abort if
   it is missing.

### Secondary Decision Drivers

1. **Discoverability**: A machine-readable catalog (`index.json`) lets tooling
   enumerate all schemas and resolve versioned or alias URLs without scraping
   the site.
2. **Consistency with the doc site**: The mirror lives in `public/schema/`,
   which the Astro/Starlight build serves at `mif-spec.dev/schema/`, so
   schema availability is bound to the same deploy that publishes the spec.
3. **Offline use**: The release artifact `mif-schemas-<version>.tar.gz` lets
   consumers validate offline without a git checkout.

## Considered Options

### Option 1: Version the canonical $id per release

**Description**: Change each schema's `$id` from the unversioned URL to a
versioned URL (e.g. `https://mif-spec.dev/schema/1.0.0/mif.schema.json`) on
each release.

**Advantages**:

- The `$id` itself encodes the version; no additional mirror infrastructure
  is needed.

**Disadvantages**:

- Breaks every published reference that cites the current canonical `$id`.
  Any document, validator, or data file that embeds
  `https://mif-spec.dev/schema/mif.schema.json` would be pointing at the
  wrong identity after the first release.
- Contradicts ADR-007, which was adopted precisely to keep `$id` values
  stable.
- Relative `$ref` resolution inside the schema set would break across version
  boundaries.

**Risk Assessment**:

- **Technical Risk**: High. Breaking change to every downstream that cites
  the canonical `$id`.

### Option 2: Build-time-only mirror generation with no committed source

**Description**: Generate the version mirrors at Astro build time from the
canonical files in `public/schema/`. Nothing is committed; the mirrors exist
only in the deployed `dist/` tree.

**Advantages**:

- No extra committed files; the repo stays slim.

**Disadvantages**:

- The deployed mirror has no reviewable, attestable source in the repo. SLSA
  provenance applies to what is committed; ephemeral build outputs are not
  independently verifiable.
- The release bundle cannot include a schema snapshot sourced from committed
  artifacts; it would have to be assembled at release time from build output,
  adding complexity and a point of failure.
- The release workflow cannot verify the mirror is present before tagging,
  so the fail-closed gate cannot be implemented against committed state.

**Risk Assessment**:

- **Technical Risk**: Medium. Attestation gap and release workflow complexity.

### Option 3: Committed per-version mirrors with a release-prep script (chosen)

**Description**: Each release adds an immutable, committed subdirectory
`public/schema/<version>/` containing verbatim copies of the canonical schema
files. Moving aliases (`latest/`, `vMAJOR/`) are refreshed at the same time.
The machine-readable catalog `public/schema/index.json` is updated to record
the new version. A release-prep script (`scripts/snapshot-schema-version.py`)
performs these writes; its `--check` flag verifies the mirror is present and
current. The release workflow fails closed if the mirror directory is absent,
preventing a tag from shipping without its schema snapshot.

**Advantages**:

- Mirrors are reviewable, committed source; SLSA attestation covers them.
- Fail-closed gate is straightforward: the workflow runs `--check` and aborts
  on failure.
- The release bundle (`mif-schemas-<version>.tar.gz`) is assembled directly
  from committed files.
- No `$id` change; ADR-007 is fully preserved.
- The Astro/Starlight deploy serves all committed mirrors automatically, so
  deploying `main` publishes canonical and versioned schemas together.

**Disadvantages**:

- Each release adds committed files to `public/schema/`; the directory grows
  over time.
- The release-prep step must not be forgotten; the workflow gate enforces this.

**Risk Assessment**:

- **Technical Risk**: Low. Additive, mechanical, and gated by the workflow.

## Decision

On every MIF release, an immutable per-version mirror of the canonical JSON
Schemas is published as committed source under `public/schema/<version>/`.

### Mirror layout

The following URL patterns are served by the Astro/Starlight doc site at
`mif-spec.dev/schema/`:

| Path | Mutability | Description |
|------|------------|-------------|
| `/schema/<file>` | moves with releases | canonical; current release; `$id` target |
| `/schema/X.Y.Z/<file>` | immutable | exact snapshot of release `vX.Y.Z` |
| `/schema/latest/<file>` | moving alias | always the newest published release |
| `/schema/vMAJOR/<file>` | moving alias | newest release in that major line |

`<file>` is a schema filename, e.g. `mif.schema.json`,
`definitions/entity-reference.schema.json`, `context.jsonld`.

### $id invariant

The `$id` field inside every mirrored file remains the canonical unversioned
URL (e.g. `https://mif-spec.dev/schema/mif.schema.json`). The version path is
an access address only; it does not create a new schema identity. Relative
`$ref` values in a mirrored copy resolve against the canonical schema set by
design, because the `$id` graph stays canonical. This preserves ADR-007
without exception.

### Mirrored files

The following files are copied verbatim into each version mirror:

- `mif.schema.json`
- `citation.schema.json`
- `context.jsonld`
- `definitions/entity-reference.schema.json`
- `ontology/ontology.schema.json`
- `ontology/ontology.context.jsonld`

Documentation files (e.g. `ontology/README.md`) are canonical-only and are
not mirrored; they live only under `/schema/ontology/`.

### Machine-readable catalog

`public/schema/index.json` is updated by the release-prep script to record
the new version in `versions[]`, update `specVersion` to the newest, refresh
`aliases` (`latest` and `vMAJOR`), and add the new versioned URL for every
schema entry. The catalog is the authoritative source for tooling that needs
to enumerate all schemas or resolve alias URLs.

### Release-prep tooling

`scripts/snapshot-schema-version.py X.Y.Z` is the canonical release-prep
command. It:

1. Copies the current canonical files into `public/schema/X.Y.Z/`.
2. Refreshes `public/schema/latest/` and `public/schema/vMAJOR/` with the
   same bytes.
3. Updates `public/schema/index.json` (versions, specVersion, aliases,
   per-schema versioned URLs).

`--check` mode verifies the mirror for `X.Y.Z` is present and byte-identical
to the current canonical files, writing nothing; it exits non-zero on any
discrepancy.

The script is run as a release-prep step before tagging. The result is
reviewed and committed; the release workflow then verifies the committed mirror
is present via `--check` and fails closed if it is not.

### Release artifact

The release workflow (ADR-015, `release.yml`) bundles
`public/schema/<version>/` into `mif-schemas-<version>.tar.gz` and attaches
it to the GitHub Release. The workflow fails closed if `public/schema/<version>/`
is absent; a tag cannot ship without its schema mirror committed to source.

### Published versions to date

| Version | Mirror path |
|---------|-------------|
| 0.1.0 | `public/schema/0.1.0/` |
| 1.0.0 | `public/schema/1.0.0/` |

The `v2` major alias path is reserved for the first `2.x` release.

### Media type

The intended media type for schema files is `application/schema+json`. GitHub
Pages serves `.json` files as `application/json` and does not support
per-file `Content-Type` overrides. Hosts that can configure response headers
should serve `application/schema+json`; consumers should not rely on the
served `Content-Type` for schema detection.

## Consequences

### Positive

1. **Pinnable, immutable schema URLs**: Consumers can reference an exact
   release snapshot and get the same bytes forever.
2. **$id stability preserved**: ADR-007 is fully honored; no published
   reference is broken.
3. **Attestable mirrors**: Committed source means SLSA provenance covers every
   schema snapshot; the release bundle is assembled from auditable artifacts.
4. **Fail-closed release gate**: A tag cannot ship without its mirror; the
   `--check` flag in the workflow enforces this automatically.
5. **Offline validation**: `mif-schemas-<version>.tar.gz` gives consumers a
   self-contained schema set without requiring a git checkout.
6. **Machine-readable catalog**: `index.json` enables tooling to enumerate
   schemas and resolve versioned or alias URLs programmatically.

### Negative

1. **Growing `public/schema/` directory**: Each release adds a committed
   subdirectory. Over many releases this accumulates; there is no pruning
   policy because immutability is the guarantee.
2. **Release-prep discipline required**: Maintainers must run
   `snapshot-schema-version.py` and commit the result before tagging. The
   workflow gate enforces this but does not automate the snapshot step itself.

### Neutral

1. **Doc site serves all mirrors automatically**: The Astro/Starlight build
   copies everything under `public/` into `dist/`; no build plugin or
   redirect configuration is needed for the version paths.
2. **`$ref` resolution in mirrors**: Because the `$id` inside each mirrored
   file is the canonical unversioned URL, a validator that follows `$ref`
   values from within a mirror will fetch the canonical schemas, not the
   mirrored ones. This is the intended behavior: the mirror pins bytes, the
   `$id` graph stays canonical.

## Decision Outcome

The versioned-mirror approach meets all four primary drivers: pinned version
paths give immutable, byte-stable URLs; the canonical unversioned `$id` is
preserved in every mirror (per ADR-007); the mirror is committed source, so
SLSA provenance covers each snapshot; and the release workflow's `--check` gate
fails closed when a mirror is missing. The secondary drivers are also satisfied:
an `index.json` catalog for discovery, doc-site-served version paths, and an
offline `mif-schemas-<version>.tar.gz`.

Mitigations for the negatives: the growing `public/schema/` directory is accepted
as the cost of the immutability guarantee (no pruning, by design); the
release-prep discipline of running `snapshot-schema-version.py` before tagging is
backed by the fail-closed gate, which blocks a tag whose mirror is absent.

## Implementation

### Release-prep sequence

Before tagging a release `vX.Y.Z`:

1. Confirm all schema changes for the release are committed to `main`.
2. Run `python3 scripts/snapshot-schema-version.py X.Y.Z`.
3. Verify the output: inspect `public/schema/X.Y.Z/`, `latest/`, `vMAJOR/`,
   and `index.json`.
4. Commit the result: `git add public/schema/ && git commit`.
5. Tag the release; push the tag.

The release workflow then runs `python3 scripts/snapshot-schema-version.py X.Y.Z --check`
as an early step and fails the run if the check exits non-zero.

### Adding a new schema file to the mirror set

To add a new canonical schema file to the mirror, update the `MIRRORED_FILES`
list in `scripts/snapshot-schema-version.py` and add the corresponding entry
to the `schemas` array in `public/schema/index.json`. All future releases will
include the new file. Retroactively mirroring the new file into past version
directories is neither required nor recommended, as those mirrors are immutable
records of what existed at that release.

## Related Decisions

- [ADR-007: GitHub Raw URLs for Schema IDs](ADR-007-github-raw-urls-for-schema-ids.md) -- the constraint this decision must not violate: canonical `$id` values are unversioned and stable.
- [ADR-015: Attested Release Orchestration](ADR-015-attested-release-orchestration.md) -- the release workflow that enforces the fail-closed gate and bundles the schema archive.
- [ADR-011: Markdown-Canonical with Derived JSON-LD](ADR-011-markdown-canonical-derived-jsonld.md) -- the JSON-LD context files (`context.jsonld`, `ontology/ontology.context.jsonld`) that are part of the mirrored set.

## Links

- [`public/schema/VERSIONING.md`](../public/schema/VERSIONING.md) -- the prose description of the mirror model this ADR formalizes.
- [`public/schema/index.json`](../public/schema/index.json) -- the machine-readable schema catalog.
- [`scripts/snapshot-schema-version.py`](../scripts/snapshot-schema-version.py) -- the release-prep tool.

## More Information

- **Date:** 2026-06-27
- **Source:** `public/schema/VERSIONING.md`; `public/schema/index.json`; `scripts/snapshot-schema-version.py`; `.github/workflows/release.yml`.
- **Related ADRs:** ADR-007, ADR-011, ADR-015

## Audit

### 2026-06-27

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Per-version immutable mirrors exist for every released version | `public/schema/0.1.0/`, `public/schema/1.0.0/` | directory trees | compliant |
| `latest/` and `v1/` aliases match the canonical (newest) schema set | `public/schema/latest/`, `public/schema/v1/` | directory trees | compliant |
| Catalog lists versions, aliases, and per-schema versioned URLs | `public/schema/index.json` | `versions`/`aliases`/`schemas` | compliant |
| Snapshot tool produces and verifies a version mirror | `scripts/snapshot-schema-version.py` | `--check` path | compliant |
| Release bundles the mirror and fails closed if it is absent | `.github/workflows/release.yml` | schema-bundle step | compliant |
| Canonical `$id` values remain unversioned per ADR-007 | `public/schema/*.schema.json` | `$id` | compliant |

**Summary:** The committed mirror set, the `latest`/`v0`/`v1` aliases, and the
`index.json` catalog are present and consistent. `snapshot-schema-version.py
1.0.0 --check` passes against the committed 1.0.0 mirror, and the release
workflow's schema-bundle step exits non-zero when the version mirror directory is
missing. Canonical `$id` values stay unversioned, preserving ADR-007.

**Action Required:** None.
