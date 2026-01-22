# 2010-2026 Software Supply Chains (Domain Application)

Tags: #domain

This is one possible slice for "software supply chains" relative to 2026-01-21: **2010-01-21 to 2026-01-21**.

---

## 0) Scope and boundary

- **Domain:** the processes and infrastructure by which software components are produced, assembled (via dependencies), built, signed, distributed, and updated into running systems (Assumption)
- **Boundary:** source repositories, dependency/package registries, build tooling, CI/CD pipelines, artifact repositories and container registries, signing and key management, release/update channels, vulnerability disclosure and patch distribution workflows (Assumption)
- **Time window:** 2010-01-21 to 2026-01-21 (Assumption)
- **Resolution:** ecosystem + organization level; not general cybersecurity, malware taxonomy, or hardware supply chains (Assumption)

## 1) Transformation space

- (Assumption) Transformations allowed when testing persistence: dependency upgrades/downgrades, lockfile changes, repackaging (library vs service), repo forks/migrations, build pipeline refactors, CI/CD vendor changes, language/runtime changes, containerization, signing key rotation, registry migration/mirroring, policy/compliance changes.
- (Inference) Persistence tests use [[transformation-space]]: does the pattern remain re-identifiable across those transformations?

## 2) Candidate differences (instances, not new primitives)

1) **Transitive dependency graphs as hidden coupling between producers and downstream systems** (Assumption)
- (Inference) Persistence test: remains re-identifiable across version churn if downstream behavior and risk exposure continue to depend on an evolving, layered dependency graph (direct + transitive).
- (Inference) If removal is claimed: [[erasure-cost]] lands on dependency discovery, compatibility testing, rebuilds, incident response, and coordinating upgrades across many downstream consumers.
- (Inference) [[erasure-asymmetry]]: adding a dependency is often local; removing/replacing it requires ecosystem-wide coordination and regression risk management.

2) **Build pipelines as production lines whose scripts, caches, and defaults shape outputs** (Assumption)
- (Inference) Persistence test: remains re-identifiable across infrastructure moves if build artifacts still reflect durable pipeline choices (reproducibility settings, dependency resolution rules, cache behavior).
- (Inference) If removal is claimed: [[erasure-cost]] lands on retooling builds, recreating provenance, revalidating releases, and unwinding implicit assumptions embedded in CI/CD automation.
- (Inference) [[erasure-asymmetry]]: adding steps and tooling is incremental; deleting or simplifying pipelines without breaking releases and auditability is coordination-heavy.

3) **Artifact distribution layers (registries, mirrors, caches, images) as replication surfaces** (Assumption)
- (Inference) Persistence test: remains re-identifiable if copies and derivatives of artifacts persist across mirrors, internal registries, and downstream images even as upstream packages change.
- (Inference) If removal is claimed: [[erasure-cost]] lands on locating copies/derivatives, revoking availability, updating pinned references, and rebuilding downstream artifacts.
- (Inference) [[erasure-asymmetry]]: replication is cheap; coordinated deletion across registries and consumers is non-local and high-cost.

4) **Signing keys and trust roots as durable coordination points** (Assumption)
- (Inference) Persistence test: remains re-identifiable across tool changes if verification ultimately depends on long-lived key material, trust roots, and their governance.
- (Inference) If removal is claimed: [[erasure-cost]] lands on key rotation, re-signing, re-establishing trust with downstream verifiers, and managing rollback/revocation constraints.
- (Inference) [[erasure-asymmetry]]: establishing a trust root is easier than replacing it while preserving continuity of verification for many dependents.

5) **Provenance and compliance requirements embedded as release interfaces** (Assumption)
- (Inference) Persistence test: remains re-identifiable across organizations when release/distribution increasingly requires legible lineage, attestations, and audit trails rather than informal trust.
- (Inference) If removal is claimed: [[erasure-cost]] lands on rebuilding alternative trust guarantees, renegotiating procurement/security gates, and reworking tooling and documentation.
- (Inference) [[erasure-asymmetry]]: adding an additional check is local; removing it requires restoring confidence across many external verifiers.

6) **Long-tail maintenance and backporting obligations for widely reused components** (Assumption)
- (Inference) Persistence test: remains re-identifiable across maintainers and repos if downstream systems continue to depend on support windows, patch cadence, and compatibility promises.
- (Inference) If removal is claimed: [[erasure-cost]] lands on migrating dependents, coordinating deprecations, sustaining forks, and absorbing operational risk during transition.
- (Inference) [[erasure-asymmetry]]: creating new components is easier than retiring old ones once they anchor many dependent systems.

## 3) Persistence and cost routing

For the above differences:

- (Assumption) [[tracking-mechanism]] examples: SBOM/dependency inventories, lockfiles and manifests, build logs and reproducibility reports, artifact registry audit logs, provenance attestations, key management logs, vulnerability/patch tracking, incident postmortems.
- (Inference) [[displacement]]: costs can route to upstream maintainers (patch work), downstream integrators (verification and upgrade coordination), operators (emergency rollouts and outages), and security/compliance teams (audit burden) rather than being eliminated.
- (Inference) [[absorption]]: costs are partly paid locally via release engineering, CI/CD spend, slower release cycles, staged rollouts, and additional review/testing capacity; absorption capacity varies by organization and criticality.
- (Inference) [[propagation]]: once dependency resolution, signing, and provenance expectations are embedded, they propagate into procurement, deployment, incident response, and vendor management as dependencies.

## 4) Constraint structure

- (Inference) [[constraint-load]] shows up as incompatibilities like: speed of delivery vs assurance/auditability, flexibility of dependency updates vs reproducibility, openness/modularity vs integrity guarantees, centralized registries vs availability/resilience, rapid patching vs backward compatibility.
- (Inference) [[constraint-accumulation]] occurs when incremental controls (policy gates, scanners, attestations, exceptions, allowlists) preserve shipping while narrowing future configurations and increasing coupling between tooling, process, and trust.
- (Inference) [[admissibility]] shifts: certain transitions become less structurally coherent (e.g., "just remove a compromised dependency everywhere", "just rotate all keys immediately", "just rebuild all images") because persistent differences imply non-local erasure work.

## 5) Failure states and boundaries

- (Inference) [[brittleness]]: tightly coupled dependency graphs and shared build/distribution infrastructure can yield discontinuous failures (widespread breakage, forced emergency updates, verification outages) from small upstream changes.
- (Inference) [[saturation]]: additional governance and scanning can increasingly reroute cost into manual exception handling, audit/report generation, and coordination overhead rather than producing clean reversibility.
- (Inference) [[collapse-surface]] (conditional examples):
  - IF dependency graphs continue to deepen and diversify across products (Assumption), THEN some "rapid ecosystem-wide removal" transitions become less [[admissibility|admissible]] because coordinated replacement implies high cross-boundary [[erasure-cost]] (Inference).
  - IF provenance and signing are increasingly required across suppliers and customers (Assumption), THEN certain "informal distribution" transitions become less admissible because trust must be re-established through legible [[tracking-mechanism]] and governance rather than ad hoc coordination (Inference).

## 6) Accounting failure check

- (Inference) Possible [[accounting-failure]] sites: dependency and artifact copies/derivatives exist without shared inventory; build inputs are not fully specified; trust roots/keys are used without clear governance; rollback narratives omit where downstream rebuild and verification work lands.
- (Assumption) A symptom to look for in any concrete case study: a claim that a component was "removed" or "fixed" that does not specify downstream rebuild/redeploy steps, derivative artifacts, and verification re-baselining.

## 7) Misuse / false-positive audit

Using [[Failure Modes of the Irreversibility Lens]]:

- (Inference) Alternative interpretation 1 (not accounting failure): added controls and provenance are deliberate risk-management improvements that trade convenience for resilience, not hidden displacement.
- (Inference) Alternative interpretation 2 (not accounting failure): observed complexity comes from product scale and heterogeneity (many languages/runtimes/environments), not constraint accumulation dynamics.
- (Inference) Alternative interpretation 3 (not accounting failure): major constraints are driven by exogenous law, procurement, and threat evolution rather than endogenous supply-chain persistence.

## 8) Output discipline

- (Inference) This note follows [[Domain Template]]: definitions come from `/concepts`, and domain-specific statements are tagged (Assumption) unless they are direct applications of concept definitions.

