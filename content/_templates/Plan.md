---
role: template
---
## Irreversibility-First Plan Design Prompt

**Purpose:**
Design a plan for an action that may produce irreversible effects. The goal is not optimization, but **honest accounting of persistence, cost, and responsibility**.

Answer each section explicitly. If you cannot answer a section, the plan is *inadmissible* until resolved.

---

### 1. Action Definition

* What *specific* action is being performed?
* What system(s) or substrate(s) does it touch?
* What is the minimal description that distinguishes this action from similar ones?

---

### 2. Boundary Declaration

* What is allowed to change?
* What must not change?
* What files, records, artifacts, schemas, or external systems are in scope?
* What explicit paths/resources are **out of bounds**?

> If the boundary is vague, the plan is invalid.

---

### 3. Persistence Analysis

* After the action completes, what differences remain even if no one “uses” the result?
* Which changes persist by default?
* Which changes would require *active effort* to undo?

---

### 4. Erasure Cost

* If you attempted to undo this action, what would be lost?
* Classify the erasure cost:

  * **Grade 0:** Fully reversible, no loss
  * **Grade 1:** Reversible with routine effort
  * **Grade 2:** Costly or lossy to reverse
  * **Grade 3:** Irreversible or externally irreversible
* Describe the cost in concrete terms (time, data loss, trust loss, external impact).

---

### 5. Displacement & Ownership

* Who absorbs the cost if reversal is required?
* Is the cost borne by:

  * the actor
  * future maintainers
  * users
  * external systems or people
* Is this displacement explicit and accepted?

---

### 6. Preconditions (Witnesses Required Before Action)

* What facts must be true *before* execution?
* What evidence is required to prove those facts?
* How are those facts snapshotted or attested?

> If a precondition cannot be witnessed, it must not be assumed.

---

### 7. Execution Constraints

* What constraints must hold *during* execution?
* What failure modes are acceptable?
* What failures must abort the action immediately?

---

### 8. Postconditions (Witnesses Required After Action)

* What evidence will prove what actually happened?
* How will success be distinguished from partial or failed execution?
* What artifacts or records must be produced?

---

### 9. Accountability

* Who is the acting entity?
* Under what authority is the action performed?
* What identifier ties this action to a responsible actor or system?

---

### 10. Acceptance Criteria

* Under what conditions is the action considered “done”?
* What would count as unacceptable even if execution technically succeeded?

---

### 11. Refusal Conditions

* List conditions under which the plan must *not* be executed.
* What missing evidence or ambiguity should cause a hard stop?

---

### Final Check

Answer **yes/no**:

* Are all irreversible effects bounded?
* Is erasure cost explicitly declared and accepted?
* Is responsibility assigned without ambiguity?
* Could a future reader reconstruct *why* this action happened?

If any answer is “no,” the plan is not admissible.

---

### Output Format (recommended)

* One plan document
* Structured sections matching the above
* Machine-checkable where possible
* Human-readable everywhere

---
