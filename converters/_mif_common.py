#!/usr/bin/env python3
"""
_mif_common.py — shared helpers for the MIF reference converters.

Every converter reads a source AI-memory system and emits a MIF **Container
Profile** corpus. This module centralizes the MIF-facing output so all
converters produce consistent, schema-valid units: a source only supplies a
mapping (id, conceptType, content, namespace, created, source-extensions) and
gets back a valid MIF memory unit and, at the end, a Container Profile corpus.

The emitted memory unit satisfies schema/mif.schema.json (required:
@context, @type, @id, conceptType, content, created).
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

MIF_CONTEXT = "https://mif-spec.dev/schema/context.jsonld"
MIF_VERSION = "1.2.2"
CONCEPT_TYPES = ("semantic", "episodic", "procedural")

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc).isoformat()


def ns_component(text: Any) -> str:
    """Coerce an arbitrary label into a valid namespace path component
    (^[a-zA-Z0-9_-]+$)."""
    c = re.sub(r"[^A-Za-z0-9_-]+", "-", str(text or "").strip()).strip("-")
    return c or "unknown"


def iso(value: Any) -> Optional[str]:
    """Return an ISO-8601-ish string unchanged, else None."""
    if not value:
        return None
    s = str(value)
    return s if ("T" in s or re.match(r"^\d{4}-\d{2}-\d{2}", s)) else None


def mif_uuid(namespace: uuid.UUID, source_id: str, *, restore: Optional[str] = None) -> str:
    """urn:mif:<uuid>. If `restore` is already a UUID, reuse it; else
    UUIDv5(namespace, source_id) — deterministic and stable across re-exports."""
    if restore:
        try:
            return "urn:mif:" + str(uuid.UUID(str(restore)))
        except (ValueError, AttributeError):
            pass
    return "urn:mif:" + str(uuid.uuid5(namespace, source_id))


def mif_memory(
    *,
    mif_id: str,
    concept_type: str,
    content: str,
    namespace: str,
    created: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    relationships: Optional[List[Dict[str, Any]]] = None,
    source: str,
    extensions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one schema-valid MIF memory unit. `source` names the provider whose
    round-trip blob (`extensions`) is preserved under `extensions.<source>`."""
    if concept_type not in CONCEPT_TYPES:
        raise ValueError(f"conceptType must be one of {CONCEPT_TYPES}, got {concept_type!r}")
    mem: Dict[str, Any] = {
        "@context": MIF_CONTEXT,
        "@type": "Memory",
        "@id": mif_id,
        "conceptType": concept_type,
        "namespace": namespace,
        "content": (content or "").strip() or "(empty)",
        "created": iso(created) or _EPOCH,
    }
    if title:
        mem["title"] = str(title)
    if tags:
        mem["tags"] = sorted({ns_component(t) if "/" not in str(t) else str(t) for t in tags})
    if relationships:
        mem["relationships"] = relationships
    if extensions:
        mem["extensions"] = {source: extensions}
    return mem


def build_corpus(
    records: List[Dict[str, Any]], *, source_system: str, source_instance: Optional[str] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrap `records` (each `{"kind": "memory"|"document", "payload": ...}`) in a
    MIF Container Profile corpus."""
    corpus: Dict[str, Any] = {
        "@context": MIF_CONTEXT,
        "@type": "MemoryCorpus",
        "mif_version": MIF_VERSION,
        "records": records,
        "provenance": {
            "@type": "prov:Entity",
            "prov:wasGeneratedBy": {
                "@type": "prov:Activity",
                "prov:used": source_system,
                "prov:generatedAtTime": generated_at or datetime.now(timezone.utc).isoformat(),
            },
        },
    }
    if source_instance:
        corpus["provenance"]["prov:wasDerivedFrom"] = source_instance
    return corpus
