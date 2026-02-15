---
layer: first-order
role: concept
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
---

# Scope Change

## Definition

**Scope change** is a boundary operation: a transition from one scope to another where
distinctions can be erased and commitments can persist across domains.

Scope change is treated as an irreversibility boundary. The relevant question is not
intent, but structure: a boundary crossing can introduce loss of distinctions (an
implicit erasure surface) and can propagate persistent commitments into a wider
transformation space.

## Structural dependencies

- [[irreversibility]]
- [[erasure-cost]]
- [[displacement]]
- [[persistence]]
- [[transformation-space]]
- [[boundary-crossing]]
- [[scope]]
- [[witness]]

## Structural role

Scope change is the primitive that makes "domain boundary" a first-class admissibility
object. It is a witnessable event that can require explicit accounting when the change
widens or translates the space of interpretations.

Scope change does not assert that a boundary crossing is good or bad. It marks a
transition where irreversible effects can occur unless the boundary loss is accounted
within the admissibility system.

## Vocabulary (minimal)

- Boundary: a transition between scopes/domains.
- Scope change: a boundary event recorded in admissibility artifacts.
- Boundary loss: distinctions that may not survive the crossing.
- Accounting requirement: widen/translate boundary loss is inadmissible unless it is
  explicitly allowed and cost-routed.

## Example (.adm)

These examples demonstrate scope change as a boundary primitive with witnessable
outcomes and displacement accounting.

### Widen without accounting (inadmissible)

```adm
module test@1
depends [irrev_std@1]
scope main

scope_change main -> prod widen
query admissible
```

Witness facts include `scope_change_used` and `unaccounted_boundary_change`. The
displacement trace has no contributions because no accounting rule exists for the
boundary loss surface.

### Widen with accounting (admissible + displacement contribution)

```adm
module test@1
depends [irrev_std@1]
scope main

scope_change main -> prod widen
allow_scope_change main -> prod
scope_change_rule main -> prod cost 1 "risk_points" -> boundary_risk

query admissible
```

Witness facts include `scope_change_used` and the displacement trace includes a
contribution for the synthetic difference `boundary_loss:scope:main->scope:prod`
routed into `bucket:boundary_risk`.
