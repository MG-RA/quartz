---
layer: first-order
role: concept
canonical: true
---

# Constraint Load

## Definition

**Constraint load** is a bookkeeping shorthand for the accumulation of incompatibilities that reduce the set of configurations a system can occupy without additional cost. Here, incompatibility refers not to error or contradiction, but to conditions that cannot be jointly satisfied without exporting erasure cost elsewhere.

Constraint load describes how stability conditions, commitments, [[residual|residuals]], and persistent differences have propagated through a domain, progressively narrowing the space of viable actions.

> [!note]
> Interpretation constraint: Diagnostic descriptor only; no privileged unit, scale, or metric. Treat it as a behavioral equivalence class (what patterns are functionally the same for admissibility), not a mechanism or a metaphor.

## Ontological status (structural)

Constraint load is an ontological claim only in the narrow, structural sense: it names a class of states that are behaviorally equivalent with respect to what transitions remain feasible.

- It is **not a mechanism** (it does not "act"); mechanisms produce [[residual|residuals]] that can contribute to load.
- It is **not a metaphor** for stress or difficulty; it is a bookkeeping handle for incompatibilities that force routing.
- It is an **equivalence class**: many different residual compositions can be "the same" if they foreclose the same options under a declared [[transformation-space]].
- It is **regime-relative**: it matters most where erasure work is non-local and [[rollback]] cannot restore global options at comparable cost.

## Structural dependencies
- [[constraint]]
- [[erasure-cost]]
- [[residual]]

## What this is NOT

- Not technical debt (technical debt is one instance; constraint load is the general form)
- Not complexity (complexity can exist without constraint; constraint load specifically narrows options)
- Not burden (burden implies an identified bearer; constraint load may be unassigned)
- Not responsibility (responsibility is normative; constraint load is structural)
- Not pressure (pressure motivates action; constraint load restricts it)
- Not risk (risk concerns likelihood; constraint load concerns admissibility)

## Structural role

Constraint load constrains what _flexibility_ can mean in a system. As constraint load increases, fewer configurations are reachable without paying additional erasure cost, and remaining options increasingly require **routing cost rather than resolving it**. The diagnostic question is not whether a system appears stable, but whether that stability reflects resilience or merely the absence of remaining room to move.

## Aggregation rule

Constraint load aggregates heterogeneous [[residual|residuals]] and persistent differences into a single diagnostic quantity: "how many incompatibilities must be routed around to act at all."

## Effect on admissibility

As constraint load rises, the [[feasible-set|feasible set]] shrinks and fewer transitions remain [[admissibility|admissible]] without paying additional non-local erasure cost.

## Saturation behavior

Under sustained accumulation, constraint load tends to express as [[saturation]]: action collapses into maintenance because most moves primarily reroute cost instead of reducing it.
