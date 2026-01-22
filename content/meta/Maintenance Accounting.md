---
role: support
type: maintenance-accounting
canonical: true
facets:
  - meta
---

## Purpose

This document defines how **structural maintenance** is detected and interpreted within the Irreversibility Accounting vault.

It does not prescribe maintenance actions.
It defines **what counts as evidence** that maintenance has occurred.

> [!note]
> Scope: Defines evidence of maintenance; it does not prescribe maintenance actions.

---

## Structural Definition (Source of Truth)

Maintenance is defined as:

> Any change that alters reference topology, layer designation, or invariant phrasing.

(See: Decomposition Map §11)

This definition is structural, not procedural.
It does not imply frequency, cadence, or obligation.

---

## Accounting Surface

Structural maintenance is tracked via **explicit accounting surfaces** embedded in core documents.

The primary accounting surface is:

- Frontmatter field: `structural_maintenance`
- Location: `Failure Modes of the Irreversibility Lens.md`

Example:

```yaml
structural_maintenance:
  last_event: YYYY-MM-DD
  scope: "<one sentence description>"
  affected_invariants:
    - FM#
