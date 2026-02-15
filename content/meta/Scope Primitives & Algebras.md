---
role: support
type: meta
canonical: true
depends_on:
  - decomposition
  - admissibility
  - transformation-space
  - boundary
---

# Scope Primitives & Algebras

## Purpose

Record the minimal implementation-facing concepts that clarify the vault’s lens when it is used to govern or audit real systems.

This note is not an implementation plan. It is a *concept export*: a small vocabulary that makes “what is being governed” legible.

## Domain vs Scope vs DSL

Separate three layers that are often conflated:

- **Domain** = semantic universe (meaning). What kinds of objects/judgments exist here?
- **Scope** = admissible interface into that universe (power). How may the system observe/act, and what evidence does it emit?
- **DSL** = surface syntax for stating things in a domain. How are claims written before they are lowered into checkable form?

The compiler/runtime question is admissibility:

> Given domain statements (lowered) and available witnesses, is this move admissible?

## What a scope is made of (before implementation)

Every scope is definable by:

1. **Primitives (atoms)**: the irreducible objects the scope can talk about.
2. **Operations (legal transformations)**: the admissible moves over primitives.
3. **Witnesses (evidence schemas)**: the proof objects the scope emits (snapshots/findings/plans/results).
4. **Laws (meta-constraints)**: phase placement, determinism/oracle profile, authority role, and dependency discipline.

Implementation details are projections of this contract, not part of the definition.

## Witness-first facts (claims that must carry evidence)

A witness-first system treats key claims as inadmissible unless they come with checkable evidence objects:

- a claim names its witness schema (and version)
- the witness binds its inputs (snapshots, plan hashes, rule/pack IDs)
- verification can be re-run without importing trust-by-prose

## Boot set / foundational scopes

“Foundational” is a *property of scopes*, not domains.

A foundational (boot) scope is one that can run and emit witnesses **without requiring prior authority** from other scopes.

This matters because it determines what can be used as the base of a dependency DAG without self-referential justification.

## Projection vs authority

Separate what is authoritative from what is accelerative:

- **Authority / core truth** is small, typed, and witnessable.
- **Projections** (DBs, indexes, views, dashboards) are disposable and rebuildable from authority.

This prevents “the index becomes the source of truth” drift.

## Phase discipline

To keep systems analyzable, separate phases of evaluation:

1. **Observe** (P0): read world state into snapshots
2. **Derive** (P1): compute witnesses/findings deterministically from snapshots
3. **Verdict** (P2): decide admissibility using witnesses + law
4. **Effect** (P3): execute only against plan hashes with required witnesses
5. **Account** (P4): append-only recording of what happened and why

This is the ceremony that makes boundary crossings explicit and auditable.

## Semantic deadlock

Semantic deadlock occurs when producing the witness required to obtain a verdict already requires that verdict/effect.

Deadlock is a structural symptom of missing scope boundaries (and missing boot scopes), not “complexity” in the domain itself.

