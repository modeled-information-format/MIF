---
title: "Confidence-Tiered Entity-Type Classification as a MIF Ontology Capability"
description: "Adopt a two-threshold, three-tier confidence-score policy (auto-classify-eligible / flag-for-review / trigger-expansion) as the MIF-level pattern for embedding-based entity-type classification, and extend the ontology schema's entity_type definition with three optional fields (aliases, exemplars, negative_examples) that make classification scores trustworthy."
type: adr
category: architecture
tags:
  - ontologies
  - schema
  - classification
  - embeddings
  - confidence
status: accepted
created: 2026-07-04
updated: 2026-07-06
author: MIF Maintainers
project: MIF
audience:
  - developers
  - architects
related:
  - ADR-018-ontology-corpus-dedicated-repository-and-serving.md
---

# ADR-020: Confidence-Tiered Entity-Type Classification as a MIF Ontology Capability

## Status

Accepted

## Context

### Background and Problem Statement

Any MIF-conformant tool that classifies content against a bound ontology's
`entity_type` set — deciding which typed entity a piece of content resembles,
and what confidence that decision deserves — faces two open questions the MIF
model did not answer: what a classification score should cause to happen, and
what an `entity_type` needs to carry for that score to be trustworthy in the
first place. Until this decision, `ontology.schema.json`'s `$defs.entityType`
carried exactly one free-text field usable as embedding input
(`description`), and no MIF-level vocabulary existed for expressing a
classification's confidence tier.

The question was forced by a concrete consumer: the research-harness
ontology engine (`mif-rh-cli`/`mif-rh-mcp` in the `mif-rs` workspace), whose
`suggest_type`/`find_similar` tools return raw embedding-similarity scores
with no defined meaning past "higher is more similar." A dedicated research
session (`ontology-semantic-classification-scoring`: 39 findings through an
adversarial falsification gate — 0 falsified, 4 weakened, 35 survived)
produced the evidence base and draft this ADR condenses. The capability is
adopted at the MIF level, not in that consumer, because every other
MIF-conformant classifier faces the identical questions; the engine is the
worked example, not the owner.

### Current Limitations

1. **No score-to-action policy existed**: nothing distinguished a
   confidently-typed candidate from a coin-flip guess for any consumer.
2. **`description` alone embeds poorly**: a single terse line gives an
   embedding model too little signal, and real-world taxonomies published as
   bare labels (for example the IAB Content Taxonomy) demonstrably force
   every downstream classifier to build its own labeled corpus per category.

## Decision Drivers

### Primary Decision Drivers

1. **Classification stays a hypothesis, never an auto-write.** WHEN a
   classifier returns a candidate entity type at any confidence tier, THE
   SYSTEM SHALL NOT write that candidate to a document's `entity_type`
   without a confirming agent or human action.
2. **No single global threshold generalizes.** Precedent is direct: DBpedia
   Spotlight's documented 0.5 default is retuned to 0.3-0.35 by independent
   studies; BERTMap requires two distinct thresholds for two distinct
   decisions. WHILE the policy is in force, THE SYSTEM SHALL treat threshold
   values as calibrated and recalibratable per embedding model and corpus,
   never as hardcoded constants.

### Secondary Decision Drivers

1. **Schema additions anchor to standards precedent** (W3C SKOS's
   `prefLabel`/`altLabel`/`example` separation) rather than inventing a
   bespoke shape.
2. **Expansion must not trigger from a single miss**: Home Depot's KDD'20
   production taxonomy-expansion pipeline saw human-approval precision decay
   from 32% to 13% across 50 iterations of single-miss-driven expansion.

## Considered Options

### Option 1: Single fixed global threshold

**Description**: One similarity cutoff applied uniformly; everything below
it is untyped.

**Advantages**:

- Trivial to implement and explain; no calibration pipeline.

**Disadvantages**:

- Directly contradicted by the cited precedent (Spotlight retuning, BERTMap's
  two thresholds).
- Cannot distinguish "ambiguous but known" from "genuinely novel," so it
  cannot support an expansion tier at all.

**Risk Assessment**:

- **Technical Risk**: High — contradicted by the gathered evidence across
  every cited matcher.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: Low.

### Option 2: Two-threshold, three-tier score-band policy plus entity-type enrichment fields (chosen)

**Description**: Two calibrated thresholds partition classification scores
into three action bands — auto-classify-eligible (score clears a calibrated
floor AND holds a clear margin over the second-best candidate, per TAC-KBP's
two-parameter entity-linking design), flag-for-review (mid band routes to a
human-reviewable queue), trigger-expansion (repeated, mutually-similar
low-band misses must cluster before proposing a new entity type). Paired
with three optional `entity_type` schema fields that make the scores
trustworthy: `aliases`, `exemplars`, `negative_examples`.

**Advantages**:

- Formalized by selective-prediction/reject-option theory (Chow's rule,
  SelectiveNet) and shipped precedent (TAC-KBP NIL thresholds; Palantir
  Foundry's lifecycle-gated, PR-style ontology review).
- Compatible with recalibration (conformal prediction is the upgrade path).
- The schema fields are additive and backward compatible: every field is
  optional, so existing ontologies carrying only `description` remain valid.

**Disadvantages**:

- Thresholds are meaningless without a calibration step each consumer must
  implement against its own corpus and embedding model.
- More authoring surface for ontology maintainers; existing ontologies read
  as thin against the new fields until enriched.

**Risk Assessment**:

- **Technical Risk**: Low — every sub-mechanism has cited precedent.
- **Schedule Risk**: Low for the schema; calibration cost falls on consumers.
- **Ecosystem Risk**: Low — purely additive schema change.

### Option 3: Fully autonomous, threshold-free ontology expansion

**Description**: Mint new entity types automatically whenever content fails
to match existing types well enough, with no human confirmation tier.

**Advantages**:

- Real research momentum (AutoSchemaKG's 92% semantic alignment at
  web scale) suggests eventual viability for bulk schema induction.

**Disadvantages**:

- Contradicts Primary Driver 1 outright — no confirming step at all.
- The cited systems are bulk/offline schema induction, not interactive
  per-document gating; enterprise-adoption evidence does not support full
  autonomy for governance-bearing classification.

**Risk Assessment**:

- **Technical Risk**: Medium — unproven for interactive per-document gating.
- **Schedule Risk**: Low.
- **Ecosystem Risk**: High — a governance-model change, not a scoped policy.

## Decision

Adopt **Option 2**. Concretely, in this repository:

1. `schema/ontology/ontology.schema.json` `$defs.entityType` gains three
   optional string-array fields (`uniqueItems`, non-empty items):
   - **`aliases`** — synonyms and label variations (SKOS `altLabel` analog).
   - **`exemplars`** — 2-5 curated canonical example phrases or instances
     (SKOS `example` analog; the count is authoring guidance, not schema
     law).
   - **`negative_examples`** — curated near-misses from the ontology's most
     confusable type pairs. Human-curated, never auto-mined.
2. `schema/ontology/ontology.context.jsonld` maps `aliases` to
   `skos:altLabel`, `exemplars` to `skos:example`, and `negative_examples`
   to `https://mif-spec.dev/ns/ontology#negativeExample` — SKOS defines no
   property asserting "this text does NOT denote the concept," and
   mislabeling counter-examples with a positive-assertion SKOS property
   (`scopeNote`, `hiddenLabel`) would mislead generic SKOS consumers.
3. **Embedding-document composition rule** (documented in
   `schema/ontology/README.md`): a classifier's positive embedding document
   concatenates `description` + `aliases` + `exemplars`; `negative_examples`
   is never concatenated into the positive document.
4. The **three-tier pattern** (auto-classify-eligible / flag-for-review /
   trigger-expansion, with a margin check on tier 1 and cluster-before-expand
   on tier 3) is the MIF-level vocabulary for score-to-action policy. How
   the review and expansion tiers are routed — which queue, which mining
   pipeline — is explicitly a consumer decision, recorded in each consumer's
   own decision log, not fixed here.
5. Ontology schema version: **1.0.0 → 1.1.0** (`VERSION.json`).

## Consequences

### Positive

1. Classification scores gain a defined, precedented meaning any
   MIF-conformant tool can implement identically.
2. The schema fields are additive: no existing ontology breaks, and
   enrichment can proceed ontology-by-ontology.

### Negative

1. Consumers must implement and maintain a calibration step before the tier
   thresholds mean anything; this ADR does not remove that cost.
2. Ontology authoring gains three more fields to curate well; badly-curated
   `negative_examples` (or auto-mined ones) can actively hurt boundary
   sharpening, which is why curation is mandated.

### Neutral

1. This ADR fixes no numeric threshold values — they are per-model,
   per-corpus calibration outputs by design.
2. Consumers' routing choices (review queues, expansion mining) remain
   theirs; divergence between consumers is expected and acceptable.

## Decision Outcome

The decision achieves its objective — a MIF-level, standards-anchored
vocabulary for trustworthy embedding-based classification — measured by:
the three fields validate in `ontology.schema.json` (additive; existing
corpus ontologies remain valid unchanged), the JSON-LD context maps them to
the stated IRIs, `yaml2jsonld.py` projects them losslessly, and the first
consumer (the `mif-rs` workspace's `mif-ontology`/`mif-rh` crates) can
implement the tier pattern against vendored copies of these schemas without
further MIF-side changes.

## Related Decisions

- [ADR-018](ADR-018-ontology-corpus-dedicated-repository-and-serving.md) —
  the ontology corpus lives in the dedicated `ontologies` repository;
  enriching corpus ontologies with the new fields happens there, against
  this schema.

## Links

- Research basis: `ontology-semantic-classification-scoring` session
  (39 findings, 0 falsified; draft proposal "Confidence-Threshold
  Classification as a MIF Ontology Capability", 2026-07-04) — the evidence
  and citations (BERTMap, TAC-KBP, Palantir Foundry, W3C SKOS, Home Depot
  KDD'20, selective-prediction theory) condensed here.
- [W3C SKOS Reference](https://www.w3.org/TR/skos-reference/) — the
  standards precedent for the label/definition/example field separation.
- [TAC-KBP entity-linking NIL thresholds](https://nlp.stanford.edu/pubs/kbp2011-entitylinking.pdf)
  — the absolute-score-plus-margin two-parameter precedent for tier 1.

## More Information

- **Date**: 2026-07-04
- **Source**: the research session's draft proposal, adopted here as its
  "Path to Adoption" hop 1 (MIF spec first; consumers second).

## Audit

### 2026-07-04

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
| --- | --- | --- | --- |
| Three optional entity_type fields present, additive | schema/ontology/ontology.schema.json | $defs.entityType.properties | accepted |
| Context maps aliases/exemplars to SKOS, negative_examples to mif ontology ns | schema/ontology/ontology.context.jsonld | term definitions | accepted |
| Projection passes the new fields through | scripts/yaml2jsonld.py | transform_entity_type | accepted |
| Ontology schema version bumped 1.0.0 -> 1.1.0 | VERSION.json | schemas.ontology | accepted |

**Summary:** Schema, context, projection, docs, and version constants all
carry the decision; no numeric thresholds are fixed anywhere in this repo,
matching the decision's calibration requirement.

**Action Required:** None.

### 2026-07-06

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
| --- | --- | --- | --- |
| `negative_examples` scoring implemented as a non-reordering demotion gate (`negative-demotion-v1`), matching this ADR's decision-boundary-only framing | `mif-rs` `crates/mif-ontology/src/confidence.rs`, `crates/mif-rh/src/suggest.rs` | `negative_demotes`, `build_candidates`/`suggest_from_candidates` | accepted |
| Confusion-matrix export (`calibrate --confusions`) shipped to ground human curation, per this ADR's "human-curated, never auto-mined" requirement | `mif-rs` `crates/mif-rh/src/calibrate.rs` | `confusions()` | accepted |
| 234 `negative_examples` curated for 59 entity types across 8 packs (`data-engineering`, `engineering-base`, `market-research`, `mif-generic`, `observability`, `software-engineering`, `software-security`, `trend-analysis`), human-reviewed across three fix passes before merge | `modeled-information-format/ontologies` v0.4.0 (modeled-information-format/ontologies#40, modeled-information-format/ontologies#41) | `*.ontology.yaml` `negative_examples` fields | accepted |
| Before/after calibration evidence produced; honest result recorded even though it did not match the naive expectation | `modeled-information-format/mif-rs` `reviews/mif-rs-negative-examples-evidence.md` | full report | accepted |

**Summary:** All three schema fields (`aliases`, `exemplars`, `negative_examples`) are now implemented end to end: parsed, scored, curated in the corpus, and calibration-evidenced. The evidence found that `negative_examples` does not move `calibrate`'s tier1_floor/tier1_margin/tier2_floor/confusion-pair metrics, because `negative-demotion-v1` is a non-reordering gate applied downstream of the raw ranking those metrics measure, an architectural property of this ADR's own design (negative evidence "for decision-boundary sharpening only," never concatenated into the positive embedding document), not a curation defect. A correctly-scoped metric, the direct demotion rate measured via `suggest-type`, confirms the mechanism is real: 138 of 226 current confusion pairs (61.1%) demote their wrong-answer candidate out of `auto_classify_eligible` on the first grounding finding tested.

**Action Required:** None. Future recalibration work on this corpus should measure `negative_examples`' effect via demotion rate (`suggest-type`), not `calibrate`'s aggregate gate-quality numbers, which are structurally insensitive to it by this ADR's own design.
