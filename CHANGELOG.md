# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **[Schema]**: EntityData field for ontology-typed memories
  - New `entity` property with `name` (required), `entity_type`, and `entity_id` fields
  - Supports additional properties defined by ontology entity_type schemas
  - Links structured data to ontology definitions

- **[Schema]**: Block references field
  - New `blocks` object for named block references (`^block-id`)
  - Maps block identifiers to their text content for granular linking

- **[Schema]**: Shared EntityReference definition
  - Extracted to `schema/definitions/entity-reference.schema.json`
  - Reused by both MIF schema and Citation schema
  - Prevents definition divergence across schemas

- **[Schema]**: Ontology `extends` field for inheritance
  - Ontologies can declare parent ontologies to inherit from
  - Enables trait inheritance model: `mif-base → shared-traits → domain`
  - Added to ontology.schema.json and all domain ontologies

- **[Project]**: VERSION.json for centralized version constants
  - Specification version, schema versions, ontology versions
  - Single source of truth for all version numbers

### Changed

- **[Schema]**: Standardized schema identifiers to `https://mif-spec.dev/schema/` namespace
  - Updated ontology.schema.json `$id`
  - Updated all domain ontology `schema_url` fields
  - Note: These are identifiers, not resolvable URLs

- **[Schema]**: Discovery patterns structure updated
  - Split single `patterns[]` into `content_patterns[]` and `file_patterns[]`
  - Each pattern type has specialized fields for its use case
  - Aligns schema with actual mif-base ontology usage

- **[Examples]**: Updated JSON-LD context property names
  - Changed `dc:created` to `created`, `dc:modified` to `modified`
  - Consistent with unprefixed field names in specification

- **[Examples]**: Clarified Level 1 conformance requirements
  - `namespace` is recommended but optional at Level 1
  - Level 1 only requires: `id`, `type`, `created`, and content body

### Fixed

- **[Examples]**: Fixed ontology reference format in example memories
  - Changed from incorrect `ontology.entity_type` to proper `ontology.id` + `entity` block
  - Updated 6 example memory files across agriculture, publishing, biology-lab directories

- **[Documentation]**: Added trait inheritance documentation to ontologies/README.md
  - Documents the three-tier trait system
  - Explains how domain ontologies inherit from shared-traits

- **[Documentation]**: Added decay model rationale (Section 9.3)
  - Explains P7D/P14D/P30D half-life values as pragmatic defaults
  - Documents scientific background from Ebbinghaus forgetting curve
  - Cites Murre & Dros (2015), Squire & Bayley (2007), Wickelgren (1972)
  - Provides guidance for tuning values per memory type

### Changed

- **[Schema]**: Memory types now use three base types
  - Replaced ad-hoc types (`memory`, `decision`, `preference`, `fact`, `episode`, `pattern`, `learning`, `context`)
  - New base types: `semantic` (facts/knowledge), `episodic` (events/experiences), `procedural` (processes/how-to)
  - Specific categorization expressed through namespace hierarchy (e.g., `_semantic/decisions`, `_episodic/incidents`)
  - Ontologies can extend types via entity_types with `base` field
  - **BREAKING**: Existing memories using old type values need migration

### Added

- **[Schema]**: OntologyReference field in MIF schema
  - New `ontology` property for declaring which ontology a memory applies
  - Fields: `id` (required), `version` (optional), `uri` (optional)
  - Enables validation that memories conform to declared ontology
  - Links MIF documents to ontology definitions

- **[Ontology]**: Industry-specific ontology examples
  - `regenerative-agriculture.ontology.yaml` - Farm operations, carbon credits, certifications
  - `k12-educational-publishing.ontology.yaml` - K-12 curriculum, state adoptions
  - `biology-research-lab.ontology.yaml` - Academic research, grants, compliance
  - `backstage.ontology.yaml` - Developer portal entity catalog
  - `shared-traits.ontology.yaml` - Reusable trait mixins

- **[Backstage]**: Backstage.io catalog integration examples
  - Example catalog-info.yaml files for each industry ontology
  - MIF-to-Backstage entity mapping via annotations

- **[Ontology]**: Three-type namespace hierarchy
  - Base ontology with semantic/episodic/procedural top-level namespaces
  - Nine sub-namespaces: decisions, knowledge, entities, incidents, sessions, blockers, runbooks, patterns, migrations
  - Entity type definitions with traits and schemas
  - Relationship types with cardinality constraints
  - Discovery patterns for content and file-based detection

- **[Ontology]**: JSON-LD semantic web support
  - `ontology.context.jsonld` for semantic vocabulary mapping
  - `yaml2jsonld.py` converter script
  - Alignment with Schema.org and SKOS vocabularies

- **[Schema]**: Ontology validation schema
  - `schema/ontology/ontology.schema.json` for YAML validation
  - Supports hierarchical namespace children
  - Entity type and relationship validation

- **[Specification]**: Initial MIF (Memory Interchange Format) specification
  - JSON-LD based format for AI memory interoperability
  - Bi-temporal model with valid time and transaction time
  - W3C PROV-compliant provenance tracking
  - Conformance levels (Core, Extended, Full)
  - Human-readable Markdown export support

- **[Specification]**: Citations structure (Level 3 optional feature)
  - Structured citation references with type/role taxonomy
  - Required fields: type, title, url, role
  - Optional fields: author, date, accessed, relevance, note
  - Entity references in author field using wiki-link syntax
  - Citation types: article, book, paper, website, documentation, repository, video, podcast, specification, dataset, tool
  - Citation roles: supports, refutes, background, methodology, contradicts, extends, derived, source, example, review
  - Frontmatter YAML schema and body section Markdown syntax
  - JSON-LD vocabulary with Schema.org alignment
  - Validation rules (Section 5.5.7) with field constraints and error handling
  - Appendix D: Citations Quick Reference

- **[Specification]**: Compression fields (Level 3 optional feature)
  - `summary` - Concise 2-3 sentence summary (max 500 characters)
  - `compressed_at` - Timestamp when compression was applied
  - Compression criteria: Age > 30 days AND lines > 100, OR Strength < 0.3 AND lines > 100

- **[Schema]**: JSON Schema for automated validation
  - `schema/mif.schema.json` - Complete MIF document validation
  - `schema/citation.schema.json` - Standalone citation object validation
  - Draft 2020-12 compliant schemas with comprehensive type definitions

- **[Examples]**: Reference MIF document examples
  - Basic memory interchange examples
  - Entity and relationship examples
  - Temporal metadata examples
  - Level 3 citations example (level-3-citations.memory.md/.json)

### Changed

- **[README]**: Updated to reflect new features
  - Added Citations and JSON Schema to Key Features table
  - Added Validation section with schema usage examples
  - Updated Level 3 conformance to include citations and compression
  - Updated examples description

- **[CONTRIBUTING]**: Added JSON Schema validation guidance

### Documentation

- **[Research]**: Comprehensive market research report
  - Competitive landscape analysis (Mem0, Zep, Letta, LangMem, Cognee, Graphlit)
  - Standards alignment review (JSON-LD, RDF/OWL, ONNX, PROV)
  - Enterprise requirements assessment (EU AI Act, GDPR, NIST AI RMF)
  - Adoption strategy recommendations

- **[Research]**: Executive brief for decision support
  - Market opportunity summary ($2.1B SAM)
  - Competitive positioning analysis
  - Prioritized action items

- **[Research]**: Trend models and forecasting
  - Market growth projections (2024-2030)
  - Technology adoption S-curve
  - Scenario analysis (standard adoption vs fragmentation)
  - Regulatory impact timeline (EU AI Act milestones)

## [0.1.0] - 2026-01-23

### Added

- Initial project setup
- MIF specification draft v0.1
- Market research framework

[Unreleased]: https://github.com/modeled-information-format/MIF/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/modeled-information-format/MIF/releases/tag/v0.1.0
