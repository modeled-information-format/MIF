<!-- diataxis_type: reference -->

# Container Profile

**Proposed — see [ADR-021](../adr/ADR-021-container-profile.md).**

The Container Profile is an OPTIONAL, single-file JSON artifact
(`*.corpus.json`) that serializes a Bundle — or a subset of one — into one
self-describing transport envelope, so many memory units and the documents
they derive from can move across a wire boundary as a single artifact.

> **It is not a second storage format.** A Bundle (a directory of `.md`
> units, see SPECIFICATION.md §3.3) remains the authoring/storage shape. A
> container is what a Bundle looks like serialized to cross a wire boundary
> once — an API response, an export/import operation, a sync to a system
> that has no concept of a file tree.

---

## 1. Envelope shape

```json
{
  "@context": "https://mif-spec.dev/schema/container-context.jsonld",
  "@type": "MemoryCorpus",
  "containerProfileVersion": "0.1.0",
  "records": [
    { "kind": "memory", "payload": { "...": "a full MIF memory JSON-LD projection, conceptType required" } },
    { "kind": "document", "payload": { "@type": "DocumentReference", "url": "https://...", "hash": { "algorithm": "sha256", "value": "..." } } }
  ],
  "provenance": {
    "@type": "prov:Entity",
    "wasDerivedFrom": { "@id": "urn:mif:bundle:<bundle-id>" }
  },
  "editChain": [],
  "extensions": {}
}
```

See `examples/container/ncp-requirements.corpus.json` for a complete,
schema-valid worked example (two memory records, one document record, and a
vendor `extensions` block).

## 2. `records[]`, `kind`-discriminated

Every entry is `{ "kind": "memory" | "document", "payload": {...} }`.

- **`kind: "memory"`** payloads validate against `schema/mif.schema.json`
  unmodified — `conceptType` is required, exactly as for any standalone
  memory unit. A `payload` is exactly the JSON-LD projection of some
  canonical `.md` unit; nothing about an individual memory changes inside a
  container.
- **`kind: "document"`** payloads MUST be a `DocumentReference`
  (`schema/mif.schema.json#/$defs/DocumentReference`, see
  [ADR-014](../adr/ADR-014-document-reference-not-embed.md)) — a pointer
  (`url` or `id`, plus `hash`/`contentType`/`byteLength`), never an embedded
  vendor document schema.

Fact/Event distinction is expressed via `namespace` (e.g.
`_semantic/requirements/facts` vs. `_episodic/events`), the same rule that
applies to every MIF memory outside a container — there is no
`memoryCategory` field.

## 3. Corpus-level fields

| Field | Meaning |
| --- | --- |
| `containerProfileVersion` | The Container Profile schema's own version — independent of `mif_version` (which already means an implementation's declared spec-conformance version in `.mif/config.yaml`, §13.4). |
| `provenance` | Corpus-level provenance, reusing SPECIFICATION.md §12.3's PROV shape exactly: plain keys except `@type`; `wasDerivedFrom` (and any other PROV relation) takes object form `{"@id": "..."}`. |
| `editChain` | Corpus-transport edit/transfer lineage only — **not** a substitute for a memory record's own `Supersedes`/`SupersededBy` relationship (§8.2). If a record's own relationship disagrees with an `editChain` entry about the same pair, the per-record relationship wins. |
| `extensions` | See below. |

## 4. `extensions`: vendor-owned, unvalidated, and that is the point

Anything that is a single implementation's own concept — a compression
manifest, a version-DAG shape, anything that is not a MIF concept — travels
under a corpus-level `extensions` object, generalizing the per-unit
`extensions` field `schema/mif.schema.json` already defines
(`additionalProperties: true`, provider-namespaced keys like `subcog:domain`
today):

```json
"extensions": {
  "mnemos:compressionManifest": [ { "engine": "apollo", "compression_ratio": 0.42 } ]
}
```

MIF does not validate what is inside `extensions` — that is the owning
implementation's responsibility, in its own tooling. A concept is promoted
out of `extensions` into a native Container Profile field only once a
second, independent implementation needs the identical shape; until then,
reserving native vocabulary for one adopter's roadmap would encode that
adopter's internal data model as MIF's own — exactly the coupling this
mechanism exists to avoid. See ADR-021 Decision point 7.

`extensions` is mapped as JSON-LD `@type: @json` in
`schema/container-context.jsonld`, not the per-unit `extensions` field's
`@container: @index` pattern — `@type: @json` carries the entire object as
an opaque JSON-LD literal, round-tripping arbitrary vendor content through
`expand`/`compact` losslessly with zero imposed vocabulary. `@container:
@index` was tried first and confirmed (via `pyld.jsonld.expand()`) to
silently drop the *value* at each index key on expansion — only the key
itself survives — the same class of content-loss defect this whole design
exists to fix, recurring in a new field. See ADR-021 Decision point 8.

## 5. Validating a corpus locally

`*.corpus.json` files are **invisible to the `.md`-only gates**
(`okf_validate.py`, `mif_convert.py roundtrip`) by construction —
`mif_convert.py`'s `iter_concepts()` only discovers `*.md` files. Use the
dedicated validator instead:

```bash
python scripts/validate_container.py examples/container   # or any directory
```

This validates the envelope against `schema/container.schema.json`, then
every record's `payload` against the correct external schema for its
`kind` — `schema/mif.schema.json` for `kind: "memory"`, and
`schema/document-reference.schema.json` (a small `$ref` wrapper onto
`mif.schema.json`'s `DocumentReference` `$defs` entry — `ajv-cli` cannot
take a `#/$defs/...` fragment appended to `-s` directly) for
`kind: "document"`. `extensions` content is not schema-checked — see
§4 above.

Exit code `0` means every `*.corpus.json` file found conforms.

## 6. Round-tripping to and from a Bundle

A container's `kind: "memory"` records are exactly the JSON-LD projections
`scripts/mif_convert.py`'s `emit-jsonld` command already produces for any
Bundle. Reconstructing a Bundle from a container is the reverse projection
the same tool already performs for any other JSON-LD projection —
Invariant 2 (markdown is canonical, JSON-LD is derived) applies per-record,
not to the envelope as a whole.
