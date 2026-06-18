---
diataxis_type: tutorial
diataxis_learning_goals:
  - Create a valid MIF v1.0 / OKF concept bundle from scratch
  - Add a typed relationship as an OKF-legible body markdown link
  - Validate the bundle and emit its derived JSON-LD projection
---

# Tutorial: Build Your First MIF Bundle

In this tutorial we will build a tiny MIF v1.0 bundle — a directory of `.md`
concept files that is also a valid OKF bundle — and validate it with the
project's own tools. By the end you will have a two-concept bundle that passes
OKF conformance and round-trips losslessly to JSON-LD.

## What you'll learn

- How a MIF concept file is structured (frontmatter `type`/`id`/`created` + body)
- How to express a typed relationship that an OKF consumer can see
- How to validate a bundle and regenerate its JSON-LD projection

## Prerequisites

- Python 3.12+ with `pyyaml` installed (`pip install pyyaml`)
- A clone of this repository (the scripts live in `scripts/`)

## Step 1: Create the bundle directory

We will keep everything under `my-bundle/`.

```bash
mkdir -p my-bundle/semantic my-bundle/procedural
```

## Step 2: Write your first concept

Create `my-bundle/semantic/welcome.md`. The frontmatter needs three required
fields — `id` (a UUID), `type` (one of `semantic`, `episodic`, `procedural`),
and `created` (ISO 8601):

```markdown
---
id: 11111111-1111-4111-8111-111111111111
type: semantic
created: 2026-06-18T09:00:00Z
title: Welcome Concept
relationships:
  - type: relates-to
    target: /procedural/say-hello.md
---

# Welcome Concept

This is declarative knowledge: a fact stated in plain markdown.

## Relationships

- relates-to [Say Hello](/procedural/say-hello.md)
```

Notice that the relationship appears **twice**: once in the frontmatter
`relationships` array (authoritative) and once in the body `## Relationships`
section as a standard markdown link (so an OKF consumer sees the edge). They
must stay in sync — the validator checks this.

## Step 3: Write the target concept

Create `my-bundle/procedural/say-hello.md`:

```markdown
---
id: 22222222-2222-4222-8222-222222222222
type: procedural
created: 2026-06-18T09:05:00Z
title: Say Hello
---

# Say Hello

How-to knowledge:

1. Open a terminal.
2. Run `echo "hello"`.
```

## Step 4: Validate the bundle

Run the OKF conformance validator against your bundle:

```bash
python scripts/okf_validate.py my-bundle
```

You should see output ending in:

```
OKF conformance: checked 2 concept(s) in 1 bundle(s)
OKF conformance: PASS (all concepts conform)
```

If you mistyped the body link so it no longer matches the frontmatter, the
validator will report `relationships out of sync` — fix the link and re-run.

## Step 5: Confirm the lossless round-trip

Markdown is canonical; JSON-LD is derived. Confirm the two are equivalent:

```bash
python scripts/mif_convert.py roundtrip my-bundle
```

Expected:

```
Round-trip lossless: PASS
```

## Step 6: Emit the derived JSON-LD projection

```bash
python scripts/mif_convert.py emit-jsonld my-bundle --out-dir my-bundle-jsonld
```

Open `my-bundle-jsonld/my-bundle/semantic/welcome.jsonld` — that's the
machine-processable projection of your canonical markdown. You never edit it by
hand; you regenerate it.

## What you've accomplished

You built a valid MIF v1.0 / OKF bundle with two concepts and a typed
relationship, validated its conformance, confirmed the lossless markdown↔JSON-LD
round trip, and generated the derived projection.

## Next steps

- Read the [Migration guide](../MIGRATION.md) if you have a 0.1.0-draft bundle.
- See [OKF conformance](okf-conformance.md) for the pinned criteria.
- Explore the [AI Memory profile](../profiles/ai-memory/SPECIFICATION.md) for a
  domain profile built on this core.
