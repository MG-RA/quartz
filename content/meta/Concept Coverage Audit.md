---
role: support
type: audit
status: draft
date: 2026-02-12
canonical: false
---

# Concept Coverage Audit (2026-02-12)

## Claim being tested

1) “We have 68 concepts, but they aren’t tracked / tied to invariants.”  
2) “The three new invariant spines might hide something deeper.”

## What’s true in this vault (grounding)

- **Concept count:** 68 markdown files in `concepts/`.
- **Registry coverage:** all 68 concepts appear in `papers/Irreversibility Accounting (Registry).md` (so they *are* tracked as vocabulary).
- **Invariant linkage coverage (narrow test):** “linked from `invariants/` and/or `diagnostics/` via `[[concept]]` references.”

## Coverage results (invariants + diagnostics only)

Out of 68 concepts:

- **57** are referenced by at least one invariant note and/or diagnostic note.
- **37** are referenced by both an invariant note and diagnostics.
- **19** are referenced only by diagnostics (operators use them; invariant definitions don’t always enumerate them).
- **11** are referenced by neither invariants nor diagnostics (they show up elsewhere in domains/projections/meta).

### Concepts with zero invariant/diagnostic references (11)

- [[boundary]]
- [[boundary-crossing]]
- [[containment]]
- [[deprecation]]
- [[irreversibility-quanta]]
- [[migration]]
- [[persistence-gradient]]
- [[quarantine]]
- [[ratchet]]
- [[scope]]
- [[scope-change]]

Interpretation: these are mostly **boundary/lifecycle/operator-pattern** concepts. Their absence from the invariant + diagnostic layer does not imply “missing”; it implies they aren’t currently being used as *minimal decomposition vocabulary* for the invariant operators.

If you *want* every concept to be “invariant-attached”, the way to do that is to explicitly classify each concept as:

- **spine core** (belongs to Attribution/Governance/Decomposition/Irreversibility)
- **cross-spine support** (used by multiple invariants)
- **domain/method vocabulary** (used in domains/projections but not required by invariant checks)

## “Something deeper” hypothesis (why the 3 new spines feel like they hide a layer)

There is a plausible “hidden common shape” across the four invariants:

> Each invariant is an **anti-displacement constraint** for a different conserved quantity.

Concrete parallels already present in the vocabulary:

- **Irreversibility:** untracked **cost** displacement ([[displacement]] / [[absorption]]).
- **Attribution:** untracked **responsibility** displacement ([[attribution-displacement]]).
- **Governance:** untracked **constraint applicability** displacement (via [[exemption-path]] / [[silent-correction]]).
- **Decomposition:** untracked **structural function** displacement ([[function-merge]] / [[normativity-leak]]).

Under this reading, the three “new” invariants aren’t “extra morality”; they are structural conditions that keep irreversibility accounting *inspectable* instead of collapsing into narrative authority.

## Actual structural gap (not philosophical): link ambiguity

There was an ambiguity hotspot: both a concept note and a meta note had the same title “Scope Patterns”, which can cause Obsidian link resolution to silently point to the wrong note.

This was resolved by renaming the concept note to [[scope-pattern]] and keeping [[Scope Patterns]] as the catalog note.

## Next high-leverage actions (pick one)

1) **Add an explicit “Concept → Spine” index** (single note or YAML) so it’s impossible for concepts to feel “untracked”.
2) **Do a multi-spine integration pass** on 3–5 high-priority notes so Attribution/Governance/Decomposition concepts become load-bearing outside diagnostics.
3) **Make boundary/scope vocabulary operator-visible** by linking the zero-reference concepts into the relevant invariant/operator docs where they are already implicitly used.

