---
aliases:
  - "role merger"
  - "decomposition collapse"
layer: failure-state
role: concept
canonical: true
invariants:
  - decomposition
---

# Role Collapse

## Definition

**Role collapse** is a failure state in which distinct structural roles merge, producing artifacts that simultaneously describe, evaluate, prescribe, or govern without maintaining [[role-boundary|role boundaries]]. When roles collapse, the structural function of an artifact becomes ambiguous — it is unclear whether it is stating a fact, evaluating a claim, or directing action.

Role collapse is the primary failure mode that the [[Decomposition]] invariant exists to prevent. It can occur through:

- Operators embedded in object definitions ("this concept means you should...").
- Descriptions that carry implicit authority ("the correct interpretation is...").
- Governance logic embedded in diagnostic output (prescriptions disguised as diagnosis).
- Accounting that directs action instead of tracking state.

Role collapse is not merely imprecise — it is structurally destabilizing, because once roles merge, subsequent refinement cannot distinguish between clarifying a description and changing a prescription.

## Structural dependencies

- [[role-boundary]]

## What this is NOT

- Not complexity (a system can be complex with clear role boundaries; collapse is specifically about boundary failure)
- Not integration (integration coordinates across boundaries; collapse eliminates boundaries)
- Not pragmatism (pragmatic shortcuts that preserve role boundaries are not collapse; shortcuts that merge roles are)

## Structural role

Role collapse is a failure state detectable by checking whether an artifact's content crosses its declared [[role-boundary]]. Where an object note contains evaluative logic, or an operator note contains self-justifying authority, role collapse has occurred. The decomposition diagnostic identifies which role boundaries have failed and what structural functions have merged.

## Parallels

- Analogous to [[collapse-surface]] but for structural roles rather than option space: collapse-surface names where options disappear discontinuously; role-collapse names where structural distinctions disappear, making decomposition indeterminate.
