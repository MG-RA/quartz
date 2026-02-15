---
aliases:
  - "separation depth"
  - "role articulation depth"
layer: accounting
role: concept
canonical: true
invariants:
  - decomposition
---

# Decomposition Depth

## Definition

**Decomposition depth** measures how many layers of structural role separation are explicitly maintained and mechanically enforced in a system. It is the accounting measure for decomposition: not just whether roles are declared, but how deeply the separation is realized in practice.

A system with shallow decomposition depth may declare role boundaries but enforce them only at the top level. A system with deep decomposition depth maintains role separation through multiple layers: conceptual definitions are role-pure, operators declare their inputs and outputs, diagnostics are separate from prescriptions, and governance mechanisms are themselves subject to governance.

Decomposition depth is bounded: beyond the point where adding separation no longer eliminates new classes of errors, further decomposition is ornamental (per the [[Decomposition]] invariant's termination condition).

## Structural dependencies

- [[role-boundary]]

## What this is NOT

- Not complexity (deep decomposition can be simple; shallow decomposition can be complex)
- Not granularity (decomposition depth is about role separation, not about how finely concepts are divided)
- Not hierarchy (depth measures enforcement layers, not authority levels)

## Structural role

Decomposition depth is the accounting measure that determines whether decomposition is structurally real or aspirational. A system's decomposition depth can be assessed by counting how many levels of role separation survive under mechanical enforcement. Where decomposition depth is shallow, [[role-collapse]] and [[normativity-leak]] are more likely to accumulate undetected.
