---
id: b2c3d4e5-6789-01bc-def0-2345678901bc
type: procedural
created: '2026-03-01T08:00:00Z'
modified: '2026-03-01T08:00:00Z'
namespace: _procedural/animal-welfare
title: 2026 Spring Rotational Grazing Plan - Beef Herd
tags:
- grazing
- livestock
- adaptive-multi-paddock
- regenerative
relationships:
- type: documents
  target: /herd-beef-main.md
- type: located-on
  target: /field-pasture-north.md
- type: located-on
  target: /field-pasture-south.md
- type: contributes-to
  target: /carbon-credit-2026.md
temporal:
  '@type': TemporalMetadata
  validFrom: '2026-04-01T00:00:00Z'
  validUntil: '2026-10-31T00:00:00Z'
  recordedAt: '2026-03-01T08:00:00Z'
provenance:
  agent: claude-opus-4
  confidence: 0.95
  sourceType: user_explicit
ontology:
  id: regenerative-agriculture
  version: 0.1.0
entity:
  entity_type: grazing-plan
  entity_id: grazing-plan-beef-2026-spring
  name: 2026 Spring-Fall Beef Grazing Rotation
  herd_id: herd-beef-main
  stock_density: 250000
  rest_period_days: 45
---

# 2026 Spring Rotational Grazing Plan - Beef Herd

Adaptive multi-paddock (AMP) grazing plan for the main beef herd
(85 head) across 120 acres of improved pasture.

## Grazing Principles

Following Savory Institute guidelines for high-density, short-duration
grazing with adequate recovery periods:

1. **Stock Density**: 250,000 lbs/acre (high impact)
2. **Grazing Duration**: 1-3 days per paddock
3. **Recovery Period**: 45-60 days minimum
4. **Target Residual**: 4-6 inches forage height

## Paddock Rotation Schedule

| Week | Paddock | Entry Date | Exit Date | Animal Days | Notes |
|------|---------|------------|-----------|-------------|-------|
| 1 | P-01 | Apr 1 | Apr 3 | 255 | Spring flush |
| 2 | P-02 | Apr 4 | Apr 6 | 255 | |
| 3 | P-03 | Apr 7 | Apr 9 | 255 | Water tank here |
| 4 | P-04 | Apr 10 | Apr 12 | 255 | |
| 5 | P-05 | Apr 13 | Apr 16 | 340 | Larger paddock |
| 6 | P-06 | Apr 17 | Apr 19 | 255 | |
| 7 | P-07 | Apr 20 | Apr 22 | 255 | |
| 8 | P-08 | Apr 23 | Apr 25 | 255 | Shade trees |

*Cycle repeats with 45-day recovery*

## Monitoring Protocol

Check daily:
- [ ] Forage height at entry (target: 12-18 inches)
- [ ] Forage height at exit (target: 4-6 inches)
- [ ] Water availability
- [ ] Animal condition and behavior
- [ ] Soil moisture (move early if wet)

Check weekly:
- [ ] Paddock recovery (previous locations)
- [ ] Fence condition
- [ ] Mineral feeder levels

## Decision Triggers

**Move Early If:**
- Soil is saturated (pugging risk)
- Forage grazed below 4 inches
- Animals bunching at gate

**Extend Stay If:**
- Forage still above 6 inches
- Weather preventing move
- No pugging observed

## Expected Outcomes

- 30% improvement in forage productivity
- Improved soil carbon sequestration
- Even manure distribution
- Reduced parasite pressure
- Animal weight gain: 2.5 lbs/day target

## Relationships

- documents [Herd Beef Main](/herd-beef-main.md)
- located-on [Field Pasture North](/field-pasture-north.md)
- located-on [Field Pasture South](/field-pasture-south.md)
- contributes-to [Carbon Credit 2026](/carbon-credit-2026.md)
