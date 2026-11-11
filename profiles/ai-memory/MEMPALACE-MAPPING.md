<!-- diataxis_type: reference -->

# MemPalace → MIF AI-Memory Mapping (draft)

> **Status: draft for discussion.** This maps the [MemPalace](https://github.com/MemPalace/mempalace)
> AI-memory system onto the MIF AI-Memory profile at **Level 1** (OKF-valid +
> cognitive-triad typing), and records what is deliberately deferred to Levels 2
> and 3. It is the field-mapping basis for the converter and the
> `examples/mempalace-*.md` Level-1 concepts in this PR.

## 1. Source model (MemPalace)

MemPalace stores memory in two structures:

- **Drawers** — content documents (`id`, `source`, `filed_at`, `added_by`),
  organized into *wings* (people / projects) and *rooms* (topics). MemPalace
  already exports these as `wing/room.md` markdown.
- **Knowledge graph** — *entities* (`id`, `name`, `type` ∈ {person, project,
  topic, animal, …}, a `properties` blob with `confidence`/`source`, `aliases`)
  and *triples* (`subject — predicate — object`) carrying **bitemporal validity**
  (`valid_from` / `valid_to`).

## 2. Structure mapping

| MemPalace construct | MIF concept | `type` (cognitive triad) | Namespace / path |
| --- | --- | --- | --- |
| **Entity** (person/project/topic/…) | one concept | **`semantic`** — decontextualized, stably-true world knowledge (`observation`) | `_semantic/observations` |
| **Drawer** (`filed_at`, `source`, `added_by`) | one concept | **`episodic`** — time-anchored record of a lived event (`session`) | `_episodic/sessions` |
| *(no native MemPalace construct)* | — | **`procedural`** (`skill`) | `_procedural/skills` — **declared gap**; a future export could route how-to drawers here |

## 3. Field mapping

| MemPalace field | MIF field | Notes |
| --- | --- | --- |
| entity `id` / drawer `id` | `id` | **UUIDv5** derived from the MemPalace id under a fixed MemPalace namespace UUID (`b7df7f72-3631-5a73-a4f2-b085a4a3b173`) when the source id is not already a UUID — deterministic and stable across re-exports. |
| entity `name` / drawer title | `title` | |
| drawer `filed_at` / entity first-seen | `created` | The fact's *assertion* time, when available. |
| wing / room | `namespace` + path | wing → `_episodic/sessions/<wing>`; topic rooms → `_semantic/observations/<room>`. |
| `properties.source`, `added_by` | `tags` (L1) → provenance (L2) | |
| `properties.confidence` | relationship `strength` (L1) → trust tier (L2) | |
| `aliases` | `aliases` (L2) | |

## 4. Triples → relationships

- **object is an entity** → a typed MIF `relationships[]` entry on the subject
  concept: `type` = predicate, `target` = the object concept's bundle-relative
  path, `strength` = `confidence`. Mirrored in the body `## Relationships` section
  (frontmatter ↔ body must stay in sync).
- **object is a literal/value** → mapped to the first-class scalar `properties`
  field (string / number / boolean / null), added in v1.0.0 (#79) precisely for
  literal-object triples that have no concept `target`. *(This mapping originally
  flagged the absence of such a construct; v1.0.0 closed that gap, so literals no
  longer need the body `## Properties` fallback.)*

## 5. Deferred to higher levels

- **Bitemporal validity (`valid_from` / `valid_to`)** → **Level 3**
  temporal / version-DAG sidecar. It is **not** folded into `created`/`modified`
  (those are document times, not fact-validity windows). This is the natural home
  for the *memory-version DAG sidecar* and edit-chain tracking.
- **Compression manifest** → Level-3 sidecar.
- **Trust tiers / provenance** (`confidence`, `source`, `added_by`) → Level 2.

## 6. Worked example

See [`examples/mempalace-observation.md`](examples/mempalace-observation.md)
(entity → `semantic` observation, with a triple rendered as a `derived-from`
relationship) and [`examples/mempalace-session.md`](examples/mempalace-session.md)
(drawer → `episodic` session). Both pass `scripts/okf_validate.py` and the
`scripts/mif_convert.py roundtrip` lossless check.
