# Irreversibility Accounting (MOC)

**Type:** Map of Content  
**Domain:** Diagnostic frameworks / Systems analysis  
**Core question:** *What persistent differences is this system producing, and who is carrying them?*

> [!note]
> Orientation: Map of content; definitions come from `/concepts` and the linked paper(s).

---

## The Problem

Systems operate under a **reversibility assumption**: effects are correctable by default, [[rollback|rollback]] is sufficient, "we can fix it later."

This assumption fails at scale. Effects [[propagation|propagate]], [[erasure-asymmetry|asymmetry]] compounds, and [[constraint-accumulation|constraint accumulation]] proceeds invisibly until [[collapse-surface|collapse surfaces]] are crossed.

---

## Core Concept Stack

The framework rests on a vertical dependency chain. Concepts lower in the stack are required to make concepts higher in the stack meaningful.

```
┌─────────────────────────────────────────┐
│         FAILURE STATES                  │
│  ┌─────────────┐  ┌─────────────┐       │
│  │ brittleness │  │ saturation  │       │
│  └──────┬──────┘  └──────┬──────┘       │
│         └────────┬───────┘              │
│                  ▼                      │
│         ┌───────────────┐               │
│         │collapse-surface│              │
│         └───────┬───────┘               │
├─────────────────┼───────────────────────┤
│         ACCUMULATION                    │
│                  ▼                      │
│    ┌─────────────────────────┐          │
│    │ constraint-accumulation │          │
│    └────────────┬────────────┘          │
│                 ▼                       │
│       ┌─────────────────┐               │
│       │ constraint-load │               │
│       └────────┬────────┘               │
├────────────────┼────────────────────────┤
│         COST DYNAMICS                   │
│                ▼                        │
│  ┌─────────────────────────┐            │
│  │     displacement        │◄───────┐   │
│  └────────────┬────────────┘        │   │
│               │              ┌──────┴─┐ │
│               │              │absorption│ │
│               ▼              └────────┘ │
│    ┌───────────────────┐                │
│    │ erasure-asymmetry │                │
│    └─────────┬─────────┘                │
│              ▼                          │
│      ┌─────────────┐                    │
│      │ erasure-cost │                   │
│      └──────┬──────┘                    │
├─────────────┼───────────────────────────┤
│         FOUNDATION                      │
│             ▼                           │
│  ┌─────────────────────────┐            │
│  │  persistent-difference  │◄───┐       │
│  └────────────┬────────────┘    │       │
│               │          ┌──────┴─────┐ │
│               ▼          │ propagation │ │
│  ┌─────────────────────┐ └────────────┘ │
│  │transformation-space │                │
│  └─────────────────────┘                │
└─────────────────────────────────────────┘
```

---

## Concept Index by Layer

### Layer 1: Foundation
*What must exist before anything else makes sense*

| Concept | Role |
|---------|------|
| [[transformation-space]] | Defines what "same" and "different" mean; persistence is relative to this |
| [[persistent-difference]] | The primitive: a pattern whose removal requires exporting cost |
| [[propagation]] | How effects spread beyond origin; what makes local ≠ global |

### Layer 2: Cost Dynamics  
*How persistence generates obligation*

| Concept | Role |
|---------|------|
| [[erasure-cost]] | The price of removal; operational test for persistence |
| [[erasure-asymmetry]] | Production cheap/local; removal expensive/distributed |
| [[displacement]] | Where costs go when not absorbed; relocation mechanism |
| [[absorption]] | Capacity to bear costs locally; inverse of displacement |

### Layer 3: Accumulation
*How untracked costs compound*

| Concept | Role |
|---------|------|
| [[constraint-load]] | Accumulated incompatibilities; narrowed configuration space |
| [[constraint-accumulation]] | The process by which load grows under accounting failure |

### Layer 4: Failure States
*What accumulation produces*

| Concept | Role |
|---------|------|
| [[brittleness]] | Small perturbations → disproportionate failure |
| [[saturation]] | No room to move; action becomes pure maintenance |
| [[collapse-surface]] | Threshold where options eliminate; boundary crossed suddenly |

---

## Diagnostic Apparatus

### The Lens

| Concept | Role |
|---------|------|
| [[persistence-gradient]] | Makes "for whom is this irreversible?" askable |
| [[tracking-mechanism]] | What systems need to avoid accounting failure |
| [[accounting-failure]] | The condition the lens detects |
| [[rollback]] | The mechanism the lens problematizes |

### Diagnostic Sequence

```
1. What differences is this system producing?
              │
              ▼
2. Which persist beyond immediate action?
        (use [[transformation-space]] to evaluate)
              │
              ▼
3. What would removal require?
        ([[erasure-cost]] check)
              │
              ▼
4. Where are costs currently sitting?
        ([[displacement]] check)
              │
              ▼
5. For whom is this irreversible?
        ([[persistence-gradient]])
              │
              ▼
6. Where do accumulated effects eliminate options?
        ([[collapse-surface]] identification)
              │
              ▼
        If questions 3-6 cannot be answered:
        → [[accounting-failure]] is present
```

---

## Key Distinctions

These are not atomic concepts but *boundaries* that prevent confusion.

| Distinction | Prevents conflating... |
|-------------|------------------------|
| **Diagnostic vs. Normative** | Revealing failure ↔ Judging failure |
| **Constrains vs. Generates** | Limiting explanations ↔ Producing explanations |
| **Behavior vs. Persistence** | What systems do ↔ What remains after |
| **Local correction vs. Global options** | Fixed here ↔ Restored everywhere |
| **Practical vs. Metaphysical** | Operational detection ↔ Ontological claim |

---

## Scope Conditions

> [!warning]
> Validity limit: Apply the lens only under the scope conditions listed in this section.

The lens applies **only where:**
- [[persistent-difference|Persistent differences]] accumulate faster than [[rollback|rollback]] capacity
- [[erasure-cost|Marginal erasure cost]] begins to dominate marginal action capacity

The lens does **not** apply where:
- Effects are local, ephemeral, symmetric
- [[rollback|Rollback]] is cheap, immediate, coordination-free
- Time horizons are short
- Activity is exploratory or non-binding

---

## Structural Claims

The framework makes these claims about how concepts relate:

1. [[persistent-difference|Persistence]] is always relative to a [[transformation-space|transformation space]]
2. [[erasure-cost|Erasure cost]] is the operational test for [[persistent-difference|persistence]]
3. [[erasure-asymmetry|Asymmetry]] between production and removal is the norm, not exception
4. [[displacement|Displacement]] without [[tracking-mechanism|tracking]] produces [[accounting-failure|accounting failure]]
5. [[accounting-failure|Accounting failure]] leads to [[constraint-accumulation|constraint accumulation]]
6. [[constraint-accumulation|Accumulated constraints]] manifest as [[brittleness|brittleness]] or [[saturation|saturation]]
7. [[brittleness|Brittleness]]/[[saturation|saturation]] terminate at [[collapse-surface|collapse surfaces]]
8. Crises function as de facto audits of accumulated [[displacement|displacement]]

---

## Entry Points by Use Case

**"I want to analyze a system"**  
→ Start with [[persistent-difference]], use diagnostic sequence above

**"I want to understand why corrections aren't working"**  
→ Start with [[erasure-asymmetry]] and [[displacement]]

**"I want to know if a system is approaching failure"**  
→ Start with [[constraint-load]], [[brittleness]], [[collapse-surface]]

**"I want to design systems that don't accumulate hidden debt"**  
→ Start with [[tracking-mechanism]] and [[absorption]]

**"I want to understand the framework's limits"**  
→ See Scope Conditions above; start with [[rollback]]

---

## Sources

- [[Irreversibility Accounting (Paper)]] — Original framework introduction

---

## Open Questions

- How to operationalize [[constraint-load|constraint load]] measurement in specific domains?
- What are the signatures of approaching [[collapse-surface|collapse surfaces]] before crossing?
- When does [[absorption|absorption capacity]] itself become a [[persistent-difference|persistent difference]]?
- How do [[persistence-gradient|persistence gradients]] interact across nested systems?
