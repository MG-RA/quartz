---
aliases:
  - "auto-correction"
  - "silent fix"
layer: mechanism
role: concept
canonical: true
invariants:
  - governance
---

# Silent Correction

## Definition

**Silent correction** is a mechanism by which a tool, process, or authority modifies system state to satisfy a [[constraint-surface]] without surfacing the violation that triggered the correction. The constraint is enforced, but the enforcement is invisible: no record of the violation exists, no diagnostic output is produced, and no actor is informed that a correction occurred.

Silent correction is structurally problematic because it converts governance from inspection into automation. Where violations are silently corrected, the system loses the ability to detect patterns of constraint stress, to evaluate whether the constraint itself is appropriate, and to diagnose whether [[exemption|exemptions]] are accumulating.

The failure is not that the correction is wrong. The failure is that it is **uninspectable**.

## Structural dependencies

- [[constraint-reflexivity]]
- [[exemption]]

## What this is NOT

- Not auto-formatting (auto-formatting is cosmetic and does not suppress violation signals; silent correction suppresses the signal itself)
- Not error recovery (error recovery handles failures within declared error paths; silent correction bypasses the error path entirely)
- Not linting with auto-fix (auto-fix that logs the violation before correcting is not silent; the "silent" qualifier is about whether the violation is surfaced)

## Residuals

Silent correction commonly leaves residuals such as:
- lost violation signals that would otherwise inform governance decisions
- patterns of constraint stress that become invisible to the diagnostic apparatus
- accumulated governance drift where rules are enforced but violations are never surfaced
- false confidence in system health based on absence of visible violations

## Structural role

Silent correction is a mechanism that degrades [[self-diagnosability]]. Where silent corrections operate, the system's ability to examine its own constraint surfaces is compromised: violations occur and resolve without leaving inspectable traces. The governance diagnostic checks for silent correction wherever tools interact with constraint surfaces.
