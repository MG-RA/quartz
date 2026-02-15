---
aliases:
  - "authority accumulation"
  - "unaccounted authority"
layer: failure-state
role: concept
canonical: true
invariants:
  - governance
---

# Authority Leakage

## Definition

**Authority leakage** is a failure state in which authority accumulates at a [[constraint-surface]] without corresponding governance accounting. It occurs when a role's effective power over the system grows — through interpretive precedent, enforcement discretion, tooling control, or [[exemption-path|exemption paths]] — without that growth being tracked, declared, or subject to [[constraint-reflexivity]].

Authority leakage often looks fine locally: decisions are made, constraints are enforced, the system appears to function. The failure is that the distribution of authority has shifted without the governance mechanisms registering the shift. Over time, this produces a gap between declared governance and operational governance that can only be closed by means outside the system's own diagnostic capacity.

The structural signature: authority effects accumulate while governance accounting remains static.

## Structural dependencies

- [[exemption]]
- [[constraint-surface]]

## What this is NOT

- Not power (power is a general social concept; authority leakage is a specific structural failure of governance accounting)
- Not corruption (corruption implies intent; authority leakage can occur through mechanism drift without any actor intending it)
- Not scope creep (scope creep is about feature expansion; authority leakage is about untracked authority expansion)
- Not growth (an organization can grow without authority leaking; leakage is specifically about unaccounted authority accumulation)

## Structural role

Authority leakage is a failure state detectable by comparing declared [[enforcement-topology]] against observed authority effects. Where authority effects exceed what enforcement topology accounts for, authority has leaked. The governance diagnostic identifies where authority is being exercised outside of declared constraint surfaces.

## Parallels

- Analogous to [[accounting-failure]] but for authority rather than persistence: accounting-failure names untracked persistence; authority-leakage names untracked authority accumulation.
