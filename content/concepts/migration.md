---
aliases:
  - "transition"
  - "move"
layer: mechanism
role: concept
type: mechanism
canonical: true
note_kind: operator
---

# Migration

## Definition

**Migration** is an operator-pattern that moves a system from scheme A to scheme B by relocating state, actors, or dependencies across a boundary, typically under partial information and staggered coordination. Migration is a mechanism for changing structure while keeping the system running: it does work to preserve continuity while altering the underlying configuration.

## Preconditions

- A target scheme with enough compatibility or mapping to accept the migrating substrate.
- A coordination surface (phases, cutovers, dual-run periods) to manage partial completion.

## State transition (schematic)

Scheme A â†’ mixed A/B (dual-run) â†’ scheme B (with residue)

## Residuals

Migration typically leaves [[residual|residuals]] such as:
- mapping residue (translation layers, backfills, partial conversions)
- long-lived dual-run logic and reconciliation queues
- displaced cost into monitoring, rollback narratives, and post-cutover cleanup

## Structural dependencies
- [[persistent-difference]]
- [[propagation]]
- [[displacement]]
- [[erasure-cost]]
- [[residual]]

## What this is NOT

- Not a rename (migration changes where and how structure lives).
- Not rollback (rollback attempts to restore; migration moves forward through coordination).
- Not convergence (migration may increase divergence temporarily under dual-run).

## Accounting hooks

Migration is legible when mapping residue and reconciliation work are tracked: what differences persist after cutover, where erasure work lands, and how residual dual-run surfaces contribute to ongoing constraints.

## Examples

- Technical: database migration; residuals include backfill pipelines, schema shims, and reconciliation jobs.
- Institutions: reorganizations; residuals include parallel reporting lines and split authority surfaces.
- Personal: moving cities; residuals include social/contractual obligations and new coordination seams that persist.

