---
aliases:
  - "bypass route"
  - "constraint bypass"
layer: first-order
role: concept
canonical: true
invariants:
  - governance
---

# Exemption Path

## Definition

**Exemption path** is a named route through which a specific actor or role bypasses a [[constraint-surface]] that binds other participants. It is the concrete instantiation of [[exemption]]: not the abstract possibility of asymmetric constraint application, but the specific mechanism by which it occurs.

Exemption paths may be explicit (declared exceptions in rules, documented overrides) or implicit (convenience features that silently skip enforcement, authority that is not subject to audit, tools that auto-correct instead of surfacing violations).

The governance diagnostic task is not to eliminate all exemption paths, but to make them **legible as exemptions** — visible, named, and subject to the same inspection machinery as any other system behavior.

## Structural dependencies

- [[exemption]]
- [[constraint-surface]]

## What this is NOT

- Not an error path (error paths handle failures within constraints; exemption paths bypass constraints entirely)
- Not an escape hatch (escape hatches are temporary and scoped; exemption paths can be permanent and invisible)
- Not a workaround (workarounds operate within constraints creatively; exemption paths remove constraint application)

## Structural role

Exemption path constrains claims of "uniform enforcement." Where exemption paths exist undeclared, enforcement topology is incomplete. The diagnostic task is to enumerate exemption paths and classify each as declared/auditable or implicit/invisible.

## Parallels

- Analogous to [[displacement]] but for constraint bypass rather than cost routing: displacement in irreversibility names where erasure work relocates; exemption path names where constraint application fails to reach.
