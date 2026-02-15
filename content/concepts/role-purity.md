---
aliases:
  - "role integrity"
  - "role consistency"
layer: selector
role: concept
canonical: true
invariants:
  - decomposition
---

# Role Purity

## Definition

**Role purity** is a predicate that determines whether an artifact maintains its declared structural role without performing work belonging to a different role. An artifact is role-pure when:

- Objects describe without prescribing or evaluating.
- Operators evaluate without self-describing their authority or auto-correcting silently.
- Boundaries delimit scope without embedding evaluative logic.
- Accounting tracks without directing action.
- Governance constrains without interpreting results.

Role purity does not require absolute isolation — roles necessarily interact. It requires that each artifact's **primary structural function** remains within its declared [[role-boundary]]. An operator may reference objects, but an object must not embed operator logic.

## Structural dependencies

- [[role-boundary]]

## What this is NOT

- Not purity in a moral sense (role purity is about structural function, not cleanliness or virtue)
- Not isolation (pure roles interact across boundaries; purity means they don't absorb each other's functions)
- Not simplicity (a complex artifact can be role-pure if its complexity serves its declared role)

## Structural role

Role purity is the selector that filters well-formed artifacts from decomposition violations. It is the mechanical check for whether [[role-boundary|role boundaries]] hold at the artifact level. The lint rules for decomposition (object-operator separation, no prescriptive language in definitions) are implementations of role purity checks.

## Parallels

- Analogous to [[admissibility]] as a selector: admissibility determines which transitions are allowed in a transformation space; role purity determines which structural functions are allowed within a declared role.
