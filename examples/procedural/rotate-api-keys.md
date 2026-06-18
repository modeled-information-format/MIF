---
id: c4b5a6d7-8f90-4123-a456-7b8c9d0e1f23
type: procedural
created: 2026-01-12T14:00:00Z
namespace: _procedural/runbooks
title: Rotate API Keys
summary: Runbook for rotating a compromised or abusive API key.
tags:
  - runbook
  - api
  - security
relationships:
  - type: relates-to
    target: /semantic/rate-limit-policy.md
---

# Rotate API Keys

How-to knowledge: rotate an API key when it is compromised or implicated in an
abuse incident.

## Steps

1. Identify the key ID from gateway logs.
2. Issue a replacement key to the owner out of band.
3. Set the old key to `revoked` in the key store.
4. Confirm the old key returns HTTP 401 at the edge.

## Relationships

- relates-to [API Rate Limit Policy](/semantic/rate-limit-policy.md)
