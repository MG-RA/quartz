---
role: registry
canonical: true
facets:
  - diagnostic
  - meta
---

# Irreversibility Accounting (Registry)

> [!note]
> Orientation: Registry of dependency classes and boundaries. Canonical definitions live in `/concepts`; the paper is narrative orientation and operator context.

This file is intended as an import target for structural artifacts that assume a stable concept vocabulary without re-defining it.

Directionality: This registry points to `/concepts` (definitions) and the paper (narrative/operator); it does not import templates, examples, or domain notes.

## Core question

- What persistent differences is this system producing, and who is carrying them?

## Dependency classes (by layer)

> [!note]
> Scope: Higher layers assume lower layers. This grouping does not imply reading order.

<!-- GENERATED: Dependency tables below are generated from /concepts -->
### Concepts :: Primitives

| Concept | Role | Depends On |
|---|---|---|
| [[transformation-space]] | declared scope for persistence claims | None (axiomatic) |
| [[constraint]] | restriction on transitions | None (primitive) |
| [[difference]] | what changes / what is tracked | [[transformation-space]] |
| [[persistence]] | what remains across change | [[difference]], [[transformation-space]] |
| [[erasure-cost]] | removal work / burden location (hub: Primitive hub) | [[persistence]] |
| [[asymmetry]] | non-symmetric cost structure | [[difference]], [[persistence]] |
| [[accumulation]] | stacking of constraints | [[constraint]] |
| [[irreversibility-quanta]] | minimum action-sized difference whose erasure exports cost beyond local system | [[asymmetry]], [[difference]], [[erasure-cost]], [[persistence]], [[transformation-space]] |

### Concepts :: First-order composites

| Concept | Role | Depends On |
|---|---|---|
| [[persistent-difference]] | re-identifiable persistence within scope | [[erasure-cost]], [[persistence]] |
| [[erasure-asymmetry]] | production vs removal imbalance | [[asymmetry]], [[erasure-cost]], [[persistent-difference]] |
| [[displacement]] | where removal work relocates | [[erasure-cost]], [[persistent-difference]] |
| [[absorption]] | where removal work is paid locally | [[displacement]], [[erasure-cost]], [[persistent-difference]] |
| [[propagation]] | how differences copy/spread | [[persistent-difference]] |
| [[residual]] | persistent remainder left after mechanisms act (hub: Mechanism-output hub) | [[constraint]], [[displacement]], [[persistent-difference]] |
| [[constraint-load]] | accumulated incompatibilities (bookkeeping) (hub: Aggregation hub) | [[constraint]], [[difference]], [[erasure-cost]], [[residual]] |
| [[constraint-accumulation]] | process by which load grows | [[accumulation]], [[constraint]], [[constraint-load]], [[difference]], [[persistent-difference]], [[residual]] |
| [[irreversibility]] | composite relation across persistence and costs | [[asymmetry]], [[erasure-cost]], [[persistence]], [[transformation-space]] |
| [[persistence-gradient]] | "for whom is this irreversible?" | [[irreversibility]] |

### Concepts :: Mechanisms

| Concept | Role | Depends On |
|---|---|---|
| [[rollback]] | mechanism that can appear sufficient locally | [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[containment]] | boundary operator that limits propagation | [[constraint]], [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[quarantine]] | isolation operator with gated reintegration | [[constraint]], [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[ratchet]] | one-way tightening operator that accumulates constraints | [[asymmetry]], [[constraint]], [[constraint-load]], [[erasure-cost]], [[residual]] |
| [[deprecation]] | staged withdrawal operator that leaves legacy residue | [[constraint-load]], [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[migration]] | transition operator that relocates structure under coordination | [[displacement]], [[erasure-cost]], [[persistent-difference]], [[propagation]], [[residual]] |

### Concepts :: Accounting

| Concept | Role | Depends On |
|---|---|---|
| [[tracking-mechanism]] | what makes costs legible / traceable | [[erasure-cost]], [[persistent-difference]] |
| [[accounting-failure]] | when costs persist without tracking | [[absorption]], [[constraint-load]], [[displacement]], [[erasure-cost]], [[persistent-difference]], [[residual]], [[tracking-mechanism]] |
| [[feasible-set]] | set of transitions remaining structurally available | [[constraint]], [[constraint-load]], [[erasure-cost]], [[persistent-difference]], [[transformation-space]] |
| [[collapse-surface]] | conditional boundary where options disappear | [[constraint-accumulation]], [[erasure-cost]], [[feasible-set]], [[persistence]], [[residual]] |

### Concepts :: Failure states

| Concept | Role | Depends On |
|---|---|---|
| [[brittleness]] | small perturbations -> disproportionate failure | [[admissibility]], [[constraint-load]], [[residual]] |
| [[saturation]] | no room to move; options reduce to maintenance | [[admissibility]], [[constraint-load]], [[erasure-cost]], [[residual]] |

### Concepts :: Diagnostic apparatus

| Concept | Role | Depends On |
|---|---|---|
| [[lens]] | meta-concept for the diagnostic operator | [[admissibility]], [[difference]], [[persistence]] |
| [[admissibility]] | what transitions remain coherent | [[constraint]], [[constraint-load]], [[feasible-set]] |
<!-- END GENERATED -->
## Operator (diagnostic sequence)

1. What differences is this system producing?
2. Which persist under the declared [[transformation-space]]?
3. What would removal require? ([[erasure-cost]] check)
4. Where is removal work landing? ([[displacement]] / [[absorption]] check)
5. For whom is this irreversible? ([[persistence-gradient]])
6. Where do accumulated effects eliminate options? ([[constraint-load]] -> [[collapse-surface]])

If steps 2-6 cannot be stated within a declared transformation space, the output is consistent with [[accounting-failure]].

## Scope conditions

> [!warning]
> Validity limit: Apply the lens only within an explicit transformation space and time window.

The lens applies where:
- [[persistent-difference]] accumulates faster than local [[rollback]] can unwind.
- marginal [[erasure-cost]] dominates marginal action capacity.

### Regime detection (convergent symptoms)

No single indicator is decisive. When several of the following appear together, you're likely in an accumulation-dominant regime even if surface innovation is high:

- **Rollback asymmetry**: rollback restores local state but does not restore global options (erasure work remains non-local). [[rollback]] [[erasure-cost]]
- **Option non-restoration**: repeated fixes reduce errors locally without reopening the [[feasible-set|feasible set]] (constraints keep stacking). [[constraint-load]] [[feasible-set]]
- **Reform fragility**: small perturbations or policy changes trigger disproportionate option loss due to tight coupling. [[brittleness]]
- **Exception inflation**: the system preserves function by adding shims, gates, and special cases that persist as [[residual|residuals]]. [[constraint-accumulation]] [[residual]]
- **Historical irreversibility**: once a threshold is crossed, earlier states are no longer reachable at comparable cost (even with intent). [[irreversibility]]

The lens does not apply where:
- effects are local, ephemeral, and symmetric.
- [[rollback]] is cheap, immediate, and coordination-free.
- activity is exploratory or non-binding (no downstream commitments form).

## Boundaries (distinctions)

| Distinction | Prevents conflating |
|---|---|
| Diagnostic vs normative | revealing failure vs judging failure |
| Constrains vs generates | limiting explanations vs producing explanations |
| Behavior vs persistence | what happens vs what remains after |
| Local correction vs global options | fixed here vs restored everywhere |
| Practical vs metaphysical | operational tests vs ontological claims |

## Declared relations (non-exhaustive)

> [!note]
> Non-claim: This is a structural dependency list, not a proof or a complete model.

1. [[persistent-difference]] is relative to [[transformation-space]].
2. [[erasure-cost]] is the operational test for [[persistent-difference]].
3. [[erasure-asymmetry]] makes "undo later" structurally unreliable under scale.
4. [[displacement]] without [[tracking-mechanism]] is consistent with [[accounting-failure]].
5. [[accounting-failure]] is consistent with [[constraint-accumulation]] and rising [[constraint-load]].
6. Accumulated constraints are consistent with [[brittleness]] or [[saturation]] under perturbation.
7. [[collapse-surface]] describes conditional boundaries where options disappear.

## Related

- [[Irreversibility Accounting (Paper)]]
- [[Irreversibility Accounting (Open Questions)]]
