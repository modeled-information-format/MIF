# Contributing to MIF

Thank you for your interest in contributing to the Modeled Information Format specification.

## Ways to Contribute

### 1. Open an Issue for Discussion

Before making changes to the specification, please open an issue to discuss:
- Proposed new features or fields
- Clarifications to existing sections
- Use cases that aren't well supported
- Compatibility concerns

### 2. Submit PRs for Specification Changes

For specification changes:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/add-xyz-field`)
3. Make your changes to `SPECIFICATION.md`
4. Update examples if needed
5. Update `CHANGELOG.md` under `[Unreleased]`
6. Submit a pull request

### 3. Implement and Share Converters

Help grow the ecosystem by building:
- Import/export converters for memory providers
- Validation tools
- Editor plugins (Obsidian, VS Code, etc.)

### 4. Validate with JSON Schema

Use the provided schemas to validate your implementations:

```bash
# Validate MIF documents
npx ajv validate -s schema/mif.schema.json -d your-memory.json

# Validate citations
npx ajv validate -s schema/citation.schema.json -d citation.json
```

## Specification Change Guidelines

### Backward Compatibility

- Additive changes (new optional fields) are preferred
- Breaking changes require major version bump
- Use conformance levels to add features progressively

### Documentation Requirements

All specification changes must include:
- Clear description of the change
- Rationale for the addition
- Example in both Markdown and JSON-LD formats
- Impact on conformance levels (if any)

### Code Examples

When adding examples:
- Use language tags on all code blocks
- Ensure JSON is valid and parseable
- Ensure YAML frontmatter is valid
- Test wiki-link syntax in Obsidian if possible

## Style Guide

### Specification Language

- Use RFC 2119 keywords (MUST, SHOULD, MAY) appropriately
- Be precise and unambiguous
- Include rationale for design decisions

### Markdown Formatting

- Use ATX-style headers (`#`, `##`, etc.)
- Use fenced code blocks with language tags
- Use tables for structured comparisons
- Keep lines under 120 characters when possible

## Questions?

Open an issue with the `question` label or reach out to the maintainers.
