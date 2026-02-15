---
role: support
type: audit
status: draft
date: 2026-02-12
canonical: false
inputs:
  - "[[Spine Extraction Changelog]]"
  - "[[Spine Integration Opportunities]]"
  - "[[Attribution]]"
  - "[[Governance]]"
  - "[[Decomposition]]"
  - "[[Irreversibility (Invariant)]]"
---

# Four Invariants Spine Audit (2026-02-12)

> [!note]
> Scope: Audit of the *concept spines + diagnostics* for the four invariants, with emphasis on Attribution / Governance / Decomposition (Irreversibility is already mature).
>
> Non-goal: Retcon existing domain/projection analysis. Integration should be additive (new sections + links), per [[Spine Integration Opportunities]].

## 0) Inventory (source of truth)

The four invariants in this repo are:

- [[Governance]]: no actor may be exempt from constraints they impose.
- [[Irreversibility (Invariant)]]: persistent differences have non-local erasure cost under a declared transformation space.
- [[Decomposition]]: object/operator/boundary/accounting/governance roles must remain explicit and non-collapsed.
- [[Attribution]]: agency is layered; responsibility claims are role-dependent and must be bounded by degrees of freedom.

## 1) Spine extraction status (parity check)

Per [[Spine Extraction Changelog]]:

- New concepts exist for Attribution / Governance / Decomposition (28 total), bringing `concepts/` to 68 notes.
- New diagnostics exist for all three spines (checklist + signatures + boundaries).
- Invariant notes for all three were extended with “Minimal decomposition” and “Structural consequences”.
- The registry note includes the new concepts (grounded vocabulary is now present).

Observed in-vault:

- `concepts/`: 68 notes total.
- `diagnostics/attribution|governance|decomposition/`: checklist, failure signatures, stress tests & boundaries exist for each.

## 2) Audit criteria (what “good” means)

1. **Mechanical checkability**: violations should be detectable from explicit declarations + operator steps, not from interpretive inference.
2. **Cross-spine discipline**: spines can reference each other, but “Structural dependencies” should stay minimal and intentional.
3. **Operational grounding**: primitives should support an explicit operator question/test (even if the test is “enumerate X”).
4. **Misuse resistance**: each spine should state non-claims and boundary conditions to reduce diagnosis→prescription drift.
5. **Integration readiness**: existing content should have clear, minimal, additive link insertion points.

## 3) Attribution spine audit (focus)

### What’s solid

- The invariant statement is sharp and non-normative: layered agency + role-dependent responsibility + “maturity without structure is a trap” ([[Attribution]]).
- The spine has the right primitives and composites:
  - primitives: [[control-surface]], [[agency-layer]], [[degrees-of-freedom]]
  - first-order: [[responsibility-claim]], [[attribution-residual]], [[attribution-displacement]]
  - selector: [[attribution-admissibility]]
  - failure states: [[over-attribution]], [[under-attribution]], [[layer-collapse]]
- The diagnostic checklist cleanly enforces “declare surfaces/layers/dof → formulate claim → check admissibility” before classification.
- Stress tests explicitly warn against “blame-as-diagnosis” misuse.

### Gaps / risks

- **Integration debt (highest)**: major domain/projection notes still read “irreversibility-first” without explicit control-surface/agency-layer grounding. This is expected per [[Spine Integration Opportunities]], but it is now the main blocker to attribution being used in practice.
- **Representational ambiguity**: responsibility claims are “structured assertions” but not yet standardized as a reusable fill-in block across domains (the checklist contains one; domain templates don’t consistently require it).

### Next actions (minimal + additive)

- Add a reusable “Responsibility claims” block (copy from the checklist) into the domain diagnosis template so future domain notes can record attribution outputs without freeform prose.
- Apply the first wave of links to the high-priority targets named in [[Spine Integration Opportunities]] (AI Systems, Scope Patterns, Plato’s Republic, isomorphism).

## 4) Governance spine audit (focus)

### What’s solid

- The invariant statement is crisp and tool-applicable: “No actor may be exempt from constraints they impose” ([[Governance]]).
- The primitive set supports a concrete operator sequence:
  - primitives: [[constraint-surface]], [[exemption]]
  - first-order: [[constraint-reflexivity]], [[exemption-path]], [[governance-residual]]
  - accounting: [[enforcement-topology]], [[self-diagnosability]]
  - mechanism: [[silent-correction]]
  - failure states: [[interpretive-immunity]], [[authority-leakage]]
- The checklist’s failure classification matches the concept vocabulary (good closure).
- Stress tests call out reflexivity weaponization and “governance-as-power-struggle” misuse.

### Gaps / risks

- **Cross-spine exception (needs decision)**: [[interpretive-immunity]] has a structural dependency on [[agency-layer]]. This contradicts the strict reading of the extraction design rule (“cross-spine references go in Parallels, not Structural dependencies”), but was explicitly called out as intentional in [[Spine Extraction Changelog]].
  - Decision needed: either codify this as an allowed exception (“governance failure states may depend on attribution primitives”), or refactor so [[agency-layer]] is a parallel reference instead of a structural dependency.
- **Tooling alignment is partial**: governance in the compiler/lint stack is currently represented by a small number of rules (e.g., “missing role”), which does not yet operationalize the richer governance vocabulary (silent correction, self-diagnosability, enforcement topology).

### Next actions (minimal + additive)

- Decide and document the cross-spine dependency policy (either allow the exception explicitly, or remove it).
- Add 1–2 lint rules that operationalize governance vocabulary that’s already conceptually declared (e.g., detect auto-fix without witness emission on the tool side; detect unscoped exemptions in rulesets).

## 5) Decomposition spine audit (focus)

### What’s solid

- The invariant decomposition is explicit and enforceable in principle: objects/operators/boundaries/accounting/governance roles must not collapse ([[Decomposition]]).
- Concept vocabulary covers both the “what” and the “how it fails”:
  - primitive: [[role-boundary]]
  - selector: [[role-purity]]
  - accounting: [[decomposition-depth]], [[refinement-stability]]
  - first-order: [[function-merge]], [[scope-rigidity]]
  - failure states: [[role-collapse]], [[normativity-leak]]
- Diagnostics include the right misuse warnings: decomposition-as-gatekeeping, terminology policing.

### Gaps / risks

- **Enforcement depth**: the concepts explicitly reference lint/test/schema enforcement, but the ruleset coverage for role purity / normativity leak is not yet obviously mapped to the new vocabulary (the concept notes mention “existing lint rules”, but the mapping from rule → concept is not yet explicit in-vault).

### Next actions (minimal + additive)

- Make the mapping explicit: in the lint ruleset docs, list which constraints operationalize which decomposition concepts (at least for role purity + normativity leak).
- Add one “decomposition depth” marker: which layers are enforced mechanically vs socially for the vault and for the compiler (use the checklist’s output block).

## 6) Integration audit (where to apply the new spines next)

[[Spine Integration Opportunities]] is directionally correct; spot-checks show the priority files are still mostly irreversibility-grounded:

- `domains/2012-2026 AI Systems.md`: no explicit [[control-surface]] / [[constraint-surface]] / [[role-boundary]] grounding yet, despite natural insertion points.
- `meta/isomorphism.md`: frames isomorphism as “primarily about irreversibility”; it can now be expanded to “same invariants → same shapes” across all four invariants.
- `projections/Plato's Republic.md`: already discusses role collapse/capture; should link to [[role-boundary]] / [[role-collapse]] and optionally governance concepts for “single point of interpretive authority” failure.
- `meta/Scope Patterns.md`: already uses “degrees of freedom” language; decide whether to link it to attribution’s [[degrees-of-freedom]] or keep it domain-generic.

## 7) Minimal closure criteria (when this audit “passes”)

This audit should be considered “passing enough” when:

1. Cross-spine dependency policy is explicit (exception allowed or refactored).
2. At least one domain note and one projection note each have an additive “multi-spine grounding” section (no rewriting).
3. Lint/ruleset docs explicitly map a small subset of constraints to governance/decomposition concept vocabulary (so “mechanical enforcement” is not merely asserted).

