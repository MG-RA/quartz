---
depends_on:
  - "[[Attribution]]"
aliases:
  - "Attribution - Diagnostic Checklist"
role: diagnostic
type: checklist
canonical: true
---

# Attribution - Diagnostic Checklist

> [!note]
> Non-claim: Output is descriptive; it does not rank actors, assign blame, or recommend actions.

## Core question

What control existed, and where did it live?

## Operator sequence

### 1. Control surface declaration

- Declare the [[control-surface]]: what transitions could each relevant role vary?
- List the mechanisms through which control is exercised (direct action, rule-setting, tool configuration, enforcement discretion).

### 2. Agency layer declaration

- For each role, declare the [[agency-layer]] at which control operated:
  - Causal: mechanism produced a difference.
  - Intentional: actor selected among options.
  - Structural/governance: role shaped the constraint landscape.

### 3. Degrees of freedom enumeration

- For each role at its declared layer, enumerate the [[degrees-of-freedom]]:
  - What could this role actually vary at the time?
  - What was foreclosed by structure, resources, or information?

### 4. Responsibility claim formulation

- State each [[responsibility-claim]] explicitly:
  - Role + layer + degrees of freedom + attributed effect.
  - If any component is missing, the claim is incomplete.

### 5. Attribution admissibility check

- Run [[attribution-admissibility]] on each claim:
  - Does the attributed effect fall within the role's degrees of freedom?
  - Is the agency layer consistently specified?
  - Is the control surface declared?

### 6. Failure classification

- If admissibility fails, classify:
  - [[over-attribution]]: effect outside the role's degrees of freedom.
  - [[under-attribution]]: control surface exists but no responsibility claim binds it.
  - [[layer-collapse]]: agency layers conflated in a single claim.

## Output format (fill-in block)

### System and roles
- System:
- Roles under examination:
- Time window:

### Control surfaces
- Role:
  - Control surface:
  - Agency layer:
  - Degrees of freedom:

### Responsibility claims
- Claim:
  - Role:
  - Layer:
  - Degrees of freedom:
  - Attributed effect:
  - Admissibility: (pass / fail: over / under / layer-collapse)

### Attribution displacement check
- Where responsibility claims land vs where control lived:
- Displaced claims:

### Misuse scan (quick)
- Blame-as-diagnosis risk:
- Intent-substituted-for-control risk:
- Retrospective "should have known" risk:

## Links

- [[Attribution]]
- [[control-surface]]
- [[agency-layer]]
- [[degrees-of-freedom]]
- [[responsibility-claim]]
- [[attribution-admissibility]]
