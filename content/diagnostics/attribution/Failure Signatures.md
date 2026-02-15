---
depends_on:
  - "[[Attribution]]"
role: diagnostic
type: signatures
canonical: true
---

# Attribution - Failure Signatures

> [!note]
> Scope: These are failure signatures of attribution analyses, not claims about the system under study.

Recurring diagnostic failures that appear across domains when applying the attribution invariant.

## 1) Blame without degrees of freedom

- Signature: responsibility is assigned without specifying what the role could have varied.
- Looks like: "they should have done X" without checking whether X was in the feasible set.
- Hidden: the role's actual control surface is never declared.

## 2) Intent substituted for control

- Signature: attribution is grounded in motive or character rather than degrees of freedom.
- Looks like: "they meant well / they should have known better."
- Hidden: whether the role controlled the relevant transitions is never examined.

## 3) Layer-collapsed responsibility

- Signature: causal, intentional, and governance responsibility are conflated in a single claim.
- Looks like: treating structural failures as personal moral failures.
- Hidden: the agency layer is never specified, so the claim is evaluated at the wrong level.

## 4) Structural effects attributed to individuals

- Signature: outcomes produced by rules, interfaces, or incentive structures are attributed to individual actors.
- Looks like: blame flows "downward" to visible actors while governance surfaces remain unexamined.
- Hidden: [[under-attribution]] at the governance layer and [[over-attribution]] at the individual layer.

## 5) Retrospective feasible-set inflation

- Signature: the set of options available to a role is evaluated retrospectively rather than at the time of action.
- Looks like: "they could have done otherwise" with the benefit of hindsight.
- Hidden: the actual degrees of freedom at the time are never enumerated.

## 6) Responsibility without control surface

- Signature: responsibility is asserted without declaring what the role controlled.
- Looks like: "someone is responsible" without specifying the mechanism of control.
- Hidden: the attribution claim is structurally incomplete and unfalsifiable.

## 7) Attribution displacement masking governance gaps

- Signature: responsibility is routed to individuals while governance-layer control surfaces remain unattributed.
- Looks like: a named individual is held accountable while the system that produced the failure is unexamined.
- Hidden: [[attribution-displacement]] from governance to individual layers.

## 8) Maturity narrative replacing structure

- Signature: responsibility gaps are explained by "immaturity" rather than structural analysis.
- Looks like: "they need to grow / the organization needs to mature."
- Hidden: the constraint landscape that produces the observed behavior is never examined.

## Links

- [[Attribution]]
- [[over-attribution]]
- [[under-attribution]]
- [[layer-collapse]]
- [[attribution-displacement]]
