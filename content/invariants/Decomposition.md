---
role: invariant
status: structural
canonical: true
---

# Decomposition

> **Status:** Structural invariant  
> **Scope:** Vault-wide  
> **Non-claim:** This document is not a theory, lens, or diagnostic. It specifies a decomposition that must hold for the system to remain coherent under refinement and scale.

---

## Purpose

This document records the **minimal decomposition** required to prevent drift, hidden normativity, and authority leakage in this vault.

It exists to:

- stabilize meaning as concepts scale
- make failure modes mechanically detectable
- prevent refinement from re-collapsing roles

This decomposition is enforced by tooling (lint, schema, tests), not by interpretation.

---

## The Invariant Decomposition

Any coherent diagnostic system operating under irreversible effects must keep the following roles **explicit and non-collapsed**.

### 1. Objects

**What exists and persists**

- Descriptive structures (e.g. constraints, feasible sets, erasure costs)
- Exist independently of evaluation
- Do not act
- Do not decide

**Rule:** Object notes must not depend on operator notes.

---

### 2. Operators

**What evaluates or transforms**

- Explicit procedures, checks, or predicates
- Consume objects as inputs
- Produce bounded outputs
- Declare scope, failure modes, and non-claims

**Rule:** Operators must declare how they act (inputs, procedure, outputs).

---

### 3. Boundaries / Scope

**Where claims apply and stop**

- Domain, timeframe, transformation space
- What must not be imported
- Prevents overgeneralization and doctrine drift

**Rule:** Scope must be explicit wherever persistence or collapse is discussed.

---

### 4. Accounting / Feedback

**What accumulates over time**

- Persistent effects
- Displacement
- Erasure cost
- Constraint load

**Rule:** Any claim about stability or collapse must specify what accumulates and where cost lands.

---

### 5. Governance / Control

**How the system prevents its own drift**

- Mechanical enforcement (lint, schema, tests)
- No exemptions by authority or intent
- Rules apply to themselves

**Rule:** Violations must be detectable without interpretation.

---

## What This Is NOT

- Not a worldview
- Not a metaphysical claim
- Not a prescription
- Not an optimization target
- Not a completeness claim

This decomposition does not assert that all systems follow it.  
It asserts that **this vault must**, or it will silently fail.

---

## Failure Modes This Prevents

- Operators smuggled into definitions
- Normativity hidden in descriptive language
- Domain-specific concepts treated as universal
- Authority accumulation via explanation
- Refinement that increases ambiguity instead of reducing it

---

## Change Policy

This decomposition may only be changed if:

- a specific failure mode is demonstrated
- the proposed change reduces, not shifts, ambiguity
- enforcement rules are updated simultaneously

Any change that relaxes this decomposition must be treated as a **breaking change**.

---

## Termination Condition

Refinement is considered complete when:

- each role is explicit
- violations are mechanically caught
- adding new structure no longer removes new classes of errors

Beyond this point, further decomposition is ornamental.

---

## Summary

> **The lens can change.  
> The decomposition must not collapse.**

This document exists so that future clarity does not reintroduce old failure modes under a new vocabulary.

---

## Related invariants

- [[Governance]]
- [[Attribution]]
- [[Irreversibility]]
