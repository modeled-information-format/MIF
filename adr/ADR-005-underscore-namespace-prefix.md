---
title: "Underscore Namespace Prefix Convention"
description: "MIF prefixes the three base-type namespaces (_semantic/, _episodic/, _procedural/) with an underscore to distinguish system namespaces from domain content, while leaving domain sub-namespaces unprefixed."
type: adr
category: architecture
tags:
  - namespace
  - convention
  - filesystem
status: accepted
created: 2026-01-27
updated: 2026-07-11
author: MIF Maintainers
project: MIF
technologies:
  - markdown
audience:
  - developers
  - architects
related:
  - ADR-001-cognitive-triad-taxonomy.md
  - ADR-003-obsidian-compatibility.md
  - ADR-018-ontology-corpus-dedicated-repository-and-serving.md
---

# ADR-005: Underscore Namespace Prefix Convention

## Status

Accepted

## Context

### Background and Problem Statement

MIF organizes memory on the filesystem under three base types — semantic,
episodic, and procedural (the cognitive triad established in ADR-001). These
three categories form the top-level namespace directories under which all domain
content is filed. Because they are structural, system-level partitions rather
than user content, they have requirements that ordinary domain namespaces do
not. The base-type directories need to:

- Be visually distinguishable from domain namespaces, so a reader scanning a
  bundle can tell the structural partitions from the user's subject matter.
- Sort predictably in file listings, ideally grouping together at a stable
  position.
- Signal "system" organization versus "user" content.
- Work cleanly with existing tooling and every common file browser or IDE —
  the underscore prefix is an ordinary visible character in all of them,
  including but not limited to Obsidian (ADR-017).

The architectural question is what naming convention, if any, marks these three
directories so they read as system-level partitions across every filesystem and
tool that touches a MIF bundle.

### Current Limitations

- With no naming convention, the base-type directories are indistinguishable
  from domain directories. A `semantic/` folder sits alphabetically among
  arbitrary domain folders with no signal that it is structural.
- A convention borrowed from elsewhere (for example, a dot prefix) can be hidden
  by default in file browsers or behave inconsistently across platforms,
  defeating the goal of a visible, predictable partition.
- The convention must be applied to base types **only**. Domain sub-namespaces
  (`_semantic/land/`, `_procedural/animal-welfare/`) are user content and must
  not inherit the prefix, or the distinction it is meant to carry collapses.

## Decision Drivers

### Primary Decision Drivers

1. **Visual distinction**: The three base-type directories must be immediately
   distinguishable from domain content in any listing.
2. **Predictable sorting**: Base-type directories should sort to a stable,
   predictable position so bundle layout is consistent across tools.
3. **Cross-platform visibility**: The convention must render the directories
   visible — not hidden — in every common file browser, IDE, and the Obsidian
   vault model.

### Secondary Decision Drivers

1. **Familiarity**: A convention already understood by developers (the kind used
   for `_templates/`, `_includes/`) lowers the cost of adoption and reads as
   intentional.
2. **Scope discipline**: The convention must be unambiguous about where it
   applies (base types) and where it does not (domain sub-namespaces).

## Considered Options

### Option 1: No prefix (`semantic/`, `episodic/`, `procedural/`)

**Description**: Name the base-type directories with their bare type names and
rely on position or documentation to mark them as structural.

**Technical Characteristics**:
- Plain directory names, no marker character.
- Base types are lexically indistinguishable from domain directories.

**Advantages**:
- Shortest possible paths.
- No special character to explain or enforce.

**Disadvantages**:
- Mixes with domain content; a reader cannot tell `semantic/` (structural) from
  any domain folder at a glance.
- No visual distinction and no predictable grouping in listings.

**Risk Assessment**:
- **Technical Risk**: Low to implement, but it fails the visual-distinction and
  predictable-sorting drivers outright.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: Medium. Consumers and tooling have no stable signal for
  which directories are MIF's structural partitions.

### Option 2: Dot prefix (`.semantic/`, `.episodic/`, `.procedural/`)

**Description**: Mark the base-type directories with a leading dot, borrowing the
Unix "dotfile" convention for special directories.

**Technical Characteristics**:
- Leading dot triggers hidden-file handling on Unix-like systems.
- Behavior varies by file browser and platform.

**Advantages**:
- Strong, widely-recognized signal of a "special" directory.

**Disadvantages**:
- Hidden by default in most file browsers, so the partitions disappear from view
  — the opposite of the visibility driver.
- Inconsistent cross-platform behavior; some tools and the Obsidian vault model
  treat dotted directories unpredictably.

**Risk Assessment**:
- **Technical Risk**: Medium. Hidden-by-default behavior actively undermines the
  intent.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: Medium to High. Cross-platform inconsistency and hidden
  directories break the "visible in every tool" requirement.

### Option 3: Underscore prefix (`_semantic/`, `_episodic/`, `_procedural/`) (chosen)

**Description**: Mark the three base-type directories with a leading underscore.
Domain sub-namespaces underneath them remain unprefixed.

**Technical Characteristics**:
- The underscore is an ordinary, visible filename character on every platform.
- Sorts ahead of most alphabetic content, grouping the base types together near
  the top of a listing.
- Applied to base types only; `_semantic/land/`, not `_semantic/_land/`.

**Advantages**:
- Clear visual distinction from domain content in every listing.
- Always visible in file browsers, IDEs, and Obsidian vaults — no hidden-file
  behavior.
- Sorts predictably to the top, giving a consistent bundle layout.
- A familiar convention for "special" directories (`_templates/`, `_includes/`),
  so it reads as deliberate.

**Disadvantages**:
- Requires consistent enforcement so the prefix is applied to base types and not
  to domain sub-namespaces.
- One extra character in every base-type path.
- Could collide with another underscore convention in a host environment.

**Risk Assessment**:
- **Technical Risk**: Low. The underscore is an ordinary visible character
  everywhere.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: Low. Visible, predictable, and cross-platform consistent.

## Decision

Use an **underscore prefix** for the three base-type namespaces:

- `_semantic/` — facts, concepts, knowledge
- `_episodic/` — events, experiences, incidents
- `_procedural/` — processes, workflows, how-to

Domain-specific sub-namespaces remain **unprefixed**. The underscore marks the
structural base type only; everything filed beneath it is user content:

- `_semantic/land/` (not `_semantic/_land/`)
- `_procedural/animal-welfare/`

This convention is applied uniformly across MIF tooling and the mnemonic memory
system implementation, and the underscore prefix is an ordinary visible
character in every file browser/editor, including but not limited to
Obsidian, per ADR-017.

## Consequences

### Positive

1. **Clear visual distinction**: The three base-type directories are immediately
   set apart from domain content in any listing.
2. **Predictable sorting**: The prefix sorts the base types to a stable position
   at the top of directory listings.
3. **Universal visibility**: The directories are visible in every file browser,
   IDE, and Obsidian vault — never hidden.
4. **Familiar signal**: The underscore reads as an intentional "system-level"
   marker, matching established conventions like `_templates/`.

### Negative

1. **Enforcement burden**: The prefix must be applied consistently to base types
   and withheld from domain sub-namespaces.
2. **Path length**: One extra character on every base-type path.
3. **Potential collision**: May overlap with another underscore convention in a
   host environment.

### Neutral

1. **Two naming tiers**: Base-type directories carry the prefix; domain
   sub-namespaces do not — by design, this asymmetry is what carries the
   distinction.

## Decision Outcome

The underscore-prefix convention achieves the primary drivers: visual
distinction (the prefix sets base types apart), predictable sorting (they group
at the top), and cross-platform visibility (the underscore is an ordinary
visible character, unlike the dot prefix). Mitigations for the enforcement
burden:

- The convention is applied uniformly across every shipped ontology example, so
  authors have a consistent pattern to copy.
- `scripts/validate-namespaces.py` resolves a memory's declared namespace
  against its ontology, treating the `_semantic` / `_episodic` / `_procedural`
  base types as the always-available parents from which domain sub-namespaces
  inherit — encoding the base-type-versus-domain distinction in tooling.

## Related Decisions

- [ADR-001: Cognitive Triad Taxonomy](ADR-001-cognitive-triad-taxonomy.md) — the prefix convention exists because the three base types it names are the cognitive-triad categories.
- [ADR-003: Obsidian Compatibility](ADR-003-obsidian-compatibility.md) — the underscore prefix stays visible and well-behaved inside Obsidian vaults, where a dot prefix would not.
- [ADR-018: Ontology Corpus: Dedicated Repository, Flat Layout, and Versioned Serving](ADR-018-ontology-corpus-dedicated-repository-and-serving.md) — the corpus layout this convention applies to now lives in the dedicated `ontologies` repo.

## Links

- [Jekyll directory structure](https://jekyllrb.com/docs/structure/) — established prior art for underscore-prefixed "special" directories (`_includes/`, `_layouts/`) that this convention mirrors.

## More Information

- **Date:** 2026-01-27
- **Source:** Ontology examples under `ontologies/examples/` (uniform `_semantic/` / `_episodic/` / `_procedural/` `suggest_namespace` values) and `scripts/validate-namespaces.py`.
- **Related ADRs:** ADR-001, ADR-003

## Audit

Findings cite durable anchors (field values / function name / comment
text), not raw line numbers, and — for ontology content — the external
`modeled-information-format/ontologies` repo (source of record since
ADR-018/ADR-019) rather than paths inside this repo. `grep -n` for the
quoted anchor text to find its current line.

### 2026-06-18

**Audited revision:** `7f8d2de6c671cf5f354e4034b1524c0c112ddf1f`

**Status:** Compliant

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| Underscore-prefixed `_semantic/...` base type used in domain ontology `suggest_namespace` values | `ontologies/examples/regenerative-agriculture.ontology.jsonld` (path as it existed in this repo at this date) | `discovery.patterns[]` entries with `"suggest_namespace": "_semantic/land"` | compliant |
| Underscore-prefixed `_episodic/...` base type used in domain ontology `suggest_namespace` values | `ontologies/examples/software-engineering.ontology.jsonld` (path as it existed in this repo at this date) | `discovery.patterns[]` entry with `"suggest_namespace": "_episodic/incidents"` | compliant |
| Underscore-prefixed `_procedural/...` base type used in domain ontology `suggest_namespace` values | `ontologies/examples/software-engineering.ontology.jsonld` (path as it existed in this repo at this date) | `discovery.patterns[]` entries with `"suggest_namespace": "_procedural/runbooks"` | compliant |
| Domain sub-namespaces stay unprefixed beneath the prefixed base type (`_semantic/land`, `_procedural/animal-welfare`) | `ontologies/examples/regenerative-agriculture.ontology.jsonld` (path as it existed in this repo at this date) | `discovery.patterns[]` entries `"suggest_namespace": "_semantic/land"` and `"suggest_namespace": "_procedural/animal-welfare"` | compliant |
| Namespace validator treats `_semantic`/`_episodic`/`_procedural` base types as always-available parents that domain sub-namespaces inherit from | `scripts/validate-namespaces.py` | function `validate_memory_namespace`, the `if parent in mif_base_namespaces:` block | compliant |

**Summary:** The underscore-prefix convention is applied uniformly across the
shipped ontology examples — base types carry the `_` prefix and domain
sub-namespaces beneath them do not — and `scripts/validate-namespaces.py`
encodes the same base-type-versus-domain distinction when resolving a memory's
declared namespace.

**Action Required:** None.

### 2026-07-11

**Audited revision:** `d2b0c577f59b30beadb12ffc45bf8e303b602377` (this repo);
`bfed8cc17e08da4091e9b6c483cf03a150983cff` (`modeled-information-format/ontologies`,
verified current against `origin/main` tip `99c984c78c5153f9ec697db8818e01adac42674f`
— the intervening commits touch only CI/dependency pins, not ontology content)

**Status:** Compliant

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| Underscore-prefixed `_semantic/...` base type used in domain ontology `suggest_namespace` values | `regenerative-agriculture.ontology.jsonld` (`modeled-information-format/ontologies` repo) | `discovery.patterns[]` entries with `"suggest_namespace": "_semantic/land"` | compliant |
| Underscore-prefixed `_episodic/...` base type used in domain ontology `suggest_namespace` values | `software-engineering.ontology.jsonld` (`ontologies` repo) | `discovery.patterns[]` entry `"suggest_namespace": "_episodic/incidents"` | compliant |
| Underscore-prefixed `_procedural/...` base type used in domain ontology `suggest_namespace` values | `software-engineering.ontology.jsonld` (`ontologies` repo) | `discovery.patterns[]` entries `"suggest_namespace": "_procedural/runbooks"` | compliant |
| Domain sub-namespaces stay unprefixed beneath the prefixed base type (`_semantic/land`, `_procedural/animal-welfare`) | `regenerative-agriculture.ontology.jsonld` (`ontologies` repo) | `discovery.patterns[]` entries `"suggest_namespace": "_semantic/land"` and `"suggest_namespace": "_procedural/animal-welfare"` | compliant |
| Namespace validator treats `_semantic`/`_episodic`/`_procedural` base types as always-available parents that domain sub-namespaces inherit from | `scripts/validate-namespaces.py` | function `validate_memory_namespace`, the `if parent in mif_base_namespaces:` block (comment `# Check parent namespace (e.g., _semantic from _semantic/preferences)`) | compliant — see Summary for a tooling-wiring change since 2026-06-18 |

**Summary:** Two material changes since 2026-06-18, neither breaking the
underlying convention:

1. **Ontology example content moved cross-repo.** `ontologies/examples/` no
   longer exists in this repo — per ADR-018/ADR-019, ontology corpus content
   is now sourced-of-record in `modeled-information-format/ontologies`.
   Re-verified the underscore-prefix claim directly against that repo. The
   convention is not just intact but more uniformly applied than the
   original 2-file sample showed: swept all `*.ontology.jsonld` files in
   that repo's current corpus and every `suggest_namespace` value across
   all of them is underscore-prefixed at the base-type level with domain
   sub-namespaces unprefixed beneath it, zero exceptions found. That repo
   has also since documented its own parallel decision record for the same
   convention (`docs/decisions/0001-underscore-prefixed-base-namespaces.md`,
   accepted 2026-06-30) — corroborating, not superseding, this ADR.
2. **`validate-namespaces.py` dropped from CI gating (logic unaffected).**
   The script's `validate_memory_namespace` logic is unchanged in intent and
   still correctly treats `_semantic`/`_episodic`/`_procedural` as
   always-available parent namespaces. Per ADR-019's own 2026-07-02 audit
   entry, this script was removed from `.github/workflows/validate.yml`'s
   required check that same day: it hardcoded a scan path that no longer
   exists in this repo. It is now a standalone script requiring an explicit
   `--path` pointed at a real ontology corpus. This ADR's Decision Outcome
   only ever claimed the script encodes the distinction in tooling — not
   that it is CI-gating — so this finding stays compliant; already tracked
   in ADR-019's own audit trail, no separate action needed here.

Two related-decision linkage issues were found during this audit and are
fixed in this same PR, not deferred: this ADR's `related:` frontmatter and
Related Decisions section were missing a backlink to ADR-018 (which lists
this ADR as related — "the corpus model the layout serves" — a one-way
link `adr/README.md` requires be bidirectional), added above. Separately,
this ADR's Context and Decision sections both cited ADR-003 as a live
Obsidian-compatibility guarantee, stale since ADR-017 superseded ADR-003 —
filed as [#251](https://github.com/modeled-information-format/MIF/issues/251)
(shared with the identical issue found on ADR-002) rather than fixed inline,
since correcting that prose is an editorial-scope decision.

**Action Required:** None for the findings above. See #251 for the
ADR-003/ADR-017 prose correction.

### 2026-07-11 (follow-up)

**Audited revision:** `252767a724a20771555942afc25a622c5b7ab1a9`

**Status:** Compliant

**Findings:**

| Finding | Files | Reference | Assessment |
|---------|-------|-----------|------------|
| Context's Obsidian-compatibility reference no longer cites ADR-003 as a live guarantee | `adr/ADR-005-underscore-namespace-prefix.md` | the bullet "Work cleanly with existing tooling and every common file browser or IDE..." in `## Context` | compliant |
| Decision's Obsidian-compatibility reference no longer cites ADR-003 as a live guarantee | `adr/ADR-005-underscore-namespace-prefix.md` | the sentence following "This convention is applied uniformly across MIF tooling..." in `## Decision` | compliant |

**Summary:** Both stale ADR-003 references identified in the prior audit
entry are fixed: each now states the underlying fact directly (the
underscore prefix is an ordinary visible character in every common file
browser/editor, Obsidian included) with a pointer to ADR-017, rather than
citing ADR-003 as a live compatibility commitment ADR-017 already
superseded. The underlying convention this ADR documents is unaffected.
Issue #251 closed for this ADR's portion of the work.

**Action Required:** None.
