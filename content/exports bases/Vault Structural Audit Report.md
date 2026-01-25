---
role: report
tags:
  - audit
  - generated
generated: 2026-01-25
tool: irrev
source: bases
canonical: false
---

# Vault Structural Audit Report

> **Generated:** 2026-01-25
> **Scope:** Full vault integrity analysis using the irreversibility accounting framework
> **Non-claim:** This report surfaces structural patterns and constraint-load signals. It does not prescribe action.

---

## Executive Summary

The vault contains **66 notes** across 6 content folders. The concept graph shows a well-structured dependency hierarchy with clear layer separation. However, the audit reveals specific **constraint-load accumulation points** and **routing pressure** that merit attention.

### Key Findings

| Signal | Count | Interpretation |
|--------|-------|----------------|
| Orphan notes (0 outlinks) | 1 | Potential accounting-failure: unintegrated content |
| High-link notes (20+) | 6 | Hub candidates; may carry disproportionate constraint load |
| Domain primitive gaps | 5/5 | All domains missing 4 primitive links each |
| Diagnostics without dependencies | 1 | May not properly trace to concept graph |
| Projections missing failure_modes link | 8/10 | Incomplete failure mode documentation |

---

## 1. Concept Graph Topology

### Layer Distribution (32 concepts)

| Layer | Count | Role |
|-------|-------|------|
| primitive | 7 | Foundation: difference, persistence, erasure-cost, asymmetry, constraint, accumulation, irreversibility-quanta |
| foundational | 1 | transformation-space (single anchor) |
| first-order | 10 | Derived effects: irreversibility, persistent-difference, displacement, residual, constraint-load, etc. |
| accounting | 4 | Tracking structures: feasible-set, collapse-surface, tracking-mechanism, accounting-failure |
| mechanism | 6 | Response patterns: rollback, containment, deprecation, migration, quarantine, ratchet |
| failure-state | 2 | Terminal states: brittleness, saturation |
| selector | 1 | admissibility |
| meta-analytical | 1 | lens |

### Hub Spine (high outlink concepts)

These concepts carry the highest **dependency count** (outlinks), indicating they route through many other concepts:

| Concept | Outlinks | Dependencies span |
|---------|----------|-------------------|
| irreversibility | 14 | persistence, erasure-cost, asymmetry, transformation-space, displacement, constraint-accumulation, accounting-failure |
| feasible-set | 12 | transformation-space, constraint, constraint-load, erasure-cost, persistent-difference |
| constraint-load | 11 | residual, transformation-space, rollback, constraint, erasure-cost, feasible-set, admissibility, saturation |
| ratchet | 8 | asymmetry, residual, constraint-load, constraint, erasure-cost |
| quarantine | 8 | propagation, persistent-difference, residual, constraint, displacement |
| admissibility | 8 | feasible-set, constraint, constraint-load, lens, collapse-surface |

**Interpretation:** These concepts function as **routing junctions**. Changes to their definitions propagate constraint-load downstream. The irreversibility-feasible-set-constraint-load triad forms the load-bearing spine.

### Leaf Concepts (low outlinks)

| Concept | Outlinks | Risk |
|---------|----------|------|
| propagation | 1 | Minimal; clean dependency |
| persistence-gradient | 1 | Minimal; clean dependency |
| erasure-cost | 2 | Foundational; expected to be imported, not to import |
| persistent-difference | 2 | First-order bridge; expected |
| tracking-mechanism | 2 | Accounting primitive; expected |

---

## 2. Domain Primitive Coverage Audit

All 5 domain notes show **identical gaps** in primitive concept linkage:

| Domain | transformation_space | erasure_cost | persistence | constraint_load | difference | constraint | residual |
|--------|---------------------|--------------|-------------|-----------------|------------|------------|----------|
| Digital Platforms | yes | yes | **no** | yes | **no** | **no** | **no** |
| Financial Infrastructure | yes | yes | **no** | yes | **no** | **no** | **no** |
| Software Supply Chains | yes | yes | **no** | yes | **no** | **no** | **no** |
| AI Systems | yes | yes | **no** | yes | **no** | **no** | **no** |
| Human History | yes | yes | **no** | yes | **no** | **no** | **no** |

### Structural Diagnosis

The uniform pattern suggests **systematic omission** rather than domain-specific reasoning:

- **persistence** is foundational to all irreversibility claims. Its absence in domain notes means the grounding for "what persists" is implicit.
- **difference** anchors transformation-space. Without explicit linkage, domains assume rather than declare what constitutes change.
- **constraint** and **residual** are the operational primitives. Their absence means domains describe effects without anchoring the mechanisms.

**Recommendation:** Each domain note should explicitly link to the 4 missing primitives, even if briefly, to complete the dependency chain and prevent accounting-failure.

---

## 3. Orphan and High-Link Notes

### Orphan Notes (0 outlinks)

| Note | Location | Modified |
|------|----------|----------|
| Ontology of Irreversibility | papers | 2026-01-24 |

**Interpretation:** This paper has no internal links to the concept graph. It may be:
- A stub awaiting integration
- An external reference that deliberately avoids vault dependencies
- An accounting-failure: content exists but routing to concepts is missing

### High-Link Notes (20+ outlinks)

| Note | Location | Outlinks |
|------|----------|----------|
| Irreversibility Accounting (Registry) | papers | 168 |
| Irreversibility Accounting (Paper) | papers | 56 |
| OpenAI (projection) | projections | 36 |
| The Structure of Agency | papers | 34 |
| Quantum Measurement | projections | 31 |
| Human History (domain) | domains | 30 |

**Interpretation:** The Registry (168 links) functions as a **canonical reference hub**. High-link projections (OpenAI, Quantum Measurement) suggest these domains have been fully mapped to the concept vocabulary. Human History (30 links) is the most concept-dense domain note.

---

## 4. Diagnostics Inventory

### By Subfolder

| Location | Count | Total Links |
|----------|-------|-------------|
| diagnostics/ | 4 | 42 |
| diagnostics/irreversibility/ | 4 | 20 |

### Dependency Declaration Audit

| Diagnostic | Has Dependencies | Links |
|------------|------------------|-------|
| Concept Drift Exposure Map | yes | 11 |
| Domain Template | yes | 18 |
| **Failure Modes of the Irreversibility Lens** | **no** | 1 |
| Prompting Guide | yes | 12 |
| Diagnostic Checklist | yes | 4 |
| Failure Signatures | yes | 3 |
| README | yes | 9 |
| Stress Tests & Boundaries | yes | 4 |

**Signal:** "Failure Modes of the Irreversibility Lens" has no declared dependencies and only 1 outlink. This is a potential **containment failure**: the note that documents failure modes is itself disconnected from the concept graph that defines those modes.

---

## 5. Projections Coverage

### Core Concept Linkage

| Projection | failure_modes | rollback | lens | displacement | constraint_load | residual |
|------------|---------------|----------|------|--------------|-----------------|----------|
| Cosmology | no | yes | no | yes | yes | yes |
| Discordianism | yes | yes | no | yes | yes | yes |
| Enochian | no | no | no | yes | yes | yes |
| Fourth Way | no | yes | no | yes | yes | yes |
| Jung | no | yes | yes | yes | yes | yes |
| OpenAI | no | yes | no | yes | yes | yes |
| Plato's Republic | no | yes | no | yes | yes | yes |
| Quantum Measurement | no | yes | no | yes | yes | yes |
| Stoicism | no | yes | no | yes | yes | yes |
| Zen | yes | yes | yes | yes | yes | yes |

### Pattern Analysis

- **All projections** link to displacement, constraint_load, and residual (core first-order concepts)
- **8/10 projections** lack link to "Failure Modes of the Irreversibility Lens"
- **8/10 projections** lack link to "lens" concept
- **Only Zen** has complete coverage of all tracked link types

**Interpretation:** The projections demonstrate consistent application of the core vocabulary. The failure_modes and lens gaps may be intentional (projections describe external systems, not internal tooling) or may represent incomplete documentation of how each projection can fail.

---

## 6. Invariants Integrity

All 4 invariants are properly marked:
- role: invariant
- status: structural
- canonical: true

### Cross-Reference Integrity

| Invariant | Links | References |
|-----------|-------|------------|
| Attribution | 4 | Governance, Decomposition, Irreversibility (Invariant) |
| Decomposition | 3 | Governance, Attribution, Irreversibility (Invariant) |
| Governance | 4 | Attribution, Decomposition, Irreversibility (Invariant) |
| Irreversibility (Invariant) | 13 | transformation-space, persistent-difference, erasure-cost, erasure-asymmetry, propagation, displacement, absorption, accounting-failure, constraint-load, collapse-surface, Decomposition, Governance |

**Interpretation:** The structural invariants form a complete clique (all reference each other). The Irreversibility (Invariant) note bridges invariants to the concept graph with 13 links, properly grounding structural claims in the vocabulary.

---

## 7. Constraint-Load Summary

### Where cost accumulates

1. **Domain notes**: Missing primitive links create implicit dependencies. Any refinement of persistence, difference, constraint, or residual affects domains without explicit routing.

2. **Failure Modes diagnostic**: Single link, no dependencies. Acts as a documentation silo rather than integrated diagnostic.

3. **Orphan paper**: Ontology of Irreversibility carries no graph weight. Either integrate or explicitly mark as external.

### Routing pressure points

1. **irreversibility concept** (14 links): Central hub. Definition changes propagate widely.
2. **feasible-set concept** (12 links): Accounting hub. Tightly coupled to constraint-load and transformation-space.
3. **Registry paper** (168 links): Reference hub. Changes here affect interpretation of canonical concepts.

---

## 8. Recommended Actions

### High Priority (prevent accounting-failure)

1. **Domain primitive completion**: Add explicit links to persistence, difference, constraint, residual in all 5 domain notes
2. **Failure Modes diagnostic**: Add depends_on frontmatter and links to the concepts it describes

### Medium Priority (reduce routing pressure)

3. **Ontology paper integration**: Either link to concept graph or mark as external-only reference
4. **Projection failure_modes**: Consider whether projections should link to failure mode documentation

### Low Priority (documentation hygiene)

5. **Tags**: No notes use tags. Either adopt tagging workflow or remove tag-tracking from bases

---

## Appendix: Data Sources

This report synthesizes exports from:
- Base - Full Vault Audit
- Base - Concepts by Layer
- Base - Domain Concept Dependencies
- Base - Diagnostics Inventory
- Base - Projections
- Base - Invariants
- Base - Link Integrity

All data extracted 2026-01-25.
