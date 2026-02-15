---
aliases:
  - "constraint exemption"
  - "governance exemption"
layer: primitive
role: concept
canonical: true
invariants:
  - governance
---

# Exemption

## Definition

**Exemption** is a path where [[constraint-surface]] application differs by actor or role — where the same rule binds some participants but not others. It is the operational test for governance failure: if a constraint applies asymmetrically without explicit, inspectable justification, an exemption exists.

Exemptions are not always violations. Some exemptions are declared, scoped, and subject to review. The governance invariant does not forbid exemptions categorically; it forbids **uninspectable** exemptions — those that cannot be named, audited, or challenged through the system's own mechanisms.

The critical distinction: misuse breaks rules visibly; exemption makes rules invisible for select actors. Misuse produces errors that can be caught. Exemption produces silence that cannot be diagnosed from within.

## Structural dependencies

- [[constraint-surface]]

## What this is NOT

- Not violation (violations break constraints; exemptions bypass them)
- Not exception handling (exception handling manages error paths; exemption removes actors from constraint paths entirely)
- Not privilege (privilege is a social concept; exemption is a structural description of asymmetric constraint application)
- Not delegation (delegation redistributes authority within constraints; exemption removes constraint application)

## Structural role

Exemption is the operational test for governance integrity, analogous to how [[erasure-cost]] tests persistence and [[degrees-of-freedom]] tests attribution. If an exemption path exists and cannot be inspected, the system cannot diagnose itself at that point. Governance diagnostics begin by checking for exemption paths, then evaluating whether each is declared and auditable.
