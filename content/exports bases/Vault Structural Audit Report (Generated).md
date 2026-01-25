# Vault Structural Audit Report

> **Generated:** 2026-01-25
> **Scope:** Full vault integrity analysis using the irreversibility accounting framework
> **Non-claim:** This report surfaces structural patterns and constraint-load signals. It does not prescribe action.

---

## Executive Summary

The vault contains **65 notes** across content folders. 
The audit reveals specific **constraint-load accumulation points** and **routing pressure** that merit attention.

### Key Findings

| Signal | Count | Interpretation |
|--------|-------|----------------|
| Orphan notes (0 outlinks) | 0 | Potential accounting-failure: unintegrated content |
| High-link notes (20+) | 14 | Hub candidates; may carry disproportionate constraint load |
| Domains with primitive gaps | 0/5 | Missing foundational concept links |
| Diagnostics without dependencies | 0 | May not properly trace to concept graph |
| Projections missing failure_modes | 8/10 | Incomplete failure mode documentation |

---

## 1. Concept Graph Topology

### Layer Distribution

| Layer | Count |
|-------|-------|
| first-order | 10 |
| primitive | 7 |
| mechanism | 6 |
| accounting | 4 |
| failure-state | 2 |
| selector | 1 |
| meta-analytical | 1 |
| foundational | 1 |

### Hub Spine (high outlink concepts)

These concepts carry the highest **dependency count** (outlinks), indicating they route through many other concepts:

| Concept | Outlinks | Key Dependencies |
|---------|----------|------------------|
| [[irreversibility]] | 14 | persistence, erasure-cost, asymmetry, transformation-space, persistence (+9 more) |
| [[feasible-set]] | 12 | transformation-space, constraints, constraint-load, erasure-cost, persistent differences (+7 more) |
| [[constraint-load]] | 11 | residuals, residuals, transformation-space, rollback, constraint (+6 more) |
| [[ratchet]] | 8 | asymmetry, residuals, constraint-load, constraint, asymmetry (+3 more) |
| [[quarantine]] | 8 | propagation, persistent-difference, residuals, persistent-difference, propagation (+3 more) |
| [[admissibility]] | 8 | feasible set, feasible-set, constraint, constraint-load, lens (+3 more) |
| [[accounting-failure]] | 8 | residuals, persistent-difference, erasure-cost, tracking-mechanism, absorption (+3 more) |
| [[rollback]] | 7 | residuals, residuals, constraint-load, persistent-difference, propagation (+2 more) |
| [[residual]] | 7 | persistent-difference, constraint, displacement, accounting-failure, erasure-cost (+2 more) |
| [[persistence]] | 7 | difference, transformation-space, difference, transformation-space, erasure-cost (+2 more) |

**Interpretation:** These concepts function as **routing junctions**. Changes to their definitions propagate constraint-load downstream.

---

## 2. Domain Primitive Coverage Audit

All domains have complete primitive coverage.

---

## 3. Orphan and High-Link Notes

No orphan notes detected.

### High-Link Notes (20+ outlinks)

| Note | Location | Outlinks |
|------|----------|----------|
| Irreversibility Accounting (Registry) | papers | 168 |
| Irreversibility Accounting (Paper) | papers | 56 |
| OpenAI | projections | 36 |
| Human History | domains | 34 |
| The Structure of Agency (Derived) | papers | 34 |
| 2010-2026 Software Supply Chains | domains | 33 |
| 2008-2026 Financial Infrastructure | domains | 31 |
| Quantum Measurement | projections | 31 |
| Ontology of Irreversibility | papers | 29 |
| 2012-2026 AI Systems | domains | 29 |

**Interpretation:** High-link notes function as **reference hubs** or densely connected documents.

---

## 4. Diagnostics Inventory

### By Subfolder

| Location | Count | Total Links |
|----------|-------|-------------|
| diagnostics | 4 | 60 |
| diagnostics/irreversibility | 4 | 20 |

---

## 5. Projections Coverage

### Core Concept Linkage

| Projection | constraint_load | displacement | failure_modes | lens | residual | rollback |
|------------|---|---|---|---|---|---|
| Cosmology |yes|yes|no|no|yes|yes|
| Discordianism |yes|yes|yes|no|yes|yes|
| Enochian |yes|yes|no|no|yes|no|
| Fourth Way |yes|yes|no|no|yes|yes|
| Jung |yes|yes|no|yes|yes|yes|
| OpenAI |yes|yes|no|no|yes|yes|
| Plato's Republic |yes|yes|no|no|yes|yes|
| Quantum Measurement |yes|yes|no|no|yes|yes|
| Stoicism |yes|yes|no|no|yes|yes|
| Zen |yes|yes|yes|yes|yes|yes|

**All projections** link to: constraint_load, displacement, residual

---

## 6. Invariants Integrity

| Invariant | Role | Status | Canonical | Links |
|-----------|------|--------|-----------|-------|
| Attribution | invariant | structural | no | 4 |
| Decomposition | invariant | structural | no | 3 |
| Governance | invariant | structural | no | 4 |
| Irreversibility (Invariant) | invariant | structural | no | 13 |


---

## 7. Constraint-Load Summary

### Where cost accumulates


### Routing pressure points

1. **irreversibility** (14 links): High-dependency hub.
2. **feasible-set** (12 links): High-dependency hub.
3. **constraint-load** (11 links): High-dependency hub.

---

## 8. Recommended Actions

### High Priority (prevent accounting-failure)


---

## Appendix: Data Sources

This report synthesizes exports from Obsidian Bases CSV files.
Generated 2026-01-25.
