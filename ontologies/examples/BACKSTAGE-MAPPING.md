---
diataxis_type: how-to
---

# Backstage.io Entity Mapping Guide

This document maps MIF industry ontologies to Backstage.io's Software Catalog
model, so organizations can use both systems together.

## Complete Catalog Examples

Ready-to-use Backstage catalog files are available:

| Industry | Catalog File |
|----------|--------------|
| Agriculture | `backstage/agriculture/catalog-info.yaml` |
| Publishing | `backstage/publishing/catalog-info.yaml` |
| Biology Lab | `backstage/biology-lab/catalog-info.yaml` |

These demonstrate the full entity mapping with annotations linking back to
MIF ontology entity types.

## Backstage Entity Model Overview

Backstage uses a hierarchical entity model:

```
Domain
  └── System
        └── Component
              └── API
              └── Resource
Group → User (ownership)
```

**Core Kinds:**
- `Component` - Software components (services, websites, libraries)
- `API` - Interfaces for machine-to-machine communication
- `Resource` - Infrastructure (databases, storage, clusters)
- `System` - Collection of components that form a product
- `Domain` - Business or product area grouping systems
- `Group` - Team or organizational unit
- `User` - Individual person

## Mapping by Industry

### Regenerative Agriculture → Backstage

| MIF Entity | Backstage Kind | Rationale |
|------------|----------------|-----------|
| `farm` | `Domain` | Top-level organizational boundary |
| `field` | `System` | Self-contained operational unit |
| `herd` | `System` | Self-contained livestock unit |
| `crop-rotation` | `Component` | Managed process/procedure |
| `grazing-plan` | `Component` | Managed process/procedure |
| `equipment` | `Resource` | Physical infrastructure |
| `soil-profile` | `Resource` | Data resource |
| `carbon-baseline` | `Resource` | Data resource |
| `carbon-credit` | `Resource` | Tradeable asset |
| `certification` | `Component` | Managed compliance entity |
| `buyer` | `Group` | External organization |
| `contract` | `API` | Interface/agreement |

**Example Backstage Catalog Entry:**

```yaml
apiVersion: backstage.io/v1alpha1
kind: Domain
metadata:
  name: sunrise-farm
  description: Regenerative farm operation
  annotations:
    mif.ontology/type: farm
    mif.ontology/certification: roc_silver
spec:
  owner: farm-team
---
apiVersion: backstage.io/v1alpha1
kind: System
metadata:
  name: north-pasture
  description: 40-acre rotational grazing system
  annotations:
    mif.ontology/type: field
    mif.ontology/soil-carbon: "3.2"
spec:
  owner: farm-team
  domain: sunrise-farm
---
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: 2026-grazing-plan
  description: Annual rotational grazing schedule
  annotations:
    mif.ontology/type: grazing-plan
spec:
  type: procedure
  lifecycle: production
  owner: farm-team
  system: north-pasture
```

### K-12 Educational Publishing → Backstage

| MIF Entity | Backstage Kind | Rationale |
|------------|----------------|-----------|
| `program` | `Domain` | Product line boundary |
| `title` | `System` | Published product unit |
| `digital-resource` | `Component` | Software/digital asset |
| `content-asset` | `Resource` | Content component |
| `manuscript` | `Component` | Work in progress |
| `standard` | `Resource` | Reference data |
| `alignment` | `API` | Relationship/mapping |
| `author` | `User` | Contributor |
| `editorial-team` | `Group` | Internal team |
| `state-adoption` | `Component` | Managed process |
| `district-sale` | `Resource` | Transaction record |

**Example Backstage Catalog Entry:**

```yaml
apiVersion: backstage.io/v1alpha1
kind: Domain
metadata:
  name: into-math
  description: K-8 Mathematics Curriculum Program
  annotations:
    mif.ontology/type: program
    mif.ontology/subject: mathematics
spec:
  owner: math-editorial-team
---
apiVersion: backstage.io/v1alpha1
kind: System
metadata:
  name: into-math-grade-5
  description: Into Math Grade 5 Student Edition
  annotations:
    mif.ontology/type: title
    mif.ontology/isbn: "9780358111234"
spec:
  owner: math-editorial-team
  domain: into-math
---
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: into-math-5-digital
  description: Grade 5 Digital Learning Platform
  annotations:
    mif.ontology/type: digital-resource
spec:
  type: website
  lifecycle: production
  owner: math-editorial-team
  system: into-math-grade-5
  providesApis:
    - into-math-lti-api
```

### Biology Research Lab → Backstage

| MIF Entity | Backstage Kind | Rationale |
|------------|----------------|-----------|
| `principal-investigator` | `User` | Lab leader |
| `lab-member` | `User` | Team member |
| `grant` | `Domain` | Funding boundary |
| `project` | `System` | Research unit |
| `protocol` | `Component` | Reusable procedure |
| `experiment` | `Component` | Individual run |
| `sample` | `Resource` | Physical material |
| `equipment` | `Resource` | Infrastructure |
| `dataset` | `Resource` | Data asset |
| `publication` | `Component` | Output artifact |
| `irb-protocol` | `Component` | Compliance entity |
| `iacuc-protocol` | `Component` | Compliance entity |
| `ibc-protocol` | `Component` | Compliance entity |
| `collaborator` | `Group` | External partner |

**Example Backstage Catalog Entry:**

```yaml
apiVersion: backstage.io/v1alpha1
kind: Domain
metadata:
  name: nih-r01-ca123456
  description: "Cancer Metabolism Research Grant"
  annotations:
    mif.ontology/type: grant
    mif.ontology/agency: nih
    mif.ontology/mechanism: R01
spec:
  owner: smith-lab
---
apiVersion: backstage.io/v1alpha1
kind: System
metadata:
  name: aim-1-metabolic-profiling
  description: Specific Aim 1 - Metabolic Profiling
  annotations:
    mif.ontology/type: project
spec:
  owner: smith-lab
  domain: nih-r01-ca123456
---
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: western-blot-protocol
  description: Standard Western Blot Protocol v2.1
  annotations:
    mif.ontology/type: protocol
spec:
  type: procedure
  lifecycle: production
  owner: smith-lab
  system: aim-1-metabolic-profiling
---
apiVersion: backstage.io/v1alpha1
kind: Resource
metadata:
  name: rnaseq-dataset-2026-01
  description: RNA-seq data from metabolic screen
  annotations:
    mif.ontology/type: dataset
    mif.ontology/repository: geo
    mif.ontology/accession: GSE999999
spec:
  type: dataset
  owner: smith-lab
  system: aim-1-metabolic-profiling
```

---

## Memory Type Gap Analysis

The MIF base types (semantic/episodic/procedural) map to different
aspects of organizational knowledge. This analysis identifies gaps in each
industry ontology.

### Coverage Matrix

| Namespace | Agriculture | Publishing | Biology Lab |
|-----------|:-----------:|:----------:|:-----------:|
| **SEMANTIC** | | | |
| entities/concepts | Strong | Strong | Strong |
| relationships | Strong | Medium | Strong |
| taxonomies | Strong | Strong | Medium |
| **EPISODIC** | | | |
| events/incidents | Strong | Medium | Medium |
| timelines | Strong | Medium | Strong |
| decision history | Medium | Weak | Medium |
| **PROCEDURAL** | | | |
| SOPs/runbooks | Strong | Strong | Strong |
| workflows | Strong | Strong | Strong |
| troubleshooting | Medium | Weak | Strong |

### Gap Analysis by Industry

#### Regenerative Agriculture

**Strengths:**
- Comprehensive land/soil/crop semantic entities
- Strong seasonal/cyclical episodic coverage
- Detailed procedural protocols for soil health

**Gaps Identified:**
1. **Episodic: Decision History** - Limited tracking of why specific
   practices were adopted/abandoned
   - *Recommendation:* Add `practice-decision` entity type

2. **Semantic: Knowledge Base** - No formal entity for capturing
   agronomic learnings (e.g., "this cover crop mix works best here")
   - *Recommendation:* Add `agronomic-insight` entity type

3. **Procedural: Troubleshooting** - Limited guidance for handling
   crop failures, pest outbreaks
   - *Recommendation:* Add `diagnostic-guide` entity type

#### K-12 Educational Publishing

**Strengths:**
- Comprehensive product/content semantic entities
- Strong procedural editorial workflows
- Good standards alignment coverage

**Gaps Identified:**
1. **Episodic: Decision History** - Weak tracking of editorial decisions
   (why content was changed, approach chosen)
   - *Recommendation:* Add `editorial-decision` entity type

2. **Episodic: Events** - Limited incident tracking for production issues
   - *Recommendation:* Add `production-incident` entity type

3. **Procedural: Troubleshooting** - No formal guidance for handling
   adoption rejections, negative reviews
   - *Recommendation:* Add `remediation-guide` entity type

4. **Semantic: Competitive** - No entity for tracking competitor products
   - *Recommendation:* Add `competitive-title` entity type

#### Biology Research Lab

**Strengths:**
- Comprehensive grant and project semantic entities
- Strong compliance (IRB/IACUC/IBC) coverage
- Excellent experimental protocol procedures

**Gaps Identified:**
1. **Semantic: Knowledge Base** - Limited formal entity for capturing
   methodological learnings (e.g., "this antibody doesn't work for IF")
   - *Recommendation:* Add `methodological-note` entity type

2. **Episodic: Lab Incidents** - No formal entity for equipment failures,
   contamination events
   - *Recommendation:* Add `lab-incident` entity type

3. **Semantic: Taxonomy** - Limited entity for organism/cell line lineage
   - *Recommendation:* Add `biological-lineage` entity type

4. **Procedural: Onboarding** - No formal new member training procedures
   - *Recommendation:* Add `onboarding-procedure` entity type

---

## Cross-Industry Shared Patterns

These patterns appear across all three industries and should use shared
traits from `shared-traits.ontology.yaml`:

| Pattern | Trait | Agriculture | Publishing | Biology |
|---------|-------|-------------|------------|---------|
| Lifecycle states | `lifecycle` | crops, certifications | titles, manuscripts | grants, samples |
| Compliance audits | `auditable` | inspections | accessibility | IRB/IACUC |
| Expiring credentials | `renewable` | certifications | rights, contracts | protocols, training |
| Physical location | `located` | fields, equipment | warehouses | samples, equipment |
| Budget tracking | `budgeted` | inputs, equipment | production | grants |
| Quality checks | `quality_controlled` | harvest, soil | manuscripts | experiments |
| Scheduling | `scheduled` | planting, harvest | milestones | experiments |
| Inventory | `inventoried` | equipment, inputs | content assets | samples, reagents |

---

## Implementation Recommendations

1. **Use MIF for Deep Domain Knowledge**
   - Store detailed domain-specific memories in MIF format
   - Use base types for proper categorization
   - Enable agent-based discovery patterns

2. **Use Backstage for Developer/Operator Experience**
   - Catalog high-level entities in Backstage
   - Link to MIF memories via annotations
   - Enable search and discovery across systems

3. **Sync Strategy**
   - MIF → Backstage: Export key entities to catalog YAML
   - Backstage → MIF: Link catalog entries in memory relationships
   - Use `mif.ontology/*` annotations for type mapping

4. **Address Memory Type Gaps**
   - Prioritize adding decision history (episodic) entities
   - Add troubleshooting/diagnostic procedures
   - Create formal knowledge base entities for learnings
