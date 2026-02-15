---
aliases:
  - "attribution claim"
  - "responsibility assignment"
layer: first-order
role: concept
canonical: true
invariants:
  - attribution
---

# Responsibility Claim

## Definition

**Responsibility claim** is a structured assertion that a specific role, operating at a declared [[agency-layer]], controlled the [[degrees-of-freedom]] relevant to a given effect. It is the basic unit of attribution: an explicit binding of role, layer, control, and outcome.

A well-formed responsibility claim must specify:

1. The role or actor being attributed.
2. The agency layer at which the claim is evaluated.
3. The degrees of freedom the role controlled.
4. The effect being attributed.

Claims that omit any of these components are structurally incomplete. Claims where the effect falls outside the role's degrees of freedom are structurally invalid.

## Structural dependencies

- [[degrees-of-freedom]]
- [[agency-layer]]

## What this is NOT

- Not blame (responsibility claims are structural bindings, not moral evaluations)
- Not causation alone (causal contribution without control specification is not a responsibility claim)
- Not narrative (a plausible story about who "should have" acted differently is not a responsibility claim unless it specifies layer, degrees of freedom, and control surface)
- Not exclusive (multiple responsibility claims can validly apply to the same effect at different layers)

## Structural role

Responsibility claim is the first-order composite that makes attribution auditable. Without explicit responsibility claims, attribution collapses into narrative convenience — effects get assigned to visible actors regardless of control. The diagnostics for [[over-attribution]], [[under-attribution]], and [[layer-collapse]] operate on responsibility claims as their input.

## Parallels

- Analogous to [[persistent-difference]] as a first-order composite: persistent-difference names what remains re-identifiable in a transformation space, responsibility-claim names what can be re-identified in a control surface.
