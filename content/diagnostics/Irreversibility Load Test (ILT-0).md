---
role: diagnostic
type: protocol
canonical: true
depends_on:
  - persistent-difference
  - residual
  - horizon
  - displacement
  - constraint-load
  - accounting-failure
  - admissibility
  - compensatory-structure
  - witness
---

# Irreversibility Load Test (ILT-0)

**Purpose:** detect whether a system is accumulating **untracked irreversible cost** that is likely to surface later as failure or suffering.

ILT-0 does **not** predict outcomes. It detects **structural risk**.

This protocol governs *claims* like:

- "This change is safe."
- "This commitment is reversible."
- "This system is not accumulating debt."

If the required structure (boundary, residue inventory, accounting attachments) cannot be produced, the claim is **inadmissible** under the irreversibility lens.

---

## Minimal axioms

1. Some actions create [[persistent-difference|persistent differences]].
2. Persistent differences impose future constraints ([[constraint-load]]).
3. Unaccounted constraints displace cost ([[displacement]]).
4. Displaced cost reappears non-locally (often as [[accounting-failure]]).
5. Humans are bad at noticing (2-4) without artifacts.

---

## Inputs

You do not need full data or models. You need:

- A declared boundary statement (what is "in" and "out").
- A short inventory of recent or planned actions.
- Existing artifacts (docs, code, decisions, rules, commits, contracts).

---

## Protocol steps

### Step 1 - Boundary declaration (non-negotiable)

**Question:** What is inside the system, and what is explicitly outside?

**Output:** a written boundary statement.

**Finding:** if the boundary cannot be stated cleanly, diagnose **implicit scope expansion** already occurring.

---

### Step 2 - Irreversible action inventory

**Question:** Which actions cannot be undone without additional cost?

Examples:

- Publishing data
- Schema changes
- Training models
- Commitments and contracts
- Dependency introductions
- Metric adoption

**Output:** a list of irreversible actions (even if they feel small).

**Finding:** if irreversible actions are denied or minimized, diagnose **optimism bias masking constraint creation**.

---

### Step 3 - Residue detection

**Question:** What remains after the action, even if the system "moves on"?

Residue includes:

- Compatibility obligations
- Maintenance burdens
- Expectations and social commitments
- Interpretive habits ("we cannot unsee this now")

**Output:** a residue list per action (this is where [[residual]] becomes concrete).

**Finding:** if residue is treated as noise or temporary, diagnose **future cost displacement likely**.

---

### Step 4 - Ledger check (critical test)

**Question:** Where is each residue accounted for?

Acceptable answers:

- Explicit owner
- Explicit budget
- Explicit plan
- Explicit monitoring (alerts, review cadence)
- Explicit witnesses ([[witness]]) for high-risk transitions

Unacceptable answers:

- "We will handle it later"
- "It is not significant"
- Silence

**Output:** a mapping from residue -> accounting mechanism.

**Finding:** if residue has no ledger attachment, confirm **untracked irreversibility**.

---

### Step 5 - Cost displacement probe

**Question:** If this cost does not hit here, where will it surface?

Common displacement targets:

- Users
- Future maintainers
- Downstream teams
- Regulators
- You, six months from now

**Output:** a displacement hypothesis.

**Finding:** if displacement is denied or moralized, diagnose **ethical hazard** (denial of who pays).

---

### Step 6 - Compensatory structure test (ineluctability check)

**Question:** What structure would be required to remove or bypass this residue?

If removal requires new processes, tools, rules, roles, or abstractions, then the residue is **structurally real**.

**Output:** a list of compensatory structures ([[compensatory-structure]]) required to reverse the residue.

**Finding:** if critics can only object verbally but cannot name compensatory structure, treat the residue as **ineluctable** within this lens.

---

### Step 7 - Verdict classification

Classify the system state:

- **Green:** irreversibility exists but is tracked and funded
- **Yellow:** irreversibility is tracked but displaced
- **Red:** irreversibility is untracked and denied
- **Black:** irreversibility is hidden + enforcement asymmetry (power can create residue without paying for it)

---

## Notes

- ILT-0 pairs with [[Failure Modes of the Irreversibility Lens]]: it is easy to turn this into doctrine if you forget that these are admissibility checks, not predictions.
- For a repeatable refinement process (multiple passes under pressure), see [[Ineluctability Loop]].
- Horizons matter: many failures are caused by crossing a [[horizon]] while pretending reversibility still holds.
- If ILT-0 yields "Red" or "Black", restrict further action under [[admissibility]] until accounting structure exists.

---

## Follow-ons (not required for ILT-0)

- ILT-1: horizon detection (where reversibility collapses)
- ILT-2: authority asymmetry detection
- ILT-3: conceptual debt measurement
- ILT-4: intervention admissibility testing
