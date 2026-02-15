---
role: support
type: changelog
canonical: false
---

# Spine Extraction Changelog

**Date:** 2026-02-08
**Scope:** Extract Attribution, Governance, and Decomposition concept spines to structural parity with Irreversibility.

## Problem

The concept graph was asymmetric: Irreversibility had 40 dedicated concept files with a dense dependency network (e.g. [[erasure-cost]] at 472 inbound links), while Attribution, Governance, and Decomposition had **zero** concept files. The invariants existed as definitions but had no decomposed primitive vocabulary beneath them.

This meant:
- Diagnostics for the three underdeveloped invariants had no concept anchors to reference
- Domain applications and projections could only link to Irreversibility primitives
- The vault was "Irreversibility-first, invariant-aware, invariant-uneven"

## Design rule

**Extract spines, don't share organs.** Irreversibility can be referenced everywhere; it shouldn't silently define everything.

- Only create "primitive" layer concepts when an operational test can be stated (analogous to how [[erasure-cost]] operationally tests persistence)
- Cross-spine references go in a `## Parallels` section as analogies, **not** in `## Structural dependencies`
- No concept violation should require interpretation to detect — all mechanically checkable

## What changed

### New concept files (28 total in `concepts/`)

**Attribution spine (10 concepts):**

| Concept | Layer | Operational test / role |
|---|---|---|
| [[control-surface]] | primitive | What transitions does this role have access to? |
| [[agency-layer]] | primitive | Indexes causal / intentional / structural control types |
| [[degrees-of-freedom]] | primitive | What could the role actually vary? |
| [[responsibility-claim]] | first-order | Basic unit of attribution: "role R is responsible for X" |
| [[attribution-residual]] | first-order | Persisting responsibility artifacts across transitions |
| [[attribution-displacement]] | first-order | Routing responsibility claims away from control loci |
| [[attribution-admissibility]] | selector | Is the responsibility claim valid under declared control + layer + dof? |
| [[over-attribution]] | failure-state | Responsibility exceeds degrees of freedom |
| [[under-attribution]] | failure-state | Responsibility claim ignores available control surface |
| [[layer-collapse]] | failure-state | Agency layers conflated in a single responsibility claim |

**Governance spine (10 concepts):**

| Concept | Layer | Operational test / role |
|---|---|---|
| [[constraint-surface]] | primitive | The set of enforceable rules/interfaces at a given layer |
| [[exemption]] | primitive | A path where constraint application differs by actor/role |
| [[constraint-reflexivity]] | first-order | Does the constraint apply to its own author/enforcer? |
| [[exemption-path]] | first-order | The route by which an exemption is obtained or exercised |
| [[governance-residual]] | first-order | Unaccounted authority persisting after rule changes |
| [[silent-correction]] | mechanism | Modifying state to satisfy a constraint without surfacing the violation |
| [[enforcement-topology]] | accounting | The shape of who-enforces-what across constraint surfaces |
| [[self-diagnosability]] | accounting | Whether the system can inspect its own constraint surfaces |
| [[interpretive-immunity]] | failure-state | An actor whose interpretations are not subject to the constraints they administer |
| [[authority-leakage]] | failure-state | Constraint enforcement authority exercised outside declared scope |

**Decomposition spine (8 concepts):**

| Concept | Layer | Operational test / role |
|---|---|---|
| [[role-boundary]] | primitive | Declared separation between object/operator/boundary/accounting/governance roles |
| [[role-purity]] | selector | Does this artifact perform exactly one declared role? |
| [[role-collapse]] | failure-state | Multiple roles performed by a single artifact without declaration |
| [[normativity-leak]] | failure-state | Descriptive artifact silently performing prescriptive work |
| [[function-merge]] | first-order | Two distinct functions absorbed into a single artifact |
| [[decomposition-depth]] | accounting | How many layers of role separation are mechanically enforced |
| [[refinement-stability]] | accounting | Whether adding decomposition reduces error classes |
| [[scope-rigidity]] | first-order | Role boundaries drawn too tightly, blocking legitimate work |

### New diagnostic files (9 files in 3 subdirectories)

Each diagnostic follows the registry operator pattern: core question → operator sequence → validity limits → concept links.

- `diagnostics/attribution/` — Core question: "What control existed, and where did it live?"
  - [[Diagnostic Checklist]] (6-step operator sequence)
  - [[Failure Signatures]] (8 recurring failure patterns)
  - [[Stress Tests & Boundaries]] (where attribution analysis does not help)

- `diagnostics/governance/` — Core question: "Is the constraint itself constrained?"
  - [[Diagnostic Checklist]] (6-step operator sequence)
  - [[Failure Signatures]] (10 recurring failure patterns)
  - [[Stress Tests & Boundaries]] (where governance analysis does not help)

- `diagnostics/decomposition/` — Core question: "Are roles explicit and non-collapsed?"
  - [[Diagnostic Checklist]] (7-step operator sequence)
  - [[Failure Signatures]] (8 recurring failure patterns)
  - [[Stress Tests & Boundaries]] (where decomposition analysis does not help)

### Modified files (4)

- `invariants/Attribution.md` — Added `## Minimal decomposition` and `## Structural consequences` sections
- `invariants/Governance.md` — Added `## Minimal decomposition` and `## Structural consequences` sections
- `invariants/Decomposition.md` — Added `## Minimal decomposition (concepts)` and `## Structural consequences` sections
- `papers/Irreversibility Accounting (Registry).md` — Registry rebuilt to include 28 new concepts

## Lint verification

Final lint output (0 errors):

```
Decomposition: ✓  Governance: ⚠ (3w)  Attribution: ✓  Irreversibility: ✓  Structural: ⚠ (6w)
```

- 3 governance warnings: pre-existing (Plan.md, Drafts.md, Ineluctability missing `role` frontmatter)
- 6 structural warnings: pre-existing registry truncation artifacts (broken-link from `…` mid-wikilink)

## Counts

| Metric | Before | After |
|---|---|---|
| Concept files | 40 | 68 |
| Diagnostic files | 10 | 19 |
| Total vault notes | 109 | 146 |

## Layer violations fixed during extraction

- `decomposition-depth.md`: accounting depends on selector (`role-purity`) → removed dependency
- `function-merge.md`: first-order depends on failure-state (`role-collapse`) → removed dependency
- `role-boundary.md`: primitive depends on meta-analytical (`boundary`) → moved to Parallels section
- `silent-correction.md`: mechanism missing `## Residuals` section → added

## Cross-spine discipline

No new concept uses `## Structural dependencies` to link across spines. Cross-spine references are limited to:
- `## Parallels` sections (non-binding analogies)
- `interpretive-immunity` depends on `agency-layer` (Attribution) — this is intentional: governance failure states can reference attribution primitives where structurally necessary
