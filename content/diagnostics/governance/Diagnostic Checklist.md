---
depends_on:
  - "[[Governance]]"
aliases:
  - "Governance - Diagnostic Checklist"
role: diagnostic
type: checklist
canonical: true
---

# Governance - Diagnostic Checklist

> [!note]
> Non-claim: Output is descriptive; it does not prescribe remedies, rank authorities, or direct outcomes.

## Core question

Is the constraint itself constrained?

## Operator sequence

### 1. Constraint surface identification

- Enumerate all [[constraint-surface|constraint surfaces]] in the system under examination.
- For each: what rules bind, who they bind, and through what mechanisms.

### 2. Exemption path scan

- For each constraint surface, check for [[exemption-path|exemption paths]]:
  - Are there actors or roles to which this constraint does not apply?
  - Are those exemptions declared, scoped, and auditable?
  - Are there implicit exemptions (convenience features, silent corrections, "expert" overrides)?

### 3. Constraint reflexivity test

- For each constraint surface, test [[constraint-reflexivity]]:
  - Does the constraint apply to its author/creator?
  - Does it apply to its enforcer?
  - Does it apply to its interpreter?
  - If not: is the non-application declared and inspectable?

### 4. Enforcement topology mapping

- Map the [[enforcement-topology]]:
  - Which constraints are mechanically enforced (tools, tests, schemas)?
  - Which are socially enforced (norms, review, reputation)?
  - Which are not enforced at all?
  - What gaps exist between declared governance and operational governance?

### 5. Self-diagnosability assessment

- Assess [[self-diagnosability]]:
  - Can the system detect its own governance failures using its own tools?
  - Are there governance surfaces that can only be inspected "from outside"?
  - Are [[silent-correction|silent corrections]] operating anywhere?

### 6. Failure classification

- If violations are found, classify:
  - [[interpretive-immunity]]: a role that cannot be inspected by the system's own mechanisms.
  - [[authority-leakage]]: authority accumulating without governance accounting.
  - [[exemption-path]]: bypass routes that are not declared or auditable.

## Output format (fill-in block)

### System and scope
- System:
- Constraint surfaces examined:
- Time window:

### Constraint surfaces
- Surface:
  - Binds:
  - Mechanism:
  - Reflexive: (yes / no / partial)
  - Exemptions: (declared / implicit / none found)

### Enforcement topology
- Mechanically enforced:
- Socially enforced:
- Not enforced:

### Self-diagnosability
- System can detect own governance failures: (yes / no / partial)
- Blind spots:

### Governance failures
- Interpretive immunities found:
- Authority leakage indicators:
- Undeclared exemption paths:

### Misuse scan (quick)
- Governance-as-control-grab risk:
- Reflexivity used to obstruct rather than inspect risk:
- "Everything is an exemption" over-diagnosis risk:

## Links

- [[Governance]]
- [[constraint-surface]]
- [[exemption]]
- [[constraint-reflexivity]]
- [[enforcement-topology]]
- [[self-diagnosability]]
