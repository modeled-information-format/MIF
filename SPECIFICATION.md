<!-- diataxis_type: reference -->

# MIF — Modeled Information Format

**Version**: 1.0.0
**Status**: Release
**Last Updated**: 2026-06-18
**Authors**: Robert Allen (zircote)
**Repository**: https://github.com/modeled-information-format/MIF

---

## Abstract

MIF (Modeled Information Format) is an opinionated, OKF-compliant content model
for agent-readable knowledge. The Open Knowledge Format (OKF) defines a minimal
interoperability surface — a directory of markdown files with YAML frontmatter,
one required `type` field, a concept graph of standard markdown links, and the
reserved filenames `index.md` and `log.md` — and **deliberately refuses to
define a content model**. MIF fills that envelope: it supplies a concrete type
system, typed relationships, provenance/trust tiers, and validity/freshness
semantics.

> **MIF is the opinionated, OKF-compliant content model that fills OKF's
> deliberately empty envelope.** OKF is the transport surface; MIF supplies the
> concrete type system. AI memory is the first domain profile of MIF, not its
> identity (see `profiles/ai-memory/`).

OKF compliance is achieved as a **superset, not by subordination**: every MIF
bundle MUST validate as a conformant OKF bundle, but MIF remains an independent
specification with its own identity model and governance. MIF takes **no
normative dependency** on OKF's evolving draft — it pins OKF v0.1's conformance
criteria in [`docs/okf-conformance.md`](docs/okf-conformance.md), which is
normative within MIF (Invariant 5).

MIF is designed to be:
- **OKF-compliant**: every bundle is a valid OKF bundle (a tested invariant).
- **Markdown-canonical**: the `.md` file is the source of truth; JSON-LD is a
  derived projection (Invariant 2).
- **Human-Readable**: valid Obsidian-compatible notes in any Markdown editor.
- **Machine-Processable**: JSON-LD with semantic web compatibility.
- **Extensible**: domain profiles extend the base without breaking compatibility.

### MIF answers OKF's open questions

This table is the positioning thesis: it states what MIF supplies for each
question OKF leaves open.

| OKF open design space | MIF's opinionated answer |
| --- | --- |
| No concept-type taxonomy | `semantic` / `episodic` / `procedural` base types |
| Untyped markdown-link edges | Typed relationships (overlay on OKF links) |
| No merge / contradiction semantics | `Supersedes`, `ConflictsWith` |
| No trust tiers | Provenance `source_type` + `trust_level` |
| Stale-vs-live left to process | Validity windows + TTL/freshness |
| No provenance | W3C PROV |
| Markdown only | First-class JSON-LD projection |

---

## Table of Contents

1. [Terminology](#1-terminology)
2. [Design Principles](#2-design-principles)
3. [File Format](#3-file-format)
4. [Data Model](#4-data-model)
5. [Markdown Format (.md)](#5-markdown-format-md)
6. [JSON-LD Projection (derived)](#6-json-ld-projection-derived)
7. [Entity Types](#7-entity-types)
8. [Relationship Types](#8-relationship-types)
9. [Temporal Model](#9-temporal-model)
10. [Namespace Model](#10-namespace-model)
11. [Embedding References](#11-embedding-references)
12. [Provenance](#12-provenance)
13. [Conformance Levels](#13-conformance-levels)
14. [JSON-LD Context](#14-json-ld-context)
15. [Conversion Rules](#15-conversion-rules)
16. [Examples](#16-examples)
17. [Migration Guides](#17-migration-guides)
18. [Security Considerations](#18-security-considerations)
19. [IANA Considerations](#19-iana-considerations)

---

## 1. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

### Definitions

- **Memory**: A discrete unit of information captured from or about an AI interaction, including its content, metadata, relationships, and provenance.
- **Memory Unit**: The atomic element of MIF; a single memory with its associated data.
- **Entity**: A named thing (person, organization, technology, concept, or file) that can participate in relationships.
- **Relationship**: A typed, directed connection between two entities or between a memory and an entity.
- **Namespace**: A hierarchical scope for organizing memories (e.g., `org/user/project/session`).
- **Vault**: A collection of MIF files, analogous to an Obsidian vault.
- **Provider**: An AI memory system that can import or export MIF format.

---

## 2. Design Principles

### 2.1 Dual Representation

MIF defines two equivalent representations:

1. **Markdown Format** (`.md`): Human-readable, Obsidian-compatible
2. **JSON-LD Format** (`.jsonld`): Machine-processable, semantically linked

Both representations MUST be losslessly convertible to each other. A conforming implementation MAY support either or both formats.

### 2.2 Obsidian Compatibility

The Markdown format MUST be valid Obsidian notes, ensuring files work seamlessly in Obsidian vaults while remaining readable in any text editor or Markdown processor.

**Required Obsidian Features:**

- **YAML Frontmatter**: Structured metadata at the top of files, enclosed in `---` delimiters. Obsidian's Properties panel reads and writes this data, supporting typed fields (text, number, date, checkbox, list).

- **Wiki-Links**: Internal links using double-bracket syntax `[[Target Note]]` enable bidirectional linking. Obsidian automatically tracks backlinks, enabling graph visualization and relationship discovery. Links can include display text `[[Target|Display Text]]` and heading anchors `[[Target#Heading]]`.

- **Block References**: Unique identifiers (`^block-id`) attached to paragraphs, list items, or other blocks enable granular linking and transclusion. References like `[[Note#^block-id]]` link to specific content within a file.

- **Aliases**: The `aliases` frontmatter property allows notes to be found and linked using alternative names, improving discoverability.

- **Tags**: Both inline `#tags` and frontmatter `tags: [a, b]` are supported, with hierarchical tags using forward slashes (`#category/subcategory`).

- **Standard Markdown**: All content uses CommonMark-compatible Markdown, ensuring portability to other tools and platforms.

**Optional Obsidian Extensions:**

- **Callouts**: Admonition blocks using `> [!type]` syntax for notes, warnings, tips, etc.
- **Embeds**: Transclusion using `![[Note]]` to embed content from other files
- **Dataview Queries**: Compatible with Dataview plugin for vault-as-database queries

### 2.3 Semantic Web Compatibility

The JSON-LD format MUST be valid JSON-LD 1.1:
- Use `@context` for vocabulary mapping
- Use `@id` for unique identifiers
- Use `@type` for entity classification
- Compatible with RDF tooling

### 2.4 Local-First

MIF is designed for local-first storage:
- No required network dependencies
- Files can be read with any text editor
- No proprietary database required
- Full user data ownership

---

## 3. File Format

### 3.1 File Extensions

| Extension | Format | MIME Type |
|-----------|--------|-----------|
| `.md` | Markdown | `text/markdown; variant=mif` |
| `.jsonld` | JSON-LD | `application/ld+json; profile="https://mif-spec.dev"` |

### 3.2 File Naming

Files SHOULD be named using the memory's identifier:

```
{id}.md
{id}.jsonld
```

Example:
```
550e8400-e29b-41d4-a716-446655440000.md
550e8400-e29b-41d4-a716-446655440000.jsonld
```

Human-readable names MAY be used when the `id` is specified in frontmatter:
```
dark-mode-preference.md
```

### 3.3 Directory Structure

A MIF vault SHOULD follow this structure:

```
vault/
├── .mif/                           # MIF configuration
│   ├── config.yaml                 # Vault configuration
│   ├── context.jsonld              # Local JSON-LD context
│   └── entities/                   # Entity definitions
│       ├── person/
│       ├── organization/
│       ├── technology/
│       ├── concept/
│       └── file/
├── memories/                       # Memory files
│   ├── {namespace}/               # Namespace directories
│   │   ├── {id}.md
│   │   └── {id}.jsonld
│   └── ...
└── README.md                       # Vault documentation
```

---

## 4. Data Model

### 4.1 Memory Unit

A Memory Unit is the atomic element of MIF. It contains:

| Property | Required | Type | Description |
|----------|----------|------|-------------|
| `id` | REQUIRED | UUID | Globally unique identifier |
| `content` | REQUIRED | String | The memory content (Markdown) |
| `type` | REQUIRED | Enum | Memory classification (see 4.2) |
| `created` | REQUIRED | DateTime | When the memory was created |
| `modified` | RECOMMENDED | DateTime | When last modified |
| `ontology` | RECOMMENDED | Object | Reference to applied ontology (see 4.3) |
| `namespace` | RECOMMENDED | String | Hierarchical scope |
| `tags` | OPTIONAL | Array | Classification tags |
| `entities` | OPTIONAL | Array | Referenced entities |
| `relationships` | OPTIONAL | Array | Typed relationships |
| `temporal` | OPTIONAL | Object | Temporal validity data |
| `provenance` | OPTIONAL | Object | Source and trust data |
| `embedding` | OPTIONAL | Object | Embedding reference |
| `citations` | OPTIONAL | Array | Citation references (Level 3) |
| `summary` | OPTIONAL | String | Compressed content summary (Level 3) |
| `compressed_at` | OPTIONAL | DateTime | When compression was applied (Level 3) |
| `extensions` | OPTIONAL | Object | Provider-specific data |

### 4.2 Memory Types

MIF uses three **base memory types**, reflecting how human memory systems organize information:

| Type | Description | Namespace Hint |
|------|-------------|----------------|
| `semantic` | Facts, concepts, relationships, and knowledge | `semantic/*` |
| `episodic` | Events, experiences, sessions, and timelines | `episodic/*` |
| `procedural` | Step-by-step processes, runbooks, and patterns | `procedural/*` |

**Base Type Descriptions:**

- **Semantic**: Declarative knowledge about the world—facts, concepts, decisions, preferences, and relationships between entities. Examples: architectural decisions, technology choices, user preferences, domain knowledge.

- **Episodic**: Time-bound experiences and events—incidents, conversations, sessions, and blockers. These memories have strong temporal context and represent "what happened."

- **Procedural**: How-to knowledge—runbooks, migration guides, code patterns, and step-by-step processes. These memories describe "how to do" something.

#### 4.2.1 Ontology-Extended Types

Ontologies MAY define extended types using namespace prefixes:

```yaml
# In ontology definition
entity_types:
  - name: decision
    base: semantic
    description: "Architectural or design decision"
  - name: runbook
    base: procedural
    description: "Step-by-step operational guide"
  - name: incident
    base: episodic
    description: "Production incident record"
```

When using ontology-extended types, the `type` field uses the base type, while specific categorization is expressed through the namespace:

```yaml
---
type: semantic
namespace: _semantic/decisions
ontology:
  id: mif-base
---
```

This allows ontologies to define rich taxonomies while maintaining interoperability through the base type foundation.

### 4.3 Ontology Reference

A Memory Unit MAY declare which ontology it conforms to using the `ontology` field:

| Property | Required | Type | Description |
|----------|----------|------|-------------|
| `id` | REQUIRED | String | Ontology identifier (matches `ontology.id` in ontology definition) |
| `version` | OPTIONAL | String | Semantic version (e.g., "1.0.0") |
| `uri` | OPTIONAL | URI | URL to the ontology definition file |

**Example:**

```yaml
ontology:
  id: regenerative-agriculture
  version: "1.0.0"
  uri: https://github.com/modeled-information-format/MIF/ontologies/examples/regenerative-agriculture.ontology.yaml
```

The `ontology.id` MUST match the `ontology.id` field in the referenced ontology definition file. This enables:
- Validation that namespace paths conform to the ontology's defined namespaces
- Discovery pattern matching for entity type suggestions
- Schema validation for entity-specific fields

---

## 5. Markdown Format (.md)

### 5.1 Structure

```markdown
---
# YAML Frontmatter (required)
id: uuid-here
type: semantic
created: 2026-01-15T10:30:00Z
---

# Title (optional, first H1)

Memory content in Markdown format.

## Relationships (optional section)

- relates-to [[Other Memory]]
- derived-from [[Source Memory]]

## Entities (optional section)

- mentions @[[Person Name]]
- uses @[[Technology Name]]
```

### 5.2 Frontmatter Schema

```yaml
---
# === REQUIRED ===
id: 550e8400-e29b-41d4-a716-446655440000  # UUID v4
type: semantic                              # Base type: semantic|episodic|procedural
created: 2026-01-15T10:30:00Z              # ISO 8601 datetime

# === RECOMMENDED ===
modified: 2026-01-20T14:22:00Z             # Last modification
ontology:                                   # Applied ontology reference
  id: mif-base                             # Ontology identifier
  version: "1.0.0"                         # Ontology version
  uri: https://mif-spec.dev/ontologies/mif-base  # Ontology identifier (not a resolvable URL)
namespace: org/user/project                 # Hierarchical scope
title: "Human-readable title"               # Display title
tags:                                       # Classification
  - preference
  - ui

# === OPTIONAL: Temporal ===
temporal:
  valid_from: 2026-01-15T00:00:00Z         # When fact becomes valid
  valid_until: null                         # When fact expires (null = indefinite)
  recorded_at: 2026-01-15T10:30:00Z        # When recorded (transaction time)
  ttl: P90D                                 # Time-to-live (ISO 8601 duration)
  decay:
    model: exponential                      # Decay model
    halfLife: P7D                          # Half-life duration
    strength: 0.85                          # Current strength (0-1)
  access_count: 5                           # Times accessed
  last_accessed: 2026-01-20T14:22:00Z      # Last access time

# === OPTIONAL: Provenance ===
provenance:
  source_type: user_explicit                # How memory was created
  source_ref: conversation:conv_456         # Reference to source
  agent: claude-3-opus                      # Creating agent
  confidence: 0.95                          # Confidence score (0-1)
  trust_level: user_stated                  # Trust classification

# === OPTIONAL: Embedding ===
embedding:
  model: text-embedding-3-small             # Embedding model
  model_version: "2024-01"                  # Model version
  dimensions: 1536                          # Vector dimensions
  source_text: "User prefers dark mode"     # Text that was embedded
  # Note: Actual vectors stored externally or in JSON-LD format

# === OPTIONAL: Aliases ===
aliases:
  - "Dark Mode Preference"
  - "UI Theme Choice"

# === OPTIONAL: Extensions ===
extensions:
  subcog:
    domain: user
    hash: sha256:abc123...
  custom_provider:
    custom_field: value
---
```

### 5.3 Wiki-Link Syntax

MIF extends Obsidian wiki-link syntax for typed relationships:

```markdown
# Basic link (RelatesTo relationship)
[[Other Memory]]

# Typed relationship
[[Other Memory|derives-from]]
[[Other Memory|supersedes]]

# Entity reference (prefixed with @)
@[[Person Name]]
@[[Technology Name|uses]]

# Block reference
[[Memory Name#^block-id]]

# With display text
[[Other Memory|derives-from|"See also"]]
```

### 5.4 Block References

Blocks can be referenced for granular linking:

```markdown
This is an important statement. ^important-point

- Key insight about the system ^insight-1
```

Referenced as: `[[Memory Name#^important-point]]`

### 5.5 Citations (Level 3)

Citations provide structured references to external sources that inform, support, or relate to the memory content. Citations are a Level 3 (Full) optional feature.

#### 5.5.1 Frontmatter Schema

```yaml
# === OPTIONAL: Citations (Level 3) ===
citations:
  - type: article                          # REQUIRED: Source category
    title: "Memory Systems in AI Agents"   # REQUIRED: Citation title
    url: https://arxiv.org/abs/2024.12345  # REQUIRED: Valid URL
    role: supports                         # REQUIRED: Relationship to memory
    author: "@[[Jane Smith|Person]]"       # OPTIONAL: Entity ref or text
    date: 2024-06-15                       # OPTIONAL: Publication date
    accessed: 2026-01-20                   # OPTIONAL: Access date
    relevance: 0.95                        # OPTIONAL: Relevance score (0-1)
    note: "Foundational paper on semantic memory"  # OPTIONAL: Annotation
```

#### 5.5.2 Citation Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `type` | REQUIRED | Enum | Source category (see 5.5.3) |
| `title` | REQUIRED | String | Citation title |
| `url` | REQUIRED | URI | Valid URL or URI |
| `role` | REQUIRED | Enum | Relationship to memory (see 5.5.4) |
| `author` | OPTIONAL | String | Entity reference or plain text |
| `date` | OPTIONAL | Date | Publication date (ISO 8601) |
| `accessed` | OPTIONAL | Date | Access date (ISO 8601) |
| `relevance` | OPTIONAL | Decimal | Relevance score (0.0-1.0) |
| `note` | OPTIONAL | String | Free-form annotation |

#### 5.5.3 Citation Types

| Type | Description | Example |
|------|-------------|---------|
| `article` | Journal article, blog post | arXiv paper, Medium article |
| `book` | Published book | O'Reilly book, academic text |
| `paper` | Conference/research paper | ACM paper, IEEE publication |
| `website` | General website | Documentation site, homepage |
| `documentation` | Technical documentation | API docs, user guides |
| `repository` | Code repository | GitHub repo, GitLab project |
| `video` | Video content | YouTube tutorial, conference talk |
| `podcast` | Podcast episode | Tech podcast, interview |
| `specification` | Technical specification | W3C spec, RFC document |
| `dataset` | Data source | Kaggle dataset, research data |
| `tool` | Software tool or service | SaaS product, CLI tool |
| `other` | Miscellaneous source | Catch-all category |

Custom types MAY use namespace prefixes: `acme:internal-memo`, `research:lab-notes`

#### 5.5.4 Citation Roles

| Role | Description | Use Case |
|------|-------------|----------|
| `supports` | Provides supporting evidence | Confirming research, alignment |
| `refutes` | Contradicts or disputes | Opposing viewpoint, correction |
| `background` | General context/reference | Related reading, foundation |
| `methodology` | Method or approach source | Technique borrowed, framework |
| `contradicts` | Conflicts with claims | Disagreement, alternative view |
| `extends` | Builds upon cited work | Evolution, expansion |
| `derived` | Direct derivation source | Adapted from, based on |
| `source` | Primary source material | Original data, quote |
| `example` | Illustrative example | Case study, demo |
| `review` | Critical review/analysis | Critique, evaluation |

Custom roles MAY use namespace prefixes: `research:replicates`, `legal:cites-precedent`

#### 5.5.5 Body Section Syntax

An optional `## Citations` section MAY appear in the memory body for detailed annotations. When present, corresponding entries MUST exist in frontmatter.

```markdown
## Citations

- [Memory Systems in AI Agents](https://arxiv.org/abs/2024.12345) by @[[Jane Smith|Person]] (2024)
  - **Type**: article
  - **Role**: supports
  - **Relevance**: 0.95
  - Foundational paper on semantic memory structures. Introduces bi-temporal
    model that informed MIF's temporal design.

- [Obsidian Help](https://help.obsidian.md/) by @[[Obsidian Team|Organization]]
  - **Type**: documentation
  - **Role**: background
  - **Accessed**: 2026-01-18
  - Reference for wiki-link syntax and block references.
```

#### 5.5.6 Author Entity References

Authors MAY use wiki-link syntax to reference MIF entities:

```yaml
# Single author entity
author: "@[[Jane Smith|Person]]"

# Multiple authors (comma-separated)
author: "@[[Jane Smith|Person]], @[[John Doe|Person]]"

# Organization author
author: "@[[Anthropic|Organization]]"

# Plain text (no entity reference)
author: "Jane Smith et al."
```

#### 5.5.7 Citation Validation

Implementations SHOULD validate citations according to these rules:

**Required Field Constraints:**

| Field | Constraint |
|-------|------------|
| `type` | MUST be a value from Section 5.5.3 or a custom namespaced type (e.g., `acme:memo`) |
| `title` | MUST be a non-empty string |
| `url` | MUST be a valid URI (http, https, or custom schemes) |
| `role` | MUST be a value from Section 5.5.4 or a custom namespaced role (e.g., `legal:precedent`) |

**Optional Field Constraints:**

| Field | Constraint |
|-------|------------|
| `author` | SHOULD be entity reference(s) `@[[Name\|Type]]` or plain text; multiple authors comma-separated |
| `date` | MUST be ISO 8601 date format (`YYYY-MM-DD`) |
| `accessed` | MUST be ISO 8601 date format (`YYYY-MM-DD`) |
| `relevance` | MUST be decimal between 0.0 and 1.0 inclusive |
| `note` | SHOULD be under 1000 characters; longer notes SHOULD use body section |

**Validation Errors:**

| Error | Severity | Action |
|-------|----------|--------|
| Missing required field | Error | Reject citation |
| Invalid `type` value | Warning | Accept with `type: "other"` fallback |
| Invalid `role` value | Warning | Accept with `role: "background"` fallback |
| Malformed URL | Error | Reject citation |
| `relevance` out of range | Warning | Clamp to 0.0-1.0 |
| Invalid date format | Warning | Accept as plain text |

### 5.6 Compression (Level 3)

Compression allows large memories to be summarized while preserving the original content. Compression is typically applied by garbage collection processes to reduce memory footprint while retaining semantic value.

#### 5.6.1 Compression Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `summary` | OPTIONAL | String | Concise 2-3 sentence summary (max 500 characters) |
| `compressed_at` | OPTIONAL | DateTime | When compression was applied (ISO 8601) |

**Frontmatter Schema:**

```yaml
# === OPTIONAL: Compression (Level 3) ===
summary: "User prefers dark mode for reduced eye strain during extended coding sessions. Applies to IDE, terminal, and web applications."
compressed_at: 2026-01-24T10:00:00Z
```

#### 5.6.2 Compression Criteria

Implementations MAY apply compression when memories meet these criteria:

| Condition | Threshold |
|-----------|-----------|
| Age AND Size | Age > 30 days AND content > 100 lines |
| Decay AND Size | Strength < 0.3 AND content > 100 lines |

#### 5.6.3 Compression Behavior

- The `content` field SHOULD be replaced with the compressed summary
- The original `content` MAY be preserved in `extensions.original_content`
- The `summary` field contains the generated summary text
- The `compressed_at` timestamp indicates when compression occurred
- Compressed memories retain all other metadata (relationships, entities, etc.)

#### 5.6.4 Compression Validation

| Field | Constraint |
|-------|------------|
| `summary` | MUST be 500 characters or fewer |
| `compressed_at` | MUST be ISO 8601 datetime format |

---

## 6. JSON-LD Projection (derived)

> **Markdown is canonical (Invariant 2).** The JSON-LD form below is a *derived*
> projection: regenerate it from the `.md` source with `scripts/mif_convert.py`.
> It MUST NOT use the `.md` extension (so OKF's `*.md` glob never ingests it) and
> MUST round-trip losslessly back to markdown. If the two disagree, markdown wins.

### 6.1 Structure

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:550e8400-e29b-41d4-a716-446655440000",

  "content": "User prefers dark mode for all applications",
  "memoryType": "semantic",
  "title": "Dark Mode Preference",

  "created": "2026-01-15T10:30:00Z",
  "modified": "2026-01-20T14:22:00Z",

  "namespace": "_semantic/preferences",
  "tags": ["preference", "ui", "accessibility"],

  "entities": [...],
  "relationships": [...],
  "temporal": {...},
  "provenance": {...},
  "embedding": {...},
  "extensions": {...}
}
```

### 6.2 Full Example

```json
{
  "@context": [
    "https://mif-spec.dev/schema/context.jsonld",
    {
      "prov": "http://www.w3.org/ns/prov#",
      "dc": "http://purl.org/dc/terms/",
      "subcog": "https://github.com/modeled-information-format/subcog/ns/"
    }
  ],
  "@type": ["Memory", "prov:Entity"],
  "@id": "urn:mif:550e8400-e29b-41d4-a716-446655440000",

  "content": "User prefers dark mode for all applications. This applies to:\n- IDE themes\n- Terminal colors\n- Web applications\n- Mobile apps",
  "memoryType": "semantic",
  "title": "Dark Mode Preference",

  "dc:created": "2026-01-15T10:30:00Z",
  "dc:modified": "2026-01-20T14:22:00Z",

  "ontology": {
    "@type": "OntologyReference",
    "id": "mif-base",
    "version": "1.0.0"
  },

  "namespace": "_semantic/preferences",
  "tags": ["preference", "ui", "accessibility"],
  "aliases": ["Dark Mode Preference", "UI Theme Choice"],

  "entities": [
    {
      "@type": "EntityReference",
      "entity": {"@id": "urn:mif:entity:person:jane-doe"},
      "role": "subject"
    },
    {
      "@type": "EntityReference",
      "entity": {"@id": "urn:mif:entity:concept:dark-mode"},
      "role": "topic"
    }
  ],

  "relationships": [
    {
      "@type": "Relationship",
      "relationshipType": "RelatesTo",
      "target": {"@id": "urn:mif:memory:ui-preferences"},
      "strength": 0.85
    },
    {
      "@type": "Relationship",
      "relationshipType": "Supersedes",
      "target": {"@id": "urn:mif:memory:old-theme-preference"}
    }
  ],

  "temporal": {
    "@type": "TemporalMetadata",
    "validFrom": "2026-01-15T00:00:00Z",
    "validUntil": null,
    "recordedAt": "2026-01-15T10:30:00Z",
    "ttl": "P90D",
    "decay": {
      "model": "exponential",
      "halfLife": "P7D",
      "currentStrength": 0.85
    },
    "accessCount": 5,
    "lastAccessed": "2026-01-20T14:22:00Z"
  },

  "provenance": {
    "@type": "prov:Entity",
    "sourceType": "user_explicit",
    "prov:wasGeneratedBy": {
      "@type": "prov:Activity",
      "prov:wasAssociatedWith": {
        "@id": "urn:mif:agent:claude-3-opus",
        "@type": "prov:SoftwareAgent"
      }
    },
    "prov:wasDerivedFrom": {
      "@id": "urn:mif:conversation:conv-456"
    },
    "prov:wasAttributedTo": {
      "@id": "urn:mif:entity:person:jane-doe"
    },
    "confidence": 0.95,
    "trustLevel": "user_stated"
  },

  "embedding": {
    "@type": "EmbeddingReference",
    "model": "text-embedding-3-small",
    "modelVersion": "2024-01",
    "dimensions": 1536,
    "sourceText": "User prefers dark mode for all applications",
    "vectorUri": "urn:mif:vector:550e8400-e29b-41d4-a716-446655440000"
  },

  "citations": [
    {
      "@type": "Citation",
      "citationType": "article",
      "citationRole": "supports",
      "title": "Dark Mode UI Benefits for Developer Productivity",
      "url": "https://example.com/dark-mode-research",
      "author": {
        "@type": "EntityReference",
        "entity": {"@id": "urn:mif:entity:person:jane-smith"},
        "entityType": "Person",
        "name": "Jane Smith"
      },
      "date": "2024-03-15",
      "accessed": "2026-01-18",
      "relevance": 0.92,
      "note": "Research supporting dark mode preference for reduced eye strain"
    }
  ],

  "extensions": {
    "subcog:domain": "user",
    "subcog:hash": "sha256:4c04b32ddc2053b5..."
  }
}
```

---

## 7. Entity Types

MIF provides an **extensible entity type system**. Implementations SHOULD support the core types for interoperability, but MAY define custom types for domain-specific needs.

### 7.1 Entity Type Architecture

Entity types are **not hard-coded**. They are defined in vault configuration and can be extended per-project:

```yaml
# .mif/config.yaml
entity_types:
  # Core types (RECOMMENDED for interoperability)
  - name: Person
    description: Human individual
    icon: 👤
    color: blue
  - name: Organization
    description: Company, team, or group
    icon: 🏢
    color: purple
  - name: Technology
    description: Tool, language, or framework
    icon: 🔧
    color: green
  - name: Concept
    description: Abstract idea or topic
    icon: 💡
    color: yellow
  - name: File
    description: Document or code file
    icon: 📄
    color: gray

  # Custom types (domain-specific)
  - name: Project
    description: Work initiative or product
    icon: 📦
    color: orange
  - name: Event
    description: Meeting, deadline, or occurrence
    icon: 📅
    color: red
  - name: Location
    description: Physical or virtual place
    icon: 📍
    color: teal
```

### 7.2 Core Entity Types (Recommended)

For maximum interoperability, implementations SHOULD recognize these five core types:

| Type | Description | Example | URI |
|------|-------------|---------|-----|
| `Person` | Human individual | User, team member | `mif:Person` |
| `Organization` | Company, team, or group | Acme Corp | `mif:Organization` |
| `Technology` | Tool, language, or framework | Python, React | `mif:Technology` |
| `Concept` | Abstract idea or topic | Dark Mode | `mif:Concept` |
| `File` | Document or code file | src/main.py | `mif:File` |

### 7.3 Custom Entity Types

Providers MAY define additional entity types using namespaced URIs:

```yaml
# Custom type definition
entity_types:
  - name: Animal
    namespace: farm        # Results in URI: farm:Animal
    description: Livestock or pet
    properties:
      - name: breed
        type: string
      - name: birth_date
        type: date
      - name: registry_id
        type: string
```

**JSON-LD representation of custom types:**

```json
{
  "@context": [
    "https://mif-spec.dev/schema/context.jsonld",
    {"farm": "https://example.org/farm/"}
  ],
  "@type": "farm:Animal",
  "@id": "urn:mif:entity:animal:sheep-001",
  "name": "Dolly",
  "farm:breed": "Dorper",
  "farm:birth_date": "2025-03-15"
}
```

### 7.4 Entity Schema

**Markdown (in `.mif/entities/` directory):**

```yaml
# .mif/entities/person/jane-doe.yaml
id: jane-doe
type: Person
name: Jane Doe
aliases:
  - J. Doe
  - jdoe
properties:
  email: jane@example.com
  role: Engineer
```

**JSON-LD:**

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Person",
  "@id": "urn:mif:entity:person:jane-doe",
  "name": "Jane Doe",
  "aliases": ["J. Doe", "jdoe"],
  "properties": {
    "email": "jane@example.com",
    "role": "Engineer"
  }
}
```

### 7.5 Entity References in Memories

**Markdown:**
```markdown
## Entities

- mentions @[[Jane Doe]]
- uses @[[Python|Technology]]
- about @[[Dark Mode|Concept]]
```

**JSON-LD:**
```json
"entities": [
  {
    "@type": "EntityReference",
    "entity": {"@id": "urn:mif:entity:person:jane-doe"},
    "role": "mentions"
  }
]
```

---

## 8. Relationship Types

MIF provides an **extensible relationship type system**. Implementations SHOULD support the core types for interoperability, but MAY define custom relationship types for domain-specific needs.

### 8.1 Relationship Type Architecture

Relationship types are **not hard-coded**. They are defined in vault configuration and can be extended per-project:

```yaml
# .mif/config.yaml
relationship_types:
  # Core types (RECOMMENDED for interoperability)
  - name: RelatesTo
    description: General semantic relationship
    symmetric: true
    icon: 🔗
  - name: DerivedFrom
    description: Memory created based on source
    inverse: Derives
    icon: ⬅️
  - name: Supersedes
    description: Replaces an older memory
    inverse: SupersededBy
    icon: ⏫
  - name: ConflictsWith
    description: Contradicts another memory
    symmetric: true
    icon: ⚠️
  - name: PartOf
    description: Component of a larger whole
    inverse: Contains
    icon: 🧩
  - name: Implements
    description: Realizes a concept or pattern
    inverse: ImplementedBy
    icon: ✅
  - name: Uses
    description: Utilizes a technology or tool
    inverse: UsedBy
    icon: 🔧
  - name: Created
    description: Authored by an entity
    inverse: CreatedBy
    icon: ✍️
  - name: MentionedIn
    description: Referenced within a memory
    inverse: Mentions
    icon: 📎

  # Custom types (domain-specific)
  - name: Reinforces
    namespace: subcog
    description: Strengthens confidence in another memory
    inverse: ReinforcedBy
    icon: 💪
  - name: Contradicts
    namespace: subcog
    description: Provides evidence against another memory
    inverse: ContradictedBy
    icon: ❌
  - name: BreedsWith
    namespace: farm
    description: Animal breeding relationship
    symmetric: false
    properties:
      - name: breeding_date
        type: date
      - name: success
        type: boolean
```

### 8.2 Core Relationship Types (Recommended)

For maximum interoperability, implementations SHOULD recognize these nine core types:

| Type | Description | Inverse | Symmetric |
|------|-------------|---------|-----------|
| `RelatesTo` | General relationship | `RelatesTo` | Yes |
| `DerivedFrom` | Created based on source | `Derives` | No |
| `Supersedes` | Replaces older memory | `SupersededBy` | No |
| `ConflictsWith` | Contradicts another memory | `ConflictsWith` | Yes |
| `PartOf` | Component of larger whole | `Contains` | No |
| `Implements` | Realizes a concept/pattern | `ImplementedBy` | No |
| `Uses` | Utilizes a technology/tool | `UsedBy` | No |
| `Created` | Authored by entity | `CreatedBy` | No |
| `MentionedIn` | Referenced in memory | `Mentions` | No |

### 8.3 Custom Relationship Types

Providers MAY define additional relationship types using namespaced URIs:

```yaml
# Custom relationship type definition
relationship_types:
  - name: Contradicts
    namespace: farm           # Results in URI: farm:Contradicts
    description: Provides conflicting evidence
    inverse: ContradictedBy
    properties:
      - name: contradiction_type
        type: string
        enum: [direct, indirect, partial]
      - name: severity
        type: decimal
        range: [0.0, 1.0]
```

**JSON-LD representation of custom relationship types:**

```json
{
  "@context": [
    "https://mif-spec.dev/schema/context.jsonld",
    {"farm": "https://example.org/farm/"}
  ],
  "relationships": [
    {
      "@type": "Relationship",
      "relationshipType": "farm:BreedsWith",
      "target": {"@id": "urn:mif:entity:animal:ram-001"},
      "strength": 1.0,
      "farm:breeding_date": "2025-10-15",
      "farm:success": true
    }
  ]
}
```

### 8.4 Relationship Schema

**Markdown syntax:**

Relationships use a simple `type [[target]]` format in a dedicated section:

```markdown
## Relationships

- relates-to [[Other Memory]]
- derived-from [[Source Memory]]
- supersedes [[Old Memory]]
- conflicts-with [[Contradicting Memory]]
- part-of [[Parent Memory]]
```

The relationship type name is converted to kebab-case in Markdown. The target uses wiki-link syntax `[[]]` which resolves to the memory's `@id` or title.

**JSON-LD schema:**

```json
"relationships": [
  {
    "@type": "Relationship",
    "relationshipType": "DerivedFrom",
    "target": {"@id": "urn:mif:memory:source-memory"},
    "strength": 0.9,
    "metadata": {
      "reason": "Extracted key insight",
      "extractedAt": "2026-01-15T10:30:00Z"
    }
  }
]
```

### 8.5 Relationship Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `@type` | String | Yes | Always `"Relationship"` |
| `relationshipType` | URI/Vocab | Yes | Type identifier (core or custom) |
| `target` | URI Reference | Yes | Target memory or entity URI |
| `strength` | Decimal | No | Relationship strength (0.0-1.0) |
| `metadata` | Object | No | Additional relationship metadata |

---

## 9. Temporal Model

MIF uses a bi-temporal model distinguishing between:

1. **Transaction Time**: When the memory was recorded in the system
2. **Valid Time**: When the fact represented by the memory is true

### 9.1 Temporal Properties

| Property | Type | Description |
|----------|------|-------------|
| `validFrom` | DateTime | When fact becomes valid |
| `validUntil` | DateTime | When fact expires (null = indefinite) |
| `recordedAt` | DateTime | When recorded (transaction time) |
| `ttl` | Duration | Time-to-live (ISO 8601 duration) |
| `decay` | Object | Decay model parameters |
| `accessCount` | Integer | Times accessed |
| `lastAccessed` | DateTime | Last access time |

### 9.2 Decay Models

| Model | Formula | Use Case |
|-------|---------|----------|
| `none` | No decay | Permanent memories |
| `linear` | strength = 1 - (t / ttl) | Simple linear decay |
| `exponential` | strength = e^(-t/halfLife) | Gradual freshness decay |
| `step` | strength = 1 if t < ttl else 0 | Hard expiration |

### 9.3 Freshness Rationale

In the core model, the temporal decay function expresses **freshness** — how
current a piece of knowledge is — and answers OKF's open "live vs. stale"
question. The decay half-life defaults (P7D, P14D, P30D) are **pragmatic
defaults** for how quickly knowledge of a given kind loses currency; they are
not prescriptive.

The `strength = e^(-t/halfLife)` curve models a value that is fully current when
recorded and decays gradually toward stale, with `validFrom`/`validUntil`
windows bounding the interval in which a fact is asserted to hold.

#### Why These Specific Values?

| Half-Life | Use Case | Rationale |
|-----------|----------|-----------|
| **P7D** | Short-term context | Aligns with weekly work cycles |
| **P14D** | Medium-term projects | Spans typical sprint/iteration boundaries |
| **P30D** | Long-term knowledge | Corresponds to monthly review cycles |
| **P90D** | Default TTL | Quarterly relevance for most organizational knowledge |

Implementations SHOULD tune these based on:
- Knowledge kind (`episodic` records go stale faster than `semantic` facts)
- Organizational context (high-velocity vs. stable environments)
- Access patterns (frequently accessed knowledge can reinforce slower decay)

The `lastAccessed` and `accessCount` fields let implementations model
reinforcement — each access can reset or slow the freshness decay.

> **Cognitive-memory origin.** This exponential curve originates in the
> cognitive-science account of human memory decay. That rationale — including
> the underlying experimental references and decay tuning for retrieval-oriented
> systems — now lives in the **AI Memory profile**
> (`profiles/ai-memory/SPECIFICATION.md`), keeping the core framed purely as
> freshness.

### 9.4 Example

```yaml
temporal:
  valid_from: 2026-01-15T00:00:00Z
  valid_until: null
  recorded_at: 2026-01-15T10:30:00Z
  ttl: P90D
  decay:
    model: exponential
    halfLife: P7D
    strength: 0.85
    last_reinforced: 2026-01-18T09:00:00Z
  access_count: 5
  last_accessed: 2026-01-20T14:22:00Z
```

---

## 10. Namespace Model

### 10.1 Namespace Structure

Namespaces use a flexible scoping model with reserved prefixes for cross-organization sharing:

```
{root}/{scope}+[/{session}]
```

Where `{root}` is either:
- **Organization name** - private to that organization
- **Reserved prefix** - special namespace with defined semantics

### 10.2 Reserved Namespace Prefixes

Names beginning with underscore (`_`) are reserved for special namespaces:

| Prefix | Visibility | Description |
|--------|------------|-------------|
| `_public` | Global | Publicly accessible by anyone |
| `_shared` | Negotiated | Cross-organization sharing with explicit agreements |
| `_local` | Local only | Never synchronized or exported |
| `_system` | Implementation | Reserved for system/implementation use |

**Examples:**

```
# Public knowledge (globally accessible)
_public/python/async-patterns
_public/react/hooks-best-practices
_public/security/owasp-top-10

# Shared between organizations (requires agreement)
_shared/cncf/kubernetes/patterns           # CNCF member consortium
_shared/acme+bigcorp/integration-api       # Bilateral agreement
_shared/industry-healthcare/hipaa-compliance

# Organization-private (default)
acme-corp/jane-doe/preferences
acme-corp/project-x/architecture-decisions
acme-corp/team-frontend/patterns
```

### 10.3 Flexible Scopes Within Organizations

Within an organization, scopes are **peer-level** - users, projects, teams, and other organizational units are treated equally:

```
{organization}/{scope}+

Examples:
- acme-corp/jane-doe                    # user scope
- acme-corp/project-x                   # project scope
- acme-corp/team-frontend               # team scope
- acme-corp/jane-doe/project-x          # user + project (order flexible)
- acme-corp/project-x/jane-doe          # same as above
- acme-corp/team-frontend/project-x     # team + project
```

**Key principle:** Within an organization, there is no enforced hierarchy between users, projects, or teams. The path segments represent scope intersection, not parent-child relationships.

### 10.4 Shared Namespace Agreements

The `_shared` prefix requires explicit agreements between organizations:

```yaml
# .mif/shared-agreements/acme+bigcorp.yaml
id: acme+bigcorp
type: bilateral
parties:
  - acme-corp
  - bigcorp-inc
created: 2026-01-15T00:00:00Z
namespaces:
  - _shared/acme+bigcorp/integration-api
  - _shared/acme+bigcorp/data-formats
access:
  read: [acme-corp, bigcorp-inc]
  write: [acme-corp, bigcorp-inc]
```

For consortiums or communities:

```yaml
# .mif/shared-agreements/cncf.yaml
id: cncf
type: consortium
admin: cncf-foundation
members:
  - google
  - microsoft
  - redhat
  # ... (member list or reference)
namespaces:
  - _shared/cncf/*
access:
  read: members
  write: approved-contributors
```

### 10.5 Custom Reserved Prefixes

Implementations MAY define additional reserved prefixes following the underscore convention:

```yaml
# .mif/config.yaml
reserved_prefixes:
  _archive:
    description: Archived memories (read-only)
    access: read-only
  _experimental:
    description: Experimental/unstable memories
    ttl: P30D
  _imported:
    description: Memories imported from external systems
    provenance_required: true
```

### 10.6 Namespace URIs

Full URI form for cross-system references:

```
mif://{domain}/{namespace}/{memory-id}
```

Examples:
- `mif://github.com/modeled-information-format/acme-corp/project-x/550e8400...`
- `mif://registry/_public/python/async-patterns/abc123...`
- `mif://local/_local/scratch/memory-123`

### 10.7 Namespace Inheritance

Child namespaces MAY inherit properties from parents:

```yaml
# .mif/namespaces/acme-corp.yaml
id: acme-corp
type: organization
default_ttl: P365D
default_visibility: private

# .mif/namespaces/acme-corp/project-x.yaml
id: project-x
parent: acme-corp
default_tags: [project-x]
# Inherits default_ttl and default_visibility from parent
```

### 10.8 Ontology Definition

Ontologies define namespace hierarchies, entity types, and discovery patterns.
They enable domain-specific customization while maintaining MIF compatibility.

#### 10.8.1 Ontology Files

Ontologies are defined in YAML files with optional JSON-LD export:

```
.mif/ontologies/
├── mif-base.ontology.yaml       # Base ontology (semantic/episodic/procedural)
├── mif-base.ontology.jsonld     # JSON-LD export for semantic web
└── domain/
    └── software-engineering.ontology.yaml
```

#### 10.8.2 Base Type Hierarchy

The base ontology uses a three-tier hierarchy based on cognitive memory types:

```yaml
namespaces:
  semantic:                    # Facts, concepts, relationships
    type_hint: semantic
    children:
      decisions: {}
      knowledge: {}
      entities: {}
  episodic:                    # Events, experiences, timelines
    type_hint: episodic
    children:
      incidents: {}
      sessions: {}
      blockers: {}
  procedural:                  # Step-by-step processes
    type_hint: procedural
    children:
      runbooks: {}
      patterns: {}
      migrations: {}
```

#### 10.8.3 Entity Type Definition

Entity types define structured data with traits and JSON Schema:

```yaml
entity_types:
  - name: component
    base: semantic
    traits: [versioned, documented]
    schema:
      required: [name, responsibility]
      properties:
        name: { type: string }
        responsibility: { type: string }
        dependencies: { type: array, items: { type: string } }
```

#### 10.8.4 Discovery Patterns

Ontologies can define patterns for suggesting entity types:

```yaml
discovery:
  enabled: true
  confidence_threshold: 0.8
  patterns:
    - content_pattern: "\\b(PostgreSQL|MySQL|MongoDB)\\b"
      suggest_entity: technology
      suggest_namespace: _semantic/entities
    - file_pattern: "**/services/**/*.py"
      suggest_entity: component
      suggest_namespace: _semantic/components
```

#### 10.8.5 Ontology Resolution

Ontologies are loaded from multiple sources with precedence:

1. MIF base ontology (built-in)
2. User ontology (`${MNEMONIC_ROOT}/ontology.yaml`)
3. Project ontology (`./.claude/mnemonic/ontology.yaml`)

Later sources can extend or override earlier definitions.

#### 10.8.6 Trait Inheritance and Conflict Resolution

Traits support inheritance via the `extends` field, enabling composition:

```yaml
traits:
  timestamped:
    fields:
      created: { type: string, format: date-time }
      modified: { type: string, format: date-time }

  auditable:
    extends: [timestamped]
    fields:
      audit_log: { type: array }
      last_audited: { type: string, format: date-time }

  lifecycle:
    extends: [timestamped]
    fields:
      status: { type: string, enum: [draft, active, archived] }
```

**Conflict Resolution Strategy:**

When multiple traits define the same field (e.g., both `auditable` and `lifecycle` inherit `created` from `timestamped`), implementations MUST apply the following resolution rules:

| Scenario | Resolution | Rationale |
|----------|------------|-----------|
| Same field inherited via different paths | Use shared ancestor definition | Diamond inheritance resolved to common base |
| Same field defined in multiple independent traits | Error at composition time | Ambiguous definition requires explicit resolution |
| Field in trait overrides inherited field | Child definition wins | Explicit override is intentional |
| Field in entity overrides trait field | Entity definition wins | Most specific wins |

**Example - Diamond Inheritance:**

```yaml
# Both auditable and lifecycle inherit timestamped
entity_types:
  - name: document
    traits: [auditable, lifecycle]  # No conflict: `created` from shared `timestamped`
```

**Example - Conflict Requiring Resolution:**

```yaml
traits:
  trait_a:
    fields:
      status: { type: string, enum: [open, closed] }

  trait_b:
    fields:
      status: { type: string, enum: [draft, published] }

entity_types:
  - name: conflicting_entity
    traits: [trait_a, trait_b]
    # ERROR: `status` defined differently in both traits
    # Resolution: Override explicitly in entity schema
    schema:
      properties:
        status: { type: string, enum: [draft, open, published, closed] }
```

**Implementation Guidance:**

1. **Validation**: Implementations SHOULD detect conflicts at ontology load time
2. **Error Messages**: Include both conflicting definitions and their sources
3. **Explicit Override**: When conflicts exist, entity-level schema takes precedence
4. **Documentation**: Ontology authors SHOULD document intentional overrides

---

## 11. Embedding References

### 11.1 Model-Agnostic Approach

MIF stores embedding metadata, not raw vectors:

```yaml
embedding:
  model: text-embedding-3-small
  model_version: "2024-01"
  dimensions: 1536
  source_text: "The text that was embedded"
  normalized: true
  quantization: null  # or "float16", "int8"
```

This allows:
- Re-embedding on import with different models
- Smaller file sizes
- Model migration without data loss

### 11.2 Optional Vector Storage

For providers that need vector portability:

**External Reference:**
```yaml
embedding:
  model: text-embedding-3-small
  source_text: "..."
  vector_uri: "vectors/550e8400.bin"
```

**Inline (JSON-LD only):**
```json
"embedding": {
  "model": "text-embedding-3-small",
  "sourceText": "...",
  "vector": {
    "@type": "Vector",
    "encoding": "base64-float32",
    "data": "SGVsbG8gV29ybGQh..."
  }
}
```

---

## 12. Provenance

MIF uses W3C PROV vocabulary for provenance tracking.

### 12.1 Source Types

| Type | Description | Confidence Range |
|------|-------------|------------------|
| `user_explicit` | User directly stated | 0.90 - 1.00 |
| `user_implicit` | Inferred from user actions | 0.70 - 0.89 |
| `agent_inferred` | AI reasoning from context | 0.50 - 0.69 |
| `external_import` | From external data source | 0.30 - 0.70 |
| `system_generated` | Automatically generated | 0.20 - 0.50 |

### 12.2 Trust Levels

| Level | Description |
|-------|-------------|
| `verified` | Confirmed by multiple sources |
| `user_stated` | User explicitly provided |
| `high_confidence` | Strong inference |
| `moderate_confidence` | Reasonable inference |
| `low_confidence` | Weak inference |
| `uncertain` | Unverified |

### 12.3 Provenance Schema

```yaml
provenance:
  source_type: user_explicit
  source_ref: conversation:conv-456
  agent: claude-3-opus
  agent_version: "20240229"
  confidence: 0.95
  trust_level: user_stated
  derived_from:
    - memory:parent-memory-id
  attribution:
    - entity:person:jane-doe
```

---

## 13. Conformance Levels

### 13.1 Level 1: Core (REQUIRED for conformance)

- `id`, `type`, `content`, `created` fields
- Valid Markdown or JSON-LD structure
- Basic wiki-link syntax

### 13.2 Level 2: Standard (RECOMMENDED)

- All Level 1 requirements
- Namespace support
- Entity references
- Relationship types
- Temporal metadata (timestamps)

### 13.3 Level 3: Full (OPTIONAL)

- All Level 2 requirements
- Bi-temporal model
- Decay functions
- W3C PROV provenance
- Embedding references
- Citations with rich metadata
- Compression support
- Extension support

### 13.4 Conformance Statement

Implementations SHOULD declare their conformance level:

```yaml
# .mif/config.yaml
mif_version: "0.1.0"
conformance_level: 2
extensions:
  - subcog
  - custom-provider
```

---

## 14. JSON-LD Context

### 14.1 Context URL

```
https://mif-spec.dev/schema/context.jsonld
```

### 14.2 Context Definition

```json
{
  "@context": {
    "@version": 1.1,
    "mif": "https://mif-spec.dev/ns/",
    "dc": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",

    "Memory": "mif:Memory",
    "Entity": "mif:Entity",
    "Relationship": "mif:Relationship",
    "TemporalMetadata": "mif:TemporalMetadata",
    "EmbeddingReference": "mif:EmbeddingReference",
    "EntityReference": "mif:EntityReference",
    "OntologyReference": "mif:OntologyReference",

    "Person": "mif:Person",
    "Organization": "mif:Organization",
    "Technology": "mif:Technology",
    "Concept": "mif:Concept",
    "File": "mif:File",

    "id": "@id",
    "type": "@type",
    "content": "mif:content",
    "memoryType": "mif:memoryType",
    "title": "dc:title",
    "namespace": "mif:namespace",
    "tags": "mif:tags",
    "aliases": "mif:aliases",

    "created": {
      "@id": "dc:created",
      "@type": "xsd:dateTime"
    },
    "modified": {
      "@id": "dc:modified",
      "@type": "xsd:dateTime"
    },

    "ontology": "mif:ontology",
    "entities": "mif:entities",
    "relationships": "mif:relationships",
    "temporal": "mif:temporal",
    "provenance": "mif:provenance",
    "embedding": "mif:embedding",
    "extensions": "mif:extensions",

    "relationshipType": "mif:relationshipType",
    "target": "mif:target",
    "strength": "mif:strength",

    "validFrom": {
      "@id": "mif:validFrom",
      "@type": "xsd:dateTime"
    },
    "validUntil": {
      "@id": "mif:validUntil",
      "@type": "xsd:dateTime"
    },
    "recordedAt": {
      "@id": "mif:recordedAt",
      "@type": "xsd:dateTime"
    },
    "ttl": "mif:ttl",
    "decay": "mif:decay",
    "accessCount": "mif:accessCount",
    "lastAccessed": {
      "@id": "mif:lastAccessed",
      "@type": "xsd:dateTime"
    },

    "sourceType": "mif:sourceType",
    "sourceRef": "mif:sourceRef",
    "agent": "mif:agent",
    "confidence": "mif:confidence",
    "trustLevel": "mif:trustLevel",

    "model": "mif:model",
    "modelVersion": "mif:modelVersion",
    "dimensions": "mif:dimensions",
    "sourceText": "mif:sourceText",
    "vectorUri": "mif:vectorUri",

    "citations": {
      "@id": "mif:citations",
      "@container": "@set"
    },
    "Citation": "mif:Citation",
    "citationType": {
      "@id": "mif:citationType",
      "@type": "@vocab"
    },
    "citationRole": {
      "@id": "mif:citationRole",
      "@type": "@vocab"
    },
    "url": {
      "@id": "schema:url",
      "@type": "@id"
    },
    "author": {
      "@id": "dc:creator"
    },
    "date": {
      "@id": "dc:date",
      "@type": "xsd:date"
    },
    "relevance": {
      "@id": "mif:relevance",
      "@type": "xsd:decimal"
    },
    "accessed": {
      "@id": "schema:accessDate",
      "@type": "xsd:date"
    },
    "note": "schema:description",

    "summary": "mif:summary",
    "compressedAt": {
      "@id": "mif:compressedAt",
      "@type": "xsd:dateTime"
    }
  }
}
```

---

## 15. Conversion Rules

### 15.1 Markdown to JSON-LD

1. Parse YAML frontmatter as structured data
2. Map frontmatter properties to JSON-LD using context
3. Parse Markdown content for:
   - Wiki-links → `relationships` array
   - Entity references (@[[...]]) → `entities` array
   - Block references (^id) → fragment identifiers
4. Convert body content to `content` field

### 15.2 JSON-LD to Markdown

1. Generate YAML frontmatter from JSON-LD properties
2. Set first `title` or H1 from `dc:title`
3. Convert `content` to Markdown body
4. Append "## Relationships" section from `relationships`
5. Append "## Entities" section from `entities`
6. Convert `@id` URIs to wiki-links

### 15.3 Example Conversion

**Input (JSON-LD):**
```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:550e8400",
  "title": "Dark Mode",
  "content": "User prefers dark mode",
  "relationships": [
    {"relationshipType": "RelatesTo", "target": {"@id": "urn:mif:ui-prefs"}}
  ]
}
```

**Output (Markdown):**
```markdown
---
id: 550e8400
type: semantic
title: Dark Mode
---

# Dark Mode

User prefers dark mode

## Relationships

- relates-to [[ui-prefs]]
```

### 15.4 Citations Conversion

**Markdown to JSON-LD:**

1. Parse frontmatter `citations` array
2. For each citation:
   - Map `type` → `citationType` vocabulary term
   - Map `role` → `citationRole` vocabulary term
   - Resolve `@[[Entity|Type]]` author refs → entity URIs
   - For multiple authors (comma-separated), convert to array of author objects
   - Convert dates to ISO 8601 format
3. If `## Citations` body section exists:
   - Parse markdown links for title/url
   - Extract metadata from `**Key**: value` patterns
   - Merge with frontmatter (frontmatter takes precedence)
4. Build `Citation` objects array

**JSON-LD to Markdown:**

1. Generate frontmatter `citations` array from JSON-LD
2. Convert entity URIs to wiki-link syntax
3. If any citation has `note` exceeding 100 characters:
   - Create `## Citations` body section
   - Format as markdown list with metadata

**Example:**

```yaml
# Frontmatter
citations:
  - type: article
    title: "Research Paper"
    url: https://example.com/paper
    role: supports
    author: "@[[Jane Smith|Person]]"
```

Converts to:

```json
"citations": [{
  "@type": "Citation",
  "citationType": "article",
  "citationRole": "supports",
  "title": "Research Paper",
  "url": "https://example.com/paper",
  "author": {
    "@type": "EntityReference",
    "entity": {"@id": "urn:mif:entity:person:jane-smith"}
  }
}]
```

---

## 16. Examples

### 16.1 Minimal Memory (Level 1)

**Markdown:**
```markdown
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
created: 2026-01-15T10:30:00Z
---

User prefers dark mode for all applications.
```

**JSON-LD:**
```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:550e8400-e29b-41d4-a716-446655440000",
  "memoryType": "semantic",
  "content": "User prefers dark mode for all applications.",
  "created": "2026-01-15T10:30:00Z"
}
```

### 16.2 Decision Memory (Level 2)

**Markdown:**
```markdown
---
id: decision-react-over-vue
type: semantic
created: 2026-01-10T09:00:00Z
modified: 2026-01-12T14:30:00Z
namespace: _semantic/decisions
tags:
  - frontend
  - architecture
---

# Use React over Vue for the dashboard

## Context

We need to choose a frontend framework for the new dashboard.

## Decision

We will use React because:
- Team has more React experience
- Better TypeScript integration
- Larger ecosystem for our needs

## Consequences

- Need to set up Create React App or Vite
- Will use React Query for data fetching
- Component library: Radix UI

## Relationships

- relates-to [[frontend-architecture]]
- supersedes [[vue-exploration]]

## Entities

- @[[React|Technology]]
- @[[Vue.js|Technology]]
- @[[Project X|Organization]]
```

### 16.3 Full Memory (Level 3)

See Section 6.2 for a complete Level 3 example.

---

## 17. Migration

MIF v1.0.0 ships a complete upgrade path from `0.1.0-draft`. The mechanical
transform (drops the legacy `.memory` infix to plain `.md`, adds UUID identity, wiki-links → OKF-legible body
markdown links + frontmatter `relationships`, ISO 8601 timestamps) is automated
by `scripts/migrate_0_1_to_1_0.py` and documented in
[`MIGRATION.md`](MIGRATION.md).

System-specific migration guides for individual AI-memory providers are part
of the AI Memory profile, not the core model:
see [`profiles/ai-memory/SPECIFICATION.md`](profiles/ai-memory/SPECIFICATION.md).

## 18. Security Considerations

### 18.1 Data Privacy

- MIF files MAY contain sensitive personal information
- Implementations SHOULD support encryption at rest
- Namespace isolation SHOULD be enforced
- Export functions MUST respect access controls

### 18.2 Integrity

- Implementations SHOULD compute content hashes
- The `extensions.hash` field MAY store integrity hashes
- Import functions SHOULD verify integrity when hashes present

### 18.3 Provenance Trust

- `provenance.trust_level` indicates data reliability
- Implementations SHOULD NOT elevate trust levels on import
- External sources SHOULD be marked as `external_import`

---

## 19. IANA Considerations

### 19.1 Media Type Registration

**Markdown Format:**
- Type name: text
- Subtype name: markdown
- Required parameters: variant=mif
- Optional parameters: version

**JSON-LD Format:**
- Type name: application
- Subtype name: ld+json
- Required parameters: profile="https://mif-spec.dev"

### 19.2 URI Scheme

MIF URIs use the `mif:` scheme:
```
mif://{authority}/{namespace}/{memory-id}
```

---

## Appendix A: YAML Frontmatter Quick Reference

```yaml
---
# Required
id: uuid-v4
type: semantic|episodic|procedural
created: ISO-8601-datetime

# Recommended
modified: ISO-8601-datetime
ontology:
  id: ontology-identifier        # Matches ontology.id in definition
  version: "1.0.0"               # Semantic version (optional)
  uri: https://example.com/ont   # Ontology URL (optional)
namespace: hierarchical/path
title: "Human Title"
tags: [tag1, tag2]

# Optional
aliases: ["Alt Name 1", "Alt Name 2"]

temporal:
  valid_from: ISO-8601-datetime
  valid_until: ISO-8601-datetime | null
  recorded_at: ISO-8601-datetime
  ttl: ISO-8601-duration
  decay:
    model: none|linear|exponential|step
    halfLife: ISO-8601-duration
    strength: 0.0-1.0
  access_count: integer
  last_accessed: ISO-8601-datetime

provenance:
  source_type: user_explicit|user_implicit|agent_inferred|external_import|system_generated
  source_ref: uri
  agent: string
  confidence: 0.0-1.0
  trust_level: verified|user_stated|high_confidence|moderate_confidence|low_confidence|uncertain

embedding:
  model: string
  model_version: string
  dimensions: integer
  source_text: string

extensions:
  provider_name:
    custom_field: value
---
```

---

## Appendix B: Relationship Types Quick Reference

| Markdown Syntax | JSON-LD relationshipType | Description |
|-----------------|-------------------------|-------------|
| `[[X]]` | `RelatesTo` | General relationship |
| `[[X\|derived-from]]` | `DerivedFrom` | Created from source |
| `[[X\|supersedes]]` | `Supersedes` | Replaces older |
| `[[X\|conflicts-with]]` | `ConflictsWith` | Contradicts |
| `[[X\|part-of]]` | `PartOf` | Component of |
| `[[X\|implements]]` | `Implements` | Realizes |
| `[[X\|uses]]` | `Uses` | Utilizes |
| `[[X\|created-by]]` | `Created` | Authored by |
| `[[X\|mentioned-in]]` | `MentionedIn` | Referenced in |

---

## Appendix C: Entity Reference Syntax

| Markdown | Meaning |
|----------|---------|
| `@[[Name]]` | Reference entity by name |
| `@[[Name\|Person]]` | Reference with explicit type |
| `@[[Name\|uses]]` | Reference with relationship |
| `@[[Name\|Technology\|uses]]` | Type and relationship |

---

## Appendix D: Citations Quick Reference

### Citation Types

| Type | Description |
|------|-------------|
| `article` | Journal article, blog post |
| `book` | Published book |
| `paper` | Conference/research paper |
| `website` | General website |
| `documentation` | Technical documentation |
| `repository` | Code repository |
| `video` | Video content |
| `podcast` | Podcast episode |
| `specification` | Technical specification |
| `dataset` | Data source |
| `tool` | Software tool or service |
| `other` | Miscellaneous source |

### Citation Roles

| Role | Description |
|------|-------------|
| `supports` | Provides supporting evidence |
| `refutes` | Contradicts or disputes |
| `background` | General context/reference |
| `methodology` | Method or approach source |
| `contradicts` | Conflicts with claims |
| `extends` | Builds upon cited work |
| `derived` | Direct derivation source |
| `source` | Primary source material |
| `example` | Illustrative example |
| `review` | Critical review/analysis |

### Frontmatter Syntax

```yaml
citations:
  - type: article              # REQUIRED
    title: "Citation Title"    # REQUIRED
    url: https://example.com   # REQUIRED
    role: supports             # REQUIRED
    author: "@[[Name|Person]]" # OPTIONAL
    date: 2024-06-15           # OPTIONAL
    accessed: 2026-01-20       # OPTIONAL
    relevance: 0.95            # OPTIONAL (0-1)
    note: "Annotation"         # OPTIONAL
```

### Body Section Syntax

```markdown
## Citations

- [Title](url) by @[[Author|Person]] (date)
  - **Type**: article
  - **Role**: supports
  - **Relevance**: 0.95
  - Long-form annotation here.
```

---

## Changelog

### 0.1.0-draft (2026-01-26)
- **BREAKING**: Replaced ad-hoc memory types with three base types (Section 4.2)
  - New base types: `semantic`, `episodic`, `procedural`
  - Removed: `memory`, `decision`, `preference`, `fact`, `episode`, `pattern`, `learning`, `context`
  - Specific categorization via namespace hierarchy (e.g., `_semantic/decisions`)
- Added `ontology` field for declaring applied ontology (Section 4.3)
- Added `OntologyReference` type to JSON-LD context
- Updated frontmatter schema with ontology reference
- Updated JSON-LD example with ontology field

### 0.1.0-draft (2026-01-23)
- Initial draft specification
- Dual format (Markdown + JSON-LD)
- Core data model
- Entity and relationship types
- Bi-temporal model
- Hierarchical namespaces
- Provenance model
- Embedding references

---

## References

- [RFC 2119: Key words for use in RFCs](https://www.rfc-editor.org/rfc/rfc2119)
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)
- [Dublin Core Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)
- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)
- [ISO 8601: Date and Time Format](https://www.iso.org/iso-8601-date-and-time-format.html)
- [Obsidian Help](https://help.obsidian.md/)
- [JSON Canvas Specification](https://jsoncanvas.org/)

---

*This specification is open source and contributions are welcome.*
