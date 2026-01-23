---
role: support
type: standard
canonical: true
facets:
  - meta
  - diagnostic
---

# Operator Notes (Standard)

This vault uses an explicit **object / operator** split to prevent concept drift and layer leakage.

> [!note]
> Non-claim: This is a writing/typing convention for vault hygiene, not a new primitive or a prescription.

## Object vs operator

### Object notes (descriptive)

Object notes name structures in the world-model (what exists regardless of diagnosis).

- Noun-like: constraints, costs, sets, states, accumulations
- Should depend only downward (structural substrate)
- Example: [[feasible-set]] (object-level substrate)

### Operator notes (procedural / predicates)

Operator notes name **tests** applied to candidate moves or explanations.

- Verb/predicate-like: checks, selectors, evaluations
- May depend on objects freely (they consume the substrate)
- Example: [[admissibility]] (selector/predicate over [[feasible-set]])

## Minimal typing convention

Use frontmatter to declare kind:

- `note_kind: object`
- `note_kind: operator`

The linter enforces: **object notes must not depend on operator notes**.

## Operator note shape (recommended)

Operator notes should be written so the “test” is explicit and audit-friendly:

- `## Input` (what objects are required)
- `## Output` (what the operator returns / classifies)
- `## Procedure` (how the check is applied)
- `## Failure modes` (false positives/negatives, common misuse)
- `## Non-claims` (what the operator does not do)
- `## Structural dependencies` (object concepts only, where possible)

## Example seam

- [[feasible-set]]: the object-level set of transitions/configurations that remain structurally available under constraints and erasure costs.
- [[admissibility]]: the selector/predicate “is this candidate move inside the feasible set?” (optionally with context-specific gates).
## Related invariants (optional)

- [[Decomposition]]
- [[Governance]]
- [[Attribution]]
