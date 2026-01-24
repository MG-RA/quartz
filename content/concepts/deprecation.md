---
aliases:
  - "sunset"
  - "phase-out"
layer: mechanism
role: concept
type: mechanism
canonical: true
note_kind: operator
---

# Deprecation

## Definition

**Deprecation** is an operator-pattern for withdrawing an interface, behavior, or practice by shifting it from “supported” to “legacy,” while maintaining partial compatibility long enough for dependents to adapt. Deprecation is not removal; it is the managed creation of a split semantics period.

## Preconditions

- A dependency graph where consumers can be identified or inferred.
- A transition path (alternate interface, replacement practice) that dependents can migrate toward.

## State transition (schematic)

Supported behavior â†’ legacy behavior + transition window â†’ removal (optional)

## Residuals

Deprecation typically leaves [[residual|residuals]] such as:
- compatibility shims and dual semantics
- long-lived “legacy” pathways that constrain future change
- displaced coordination cost to maintain partial support across time

## Structural dependencies
- [[persistent-difference]]
- [[propagation]]
- [[displacement]]
- [[constraint-load]]
- [[residual]]

## What this is NOT

- Not immediate deletion (deprecation introduces a staged transition surface).
- Not cleanup (cleanup erases; deprecation manages persistence while shifting burdens).
- Not enforcement (enforcement is governance; deprecation is an operator that changes support surfaces).

## Accounting hooks

Deprecation is legible when the shim surface and lingering legacy paths are tracked: what remains supported, what residual compatibility obligations persist, and how they contribute to [[constraint-load]].

## Examples

- Technical: API deprecation with a version window; residuals include shims, documentation drift, and split client behaviors.
- Institutions: phased policy withdrawal; residuals include grandfathered exceptions and parallel enforcement regimes.
- Epistemic: deprecating a term/claim; residuals include archival usage, citations, and partial semantic carryover.

