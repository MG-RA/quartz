---
role: support
type: meta
canonical: true
---

# Scope Patterns

> Patterns are applied to artifacts as lenses, not as claims. Absence of a pattern is not a defect; it is an unanalyzed region.

## Purpose

Name recurring structural shapes ("scope patterns") that repeat across domains (vault, code, runtime, language, math, governance). These patterns are not domains; they are reusable forms of constraint: how a boundary is drawn, how admissible moves are defined, how failure is detected, and where irreversibility enters.

This document does not prescribe designs. It defines pattern vocabulary and the evidence questions that make patterns explicit.

## What Is A Scope Pattern?

A scope pattern is a reusable constraint form:

- boundary shape (what is in/out)
- admissible moves (what can happen inside)
- failure detection (what violations look like)
- irreversibility entry points (what gets "paid" and how)

## Core Patterns (v0)

### 1) Foundation Pattern

Statement: nothing above can repair violations below.

Examples:

- binary -> hash -> schema
- orthography -> grammar -> semantics

Evidence questions:

- What depends on this scope downstream?
- What upstream guarantees are assumed but not checked?
- Are violations fatal upstream, or can they be quarantined?

### 2) Canonicalization Pattern

Statement: many representations, one admissible form.

Examples:

- canonical CBOR encoding
- Unicode normalization

Evidence questions:

- What degrees of freedom exist in representation?
- What is the canonical form and how is it verified?
- Are non-canonical forms rejected or normalized with a witness?

### 3) Conservation Pattern

Statement: something must balance (or debt accumulates).

Examples:

- cost bucket totals
- responsibility attribution surfaces

Evidence questions:

- What quantity is conserved/tracked?
- What happens when it is not balanced?
- Where does accumulation show up in witnesses/ledgers?

### 4) Closure Pattern

Statement: operations stay inside the boundary.

Examples:

- proof checking within a fixed kernel + library set
- controlled English subsets

Evidence questions:

- What are the boundary conditions for "closed" evaluation?
- What external dependencies can silently leak in?
- What input snapshot makes closure checkable?

### 5) Bridge Pattern

Statement: crossing boundaries requires ceremony.

Examples:

- staging -> prod
- plan -> execute
- informal language -> controlled language

Evidence questions:

- What is the bridge event (plan hash, approval, attestation)?
- What costs must be declared before crossing?
- What witness thickens at the boundary (what new evidence appears)?

### 6) Attestation Pattern

Statement: claims carry their verifier.

Examples:

- "proof checked by kernel X"
- "tests run under environment hash E"
- "calculation attested by scope:calc"

Evidence questions:

- What verifier is named (id + version + hash)?
- What inputs are bound (snapshot hashes)?
- Can a third party re-verify without trust?

### 7) Degradation Pattern

Statement: guarantees weaken upward; the system labels the degradation instead of hiding it.

Examples:

- syntax -> semantics -> pragmatics
- program -> behavior

Evidence questions:

- Where do guarantees stop being checkable?
- How is that loss of guarantee named in the witness?
- What is the least-lying interface for the uncertain layer?

### 8) Quarantine Pattern

Statement: unsafe/experimental things live somewhere special to avoid contamination.

Examples:

- sandbox scopes
- staging environments
- hypothesis-only zones

Evidence questions:

- What boundary prevents contamination?
- What is allowed inside quarantine that is forbidden outside?
- How is quarantine exit mediated (bridge ceremony)?

### 9) Delegation Pattern

Statement: propose here, execute there.

Examples:

- one terminal proposes, another executes in a restricted scope
- AI proposes, human approves

Evidence questions:

- What artifact crosses the boundary (plan bundle + witness)?
- What capability is required to execute?
- How is responsibility recorded (actor ids, scope attestations)?

### 10) Accumulation Pattern

Statement: history matters; stateless systems lie about time.

Examples:

- governance drift
- technical debt
- constraint load

Evidence questions:

- What is the ledger spine for this scope?
- What is the unit of accumulation (events, cost, findings)?
- What can be replayed to reconstruct state?

### 11) Ceremony Pattern

Statement: boundary crossing is auditable because it requires structured protocol.

A ceremony is the structure that makes boundary crossing auditable. It composes elements from Bridge (boundary event), Attestation (verifier-bound claims), and Delegation (propose-then-execute separation).

Components:

- plan artifact (declares intent before execution)
- required witnesses (evidence that preconditions hold)
- approval mechanism (if crossing a high-irreversibility boundary)
- execution gate (enforces plan → witness → execute sequence)

Ceremony strength varies by irreversibility grade: read-only operations may require minimal ceremony (hash witness only), while destructive operations require full ceremony (cost declaration, approval, execution witness).

Evidence questions:

- What ceremony components are required for this boundary crossing?
- What happens if a component is missing (gate blocks, or violation is recorded)?
- Does ceremony strength match the irreversibility grade of the operation?
- Where is the ceremony completion recorded (which ledger, which witness)?

## Notes

Patterns are useful because domains change but patterns repeat. When a design feels "obvious" after constraints, it is usually because a known pattern has been made explicit.
