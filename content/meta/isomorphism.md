---
aliases:
  - Constraint Isomorphism
role: support
type: meta
canonical: true
---

# Constraint Isomorphism

## Definition

**Constraint isomorphism** is the claim that different domains can exhibit the same structural shapes because they are solving the same bookkeeping problems under the same invariants.

This is not "as above, so below" symbolism. It is a limited, testable idea:

> Same invariants -> same handling patterns.

In this vault, the invariants are primarily about irreversibility: persistence, asymmetric erasure cost, and the need to remain coherent after irreversible change.

## What it is (and is not)

It is:

- a comparative method: extract handling patterns that survive transfer across domains
- a way to predict failure modes: when a domain pretends an invariant does not apply
- a way to reduce domain-specific stories into a smaller set of structural strategies

It is not:

- a claim that domains are identical in mechanism
- a claim that metaphors are evidence
- a license to explain away details that matter locally

## Examples of recurring shapes

- [[horizon]]: where inspection stops and accounting begins
- [[displacement]]: preservation via rerouting rather than clean erasure
- [[residual]]: persistent remainder after a "completed" action
- compression (implicit): summary replaces full access under constraint
- ledgerization (implicit): irreversible action produces records/traces/witnesses (see [[Maintenance Accounting]])

## Use as a method

When you see the same pattern in unrelated domains:

1) name the invariant it is responding to
2) name the structural strategy (operator-pattern) that handles it
3) test transfer: does the pattern remain useful when applied elsewhere?
4) if it survives, treat it as a candidate invariant (and make it falsifiable)

## See also

- [[Comparative Irreversibility]]
- [[Irreversibility-First Design]]
