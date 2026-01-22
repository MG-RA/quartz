---
depends_on:
  - "[[Irreversibility Accounting (Registry)#Dependency classes (by layer)]]"
  - "[[Irreversibility Accounting (Registry)#Operator (diagnostic sequence)]]"
  - "[[Irreversibility Accounting (Registry)#Scope conditions]]"
  - "[[Irreversibility Accounting (Registry)#Boundaries (distinctions)]]"
role: paper
type: source
canonical: false
facets:
  - diagnostic
---

# Irreversibility Accounting (Paper)

**Status:** Narrative paper (concept-linked)  
**Type:** Diagnostic lens  
**Core question:** What [[persistent-difference|persistent differences]] is this system producing, and who is carrying their [[erasure-cost|erasure costs]]?  
**Core claim:** Systems that produce persistent differences without [[tracking-mechanism|tracking mechanisms]] accumulate [[constraint-load|constraint load]] until they encounter [[collapse-surface|collapse surfaces]].

> [!note]
> Scope: Orientation and narrative only. Canonical definitions live in `/concepts`. This paper does not introduce new primitives, metrics, or prescriptions.

---

## 0. Problem frame (why "accounting")

Many systems act as if their effects are reversible by default: if something goes wrong, you [[rollback]] and proceed.

Under scale, effects can [[propagation|propagate]], cleanup becomes non-local, and "undoing" turns into routing work across time, people, and subsystems. The recurring pattern is not "mistakes happen"; it is that corrections repeat without restoring options.

Irreversibility accounting is the diagnostic move that forces the missing question:

> If we claim this is reversible, where would the erasure work actually land?

---

## 1. The minimal concept chain (the only moving parts)

This paper is intentionally thin: it relies on a small set of concept notes and a diagnostic operator.

- Declare scope: [[transformation-space]] (what counts as "the same thing")
- Name what persists: [[persistent-difference]]
- Make persistence testable: [[erasure-cost]]
- Track cost routing: [[displacement]] vs [[absorption]]
- Keep "for whom?" explicit: [[persistence-gradient]]
- Track shrinking options: [[constraint-load]] -> [[constraint-accumulation]]
- Name conditional cutoffs: [[collapse-surface]]
- Name the failure mode: [[accounting-failure]] (missing/failed [[tracking-mechanism]])

For dependency structure, use [[Irreversibility Accounting (Registry)]].

---

## 2. The recurrent failure pattern (what you're noticing)

The lens is motivated by a recurring structure:

- A system produces effects that remain re-identifiable ([[persistent-difference]]).
- The system claims reversibility via local fixes or [[rollback]].
- The actual removal work is costly and non-local ([[erasure-cost]]), so it is routed elsewhere ([[displacement]]) or silently paid ([[absorption]]).
- Over time, the set of workable configurations narrows ([[constraint-load]]), even when local metrics improve.

This is not an intent claim. It is a bookkeeping claim about persistence and cost location.

---

## 3. The diagnostic operator (how to use the lens)

Use the registry sequence directly (see [[Irreversibility Accounting (Registry)#Operator (diagnostic sequence)]]) or run the template in [[Diagnostic Checklist]].

In plain language:

1. Bound the system and time window.
2. Declare the [[transformation-space]] that makes persistence auditable.
3. List candidate differences and test which are [[persistent-difference|persistent]].
4. For each: state the [[erasure-cost]] and where it lands ([[displacement]] / [[absorption]]).
5. State the [[persistence-gradient]] ("reversible for whom?").
6. Summarize accumulated incompatibilities ([[constraint-load]]) and conditional boundaries ([[collapse-surface]]).
7. If the system cannot keep correspondence between produced persistence and carried costs, the output is consistent with [[accounting-failure]].

---

## 4. Accounting failure (what "missing accounting" means here)

[[accounting-failure]] is the structural condition the lens flags: persistent differences accrue, their erasure costs move, and the system cannot keep them linked via a [[tracking-mechanism]].

The practical consequence is diagnostic (not moral):

- "We fixed it" becomes ambiguous unless it includes an erasure-cost account.
- "Progress" can be local while constraint load is still rising.
- Corrections can iterate without restoring options, producing [[brittleness]] or [[saturation]].

---

## 5. Constraint load and collapse surfaces (why this matters)

The lens is most useful when the problem is not "bad behavior" but "shrinking admissible options".

As [[constraint-load]] rises, more actions function as cost-routing rather than resolution. A [[collapse-surface]] is the point where an option disappears as a practical possibility: not because someone chooses not to take it, but because accumulated persistence makes it inadmissible (or makes erasure cost discontinuously large).

---

## 6. Walkthrough sketch: content moderation (as a structural example)

Claim: errors are reversible (retrain, appeal, revert).

Diagnostic sketch:

- Candidate persistent differences: lost visibility, disrupted coordination, reputational updates ([[persistent-difference]]).
- Removal work: re-coordination, rebuilding trust, counterfactual discovery ([[erasure-cost]]).
- Cost location: largely borne by users/moderators and future states ([[displacement]]), with some hidden local labor ([[absorption]]).
- Tracking: logs exist, but correspondence between harms and required erasure work is partial ([[tracking-mechanism]]).
- Outcome: local correctability can coexist with rising [[constraint-load]] and drift toward conditional boundaries ([[collapse-surface]]).

This is an example of the operator, not a claim that "moderation always fails".

---

## 7. Validity limits and misuse checks

The lens is not universally applicable. Use:

- [[Stress Tests & Boundaries]] for where reversibility is actually symmetric/cheap.
- [[Failure Modes of the Irreversibility Lens]] for false positives (overapplication, reification, diagnosis->prescription drift, totalizing explanation).

> [!warning]
> Validity limit: Apply only within a declared transformation space and a bounded time window.

---

## 8. Relationship to other frameworks (non-exclusive)

The lens is compatible with other models, but it does not reduce to them:

- Thermodynamics: compatible at a different level; this lens is substrate-agnostic.
- Ethics/policy: not supplied here (this is diagnostic, not normative).
- Optimization/prediction: constrained by persistence; local improvements can be consistent with rising constraint load.

---

## 9. Open questions

See [[Irreversibility Accounting (Open Questions)]].

---

## Non-claims (explicit scope)

This paper does **not** claim:

- All change is irreversible
- Irreversibility is always harmful
- The lens supplies moral judgment or ranks outcomes
- The lens supplies metrics or optimization targets
- This replaces thermodynamic, economic, or institutional models
