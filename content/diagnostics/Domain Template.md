# Domain Template

Tags: #diagnostic #template

Apply the lens to a specific domain **without introducing new concepts**. Definitions come from `/concepts`. Domain facts must be tagged as (Assumption) unless directly provided.

> [!note]
> Diagnosis only: this template constrains interpretation; it does not recommend actions or outcomes.

---

## 0) Scope and boundary

- **Domain:** (what system are we analyzing?)
- **Boundary:** (what is inside vs outside?)
- **Time window:** (start/end)
- **Resolution:** (events, institutions, regions, organizations, individuals?)

## 1) Transformation space

State the relevant [[transformation-space]]: what counts as "the same thing" after change, and what transformations are allowed when testing persistence?

## 2) Candidate differences (instances, not new primitives)

List domain-specific differences you will track. For each, fill:

- **Difference:** (Assumption)
- **Persistence test:** is it re-identifiable across the transformation space? (Inference)
- **If removal is claimed:** where does [[erasure-cost]] land? (Inference)
- **Erasure asymmetry:** what is easier, creation or erasure? [[erasure-asymmetry]] (Inference)

## 3) Persistence and cost routing

For each persistent difference:

- **Tracking mechanism:** does a [[tracking-mechanism]] exist? (Assumption/Inference)
- **Displacement:** is cost routed elsewhere? [[displacement]] (Inference)
- **Absorption:** where is cost paid locally (if anywhere)? [[absorption]] (Inference)
  - *Visibility check:* What persistence was absorbed locally and therefore rendered invisible? (Absorption is structurally harder to see than displacement; displacement shows up narratively while absorption often looks like "nothing happened.")
- **Propagation:** how does it spread constraints across the domain? [[propagation]] (Inference)

## 4) Constraint structure

- **Constraint load:** what incompatibilities narrow future configurations? [[constraint-load]] (Inference)
- **Constraint accumulation:** where do persistent differences compound? [[constraint-accumulation]] (Inference)
- **Admissibility shifts:** which transitions stop being [[admissibility|admissible]]? (Inference)

## 5) Failure states and boundaries

- **Brittleness:** where does the system lose graceful degradation? [[brittleness]] (Inference)
- **Saturation:** where does additional change mostly reroute cost? [[saturation]] (Inference)
- **Collapse surface:** conditional boundary statements ("IF X continues THEN Y becomes unavailable"). [[collapse-surface]] (Inference)

## 6) Accounting failure check

Where might there be [[accounting-failure]] (i.e., persistent differences produced without adequate tracking)?

## 7) Misuse / false-positive audit

> [!warning]
> Misuse risk: defaulting to accounting failure without testing plausible alternatives (false positives).

Using [[Failure Modes of the Irreversibility Lens]]:
- Provide 2–3 plausible alternative interpretations that *do not* assume accounting failure. (Inference)
- Flag any reification, totalizing explanation, or prescription drift. (Inference)

## 8) Output discipline

Every claim must be tagged as:
- (Definition) from `/concepts`
- (Inference) derived from those definitions
- (Assumption) requires external facts
