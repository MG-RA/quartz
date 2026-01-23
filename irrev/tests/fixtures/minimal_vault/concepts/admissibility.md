---
layer: selector
role: concept
canonical: true
note_kind: operator
---

# Admissibility

A selector operator that checks structural allowance.

## Input

- Candidate transition
- Current [[object-ok]]

## Output

Boolean: is the transition structurally allowed?

## Procedure

1. Check if candidate lies within feasible set
2. Verify no constraint violations
3. Return admissibility result

## Failure modes

- False positive: transition allowed but structurally incoherent
- False negative: transition disallowed but structurally valid

## Non-claims

This does not rank transitions by desirability or predict which will be chosen.

## Structural dependencies

- [[object-ok]]
