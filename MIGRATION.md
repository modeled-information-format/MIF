<!-- diataxis_type: how-to -->

# Migration Guide: MIF 0.1.0-draft → 1.0.0

MIF v1.0.0 repositions MIF as an **OKF-compliant opinionated knowledge content
model**. AI memory is now the first *profile* of MIF, not its identity. This
guide is the how-to for upgrading an existing `0.1.0-draft` bundle. The
mechanical steps are automated by `scripts/migrate_0_1_to_1_0.py`.

## TL;DR

```bash
python scripts/migrate_0_1_to_1_0.py <old-bundle> <new-bundle>
python scripts/okf_validate.py <new-bundle>     # should print PASS
```

## What changed (and why)

| 0.1.0-draft | 1.0.0 | Why |
| --- | --- | --- |
| `*.memory.md` files | `*.md` files | OKF concept ID is the path minus `.md`; a `.memory` infix would leak into the ID. |
| Relationships as body wiki-links `[[slug]]` only | Authoritative frontmatter `relationships[]` **plus** body `## Relationships` markdown links `[Text](/path/target.md)` | OKF consumers must see every edge as a standard markdown link (Invariant 3). |
| `id` could be a slug | `id` MUST be a UUID | Stable, location-independent identity (§4.3). Slugs are preserved as `aliases`. |
| Memory-specific framing in the core spec | Moved to `profiles/ai-memory/` | The core is now a general knowledge model; memory is a profile (Invariant 6). |
| `*.memory.json` committed beside source | JSON-LD is a **derived** projection (regenerate with `mif_convert.py`) | Markdown is canonical (Invariant 2). |
| Temporal model framed as a "forgetting curve" | Same math, reframed as **validity windows & freshness** | Answers OKF's open "live vs stale" question; the forgetting-curve rationale lives in the AI Memory profile. |

## Steps the migration script performs

For every `*.memory.md` in the source bundle it:

1. Renames `*.memory.md` → `*.md`.
2. Ensures `id` is a UUID — a non-UUID slug is rehashed to a deterministic
   UUIDv5 and the original slug is kept as an `alias`.
3. Converts each `## Relationships` wiki-link (`- supersedes [[target-slug]]`)
   into an OKF-legible markdown link (`- supersedes [Target Slug](/target-slug.md)`)
   and synthesizes the authoritative frontmatter `relationships[]` array to
   match.
4. Normalizes timestamps to ISO 8601 (`...Z`).

It does **not** migrate `*.memory.json` files — regenerate the JSON-LD
projection from the canonical markdown instead:

```bash
python scripts/mif_convert.py emit-jsonld <new-bundle> --out-dir jsonld
```

## Manual follow-up

- **Relink targets.** Migrated relationship links point at `/target-slug.md`.
  Where the target concept exists in your bundle, adjust the link to its real
  bundle-relative path. Broken links are tolerated (warnings), so this can be
  done incrementally.
- **Relocate memory framing.** If your bundle's prose leaned on memory metaphors
  (forgetting curves, recall, sessions), move that narrative under your own
  profile and keep the core concepts general. See `profiles/ai-memory/` for the
  reference profile.
- **Regenerate examples / validate.** Run `python scripts/okf_validate.py` and
  the schema validation in CI (`.github/workflows/validate.yml`) before
  publishing.

## Coming from another memory system?

System-specific migration guides (Mem0, Zep, Letta, Subcog, Basic-Memory) now
live in the AI Memory profile: see
[`profiles/ai-memory/SPECIFICATION.md`](profiles/ai-memory/SPECIFICATION.md).
