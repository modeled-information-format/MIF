---
diataxis_type: reference
---

# MIF Namespace

Base IRI: `https://mif-spec.dev/ns/`

The MIF vocabulary defines terms for portable AI memory representation.

> **Note:** Both the schema `$id` values (`https://mif-spec.dev/schema/...`) and
> the JSON-LD namespace IRI (`https://mif-spec.dev/ns/`) are stable, resolvable
> identifiers on the `mif-spec.dev` domain (per ADR-007). Neither is expected to
> change.

## Vocabulary Terms

### Core Types

| Term | IRI | Description |
|------|-----|-------------|
| `Memory` | `mif:Memory` | A memory document |
| `Entity` | `mif:Entity` | A named entity |
| `Relationship` | `mif:Relationship` | A typed relationship between memories or entities |
| `TemporalMetadata` | `mif:TemporalMetadata` | Temporal validity and decay metadata |
| `EmbeddingReference` | `mif:EmbeddingReference` | Reference to a vector embedding |
| `EntityReference` | `mif:EntityReference` | A reference to an entity within a memory |
| `OntologyReference` | `mif:OntologyReference` | A reference to an ontology definition |
| `EntityData` | `mif:EntityData` | Structured entity data |
| `Vector` | `mif:Vector` | An embedding vector |
| `Citation` | `mif:Citation` | A citation or bibliographic reference |

### Entity Types

| Term | IRI | Description |
|------|-----|-------------|
| `Person` | `mif:Person` | A human individual |
| `Organization` | `mif:Organization` | A company, institution, or group |
| `Technology` | `mif:Technology` | A technology, framework, or tool |
| `Concept` | `mif:Concept` | An abstract concept or idea |
| `File` | `mif:File` | A file or document |

### Memory Type Terms

| Term | IRI | Description |
|------|-----|-------------|
| `semantic` | `mif:SemanticType` | Facts, concepts, decisions, preferences, knowledge |
| `episodic` | `mif:EpisodicType` | Events, experiences, sessions, incidents |
| `procedural` | `mif:ProceduralType` | Processes, runbooks, patterns, how-to guides |

### Properties

| Property | IRI | XSD Type | Description |
|----------|-----|----------|-------------|
| `content` | `mif:content` | `xsd:string` | The textual content of a memory |
| `memoryType` | `mif:memoryType` | `@vocab` | The base memory type classification |
| `title` | `dc:title` | -- | Human-readable title |
| `namespace` | `mif:namespace` | -- | Hierarchical scope for categorization |
| `tags` | `mif:tags` | `@set` | Classification tags |
| `aliases` | `mif:aliases` | `@set` | Alternative names or identifiers |
| `blocks` | `mif:blocks` | `@index` | Named content blocks |
| `created` | `dc:created` | `xsd:dateTime` | Creation timestamp |
| `modified` | `dc:modified` | `xsd:dateTime` | Last modification timestamp |
| `name` | `schema:name` | -- | Display name (from Schema.org) |
| `role` | `mif:role` | -- | Role in memory context |
| `version` | `mif:version` | -- | Version string |
| `uri` | `mif:uri` | `@id` | URI reference |
| `url` | `schema:url` | `@id` | URL (from Schema.org) |
| `author` | `schema:author` | -- | Author (from Schema.org) |
| `date` | `schema:datePublished` | `xsd:date` | Publication date |
| `note` | `mif:note` | -- | Annotation or note text |
| `extensions` | `mif:extensions` | `@index` | Vendor-specific extension data |

### Relationship Types

| Term | IRI | Description |
|------|-----|-------------|
| `RelatesTo` | `mif:RelatesTo` | General relationship |
| `DerivedFrom` | `mif:DerivedFrom` | Created based on a source |
| `Supersedes` | `mif:Supersedes` | Replaces an older memory |
| `ConflictsWith` | `mif:ConflictsWith` | Contradicts another memory |
| `PartOf` | `mif:PartOf` | Component of a larger whole |
| `Implements` | `mif:Implements` | Realizes a concept or pattern |
| `Uses` | `mif:Uses` | Utilizes a technology or tool |
| `Created` | `mif:Created` | Authored by an entity |
| `MentionedIn` | `mif:MentionedIn` | Referenced in a memory |

### Relationship Properties

| Property | IRI | XSD Type | Description |
|----------|-----|----------|-------------|
| `relationshipType` | `mif:relationshipType` | `@vocab` | The type of relationship |
| `target` | `mif:target` | `@id` | The target of the relationship |
| `strength` | `mif:strength` | `xsd:decimal` | Relationship strength (0.0-1.0) |
| `entities` | `mif:entities` | `@set` | Entity references |
| `entity` | `mif:entity` | `@id` | Reference to a single entity |
| `entityType` | `mif:entityType` | -- | Type classification of an entity |
| `entity_type` | `mif:entity_type` | -- | Alias for entityType |
| `entity_id` | `mif:entity_id` | -- | Entity identifier |
| `relationships` | `mif:relationships` | `@set` | Relationship references |

### Citation Properties

| Property | IRI | XSD Type | Description |
|----------|-----|----------|-------------|
| `citations` | `mif:citations` | `@set` | Collection of citations |
| `citationType` | `mif:citationType` | `@vocab` | Category of the citation source |
| `citationRole` | `mif:citationRole` | `@vocab` | How the citation relates to the memory |
| `accessed` | `mif:accessed` | `xsd:dateTime` | When the citation was last accessed |
| `relevance` | `mif:relevance` | `xsd:decimal` | Relevance score (0.0-1.0) |

### Provenance Terms

| Term | IRI | Description |
|------|-----|-------------|
| `provenance` | `mif:provenance` | Provenance metadata container |
| `sourceType` | `mif:sourceType` | How the memory was created |
| `sourceRef` | `mif:sourceRef` | Reference to the original source |
| `agent` | `mif:agent` | The agent that created the memory |
| `agentVersion` | `mif:agentVersion` | Version of the creating agent |
| `confidence` | `mif:confidence` | Confidence score (0.0-1.0) |
| `trustLevel` | `mif:trustLevel` | Trust classification level |

### Source Types

| Term | IRI | Description |
|------|-----|-------------|
| `user_explicit` | `mif:UserExplicit` | Directly stated by user |
| `user_implicit` | `mif:UserImplicit` | Inferred from user behavior |
| `agent_inferred` | `mif:AgentInferred` | Inferred by an AI agent |
| `external_import` | `mif:ExternalImport` | Imported from external system |
| `system_generated` | `mif:SystemGenerated` | Generated by the system |

### Trust Levels

| Term | IRI | Description |
|------|-----|-------------|
| `verified` | `mif:Verified` | Independently verified |
| `user_stated` | `mif:UserStated` | Stated by the user |
| `high_confidence` | `mif:HighConfidence` | High confidence inference |
| `moderate_confidence` | `mif:ModerateConfidence` | Moderate confidence inference |
| `low_confidence` | `mif:LowConfidence` | Low confidence inference |
| `uncertain` | `mif:Uncertain` | Uncertain or unverified |

### Temporal / Decay Terms

| Property | IRI | XSD Type | Description |
|----------|-----|----------|-------------|
| `temporal` | `mif:temporal` | -- | Temporal metadata container |
| `validFrom` | `mif:validFrom` | `xsd:dateTime` | When the fact becomes valid |
| `validUntil` | `mif:validUntil` | `xsd:dateTime` | When the fact expires |
| `recordedAt` | `mif:recordedAt` | `xsd:dateTime` | Transaction time (when recorded) |
| `ttl` | `mif:ttl` | `xsd:duration` | Time-to-live duration |
| `decay` | `mif:decay` | -- | Decay model container |
| `model` | `mif:model` | -- | Decay model type (none, linear, exponential, step) |
| `halfLife` | `mif:halfLife` | `xsd:duration` | Decay half-life duration |
| `currentStrength` | `mif:currentStrength` | `xsd:decimal` | Current memory strength (0.0-1.0) |
| `lastReinforced` | `mif:lastReinforced` | `xsd:dateTime` | When memory was last reinforced |
| `accessCount` | `mif:accessCount` | `xsd:integer` | Number of times accessed |
| `lastAccessed` | `mif:lastAccessed` | `xsd:dateTime` | When memory was last accessed |
| `reinforcementHistory` | `mif:reinforcementHistory` | `@list` | Ordered list of reinforcement events |

### Embedding Properties

| Property | IRI | XSD Type | Description |
|----------|-----|----------|-------------|
| `embedding` | `mif:embedding` | -- | Embedding reference container |
| `modelVersion` | `mif:modelVersion` | -- | Embedding model version |
| `dimensions` | `mif:dimensions` | `xsd:integer` | Vector dimensions |
| `sourceText` | `mif:sourceText` | -- | Text that was embedded |
| `normalized` | `mif:normalized` | `xsd:boolean` | Whether vector is normalized |
| `vectorUri` | `mif:vectorUri` | `@id` | URI to external vector data |
| `vector` | `mif:vector` | -- | Vector data container |
| `encoding` | `mif:encoding` | -- | Vector encoding format |
| `data` | `mif:data` | -- | Raw vector data |

### Ontology Properties

| Property | IRI | Description |
|----------|-----|-------------|
| `ontology` | `mif:ontology` | Ontology reference container |

## External Vocabularies

MIF reuses terms from established vocabularies:

| Prefix | Namespace | Source |
|--------|-----------|--------|
| `dc` | `http://purl.org/dc/terms/` | Dublin Core Metadata Terms |
| `prov` | `http://www.w3.org/ns/prov#` | W3C Provenance Ontology |
| `xsd` | `http://www.w3.org/2001/XMLSchema#` | XML Schema Datatypes |
| `schema` | `https://schema.org/` | Schema.org vocabulary |

## Usage in JSON-LD Context

```json
{
  "@context": {
    "mif": "https://mif-spec.dev/ns/",
    "Memory": "mif:Memory",
    "memoryType": "mif:memoryType"
  }
}
```

This creates IRIs like:
- `https://mif-spec.dev/ns/Memory`
- `https://mif-spec.dev/ns/memoryType`

For full context including all term definitions, reference the MIF context file:

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld"
}
```

## Note

JSON-LD namespace prefixes are identifiers for vocabulary terms. While they form valid URLs, they don't need to resolve to actual content -- they serve as unique identifiers in the semantic web.
