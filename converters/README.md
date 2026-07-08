<!-- diataxis_type: reference -->

# MIF Reference Converters

Reference converters that read a source AI-memory system and emit a MIF
**[Container Profile](../SPECIFICATION.md#container-profile-corpus-envelope--proposed)**
corpus (`*.corpus.json`) — many MIF memory units (and, where applicable, their
source `document` records) as one transportable artifact.

These realize the "reference converters … in progress (#77)" note in the
Container Profile section. Each converter:

- reads the source store **directly** (offline path) or via the source API,
  using only the source tool's own client dependency (no MIF runtime, no
  cross-source coupling — stdlib + the one source client);
- emits the Container Profile envelope (`@type: MemoryCorpus`), where each record
  is a schema-valid MIF memory unit (`conceptType` ∈ semantic|episodic|procedural,
  required `@context`/`@type`/`@id`/`content`/`created`);
- preserves source-specific fields losslessly under each memory's
  `extensions.<source>` for round-trip;
- derives stable `urn:mif:` ids via UUIDv5 from the source id under a fixed
  per-source namespace UUID (reusing an already-UUID source id where present).

All MIF emission goes through the shared [`_mif_common.py`](_mif_common.py)
helper, so every converter produces consistent, schema-valid output. Each
converter ships a **schema-validated example** under
[`../examples/converters/`](../examples/converters/); every emitted memory unit
is validated against [`../schema/mif.schema.json`](../schema/mif.schema.json).

## Converters

| Source | Directory | Typing (source → `conceptType`) |
|---|---|---|
| **MemPalace** | [`mempalace/`](mempalace/) | drawer → `episodic`; entity → `semantic` (see [ai-memory mapping](../profiles/ai-memory/MEMPALACE-MAPPING.md)) |
| **Mem0** | [`mem0/`](mem0/) | fact/observation → `semantic`; history event → `episodic` |
| **Letta** | [`letta/`](letta/) | core/archival passage → `semantic`; recall message → `episodic` |
| **Cognee** | [`cognee/`](cognee/) | entity / chunk / entity-type → `semantic`; source docs → `document` records |
| **Graphiti** | [`graphiti/`](graphiti/) | entity node → `semantic`; episode → `episodic`; edges → `relationships[]` (bitemporal → Level-3, kept in `extensions`) |
| **Obsidian** | [`obsidian/`](obsidian/) | note → `semantic`; journal/daily note → `episodic`; `[[wikilinks]]` → `relationships[]` |

All six emit the Container Profile natively (they do **not** go through the
retired MPF envelope). Each was verified with a schema-validated example: every
`kind: memory` payload validates against `schema/mif.schema.json`; `kind: document`
records (Cognee) carry a stable `@id` so provenance resolves within the corpus.

## Usage

```bash
python converters/mempalace/mempalace_to_mif.py --palace ~/.mempalace/palace --out palace.corpus.json
python converters/mem0/mem0_to_mif.py          --qdrant-path /tmp/qdrant       --out mem0.corpus.json
python converters/letta/letta_to_mif.py        --mode auto                     --out letta.corpus.json
python converters/cognee/cognee_to_mif.py      --dataset my-dataset            --out cognee.corpus.json
python converters/graphiti/graphiti_to_mif.py  --neo4j bolt://localhost:7687   --out graphiti.corpus.json
python converters/obsidian/obsidian_to_mif.py  --vault ~/MyVault               --out obsidian.corpus.json
```

Each converter needs only its source tool's own client (e.g. `chromadb` for
MemPalace, `qdrant-client` for Mem0, `neo4j` for Graphiti; Obsidian needs
nothing — a vault is plain Markdown), not the source runtime itself, and no MIF
runtime beyond the published schemas.

> **Obsidian is a converter, not a profile.** MIF's core stays vendor-neutral
> (see [ADR-017](../adr/ADR-017-revert-obsidian-compatibility.md)); Obsidian
> conventions live only in the source vault and are preserved under
> `extensions.obsidian`, never in the MIF unit's required shape.
