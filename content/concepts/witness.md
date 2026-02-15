---
layer: first-order
role: concept
canonical: true
invariants:
  - governance
  - irreversibility
  - decomposition
  - attribution
---

# Witness

## Definition

A **witness** is a structured evidence bundle that records why an admissibility verdict
follows from declared constraints, permissions, and accounting rules.

Witnesses are proof objects in this system: they describe conditions and outcomes.
They do not encode advice, recommendations, or prescriptions.

## Structural dependencies

- [[constraint-accumulation]]
- [[displacement]]
- [[erasure-cost]]
- [[irreversibility]]
- [[persistence]]
- [[transformation-space]]

## Properties (structural)

- Attributable: violations and uses are linked to source locations (spans).
- Deterministic: the same inputs produce the same witness facts and ordering.
- Identity by hash: canonical bytes define the witness identity; content hashes are
  computed over canonical bytes.
- Portable: witnesses can be recomputed and compared without negotiation.
- Disputable by recomputation: disagreement is resolved by rerunning evaluation, not
  by persuasion.

## Term senses

The term "witness" appears in three distinct structural roles:

1. **Witness (artifact):** The structured evidence bundle defined in this concept — a proof object recording why an admissibility verdict follows from constraints, permissions, and rules. This is the primary sense.

2. **Witnessing (property):** The quality of having a verifiable artifact trail. "This operation was witnessed" means it has an associated witness artifact with hashes and provenance, not merely a log entry.

3. **Evidence scope (scope role):** Scopes that produce witness artifacts without issuing verdicts. Renamed from "witness scope" to avoid collision with the artifact type.

> [!note]
> Invariant: "Witness" refers to the evidence object. Scope roles must not reuse the same noun.

## What this is NOT

- Not a recommendation engine.
- Not a global state transition log.
- Not a claim about the external world.
- Not a policy statement or instruction.
