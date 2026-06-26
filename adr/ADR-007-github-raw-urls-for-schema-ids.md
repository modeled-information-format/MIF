# ADR-007: GitHub Raw URLs for Schema IDs

## Status

Amended

## Date

2026-01-27

## Context

JSON Schema requires `$id` values to be URIs. Options considered:

1. **Custom domain** (e.g., `https://mif.io/schema/...`)
   - Requires domain registration and hosting
   - Single point of failure
   - Ongoing maintenance cost

2. **JSON-LD standard namespaces** (e.g., `http://schema.org/...`)
   - Not appropriate for custom schemas
   - Would require schema.org integration

3. **URN namespace** (e.g., `urn:mif:schema:...`)
   - Not resolvable
   - Requires separate resolution mechanism

4. **GitHub raw URLs** (e.g., `https://raw.githubusercontent.com/...`)
   - Automatically resolvable
   - Zero hosting cost
   - Version control via branches/tags
   - Community-accessible

## Decision

Use **GitHub raw content URLs** for all schema `$id` values:

```
https://raw.githubusercontent.com/zircote/MIF/main/schema/mif.schema.json
https://raw.githubusercontent.com/zircote/MIF/main/schema/ontology/ontology.schema.json
https://raw.githubusercontent.com/zircote/MIF/main/schema/context.jsonld
```

## Consequences

### Positive
- Immediately resolvable by any HTTP client
- No infrastructure to maintain
- Free, reliable GitHub CDN
- Natural versioning via git refs (`main`, `v0.1.0`, etc.)
- Open source transparency
- Community can fork and modify

### Negative
- Dependency on GitHub availability
- URLs are verbose
- Repository rename would break URLs (mitigated by stability commitment)
- Rate limits for heavy consumers (mitigated by caching)

## Implementation Notes

- Use `main` branch for latest stable schemas
- Use tags (e.g., `v0.1.0`) for version-specific URLs
- JSON-LD `@context` references same URL pattern
- Schema `$ref` uses relative paths within repository

## Related Decisions

- [ADR-002](ADR-002-dual-format-design.md) - JSON-LD format requires resolvable schema $id URIs

## Migration History

Originally used placeholder domains:
- ~~`mif.io`~~ → Never existed (hallucinated)
- ~~`subcog.io`~~ → Never existed (hallucinated)
- ~~`subcog.dev`~~ → Never existed (hallucinated)

All replaced with GitHub raw URLs in v0.1.0.

## Amendment (2026-02)

The original decision to use GitHub raw URLs was superseded by migration to a custom domain `mif-spec.dev`. Schema `$id` values now use `https://mif-spec.dev/schema/...`. At the time of this amendment the JSON-LD namespace prefix (`ns/`) was left on `https://raw.githubusercontent.com/zircote/MIF/main/ns/` (subsequently migrated to `https://mif-spec.dev/ns/`; see the 2026-06 amendment below).

**Rationale for amendment:** A custom domain provides URL stability independent of repository location, enables proper HTTP content negotiation, and presents a more professional identity. The zero-infrastructure benefit is preserved via GitHub Pages hosting.

## Amendment (2026-06)

The repository was transferred from the personal account to the
`modeled-information-format` GitHub organization. The JSON-LD namespace prefix
(`ns/`), previously served from `https://raw.githubusercontent.com/zircote/MIF/main/ns/`,
is migrated to `https://mif-spec.dev/ns/`, completing the move of all canonical
spec and schema identifiers onto the `mif-spec.dev` custom domain.

**Rationale for amendment:** Removes the dependency on a personal-account raw
path, aligns the namespace IRI with the schema `$id` scheme already on
`mif-spec.dev`, and keeps every normative identifier on a single
location-independent domain.
