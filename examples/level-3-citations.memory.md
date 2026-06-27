---
id: a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d
type: semantic
created: 2026-01-20T10:00:00Z
modified: 2026-01-22T15:30:00Z
namespace: _semantic/decisions
title: "Adopt MIF for AI Memory Interchange"
tags:
  - architecture
  - memory-systems
  - integration
  - ai
aliases:
  - "MIF Adoption Decision"
  - "Memory Format Choice"

temporal:
  valid_from: 2026-01-20T00:00:00Z
  valid_until: null
  recorded_at: 2026-01-20T10:00:00Z
  ttl: P730D
  decay:
    model: none
    strength: 1.0
  access_count: 12
  last_accessed: 2026-01-22T15:30:00Z

provenance:
  source_type: user_explicit
  source_ref: meeting:arch-review-2026-01-20
  agent: claude-3-opus
  agent_version: "20240229"
  confidence: 0.98
  trust_level: verified

embedding:
  model: text-embedding-3-small
  model_version: "2024-01"
  dimensions: 1536
  source_text: "Decision to adopt MIF Memory Interchange Format for portable AI memory representation"
  normalized: true

citations:
  - type: specification
    title: "Memory Interchange Format (MIF) Specification"
    url: https://github.com/zircote/subcog/blob/main/SPECIFICATION.md
    role: source
    author: "@[[Robert Allen|Person]]"
    date: 2026-01-23
    accessed: 2026-01-20
    relevance: 1.0
    note: "Primary specification document defining the format we are adopting"

  - type: article
    title: "The Case for Portable AI Memory"
    url: https://example.com/ai-memory-portability
    role: supports
    author: "@[[Jane Smith|Person]], @[[John Doe|Person]]"
    date: 2025-11-15
    accessed: 2026-01-18
    relevance: 0.92
    note: "Research article supporting vendor-neutral memory formats"

  - type: documentation
    title: "Obsidian Help Documentation"
    url: https://help.obsidian.md/
    role: background
    author: "@[[Obsidian Team|Organization]]"
    accessed: 2026-01-19
    relevance: 0.85

  - type: paper
    title: "Bi-temporal Data Models in Knowledge Systems"
    url: https://arxiv.org/abs/2024.54321
    role: methodology
    author: "@[[Research Group|Organization]]"
    date: 2024-08-20
    relevance: 0.78
    note: "Theoretical foundation for MIF's temporal model"

  - type: repository
    title: "Subcog Memory System"
    url: https://github.com/zircote/subcog
    role: extends
    author: "@[[Robert Allen|Person]]"
    accessed: 2026-01-20
    relevance: 0.88

extensions:
  subcog:
    domain: architecture
    hash: "sha256:7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a"
---

# Adopt MIF for AI Memory Interchange

## Context

Our AI systems currently use proprietary memory formats that are incompatible across different providers (Mem0, Zep, Letta, Subcog). This creates vendor lock-in and prevents memory portability when switching or combining AI memory systems. ^context

## Decision

We will adopt the **Memory Interchange Format (MIF)** as our standard for AI memory representation and interchange. ^decision

### Key Factors

1. **Dual Representation**: MIF provides both human-readable Markdown and machine-processable JSON-LD formats
2. **Obsidian Compatibility**: Direct integration with our existing knowledge management workflows
3. **Semantic Web Support**: JSON-LD enables RDF tooling and semantic queries
4. **Local-First**: No cloud dependencies, full data ownership
5. **Extensibility**: Custom properties without breaking compatibility

## Consequences

### Positive

- Memories portable between AI providers
- Human-readable format for manual review and editing
- Compatible with existing Obsidian vaults
- Future-proof with semantic web standards

### Negative

- Migration effort for existing memory stores
- Team training on new format
- Tooling development for format conversion

## Implementation Plan

1. **Phase 1**: Implement MIF export from current Subcog format
2. **Phase 2**: Build import adapters for Mem0, Zep, Letta
3. **Phase 3**: Native MIF storage in new projects
4. **Phase 4**: Deprecate proprietary formats

## Relationships

- supersedes [[proprietary-memory-format-2024]]
- relates-to [[ai-infrastructure-standards]]
- part-of [[platform-architecture-decisions]]
- implements [[memory-portability-requirement]]

## Entities

- @[[MIF|Technology]]
- @[[Subcog|Technology]]
- @[[Obsidian|Technology]]
- @[[JSON-LD|Technology]]
- @[[Engineering Architecture Team|Organization]]

## Citations

- [Memory Interchange Format (MIF) Specification](https://github.com/zircote/subcog/blob/main/SPECIFICATION.md) by @[[Robert Allen|Person]] (2026)
  - **Type**: specification
  - **Role**: source
  - **Relevance**: 1.0
  - Primary specification document defining the format we are adopting. This is the authoritative
    source for MIF structure, conformance levels, and implementation requirements.

- [The Case for Portable AI Memory](https://example.com/ai-memory-portability) by @[[Jane Smith|Person]], @[[John Doe|Person]] (2025)
  - **Type**: article
  - **Role**: supports
  - **Relevance**: 0.92
  - Research article arguing for vendor-neutral memory formats in AI systems. Provides empirical
    evidence for productivity gains and reduced lock-in risks.

- [Bi-temporal Data Models in Knowledge Systems](https://arxiv.org/abs/2024.54321) by @[[Research Group|Organization]] (2024)
  - **Type**: paper
  - **Role**: methodology
  - **Relevance**: 0.78
  - Theoretical foundation for MIF's temporal model, explaining valid time vs transaction time
    and decay functions for memory strength.
