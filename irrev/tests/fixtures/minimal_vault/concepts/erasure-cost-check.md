---
layer: selector
role: concept
canonical: true
note_kind: operator
---

# Erasure Cost Check

A descriptive operator for quantifying erasure requirements.

## Input

- Persistent difference to be removed
- System context

## Output

Work required for erasure (time, coordination, resources).

## Procedure

1. Identify all dependencies on the persistent difference
2. Enumerate required state changes for removal
3. Calculate coordination overhead
4. Sum total non-local work
5. Report erasure cost breakdown

## Failure modes

- Underestimation: hidden dependencies missed
- Boundary error: incomplete system context

## Non-claims

This does not prescribe whether erasure should occur.
This does not optimize erasure strategies.

## Structural dependencies

- [[primitive-ok]]
