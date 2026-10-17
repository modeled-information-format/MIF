---
id: 0c523a47-28b3-559f-94ce-692cf88c2d9f
type: episodic
created: '2026-01-15T10:30:00Z'
namespace: _episodic/sessions
title: Phoenix Rate-Spike Debug Session
tags:
- debug
- incident
- mempalace
---

Debug session on 2026-01-15 investigating a request rate spike on Project
Phoenix. The team traced it to an un-throttled batch consumer and added a
sliding-window limit.

Derived from a MemPalace **drawer** (wing `Project Phoenix`, room `Incidents`,
`filed_at: 2026-01-15T10:30:00Z`, `source: chat`, `added_by: agent`). A drawer is
a time-anchored record of something the agent lived through, so it maps to the
cognitive-triad `episodic` type (the AI-memory `session` reinterpretation): the
drawer's `filed_at` becomes `created`, and its wing/room become the
`_episodic/sessions` namespace path.
