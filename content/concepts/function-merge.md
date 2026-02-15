---
aliases:
  - "role absorption"
  - "function absorption"
layer: first-order
role: concept
canonical: true
invariants:
  - decomposition
---

# Function Merge

## Definition

**Function merge** is the process by which one structural role absorbs the function of another, producing an artifact or component that performs work belonging to two or more roles without maintaining [[role-boundary|role boundaries]] between them. It is the mechanism through which [[role-collapse]] occurs incrementally.

Function merges are often well-intentioned: an operator that "helpfully" embeds its own validation criteria, a diagnostic that "naturally" prescribes remediation, a governance constraint that "obviously" includes the rationale for its existence. Each individual merge may appear to add clarity or convenience. Accumulated, they produce artifacts whose structural function is indeterminate.

The key distinction from role collapse: function merge is the **process**, role collapse is the **state**. Detecting function merges early prevents role collapse from becoming entrenched.

## Structural dependencies

- [[role-boundary]]

## What this is NOT

- Not composition (composition coordinates distinct roles across boundaries; function merge eliminates the boundary)
- Not evolution (evolution can add new functions within a role; function merge absorbs functions from other roles)
- Not refactoring (refactoring reorganizes within constraints; function merge crosses role boundaries)

## Structural role

Function merge is detectable by tracking whether artifacts acquire structural functions beyond their declared role over time. Where an artifact's effective role expands beyond its declared [[role-boundary]], function merge has occurred. The diagnostic identifies which functions have been absorbed from which roles.

## Parallels

- Analogous to [[displacement]] but for structural function rather than cost: displacement relocates erasure work; function merge relocates structural function across role boundaries.
