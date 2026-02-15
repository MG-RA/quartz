---
aliases:
  - "enforcement shape"
  - "enforcement coverage"
layer: accounting
role: concept
canonical: true
invariants:
  - governance
---

# Enforcement Topology

## Definition

**Enforcement topology** is the actual shape of what is enforced in practice across a system's [[constraint-surface|constraint surfaces]]. It maps which constraints bind which actors through which mechanisms, revealing the gap between declared governance and operational governance.

Enforcement topology is an accounting concept because it requires enumeration: listing constraint surfaces, tracing their application paths, identifying [[exemption-path|exemption paths]], and mapping where [[constraint-reflexivity]] holds or fails. The result is a structural description of **where governance is real** versus where it is aspirational.

A system's enforcement topology may differ significantly from its declared governance. Rules may exist on paper but lack enforcement mechanisms. Enforcement may be selective. Tools may enforce constraints that are not declared as rules. Enforcement topology names the actual shape, not the intended one.

## Structural dependencies

- [[constraint-surface]]
- [[constraint-reflexivity]]

## What this is NOT

- Not policy (policy declares intent; enforcement topology describes what is actually enforced)
- Not organizational chart (org charts show authority relationships; enforcement topology shows constraint application paths)
- Not security model (security models describe access control; enforcement topology describes the full constraint enforcement landscape)

## Structural role

Enforcement topology is the accounting layer for governance. It makes governance auditable by requiring explicit enumeration of what is enforced, by whom, and through what mechanisms. Without enforcement topology, governance claims are unfalsifiable — they cannot be tested against operational reality.
