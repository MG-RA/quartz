# Saturation

Tags: #concept #failure-state

Layer: failure-state → [[admissibility]] (selector)

## Definition

**Saturation** is a system state in which constraint load has exhausted the available configuration space, leaving no [[admissibility|admissible]] room for further adaptation without first removing existing constraints. In a saturated state, a system may continue operating, but it cannot change direction, absorb new requirements, or respond meaningfully to novel conditions. Action collapses into maintenance: continued function is possible, but strategic movement requires **discontinuous restructuring** that pays down accumulated erasure costs.

## Structural dependencies
- [[constraint-load]]
- [[admissibility]]
- [[erasure-cost]]

## What this is NOT

- Not capacity limit (capacity limits concern throughput; saturation concerns admissible option space)
- Not exhaustion (exhaustion depletes resources; saturation depletes configurations)
- Not stagnation (stagnation is lack of change; saturation is inability to change)
- Not equilibrium (equilibrium is a balanced state; saturation is maximal constraint with no remaining slack)

## Structural role

Saturation names one of the terminal failure states produced by constraint accumulation, alongside brittleness. Where saturation is present, adaptation is impossible without first reducing constraint load, which requires confronting accumulated erasure costs directly. The diagnostic question is whether a system has ceased moving because it has _arrived_, or because it has become **structurally unable to move at all**.
