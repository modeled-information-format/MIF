---
id: 0b191afe-df8d-5858-8e1d-438787ebdeee
type: semantic
created: '2026-01-10T09:00:00Z'
modified: '2026-01-12T14:30:00Z'
namespace: _semantic/decisions
title: Use React for Dashboard Frontend
tags:
- frontend
- architecture
- technology-choice
aliases:
- React Decision
- Frontend Framework Choice
- decision-react-frontend
relationships:
- type: supersedes
  target: /vue-exploration-2025.md
- type: relates-to
  target: /frontend-architecture-standards.md
- type: part-of
  target: /project-x-technical-decisions.md
entities:
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:technology:react
  entityType: Technology
  name: React
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:technology:typescript
  entityType: Technology
  name: TypeScript
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:technology:vue-js
  entityType: Technology
  name: Vue.js
- "@type": EntityReference
  entity:
    "@id": urn:mif:entity:concept:project-x-dashboard
  entityType: Concept
  name: Project X Dashboard
---

# Use React for Dashboard Frontend

## Context

We need to choose a frontend framework for the new analytics dashboard. The team evaluated React, Vue.js, and Angular.

## Decision

We will use **React** with TypeScript for the dashboard frontend.

### Rationale

- Team has 3+ years of React experience
- Better TypeScript integration than Vue 2.x
- Larger ecosystem for data visualization (Recharts, Victory, Nivo)
- Company standard for new projects

## Consequences

- Set up Vite for build tooling
- Use React Query for server state
- Component library: Radix UI + Tailwind CSS
- Testing: Vitest + React Testing Library

## Relationships

- supersedes [Vue Exploration 2025](/vue-exploration-2025.md)
- relates-to [Frontend Architecture Standards](/frontend-architecture-standards.md)
- part-of [Project X Technical Decisions](/project-x-technical-decisions.md)
