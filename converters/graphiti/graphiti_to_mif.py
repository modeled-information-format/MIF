#!/usr/bin/env python3
"""
graphiti_to_mif.py — reference converter: Graphiti temporal KG -> MIF Container Profile.

Reads a Graphiti temporal knowledge graph (Neo4j by default) and emits a MIF
**Container Profile** corpus (`*.corpus.json`, see SPECIFICATION.md "Container
Profile"), where each Graphiti node becomes a `kind: "memory"` record whose
payload is a valid MIF memory unit.

Graphiti is a bi-temporal knowledge graph. Its store holds two families of node
plus typed edges between them:

  * **Entity nodes** — the facts/entities distilled into the KG. They are
    declarative knowledge about the world, so they map to the cognitive-triad
    `conceptType: semantic` and live under the `_semantic/entities/<group>`
    namespace.
  * **Episodic nodes** — the time-anchored raw events (messages, documents,
    JSON) that were ingested and from which entities were extracted. They are
    records of something that happened at a point in time, so they map to
    `conceptType: episodic` under `_episodic/episodes/<group>`.
  * **Edges / relationships** between entities (Graphiti `RELATES_TO` /
    `EntityEdge`) become MIF `relationships[]` on the **subject** memory: the
    relationship `type` is the edge label (kebab-cased) and `target` points at
    the object entity's `urn:mif:` id (its bundle identity). The Graphiti-minted
    `fact` sentence and edge uuid travel in the relationship `metadata`.

Bi-temporal validity (Level-3 deferral)
---------------------------------------
Graphiti carries TWO time axes: `created_at` (when the system ingested/observed
the fact) and `valid_at` / `invalid_at` (when the fact was true *in the world*).
Bi-temporal world-validity is a **Level-3** concern in MIF and is deliberately
NOT folded into the Level-1 `created` / `modified` fields (those track record
lifecycle, not world-truth). Instead the full bi-temporal window is preserved
losslessly under the memory's `extensions.graphiti` blob
(`{valid_at, invalid_at, created_at, ...}`), where a downstream Level-3 temporal
sidecar can lift it into `temporal.validFrom` / `temporal.validUntil`. This
matches the ai-memory mapping's treatment of bi-temporal validity: only
`created_at` participates in the Level-1 `created` field; the validity window is
carried as provider-specific extension data pending a Level-3 pass.

Source access
-------------
Reads the backing graph store directly with Cypher (Neo4j default, via the same
`neo4j` driver the CHARON adapter uses), so the `graphiti` runtime is not
required — an adapter must be operable against a quiesced snapshot. Only the
stdlib plus the `neo4j` driver are needed; there is no mnemos/charon or MIF
runtime dependency.

Usage:
    python -m graphiti_to_mif --neo4j bolt://localhost:7687 \
        --neo4j-user neo4j --neo4j-password $NEO4J_PASSWORD \
        --out graphiti.corpus.json
    python -m graphiti_to_mif --neo4j bolt://... --group-id customer-42 \
        --out - | python ../../scripts/okf_validate.py --stdin-corpus

Determinism: a given graph snapshot + group filter produces a byte-identical
corpus modulo `provenance.generatedAtTime`. Memory `@id`s are UUIDv5-derived
from the Graphiti node uuid under a fixed Graphiti namespace UUID (or reuse the
node's own uuid when it is already a UUID), so they are stable across re-exports.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from _mif_common import (  # noqa: E402
    build_corpus,
    iso,
    mif_memory,
    mif_uuid,
    ns_component,
)

SOURCE_SYSTEM = "graphiti"

# Fixed Graphiti namespace UUID for deterministic UUIDv5 derivation of memory
# ids. Stable so re-exports of the same node produce the same urn:mif: id.
GRAPHITI_NS = uuid.UUID("6c3d8f1a-2b47-5e9c-a1d0-7f4e2b8c9d63")

try:
    import neo4j  # type: ignore
except ImportError:
    neo4j = None  # noqa: N816


# ─── Backend (Neo4j, mirroring the CHARON adapter's Neo4jBackend) ────────────


def _gid_clause(group_id: Optional[str], var: str = "n") -> tuple[str, Dict[str, Any]]:
    if group_id is None:
        return "", {}
    return f" WHERE {var}.group_id = $group_id ", {"group_id": group_id}


class Neo4jBackend:
    """Uniform Cypher reader over the Graphiti Neo4j store. Only the SELECT
    surface Graphiti uses is needed (MATCH with optional group_id filter)."""

    def __init__(self, uri: str, user: str, password: str, database: Optional[str] = None):
        if neo4j is None:
            raise SystemExit(
                "neo4j driver is required for the Neo4j backend. Install with:\n"
                "  pip install neo4j"
            )
        self._driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        self._database = database

    def close(self) -> None:
        try:
            self._driver.close()
        except Exception:
            pass

    def _run(self, cy: str, **params: Any) -> Iterator[Dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            for rec in session.run(cy, **params):
                yield dict(rec)

    def entities(self, group_id: Optional[str]) -> Iterator[Dict[str, Any]]:
        where, params = _gid_clause(group_id, "n")
        yield from self._run(
            f"MATCH (n:Entity){where}RETURN n, labels(n) AS labels", **params
        )

    def episodes(self, group_id: Optional[str]) -> Iterator[Dict[str, Any]]:
        where, params = _gid_clause(group_id, "n")
        yield from self._run(f"MATCH (n:Episodic){where}RETURN n", **params)

    def entity_edges(self, group_id: Optional[str]) -> Iterator[Dict[str, Any]]:
        where, params = _gid_clause(group_id, "e")
        yield from self._run(
            "MATCH (s:Entity)-[e:RELATES_TO]->(t:Entity)"
            + where
            + "RETURN e, s.uuid AS source_uuid, t.uuid AS target_uuid, "
            "s.name AS source_name, t.name AS target_name",
            **params,
        )


# ─── Row normalisation ───────────────────────────────────────────────────────


def _unwrap_node(val: Any) -> Dict[str, Any]:
    """Neo4j `Node` -> dict; pass a dict through unchanged."""
    props = getattr(val, "_properties", None)
    if props is not None:
        return dict(props)
    if hasattr(val, "items") and not isinstance(val, dict):
        try:
            return dict(val.items())
        except Exception:
            pass
    return dict(val) if isinstance(val, dict) else {}


def _isoformat(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        return v
    if isinstance(v, datetime):
        return v.isoformat()
    fmt = getattr(v, "iso_format", None)  # neo4j.time.DateTime
    if callable(fmt):
        return fmt()
    return str(v)


def _coerce_attrs(raw: Any) -> Dict[str, Any]:
    """Graphiti stashes per-node attributes either as a JSON string or as a
    dict. Normalise to a dict."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            out = json.loads(raw)
            return out if isinstance(out, dict) else {"_raw": out}
        except json.JSONDecodeError:
            return {"_raw": raw}
    return {"_raw": raw}


def _kebab(text: Any) -> str:
    """Coerce an edge label into a schema-valid relationship type token
    (^[a-z0-9][a-z0-9-]*(:[a-z0-9][a-z0-9-]*)?$)."""
    import re

    t = re.sub(r"[^a-z0-9]+", "-", str(text or "").strip().lower()).strip("-")
    return t or "relates-to"


# ─── Mapping: Graphiti node/edge -> MIF memory unit ──────────────────────────


def _node_urn(node_uuid: Optional[str], fallback_key: str) -> str:
    """urn:mif: id for a Graphiti node. Reuse the node's own uuid if it is a
    UUID; else UUIDv5(Graphiti-ns, uuid-or-fallback-key)."""
    seed = node_uuid or fallback_key
    return mif_uuid(GRAPHITI_NS, seed, restore=node_uuid)


def entity_to_memory(
    row: Dict[str, Any],
    *,
    edges_by_source: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    """Map a Graphiti Entity node -> MIF `semantic` memory. If `edges_by_source`
    is supplied (keyed by source entity uuid), the entity's outgoing edges are
    attached as `relationships[]`."""
    n = _unwrap_node(row.get("n"))
    labels = row.get("labels") or []
    if isinstance(labels, str):
        labels = [labels]
    labels = [lbl for lbl in labels if lbl != "Entity"]

    node_uuid = n.get("uuid")
    name = n.get("name", "") or ""
    summary = n.get("summary", "") or ""
    body = f"{name}\n\n{summary}" if summary else name
    group = n.get("group_id") or "default"

    tags = ["graphiti", "entity"] + [str(lbl) for lbl in labels]

    # Bi-temporal + provider round-trip blob (Level-3 deferral: valid_at /
    # invalid_at are preserved here, NOT folded into created/modified).
    ext: Dict[str, Any] = {
        "kind": "EntityNode",
        "uuid": node_uuid,
        "name": name,
        "group_id": n.get("group_id"),
        "labels": labels,
        "attributes": _coerce_attrs(n.get("attributes")),
        "created_at": _isoformat(n.get("created_at")),
        "valid_at": _isoformat(n.get("valid_at")),
        "invalid_at": _isoformat(n.get("invalid_at")),
    }

    relationships: List[Dict[str, Any]] = []
    for edge in (edges_by_source or {}).get(str(node_uuid), []):
        relationships.append(edge)

    return mif_memory(
        mif_id=_node_urn(node_uuid, f"entity:{name}:{group}"),
        concept_type="semantic",
        content=body,
        namespace=f"_semantic/entities/{ns_component(group)}",
        created=_isoformat(n.get("created_at")),
        title=name or None,
        tags=tags,
        relationships=relationships or None,
        source=SOURCE_SYSTEM,
        extensions=ext,
    )


def episode_to_memory(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map a Graphiti Episodic node -> MIF `episodic` memory."""
    n = _unwrap_node(row.get("n"))
    node_uuid = n.get("uuid")
    name = n.get("name", "") or ""
    content = n.get("content", "") or ""
    group = n.get("group_id") or "default"

    ext: Dict[str, Any] = {
        "kind": "EpisodicNode",
        "uuid": node_uuid,
        "name": name,
        "group_id": n.get("group_id"),
        "source": n.get("source"),
        "source_description": n.get("source_description"),
        "created_at": _isoformat(n.get("created_at")),
        "valid_at": _isoformat(n.get("valid_at")),
        "invalid_at": _isoformat(n.get("invalid_at")),
        "entity_edges": n.get("entity_edges") or [],
    }

    return mif_memory(
        mif_id=_node_urn(node_uuid, f"episode:{name}:{group}"),
        concept_type="episodic",
        content=content or name,
        namespace=f"_episodic/episodes/{ns_component(group)}",
        created=_isoformat(n.get("created_at")),
        title=name or None,
        tags=["graphiti", "episode"],
        source=SOURCE_SYSTEM,
        extensions=ext,
    )


def edge_to_relationship(row: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Map a Graphiti EntityEdge -> (source_uuid, MIF relationship). The
    relationship's `target` is the object entity's urn:mif: id. Bi-temporal
    validity + the Graphiti fact sentence ride in relationship `metadata`
    (Level-3 sidecar reads them from there)."""
    e = _unwrap_node(row.get("e"))
    source_uuid = row.get("source_uuid")
    target_uuid = row.get("target_uuid")
    target_name = row.get("target_name")
    label = e.get("name") or "relates_to"

    rel: Dict[str, Any] = {
        "type": _kebab(label),
        "target": _node_urn(target_uuid, f"entity:{target_name}:"),
        "metadata": {
            "graphiti": {
                "kind": "EntityEdge",
                "uuid": e.get("uuid"),
                "label": label,
                "fact": e.get("fact"),
                "group_id": e.get("group_id"),
                "created_at": _isoformat(e.get("created_at")),
                "valid_at": _isoformat(e.get("valid_at")),
                "invalid_at": _isoformat(e.get("invalid_at"))
                or _isoformat(e.get("expired_at")),
                "episodes": e.get("episodes") or [],
            }
        },
    }
    return str(source_uuid), rel


# ─── Corpus assembly ─────────────────────────────────────────────────────────


def iter_memory_records(
    backend: Neo4jBackend, *, group_id: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """Stream Container `memory` records: semantic entities (each carrying its
    outgoing edges as relationships[]) then episodic episodes."""
    # Gather entity edges first so each entity memory can embed its outgoing
    # relationships in one pass.
    edges_by_source: Dict[str, List[Dict[str, Any]]] = {}
    for row in backend.entity_edges(group_id):
        src, rel = edge_to_relationship(row)
        edges_by_source.setdefault(src, []).append(rel)

    for row in backend.entities(group_id):
        yield {
            "kind": "memory",
            "payload": entity_to_memory(row, edges_by_source=edges_by_source),
        }
    for row in backend.episodes(group_id):
        yield {"kind": "memory", "payload": episode_to_memory(row)}


def build_container(
    backend: Neo4jBackend,
    *,
    source_instance: Optional[str] = None,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble a MIF Container Profile corpus from a Graphiti graph snapshot."""
    records = list(iter_memory_records(backend, group_id=group_id))
    return build_corpus(
        records, source_system=SOURCE_SYSTEM, source_instance=source_instance
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="graphiti_to_mif",
        description="Convert a Graphiti temporal KG (Neo4j) to a MIF Container Profile corpus.",
    )
    ap.add_argument("--neo4j", default="bolt://localhost:7687", metavar="URI",
                    help="Neo4j bolt URI (default: bolt://localhost:7687).")
    ap.add_argument("--neo4j-user", default="neo4j",
                    help="Neo4j username (default: neo4j).")
    ap.add_argument("--neo4j-password", default=None,
                    help="Neo4j password (or env NEO4J_PASSWORD).")
    ap.add_argument("--neo4j-database", default=None,
                    help="Neo4j database name (default: driver default).")
    ap.add_argument("--group-id", default=None,
                    help="Restrict export to a single Graphiti group_id (tenant partition).")
    ap.add_argument("--out", default="-",
                    help="Output path, or '-' for stdout (default).")
    ap.add_argument("--source-instance", default=None,
                    help="Optional source instance IRI/label for corpus provenance.")
    args = ap.parse_args(argv)

    import os

    backend = Neo4jBackend(
        uri=args.neo4j,
        user=args.neo4j_user,
        password=args.neo4j_password or os.environ.get("NEO4J_PASSWORD", ""),
        database=args.neo4j_database,
    )
    try:
        corpus = build_container(
            backend, source_instance=args.source_instance, group_id=args.group_id
        )
    finally:
        backend.close()

    text = json.dumps(corpus, indent=2, ensure_ascii=False)
    if args.out == "-":
        sys.stdout.write(text + "\n")
    else:
        from pathlib import Path

        Path(args.out).write_text(text + "\n", encoding="utf-8")
        sys.stderr.write(f"wrote {len(corpus['records'])} records -> {args.out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
