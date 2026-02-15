---
aliases:
  - event-horizon
layer: meta-analytical
role: concept
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
facets:
  - governance
  - runtime
---

# Horizon

## Definition

A **horizon** is a boundary across which state transitions remain causal in one direction but become unrecoverable (or only statistically recoverable) in the other.

Equivalently: a horizon is where **inspection stops and accounting begins**. The interior can keep evolving, but the exterior can only interact via boundary residues.

## Minimal structure

A horizon is a relation between:

1) a process that evolves
2) a boundary that limits access
3) an asymmetry in recoverability across that boundary

This is a recoverability primitive, not a gravity primitive.

## Operator model

A horizon partitions description into three regimes:

- **Interior**: rich, generative dynamics; not jointly inspectable from the exterior
- **Boundary**: residues/attestations that encode the interior indirectly
- **Exterior**: observers/processes that can only act through the boundary interface

Crossing the horizon does not destroy state. It changes what can be jointly recovered and coordinated on.

## Horizon vs boundary

Not all [[boundary]] objects are horizons.

- A boundary limits interaction or scope classification.
- A horizon limits recoverability. Crossing it changes what can be known or reconstructed without additional structure.

Examples:

- A sandbox boundary is not necessarily a horizon.
- A commit boundary is a horizon (it creates an irreversible accounting surface).

## Structural dependencies

- [[irreversibility]]
- [[residual]]
- [[erasure-cost]]
- [[constraint]]
- [[boundary]]
- [[boundary-crossing]]
- [[constraint-load]]
- [[accounting-failure]]

## Examples (cross-domain)

- Ledger append: interior work becomes an external record; rollbacks require compensatory structure.
- DAG finalization: the build graph becomes a boundary object; internal steps are summarized into a hash and witnesses.
- Approval issuance: a decision becomes a boundary artifact; later disputes reference the artifact, not the private deliberation.
- Database commit log: internal mutation becomes an externalizable trace; reconstruction is bounded by what was logged.
- Legal ratification: internal negotiation collapses into a public decision record; future coordination routes around the record.

## Horizons in this system (current and planned)

You already have horizon-like surfaces:

- Identity hashing (content addressing)
- Ledger append (`out/ledger.jsonl`)
- Witness issuance (artifacts that attest to a claim)
- Projection run completion (queryable boundary for "what the DB reflects")

Making horizons explicit unlocks:

- horizon-aware diagnostics ("what crossed the horizon?", "what evidence exists at the boundary?")
- safer governance ("no pretending reversibility exists when it does not")
- clearer DSL semantics (distinguish interior generative steps from boundary commitments)

## See also

- [[containment]] (boundaries with routing/gating work attached)
- [[displacement]] (where costs go when they cross a horizon)
- [[persistent-difference]] (what remains after crossing)
- [[Irreversibility Load Test (ILT-0)]] (first diagnostic protocol; includes horizon detection as a follow-on)
