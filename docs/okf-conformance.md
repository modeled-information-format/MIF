<!-- diataxis_type: reference -->

# OKF Conformance (pinned)

**Conforms to OKF v0.1, criteria copied 2026-06.**

This document is **normative within MIF**. It embeds a pinned copy of Google's
Open Knowledge Format (OKF) v0.1 conformance criteria. MIF conforms to *this
pinned copy*, not to whatever OKF publishes next. Updates to OKF are reviewed
deliberately and adopted only by an explicit MIF revision (see SPECIFICATION.md,
Invariant 5 — "No floating dependency on OKF").

> **Provenance note.** The criteria below are reconstructed from the OKF v0.1
> interoperability surface (a directory of markdown files with YAML frontmatter,
> a single required `type` field, a concept graph built from standard markdown
> links, and the reserved filenames `index.md` and `log.md`). Where the upstream
> wording is unavailable, the criteria are stated in MIF's words and frozen here.
> A future MIF revision MAY replace this section verbatim with upstream text;
> until then, **this pinned text is authoritative for MIF conformance.**

---

## 1. Pinned OKF v0.1 criteria

A bundle conforms to OKF v0.1 when:

1. **Bundle shape.** The bundle is a directory tree of `.md` files. Each `.md`
   file (except reserved filenames) is a *concept*.
2. **Required frontmatter field.** Every concept file begins with YAML
   frontmatter containing at least a `type` field. All other fields are optional
   and pass through untouched.
3. **Reserved filenames.** `index.md` (progressive disclosure) and `log.md`
   (chronological bundle history) are reserved at every directory level and MUST
   NOT be used as concept documents.
4. **Concept identity.** A concept's OKF identity is its bundle-relative path
   minus the `.md` extension.
5. **Concept graph.** Relationships between concepts are expressed as standard
   bundle-relative markdown links, `[text](/path/to/target.md)`, so a generic
   OKF consumer sees every edge.
6. **Broken links are tolerated.** A link whose target does not resolve is a
   warning, never a conformance failure. Missing `index.md` is likewise allowed.

OKF **deliberately refuses to define a content model**: typed relationships,
contradiction/merge semantics, trust tiers, provenance, and stale-vs-live
handling are left as open design space. MIF fills that envelope (see
SPECIFICATION.md §6).

---

## 2. MIF → OKF mapping

| MIF construct | OKF construct |
| --- | --- |
| Concept file (`.md`) | OKF concept |
| Bundle-relative path minus `.md` | OKF concept ID |
| Frontmatter `type` (`semantic` / `episodic` / `procedural`) | OKF required `type` |
| `id` (UUID) | MIF-only stable identity; invisible to OKF |
| Frontmatter `relationships[]` (typed) | MIF overlay on OKF edges |
| Body `## Relationships` markdown links | OKF concept-graph edges |
| `index.md` / `log.md` | OKF reserved filenames (verbatim) |
| JSON-LD projection (`*.jsonld`, never `*.md`) | derived; outside the OKF `*.md` glob |

A MIF bundle is a **superset** of a conformant OKF bundle: every MIF concept is
a valid OKF concept, and every typed MIF relationship also appears as a plain
OKF-legible markdown link.

---

## 3. The conformance test

The validator `scripts/okf_validate.py` enforces, for every concept in every
bundle:

1. **Type present.** The concept has YAML frontmatter containing `type`.
2. **No reserved-filename concepts.** No concept document is named `index.md` or
   `log.md`.
3. **Relationship synchronization.** Every frontmatter `relationships` entry has
   a corresponding body markdown link in a `## Relationships` section, and every
   such body link maps back to a frontmatter entry (SPECIFICATION.md §4.4).
4. **Broken links tolerated.** Unresolvable bundle-relative `.md` links are
   reported as warnings, not failures.
5. **Lossless projection.** The `markdown → json-ld → markdown` round trip is
   lossless for all conformance-level data (`scripts/mif_convert.py roundtrip`).

Run it with:

```bash
python scripts/okf_validate.py            # examples/ + profiles/*/examples/
python scripts/okf_validate.py <bundle>   # a specific bundle
python scripts/mif_convert.py roundtrip <bundle> [<bundle> ...]
```

Exit code `0` means every concept conforms.
