<!-- diataxis_type: reference -->

# MIF Reference Converters

Reference converters that read a source AI-memory system and emit a **MIF
[Container Profile](../SPECIFICATION.md#container-profile-corpus-envelope--proposed)**
corpus (`*.corpus.json`) — many MIF memory units (and, where applicable, their
source `document` records) as one transportable artifact.

These realize the "reference converters … in progress (#77)" note in the
Container Profile section. Each converter:

- reads the source store **directly** (offline path) or via the source API,
  using only the source tool's own client dependency;
- emits the Container Profile envelope (`@type: MemoryCorpus`), where each record
  is a schema-valid MIF memory unit (`conceptType` ∈ semantic|episodic|procedural,
  required `@context`/`@type`/`@id`/`content`/`created`);
- preserves source-specific fields losslessly under each memory's
  `extensions.<source>` for round-trip;
- derives stable `urn:mif:` ids via UUIDv5 from the source id under a fixed
  per-source namespace UUID.

Every converter ships a **schema-validated example** under
[`../examples/converters/`](../examples/converters/); each emitted memory unit is
validated against [`../schema/mif.schema.json`](../schema/mif.schema.json).

## Converters

| Source | Directory | Typing (source → `conceptType`) | Status |
|---|---|---|---|
| **MemPalace** | [`mempalace/`](mempalace/) | drawer → `episodic` (session); entity → `semantic` (see [ai-memory mapping](../profiles/ai-memory/MEMPALACE-MAPPING.md)) | ✅ converter + validated example |
| **Mem0** | `mem0/` | fact/observation → `semantic`; history event → `episodic` | 🚧 in progress |
| **Letta** | `letta/` | core/archival passage → `semantic`; message/session → `episodic` | 🚧 in progress |
| **Cognee** | `cognee/` | entity/chunk → `semantic` | 🚧 in progress |
| **Graphiti** | `graphiti/` | entity node → `semantic`; episode → `episodic` (bitemporal → Level-3 sidecar) | 🚧 in progress |

The Mem0/Letta/Cognee/Graphiti converters are being ported from the existing
MPF-era adapters to emit the Container Profile natively, each landing as its own
PR with a schema-validated example (same shape as the MemPalace one). Their
source-reading paths are unchanged; only the output layer is re-targeted from the
retired MPF envelope to this Container Profile.

## Usage

```bash
# MemPalace -> MIF corpus
python converters/mempalace/mempalace_to_mif.py --palace ~/.mempalace/palace --out palace.corpus.json
```

Each converter needs only its source tool's own client (e.g. `chromadb` for
MemPalace, `qdrant-client` for Mem0) — not the source runtime itself, and no MIF
runtime beyond the published schemas.
