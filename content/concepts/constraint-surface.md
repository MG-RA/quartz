---
aliases:
  - "enforcement interface"
  - "rule surface"
layer: primitive
role: concept
canonical: true
invariants:
  - governance
---

# Constraint Surface

## Definition

**Constraint surface** is the set of enforceable rules, interfaces, and mechanisms that actively bind actors within a system at a given layer. It names not the abstract existence of rules, but the **enforcement interface itself** — the point where constraints make contact with behavior.

A constraint surface differs from a [[constraint]] (a general restriction on transitions) and from a [[boundary]] (a scope delimiter). Constraint surface specifically names the enforceable shape of governance: what rules actually bind, who they bind, and through what mechanisms enforcement occurs.

The operational test: if removing this surface would change which actors are bound by which rules, it is a constraint surface. If it would only change documentation, it is not.

## Structural dependencies

(none — primitive)

## What this is NOT

- Not a constraint (constraints restrict transitions in general; constraint surfaces are the specific enforcement interfaces where governance contacts behavior)
- Not a boundary (boundaries delimit scope; constraint surfaces delimit enforcement)
- Not policy (policy is declared intent; constraint surface is the operational shape of what is actually enforced)
- Not architecture (architecture includes non-constraining structure; constraint surface is specifically the enforcement-carrying subset)

## Structural role

Constraint surface is the primitive that makes governance auditable. Without it, governance claims float free of mechanism. Every governance diagnostic must declare what constraint surfaces exist before evaluating whether they are reflexive, exemption-free, or topologically complete.
