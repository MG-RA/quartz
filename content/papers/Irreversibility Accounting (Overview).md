---
depends_on:
  - "[[Irreversibility Accounting (Registry)#Dependency classes (by layer)]]"
---

# Irreversibility Accounting (Overview)

Tags: #diagnostic #paper

> [!note]
> Scope: Context and orientation only. Canonical definitions live in `/concepts`.

## Problem frame (non-normative)

- Reversibility assumption: effects are treated as correctable by default; local [[rollback]] is treated as sufficient.
- Under scale, effects can [[propagation|propagate]], [[erasure-asymmetry]] can compound, and downstream cleanup can become non-local.
- When removal work is displaced without tracking, the analysis can be consistent with [[accounting-failure]].

## What this file is not

- Not a definition source (use `/concepts`).
- Not a prescription set.
- Not a prediction of outcomes.

## Navigation

- Registry / dependency classes: [[Irreversibility Accounting (Registry)]]
- Paper: [[Irreversibility Accounting (Paper)]]
- Failure modes of the lens: [[Failure Modes of the Irreversibility Lens]]
