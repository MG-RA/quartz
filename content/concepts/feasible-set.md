---
aliases:
  - "available option set"
  - "reachable options"
  - "feasible options"
layer: accounting
role: concept
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
note_kind: object
---

# Feasible Set

## Definition

The **feasible set** is the set of transitions (or configurations) that remain structurally available for a system within a declared [[transformation-space]], given current [[constraint|constraints]] and accumulated [[constraint-load]], including the non-local work implied by [[erasure-cost]] for removing [[persistent-difference|persistent differences]].

This is descriptive bookkeeping: it names what options remain *available* once constraints and erasure asymmetries are respected, without claiming what should be chosen.

## Structural dependencies
- [[transformation-space]]
- [[constraint]]
- [[constraint-load]]
- [[persistent-difference]]
- [[erasure-cost]]

## What this is NOT

- Not desirability (does not rank outcomes)
- Not policy or permission (does not assert legitimacy)
- Not feasibility-as-capacity (it is not a resource planning notion)
- Not optimism about rollback (does not assume reversibility is symmetric or local)

## Structural role

The feasible set is the object-level substrate that higher-level selectors can query (e.g., “is this transition still available?”). Under increasing [[constraint-load]] and rising marginal [[erasure-cost]], the feasible set typically shrinks, making apparent “options” functionally unavailable even if they remain rhetorically imaginable.
