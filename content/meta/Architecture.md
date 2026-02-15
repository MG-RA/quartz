---
role: support
type: meta
status: draft
canonical: false
---

# Architecture

## Purpose

This note is a structural overview of how the vault/tooling is organized (scopes, boundaries, artifacts, and the compiler surfaces), not a concept definition.

## Invariant-first principle

The compiler treats all four invariants — Irreversibility, Attribution, Governance, Decomposition — as structurally equal in the witness and verdict machinery. See [[Invariant-First Design]] for design heuristics.

**Deliberate asymmetry:** Irreversibility has specialized IR primitives (`ErasureRule`, `DisplacementTrace`, boundary-loss accounting) because cost-routing requires quantity arithmetic. The other three invariants operate through the generic constraint + metadata system (`tag invariant <name>`). Both paths have equal verdict authority — the difference is operational, not hierarchical.

**Witness envelope:** Every `Witness` carries an `InvariantProfile` summarizing which invariants were touched, computed purely from facts. Verdict reasons include invariant names in a stable bracket-delimited format.

## Known Non-Enforcements

- **Invariant tagging is opt-in.** An untagged constraint contributes to the verdict but is invisible to invariant-level analysis. No enforcement requires all constraints to carry `tag invariant`.
- **No hardcoded invariant enum.** The system accepts any string as an invariant name. The four canonical names are convention, not compile-time enforcement.

## Pointers

- [[Scope]]
- [[Boundary]]
- [[Scope Patterns]]
- [[Irreversibility Accounting (Registry)]]
- [[Invariant-First Design]]

