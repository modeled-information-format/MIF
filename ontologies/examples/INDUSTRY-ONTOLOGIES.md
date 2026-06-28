---
diataxis_type: reference
---

# Industry Ontologies for MIF

This document provides comprehensive documentation for the four industry
ontologies created for the Modeled Information Format (MIF) system.

## Overview

Four domain-specific ontologies demonstrate how to extend the MIF base
ontology for different industries:

| Ontology | Domain | Entity Types | Traits Used |
|----------|--------|--------------|-------------|
| `regenerative-agriculture` | Farm operations | 17 | 12 |
| `k12-educational-publishing` | Educational content | 16 | 10 |
| `biology-research-lab` | Academic research | 18 | 11 |
| `backstage` | Developer portals | 12 | 6 |

All four ontologies:
- Extend `mif-base.ontology.yaml` (base type namespaces)
- Use traits from `shared-traits.ontology.yaml` (DRY mixins)
- Follow the MIF schema specification v1.0
- Include discovery patterns for entity suggestion

---

## Regenerative Agriculture Ontology

### Purpose

Models regenerative farm operations with full ecosystem coverage including
supply chain integration, carbon credit markets, and certification bodies.

### Research Sources

| Source | URL | Relevance |
|--------|-----|-----------|
| Rodale Institute ROC Standards | https://rodaleinstitute.org | Certification tiers |
| Soil & Climate Initiative v3.0 | https://soilclimateinitiative.org | Verification framework |
| USDA NRCS Soil Health | https://www.nrcs.usda.gov | Core principles |
| Rainforest Alliance (2025) | https://rainforest-alliance.org | Regen ag standard |
| FoodChain ID RGN Standard | https://foodchainid.com | Tiered certification |
| FAO Agroecology Hub | https://www.fao.org | Global standards |

### Design Rationale

**Namespace Structure:**
- `_semantic/land` - Physical assets (fields, soil profiles)
- `_semantic/livestock` - Animal management
- `_semantic/crops` - Crop types and rotations
- `_semantic/carbon` - Carbon credits and baselines
- `_semantic/supply-chain` - Buyers, contracts
- `_episodic/seasons` - Growing cycle events
- `_procedural/soil-health` - Regenerative practices

**Key Design Decisions:**

1. **Tiered Certification Model**: Supports multiple certification
   standards (ROC Bronze/Silver/Gold, SCI Tiers 1-4, RGN Basic/Advanced)
   reflecting the industry's multi-standard reality.

2. **Carbon Integration**: First-class entities for carbon baselines and
   credits, recognizing the growing importance of carbon markets.

3. **Supply Chain**: Includes buyer and contract entities to model
   the full value chain, not just on-farm operations.

4. **Weather Events**: Episodic events for weather impacts, enabling
   insurance and risk management integrations.

### Entity Summary

| Entity | Type | Purpose |
|--------|------|---------|
| `farm` | semantic | Primary organizational unit |
| `field` | semantic | Individual land parcel |
| `soil-profile` | semantic | Soil health measurements |
| `crop` | semantic | Crop type definitions |
| `crop-rotation` | procedural | Multi-year rotation plans |
| `planting` | episodic | Planting events |
| `herd` | semantic | Livestock groups |
| `animal` | semantic | Individual animal records |
| `grazing-plan` | procedural | Rotational grazing SOPs |
| `equipment` | semantic | Farm machinery |
| `input` | semantic | Seeds, amendments |
| `certification` | semantic | Organic/ROC certifications |
| `inspection` | episodic | Audit events |
| `carbon-baseline` | semantic | Carbon measurements |
| `carbon-credit` | semantic | Verified credits |
| `buyer` | semantic | Market channels |
| `contract` | semantic | Sales agreements |
| `harvest-record` | episodic | Yield data |
| `weather-event` | episodic | Climate impacts |

---

## K-12 Educational Publishing Ontology

### Purpose

Models educational publishing operations focused on K-12 curriculum,
textbook development, digital content, and state adoption processes.
Designed after legacy publishers like Houghton Mifflin Harcourt.

### Research Sources

| Source | URL | Relevance |
|--------|-----|-----------|
| EdReports.org | https://edreports.org | Quality standards |
| NASBE | https://nasbe.org | State adoption guidance |
| CA Dept of Education | https://cde.ca.gov | Curriculum frameworks |
| Common Core | https://corestandards.org | Standards alignment |
| ISTE Standards | https://iste.org | Technology standards |
| AAP K-12 Guidelines | https://publishers.org | Industry practices |

### Design Rationale

**Namespace Structure:**
- `_semantic/titles` - Published products
- `_semantic/programs` - Curriculum series
- `_semantic/content` - Content assets
- `_semantic/standards` - Educational standards
- `_semantic/contributors` - Authors, editors
- `_semantic/adoptions` - State adoption entities
- `_episodic/editorial` - Development milestones
- `_procedural/editorial-workflow` - Production SOPs

**Key Design Decisions:**

1. **Standards-First Alignment**: Dedicated entities for standards and
   alignments, reflecting the critical importance of CCSS/state standards.

2. **State Adoption Lifecycle**: Full modeling of the adoption process
   including submission, review, and decision tracking.

3. **Content Asset Reuse**: Granular content-asset entity enables
   tracking of reusable components across titles.

4. **Accessibility Built-In**: Accessibility specification entity
   reflects regulatory requirements (WCAG, Section 508).

### Entity Summary

| Entity | Type | Purpose |
|--------|------|---------|
| `title` | semantic | Published textbook/workbook |
| `program` | semantic | Curriculum program/series |
| `digital-resource` | semantic | LMS, interactive content |
| `manuscript` | semantic | Work in editorial pipeline |
| `content-asset` | semantic | Reusable content component |
| `standard` | semantic | Learning standard/objective |
| `alignment` | semantic | Content-to-standard mapping |
| `author` | semantic | Content contributor |
| `editorial-team` | semantic | Internal editorial group |
| `state-adoption` | semantic | State adoption cycle |
| `adoption-submission` | episodic | Title submission event |
| `district-sale` | episodic | District purchase record |
| `editorial-milestone` | episodic | Development checkpoint |
| `review-cycle` | episodic | Content review event |
| `print-specification` | procedural | Print production specs |
| `accessibility-spec` | procedural | A11y requirements |

---

## Biology Research Lab Ontology

### Purpose

Models academic biology research labs with full research lifecycle
coverage including grant management, experiment tracking, sample
handling, publication pipeline, and regulatory compliance.

### Research Sources

| Source | URL | Relevance |
|--------|-----|-----------|
| NIH Grants & Funding | https://grants.nih.gov | Grant policies |
| NSF PAPPG | https://nsf.gov | Proposal procedures |
| OHRP | https://hhs.gov/ohrp | Human subjects |
| OLAW/NIH | https://olaw.nih.gov | Animal welfare |
| FAIR Principles | https://go-fair.org | Data management |
| CRediT Taxonomy | https://credit.niso.org | Author contributions |

### Design Rationale

**Namespace Structure:**
- `_semantic/personnel` - PIs, lab members
- `_semantic/grants` - Funding awards
- `_semantic/projects` - Research projects
- `_semantic/samples` - Biological specimens
- `_semantic/datasets` - Research data
- `_semantic/publications` - Papers, patents
- `_semantic/compliance` - IRB, IACUC, IBC
- `_episodic/experiments` - Experiment runs
- `_procedural/lab-protocols` - SOPs

**Key Design Decisions:**

1. **Grant-Centric Organization**: Grants as domains, reflecting how
   academic labs are organized around funding sources.

2. **Compliance First-Class**: Dedicated entities for IRB, IACUC, and
   IBC protocols, reflecting regulatory requirements.

3. **Publication Pipeline**: Full manuscript lifecycle from preparation
   through peer review to publication.

4. **Sample Chain of Custody**: Comprehensive sample tracking with
   storage, status, and compliance linkage.

5. **CRediT Roles**: Author entity supports CRediT contributor roles
   for proper attribution.

### Entity Summary

| Entity | Type | Purpose |
|--------|------|---------|
| `principal-investigator` | semantic | Lab PI |
| `lab-member` | semantic | Postdocs, students, staff |
| `collaborator` | semantic | External partners |
| `grant` | semantic | Funding award |
| `grant-submission` | episodic | Proposal submission |
| `grant-report` | procedural | Progress reports |
| `project` | semantic | Research project/aim |
| `protocol` | procedural | Experimental SOP |
| `experiment` | episodic | Individual experiment run |
| `sample` | semantic | Biological specimen |
| `reagent` | semantic | Lab consumable |
| `equipment` | semantic | Lab instrument |
| `dataset` | semantic | Research data |
| `publication` | semantic | Paper, preprint |
| `manuscript-submission` | episodic | Journal submission |
| `irb-protocol` | semantic | Human subjects protocol |
| `iacuc-protocol` | semantic | Animal use protocol |
| `ibc-protocol` | semantic | Biosafety protocol |
| `training-record` | episodic | Compliance training |

---

## Shared Traits (Mixins)

The `shared-traits.ontology.yaml` file provides reusable traits that
are composed into entity types across all four industries.

### Trait Categories

| Category | Traits | Description |
|----------|--------|-------------|
| Lifecycle | `lifecycle`, `renewable` | State tracking, expiration |
| Compliance | `auditable`, `certified`, `regulated` | Audit trails |
| Geographic | `located`, `bounded` | Physical location |
| Stakeholder | `owned`, `contactable` | Responsibility |
| Financial | `budgeted`, `transactional` | Money tracking |
| Temporal | `scheduled`, `seasonal` | Time-based |
| Measurement | `measured`, `scored` | Quantitative data |
| Classification | `categorized`, `tagged` | Organization |
| Asset | `inventoried`, `maintainable` | Physical assets |
| Quality | `reviewed`, `quality_controlled` | Approval workflows |

### Cross-Industry Usage

| Trait | Agriculture | Publishing | Biology Lab |
|-------|:-----------:|:----------:|:-----------:|
| `lifecycle` | crops, certs | titles, mss | grants, samples |
| `auditable` | inspections | accessibility | compliance |
| `renewable` | certifications | rights | protocols |
| `budgeted` | equipment | production | grants |
| `scheduled` | planting | milestones | experiments |
| `inventoried` | equipment | assets | samples |
| `reviewed` | crop plans | manuscripts | protocols |
| `certified` | organic | - | training |
| `measured` | soil, yield | - | experiments |
| `owned` | farm, herds | programs | projects |

---

## File Structure

```
ontologies/
├── mif-base.ontology.yaml          # Core base types
├── shared-traits.ontology.yaml     # Reusable mixins
├── examples/
│   ├── software-engineering.ontology.yaml
│   ├── regenerative-agriculture.ontology.yaml
│   ├── k12-educational-publishing.ontology.yaml
│   ├── biology-research-lab.ontology.yaml
│   ├── csi-5w1h.ontology.yaml
│   ├── backstage/
│   ├── INDUSTRY-ONTOLOGIES.md      # This file
│   ├── BACKSTAGE-MAPPING.md        # Backstage integration
│   └── memories/
│       ├── agriculture/
│       │   ├── soil-profile-example.md
│       │   └── grazing-plan-example.md
│       ├── publishing/
│       │   ├── state-adoption-example.md
│       │   └── editorial-workflow-example.md
│       └── biology-lab/
│           ├── grant-example.md
│           └── protocol-example.md
```

---

## Usage

### Loading an Ontology

Place the ontology file in your project's mnemonic directory:

```bash
cp ontologies/examples/biology-research-lab.ontology.yaml \
   .claude/mnemonic/ontology.yaml
```

### Creating Memories

Use the entity types and namespaces defined in the ontology:

```bash
/mnemonic:capture _semantic/grants "NIH R01 Award" \
  --entity-type grant \
  --tags nih,funding
```

### Discovery Patterns

The ontology's discovery patterns will automatically suggest entity
types based on content:

```
User: "We got the R01 funded!"
Claude: Detected grant-related content. Suggesting:
  - Entity type: grant
  - Namespace: _semantic/grants
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-26 | Initial release |

## License

Same license as parent MIF project.
