---
id: 7b3c1e90-5a2f-4c8d-9e10-2f6a4b8c1d3e
type: semantic
created: 2026-01-15T10:30:00Z
modified: 2026-01-20T09:00:00Z
namespace: _semantic/policies
title: API Rate Limit Policy
summary: Declarative limits for the public API gateway.
tags:
  - api
  - policy
  - gateway
relationships:
  - type: derived-from
    target: /episodic/incident-2026-01-rate-spike.md
    strength: 0.9
  - type: relates-to
    target: /procedural/rotate-api-keys.md
---

# API Rate Limit Policy

Declarative knowledge: the public API gateway enforces a sliding-window rate
limit of 600 requests per minute per API key, with a burst allowance of 100.

## Rationale

The limit was set after observing sustained abuse traffic. It balances
legitimate batch consumers against gateway saturation.

## Relationships

- derived-from [Rate Spike Incident](/episodic/incident-2026-01-rate-spike.md)
- relates-to [Rotate API Keys](/procedural/rotate-api-keys.md)
