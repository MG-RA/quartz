---
role: paper
canonical: true
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
| [[agency-layer]] | agency layer is an indexing scheme that distinguishes the type of control being exercised or attributed | [[control-surface]] |
| [[constraint-surface]] | constraint surface is the set of enforceable rules, interfaces, and mechanisms that actively bind actors within a system at a given layer | None (primitive) |
| [[control-surface]] | control surface is the declared set of transitions that a given role or actor can vary within a system | None (primitive) |
| [[degrees-of-freedom]] | Degrees of freedom names the set of transitions that were actually available to a role at the time of action, within its declared [[contr… | [[agency-layer]], [[control-surface]] |
| [[exemption]] | Exemption is a path where [[constraint-surface]] application differs by actor or role — where the same rule binds some participants but n… | [[constraint-surface]] |
| [[role-boundary]] | Role boundary is the declared separation between the five structural roles in the decomposition invariant: objects, operators, boundaries… | None (primitive) |

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
| [[persistence-gradient]] | "for whom is this irreversible?" | [[irreversibility]] |
| [[attribution-displacement]] | Attribution displacement is the routing of responsibility claims away from the [[control-surface]] where control actually operated, and o… | [[control-surface]], [[responsibility-claim]] |
| [[attribution-residual]] | Attribution residual is a responsibility artifact that persists after the role, context, or organizational structure that produced it has… | [[responsibility-claim]] |
| [[boundary-crossing]] | a boundary crossing is a transition between scopes or domains in which some
distinctions may not survive | [[displacement]], [[erasure-cost]], [[irreversibility]], [[scope]], [[transformation-space]] |
| [[compensatory-structure]] | compensatory structure is any new structure an agent must build to route around a [[constraint]] rather than satisfying it directly | [[constraint]], [[erasure-cost]] |
| [[constraint-reflexivity]] | Constraint reflexivity is the structural property that constraints apply to their own authors, enforcers, and interpreters — not only to… | [[constraint-surface]], [[exemption]] |
| [[exemption-path]] | exemption path is a named route through which a specific actor or role bypasses a [[constraint-surface]] that binds other participants | [[constraint-surface]], [[exemption]] |
| [[function-merge]] | Function merge is the process by which one structural role absorbs the function of another, producing an artifact or component that perfo… | [[role-boundary]] |
| [[governance-residual]] | governance residual is unaccounted authority that persists after rule changes, role transitions, or governance restructuring | [[exemption]] |
| [[responsibility-claim]] | Responsibility claim is a structured assertion that a specific role, operating at a declared [[agency-layer]], controlled the [[degrees-o… | [[agency-layer]], [[degrees-of-freedom]] |
| [[scope]] | a scope is an evaluation context: the bounded environment in which admissibility
is computed | [[persistence]], [[transformation-space]] |
| [[scope-change]] | Scope change is a boundary operation: a transition from one scope to another where
distinctions can be erased and commitments can persist… | [[boundary-crossing]], [[displacement]], [[erasure-cost]], [[irreversibility]], [[persistence]], [[scope]], [[transformation-space]], [[witness]] |
| [[scope-rigidity]] | Scope rigidity is accumulated over-specification within a decomposition: the state where [[role-boundary|role boundaries]] have been draw… | [[role-boundary]] |
| [[witness]] | A witness is a structured evidence bundle that records why an admissibility verdict
follows from declared constraints, permissions, and a… | [[constraint-accumulation]], [[displacement]], [[erasure-cost]], [[irreversibility]], [[persistence]], [[transformation-space]] |

### Concepts :: Mechanisms

| Concept | Role | Depends On |
|---|---|---|
| [[rollback]] | mechanism that can appear sufficient locally | [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[containment]] | boundary operator that limits propagation | [[constraint]], [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[quarantine]] | isolation operator with gated reintegration | [[constraint]], [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[ratchet]] | one-way tightening operator that accumulates constraints | [[asymmetry]], [[constraint]], [[constraint-load]], [[erasure-cost]], [[residual]] |
| [[deprecation]] | staged withdrawal operator that leaves legacy residue | [[constraint-load]], [[displacement]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[migration]] | transition operator that relocates structure under coordination | [[displacement]], [[erasure-cost]], [[persistent-difference]], [[propagation]], [[residual]] |
| [[silent-correction]] | Silent correction is a mechanism by which a tool, process, or authority modifies system state to satisfy a [[constraint-surface]] without… | [[constraint-reflexivity]], [[exemption]] |

### Concepts :: Accounting

| Concept | Role | Depends On |
|---|---|---|
| [[tracking-mechanism]] | what makes costs legible / traceable | [[erasure-cost]], [[persistent-difference]] |
| [[accounting-failure]] | when costs persist without tracking | [[absorption]], [[constraint-load]], [[displacement]], [[erasure-cost]], [[persistent-difference]], [[residual]], [[tracking-mechanism]] |
| [[feasible-set]] | set of transitions remaining structurally available | [[constraint]], [[constraint-load]], [[erasure-cost]], [[persistent-difference]], [[transformation-space]] |
| [[collapse-surface]] | conditional boundary where options disappear | [[constraint-accumulation]], [[erasure-cost]], [[feasible-set]], [[persistence]], [[residual]] |
| [[decomposition-depth]] | decomposition depth measures how many layers of structural role separation are explicitly maintained and mechanically enforced in a system | [[role-boundary]] |
| [[enforcement-topology]] | enforcement topology is the actual shape of what is enforced in practice across a system's [[constraint-surface|constraint surfaces]] | [[constraint-reflexivity]], [[constraint-surface]] |
| [[refinement-stability]] | Refinement stability is the property that adding structure to a system reduces the number of detectable error classes rather than shiftin… | [[decomposition-depth]], [[role-boundary]] |
| [[self-diagnosability]] | Self-diagnosability is a system's capacity to examine its own [[constraint-surface|constraint surfaces]] using the same machinery it appl… | [[constraint-reflexivity]], [[enforcement-topology]] |

### Concepts :: Failure states

| Concept | Role | Depends On |
|---|---|---|
| [[brittleness]] | small perturbations -> disproportionate failure | [[admissibility]], [[constraint-load]], [[residual]] |
| [[saturation]] | no room to move; options reduce to maintenance | [[admissibility]], [[constraint-load]], [[erasure-cost]], [[residual]] |
| [[authority-leakage]] | authority leakage is a failure state in which authority accumulates at a [[constraint-surface]] without corresponding governance accounting | [[constraint-surface]], [[exemption]] |
| [[interpretive-immunity]] | Interpretive immunity is a failure state in which a role that interprets, enforces, or authors constraints cannot itself be inspected or… | [[agency-layer]], [[exemption]] |
| [[layer-collapse]] | layer collapse is the conflation of distinct [[agency-layer|agency layers]] within a single [[responsibility-claim]] | [[agency-layer]], [[responsibility-claim]] |
| [[normativity-leak]] | Normativity leak is a failure state in which prescriptive, evaluative, or action-directing content appears in artifacts whose declared ro… | [[role-boundary]] |
| [[over-attribution]] | over-attribution is the assignment of responsibility to roles that did not control the relevant [[degrees-of-freedom]] | [[degrees-of-freedom]], [[responsibility-claim]] |
| [[role-collapse]] | Role collapse is a failure state in which distinct structural roles merge, producing artifacts that simultaneously describe, evaluate, pr… | [[role-boundary]] |
| [[under-attribution]] | Under-attribution is the failure to assign responsibility to roles that controlled the relevant [[degrees-of-freedom]] within a [[control… | [[control-surface]], [[responsibility-claim]] |

### Concepts :: Diagnostic apparatus

| Concept | Role | Depends On |
|---|---|---|
| [[lens]] | meta-concept for the diagnostic operator | [[admissibility]], [[difference]], [[persistence]] |
| [[admissibility]] | what transitions remain coherent | [[constraint]], [[constraint-load]], [[feasible-set]] |
| [[attribution-admissibility]] | attribution admissibility is a predicate that determines whether a [[responsibility-claim]] is structurally valid | [[agency-layer]], [[degrees-of-freedom]], [[responsibility-claim]] |
| [[boundary]] | a boundary is a declared separation between scopes/domains that classifies effects as “inside” vs “outside” (what counts as in-scope) | [[admissibility]], [[difference]], [[irreversibility]], [[persistence]] |
| [[horizon]] | A horizon is a boundary across which state transitions remain causal in one direction but become unrecoverable (or only statistically rec… | [[accounting-failure]], [[boundary]], [[boundary-crossing]], [[constraint]], [[constraint-load]], [[erasure-cost]], [[irreversibility]], [[residual]] |
| [[role-purity]] | Role purity is a predicate that determines whether an artifact maintains its declared structural role without performing work belonging t… | [[role-boundary]] |
| [[scope-pattern]] | a scope pattern is a reusable structural form for how a scope is drawn and maintained: | [[accounting-failure]], [[admissibility]], [[boundary]], [[constraint]], [[irreversibility]] |
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
