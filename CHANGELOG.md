# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (proposed)

- **Container Profile (ADR-021)** — an OPTIONAL, single-file `*.corpus.json`
  transport envelope that serializes a Bundle (or a subset of one) for wire
  transport: `schema/container.schema.json`, `schema/container-context.jsonld`,
  `schema/document-reference.schema.json`, `scripts/validate_container.py`,
  a `container-validation` CI job, a worked example under
  `examples/container/`, and `docs/CONTAINER-PROFILE.md`. Vendor-specific
  corpus metadata (compression manifests, version DAGs) routes through a
  generalized `extensions` mechanism rather than becoming native MIF
  vocabulary. Proposed — ADR-021's `Status` stays `Proposed` pending
  `@perlowja`'s confirmation on issue #77.

### Added

- **[Tooling]**: `scripts/check_relationship_type_vocab_coverage.py` — cross-checks
  `schema/context.jsonld`'s `relationships.type.@context` term mapping against
  `public/ns/vocabulary.jsonld`'s registered `rdfs:Class` terms, guarding against
  the #230 defect class (a relationship-type term declared in one file but never
  wired to the other) recurring. Wired into the `okf-conformance` CI job. (#233)
- **[Tooling]**: `scripts/test_temporal_and_properties.py` (temporal-consistency
  and `properties`-construct regression suite) is now run in the `okf-conformance`
  CI job via `pytest`; previously it only ran if a contributor had `pytest`
  installed locally and remembered to invoke it by hand. (#235)

## [1.2.2] - 2026-07-04

### Fixed

- **Release workflow: draft-first publication** — the workflow now triggers
  on the version tag push, creates the release itself as a draft after all
  attestations verify fail-closed, uploads the attested artifacts to the
  draft, and publishes last via the release App identity. Under the repo's
  immutable-releases setting the previous publish-then-upload flow could
  never attach assets (HTTP 422 at upload); the v1.2.0 and v1.2.1 release
  slots remain published but assetless for this reason. v1.2.2 is the first
  release carrying its attested artifacts.

## [1.2.1] - 2026-07-04

### Fixed

- **JSON-LD context: `accessed` typed `xsd:date`** — the context declared
  `xsd:dateTime` while both `citation.schema.json` and `mif.schema.json`
  constrain `accessed` to `format: date` (YYYY-MM-DD, not a valid
  `xsd:dateTime` lexical form); the context now agrees with the schemas,
  matching the sibling `date` term.
- **Release workflow: SBOM release attach removed** (#210) — the SBOM
  generation action attempted to attach the raw SBOM file to the release
  under the job's read-only `GITHUB_TOKEN` and failed every
  release-published run; the verified App-token upload step already
  publishes the SBOM alongside the attested artifacts. No attestation or
  verification step changed.
- The v1.2.0 GitHub release object was deleted during failure recovery
  and cannot be recreated (immutable releases); the `v1.2.0` tag and its
  content remain. v1.2.1 is the attested release for the 1.2 line.

## [1.2.0] - 2026-07-04

### Added

- **Entity-type classification fields** (ADR-020) — the ontology schema's
  `entity_type` definition gains three optional, additive string-array
  fields supporting confidence-tiered embedding-based classification:
  `aliases` (synonyms/label variations, `skos:altLabel`), `exemplars`
  (curated canonical examples, `skos:example`), and `negative_examples`
  (curated near-misses from confusable type pairs,
  `https://mif-spec.dev/ns/ontology#negativeExample`). Ontology schema version
  1.0.0 -> 1.1.0; `yaml2jsonld.py` projects the new fields; existing
  ontologies carrying only `description` remain valid.

## [1.1.0] - 2026-06-30

### Breaking Changes

- **[Format]**: Removed all Obsidian-specific conventions for vendor neutrality
  (ADR-017, superseding ADR-003) — wiki-link relationships (`[[...]]`),
  `@[[Name|Type]]` entity references, block references, and embeds, plus the
  Obsidian-compatibility positioning. Relationships use markdown links; entity
  references use frontmatter `EntityReference` objects. The `blocks` field is
  removed from the schema and converter; existing data still carrying a `blocks`
  object continues to validate (the concept object permits additional
  properties).

### Added

- **Serve the canonical ontology corpus at `mif-spec.dev/ontologies/`** (#186) —
  the org's domain ontologies are published and resolvable at the custom domain.
- **Serve the object vendoring index and the layered v0.2.0 corpus** (#193,
  ADR-0002) — the registry `index.json` is reconciled to object entries each
  carrying a `sha256` field, so downstream consumers fail-closed vendor pinned
  ontology packs.

### Changed

- Reconcile base-type namespace prefixes with §10.2 of the specification (#182).
- Mark v1.0.0 Released and bring `SPECIFICATION.md` to lint-clean (#173).

### Fixed

- **Serve the JSON-LD namespace IRI at `mif-spec.dev/ns/`** (#166) — the
  namespace IRI used by the published context now resolves at the custom domain.

## [1.0.0] - 2026-06-28

### Breaking Changes

- **[Format]**: Concept files use the `.md` extension only — the `.memory.md`
  infix is **removed** (an OKF concept ID is the path minus `.md`). The
  `.memory.json` sidecar is replaced by a derived `*.jsonld` projection.
- **[Format]**: Markdown is now the **canonical** representation; JSON-LD is a
  derived, regenerable projection (`scripts/mif_convert.py`). Lossless
  `markdown → json-ld → markdown` round-trip is a tested invariant.
- **[Relationships]**: Typed relationships are authoritative in the frontmatter
  `relationships` array **and** mirrored as OKF-legible body markdown links in a
  `## Relationships` section (`- <type> [Text](/path/target.md)`). Obsidian
  wiki-links are no longer the canonical edge representation.
- **[Identity]**: `id` MUST be a UUID (OKF concept ID is the path; the UUID is
  MIF's stable, location-independent identity). Legacy slug ids migrate to a
  deterministic UUIDv5 with the slug preserved as an `alias`.
- **[Schema]**: `schema/mif.schema.json` v1.0 — `@type: Concept`, `conceptType`
  replaces required `memoryType` (kept as a deprecated alias), and the
  `Relationship` shape is `{ type, target }`.
- **[Schema]**: Memory types now use three base types — replaced ad-hoc types
  (`memory`, `decision`, `preference`, `fact`, `episode`, `pattern`, `learning`,
  `context`) with `semantic` (facts/knowledge), `episodic` (events/experiences),
  and `procedural` (processes/how-to). Specific categorization is expressed
  through the namespace hierarchy (e.g. `_semantic/decisions`,
  `_episodic/incidents`); ontologies can extend types via `entity_types` with a
  `base` field. **Existing memories using old type values need migration.**
- **[Temporal]**: The bi-temporal/decay model is reframed as **validity windows
  & freshness** (answering OKF's open live-vs-stale question). The math is
  unchanged; the forgetting-curve/Ebbinghaus rationale moves to the AI Memory
  profile.
- **[Profile]**: All memory-specific normative material (decay tuning, episodic
  *session* framing, retrieval embeddings, and the Mem0/Zep/Letta/Subcog/
  Basic-Memory migration guides) moves out of the core into
  `profiles/ai-memory/`.

### Added

- **[Release]**: Attested release orchestration (ADR-015). `release.yml` builds
  and attests the source tarball and the schema bundle with SLSA build
  provenance (the source tarball additionally carries a CycloneDX SBOM),
  fail-closed verified before publish. The full security-gate suite (CodeQL,
  Semgrep, OSV, Trivy, Checkov, secrets, ShellCheck, Scorecard, and on-demand
  ZAP DAST) is wired by SHA pin to the org's central reusable workflows.
  Artifact verification is documented in `SECURITY.md`.
- **[Schema]**: Per-version schema mirror publication (ADR-016) with
  `scripts/snapshot-schema-version.py`, producing immutable `/schema/X.Y.Z/`,
  `latest/`, and `vMAJOR/` mirrors for each release while canonical `$id` values
  stay unversioned (ADR-007).
- **[OKF]**: `docs/okf-conformance.md` — pinned OKF v0.1 conformance criteria
  (version-stamped) and the MIF → OKF mapping. MIF takes no normative dependency
  on OKF's live draft (Invariant 5).
- **[OKF]**: Reserved filenames `index.md` / `log.md` adopted verbatim.
- **[Positioning]**: "MIF answers OKF's open questions" table in both
  `README.md` and `SPECIFICATION.md`.
- **[Tooling]**: `scripts/okf_validate.py` (conformance + relationship sync +
  round-trip), `scripts/mif_convert.py` (markdown↔json-ld), and
  `scripts/migrate_0_1_to_1_0.py` (0.1→1.0 transform).
- **[Tooling]**: `scripts/okf_validate.py` temporal-consistency check — a
  `derived-from` / `supersedes` / `cites` target must not be `created` after the
  concept that derives from it. Warns by default; `--strict-temporal` promotes it
  to a failing check once a corpus is known clean. (#79)
- **[Schema]**: first-class scalar `properties` field (string / number / boolean /
  null) for literal-object knowledge-graph triples that have no concept `target`.
  Additive and backward compatible. (#79)
- **[Schema]**: Entity-type subsumption — optional `subtype_of` field on entity types.
  - A type may declare `subtype_of: [parent, ...]`; a subtype is substitutable for any
    of its supertypes wherever the supertype is admissible (e.g. a relationship endpoint
    domain). Optional and additive — existing ontologies are unaffected.
  - Projected to JSON-LD as `mif:subtypeOf` (`scripts/yaml2jsonld.py`,
    `ontology.context.jsonld`).
  - `scripts/validate-ontologies.py` enforces integrity across the whole ontology
    corpus: every parent resolves to a declared type (in the ontology or one it
    `extends`, resolved over the full chain), a subtype's `required` set includes each
    parent's (substitutability), no self-reference, acyclic graph. Covered by
    `scripts/test_subtype_of.py` (+ `test/subtype_of/` fixtures, run in CI). Demonstrated
    by `software-engineering` `security-incident` `subtype_of: [incident-report]`.
  - `scripts/validate-ontologies.py` now validates schema conformance with **ajv**
    (draft2020, matching the JSON-LD validation job) instead of Python `jsonschema`.
- **[Schema]**: EntityData field for ontology-typed memories.
  - New `entity` property with `name` (required), `entity_type`, and `entity_id` fields.
  - Supports additional properties defined by ontology entity_type schemas.
  - Links structured data to ontology definitions.
- **[Schema]**: Block references field.
  - New `blocks` object for named block references (`^block-id`).
  - Maps block identifiers to their text content for granular linking.
- **[Schema]**: Shared EntityReference definition.
  - Extracted to `schema/definitions/entity-reference.schema.json`.
  - Reused by both MIF schema and Citation schema; prevents definition divergence.
- **[Schema]**: Ontology `extends` field for inheritance.
  - Ontologies can declare parent ontologies to inherit from.
  - Enables the trait inheritance model: `mif-base → shared-traits → domain`.
  - Added to `ontology.schema.json` and all domain ontologies.
- **[Schema]**: OntologyReference field in MIF schema.
  - New `ontology` property declaring which ontology a memory applies.
  - Fields: `id` (required), `version` (optional), `uri` (optional).
  - Enables validation that memories conform to their declared ontology.
- **[Schema]**: Ontology validation schema.
  - `schema/ontology/ontology.schema.json` for YAML validation.
  - Supports hierarchical namespace children; entity-type and relationship validation.
- **[Schema]**: JSON Schema for automated validation.
  - `schema/mif.schema.json` — complete MIF document validation.
  - `schema/citation.schema.json` — standalone citation object validation.
  - Draft 2020-12 compliant schemas with comprehensive type definitions.
- **[Schema]**: additive versioned schema mirrors under `public/schema/` —
  `1.0.0/` (immutable), `latest/`, major alias `v1/`, plus `index.json` (catalog)
  and `VERSIONING.md`. Canonical `$id` values are unchanged (ADR-007). (#72)
- **[Schema]**: immutable `0.1.0/` schema mirror and `v0/` alias snapshotted from
  the v0.1.0 tag; `index.json` extended (`v0` → 0.1.0, `v1` → 1.0.0). (#73)
- **[Project]**: `VERSION.json` for centralized version constants (specification,
  schema, and ontology versions) — single source of truth for all version numbers.
- **[Profile]**: `profiles/ai-memory/` — profile spec, ontology, and examples.
- **[Ontology]**: Industry-specific ontology examples.
  - `regenerative-agriculture.ontology.yaml` — farm operations, carbon credits, certifications.
  - `k12-educational-publishing.ontology.yaml` — K-12 curriculum, state adoptions.
  - `biology-research-lab.ontology.yaml` — academic research, grants, compliance.
  - `backstage.ontology.yaml` — developer portal entity catalog.
  - `shared-traits.ontology.yaml` — reusable trait mixins.
- **[Ontology]**: Three-type namespace hierarchy.
  - Base ontology with semantic/episodic/procedural top-level namespaces.
  - Nine sub-namespaces: decisions, knowledge, entities, incidents, sessions, blockers, runbooks, patterns, migrations.
  - Entity type definitions with traits and schemas; relationship types with cardinality constraints; discovery patterns for content- and file-based detection.
- **[Ontology]**: JSON-LD semantic web support.
  - `ontology.context.jsonld` for semantic vocabulary mapping; `yaml2jsonld.py` converter.
  - Alignment with Schema.org and SKOS vocabularies.
- **[Backstage]**: Backstage.io catalog integration examples.
  - Example `catalog-info.yaml` files for each industry ontology.
  - MIF-to-Backstage entity mapping via annotations.
- **[Specification]**: Initial MIF specification.
  - JSON-LD based format for AI memory interoperability.
  - Bi-temporal model with valid time and transaction time.
  - W3C PROV-compliant provenance tracking; conformance levels (Core, Extended, Full).
  - Human-readable Markdown export support.
- **[Specification]**: Citations structure (Level 3 optional feature).
  - Structured citation references with type/role taxonomy.
  - Required fields: type, title, url, role. Optional: author, date, accessed, relevance, note.
  - Entity references in the author field using wiki-link syntax.
  - Citation types: article, book, paper, website, documentation, repository, video, podcast, specification, dataset, tool.
  - Citation roles: supports, refutes, background, methodology, contradicts, extends, derived, source, example, review.
  - Frontmatter YAML schema and body-section Markdown syntax; JSON-LD vocabulary with Schema.org alignment.
  - Validation rules (Section 5.5.7) with field constraints and error handling; Appendix D quick reference.
- **[Specification]**: Compression fields (Level 3 optional feature).
  - `summary` — concise 2-3 sentence summary (max 500 characters).
  - `compressed_at` — timestamp when compression was applied.
  - Compression criteria: Age > 30 days AND lines > 100, OR Strength < 0.3 AND lines > 100.
- **[Examples]**: Reference MIF document examples.
  - Basic memory interchange examples; entity and relationship examples; temporal metadata examples.
  - Level 3 citations example (`level-3-citations.memory.md/.json`).
- **[Docs]**: `MIGRATION.md` upgrade guide (`0.1.0-draft → 1.0.0`).
- **[CI]**: `validate.yml` runs the OKF conformance + lossless round-trip tests
  and validates the JSON-LD projection against the schema.
- **[CI]**: `schema-check.yml` — meta-validates every schema set as JSON Schema
  2020-12, parses all JSON-LD contexts, and verifies mirror alias consistency
  (`latest` == canonical, `v1` == 1.0.0, `v0` == 0.1.0) as a required gate. (#75)
- **[Brand]**: `mif-brand` applied to the spec site — chevron-M logos, two-accent
  brand CSS, favicon. (#72)

### Changed

- **[Ontology]**: Base ontology re-motivated as a general knowledge taxonomy
  (declarative / time-bound / how-to); memory-only framing removed.
- **[Schema]**: Standardized schema identifiers to the
  `https://mif-spec.dev/schema/` namespace — updated `ontology.schema.json` `$id`
  and all domain ontology `schema_url` fields (identifiers, not resolvable URLs).
- **[Schema]**: Discovery patterns structure updated — split a single `patterns[]`
  into `content_patterns[]` and `file_patterns[]`, each with specialized fields;
  aligns the schema with actual mif-base ontology usage.
- **[Examples]**: Core `examples/` regenerated as a generalized (non-memory)
  bundle; memory examples relocated to `profiles/ai-memory/examples/`.
- **[Examples]**: Updated JSON-LD context property names — `dc:created` → `created`,
  `dc:modified` → `modified`, consistent with unprefixed field names.
- **[Examples]**: Clarified Level 1 conformance — `namespace` is recommended but
  optional; Level 1 requires only `id`, `type`, `created`, and a content body.
- **[Docs]**: ecosystem docs rehomed from the spec site to `doc-site`; the
  Starlight spec site is trimmed to spec-only content (sidebar and index). (#72)
- **[CI]**: `validate.yml` actions are SHA-pinned (org policy) and the workflow
  runs on all pull requests (PR path filter removed) so it can serve as a required
  gate. (#74)
- **[README]**: Updated to reflect new features — Citations and JSON Schema in the
  Key Features table, a Validation section with schema usage, Level 3 conformance
  updated for citations and compression.
- **[CONTRIBUTING]**: Added JSON Schema validation guidance.

### Removed

- **[Tooling]**: `scripts/validate-memories.py` and `scripts/test-conversion.py`
  superseded by `okf_validate.py` + `mif_convert.py`.

### Fixed

- **[Tooling]**: `scripts/mif_convert.py` restores `compressedAt` and `memoryType`
  to the round-trip passthrough; both were silently dropped on
  `markdown → json-ld → markdown`, breaking the lossless invariant. A regression
  test now enumerates every top-level schema field so a dropped field fails CI. (#79)
- **[Tooling]**: the temporal check skips targets that resolve outside the bundle
  (no out-of-bundle reads) and no longer crashes on a malformed-YAML target. (#79)
- **[Examples]**: Fixed ontology reference format in example memories — changed from
  incorrect `ontology.entity_type` to proper `ontology.id` + `entity` block across
  6 example memory files (agriculture, publishing, biology-lab).

### Documentation

- **[Documentation]**: Added trait inheritance documentation to
  `ontologies/README.md` — documents the three-tier trait system and how domain
  ontologies inherit from shared-traits.
- **[Documentation]**: Added decay model rationale (Section 9.3) — explains
  P7D/P14D/P30D half-life defaults, the Ebbinghaus forgetting-curve background
  (Murre & Dros 2015, Squire & Bayley 2007, Wickelgren 1972), and per-type tuning.
- **[Research]**: Comprehensive market research report — competitive landscape
  (Mem0, Zep, Letta, LangMem, Cognee, Graphlit), standards alignment (JSON-LD,
  RDF/OWL, ONNX, PROV), enterprise requirements (EU AI Act, GDPR, NIST AI RMF),
  adoption strategy.
- **[Research]**: Executive brief — market opportunity ($2.1B SAM), competitive
  positioning, prioritized action items.
- **[Research]**: Trend models and forecasting — growth projections (2024-2030),
  technology adoption S-curve, scenario analysis, regulatory impact timeline.

### Migration

See [MIGRATION.md](MIGRATION.md) and run
`python scripts/migrate_0_1_to_1_0.py <old> <new>`.

## [0.1.0] - 2026-01-23

### Added

- Initial project setup
- MIF specification draft v0.1
- Market research framework

[Unreleased]: https://github.com/modeled-information-format/MIF/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/modeled-information-format/MIF/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/modeled-information-format/MIF/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/modeled-information-format/MIF/releases/tag/v0.1.0
