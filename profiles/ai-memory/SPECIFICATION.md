<!-- diataxis_type: explanation -->

# MIF AI Memory Profile

> **AI Memory is the first domain profile of MIF, not its identity.** The core
> MIF specification defines a general-purpose, OKF-compliant knowledge content
> model. This profile reinterprets that model for one domain: the persistent
> memory of autonomous AI agents.

This document is a **normative domain profile** of MIF v1.0. It builds on:

- The core specification at [`../../SPECIFICATION.md`](../../SPECIFICATION.md) — the general `.md`/JSON-LD knowledge model, namespaces, temporal model, embeddings, and provenance.
- The AI-memory ontology at [`./ontology.yaml`](./ontology.yaml) — the entity types, traits, and relationships this profile adds on top of `mif-base`.

Everything in the core spec applies unchanged. This profile **adds** memory-specific
rationale, defaults, and mappings. Where the core spec frames a mechanism in
neutral knowledge-management terms (e.g. "validity windows and freshness"), this
profile keeps the original cognitive-memory rationale (e.g. "the forgetting
curve") that motivated the design.

---

## 1. Scope

The AI Memory profile applies when MIF is used as the storage substrate for an
agent's long-lived memory: facts it has learned, sessions it has lived through,
and skills it can replay. A conforming AI-memory implementation:

- Stores memories as MIF `.md` (or JSON-LD) documents per the core spec.
- Maps memory `type` onto the core triad: `semantic`, `episodic`, `procedural`.
- Applies the forgetting-curve decay tuning in §3 to the core temporal model.
- Uses recall-oriented embeddings (§4) for similarity retrieval.
- MAY use the `ai-memory` ontology entity types (`session`, `observation`, `skill`).

This profile is OPTIONAL. A core-conformant tool that ignores it is still valid MIF.

---

## 2. The Cognitive-Memory Origin of the Triad

The core spec organizes all knowledge into three top-level namespaces —
`semantic`, `episodic`, `procedural` — and presents them as a general knowledge
taxonomy (declarative knowledge, time-bound records, how-to knowledge). The core
spec mentions in a single cross-referencing sentence that these names come from
cognitive science. **This profile is where that origin is fully motivated.**

The triad is borrowed from the psychology of human long-term memory:

| Triad type | Cognitive-memory meaning | MIF reinterpretation |
|------------|--------------------------|----------------------|
| **Semantic** | General world knowledge and facts, decontextualized from when they were learned | Facts the agent knows (`observation`) |
| **Episodic** | Autobiographical record of specific events the subject experienced, anchored in time and place | Sessions the agent participated in (`session`) |
| **Procedural** | Skills and motor/cognitive procedures executed without conscious recall of their acquisition | Replayable how-to sequences (`skill`) |

The value of the metaphor for AI memory is that it gives an agent a principled
place to put each kind of thing it needs to remember:

- A fact ("the staging DB is Postgres 16") is **semantic** — it does not matter
  *when* the agent learned it, only that it is true now.
- The record of a specific debugging run is **episodic** — it is anchored to a
  start time, an end time, and the participants present.
- Knowing *how* to run the deploy procedure is **procedural** — a sequence the
  agent replays, reinforced each time it is used successfully.

Because the core model keeps these as plain namespaces, an AI-memory store and a
non-memory knowledge base remain interoperable: they share the same triad, even
though only this profile reads it as "memory."

---

## 3. Forgetting-Curve Decay Tuning

The core temporal model (core spec §9) defines `validFrom` / `validUntil`,
`ttl`, an `accessCount` / `lastAccessed` pair, and a `decay` object with
`none` / `linear` / `exponential` / `step` models. The core spec frames this as
**validity windows and freshness**. This profile keeps the **forgetting-curve
rationale** that the same math was designed around — the framing is different, the
formulas are identical.

### 3.1 The Exponential Model Is a Forgetting Curve

The exponential decay model

```
strength = e^(-t / halfLife)
```

is the Ebbinghaus forgetting curve (Ebbinghaus, 1885): retention of an
un-reinforced memory declines exponentially with elapsed time. Writing `R` for
retrievability, `t` for time elapsed, and `S` for memory strength, the curve is

```
R = e^(-t / S)
```

Modern replication (Murre & Dros, 2015) confirms the exponential form. For an AI
memory store this is the right default because un-accessed memories *should*
become less retrievable over time, exactly as human memory does:

| Time elapsed | Approximate retention |
|--------------|-----------------------|
| 1 hour       | ~50% |
| 24 hours     | ~30–35% |
| 7 days       | ~25% |
| 30 days      | ~10% |

### 3.2 Half-Life Defaults

These half-lives are forgetting-curve tunings, not arbitrary TTLs. They are
RECOMMENDED defaults; implementations SHOULD tune them per deployment.

| Half-life | Memory horizon | Forgetting-curve rationale |
|-----------|----------------|----------------------------|
| **P7D** | Short-term context | Weekly work cycle; episodic consolidation window |
| **P14D** | Medium-term projects | Spans a typical sprint/iteration |
| **P30D** | Long-term knowledge | Monthly review cycle; ~30-day consolidation period seen in memory studies |
| **P90D** | Default TTL | Quarterly relevance for durable knowledge |

Tuning guidance:

- **Episodic decays faster than semantic.** A `session` should forget faster
  than a stable `observation`. Apply a shorter half-life (e.g. P7D) to episodic
  memories and a longer one (e.g. P30D) to semantic facts.
- **Access reinforces.** Each recall MAY reset or slow decay by updating
  `lastReinforced` and incrementing `accessCount`, analogous to spaced
  repetition strengthening a memory trace. This is why the `recallable` trait
  carries `accessCount` and `lastAccessed`.
- **High-velocity environments forget faster.** Shorten half-lives where context
  churns quickly; lengthen them for stable domains.

### 3.3 Example

```yaml
temporal:
  validFrom: 2026-01-15T00:00:00Z
  validUntil: null
  recordedAt: 2026-01-15T10:30:00Z
  ttl: P90D
  decay:
    model: exponential
    halfLife: P7D          # forgetting-curve half-life
    strength: 0.85
    lastReinforced: 2026-01-18T09:00:00Z
  accessCount: 5
  lastAccessed: 2026-01-20T14:22:00Z
```

**References**

- Ebbinghaus, H. (1885). *Memory: A Contribution to Experimental Psychology.*
- Murre & Dros (2015). [Replication and Analysis of Ebbinghaus' Forgetting Curve](https://pmc.ncbi.nlm.nih.gov/articles/PMC4492928/).
- Squire & Bayley (2007). [The neuroscience of remote memory](https://pmc.ncbi.nlm.nih.gov/articles/PMC2791502/).
- Wickelgren (1972). [Trace resistance and the decay of long-term memory](https://psycnet.apa.org/record/1973-08477-007).

---

## 4. Episodic Session Framing

In this profile, episodic memories are **sessions**: bounded stretches of agent
activity with a beginning and an end. The `ai-memory` ontology defines a
`session` entity type (`base: episodic`) under the `_episodic/sessions`
namespace. A session memory SHOULD record:

- `session_type` — one of `debug`, `work`, `meeting`, `exploration`, `review`.
- `summary` — what happened.
- `started_at` / `ended_at` — the time bounds that make the memory episodic.
- `participants` — agents or people present.
- `outcomes` — decisions, fixes, or artifacts produced.

Session types correspond to recognizable agent activities:

- **debug session** — reproducing and fixing a defect; high churn, short half-life.
- **work session** — implementing a feature or task.
- **meeting session** — a sync, standup, or review with other participants.

Facts learned and skills practiced during a session SHOULD link back to it via
the `learned_in` / `recalled_in` relationships, so the agent can trace *which
episode* a piece of semantic or procedural memory came from.

---

## 5. Recall-Oriented Embeddings

The core spec (core spec §11) stores embedding **metadata**, not raw vectors,
and is deliberately model-agnostic. This profile uses that mechanism for one
purpose: **similarity recall** — finding the memories most relevant to the
agent's current context.

The `recallable` trait in [`./ontology.yaml`](./ontology.yaml) carries
access-frequency and last-access metadata together with an embedding reference;
in the JSON-LD projection these correspond to the schema's `accessCount`/`lastAccessed`
and `model`/`sourceText`. Profile guidance:

- Embed the `sourceText` that best represents *what the agent would search for*,
  not necessarily the full stored content. For a session, that is usually the
  `summary`; for an observation, the `statement`.
- Recall ranking SHOULD combine embedding similarity with decay `strength`: a
  highly similar but heavily-decayed memory is less useful than a fresh one. A
  simple composite is `score = similarity * strength`.
- Re-embedding on import (per core §11.1) is expected when migrating between
  models; only the metadata and `sourceText` need survive.

```yaml
embedding:
  model: text-embedding-3-small
  modelVersion: "2024-01"
  dimensions: 1536
  sourceText: "User prefers dark mode"
  normalized: true
```

---

## 6. Migration Guides

These map each system's memory model onto MIF v1.0 `.md`/JSON-LD concepts.
In every case, the memory `type` lands on the triad, the namespace uses a
triad-prefixed path, and provider-specific fields are preserved under
`extensions`.

### 6.1 From Mem0

Mem0 stores flat memories with a free-form `metadata.category`.

```python
# Mem0 export
{
    "id": "mem0_123",
    "memory": "User prefers dark mode",
    "user_id": "user_456",
    "metadata": {"category": "preference"},
    "created_at": "2026-01-15T10:30:00Z"
}

# MIF mapping
{
    "@context": "https://mif-spec.dev/schema/context.jsonld",
    "@id": "urn:mif:mem0_123",                 # id -> @id
    "content": "User prefers dark mode",       # memory -> content
    "conceptType": "semantic",                  # a preference is a known fact
    "namespace": "_semantic/preferences",      # base type + category
    "created": "2026-01-15T10:30:00Z",         # created_at -> created
    "extensions": {
        "mem0": {"original_id": "mem0_123", "category": "preference"}
    }
}
```

### 6.2 From Zep

Zep is a temporal knowledge graph; its `t_valid` / `t_invalid` map directly onto
the bi-temporal model, and its entity edges become relationships.

```python
# Zep node
{
    "uuid": "zep_789",
    "content": "User prefers dark mode",
    "created_at": "2026-01-15T10:30:00Z",
    "t_valid": "2026-01-15T00:00:00Z",
    "t_invalid": null,
    "entity_edges": [...],
    "embedding": [0.1, 0.2, ...]
}

# MIF mapping
{
    "@id": "urn:mif:zep_789",
    "content": "User prefers dark mode",
    "created": "2026-01-15T10:30:00Z",
    "temporal": {
        "validFrom": "2026-01-15T00:00:00Z",   # t_valid
        "validUntil": null,                     # t_invalid
        "recordedAt": "2026-01-15T10:30:00Z"   # created_at
    },
    "relationships": [...],                     # entity_edges
    "embedding": {
        "model": "zep-default",
        "sourceText": "User prefers dark mode"  # vectors re-embedded on import
    }
}
```

### 6.3 From Letta (Agent File)

Letta memory blocks are dense, multi-fact strings. Split each block into one MIF
memory per fact so decay and recall apply at the right granularity.

```python
# Letta memory block
{
    "label": "human",
    "value": "Name: Alice. Prefers dark mode.",
    "limit": 5000
}

# MIF mapping (one memory per fact)
{
    "@id": "urn:mif:letta-human-name",
    "conceptType": "semantic",
    "content": "Name: Alice",
    "namespace": "_semantic/entities"
},
{
    "@id": "urn:mif:letta-human-pref",
    "conceptType": "semantic",
    "content": "Prefers dark mode",
    "namespace": "_semantic/preferences"
}
```

### 6.4 From Subcog

Subcog memories are already namespaced; the mapping is nearly 1:1, prefixing the
namespace with its triad base type.

```python
# Subcog memory
{
    "id": "subcog_abc",
    "content": "Decision: Use React",
    "namespace": "decisions",
    "domain": "project",
    "tags": ["frontend"],
    "created_at": "2026-01-15T10:30:00Z"
}

# MIF mapping
{
    "@id": "urn:mif:subcog_abc",
    "content": "Decision: Use React",
    "conceptType": "semantic",                  # a decision is known knowledge
    "namespace": "_semantic/decisions",        # base prefix + category
    "tags": ["frontend"],
    "created": "2026-01-15T10:30:00Z"
}
```

### 6.5 From Basic-Memory

Basic-Memory already stores Markdown notes with wiki-links and observations,
making it the closest fit to MIF. Notes become MIF `.md` documents; its
`observations` become `observation` entities and its wiki-links become MIF
relationships.

```markdown
<!-- Basic-Memory note: debugging-auth.md -->
# Debugging the auth timeout
- [observation] JWT clock skew caused the 401s #auth
- relates_to [[Auth Service]]
```

```yaml
# MIF mapping (frontmatter + body)
---
id: urn:mif:basicmem-debugging-auth
type: episodic                       # a note about a specific debugging effort
namespace: _episodic/sessions
title: "Debugging the auth timeout"
created: 2026-01-15T10:30:00Z
ontology:
  id: ai-memory
relationships:
  - type: relates-to
    target: urn:mif:entity:auth-service   # [[Auth Service]] -> relates-to
---
The auth timeout was caused by JWT clock skew producing 401s.
```

Standalone `[observation]` lines map to `observation` entities under
`_semantic/observations`, with the note recorded as their `derived_from_session`.

---

## 7. Conformance

An implementation conforms to the **AI Memory profile** when, in addition to
core-spec conformance:

1. It maps every stored memory `type` onto the `semantic` / `episodic` /
   `procedural` triad.
2. It applies an exponential (forgetting-curve) decay model by default to
   un-reinforced memories, with per-type half-lives per §3.2.
3. It updates `accessCount` / `lastAccessed` (and MAY update
   `lastReinforced`) on each recall.
4. It uses recall-oriented embedding metadata per §5 for similarity retrieval.

Profile conformance is independent of which ontology entity types are used; an
implementation MAY adopt the `ai-memory` ontology in full, in part, or define
its own entity types over the same triad.
