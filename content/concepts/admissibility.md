---
aliases:
  - "what remains available"
layer: selector
role: concept
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
note_kind: operator
---

# Admissibility

## Definition

**Admissibility** is a structural **selector / predicate** applied to a proposed transition (or explanation): *is this move still allowed by the current structure?*

Operationally, admissibility is the check “does this candidate move lie inside the current [[feasible-set|feasible set]]?” It does not rank options by desirability or predict which will be chosen. It identifies which options remain structurally coherent—and which have been foreclosed by accumulated constraints.

> [!note]
> Non-claim: Admissibility does not rank options by desirability or predict which will be chosen.

## Structural dependencies
- [[feasible-set]]
- [[constraint]]
- [[constraint-load]]

## What this is NOT

- Not possibility (possibility ignores constraints; admissibility respects them)
- Not desirability (desirability ranks by value; admissibility is structural)
- Not optimality (optimality seeks the best; admissibility identifies the available)
- Not legality (legality is rule-based; admissibility is constraint-based)
- Not feasibility (feasibility concerns capacity; admissibility concerns structural allowance)

## Structural role

Admissibility is the selector that lenses enforce. A [[lens]] does not directly constrain the world; it filters interpretations, narratives, and proposed transitions by whether they respect the admissibility rules derived from underlying structure.

When [[constraint-load]] increases, the [[feasible-set|feasible set]] shrinks and fewer candidate moves remain admissible. When [[collapse-surface|collapse surfaces]] are approached, entire regions of the feasible set disappear. The diagnostic question is: *What remains admissible here, and what has been foreclosed?*
