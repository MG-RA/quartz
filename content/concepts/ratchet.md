---
aliases:
  - "one-way tightening"
  - "lock-in"
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

# Ratchet

## Definition

A **ratchet** is an operator-pattern that makes certain transitions effectively one-way: constraints can tighten, commitments can accumulate, and degrees of freedom can be consumed, while reversal requires discontinuous coordination and cost. A ratchet does not require explicit intent; it can emerge from repeated local “reasonable” moves that each add structure.

## Preconditions

- A mechanism that preserves additions more easily than removals (structural [[asymmetry]]).
- A way for constraints to accumulate without being paid down locally.

## State transition (schematic)

Low constraint load → higher constraint load (reversal requires non-local work)

## Residuals

Ratchets typically leave [[residual|residuals]] as:
- accumulated commitments and compatibility obligations
- rising [[constraint-load]] that narrows future options
- displaced erasure work into future coordination

## Structural dependencies
- [[constraint]]
- [[asymmetry]]
- [[erasure-cost]]
- [[constraint-load]]
- [[residual]]

## What this is NOT

- Not progress (ratcheting can coincide with improvement, but names the structural one-wayness).
- Not a failure state (ratchets can operate under “normal” function).
- Not irreversibility itself (ratchet is a mechanism that tends to produce it).

## Accounting hooks

Ratchets become legible when additions and removals are tracked symmetrically: what constraints were added, what would removal require, and where would erasure work land if reversal were attempted.

## Examples

- Technical: accumulating feature flags/config branches that never retire, leaving long-lived routing and test-surface residue.
- Institutions: policy exceptions that persist as precedents, creating a one-way growth of special cases.
- Personal: commitments that accumulate coordination obligations (calendars, dependents), narrowing feasible future moves.
