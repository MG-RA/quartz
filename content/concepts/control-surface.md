---
aliases:
  - "locus of control"
  - "control locus"
layer: primitive
role: concept
canonical: true
invariants:
  - attribution
---

# Control Surface

## Definition

**Control surface** is the declared set of transitions that a given role or actor can vary within a system. It specifies which degrees of freedom are accessible to whom, under what conditions, and within what boundaries.

A control surface is not the same as a permission set or an authority claim. It is the structural description of **what could actually be varied** by a role, independent of whether that variation is exercised, intended, or acknowledged. Where no control surface is declared, attribution claims are structurally underspecified.

## Structural dependencies

(none — primitive)

## What this is NOT

- Not authority (authority is a governance claim about who may act; control surface is the structural description of what can vary)
- Not capability (capability implies resources and readiness; control surface is about the space of possible variation, not the ability to execute)
- Not interface (interfaces are access points; control surfaces include the full set of transitions a role can produce, whether exposed or implicit)
- Not blame surface (control surface is descriptive, not evaluative)

## Structural role

Control surface constrains what attribution claims can mean. Any responsibility claim must specify the control surface within which the attributed role operated. If the claimed effect lies outside the role's control surface, the attribution is structurally invalid regardless of narrative plausibility.

## Parallels

- Analogous to [[transformation-space]] but for control rather than change: transformation-space declares what counts as "the same thing," control surface declares what a role can vary.
