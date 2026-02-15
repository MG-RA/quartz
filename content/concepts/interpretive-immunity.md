---
aliases:
  - "uninspectable authority"
  - "interpretive exemption"
layer: failure-state
role: concept
canonical: true
invariants:
  - governance
---

# Interpretive Immunity

## Definition

**Interpretive immunity** is a failure state in which a role that interprets, enforces, or authors constraints cannot itself be inspected or evaluated by the system's governance mechanisms. The role operates within the [[constraint-surface]] as an enforcer but exists outside it as a subject.

Interpretive immunity is the most structurally dangerous form of [[exemption]] because it is self-reinforcing: the role that cannot be inspected is often the same role that determines what counts as a valid inspection. Once interpretive immunity is established, the system cannot detect it from within — diagnosis requires a perspective that the immune role does not control.

Common instantiations: an author whose notes are exempt from lint, a tool whose behavior cannot be audited by the same diagnostics it runs on others, an authority whose interpretations are treated as definitional rather than evaluable.

## Structural dependencies

- [[exemption]]
- [[agency-layer]]

## What this is NOT

- Not expertise (expertise is a capacity; interpretive immunity is a structural exemption from inspection)
- Not trust (trust is a social stance; interpretive immunity is a governance architecture failure)
- Not authority (authority can be inspectable; interpretive immunity means the authority cannot be inspected)

## Structural role

Interpretive immunity is a failure state detectable by checking whether any role that operates on [[constraint-surface|constraint surfaces]] is itself exempt from those surfaces. Where interpretive immunity exists, [[self-diagnosability]] is compromised at that point. The governance diagnostic identifies which roles have interpretive immunity and what constraint surfaces they are exempt from.
