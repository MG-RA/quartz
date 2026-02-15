---
layer: first-order
role: concept
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
---

# Scope

## Definition

A **scope** is an evaluation context: the bounded environment in which admissibility
is computed.

In this system, a scope is the unit of locality for:

- which constraints are active
- which permissions apply
- which accounting rules (erasure routing) exist
- which commitments/commits are in force

## Structural dependencies

- [[persistence]]
- [[transformation-space]]

## Structural role

Scope provides a boundary for admissibility contexts. A change in scope (or a widening
of scope reach) is a boundary event that can change the feasible set of admissible
operations.

## What this is NOT

- Not a namespace convention.
- Not an authority claim.
- Not the "global world state".
