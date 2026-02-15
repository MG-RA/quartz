---
depends_on:
  - "[[Decomposition]]"
role: diagnostic
type: boundaries
canonical: true
---

# Decomposition - Stress Tests & Boundaries

> [!warning]
> Misuse risk: Turning decomposition analysis into gatekeeping or terminology policing.

## Where the decomposition lens does not help

- The system is genuinely simple enough that all roles are trivially visible and non-overlapping.
- The artifact is exploratory or draft-state and has not committed to a structural role.
- The system does not claim structural coherence (informal notes, brainstorming artifacts).
- Decomposition analysis is being used to reject contributions on terminological grounds rather than structural ones.

## Apparent counterexamples (brief)

- Tutorials: tutorials necessarily mix description and instruction. Decomposition analysis applies to the underlying concepts referenced, not to the tutorial itself (which has its own role).
- Working drafts: drafts may legitimately contain mixed roles as part of a refinement process. The diagnostic question is whether the draft is converging toward role purity, not whether it currently exhibits it.
- Small systems: in very small systems, role separation may be overkill. The termination condition applies: if adding decomposition does not eliminate error classes, it is ornamental.

## Misuse patterns

- Using decomposition to reject contributions that violate role boundaries rather than helping them converge.
- Treating role purity as a test of quality rather than a structural property (well-written mixed artifacts are still structurally problematic; poorly-written pure artifacts are still structurally sound).
- Over-decomposing: creating new roles and boundaries past the point where they eliminate error classes.
- Terminology policing: insisting on specific vocabulary when the structural function is clear.
- Decomposition as gatekeeping: using structural requirements to exclude participants rather than to maintain system coherence.

## Links

- [[Decomposition]]
- [[role-boundary]]
- [[role-purity]]
- [[scope-rigidity]]
- [[refinement-stability]]
