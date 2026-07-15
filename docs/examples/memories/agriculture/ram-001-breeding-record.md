---
id: c3d4e5f6-7890-12cd-ef01-3456789012cd
type: semantic
created: '2026-04-10T09:00:00Z'
modified: '2026-04-10T09:00:00Z'
namespace: _semantic/livestock
title: Ram 001 Breeding Record
tags:
- livestock
- breeding
- ram
relationships:
- type: farm:breeds-with
  target: /ewe-002-breeding-record.md
  metadata:
    farm:breeding_date: '2026-04-10'
    farm:success: true
entity:
  entity_type: animal
  entity_id: ram-001
  name: Ram 001
---

# Ram 001 Breeding Record

Breeding pairing record for Ram 001, demonstrating a custom
`farm:breeds-with` relationship type declared in this bundle's
`.mif/config.yaml` (SPECIFICATION.md 8.1/8.3).

## Relationships

- farm:breeds-with [Ewe 002 Breeding Record](/ewe-002-breeding-record.md)
