---
depends_on:
  - "[[Governance]]"
role: diagnostic
type: signatures
canonical: true
---

# Governance - Failure Signatures

> [!note]
> Scope: These are failure signatures of governance analyses, not claims about the system under study.

Recurring diagnostic failures that appear across domains when applying the governance invariant.

## 1) Exemption by automation

- Signature: tools silently correct violations instead of surfacing them.
- Looks like: "no violations found" when violations were auto-resolved.
- Hidden: the violation signal was consumed by the tool, not eliminated by the system.

## 2) Reflexivity gap

- Signature: constraints apply to all participants except the constraint author.
- Looks like: lint rules that don't apply to "core" notes, audit processes that skip the auditor.
- Hidden: the author's artifacts operate in an uninspected space.

## 3) Expert exception accumulation

- Signature: exemptions are granted on the basis of expertise without auditable justification.
- Looks like: "the expert knows what they're doing" as grounds for bypassing constraints.
- Hidden: [[interpretive-immunity]] accretes incrementally without governance accounting.

## 4) Enforcement topology drift

- Signature: declared governance diverges from operational governance over time.
- Looks like: rules exist on paper but are not mechanically enforced; enforcement is selective.
- Hidden: the gap between declared and operational governance is not itself tracked.

## 5) Authority leakage through interpretation

- Signature: a role that interprets rules gains effective authority through precedent.
- Looks like: interpretive decisions become de facto binding without governance review.
- Hidden: authority accumulates at the interpretation layer without corresponding accountability.

## 6) Governance as compliance theater

- Signature: governance mechanisms exist but produce no actionable output.
- Looks like: audits run, reports are filed, nothing changes.
- Hidden: the governance mechanism is not connected to enforcement; it tracks without binding.

## 7) Self-diagnosability loss

- Signature: governance failures can only be detected by external parties.
- Looks like: internal tools see no problems; external observers see systemic issues.
- Hidden: the diagnostic apparatus has an [[exemption-path]] that covers the failure.

## 8) Silent correction masking constraint stress

- Signature: auto-corrections prevent violation signals from reaching governance surfaces.
- Looks like: the system appears healthy because problems are silently resolved.
- Hidden: patterns of constraint stress that would indicate needed governance changes are invisible.

## 9) Governance residual after restructuring

- Signature: authority effects from prior governance regimes persist after changes.
- Looks like: "we changed the rules but behavior hasn't changed."
- Hidden: [[governance-residual|governance residuals]] from the prior regime are still operative.

## 10) Governance self-exemption

- Signature: the governance framework treats itself as exempt from its own diagnostic.
- Looks like: the meta-level is assumed to be correct because it defines correctness.
- Hidden: the governance apparatus has accumulated [[interpretive-immunity]].

## Links

- [[Governance]]
- [[exemption]]
- [[exemption-path]]
- [[constraint-reflexivity]]
- [[interpretive-immunity]]
- [[authority-leakage]]
- [[silent-correction]]
- [[governance-residual]]
