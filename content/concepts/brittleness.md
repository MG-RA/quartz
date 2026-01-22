---
aliases:
  - fragility
layer: failure-state
role: concept
type: failure-state
canonical: true
---

# Brittleness

## Definition

**Brittleness** is a system property in which small perturbations produce disproportionately large losses of function or options due to a scarcity of [[admissibility|admissible]] responses. Brittleness emerges when constraint load has narrowed the space of viable configurations such that the system lacks redundant ways to accommodate variation.

Unlike fragility, which breaks under increasing stress, brittleness concerns a **discontinuity between apparent stability and sudden failure**: the system continues to perform normally until a perturbation exceeds its remaining narrow tolerance, at which point recovery without significant reconfiguration becomes infeasible.

## Structural dependencies
- [[admissibility]]
- [[constraint-load]]

## What this is NOT

- Not fragility (fragility breaks easily; brittleness breaks abruptly after appearing stable)
- Not rigidity (rigidity resists change; brittleness fails under change it cannot absorb)
- Not weakness (weakness concerns capacity; brittleness concerns failure mode)
- Not instability (instability manifests as visible drift or oscillation; brittleness conceals degradation until failure)
- Not risk exposure (risk is probabilistic; brittleness is structural)

## Structural role

Brittleness names one failure state produced by constraint accumulation. When brittleness increases, a system's tolerance for perturbation shrinks even if surface performance remains unchanged. The diagnostic question is whether the system retains **multiple admissible responses to variation**, or whether continued stability depends on avoiding a narrow and increasingly fragile set of conditions.
