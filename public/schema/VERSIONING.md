# Schema serving & versioning

MIF JSON Schemas are served at `https://mif-spec.dev/schema/` from this directory.

## Canonical identity (unchanged — ADR-007)

Each schema's `$id` is an **unversioned, stable** URL, e.g.
`https://mif-spec.dev/schema/mif.schema.json`. These canonical URLs always
resolve to the current release and are the values referenced by `$id`/`$ref`.
Release-to-release versioning of the canonical identity is by git tag
(`v1.0.0`, ...), per ADR-007 (adr/ADR-007-github-raw-urls-for-schema-ids.md).

## Versioned mirrors (additive)

For consumers who need to pin an exact, immutable release, each schema is also
published at version-pathed mirrors — **without changing the `$id`**:

Here `<file>` is a schema's actual filename — e.g. `mif.schema.json`,
`citation.schema.json`, `definitions/entity-reference.schema.json`,
`ontology/ontology.schema.json`, or `context.jsonld`.

| Access | Path | Mutability |
| --- | --- | --- |
| Canonical (latest) | `/schema/<file>` | moves with releases |
| Exact version | `/schema/0.1.0/<file>`, `/schema/1.0.0/<file>` | immutable |
| Moving alias | `/schema/latest/<file>` | tracks newest release |
| Major alias | `/schema/v0/<file>` (newest 0.x), `/schema/v1/<file>` (newest 1.x) | `v2` reserved for 2.0.0 |

Every published version mirror is an exact, immutable snapshot of that
release's schema set, committed during release prep and carried unchanged by
the release tag (e.g. `/schema/1.4.1/` ← tag `v1.4.1`). The published versions
and aliases are listed in [`index.json`](./index.json).

The internal `$id` of every mirrored copy remains the canonical unversioned URL;
the version path is an additional access location, not a new schema identity.
Because the `$id` stays canonical, a relative `$ref` inside a mirror resolves
against the canonical schema set by design (the mirror pins the bytes, the
`$id`/`$ref` graph stays canonical). Every schema declares
`$schema: https://json-schema.org/draft/2020-12/schema`. The mirrors carry schema
files only; documentation (e.g. the ontology README) lives canonically under
`/schema/ontology/`.

[`index.json`](./index.json) is the machine-readable catalog of all schemas,
their canonical URLs, versioned paths, and alias resolution.

## Media type

The intended media type is `application/schema+json`. GitHub Pages serves `.json`
as `application/json` and does not support per-file `Content-Type` overrides;
hosts that can set it should serve `application/schema+json`.

## Cutting a new release

1. On the release-prep branch, bump the repo-root `VERSION.json` and run
   `python3 scripts/snapshot-schema-version.py <version>`: it snapshots the
   canonical schema set into `/schema/<version>/` (immutable; `$id` unchanged),
   refreshes `/schema/latest/` and the major alias (`/schema/vN/`), and updates
   `aliases` + `versions` in `index.json`.
2. Merge the release-prep PR, then tag the release (`vMAJOR.MINOR.PATCH`). The
   full procedure is `docs/RELEASING.md`.
