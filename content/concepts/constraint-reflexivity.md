---
aliases:
  - "reflexive constraint"
  - "self-binding constraint"
layer: first-order
role: concept
canonical: true
invariants:
  - governance
---

# Constraint Reflexivity

## Definition

**Constraint reflexivity** is the structural property that constraints apply to their own authors, enforcers, and interpreters — not only to downstream participants. A [[constraint-surface]] is reflexive when the roles that create, maintain, or enforce rules are themselves subject to those rules through inspectable mechanisms.

Constraint reflexivity is the core structural requirement of the [[Governance]] invariant. Without it, a system can function locally but loses the ability to diagnose itself under scale, because the constraint-making apparatus becomes exempt from its own output.

Reflexivity does not require identical application. It requires that the application path is **inspectable and auditable** — that the system can verify whether constraint-makers are bound by the constraints they produce.

## Structural dependencies

- [[constraint-surface]]
- [[exemption]]

## What this is NOT

- Not equality (reflexivity does not require that all actors are treated identically; it requires that asymmetries are declared and auditable)
- Not self-reference (reflexivity is about constraint application, not about a system referring to itself in general)
- Not democracy (reflexivity is a structural property of constraint systems, not a political principle)
- Not completeness (a system can be reflexive in some constraint surfaces and not others)

## Structural role

Constraint reflexivity is the first-order property that separates governance from authority. Where reflexivity holds, correction is mechanical — violations can be detected by the same machinery that detects any other violation. Where reflexivity fails, correction requires overthrow rather than debugging. Every governance diagnostic checks reflexivity before evaluating enforcement topology.
