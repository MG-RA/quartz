---
aliases:
  - "isolation"
  - "segregation"
layer: mechanism
role: concept
type: mechanism
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
note_kind: operator
---

# Quarantine

## Definition

**Quarantine** is a containment operator-pattern that **isolates** a region, actor, or subsystem to limit [[propagation]] of a [[persistent-difference]], while deferring reintegration to a controlled process. Quarantine trades immediate spread for delayed coordination: it keeps the difference “somewhere” while the system figures out what can be rejoined and at what cost.

## Preconditions

- A separable region that can be isolated without immediate collapse of core function.
- A reintegration interface (rules for what can re-enter, when, and under what checks).

## State transition (schematic)

Exposed system → isolated region + gated reintegration

## Residuals

Quarantine commonly leaves [[residual|residuals]] such as:
- reintegration backlog and accumulated deltas that must be reconciled
- divergence in interfaces/assumptions between quarantined and non-quarantined regions
- displaced responsibility for monitoring and reintegration work

## Structural dependencies
- [[persistent-difference]]
- [[propagation]]
- [[constraint]]
- [[displacement]]
- [[residual]]

## What this is NOT

- Not deletion (quarantine preserves the isolated region; it does not erase it).
- Not denial (denial ignores; quarantine allocates a location and interface).
- Not permanence (quarantine is defined by a reintegration surface, even if it is never exercised).

## Accounting hooks

Quarantine is legible when reintegration work and divergence residue are tracked: what must be reconciled, who owns the check surface, and what constraints are being accumulated while isolation holds.

## Examples

- Technical: quarantining compromised machines; residuals include rebuild queues, credential rotation work, and reintegration drift.
- Institutions: isolating a failed program; residuals include exceptions, parallel processes, and later reconciliation conflicts.
- Epistemic: “set aside” a claim pending verification; residuals include attention structures and downstream citations that persist.
