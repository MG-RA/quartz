---
aliases:
  - "attribution validity check"
  - "responsibility admissibility"
layer: selector
role: concept
canonical: true
invariants:
  - attribution
---

# Attribution Admissibility

## Definition

**Attribution admissibility** is a predicate that determines whether a [[responsibility-claim]] is structurally valid. A responsibility claim is admissible if and only if:

1. The attributed role's [[control-surface]] is declared.
2. The [[agency-layer]] at which the claim is evaluated is specified.
3. The [[degrees-of-freedom]] available to the role include the effect being attributed.
4. The effect falls within the role's control surface at the declared layer.

Claims that fail any of these conditions are inadmissible — not necessarily wrong, but structurally underspecified to the point of being unevaluable.

## Structural dependencies

- [[responsibility-claim]]
- [[degrees-of-freedom]]
- [[agency-layer]]

## What this is NOT

- Not a truth test (admissibility checks structural well-formedness, not whether the attribution is factually correct)
- Not a moral filter (inadmissible claims are structurally incomplete, not morally invalid)
- Not a permission gate (admissibility does not determine who is allowed to make responsibility claims)

## Structural role

Attribution admissibility is the selector that filters structurally valid responsibility claims from underspecified or invalid ones. It operates on responsibility claims the same way [[admissibility]] operates on transitions in transformation space: it determines what can be meaningfully evaluated, not what is true.

## Parallels

- Analogous to [[admissibility]] but for responsibility claims rather than state transitions: admissibility in irreversibility determines which transitions are allowed in a transformation space; attribution admissibility determines which responsibility claims are structurally evaluable.
