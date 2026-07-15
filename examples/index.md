# Core Examples (progressive disclosure)

This bundle demonstrates the three MIF base knowledge types as plain OKF
concepts. `index.md` is an OKF reserved filename for progressive disclosure and
is not itself a concept document.

- `semantic/rate-limit-policy.md` — declarative knowledge
- `episodic/incident-2026-01-rate-spike.md` — a time-bound record
- `procedural/rotate-api-keys.md` — how-to knowledge

`container/` holds worked `*.corpus.json` Container Profile transport
envelopes (ADR-021). They are not concepts in this bundle's graph —
OKF's `*.md` glob never ingests them — and are validated separately by
`scripts/validate_container.py`.
