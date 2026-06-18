---
id: a1d2c3b4-6e7f-4a8b-9c0d-1e2f3a4b5c6d
type: episodic
created: 2026-01-08T03:12:00Z
namespace: _episodic/incidents
title: Rate Spike Incident 2026-01
summary: Gateway saturation caused by an unthrottled batch client.
tags:
  - incident
  - api
  - gateway
---

# Rate Spike Incident 2026-01

Time-bound record: on 2026-01-08 between 03:00 and 03:40 UTC the API gateway
saturated when a single client issued ~12k requests/minute. Requests were shed
with HTTP 503 until the client was throttled at the edge.

## Timeline

- 03:12 — alert fired on gateway p99 latency
- 03:25 — offending key identified
- 03:38 — edge throttle applied; latency recovered
