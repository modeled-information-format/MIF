---
id: 7f3a8b2c-1d4e-5f6a-9b0c-2d3e4f5a6b7c
type: semantic
created: '2026-01-15T10:30:00Z'
modified: '2026-01-20T14:22:00Z'
namespace: _semantic/preferences
title: Dark Mode UI Preference
tags:
- preference
- ui
- accessibility
aliases:
- Dark Mode Preference
- UI Theme Choice
relationships:
- type: relates-to
  target: /ide-configuration-preferences.md
- type: relates-to
  target: /terminal-setup.md
- type: part-of
  target: /user-jane-doe-profile.md
temporal:
  '@type': TemporalMetadata
  validFrom: '2026-01-15T00:00:00Z'
  validUntil: null
  recordedAt: '2026-01-15T10:30:00Z'
  ttl: P365D
  decay:
    model: exponential
    halfLife: P30D
    currentStrength: 0.92
    lastReinforced: '2026-01-20T14:22:00Z'
  accessCount: 8
  lastAccessed: '2026-01-20T14:22:00Z'
provenance:
  '@type': prov:Entity
  sourceType: user_explicit
  sourceRef: conversation:conv-2026-01-15-001
  agent: claude-3-opus
  agentVersion: '20240229'
  confidence: 0.98
  trustLevel: user_stated
  wasGeneratedBy:
    '@id': urn:mif:activity:extraction:conv-2026-01-15-001
    '@type': prov:Activity
    wasAssociatedWith:
      '@id': urn:mif:agent:claude-3-opus
      '@type': prov:SoftwareAgent
  wasAttributedTo:
    '@id': urn:mif:entity:person:jane-doe
  wasDerivedFrom:
    '@id': urn:mif:conversation:conv-2026-01-15-001
embedding:
  '@type': EmbeddingReference
  model: text-embedding-3-small
  modelVersion: 2024-01
  dimensions: 1536
  sourceText: User prefers dark mode for all applications including IDE, terminal,
    and web apps
  normalized: true
extensions:
  subcog:
    domain: user
    hash: sha256:4c04b32ddc2053b5a8f9e2d1c0b7a6e5d4c3b2a1
entities:
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:person:jane-doe
  entityType: Person
  name: Jane Doe
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:technology:vs-code
  entityType: Technology
  name: VS Code
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:concept:dark-mode
  entityType: Concept
  name: Dark Mode
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:concept:accessibility
  entityType: Concept
  name: Accessibility
---

# Dark Mode UI Preference

User strongly prefers dark mode for all applications. ^main-preference

## Details

This preference applies to: ^details

- **IDE/Editor**: VS Code, JetBrains IDEs
- **Terminal**: iTerm2, built-in terminal
- **Web applications**: GitHub, documentation sites
- **Mobile apps**: When available

## Context

User mentioned eye strain with light themes during extended coding sessions. Dark mode reduces eye fatigue and is preferred for:

- Late-night coding sessions
- Low-light environments
- General aesthetic preference

## Reinforcement History

This preference has been confirmed multiple times:

1. 2026-01-15: Initial statement during onboarding
2. 2026-01-16: Confirmed when setting up VS Code
3. 2026-01-18: Applied to terminal configuration
4. 2026-01-20: Extended to web application preferences

## Relationships

- relates-to [Ide Configuration Preferences](/ide-configuration-preferences.md)
- relates-to [Terminal Setup](/terminal-setup.md)
- part-of [User Jane Doe Profile](/user-jane-doe-profile.md)
