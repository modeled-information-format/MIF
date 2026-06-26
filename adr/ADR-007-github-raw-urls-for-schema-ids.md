---
title: "GitHub Raw URLs for Schema IDs (Amended to mif-spec.dev)"
description: "MIF's JSON Schema $id values use resolvable HTTP URIs; originally GitHub raw content URLs, amended in 2026-02 to the custom domain mif-spec.dev for schema $id values, with the JSON-LD namespace IRI migrated onto mif-spec.dev in 2026-06."
type: adr
category: api
tags:
  - schema
  - json-schema
  - identifiers
  - hosting
  - amendment
status: accepted
created: 2026-01-27
updated: 2026-06-18
author: MIF Maintainers
project: MIF
technologies:
  - json-schema
  - json-ld
  - github-pages
audience:
  - developers
  - architects
related:
  - ADR-002-dual-format-design.md
  - ADR-011-markdown-canonical-derived-jsonld.md
---

# ADR-007: GitHub Raw URLs for Schema IDs (Amended to mif-spec.dev)

## Status

Accepted (amended 2026-02 and 2026-06 — see Amendment section)

## Context

### Background and Problem Statement

JSON Schema requires every schema's `$id` to be a URI, and MIF's dual-format
design (ADR-002) emits a JSON-LD projection whose `@context` and `$id`
references must resolve for tooling that follows them. MIF therefore needs a
stable, dereferenceable identifier scheme for its schema family
(`schema/mif.schema.json`, `schema/citation.schema.json`,
`schema/ontology/ontology.schema.json`,
`schema/definitions/entity-reference.schema.json`) and for the JSON-LD
namespace IRI that the vocabulary terms hang off of.

The architectural question is *which URI scheme* to adopt. The choice trades
off resolvability, hosting cost, identifier stability across repository moves,
and the professional identity the project presents to consumers. A schema `$id`
is effectively forever — once published bundles reference it, changing it is a
breaking change — so the decision needed to be deliberate rather than incidental.

### Current Limitations

- A non-resolvable identifier scheme (URN, opaque string) forces every consumer
  to ship a separate resolution mechanism; MIF wants `$id` values that a plain
  HTTP client can dereference.
- Borrowing a third-party vocabulary namespace (e.g. `schema.org`) is wrong for
  MIF-specific schemas — those terms are not MIF's to define.
- Tying identifiers to a single hosting location makes them fragile: a
  repository rename or org move silently breaks every published `$id`.
- The project's earliest drafts recorded placeholder domains
  (`mif.io`, `subcog.io`, `subcog.dev`) that never existed — hallucinated
  identifiers that had to be purged before any identifier scheme could be
  trusted.

## Decision Drivers

### Primary Decision Drivers

1. **Resolvability**: `$id` and `@context` URIs must dereference over plain HTTP
   with no special tooling.
2. **Zero/low infrastructure**: The scheme should not require standing up and
   maintaining bespoke hosting.
3. **Identifier stability**: Identifiers should survive repository renames and
   hosting changes without breaking published bundles.

### Secondary Decision Drivers

1. **Professional identity**: The identifier presented to consumers should read
   as a deliberate project namespace, not an implementation detail.
2. **Content negotiation**: The ability to serve schema vs. human-readable
   representations from the same URI is desirable for a spec project.
3. **Versioning**: Identifiers should compose cleanly with version refs.

## Considered Options

### Option 1: URN namespace (e.g. `urn:mif:schema:...`)

**Description**: Use opaque URN identifiers for `$id`.

**Technical Characteristics**:
- Stable and location-independent by construction.
- Not dereferenceable without a separate resolver.

**Advantages**:
- Maximum stability; no hosting coupling at all.

**Disadvantages**:
- Not resolvable; every consumer must supply a resolution layer.
- Defeats the JSON-LD goal of `@context`/`$id` URIs that tools can follow.

**Risk Assessment**:
- **Technical Risk**: Medium. Pushes resolution complexity onto consumers.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: High. A non-resolvable scheme is hostile to generic
  JSON Schema / JSON-LD tooling.

### Option 2: Third-party standard namespaces (e.g. `http://schema.org/...`)

**Description**: Reuse an existing vocabulary's namespace for MIF schemas.

**Advantages**:
- No hosting to manage.

**Disadvantages**:
- Inappropriate for custom MIF schemas — those terms are not defined by the
  third party.
- Would require integration with / dependency on an external vocabulary owner.

**Risk Assessment**:
- **Technical Risk**: Medium.
- **Ecosystem Risk**: High. Semantically wrong; misrepresents ownership of terms.

### Option 3: GitHub raw content URLs (original decision)

**Description**: Use `https://raw.githubusercontent.com/zircote/MIF/main/...`
for all schema `$id` values and the JSON-LD namespace IRI.

**Technical Characteristics**:
- Immediately resolvable by any HTTP client via GitHub's CDN.
- Versionable through git refs (`main`, `v0.1.0`, …).
- `$ref` uses relative paths within the repository.

**Advantages**:
- Zero hosting cost; nothing to operate.
- Free, reliable CDN; open-source transparency; forkable by the community.
- Natural versioning via branches and tags.

**Disadvantages**:
- Couples identifiers to GitHub availability and to the `zircote/MIF` repo path.
- A repository rename breaks every URL (mitigated only by a stability pledge).
- Verbose URLs; no content negotiation.

**Risk Assessment**:
- **Technical Risk**: Low to adopt.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: Medium. Identifier longevity is hostage to a hosting path
  the project does not fully control.

### Option 4: Custom domain with GitHub Pages hosting — `mif-spec.dev` (chosen)

**Description**: Use a dedicated `mif-spec.dev` domain for all schema `$id`
values, served via GitHub Pages so no bespoke infrastructure is required. As
originally adopted (2026-02), the JSON-LD namespace IRI deliberately remained on
GitHub raw (`https://raw.githubusercontent.com/zircote/MIF/main/ns/`) as a stable
term identifier; the 2026-06 amendment subsequently migrated it to
`https://mif-spec.dev/ns/` as well, so every canonical identifier now lives on
the custom domain (see the Amendment section).

**Technical Characteristics**:
- Schema `$id` values read `https://mif-spec.dev/schema/...`.
- Hosting is GitHub Pages, so the zero-infrastructure property of Option 3 is
  preserved.
- The custom domain decouples identifier stability from the repository's
  location.

**Advantages**:
- Identifier stability independent of repository path or org.
- Enables proper HTTP content negotiation.
- Presents a deliberate, professional project identity.
- Retains zero-infrastructure operation through GitHub Pages.

**Disadvantages**:
- Requires owning and renewing a domain.
- Initially introduced a split — schema `$id` on `mif-spec.dev`, namespace IRI on
  GitHub raw — i.e. two identifier authorities to understand. The 2026-06
  amendment removed the split by migrating the namespace IRI onto `mif-spec.dev`.

**Risk Assessment**:
- **Technical Risk**: Low. Pages hosting is the same delivery path, behind a
  stable domain.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: Low. The domain is the long-lived contract; hosting can
  move beneath it.

## Decision

MIF uses resolvable HTTP URIs for all schema `$id` values. The **current**
scheme (post-amendment) is the custom domain `mif-spec.dev`, served via GitHub
Pages:

```
https://mif-spec.dev/schema/mif.schema.json
https://mif-spec.dev/schema/citation.schema.json
https://mif-spec.dev/schema/ontology/ontology.schema.json
https://mif-spec.dev/schema/definitions/entity-reference.schema.json
```

The JSON-LD namespace IRI — the base the vocabulary terms resolve against — now
also resolves on the `mif-spec.dev` domain (see the 2026-06 amendment):

```
https://mif-spec.dev/ns/
```

Both the schema `$id` URLs and the namespace IRI are served from `mif-spec.dev`
via GitHub Pages, keeping every normative identifier on a single,
location-independent domain. The namespace IRI is a stable term identifier whose
exact string is baked into every published JSON-LD `@context`. Schema `$ref`
values continue to use relative paths within the repository.

## Consequences

### Positive

1. **Resolvable identifiers**: Every `$id` dereferences over plain HTTP.
2. **Stable contract**: The `mif-spec.dev` domain survives repository renames
   and org moves that would have broken raw-GitHub `$id` URLs.
3. **Zero infrastructure retained**: GitHub Pages hosting keeps operational cost
   at zero while adding a stable front door.
4. **Content negotiation enabled**: A custom domain can serve schema vs.
   human-readable representations from one URI.
5. **No hallucinated identifiers**: The purged placeholder domains
   (`mif.io`, `subcog.io`, `subcog.dev`) are gone; nothing references a domain
   that never existed.

### Negative

1. **Domain ownership cost**: `mif-spec.dev` must be registered and renewed.
2. **Two identifier authorities**: Contributors must understand why schema `$id`
   lives on `mif-spec.dev` while the namespace IRI lives on GitHub raw.

### Neutral

1. **Split is by design, not drift**: The schema-vs-namespace URI divergence is
   an intentional architectural choice documented in `ns/README.md`, not an
   inconsistency to be "fixed."

## Decision Outcome

The custom-domain approach achieves the primary drivers: resolvability (HTTP
dereferenceable), low infrastructure (GitHub Pages), and identifier stability
(domain outlives hosting path). Mitigations:

- The intentional schema-`$id` vs. namespace-IRI split is documented inline in
  `ns/README.md` so it reads as a decision rather than a bug.
- The amendment preserved the zero-infrastructure benefit of the original
  GitHub-raw decision by keeping delivery on GitHub Pages.

## Related Decisions

- [ADR-002: Dual-Format Design](ADR-002-dual-format-design.md) — the JSON-LD projection requires resolvable schema `$id` / `@context` URIs, which is the constraint this ADR satisfies.
- [ADR-011: Markdown-Canonical with Derived JSON-LD](ADR-011-markdown-canonical-derived-jsonld.md) — the derived JSON-LD projection that carries the namespace IRI established here.

## Links

- [JSON Schema `$id` and identifiers](https://json-schema.org/understanding-json-schema/structuring) — why `$id` must be a URI.
- [GitHub Pages](https://pages.github.com/) — the zero-infrastructure hosting path used to serve `mif-spec.dev`.

## More Information

- **Date:** 2026-01-27 (original); amended 2026-02
- **Source:** `schema/mif.schema.json` and sibling schema `$id` values; `schema/context.jsonld`; `ns/README.md`.
- **Related ADRs:** ADR-002, ADR-011

## Amendment

### 2026-02 — GitHub raw URLs → `mif-spec.dev`

The original decision (2026-01-27) used GitHub raw content URLs
(`https://raw.githubusercontent.com/zircote/MIF/main/schema/...`) for all schema
`$id` values. In 2026-02 this was superseded by migration to the custom domain
`mif-spec.dev`. Schema `$id` values now use `https://mif-spec.dev/schema/...`.

The JSON-LD namespace prefix (`ns/`) was **not** migrated at that time: it was
left on `https://raw.githubusercontent.com/zircote/MIF/main/ns/` as the canonical
namespace IRI (subsequently migrated to `https://mif-spec.dev/ns/`; see the
2026-06 amendment below).

**Rationale for amendment:** A custom domain provides URL stability independent
of repository location, enables proper HTTP content negotiation, and presents a
more professional identity. The zero-infrastructure benefit of the original
decision is preserved by hosting `mif-spec.dev` on GitHub Pages. The namespace
IRI was deliberately left on GitHub raw because it is a stable term identifier
embedded in every published JSON-LD `@context`; changing it would be a breaking
change to the vocabulary, whereas schema-document URLs are safer to relocate.

**Earlier placeholder-domain history (preserved):** The project's earliest
drafts recorded placeholder domains that never existed and were hallucinated:
`mif.io`, `subcog.io`, and `subcog.dev`. All three were purged — first replaced
by GitHub raw URLs in v0.1.0, then (for schema `$id`) by `mif-spec.dev` in the
2026-02 amendment. No published MIF artifact references any of these domains.

### 2026-06 — namespace IRI → `mif-spec.dev`

The repository was transferred from the personal account to the
`modeled-information-format` GitHub organization. The JSON-LD namespace prefix
(`ns/`), which the 2026-02 amendment had deliberately left on
`https://raw.githubusercontent.com/zircote/MIF/main/ns/`, is migrated to
`https://mif-spec.dev/ns/`. This completes the move of every canonical spec and
schema identifier onto the `mif-spec.dev` custom domain and removes the
schema-`$id`-vs-namespace-IRI split introduced in 2026-02.

**Rationale for amendment:** The org transfer made the personal raw path a
liability rather than a stable anchor. Co-locating the namespace IRI with the
schema `$id` scheme on `mif-spec.dev` removes the personal-account dependency and
keeps all normative identifiers on a single location-independent domain. The
one-time `@context` rewrite is the same class of change the 2026-02 amendment
deferred; it is taken now alongside the org transfer.

## Audit

### 2026-06-18

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Primary schema `$id` uses the amended `mif-spec.dev` domain | `schema/mif.schema.json` | L3 | compliant |
| Sibling schema `$id` values also use `mif-spec.dev` (citation, ontology, entity-reference) | `schema/citation.schema.json`, `schema/ontology/ontology.schema.json`, `schema/definitions/entity-reference.schema.json` | L3 (each) | compliant |
| JSON-LD `@context` namespace prefix `mif` stays on GitHub raw `ns/` IRI | `schema/context.jsonld` | L4 | compliant |
| The schema-`$id`-vs-namespace-IRI split is documented as intentional | `ns/README.md` | L7, L11-L14 | compliant |

**Summary:** The current (amended) state is verified: all four schema `$id`
values resolve to `https://mif-spec.dev/schema/...`, while the JSON-LD namespace
IRI deliberately remains `https://raw.githubusercontent.com/zircote/MIF/main/ns/`
in `schema/context.jsonld`, and `ns/README.md` documents this split as
intentional. The placeholder domains (`mif.io`, `subcog.io`, `subcog.dev`) do
not appear in any audited artifact.

**Action Required:** None.
