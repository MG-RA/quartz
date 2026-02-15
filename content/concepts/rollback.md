---
aliases:
  - "revert"
  - "undo"
layer: mechanism
role: concept
type: mechanism
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
note_kind: operator
---

# Rollback

## Definition
An operation that attempts to restore a prior state by reversing or undoing recent changes. Rollback assumes that the path from state A to state B can be traversed in reverse at comparable cost. In systems with persistent differences, rollback may restore local state while leaving propagated effects, displaced costs, and accumulated constraints intact—i.e., leaving [[residual|residuals]] behind. Rollback is the implicit mechanism behind correction narratives.

## Residuals

Rollback commonly leaves [[residual|residuals]] such as:
- propagated effects that are not undone (downstream references, caches, coordination states)
- displaced erasure work and responsibility ambiguity (cost lands elsewhere or later)
- compatibility and process residue that tightens [[constraint-load]] under repetition

## Structural dependencies
- [[persistent-difference]]
- [[propagation]]
- [[displacement]]
- [[residual]]

## What this is NOT
- Not undo (undo is a user-facing command; rollback is a system operation with structural implications)
- Not recovery (recovery may move forward to a new stable state; rollback specifically returns)
- Not reset (reset clears to initial conditions; rollback returns to a specified prior state)
- Not reversal (reversal undoes effects; rollback restores state, which may not undo all effects)

## Structural role
Constrains what "fixable" means. If rollback capacity is limited relative to persistent difference production, then correction narratives become incoherent at scale. Identifies: what does rollback actually restore, and what does it leave in place?
