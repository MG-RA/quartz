---
aliases:
  - "role separation"
  - "decomposition boundary"
layer: primitive
role: concept
canonical: true
invariants:
  - decomposition
---

# Role Boundary

## Definition

**Role boundary** is the declared separation between the five structural roles in the decomposition invariant: objects, operators, boundaries/scope, accounting/feedback, and governance/control. It names the specific interfaces where one role ends and another begins.

Role boundary delimits **what kind of structural work** an artifact, note, or component is allowed to perform. Objects describe; operators evaluate; boundaries scope; accounting tracks; governance constrains.

The operational test: if removing this boundary would allow an artifact to perform structural work belonging to a different role (e.g., a definition that prescribes, an operator that self-validates), it is a role boundary.

## Structural dependencies

(none — primitive)

## What this is NOT

- Not a module boundary (module boundaries separate implementation units; role boundaries separate structural functions)
- Not a permission boundary (permissions control access; role boundaries control structural function)
- Not a conceptual distinction (role boundaries must be mechanically enforceable, not merely intellectually recognized)
- Not rigid (role boundaries can be refined, but relaxation is a breaking change per the [[Decomposition]] invariant)

## Structural role

Role boundary is the primitive that makes decomposition auditable. Without declared role boundaries, decomposition is aspirational — roles can merge, normativity can leak into descriptions, and operators can accumulate authority without detection. Every decomposition diagnostic begins by identifying role boundaries and checking whether they hold.

## Parallels

- Specializes [[boundary]] for the decomposition context: boundary in general delimits scope; role boundary delimits structural function.
