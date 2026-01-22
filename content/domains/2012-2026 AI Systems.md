# 2012-2026 AI Systems (Domain Application)

Tags: #domain

This is one possible slice for "modern AI" relative to 2026-01-21: **2012-01-21 to 2026-01-21**.

> [!note]
> Scope: Domain application; domain statements are tagged (Assumption)/(Inference) and do not introduce new concepts.

---

## 0) Scope and boundary

- **Domain:** machine learning systems (training, evaluation, deployment) used in products and institutions (Assumption)
- **Boundary:** data pipelines, model artifacts (weights), inference services/APIs, evaluation practices, deployment feedback loops, governance/compliance processes (Assumption)
- **Time window:** 2012-01-21 to 2026-01-21 (Assumption)
- **Resolution:** ecosystem + organization level; not individual cognition or philosophy of mind (Assumption)

## 1) Transformation space

- (Assumption) Transformations allowed when testing persistence: retraining, fine-tuning, distillation, model versioning, architecture changes, provider changes, dataset refreshes, deployment/context changes, policy/regulatory changes.
- (Inference) Persistence tests use [[transformation-space]]: does the pattern remain re-identifiable across those transformations?

## 2) Candidate differences (instances, not new primitives)

1) **Training data lineage and imprint on model behavior** (Assumption)
- (Inference) Persistence test: re-identifiable across model versions when behavior or outputs remain traceable to (possibly shifting) data sources and labeling regimes.
- (Inference) If removal is claimed: [[erasure-cost]] lands on data discovery, rights/compliance work, rebuild/retrain cycles, and downstream derivatives (fine-tunes, distillations, cached outputs).
- (Inference) [[erasure-asymmetry]]: ingesting data is easy; proving deletion of influence across a deployed ecosystem is non-local and high-cost.

2) **Model weights as portable, forkable artifacts** (Assumption)
- (Inference) Persistence test: remains re-identifiable across hosting/provider changes because weights (or close derivatives) can be copied, fine-tuned, and redeployed.
- (Inference) If removal is claimed: erasure requires locating copies, derivatives, and integrations; [[erasure-cost]] routes to inventory, access control, and contractual enforcement.
- (Inference) [[erasure-asymmetry]]: creating new forks is cheap relative to coordinating deletion across many holders.

3) **Evaluation benchmarks and leaderboards as coordination infrastructure** (Assumption)
- (Inference) Persistence test: re-identifiable as a stable selection pressure even as tasks and metrics evolve, because actors optimize for legible comparisons.
- (Inference) If removal is claimed: [[erasure-cost]] lands on rebuilding coordination mechanisms, re-validating claims, and retooling incentives for funding/procurement.
- (Inference) [[erasure-asymmetry]]: establishing a benchmark is easier than undoing widespread optimization to it.

4) **Compute and deployment infrastructure as a bottlenecked capacity** (Assumption)
- (Inference) Persistence test: re-identifiable when scale/cost constraints continue to shape which models are trained, served, and updated.
- (Inference) If removal is claimed: [[erasure-cost]] lands on procurement, supply constraints, re-architecture, and service-level tradeoffs rather than clean rollback.
- (Inference) [[erasure-asymmetry]]: scaling up can be incremental; scaling down without losing dependents is coordination-heavy.

5) **Deployment feedback loops: user interactions as ongoing training signal** (Assumption)
- (Inference) Persistence test: remains re-identifiable across model updates when deployed systems keep generating data, policy exceptions, and operational heuristics that constrain future changes.
- (Inference) If removal is claimed: [[erasure-cost]] lands on decoupling products from learned operational dependencies (workflows, prompts, guardrails, downstream automation).
- (Inference) [[erasure-asymmetry]]: adding feedback channels is easy; removing them while preserving performance and accountability is costly.

## 3) Persistence and cost routing

For the above differences:

- (Assumption) [[tracking-mechanism]] examples: dataset inventories, provenance logs, model/version registries, evaluation reports, incident logs, audit trails, change-management processes.
- (Inference) [[displacement]]: costs can route to users (verification burden, exposure to errors), workers (monitoring/triage), institutions (audit/compliance), and third parties (rights-holders, downstream deployers) rather than being eliminated.
- (Inference) [[absorption]]: costs are partly paid locally via compute spend, labeling/QA, safety testing, monitoring, and slower deployment cycles; absorption capacity varies by organization and period.
- (Inference) [[propagation]]: integration into workflows propagates dependencies into adjacent domains (education, healthcare, law, media, security), increasing non-local erasure work.

## 4) Constraint structure

- (Inference) [[constraint-load]] shows up as incompatibilities like: capability vs interpretability, speed-to-deploy vs auditability, openness vs abuse surface, automation vs accountability, global scale vs local governance.
- (Inference) [[constraint-accumulation]] occurs when repeated patches (guardrails, policy exceptions, monitoring layers, compliance checklists) preserve function while narrowing future configurations and increasing coupling.
- (Inference) [[admissibility]] shifts: certain transitions become less structurally coherent (e.g., "just roll back to a previous model everywhere", "just delete a data source and keep behavior identical") because persistent differences require non-local erasure work.

## 5) Failure states and boundaries

- (Inference) [[brittleness]]: small distribution shifts, adversarial interaction, or policy changes can yield disproportionate failures when many workflows depend on a shared model/service.
- (Inference) [[saturation]]: additional scaling can increasingly reroute costs into monitoring, governance, and exception handling rather than producing clean reversibility.
- (Inference) [[collapse-surface]] (conditional examples):
  - IF model artifacts and derivatives continue to proliferate across organizations (Assumption), THEN "global deletion" transitions become less [[admissibility|admissible]] without paying large cross-boundary [[erasure-cost]] (Inference).
  - IF institutions embed models as default workflow infrastructure (Assumption), THEN rapid rollback transitions become less admissible because dependencies shift into training data, evaluation baselines, and operational procedures (Inference).

## 6) Accounting failure check

- (Inference) Possible [[accounting-failure]] sites: persistent differences are produced (lineage uncertainty, derivative proliferation, deployment dependencies) without adequate shared tracking of where erasure work lands across time/agents.
- (Assumption) A symptom to look for in any concrete case study: rollback claims that omit where deletion, retraining, audit, and coordination costs moved.

## 7) Misuse / false-positive audit

Using [[Failure Modes of the Irreversibility Lens]]:

- (Inference) Alternative interpretation 1 (not accounting failure): observed lock-in reflects straightforward comparative advantage (cost/performance) and tooling convenience, not hidden displacement.
- (Inference) Alternative interpretation 2 (not accounting failure): instability reflects rapid research progress and competitive dynamics, not constraint accumulation.
- (Inference) Alternative interpretation 3 (not accounting failure): major constraints come from exogenous law, geopolitics, and organizational risk tolerance, not AI-produced persistence.
