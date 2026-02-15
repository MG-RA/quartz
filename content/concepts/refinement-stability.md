---
aliases:
  - "refinement convergence"
  - "error class reduction"
layer: accounting
role: concept
canonical: true
invariants:
  - decomposition
---

# Refinement Stability

## Definition

**Refinement stability** is the property that adding structure to a system reduces the number of detectable error classes rather than shifting or creating new ambiguity. A system exhibits refinement stability when each decomposition step eliminates failure modes without introducing new ones of equal or greater severity.

Refinement stability is the accounting test for whether decomposition is productive: is the system converging toward fewer structural errors, or merely rearranging them? The [[Decomposition]] invariant's termination condition — "refinement is considered complete when adding new structure no longer removes new classes of errors" — is a direct application of refinement stability.

A system that lacks refinement stability may be actively refined (more concepts, sharper boundaries, deeper role separation) while its overall ambiguity remains constant or increases. This indicates that refinement is ornamental rather than structural.

## Structural dependencies

- [[decomposition-depth]]
- [[role-boundary]]

## What this is NOT

- Not convergence to zero errors (refinement stability means errors decrease, not that they disappear)
- Not simplification (a system can become more detailed while maintaining refinement stability, as long as each addition eliminates error classes)
- Not diminishing returns (diminishing returns is about effort; refinement stability is about whether the structural output improves)

## Structural role

Refinement stability is the accounting measure that determines when decomposition work is still productive. It constrains claims of "improvement": if adding structure does not reduce detectable error classes, the system has reached either its refinement ceiling or a structural misalignment. The diagnostic checks whether recent structural additions have eliminated error classes or merely redistributed them.

## Parallels

- Analogous to [[feasible-set]] as an accounting measure: feasible-set tracks which options remain available; refinement-stability tracks whether structural work is reducing the error space or merely reshaping it.
