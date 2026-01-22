# Decomposition Map and Structural Clarifications

Tags: #meta #architecture #diagnostic

## Purpose

This document captures a **structural decomposition pass** over the irreversibility work.
Its role is to:

- Make explicit which notions are **primitive**, **composed**, or **instrumental**
- Clarify the relationship between *irreversibility*, *lenses*, and *admissibility*
- Prevent conceptual drift as the repository matures
- Serve as a reference for future refactors (concept notes, kernel design, tooling)

This is not a new theory or extension of scope. It is a **reverse-engineering document**: a record of what the work already assumes once stripped of metaphor and narrative compression.

---

## 1. Core Clarification

The central clarification is the following:

> The irreversibility lens is not primitive. It is a **composed lens** whose admissibility rules are derived from irreversibility structure.

This implies three distinct layers:

1. **Structural conditions** (what exists regardless of diagnosis)
2. **Selectors** (what transitions are admissible under those conditions)
3. **Lenses** (mechanisms that enforce selectors over interpretation)

Much prior confusion came from collapsing these layers into single terms.

---

## 2. Primitive Concepts (Irreducible)

The following concepts are treated as **structural primitives**.
They cannot be decomposed further without losing explanatory power, and they do not presuppose the existence of a lens.

### 2.1 Difference

A detectable distinction under a specified transformation space.

### 2.2 Persistence

A difference that remains re-identifiable across relevant transformations.

### 2.3 Erasure Cost

The resources required to eliminate a persistent difference.

### 2.4 Asymmetry

The fact that creation and erasure of differences have unequal costs.

### 2.5 Constraint

A restriction on the set of admissible transitions.

### 2.6 Accumulation

The stacking of constraints such that they do not cancel or dissipate locally.

These primitives apply across physical, biological, informational, institutional, and economic domains.

---

## 3. First-Order Composites (Structural Conditions)

These concepts are **composed directly from primitives** and describe system conditions rather than interpretive tools.

### 3.1 Irreversibility

Irreversibility = Persistence + Erasure Cost Asymmetry

It is a **structural property**, not a process, value, or ontology of time.

### 3.2 Constraint Accumulation

Accumulation of constraints over time due to non-symmetric erasure.

### 3.3 Displacement

Redistribution of erasure costs across agents, subsystems, layers, or time horizons.

### 3.4 Constraint Load

The effective burden imposed by accumulated constraints on future admissible transitions.

These describe *what happens* structurally, independent of whether anyone accounts for it.

---

## 4. Accounting-Level Composites (Failure Detection)

These concepts only arise **once irreversibility exists** and are specifically about diagnostic failure.

### 4.1 Tracking Mechanism

Any system capable of assigning, localizing, or recording persistent effects and their erasure costs.

### 4.2 Accounting Failure

The absence or insufficiency of tracking mechanisms in systems producing persistent differences.

### 4.3 Collapse Surface

A region of the admissibility space where accumulated constraints sharply eliminate viable transitions.

These are the *subjects* of the papers. Irreversibility is upstream; accounting failure is the focus.

---

## 5. Selector-Level Concept: Admissibility

### 5.1 Definition (informal)

**Admissibility** refers to whether a transition, explanation, or action is structurally allowed once constraints are respected.

Admissibility is:

- Not possibility
- Not desirability
- Not optimality

It is a **structural selector**.

### 5.2 Role

Admissibility determines:

- Which explanations remain coherent
- Which transitions remain viable
- Which paths are false-open vs real

Admissibility is always relative to a set of constraints.

---

## 6. Lenses (Second-Order Constructs)

A **lens** is not primitive.
It is an **instrument** built on top of admissibility.

### 6.1 Lens (general)

A lens is a constrained transformation layer that:

- Takes inputs (observations, narratives, events)
- Applies admissibility rules
- Produces reduced representations suitable for diagnosis or action

Lenses:

- Discard degrees of freedom
- Enforce resolution limits
- Exhibit characteristic failure modes
- Require calibration and maintenance

### 6.2 Irreversibility Lens (composed)

The irreversibility lens is a lens whose admissibility rules are defined by irreversibility structure.

It rejects:

- Explanations that assume symmetric rollback
- Accounts that ignore persistence
- Narratives that erase displaced costs

It does not prescribe action. It enforces coherence.

---

## 7. Multi-Lens Admissibility Lattice

### 7.1 Structural Description

A **multi-lens admissibility lattice** is a directed structure where:

- Nodes represent system states as seen through one or more lenses
- Edges represent admissible transitions
- Direction reflects irreversibility gradients
- Edge weight reflects erasure, coordination, or constraint costs

This is not a state space or optimization landscape.

### 7.2 What It Is Not

- Not a simulator
- Not a predictor
- Not a planner
- Not a value-ranking system

### 7.3 What It Is For

- Identifying false-open paths
- Detecting collapse surfaces
- Comparing relative loss of admissibility
- Understanding cross-domain constraint propagation

---

## 8. Collapse Kernel (Implementation Target)

The **collapse kernel** refers to the minimal runtime machinery required to:

- Track admissible transitions
- Record constraint accumulation
- Detect saturation and collapse surfaces
- Maintain lens separation without collapsing domains

The kernel:

- Does not decide
- Does not optimize
- Does not recommend

It answers one question only:

> Which transitions are no longer structurally admissible?

---

## 9. Implementation Implications for the Repository

### 9.1 Concept Notes

- Add concept notes for:
  - `irreversibility` (minimal, structural)
  - `admissibility`
  - `lens`
- Explicitly mark composed concepts as such in their notes

### 9.2 Documentation Discipline

- Avoid treating lenses as primitives
- Avoid treating irreversibility as explanatory rather than conditional
- Keep accounting as the explicit subject

### 9.3 Future Work Guardrails

If future additions:

- Introduce values → they belong outside the diagnostic layer
- Rank paths → they exceed admissibility
- Predict futures → they exceed scope

They should be flagged as out-of-layer extensions.

---

## 10. One-Line Hierarchy (for orientation)

Persistence → Irreversibility → Constraints → Admissibility → Lenses → Diagnosis

Anything that violates this ordering is suspect.

---

## 11. Structural Definition of Maintenance

**Maintenance** is defined structurally, not procedurally:

> Maintenance = any change that alters reference topology, layer designation, or invariant phrasing.

Under this definition:

- Timestamps and change logs are *evidence* of maintenance, not requirements
- A change log is an *accounting surface*, not a workflow
- The framework remains non-operational while gaining traceability

This prevents Failure Mode #10 (failure to apply the lens to itself) from sliding into process prescription.

---

## Status

This document is a structural reference. It should be updated when:

- New primitives are proposed
- Layer boundaries are contested
- The kernel design evolves
- Reference topology, layer designation, or invariant phrasing changes (per §11)
