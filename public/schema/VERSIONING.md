# Schema serving & versioning

MIF JSON Schemas are served at `https://mif-spec.dev/schema/` from this directory.

## Canonical identity (unchanged — ADR-007)

Each schema's `$id` is an **unversioned, stable** URL, e.g.
`https://mif-spec.dev/schema/mif.schema.json`. These canonical URLs always
resolve to the current release and are the values referenced by `$id`/`$ref`.
Release-to-release versioning of the canonical identity is by git tag
(`v0.1.0`, ...), per [ADR-007](../../adr/ADR-007-github-raw-urls-for-schema-ids.md).

## Versioned mirrors (additive)

For consumers who need to pin an exact, immutable release, each schema is also
published at version-pathed mirrors — **without changing the `$id`**:

| Access | Path | Mutability |
| --- | --- | --- |
| Canonical (latest) | `/schema/<name>.json` | moves with releases |
| Exact version | `/schema/0.1.0/<name>.json` | immutable |
| Moving alias | `/schema/latest/<name>.json` | tracks newest release |
| Major alias | `/schema/v0/<name>.json` | newest 0.x (`v1` reserved for 1.0.0) |

The internal `$id` of every mirrored copy remains the canonical unversioned URL;
the version path is an additional access location, not a new schema identity.
Every schema declares `$schema: https://json-schema.org/draft/2020-12/schema`.

[`index.json`](./index.json) is the machine-readable catalog of all schemas,
their canonical URLs, versioned paths, and alias resolution.

## Media type

The intended media type is `application/schema+json`. GitHub Pages serves `.json`
as `application/json` and does not support per-file `Content-Type` overrides;
hosts that can set it should serve `application/schema+json`.

## Cutting a new release

1. Bump `VERSION.json`.
2. Copy the current top-level schema set into `/schema/<new-version>/`.
3. Refresh `/schema/latest/` and the matching major alias (`/schema/vN/`); update
   `aliases` + `versions` in `index.json`.
4. Tag the release.
