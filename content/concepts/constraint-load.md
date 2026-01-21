# Constraint Load

Tags: #concept

Layer: first-order

## Definition

**Constraint load** is a bookkeeping shorthand for the accumulation of incompatibilities that reduce the set of configurations a system can occupy without additional cost. Here, incompatibility refers not to error or contradiction, but to conditions that cannot be jointly satisfied without exporting erasure cost elsewhere.

Constraint load describes how stability conditions, commitments, and persistent differences have propagated through a domain, progressively narrowing the space of viable actions. It is a **diagnostic descriptor**, not an ontological claim about what constraints "really are," and carries no privileged unit, scale, or metric.

## Structural dependencies
- [[constraint]]
- [[erasure-cost]]

## What this is NOT

- Not technical debt (technical debt is one instance; constraint load is the general form)
- Not complexity (complexity can exist without constraint; constraint load specifically narrows options)
- Not burden (burden implies an identified bearer; constraint load may be unassigned)
- Not responsibility (responsibility is normative; constraint load is structural)
- Not pressure (pressure motivates action; constraint load restricts it)
- Not risk (risk concerns likelihood; constraint load concerns admissibility)

## Structural role

Constraint load constrains what _flexibility_ can mean in a system. As constraint load increases, fewer configurations are reachable without paying additional erasure cost, and remaining options increasingly require **routing cost rather than resolving it**. The diagnostic question is not whether a system appears stable, but whether that stability reflects resilience or merely the absence of remaining room to move.
