---
role: domain
type: timeslice
canonical: true
---

# 2006-2026 Digital Platforms (Domain Application)

This is one possible slice for "the last 20 years" relative to 2026-01-21: **2006-01-21 to 2026-01-21**.

> [!note]
> Scope: Domain application; domain statements are tagged (Assumption)/(Inference) and do not introduce new concepts.

---

## 0) Scope and boundary

- **Domain:** large-scale digital platforms mediating communication, media distribution, and advertising (Assumption)
- **Boundary:** platform protocols, ranking/recommendation systems, identity/account systems, data retention, moderation/enforcement, ad markets (Assumption)
- **Time window:** 2006-01-21 to 2026-01-21 (Assumption)
- **Resolution:** platform/ecosystem level; not individual-level psychology (Assumption)

## 1) Transformation space

- (Assumption) Transformations allowed when testing persistence: platform rebrands/ownership changes, policy and regulation changes, interface changes, geographic rollout differences, migration between services.
- (Inference) Persistence tests use [[transformation-space]]: does the pattern remain re-identifiable across those transformations?

## 2) Candidate differences (instances, not new primitives)

1) **Cross-service behavioral data trails** (Assumption)
- (Inference) Persistence test: remains re-identifiable across account changes and platform evolution, because data is copied, aggregated, and linked.
- (Inference) If removal is claimed: [[erasure-cost]] lands on many systems (storage, backups, derived models, downstream copies, compliance processes).
- (Inference) [[erasure-asymmetry]]: generating data is low-cost; full elimination is non-local and high-cost.

2) **Algorithmic ranking as a default coordination layer** (Assumption)
- (Inference) Persistence test: remains re-identifiable across UI changes as long as ranking governs visibility/attention allocation.
- (Inference) Erasure-cost lands on rebuild of distribution, incentives, and creator/advertiser strategies.
- (Inference) Erasure asymmetry: deploying ranking is easier than removing its downstream dependencies.

3) **Network effects and lock-in via social graphs and content libraries** (Assumption)
- (Inference) Persistence test: re-identifiable as "switching cost" even when competitors exist.
- (Inference) Erasure-cost lands on coordination to move communities + rebuild archives + interoperability.
- (Inference) Erasure asymmetry: building a network can be incremental; undoing lock-in is coordination-heavy.

4) **Global policy mismatch: local rules vs global infrastructure** (Assumption)
- (Inference) Persistence test: re-identifiable as recurring incompatibilities across jurisdictions and products.
- (Inference) Erasure-cost lands on compliance systems, geo-segmentation, and enforcement overhead.
- (Inference) Erasure asymmetry: expansion creates new mismatches faster than harmonization removes them.

## 3) Persistence and cost routing

For the above differences:

- (Assumption) [[tracking-mechanism]] examples: audit logs, transparency reports, privacy controls, compliance programs, incident response.
- (Inference) [[displacement]]: costs can route to users (attention management, harassment handling), institutions (verification burdens), states (enforcement), and adjacent markets (moderation vendors, security), rather than being eliminated.
- (Inference) [[absorption]]: costs are partly paid locally via staff, tooling, friction, and product constraints; absorption capacity can vary by platform and period.
- (Inference) [[propagation]]: platform rules and incentives propagate into media, politics, commerce, and workplace coordination as dependencies.

## 4) Constraint structure

- (Inference) [[constraint-load]] shows up as incompatibilities like: personalization vs privacy, scale vs trust/safety enforcement, global reach vs local governance, open sharing vs identity/verification demands.
- (Inference) [[constraint-accumulation]] occurs when "fixes" add enforcement layers, exceptions, and compliance machinery that preserve function while narrowing future configurations.
- (Inference) [[admissibility]] shifts: certain transitions become less structurally coherent (e.g., "just delete it everywhere", "just be neutral everywhere", "just localize everywhere") because the persistent differences require non-local erasure work.

## 5) Failure states and boundaries

- (Inference) [[brittleness]]: small changes in policy, ranking, or adversary behavior can produce large coordination effects when many actors depend on the same distribution layer.
- (Inference) [[saturation]]: additional growth can increasingly reroute enforcement/coordination costs rather than remove them.
- (Inference) [[collapse-surface]] (conditional examples):
  - IF ranking + network effects remain dominant coordination mechanisms (Assumption), THEN some governance transitions that assume easy rollback become less [[admissibility|admissible]] because erasure requires non-local coordination (Inference).
  - IF data trails remain widely replicated across systems (Assumption), THEN "clean deletion" transitions become less admissible without paying large cross-boundary [[erasure-cost]] (Inference).

## 6) Accounting failure check

- (Inference) Possible [[accounting-failure]] sites: persistent differences are produced (data trails, lock-in, enforcement debt) without adequate, shared tracking of where erasure work lands across time/agents.
- (Assumption) A symptom to look for in any concrete case study: rollback claims that omit where deletion, coordination, or enforcement costs moved.

## 7) Misuse / false-positive audit

Using [[Failure Modes of the Irreversibility Lens]]:

- (Inference) Alternative interpretation 1 (not accounting failure): many outcomes reflect preference shifts and new communication affordances, not hidden cost displacement.
- (Inference) Alternative interpretation 2 (not accounting failure): observed instability is strategic conflict/adaptation (adversaries, competition), not constraint accumulation.
- (Inference) Alternative interpretation 3 (not accounting failure): constraints come from exogenous geopolitics/law and demographic/economic change, not platform-produced persistence.
