---
depends_on:
  - "[[Decomposition]]"
role: diagnostic
type: signatures
canonical: true
---

# Decomposition - Failure Signatures

> [!note]
> Scope: These are failure signatures of decomposition analyses, not claims about the system under study.

Recurring diagnostic failures that appear across domains when applying the decomposition invariant.

## 1) Operators smuggled into definitions

- Signature: a concept definition contains evaluative or prescriptive logic.
- Looks like: "this concept means you should..." or "the correct approach is..."
- Hidden: [[normativity-leak]] — the object role is performing operator work.

## 2) Descriptions that carry authority

- Signature: a descriptive artifact is treated as binding because of its clarity or provenance.
- Looks like: "the definition says X, therefore X is the rule."
- Hidden: [[function-merge]] — the object role has absorbed governance function through being well-written.

## 3) Diagnostics that prescribe

- Signature: diagnostic output is treated as an action mandate.
- Looks like: "the diagnostic found a problem, therefore we must do Y."
- Hidden: operator output has leaked into governance territory; the diagnostic's role boundary is violated.

## 4) Governance embedded in tools silently

- Signature: tooling makes governance decisions without surfacing them as governance.
- Looks like: auto-formatting, default selections, silent exclusions.
- Hidden: governance function is performed by tooling without being declared or auditable as governance.

## 5) Role declaration without enforcement

- Signature: artifacts declare roles in frontmatter but the roles are not mechanically checked.
- Looks like: `role: concept` in frontmatter but no lint rule validates the content against concept requirements.
- Hidden: decomposition is aspirational rather than structural; [[decomposition-depth]] is shallow.

## 6) Refinement that increases ambiguity

- Signature: adding new concepts, boundaries, or distinctions does not reduce error classes.
- Looks like: vocabulary grows but the same structural failures persist or new ones appear.
- Hidden: [[refinement-stability]] has failed; decomposition work is ornamental.

## 7) Scope rigidity masking structural problems

- Signature: legitimate work consistently triggers decomposition violations.
- Looks like: contributors repeatedly "violate" role boundaries when doing useful work.
- Hidden: [[scope-rigidity]] — the role boundaries are drawn incorrectly or too tightly, not the work.

## 8) Terminology inflation

- Signature: concepts proliferate without corresponding reductions in ambiguity.
- Looks like: every distinction gets its own concept file; the concept graph grows but diagnostic power does not.
- Hidden: decomposition depth increases without refinement stability.

## Links

- [[Decomposition]]
- [[role-collapse]]
- [[normativity-leak]]
- [[function-merge]]
- [[decomposition-depth]]
- [[refinement-stability]]
- [[scope-rigidity]]
