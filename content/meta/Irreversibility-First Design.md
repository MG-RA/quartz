---
role: support
type: meta
status: structural
canonical: false
---

# Invariant-First Design

## Purpose

This note collects design heuristics that treat all four invariants — Irreversibility, Attribution, Governance, and Decomposition — as first-class structural constraints. It supersedes the earlier "Irreversibility-First Design" stub.

## Core principle

Every diagnostic, witness, and verdict should declare which invariants it serves. The compiler machinery (traces, profiles, verdicts) must give all four invariants the same structural standing.

## The deliberate asymmetry

Irreversibility has specialized IR primitives (`ErasureRule`, `DisplacementTrace`, boundary-loss accounting) because **cost-routing is quantitative arithmetic** — you need quantity accumulation, bucket tracking, and displacement summation. This cannot be expressed adequately through boolean constraint evaluation alone.

Attribution, Governance, and Decomposition operate through the **generic constraint + metadata system**: `Constraint` statements with `tag invariant <name>` declarations. This is not a demotion — the constraint system has the same verdict authority as specialized IR. The difference is that these three invariants don't need quantity arithmetic; they need structural pattern detection, which the constraint+predicate system provides.

## Design heuristics

1. **Tag every constraint.** When writing `.adm` rules, declare `tag invariant <name>` so the invariant appears in the witness `InvariantProfile` and verdict reason. An untagged constraint is invisible to invariant-level analysis.

2. **Fact-driven aggregation.** The `InvariantProfile` on a witness is computed purely from facts that carry an `invariant` field. No special-casing per invariant in the aggregation logic. To add a new invariant axis, simply tag constraints with the new name — no compiler changes needed.

3. **Normalization.** Invariant names are normalized (lowercase, trimmed, whitespace → underscore) to prevent drift. `"Governance"`, `" governance "`, and `"GOVERNANCE"` all resolve to `"governance"`.

4. **Determinism.** `BTreeMap` and `BTreeSet` throughout the profile computation ensure the same facts always produce the same canonical output, regardless of evaluation order.

5. **Two layers of invariant tracking.** Plan-time heuristic (`DerivedRisks.invariants_touched` from answer keywords) predicts which invariants matter. Evaluation-time truth (`Witness.invariant_profile`) confirms which ones actually triggered. The two complement each other.

## Data flow

```
.adm rule:  constraint C; tag invariant governance; @inadmissible_if ...
                                    │
              Env.constraint_meta ──┘
                                    │
    constraints.rs: lookup + normalize_invariant()
                                    │
    Fact::ConstraintTriggered { invariant: Some("governance"), ... }
                                    │
    WitnessBuilder::build() ── compute_invariant_profile(facts)
                                    │
    Witness.invariant_profile.summaries: [{ invariant: "governance", ... }]
                                    │
    eval.rs: reason = "constraints triggered [governance]"
```

## Pointers

- [[Irreversibility (Invariant)]] — specialized IR: ErasureRule, DisplacementTrace, boundary-loss
- [[Attribution]] — constraint+tag: control-surface, agency-layer, degrees-of-freedom
- [[Governance]] — constraint+tag: constraint-surface, exemption, reflexivity
- [[Decomposition]] — constraint+tag: role-boundary, role-purity, role-collapse
- [[Admissibility]] — verdict computed from all four axes
- [[Tracking-mechanism]] — witness as the common envelope
