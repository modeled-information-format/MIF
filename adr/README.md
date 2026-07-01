---
id: reference-mif-adr-index
type: semantic
created: '2026-06-30T12:00:00Z'
modified: '2026-06-30T12:00:00Z'
namespace: reference/adr
title: Architecture Decision Records
tags:
  - reference
  - adr
  - index
temporal:
  '@type': TemporalMetadata
  validFrom: '2026-06-30T00:00:00Z'
  recordedAt: '2026-06-30T12:00:00Z'
  ttl: P1Y
relationships:
  - type: relates-to
    target: ADR-018-ontology-corpus-dedicated-repository-and-serving.md
ontology:
  '@type': OntologyReference
  id: mif-docs
  version: 1.0.0
  uri: https://mif-spec.dev/ontologies/mif-docs
entity:
  name: Architecture Decision Records
  entity_type: reference-document
---

# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Modeled Information Format (MIF) project.

## Format

ADRs follow the **Structured MADR** format — an extension of [MADR](https://adr.github.io/madr/) (Markdown Architectural Decision Records) that adds YAML frontmatter, full risk-assessed option analysis, split Positive/Negative/Neutral consequences, and a required code-grounded Audit section.

## Index

| ADR | Title | Status | Description |
|-----|-------|--------|-------------|
| [ADR-001](ADR-001-cognitive-triad-taxonomy.md) | Cognitive Triad Taxonomy | Accepted | Adopts the cognitive triad (semantic, episodic, procedural) as the foundational concept taxonomy — MIF's answer to OKF's absent concept-type system |
| [ADR-002](ADR-002-dual-format-design.md) | Dual-Format Design (Markdown + JSON-LD) | Accepted | Supports both Markdown and JSON-LD as first-class formats (refined by ADR-011: Markdown is canonical) |
| [ADR-003](ADR-003-obsidian-compatibility.md) | Obsidian Compatibility | Superseded (by ADR-017) | Originally adopted Obsidian-specific conventions (wiki-links, `@[[]]`, block references); reverted by ADR-017 for vendor neutrality |
| [ADR-004](ADR-004-three-tier-trait-inheritance.md) | Three-Tier Trait Inheritance | Accepted | Defines a three-level trait inheritance model: mif-base, shared-traits, domain ontologies |
| [ADR-005](ADR-005-underscore-namespace-prefix.md) | Underscore Namespace Prefix Convention | Accepted | Uses underscore prefix for base-type namespace directories to distinguish from domain content |
| [ADR-006](ADR-006-entitydata-vs-entityreference.md) | EntityData vs EntityReference | Accepted | Distinguishes inline structured entity data from lightweight entity references |
| [ADR-007](ADR-007-github-raw-urls-for-schema-ids.md) | GitHub Raw URLs for Schema IDs | Accepted (amended → mif-spec.dev) | Originally used GitHub raw URLs for schema $id values; amended to use mif-spec.dev |
| [ADR-008](ADR-008-decay-model-rationale.md) | Decay Model Rationale | Accepted | Implements configurable exponential decay with half-life for memory relevance ranking |
| [ADR-009](ADR-009-okf-compliance-superset.md) | OKF Compliance as a Superset (Pinned OKF v0.1) | Accepted | MIF is a superset of a conformant OKF v0.1 bundle and pins the criteria — no floating dependency (Invariant 5) |
| [ADR-010](ADR-010-modeled-information-format-repositioning.md) | Repositioning to Modeled Information Format | Accepted | Renames/repositions MIF as a general OKF-compliant content model; AI memory becomes the first domain profile |
| [ADR-011](ADR-011-markdown-canonical-derived-jsonld.md) | Markdown-Canonical with Derived JSON-LD Projection | Accepted | Markdown `.md` is the source of truth; JSON-LD is a derived projection (Invariant 2) — refines ADR-002 |
| [ADR-012](ADR-012-okf-conformance-tested-invariant.md) | OKF Conformance Enforced as a Tested CI Invariant | Accepted | Enforces OKF conformance, lossless round-trip, schema, and ontology/namespace validity as gating CI checks |
| [ADR-013](ADR-013-provenance-lightweight-core-optional-prov-layer.md) | Provenance: Lightweight Core + Optional W3C-PROV Layer | Accepted | Lightweight provenance core (`sourceType`/`trustLevel`) plus an OPTIONAL, additive W3C-PROV-aligned layer (`wasGeneratedBy`/`wasAttributedTo`/`wasDerivedFrom`); full PROV graphs stay optional |
| [ADR-014](ADR-014-document-reference-not-embed.md) | Document References, Not Embedded Vendor Schema | Accepted | Source documents travel by vendor-neutral `DocumentReference` (pointer + integrity metadata), not by embedding a vendor model like DoclingDocument (reframes issue #77) |
| [ADR-015](ADR-015-attested-release-orchestration.md) | Attested Release Orchestration | Accepted | Every release is SLSA-attested (provenance + CycloneDX SBOM, fail-closed verify), with the full SAST/DAST/SCA/posture gate suite wired by SHA pin to the org's central reusable workflows |
| [ADR-016](ADR-016-versioned-schema-mirror-publication.md) | Per-Version Schema Mirror Publication | Accepted | Each release publishes an immutable versioned schema mirror (`/schema/X.Y.Z/`, `latest/`, `vMAJOR/`) served by the doc site, keeping canonical `$id` values unversioned per ADR-007 |
| [ADR-017](ADR-017-revert-obsidian-compatibility.md) | Revert Obsidian Compatibility | Accepted | Supersedes ADR-003: drops Obsidian-specific notation (wiki-links, `@[[]]`, block references, embeds) for vendor-neutral CommonMark with markdown-link relationships and frontmatter `EntityReference`s |
| [ADR-018](ADR-018-ontology-corpus-dedicated-repository-and-serving.md) | Ontology Corpus: Dedicated Repository, Flat Layout, and Versioned Serving | Accepted (propagation amended by ADR-019) | Resolves discussion #168: ontologies live in the dedicated `ontologies` repo (source of record) while the schema/context stay in MIF; served at `mif-spec.dev/ontologies/` with immutable corpus-release mirrors per the ADR-016 model |
| [ADR-019](ADR-019-deploy-time-attested-ontology-vendoring.md) | Deploy-Time, Attestation-Verified Ontology Vendoring | Proposed | Amends ADR-018's propagation mechanism: the deploy fetches the ontologies repo's signed release tarball and fail-closed verifies it with `gh attestation verify`, replacing the committed `public/ontologies/` mirror and its unbuilt PR-propagation follow-up |

## Creating New ADRs

1. Copy the structure from a recent ADR (e.g. [ADR-009](ADR-009-okf-compliance-superset.md)) as the Structured MADR exemplar
2. Use sequential numbering: `ADR-NNN-short-title.md`
3. Fill in all sections: frontmatter, Status, Context, Decision Drivers, Considered Options (with risk assessments), Decision, Consequences (Positive/Negative/Neutral), Decision Outcome, Related Decisions, Links, More Information, and Audit
4. In the **Audit** section, cite only `file:line` anchors you have opened and confirmed; if a finding cannot be confirmed, set the audit `Status: Pending` rather than inventing a citation
5. Update this index and link related ADRs bidirectionally via the `related` frontmatter

## Status Values

Structured MADR frontmatter uses the standard MADR status enum:

- **proposed** - Under discussion
- **accepted** - Decision approved and in effect
- **deprecated** - No longer recommended
- **superseded** - Replaced by another ADR

An amended decision keeps `status: accepted` and documents the change in its `## Status` line plus an `## Amendment` section (see [ADR-007](ADR-007-github-raw-urls-for-schema-ids.md)).
