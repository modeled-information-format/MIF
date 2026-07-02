---
id: f6a7b8c9-0123-45f0-1234-6789012345f0
type: procedural
created: '2026-01-08T15:30:00Z'
modified: '2026-01-08T15:30:00Z'
namespace: _procedural/lab-protocols
title: Western Blot Protocol - Standard
tags:
- protocol
- western-blot
- protein
- molecular-biology
relationships:
- type: uses-equipment
  target: /equipment-chemidoc.md
- type: uses-equipment
  target: /equipment-transblot.md
- type: used-by
  target: /experiment-metabolic-screen-001.md
temporal:
  '@type': TemporalMetadata
  validFrom: '2026-01-01T00:00:00Z'
  recordedAt: '2026-01-08T15:30:00Z'
provenance:
  agent: claude-opus-4
  confidence: 0.95
  sourceType: external_import
ontology:
  id: biology-research-lab
  version: 0.1.0
entity:
  entity_type: protocol
  entity_id: protocol-western-blot-v2.1
  name: Standard Western Blot Protocol
  protocol_type: molecular_biology
  version: '2.1'
  author: Raj Patel
---

# Western Blot Protocol - Standard

Lab standard operating procedure for Western blot analysis of protein
expression. Version 2.1 updated January 2026.

## Overview

| Parameter | Value |
|-----------|-------|
| **Protocol ID** | WB-001 |
| **Version** | 2.1 |
| **Author** | Raj Patel |
| **Approved By** | Dr. Jane Smith |
| **Last Updated** | 2026-01-08 |

## Required Materials

### Reagents
- [ ] RIPA lysis buffer (Pierce #89901)
- [ ] Protease inhibitor cocktail (Roche #04693159001)
- [ ] Phosphatase inhibitor (Roche #04906845001)
- [ ] BCA protein assay kit (Pierce #23225)
- [ ] 4x Laemmli buffer (Bio-Rad #1610747)
- [ ] DTT or 2-mercaptoethanol
- [ ] Pre-cast gels (Bio-Rad 4-20% gradient)
- [ ] Running buffer (Tris-Glycine-SDS)
- [ ] Transfer buffer (Tris-Glycine-Methanol)
- [ ] PVDF membrane (Millipore #IPVH00010)
- [ ] Blocking buffer (5% milk or BSA in TBST)
- [ ] Primary antibodies (see antibody database)
- [ ] HRP-conjugated secondary antibodies
- [ ] ECL substrate (Pierce #34580)

### Equipment
- [ ] Mini-PROTEAN electrophoresis system
- [ ] Trans-Blot transfer system
- [ ] ChemiDoc imaging system
- [ ] Heat block or boiling water bath

## Procedure

### Day 1: Sample Preparation & Gel Electrophoresis

#### Step 1: Cell Lysis (30 min)

1. Aspirate media from cells
2. Wash 2x with ice-cold PBS
3. Add RIPA buffer (100 µL per 10 cm dish)
   - Include 1x protease inhibitor
   - Include 1x phosphatase inhibitor (if detecting phospho-proteins)
4. Scrape cells and transfer to microcentrifuge tube
5. Incubate on ice for 15 minutes
6. Sonicate briefly (3 pulses, 5 sec each)
7. Centrifuge at 14,000 x g for 15 min at 4°C
8. Transfer supernatant to new tube

**Critical:** Keep samples on ice at all times.

#### Step 2: Protein Quantification (45 min)

1. Perform BCA assay per manufacturer protocol
2. Prepare BSA standard curve (0-2000 µg/mL)
3. Load 10 µL sample + 200 µL BCA reagent
4. Incubate 30 min at 37°C
5. Read absorbance at 562 nm
6. Calculate protein concentration

#### Step 3: Sample Preparation (15 min)

1. Dilute samples to equal concentration (typically 1-2 µg/µL)
2. Add 4x Laemmli buffer (1:4 ratio)
3. Add DTT to 50 mM final concentration
4. Heat at 95°C for 5 minutes
5. Brief centrifuge to collect sample

#### Step 4: Gel Electrophoresis (90 min)

1. Assemble gel cassette in tank
2. Fill with 1x running buffer
3. Load samples (20-40 µg protein per lane)
4. Include protein ladder in first and last lanes
5. Run at 100V through stacking gel
6. Increase to 150V through resolving gel
7. Run until dye front reaches bottom

### Day 1-2: Transfer & Detection

#### Step 5: Transfer (90 min)

1. Activate PVDF membrane in methanol (1 min)
2. Equilibrate membrane in transfer buffer (5 min)
3. Equilibrate gel in transfer buffer (5 min)
4. Assemble transfer sandwich:
   - Cathode (black) → Sponge → Filter paper → Gel →
     Membrane → Filter paper → Sponge → Anode (red)
5. Transfer at 100V for 60-90 min at 4°C
   - Or 30V overnight at 4°C

**Quality Check:** Ponceau S stain to verify transfer.

#### Step 6: Blocking (60 min)

1. Wash membrane briefly in TBST
2. Block in 5% milk/TBST for 1 hour at RT
   - Use 5% BSA/TBST for phospho-antibodies

#### Step 7: Primary Antibody (Overnight)

1. Dilute primary antibody per datasheet
2. Incubate membrane overnight at 4°C with rocking

### Day 2: Detection

#### Step 8: Secondary Antibody (90 min)

1. Wash membrane 3x in TBST (10 min each)
2. Dilute HRP-secondary antibody (typically 1:5000)
3. Incubate 1 hour at RT with rocking
4. Wash membrane 3x in TBST (10 min each)

#### Step 9: Detection (30 min)

1. Prepare ECL substrate per manufacturer
2. Incubate membrane 1-2 min
3. Image on ChemiDoc system
4. Adjust exposure as needed
5. Save images in .tif format

## Troubleshooting

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| No signal | Insufficient protein | Load more protein |
| | Antibody issue | Verify antibody works |
| | Transfer failed | Check Ponceau stain |
| High background | Insufficient blocking | Block longer |
| | Antibody too concentrated | Dilute antibody |
| | Insufficient washing | Wash more |
| Uneven bands | Air bubbles in transfer | Remove bubbles |
| | Uneven loading | Requantify samples |

## Data Analysis

1. Open images in ImageJ/Fiji
2. Subtract background
3. Measure band intensity
4. Normalize to loading control (β-actin, GAPDH)
5. Calculate fold change relative to control

## Safety Notes

- Acrylamide is a neurotoxin - wear gloves
- Methanol is flammable - use in fume hood
- DTT/2-ME are reducing agents - use in fume hood
- Dispose of gels and buffers per EHS guidelines

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | 2026-01-08 | Updated transfer conditions |
| 2.0 | 2025-06-15 | Added phospho-protein notes |
| 1.0 | 2024-09-01 | Initial protocol |

## Relationships

- uses-equipment [Equipment Chemidoc](/equipment-chemidoc.md)
- uses-equipment [Equipment Transblot](/equipment-transblot.md)
- used-by [Experiment Metabolic Screen 001](/experiment-metabolic-screen-001.md)
