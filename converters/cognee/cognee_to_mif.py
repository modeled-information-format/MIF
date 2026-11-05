#!/usr/bin/env python3
"""
cognee_to_mif.py — reference converter: Cognee -> MIF Container Profile.

Reads a Cognee deployment (graph DB + vector DB + relational document catalogue,
scoped by user/dataset) and emits a MIF **Container Profile** corpus
(`*.corpus.json`, see SPECIFICATION.md "Container Profile"), where Cognee graph
nodes become `kind: "memory"` records whose payloads are valid MIF memory units,
and Cognee source documents (Data/Dataset rows) become `kind: "document"`
records that carry a stable `@id` so a memory's provenance resolves.

Source reading (faithful to the CHARON adapter it is ported from):

  Cognee stores its content across three backends tied together by a shared
  DataPoint UUID:
    * a graph database (Neo4j / Kuzu / Postgres / Neptune) holds
      DocumentChunks, Entities, EntityTypes and their relationships;
    * a vector database holds the embeddings (NOT emitted — MIF permits
      regeneration at import and Cognee embeddings are model-coupled);
    * a relational SQLAlchemy catalogue holds Dataset / Data (document) rows
      with user/tenant ownership.

  This converter drives Cognee's own Python API where the CHARON adapter does:
    * ``cognee.api.v1.datasets.datasets.list_datasets`` / ``list_data`` —
      source-of-truth document catalogue, with owner/tenant.
    * ``cognee.infrastructure.databases.graph.get_graph_engine`` →
      ``await graph.get_graph_data()`` — ``(nodes, edges)`` for the graph.
  The Cognee runtime is required only for a *live* read (guarded by
  ``_require_cognee``); the mapping functions below have no Cognee, mnemos or
  charon dependency and no MIF runtime, so they can be unit-tested directly.

Typing (Cognee -> MIF cognitive triad, conceptType enum exactly
semantic|episodic|procedural):

    Data / Dataset document row  -> kind="document" record (stable @id, provenance)
    DocumentChunk node           -> conceptType semantic (decontextualized
                                    knowledge distilled from a document)
    Entity node                  -> conceptType semantic
    EntityType node              -> conceptType semantic
    other DataPoint graph nodes  -> conceptType semantic

  Cognee has no strong episodic construct, so every emitted memory is
  ``semantic``. Namespace is ``_semantic/<dataset-or-entitytype>``. Cognee-native
  fields (DataPoint UUID, node type, dataset/user ownership, chunk index, ...)
  survive round-trip under ``extensions.cognee``.

Usage:
    python -m cognee_to_mif --out cognee.corpus.json
    python -m cognee_to_mif --dataset my_dataset --out cognee.corpus.json
    python -m cognee_to_mif --out - | python ../../scripts/okf_validate.py --stdin-corpus

Determinism: a given Cognee snapshot produces a byte-identical corpus modulo the
`provenance.generatedAtTime` timestamp. Memory/document `@id`s are UUIDv5-derived
from the Cognee DataPoint UUID under a fixed Cognee namespace UUID, so they are
stable across re-exports (a node whose id is already a UUID keeps that UUID).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# Shared MIF-facing helpers — the only import this converter needs for OUTPUT.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _mif_common import (  # noqa: E402
    CONCEPT_TYPES,
    MIF_CONTEXT,
    build_corpus,
    iso,
    mif_memory,
    mif_uuid,
    ns_component,
)

SOURCE_SYSTEM = "cognee"

# Fixed Cognee namespace UUID for deterministic UUIDv5 derivation of MIF ids.
COGNEE_NS = uuid.UUID("5f2b1c8e-9d3a-5e47-b1c0-6a4e2d9f0c81")

# Cognee is required only for a *live* read. The mapping functions below never
# touch it, so import is guarded and deferred.
try:
    import cognee  # type: ignore  # noqa: F401

    _COGNEE_AVAILABLE = True
except ImportError:
    _COGNEE_AVAILABLE = False

# Graph node classes that are Cognee source *documents*; they are already
# represented as kind="document" records from the relational Data catalogue and
# must not be duplicated as memories.
_DOC_GRAPH_TYPES = {
    "Document", "TextDocument", "PdfDocument", "AudioDocument", "ImageDocument",
    "CsvDocument", "UnstructuredDocument", "DltRowDocument",
}


def _require_cognee() -> None:
    if not _COGNEE_AVAILABLE:
        raise SystemExit(
            "cognee is required for a live read. Install with:\n"
            "  pip install cognee\n"
            "and point it at your configured graph + vector stores via the same "
            "env vars the Cognee runtime uses (GRAPH_DATABASE_*, VECTOR_DB_*, DB_*)."
        )


# ─── Cognee access (mirrors the CHARON adapter) ──────────────────────────────


async def _load_datasets(dataset_names: Optional[List[str]]) -> List[Any]:
    """Return the Dataset rows to export (all readable, or name-filtered)."""
    from cognee.api.v1.datasets import datasets as datasets_api  # type: ignore

    all_datasets = await datasets_api.list_datasets()
    if not dataset_names:
        return list(all_datasets)
    wanted = set(dataset_names)
    return [ds for ds in all_datasets if getattr(ds, "name", None) in wanted]


async def _load_dataset_data(dataset: Any) -> List[Any]:
    """Return the Data (document) rows for a given dataset."""
    from cognee.api.v1.datasets import datasets as datasets_api  # type: ignore

    return list(await datasets_api.list_data(dataset.id))


async def _load_graph_snapshot() -> Tuple[List[Any], List[Any]]:
    """Return ``(nodes, edges)`` from Cognee's graph engine."""
    from cognee.infrastructure.databases.graph import (  # type: ignore
        get_graph_engine,
    )

    graph = await get_graph_engine()
    nodes, edges = await graph.get_graph_data()
    return list(nodes or []), list(edges or [])


# ─── Node + edge normalisation (faithful to CHARON) ──────────────────────────


def _node_id(node: Any) -> str:
    """Stable string id from whatever the backend returned (dict / (id, props)
    tuple / DataPoint instance). DataPoint ids are always UUIDs."""
    if isinstance(node, tuple) and len(node) == 2:
        nid, _props = node
        return str(nid)
    if isinstance(node, dict):
        for key in ("id", "node_id", "uuid"):
            if key in node and node[key] is not None:
                return str(node[key])
    return str(getattr(node, "id", node))


def _node_props(node: Any) -> Dict[str, Any]:
    """Normalise a node into its properties dict."""
    if isinstance(node, tuple) and len(node) == 2:
        _nid, props = node
        return dict(props or {})
    if isinstance(node, dict):
        if "properties" in node and isinstance(node["properties"], dict):
            merged = dict(node["properties"])
            for k in ("id", "type"):
                if k in node and k not in merged:
                    merged[k] = node[k]
            return merged
        return dict(node)
    if hasattr(node, "model_dump"):
        return node.model_dump(mode="json")
    if hasattr(node, "dict"):
        return node.dict()
    return {}


def _node_type(props: Dict[str, Any]) -> str:
    """Cognee writes the class name into ``type`` / ``_type``; default DataPoint."""
    return str(
        props.get("type")
        or props.get("_type")
        or props.get("node_type")
        or "DataPoint"
    )


def _edge_parts(edge: Any) -> Tuple[str, str, str, Dict[str, Any]]:
    """Return ``(source_id, target_id, relationship_name, properties)``."""
    if isinstance(edge, (list, tuple)):
        if len(edge) == 4:
            s, t, r, p = edge
            return str(s), str(t), str(r or ""), dict(p or {})
        if len(edge) == 3:
            s, t, r = edge
            return str(s), str(t), str(r or ""), {}
    if isinstance(edge, dict):
        s = edge.get("source") or edge.get("source_node_id") or edge.get("from")
        t = edge.get("target") or edge.get("target_node_id") or edge.get("to")
        r = (
            edge.get("relationship_name")
            or edge.get("rel_name")
            or edge.get("type")
            or edge.get("label")
            or ""
        )
        p = edge.get("properties") or {}
        return str(s), str(t), str(r), dict(p or {})
    return "", "", "", {}


# ─── Data (document) -> MIF kind="document" record ───────────────────────────


def _data_to_record(data_row: Any, dataset: Any) -> Dict[str, Any]:
    """Shape a Cognee Data row (document catalogue entry) into a MIF Container
    ``kind="document"`` record with a stable ``@id`` so a chunk memory's
    ``relationships`` / provenance can resolve to the source document."""
    if hasattr(data_row, "to_json"):
        data_dict = data_row.to_json()
    elif isinstance(data_row, dict):
        data_dict = dict(data_row)
    else:
        data_dict = {
            k: getattr(data_row, k, None)
            for k in (
                "id", "name", "extension", "mime_type", "raw_data_location",
                "content_hash", "token_count", "data_size",
                "created_at", "updated_at", "owner_id", "tenant_id",
            )
        }

    doc_id = str(data_dict.get("id"))
    mif_id = mif_uuid(COGNEE_NS, f"document:{doc_id}", restore=doc_id)

    # DocumentReference (schema/mif.schema.json#/$defs/DocumentReference) is
    # additionalProperties:false and carries no extensions mechanism (unlike
    # Memory), so none of @id/namespace/created/extensions is representable
    # here -- this cognee-specific metadata (dataset_id, token_count,
    # owner/tenant, updated_at, ...) has no schema-conformant home on a
    # document record and is intentionally dropped, not preserved elsewhere.
    payload: Dict[str, Any] = {
        "@type": "DocumentReference",
        "id": mif_id,
        "title": data_dict.get("name") or f"cognee-doc-{doc_id}",
    }
    if data_dict.get("raw_data_location"):
        payload["url"] = str(data_dict["raw_data_location"])
    if data_dict.get("content_hash"):
        payload["hash"] = {"algorithm": "sha256", "value": str(data_dict["content_hash"])}
    if data_dict.get("mime_type"):
        payload["contentType"] = str(data_dict["mime_type"])
    return {"kind": "document", "payload": payload}


# ─── Graph node -> MIF kind="memory" record (conceptType semantic) ───────────


def _chunk_to_record(
    node_id: str,
    props: Dict[str, Any],
    parent_doc_id: Optional[str],
    *,
    ds_name: str,
    owner: Optional[str],
) -> Dict[str, Any]:
    """DocumentChunk node -> semantic memory. Decontextualized knowledge
    distilled from a document => ``semantic`` per the mapping."""
    content = props.get("text") or props.get("content") or ""
    parent_mif = (
        mif_uuid(COGNEE_NS, f"document:{parent_doc_id}", restore=parent_doc_id)
        if parent_doc_id
        else None
    )
    ext: Dict[str, Any] = {
        "datapoint_id": node_id,
        "node_type": "DocumentChunk",
        "chunk_index": props.get("chunk_index"),
        "chunk_size": props.get("chunk_size"),
        "cut_type": props.get("cut_type"),
        "is_part_of": parent_doc_id,
        "version": props.get("version"),
        "topological_rank": props.get("topological_rank"),
        "importance_weight": props.get("importance_weight"),
        "dataset_name": ds_name,
        "owner_id": owner,
    }
    relationships = None
    if parent_mif:
        relationships = [{"type": "derived-from", "target": parent_mif}]
    payload = mif_memory(
        mif_id=mif_uuid(COGNEE_NS, f"chunk:{node_id}", restore=node_id),
        concept_type="semantic",
        content=content,
        namespace=f"_semantic/{ns_component(ds_name)}",
        created=iso(props.get("created_at")),
        tags=["cognee", "document-chunk"],
        relationships=relationships,
        source=SOURCE_SYSTEM,
        extensions={k: v for k, v in ext.items() if v is not None},
    )
    return {"kind": "memory", "payload": payload}


def _entity_like_to_record(
    node_id: str,
    props: Dict[str, Any],
    node_type: str,
    *,
    ds_name: str,
    owner: Optional[str],
) -> Dict[str, Any]:
    """Entity / EntityType / other DataPoint node -> semantic memory,
    preserving the Cognee class name and description under extensions.

    EntityTypes namespace on their own name (``_semantic/<entity-type>``); other
    nodes namespace on the dataset."""
    name = props.get("name") or ""
    description = props.get("description") or props.get("text") or ""
    if name and description:
        content = f"{name}: {description}"
    else:
        content = description or name or ""

    # EntityType is itself the namespace axis the mapping calls out; other nodes
    # (Entity, generic DataPoint) namespace under their dataset.
    if node_type == "EntityType":
        ns_label = name or node_type
    else:
        ns_label = ds_name

    ext: Dict[str, Any] = {
        "datapoint_id": node_id,
        "node_type": node_type,
        "name": name or None,
        "description": description or None,
        "is_a": props.get("is_a"),
        "version": props.get("version"),
        "topological_rank": props.get("topological_rank"),
        "importance_weight": props.get("importance_weight"),
        "dataset_name": ds_name,
        "owner_id": owner,
    }
    tag = "cognee-" + ns_component(node_type).lower()
    payload = mif_memory(
        mif_id=mif_uuid(COGNEE_NS, f"node:{node_id}", restore=node_id),
        concept_type="semantic",
        content=content,
        namespace=f"_semantic/{ns_component(ns_label)}",
        created=iso(props.get("created_at")),
        title=name or None,
        tags=["cognee", tag],
        source=SOURCE_SYSTEM,
        extensions={k: v for k, v in ext.items() if v is not None},
    )
    return {"kind": "memory", "payload": payload}


# ─── Extraction pipeline ─────────────────────────────────────────────────────


async def _collect(dataset_names: Optional[List[str]]) -> List[Dict[str, Any]]:
    """Main extraction: relational Data rows -> kind=document records; graph
    DocumentChunk/Entity/EntityType/... nodes -> kind=memory records."""
    _require_cognee()

    datasets = await _load_datasets(dataset_names)
    if not datasets:
        return []

    records: List[Dict[str, Any]] = []
    ds_owner: Dict[str, Tuple[str, Optional[str]]] = {}  # ds_id -> (ds_name, owner)

    # 1) Relational catalogue -> document records.
    for ds in datasets:
        ds_name = getattr(ds, "name", None) or str(getattr(ds, "id", ""))
        owner = str(getattr(ds, "owner_id", "") or "") or None
        ds_owner[str(getattr(ds, "id", ""))] = (ds_name, owner)
        for data_row in await _load_dataset_data(ds):
            records.append(_data_to_record(data_row, ds))

    # 2) Graph snapshot.
    nodes, edges = await _load_graph_snapshot()

    node_index: Dict[str, Dict[str, Any]] = {}
    node_type_index: Dict[str, str] = {}
    for n in nodes:
        nid = _node_id(n)
        if not nid:
            continue
        props = _node_props(n)
        node_index[nid] = props
        node_type_index[nid] = _node_type(props)

    # 3) chunk -> document parentage from structural is_part_of edges.
    chunk_to_doc: Dict[str, str] = {}
    for edge in edges:
        src, tgt, rel, _props = _edge_parts(edge)
        if not src or not tgt:
            continue
        if rel == "is_part_of" and node_type_index.get(src) == "DocumentChunk":
            chunk_to_doc[src] = tgt

    # 4) Node pass -> memory records (skip document-class graph nodes; the Data
    #    catalogue already produced their kind=document record).
    for nid, props in node_index.items():
        ntype = node_type_index[nid]
        if ntype in _DOC_GRAPH_TYPES:
            continue
        ds_id = str(props.get("dataset_id") or "")
        ds_name, owner = ds_owner.get(
            ds_id, next(iter(ds_owner.values()), ("default", None))
        )
        if ntype == "DocumentChunk":
            parent_doc = chunk_to_doc.get(nid) or str(props.get("is_part_of") or "") or None
            records.append(
                _chunk_to_record(nid, props, parent_doc, ds_name=ds_name, owner=owner)
            )
        else:
            records.append(
                _entity_like_to_record(nid, props, ntype, ds_name=ds_name, owner=owner)
            )

    return records


# ─── Streaming iterator ──────────────────────────────────────────────────────


def iter_records(dataset_names: Optional[List[str]] = None) -> Iterator[Dict[str, Any]]:
    """Yield MIF Container records (kind=document / kind=memory) one at a time.

    Cognee returns its graph snapshot as one ``(nodes, edges)`` pair, so we
    materialise once then yield — but callers get the familiar iterator surface
    for composition with downstream MIF tooling."""
    for rec in _collect_sync(dataset_names):
        yield rec


def _collect_sync(dataset_names: Optional[List[str]]) -> List[Dict[str, Any]]:
    return asyncio.run(_collect(dataset_names))


# ─── Container assembly ──────────────────────────────────────────────────────


def build_container(
    dataset_names: Optional[List[str]] = None,
    *,
    source_instance: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble a MIF Container Profile corpus from a Cognee deployment snapshot."""
    records = _collect_sync(dataset_names)
    return build_corpus(records, source_system=SOURCE_SYSTEM, source_instance=source_instance)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="cognee_to_mif",
        description="Convert a Cognee deployment to a MIF Container Profile corpus.",
    )
    ap.add_argument(
        "--dataset", action="append", dest="datasets", default=None, metavar="NAME",
        help="Restrict export to this dataset (by name). Repeatable. Omit to "
             "export every dataset readable by the current user.",
    )
    ap.add_argument("--out", default="-", help="Output path, or '-' for stdout (default).")
    ap.add_argument(
        "--source-instance", default=None,
        help="Optional source instance IRI/label for corpus provenance "
             "(e.g. a deployment hostname).",
    )
    args = ap.parse_args(argv)

    corpus = build_container(args.datasets, source_instance=args.source_instance)
    text = json.dumps(corpus, indent=2, ensure_ascii=False)
    if args.out == "-":
        sys.stdout.write(text + "\n")
    else:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        sys.stderr.write(f"wrote {len(corpus['records'])} records -> {args.out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
