
**Status:** Source paper  
**Type:** Diagnostic framework introduction  
**Core claim:** Systems that produce [[persistent-difference|persistent differences]] without [[tracking-mechanism|tracking mechanisms]] accumulate [[constraint-load|constraint load]] until they encounter [[collapse-surface|collapse surfaces]].

---

## Abstract (compressed)

This paper introduces **Irreversibility Accounting** as a diagnostic lens for systems that produce [[persistent-difference|persistent differences]] while operating as if those effects were reversible. The lens identifies [[accounting-failure|accounting failures]]—conditions in which [[erasure-cost|erasure costs]] go untracked and are [[displacement|displaced]] to other actors, subsystems, or future states.

The lens is:
- Diagnostic, not normative  
- A constraint on explanations, not a generator of them  
- Pre-formal (no metrics supplied)

---

## §1. The Recurrent Failure Pattern

**Observation:** Across AI systems, institutions, software, and climate domains, effects persist despite repeated corrective action.

**Shared assumption under examination:** Effects are reversible by default. [[rollback|Rollback]] is treated as sufficient.

**Structural signature:** [[persistent-difference|Persistent differences]] accumulate even as corrections are applied.

---

## §2. Why Existing Explanations Do Not Close

| Explanation type      | What it addresses             | What it misses                                           |
| --------------------- | ----------------------------- | -------------------------------------------------------- |
| Intent-based          | Why actions were taken        | Why effects persist after intent changes                 |
| Optimization-based    | Adjustment within state space | Shrinking of state space via [[constraint-accumulation]] |
| Correction narratives | Response to error             | [[erasure-asymmetry]] between causing and undoing        |

**Gap identified:** These frameworks address behavior, not persistence. They cannot account for why [[constraint-load|constraint load]] grows even under continuous “improvement.”

---

## §3. The Missing Accounting Dimension

### §3.1 Persistence and change

Not all differences are equivalent. [[persistent-difference|Persistence]] is defined relative to a [[transformation-space|transformation space]]—the set of allowed operations under which re-identification is evaluated.

**Operational test:** A difference is persistent if its removal requires exporting [[erasure-cost|erasure cost]] beyond the local frame.

---

### §3.2 Erasure asymmetry

[[erasure-asymmetry|Erasure asymmetry]] describes the structural imbalance whereby production is local and inexpensive, while removal is distributed and costly. This asymmetry is observable without reference to intent.

**Invariant:** Undoing a [[persistent-difference|persistent difference]] requires routing cost elsewhere, typically through [[displacement|displacement]].

---

### §3.3 Accounting failure

[[accounting-failure|Accounting failure]] occurs when all three conditions co-occur:
1. [[persistent-difference|Persistent effects]] accumulate  
2. [[erasure-cost|Erasure costs]] are [[displacement|displaced]] to others or the future  
3. Responsibility becomes diffused, contested, or unassigned  

**Result:** Corrections repeat without reducing [[constraint-load|constraint load]]. The system trends toward [[brittleness|brittleness]] or [[saturation|saturation]].

---

## §4. The Irreversibility Diagnostic Lens

### §4.1 Core question

> *What persistent differences is this system producing, and where are their erasure costs being carried?*

---

### §4.2 Supporting checks

| Check                    | Diagnostic question                                        |
| ------------------------ | ---------------------------------------------------------- |
| [[erasure-cost]]         | What would removal actually require?                       |
| [[displacement]]         | Where does the cost relocate?                              |
| [[persistence-gradient]] | For whom, and across which horizons, is this irreversible? |
| [[collapse-surface]]     | Where do accumulated effects eliminate options?            |

---

## §5. Stress Tests and Boundary Conditions

### §5.1 Apparent counterexamples

| Domain                 | Surface reversibility    | Hidden persistence                                              |
| ---------------------- | ------------------------ | --------------------------------------------------------------- |
| Thought                | Ideas appear discardable | Time, attention, memory modification                            |
| Simulation             | No “real” consequence    | Outputs inform real decisions; effects [[propagation]]          |
| Reversible computation | Entropy deferred         | I/O and error correction introduce irreversibility              |
| Speech                 | Retractable              | Attention, reputation, and coordination effects [[propagation]] |

**Pattern:** Reversibility holds only at constrained scale. Once effects [[propagation|propagate]], persistence emerges.

---

### §5.2 Validity limits

The lens does **not** apply where:
- Effects are local, ephemeral, and symmetric  
- [[rollback|Rollback]] is cheap and immediate  
- Time horizons are short  
- Activity is exploratory or non-binding  

**Scope condition:** The lens applies only where [[persistent-difference|persistent effects]] accumulate faster than [[rollback|rollback]] capacity.

---

## §6. Case Walkthrough: Content Moderation

| Aspect        | Claimed                              | Actual                                                               |
| ------------- | ------------------------------------ | -------------------------------------------------------------------- |
| Reversibility | Errors fixed by retraining or appeal | Lost visibility, disrupted coordination, reputational damage persist |
| Cost location | Absorbed by system                   | [[displacement]] to users, moderators, and future states             |
| Accounting    | Actions and metrics tracked          | No account of accumulated [[persistent-difference]]                  |

**Diagnosis:** Local correctability masks structural [[constraint-accumulation|constraint accumulation]].

---

## §7. Relationship to Existing Frameworks

| Framework | Relationship |
|---------|--------------|
| Thermodynamics | Compatible at a different level; lens is substrate-agnostic |
| Moral / ethical theory | Not normative; may inform but does not supply moral conclusions |
| Agency theory | Does not redefine agency; diagnoses what remains after action |
| Prediction / optimization | Constrains where these can operate; does not itself predict |

**Key distinction:** The lens constrains explanations; it does not generate them.

---

## §8. Implications (If–Then Diagnostics)

IF a system produces persistent, constraining effects  
→ THEN irreversibility accounting is required for coherence

IF accounting mechanisms are absent  
→ THEN constraint load accumulates untracked

IF untracked constraint load accumulates  
→ THEN corrections address symptoms; brittleness or saturation develops

IF brittleness or saturation is reached  
→ THEN crises function as de facto audits of accumulated displacement

---

## §9. Conclusion (Core Claim)

> *Irreversibility accounting does not explain why systems act as they do. It explains why some systems eventually cannot act at all.*

The lens identifies [[accounting-failure|accounting failures]] already present in systems that scale beyond their [[rollback|rollback]] capacity. Where such conditions do not arise, the diagnostic is unnecessary.

---

## Concept Dependencies

```
transformation-space
       │
       ▼
persistent-difference ◄──── propagation
       │
       ├──► erasure-cost
       │         │
       │         ▼
       │    erasure-asymmetry
       │         │
       │         ▼
       └──► displacement ◄───► absorption (inverse)
                 │
                 ▼
          constraint-load
                 │
                 ▼
       constraint-accumulation
                 │
         ┌───────┴───────┐
         ▼               ▼
    brittleness     saturation
         │               │
         └───────┬───────┘
                 ▼
         collapse-surface
                 
tracking-mechanism ──► (absence = accounting-failure)

persistence-gradient ──► (makes "for whom?" askable)

rollback ──► (the mechanism the lens problematizes)

tracking-mechanism ──► (absence = accounting-failure)  

persistence-gradient ──► (makes “for whom?” explicit) 
 
rollback ──► (the mechanism the lens problematizes)
```

---

## Non-Claims (Explicit Scope)

This paper does **not** claim:
- All change is irreversible  
- Irreversibility is always harmful  
- The lens supplies moral judgment  
- The lens predicts outcomes  
- Persistence should be eliminated  
- This replaces thermodynamic, economic, or institutional models  
