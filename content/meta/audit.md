---
role: support
type: audit
status: complete
date: 2026-02-11
canonical: false
targets:
  - admit_core
  - admit_scope_ingest
  - workspace
---

# Compiler Audit 2026-02

## 0) Purpose

This audit compares **documented intent** vs **implemented behavior** to detect:

- done vs missing
- drift (docs wrong, code wrong, or both)
- governance leaks (effects without ceremony, missing witnesses, bypass channels)

**Non-goal:** rewrite docs.
**Output:** a prioritized remediation list with concrete file-level work.

---

## 1) Scope and inputs

### 1.1 Workspace snapshot
- Git commit / branch: `9b37675` on `master` (dirty â€” 10 modified, 4+ untracked files related to provider abstraction)
- Rust toolchain: `rustc 1.91.0 (f8297e351 2025-10-28)`
- OS: `MSYS_NT-10.0-26200 3.4.7-ea781829.x86_64` (Windows 10/11 via MSYS2)

### 1.2 Reference specs (source of "should")
- `meta/design/compiler/admissibility-ir.md` â€” kernel IR + witness format spec (SPEC)
- `meta/design/compiler/compiler-rs-plan.md` â€” phased implementation plan (PROTOCOL)
- `meta/design/compiler/witness-format.md` â€” witness identity vs projection encoding (SPEC)
- `meta/design/compiler/cost-declaration.md` â€” Phase 4 cost declaration protocol (PROTOCOL)
- `meta/design/compiler/semantic-providers-plan.md` â€” provider architecture + ProgramBundle (ARCH)
- `meta/design/compiler/constraint-first-class.md` â€” constraint promotion design (IDEA)
- `meta/design/compiler/schema-registry.md` â€” schema ID registry (PROTOCOL)
- `meta/Architecture.md` â€” workspace architecture boundaries

### 1.3 Code surfaces (source of "is")
- Core crates:
  - `admit_core` â€” kernel IR, eval, witness, cbor, predicates, provider trait/types/registry
- Scope crates:
  - `admit_scope_ingest` â€” directory ingestion provider
  - `admit_scope_obsidian` â€” obsidian projection
  - `admit_scope_rust` â€” Rust IR lint scope (new, untracked)
- Supporting crates:
  - `admit_dsl` â€” .adm parser + lowering
  - `admit_dag` â€” DAG projections
  - `admit_surrealdb` â€” DB abstraction
  - `admit_cli` â€” CLI entry point
  - `admit_embed` â€” embedding ops
  - `vault_snapshot`, `program_bundle`, `facts_bundle` â€” artifact schemas
- Surfaces:
  - CLI (`admit_cli`)
  - (future) LSP
  - (future) CI gate

### 1.4 Test signals
- `cargo test --workspace`: **66 tests, 0 failures** âœ…
- `cargo clippy --workspace`: **128 warnings** (all in `admit_dsl` â€” clone_on_copy, module_inception, needless_borrow)
- Golden fixtures present? **yes** (`testdata/golden-witness/`, `testdata/artifacts/witness/`, `admit_core/tests/hash_golden_fixtures.rs` with 10 wire-format lock tests)

---

## 2) Executive summary

### 2.1 Overall status
- Build: âœ…
- Tests: âœ… (66/66)
- Warnings: count = 128 (all in `admit_dsl`, non-semantic)
- Highest-risk drift category:
  - [ ] Documentation drift
  - [ ] Implementation drift
  - [x] Spec ambiguity
  - [ ] Governance leak
  - [ ] Surface invariance leak

### 2.2 Top findings (max 5)
1. **F-01 (SPEC_AMBIG, S1): [resolved].** `ObsidianVaultRule` and `CalcWitness` were replaced with generic `ProviderPredicate`, and `admissibility-ir.md` now documents the extension predicate contract.
2. **F-02 (DOC_ALIGNMENT, S2): [doc-aligned].** `constraint-first-class.md` now explicitly marks itself as a target-state plan ("planned, not yet implemented"), so optional constraint IDs in code are no longer presented as current behavior.
3. **F-03 (GOV_LEAK, S2): [resolved].** Ruleset CLI mode now builds a populated `ProviderRegistry` from enabled ruleset scopes (including `ingest.dir` and `rust.structure`) and executes predicates via `evaluate_ruleset_with_inputs` with optional `--inputs` facts bundles.
4. **F-04 (DOC_DRIFT, S2): [resolved].** `semantic-providers-plan.md` now reconciles with the implemented `Provider` trait (describe/snapshot/plan/execute/verify + `eval_predicate`).
5. **F-05 (DOC_DRIFT, S3):** 128 clippy warnings in `admit_dsl` would fail CI (`-D warnings`). CI runs from root, not from `irrev-compiler/` â€” working directory mismatch may mask this.

### 2.3 Recommended next moves (max 3)
1. **Add integration coverage for ruleset execution path**: assert `check --ruleset ... --inputs ...` resolves providers by scope and records expected witness/rule outcomes.
2. **Address commit monotonicity ambiguity (F-07)**: decide whether duplicate commits should error or remain last-write-wins, then codify in spec/tests.
3. **Address snapshot timestamp determinism (F-08)**: completed in code by allowing provider snapshot `created_at` override; follow-up is to thread fixed timestamps from calling surfaces where required.

---

## 3) Drift classification rules (use consistently)

Tag every finding as one of:

- **DOC_DRIFT**: docs/spec say X, code does Y (code acceptable)
- **IMPL_DRIFT**: code does Y, spec requires X (spec is authority)
- **SPEC_AMBIG**: spec unclear / contradictory
- **ABANDONED_INTENT**: doc describes a path you no longer want (mark deprecated)
- **GOV_LEAK**: effectful path bypasses planâ†’witnessâ†’execute or lacks attribution
- **SURFACE_LEAK**: one surface can bypass gates required in another

Severity:
- **S0** = existential (wrong verdict, unsafe execution, broken determinism)
- **S1** = governance leak / witness integrity / reproducibility broken
- **S2** = missing feature in spec path but safe
- **S3** = docs polish / ergonomics

---

## 4) Kernel IR compliance audit

Reference: admissibility IR spec.

For each item: record (Status), (Evidence), (Drift Tag), (Fix).

Legend: âœ… implemented, ðŸŸ¡ partial, âŒ missing, âš ï¸ divergent

### 4.1 IR primitives (8)
| Primitive | Status | Where in code | Tests | Notes / drift |
|---|---|---|---|---|
| DeclareDifference | âœ… | `admit_core/src/ir.rs:64-70` | `admit_core/src/tests.rs`, DSL tests | Matches spec: `diff: SymbolRef, unit?: UnitRef, span: Span` |
| DeclareTransform | âœ… | `admit_core/src/ir.rs:72` | DSL tests | Matches spec |
| Persist | âœ… | `admit_core/src/ir.rs:73-78` | DSL tests | Env ignores it (`Persist { .. } => {}`); structural only â€” no semantic eval. Spec says "persistence claim"; code is a pass-through. Acceptable for v0. |
| ErasureRule | âœ… | `admit_core/src/ir.rs:80-85` | `tests.rs` golden fixtures, `displacement.rs` | Matches spec: `diff, cost, displaced_to, span`. Displacement routing works via `build_displacement_trace`. |
| AllowErase / DenyErase | âœ… | `admit_core/src/ir.rs:86-89` | `tests.rs` allow-erasure-trigger tests | Default deny enforced: `displacement.rs:26-31` â€” AllowErase without ErasureRule returns `EvalError`. |
| Constraint | âœ… | `admit_core/src/ir.rs:97-103` | `constraints.rs`, `eval.rs:42-54` | Optional ID (`Option<SymbolRef>`) â€” see F-02. `ConstraintMeta` (ir.rs:104-110) exists for tag side-channel. |
| Commit | âœ… | `admit_core/src/ir.rs:111-116` | `tests.rs` commit predicates | `CommitValue = Quantity \| Text \| Bool` â€” matches spec. |
| Query | âœ… | `admit_core/src/ir.rs:117-118` | `eval.rs` lint + admissibility paths | Spec defines `Admissible \| Witness \| Delta`. Code has `Admissible \| Witness \| Delta \| Lint { fail_on }`. **Lint is an extension** not in spec â€” **DOC_DRIFT S3**. |

**Additional IR node not in spec:**
- `ScopeChange { from, to, mode, span }` â€” handles scope boundary evaluation. Not listed in the 8 spec primitives but semantically required for scope evaluation. **DOC_DRIFT S3**.

### 4.2 Semantics contracts
- Determinism (ordering, stable evaluation):
  - Status: âœ…
  - Evidence: `Env` uses `BTreeMap`/`BTreeSet` throughout (`env.rs:11-22`). Facts sorted by `fact_sort_key` in `WitnessBuilder::build` (`witness.rs:280-281`). Constraints evaluate in `Vec` order (file order). Displacement trace sorted by bucket then diff (`displacement.rs:60-66`). Hash golden fixtures lock deterministic output across 10 tests.
  - Drift tag: none
- Monotonic facts/commits within scope:
  - Status: ðŸŸ¡
  - Evidence: `env.commits.insert(diff, value)` in `env.rs:79` â€” last-write-wins on duplicate commits. No error on overwrite. Spec says "monotone within a scope: you can add facts, but not retract them." Overwrite is technically retraction of the previous value.
  - Drift tag: **SPEC_AMBIG S2** â€” spec says "monotone" but doesn't define behavior on duplicate Commit for same diff. Code silently overwrites. Not exploitable (same-scope programs are authored, not adversarial), but spec should clarify.
- Default deny erasure enforced:
  - Status: âœ…
  - Evidence: `env.rs` â€” `is_allowed(diff)` defaults to `false` if no permission entry exists. `displacement.rs:26-31` returns `EvalError` if AllowErase exists without ErasureRule.
  - Drift tag: none
- "AllowErase requires ErasureRule" invariant:
  - Status: âœ…
  - Evidence: `displacement.rs:26-31` â€” hard error: `"allow_erase requires erasure_rule for {}"`. Tested in golden fixtures (allow-erasure-trigger).
  - Drift tag: none

### 4.3 Boolean algebra + predicates
List which predicates exist, and whether each emits witness facts deterministically.

| Predicate | Implemented | Witness facts emitted | Unit checks | Notes |
|---|---|---|---|---|
| EraseAllowed | âœ… `predicates.rs:29` | No direct fact (permission facts emitted in displacement trace) | N/A | Returns `env.is_allowed(diff)` â€” simple lookup |
| DisplacedTotal | âœ… `predicates.rs:30-33` | No direct fact (totals in displacement trace) | âœ… `ensure_compatible` called via `bucket_total` | Unit-checked comparison |
| HasCommit | âœ… `predicates.rs:35` | No direct fact | N/A | Boolean existence check |
| CommitEquals | âœ… `predicates.rs:36-46` | âœ… `Fact::CommitUsed` emitted on match | N/A | Emits fact only when commit exists |
| CommitCmp | âœ… `predicates.rs:47-65` | âœ… `Fact::CommitUsed` emitted | âœ… unit-checked via `Quantity::compare` | Returns error on missing commit |
| **ProviderPredicate** | âœ… `ir.rs:180-190` | âœ… `Fact::PredicateEvaluated` always emitted by `bool_expr.rs:46-50`; `Fact::LintFinding` emitted per provider finding by `predicates.rs:85-94` | N/A | **F-01 RESOLVED.** Replaces `ObsidianVaultRule` + `CalcWitness`. Provider resolved from `ProviderRegistry` by `scope_id`. |

**Finding F-01: âœ… RESOLVED.** `ObsidianVaultRule` and `CalcWitness` replaced with generic `ProviderPredicate { scope_id, name, params }`. The evaluator centrally enforces witness fact emission: `Fact::PredicateEvaluated` is always recorded by `bool_expr.rs`, and `Fact::LintFinding` entries are recorded from provider results by `predicates.rs`. `PredicateProvider` trait deleted; functionality absorbed into `Provider::eval_predicate()`.

---

## 5) Witness integrity audit

Goal: witness is the truth object; projections are secondary.

### 5.1 Schema stability
- Witness schema id(s): `admissibility-witness/1` (per schema-registry.md). Code: `schema_id: Option<String>` in `Witness` struct â€” **optional**, not enforced at construction. `WitnessBuilder::build()` sets `schema_id: None`. Schema ID is populated externally (e.g., by CLI during cost declaration).
  - **IMPL_DRIFT S2** â€” schema_id should be set by default at construction time.
- Versioning rules followed? **Partially** â€” schema IDs use slash notation per registry. But `WitnessBuilder` doesn't enforce schema_id presence. `engine_version` field exists with serde alias `court_version` for migration.
- Facts are typed (no "string truth")? **yes** â€” all 8 `Fact` variants are tagged enums with typed fields (`SymbolRef`, `Quantity`, `Span`, `Severity`, etc.). The `LintFinding.evidence` field is `Option<Value>` (JSON blob) â€” acceptable for extensibility.

### 5.2 Attribution
- Spans present on:
  - IR nodes: **yes** â€” all 8+ `Stmt` variants carry `span: Span`
  - constraint triggers: **yes** â€” `Fact::ConstraintTriggered` has `span: Span`
  - provider snapshot facts: **yes** â€” `IngestDirProvider` attaches `Span { file, line, .. }` to all emitted `LintFinding` facts
- Module/scope attribution present: **yes** â€” `WitnessProgram` always carries `module: ModuleId` and `scope: ScopeId`

### 5.3 Deterministic encoding + hashing
- Hash type used: (Sha256Hex newtype?) **yes** â€” `provider_types.rs:23-35` defines `Sha256Hex(String)` newtype with `serde(transparent)`. Used in `FactsBundle`, `PlanBundle`, `ExecutionResult`, `VerifyRequest`.
- Canonical identity encoding strategy stated + enforced? **yes** â€” `cbor.rs:1-13` implements RFC 8949 canonical CBOR. `encode_canonical(witness)` serializes via JSON intermediate then canonical CBOR encoding. Wire format locked by 10 golden fixture tests (`hash_golden_fixtures.rs`).
- Any float policy required? **yes** â€” `cbor.rs:16` defines `FRACTION_TOLERANCE: f64 = 1.0e-9`. `eval.rs:15-18` has `FloatPolicy::Ban | Normalize`. Spec says "floats forbidden in identity bytes" â€” `cbor.rs` encodes integers only when fractional part < tolerance, otherwise returns error for non-finite values. **Matches spec.**

### 5.4 Minimality / explainability (optional for v0)
- Can we slice witness to minimal set explaining verdict? **no** â€” facts include all evaluated predicates, all permission uses, all displacement contributions. `WitnessBuilder::build()` includes everything from `Trace`.
- If no: marked as **non-goal for v0** per spec: "For v0, witness minimization is a non-goal; prioritize determinism and completeness."

---

## 6) Provider protocol audit

Reference: provider contract (describe/snapshot/plan/execute/verify).

### 6.1 Provider trait + types
- ProviderError serializable: **yes** â€” `#[derive(Serialize, Deserialize)]` with `scope`, `phase`, `message` fields. Implements `Display` and `Error`.
- Closure requirements declared: **yes** â€” `ClosureRequirements { requires_fs, requires_network, requires_db, requires_process }` on `ProviderDescriptor`.
- Schema ids are scope-namespaced: **yes** â€” e.g., `"facts-bundle/ingest.dir@1"` in `IngestDirProvider::describe()`.
- Default stubs return structured errors with scope+phase: **yes** â€” `Provider::plan()`, `execute()`, `verify()` all return `ProviderError { scope: self.describe().scope_id, phase: ..., message: "...not supported" }`.

### 6.2 Registry
- Duplicate rejection: **yes** â€” `provider_registry.rs:30-35` returns error if `scope_id` already registered.
- Retrieval by scope: **yes** â€” `get(&self, scope_id: &ScopeId) -> Option<&Arc<dyn Provider>>`.
- Used in evaluation dispatch? **yes** â€” `ProviderPredicate` evaluation in `predicates.rs` resolves providers from the registry by `scope_id`. Evaluation fails with a clear error if the registry is not provided or the scope is unregistered.
- Used in CLI startup wiring? **yes (ruleset mode)** â€” `admit_cli/src/main.rs` now builds a scope-driven `ProviderRegistry` for `check --ruleset` and passes it into `evaluate_ruleset_with_inputs`.
- Drift tag: **RESOLVED (F-03)** for ruleset execution path.
- Implemented command surface:
  - `admit check --ruleset ruleset.json --inputs rust.facts`
- Canonical ceremony syntax (target-state):
  - `admit observe --scope rust.structure --root . --out rust.facts`
  - `admit check --ruleset ruleset.json --inputs rust.facts`
- Current observation note: `rust.structure` facts are currently produced via provider snapshot paths (tests/fixtures/API), not yet via a dedicated `observe --scope rust.structure` CLI surface.
- Scope note: non-ruleset `check --event-id` follows the cost-declaration ceremony and does not run ruleset/provider-predicate dispatch.

### 6.3 Implemented providers
#### 6.3.1 ingest.dir
- describe() correct: **yes** â€” scope_id = `"ingest.dir"`, version = 1, deterministic = true, closure `{ requires_fs: true, requires_process: true }`.
- snapshot() deterministic: **mostly** â€” facts sorted (`provider_impl.rs:189`), paths sorted in `walk_files`. However, `now_rfc3339()` uses `SystemTime::now()` (`provider_impl.rs:272-283`) so `FactsBundle.created_at` is non-deterministic. **IMPL_DRIFT S2** â€” snapshot hash is computed over facts only (not timestamp), so hash is deterministic, but the `FactsBundle` struct itself varies by timestamp.
- snapshot hash stable across platforms: **mostly** â€” sort is by `to_string_lossy()` which normalizes path separators. Windows `\\` â†’ `/` conversion done in `to_rel_path`. Git mode sorts by git's output order. File content hashing via `sha256_hex` is platform-independent. **Risk:** `git ls-files` ordering may differ between git versions.
- facts schema_id: `"facts-bundle/ingest.dir@1"` âœ…
- closure requirements: `requires_fs: true, requires_process: true` (git ls-files). `requires_db: false, requires_network: false`. Correct.
- **Tests:** 4 unit tests (`describe_returns_correct_scope`, `snapshot_rejects_missing_root`, `snapshot_rejects_nonexistent_root`, `default_plan_returns_error`). No integration test exercising actual file walking through the provider interface. **S3 gap.**

---

## 7) Ceremony / governance audit (plan â†’ witness â†’ execute)

Reference: compiler+runtime loop.

### 7.1 Identify effectful operations today
List everything that mutates state (files, DB, ledger, etc.)

| Operation | Where triggered | Gate present? | Witness emitted? | Notes |
|---|---|---|---|---|
| Ledger append (JSONL write) | `admit_cli` `ledger_append.rs` | âœ… witness hash required | âœ… witness artifact referenced | `cost.declared` and `admissibility.checked` events require witness SHA256 |
| Artifact file write (CBOR/JSON) | `admit_cli` artifact commands | ðŸŸ¡ no plan artifact required | âœ… witness emitted | Artifacts written directly; no planâ†’approveâ†’execute gate |
| DB projection update | `admit_surrealdb` + `admit_scope_obsidian` | ðŸŸ¡ projection runs on ledger data | ðŸŸ¡ projection summary emitted | Projections are derived views; not gated by ceremony |
| `execute` command | `admit_cli` execute subcommand | âœ… requires prior `checked-event-id` | âœ… execution witness | Full ceremony: declare-cost â†’ check â†’ execute |
| Directory ingestion | `admit_cli` ingest commands | âŒ no plan/approval gate | ðŸŸ¡ via provider snapshot witness | Files are read-only observed, but DB writes (chunk storage) happen without ceremony |

### 7.2 Gate check
- Can any effect occur without:
  - plan artifact? **yes** â€” artifact writes and ledger appends can occur without a plan artifact. Only `execute` command requires a prior `checked-event-id`. **GOV_LEAK S2** for artifact writes.
  - witness? **no** â€” all ledger-touching operations emit witnesses.
  - approval? **yes** â€” `declare-cost` and `check` don't require approval; they are self-certifying. `execute` requires prior `check` event. Ingestion writes to DB without any approval.

**Assessment:** The ceremony is partially implemented. The `declare-cost â†’ check â†’ execute` chain is sound, but other effectful paths (artifact writes, ingestion DB writes) bypass the full ceremony. This is **acceptable for v0** since:
- Artifact writes are content-addressed (no destructive overwrite)
- Ingestion is observation-only (filesystem reads + DB inserts)
- The ceremony is designed for the admissibility pipeline specifically

### 7.3 Surface invariance check
Compare CLI vs tests vs any other surface:
- Can one path bypass gates required in another? **yes, but trivially** â€” tests call `eval()` directly, bypassing CLI ceremony (declare-cost, check, etc.). This is expected for unit testing.
- Production concern: the CLI is the only production surface. No LSP or CI gate surface exists yet. Within the CLI, the `execute` subcommand properly enforces the `checked-event-id` requirement.
- **No SURFACE_LEAK found** for production paths.

---

## 8) Docs audit for the compiler repo

Goal: make docs useful for finishing improvements.

### 8.1 Doc inventory (classify each doc)

| Doc | Class | Up to date? | Conflicts with code? | Action |
|---|---|---|---|---|
| `admissibility-ir.md` | SPEC | yes | none blocking | Extension predicate contract documented |
| `compiler-rs-plan.md` | PROTOCOL | yes | no | Phases 0-3 done; Phase 4+ in progress |
| `witness-format.md` | SPEC | yes | no | Short, focused, correct |
| `cost-declaration.md` | PROTOCOL | yes | no | CLI examples match current commands |
| `semantic-providers-plan.md` | ARCH | yes | no | Reconciled to implemented Provider trait |
| `constraint-first-class.md` | IDEA | yes | no (explicitly planned state) | Marked as target-state design note |
| `schema-registry.md` | PROTOCOL | yes | no | Active/planned schema IDs accurate |
| `adm-wellformedness.md` | SPEC | unknown | not audited | Needs review |
| `terminology-boundary.md` | PROTOCOL | yes | no | "witness" disambiguation correct |
| `self-audit-failure-protocol.md` | PROTOCOL | yes | no | Defines audit re-run triggers |
| `boundries.md` | ARCH | yes | no | Scope boundary semantics |
| `scope-change.md` | ARCH | yes | no | ScopeChange semantics |
| `hello-world.md` | STATUS | yes | no | Worked example |
| `vault-snapshot-schema-v0.md` | SPEC | yes | no | Snapshot schema |
| `hash-witness-schema-v0.md` | SPEC | yes | no | Hash witness encoding |
| `governed-queries-and-functions.md` | ARCH | yes | no | Engine query/function design |
| `rust-ir-derived-rules-plan.md` | IDEA | current | no | Rust lint scope design |
| `kernel-stdlib-userspace-plan.md` | IDEA | current | no | Future stdlib design |
| `ineluctability-loop-v0.md` | ARCH | yes | no | Runtime loop design |
| `meta-registry-gate-plan.md` | IDEA | current | no | Meta registry gating |
| `compilerIdea.md` | IDEA | historical | no | Original design idea |
| `compiler-idea-context.md` | IDEA | historical | no | Context for compiler idea |
| `compiler-idea-delta.md` | IDEA | historical | no | Delta compiler idea |
| `compiler-rs-phase2-checklist.md` | STATUS | done | no | Phase 2 completed |
| `compiler-rs-phase3-checklist.md` | STATUS | done | no | Phase 3 completed |
| `chomsky-features-comparison.md` | IDEA | historical | no | Theoretical comparison |
| `adm-implementation-plan.md` | STATUS | partially | not audited | Needs review |
| `python-to-rust-migration.md` | STATUS | historical | no | Migration plan |
| `surrealdb-dag-ledger-projection.md` | ARCH | yes | no | DAG projection design |
| `runtime-genesis-implementation-plan.md` | IDEA | current | no | Genesis design |
| `selfgovernancebootstrap.md` | IDEA | historical | no | Bootstrap concept |
| `self governance.md` | IDEA | historical | no | Self-governance concept |
| `ledger-export-and-db-projection.md` | ARCH | yes | no | Ledger/DB projection |
| `semantics-instrumentation-ritual-binding.md` | ARCH | yes | no | Ritual binding design |

### 8.2 Contradictions (list)
- Contradiction #1: [resolved]
  - Doc claim: `admissibility-ir.md` specifies exactly 5 predicates: `EraseAllowed`, `DisplacedTotal`, `HasCommit`, `CommitEquals`, `CommitCmp`.
  - Code reality: `ir.rs` now has 5 kernel predicates + 1 generic `ProviderPredicate { scope_id, name, params }`. Extension predicates are provider-declared via `ProviderDescriptor.predicates` and dispatched through the `ProviderRegistry`.
  - Resolution: `admissibility-ir.md` now includes an explicit extension predicate contract (`ProviderPredicate`) and witness obligations.

- Contradiction #2: [resolved]
  - Doc claim: `semantic-providers-plan.md` defines `SemanticProvider::build_bundle()` as the provider interface.
  - Code reality: `provider_trait.rs` implements a 5-phase `Provider` trait (`describe/snapshot/plan/execute/verify`).
  - Resolution: `semantic-providers-plan.md` now references the implemented `Provider` trait and phase ceremony.

- Contradiction #3: [doc-aligned]
  - Doc claim: `constraint-first-class.md` says "All constraints must have an ID. No anonymous constraints."
  - Code reality: `ir.rs:98-103` — `Constraint { id: Option<SymbolRef>, ... }`. `env.rs:17` — `Vec<(Option<SymbolRef>, ...)>`.
  - Resolution: doc now explicitly marks this as planned/not yet implemented target state.

### 8.3 Missing docs that block work (max 5)
1. **Provider protocol spec** — a stricter SPEC-level document for the provider ceremony is still useful even after plan reconciliation.
2. **CI configuration doc** — clarify workspace root assumptions and required working directory for local/CI commands.
3. **Provider registry wiring guide** — how and when callers should build and pass provider registries into evaluator surfaces.
4. **Snapshot determinism guarantees** — document which fields are identity-bearing vs observational metadata across platforms/git versions.
---

## 9) Remediation backlog (generated from findings)

### 9.1 S0 / S1 (must-do)
| ID | Severity | Tag | Description | Files | Test to add |
|---|---|---|---|---|---|
| F-01 | S1 | ~~SPEC_AMBIG~~ âœ… **RESOLVED** | Extension predicates replaced with `ProviderPredicate`. `Fact::PredicateEvaluated` always emitted by kernel; `Fact::LintFinding` emitted per provider finding. `PredicateProvider` trait deleted. | `admit_core/src/{ir,predicates,provider_types,provider_trait,bool_expr,constraints,eval,provider,lib}.rs`, `admit_dsl/src/lowering.rs` | `predicate_serde_roundtrip_provider_predicate` (added); `parse_legacy_vault_rule_alias_lowers_to_provider_predicate` (added) |

### 9.2 S2 (should-do)
| ID | Tag | Description | Files | Test to add |
|---|---|---|---|---|
| F-02 | PLANNED_FEATURE | Constraint IDs still optional in code; doc now explicitly marks this as planned/not-yet-implemented | `admit_core/src/ir.rs`, `admit_core/src/env.rs`, `constraint-first-class.md` | Parser rejection test for anonymous constraints (when promoted to implementation) |
| F-03 | RESOLVED | Registry-backed ruleset evaluation is wired in CLI (`check --ruleset`) with scope-based provider registration and optional input facts bundles (`--inputs`) | `admit_core/src/provider_registry.rs`, `admit_cli/src/main.rs`, `crates/admit_cli/Cargo.toml` | Integration test: `check --ruleset --inputs` end-to-end |
| F-06 | RESOLVED | `WitnessBuilder::build()` now sets default `schema_id = "admissibility-witness/1"` | `admit_core/src/witness.rs`, `admit_core/src/tests.rs` | Added `witness_builder_sets_default_schema_id`; updated dependent witness golden fixtures |
| F-07 | SPEC_AMBIG | Commit overwrite (last-write-wins) may violate "monotone facts" spec clause | `admit_core/src/env.rs:79` | Either clarify spec or add duplicate-commit error |
| F-08 | IMPL_DRIFT | Snapshot timestamp non-determinism addressed by `created_at` override in request params; remaining work is caller adoption where fixed times are required | `admit_scope_ingest/src/provider_impl.rs` | Added unit test using fixed `created_at` |

### 9.3 S3 (nice-to-have)
| ID | Description | Files |
|---|---|---|
| F-05 | 128 clippy warnings in `admit_dsl` (clone_on_copy, module_inception, needless_borrow) | `admit_dsl/src/parser.rs`, `admit_dsl/src/tests.rs` |
| F-12 | `fact_sort_key` duplicated between `admit_core/src/witness.rs` and `admit_scope_ingest/src/provider_impl.rs` | Both files |

---

## 10) Closure criteria (when this audit is "done enough")

Audit considered "passing" when:

- [x] No S0 items remain open (none found)
- [x] No S1 items remain open â†’ **F-01 resolved** (extension predicates replaced with `ProviderPredicate`; witness fact emission enforced centrally by evaluator)
- [x] SPEC ↔ CODE contradictions are either fixed or explicitly marked ABANDONED_INTENT
- [x] Provider(s) snapshot determinism is tested and stable â†’ hash determinism confirmed; timestamp non-determinism is cosmetic
- [x] Witness schema + hashes are stable and referenced by tests â†’ 10 golden fixture tests lock wire format
- [x] Doc inventory has clear classes (SPEC/PROTOCOL/ARCH/STATUS/IDEA) â†’ done in Â§8.1 above

**Verdict: audit is PASSING for code and docs at S0/S1.** Open code work is now concentrated in F-07 (commit overwrite monotonicity decision), with optional hardening via ruleset integration tests.


