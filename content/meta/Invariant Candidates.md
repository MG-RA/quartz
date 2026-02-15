---
role: support
type: meta
status: draft
canonical: false
---

This is a *very* good moment to ask this. New invariants usually surface **after** the machinery exists but **before** it hardens. You’re exactly there.

Below are **candidate invariants** that are *already implicit* in what you’ve built and discussed, but not yet named as first-class invariants. I’ll keep them crisp, testable, and in irreversibility-first terms.

I’ll group them by what they protect.

---

## I. Invariants about **intent and meaning**

### 1. **No Unanchored Intent**

> *Any plan that leads to irreversible action must be anchored to a semantic justification.*

**Operational form**

* Every plan must reference:

  * at least one conceptual artifact (in vault)
  * at least one boundary declaration
* Plans without anchors may exist, but cannot be bound to execution.

**Why it matters**
You already saw the failure mode:

* plans drifted when separated from conceptual grounding

This invariant formalizes the fix.

---

### 2. **Intent Is a First-Class Irreversible Act**

> *Declaring intent is itself irreversible and must be accounted for.*

**Operational form**

* Plan declaration emits a durable artifact
* Plan mutation requires explicit supersession, not overwrite
* “Abandoned plans” are still history

**Why**
Intent commits future cost even before execution. Treating it as ephemeral creates epistemic rollback.

---

## II. Invariants about **authority and truth**

### 3. **No Authority Without Schema**

> *Nothing may claim meaning unless its shape is declared.*

You hinted at this, but it’s deeper than schema gating.

**Operational form**

* Any claim, witness, plan, boundary, or verdict must:

  * name a schema
  * that schema must be registered
* Prose without schema is commentary, not authority.

**Why**
This prevents semantic creep where narrative quietly becomes fact.

---

### 4. **Verdicts Cannot Be Transported**

> *Authority does not cross interfaces; only evidence does.*

**Operational form**

* JSON-RPC, DB, LSP, plugins may emit:

  * observations
  * witnesses
* They may never emit:

  * admissibility verdicts
  * registry changes
  * authority-bearing decisions

**Why**
Prevents “smart services” from becoming shadow courts.

---

## III. Invariants about **time, causality, and replay**

### 5. **No Retroactive Meaning**

> *Later information may contextualize past events, but may not change their admissibility.*

**Operational form**

* Ledger events are immutable
* New interpretations are new events
* Reclassification requires explicit supersession artifacts

**Why**
This blocks historical rewriting via better models or hindsight.

---

### 6. **Replay Must Be Possible or Explicitly Waived**

> *Every irreversible action must either be replayable or explicitly declared non-replayable.*

**Operational form**

* For each effect:

  * either all inputs + witnesses are recorded
  * or a `NonReplayable@v1` declaration exists (with reason)

**Why**
Forces honesty around oracles, humans, and external systems.

---

## IV. Invariants about **boundaries and effects**

### 7. **Implicit Boundaries Are Violations**

> *Any boundary not declared is assumed violated.*

This is strong, but transformative.

**Operational form**

* Boundary must be explicit
* If an effect touches something not listed, that’s a violation event, not undefined behavior

**Why**
Eliminates the “we didn’t think to mention it” escape hatch.

---

### 8. **No Effect Without Ownership**

> *Every irreversible effect must name who absorbs its cost.*

You already circled this.

**Operational form**

* ActorRef + cost absorption field required
* “System” or “default” is not acceptable without justification

**Why**
Stops cost displacement into the void (or future-you).

---

## V. Invariants about **structure and evolution**

### 9. **Downstream Tightening Only**

> *Constraints may become stricter over time, never looser without explicit breakage.*

**Operational form**

* Schema evolution rules:

  * additive fields allowed
  * semantic weakening requires version bump + migration plan
* Registry enforces compatibility direction

**Why**
Prevents silent erosion of guarantees.

---

### 10. **Concepts Cannot Depend on Their Own Implementations**

> *Meaning may not depend on the mechanism that realizes it.*

**Operational form**

* Vault concepts cannot reference:

  * compiler internals
  * storage backends
  * implementation details
* Implementation may reference concepts, not vice versa.

**Why**
Prevents ontology collapse into tooling.

---

## VI. Invariants about **scale and governance**

### 11. **Projection Is Always Optional**

> *No projection layer may become required for admissibility.*

**Operational form**

* DB, indexes, caches:

  * may accelerate
  * may visualize
  * may never be required to decide “allowed or not”

**Why**
Prevents performance infrastructure from becoming authority.

---

### 12. **Silence Is Not Consent**

> *Missing evidence never implies approval.*

**Operational form**

* Absence of witness = inadmissible, not “assumed ok”
* Default is refusal, not permissiveness

**Why**
This is irreversibility-first pessimism encoded.

---

## VII. Meta-invariant (the one above all)

### 13. **Irreversibility Must Be Easier to Detect Than to Justify**

> *It must be cheaper to see that an irreversible act occurred than to argue why it was fine.*

**Operational form**

* Clear ledger events
* Clear cost grades
* Clear boundaries
* Clear actors

**Why**
If justification is easier than detection, abuse wins.

---

## How to tell if something deserves invariant status

Here’s the test:

> *If violating this principle would silently erode trust or meaning without immediate failure, it should be an invariant.*

Every item above passes that test.

---
