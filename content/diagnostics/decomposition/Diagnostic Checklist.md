---
depends_on:
  - "[[Decomposition]]"
aliases:
  - "Decomposition - Diagnostic Checklist"
role: diagnostic
type: checklist
canonical: true
---

# Decomposition - Diagnostic Checklist

> [!note]
> Non-claim: Output is descriptive; it does not prescribe organizational changes or rank decomposition strategies.

## Core question

Are roles explicit and non-collapsed?

## Operator sequence

### 1. Role boundary identification

- Identify all [[role-boundary|role boundaries]] in the system under examination.
- For each artifact or component: what is its declared role (object, operator, boundary/scope, accounting, governance)?
- Are role declarations explicit or implicit?

### 2. Role purity check

- For each artifact, run [[role-purity]] check:
  - Does the artifact perform structural work within its declared role only?
  - Does it contain evaluative, prescriptive, or governance logic that belongs to another role?

### 3. Normativity leak scan

- Scan for [[normativity-leak]]:
  - Do descriptive artifacts (objects, definitions) contain prescriptive language?
  - Do diagnostics embed prescriptions in their output?
  - Do operators contain self-justifying authority?

### 4. Function merge detection

- Check for [[function-merge]]:
  - Has any artifact's effective role expanded beyond its declaration?
  - Are multiple structural functions combined in a single artifact without boundary maintenance?

### 5. Decomposition depth assessment

- Assess [[decomposition-depth]]:
  - How many layers of role separation are mechanically enforced?
  - Are role boundaries enforced by tooling (lint, schema, tests) or only by interpretation?

### 6. Refinement stability check

- Check [[refinement-stability]]:
  - Does recent structural work reduce detectable error classes?
  - Or does it merely redistribute ambiguity?
  - Is [[scope-rigidity]] present (boundaries that obstruct legitimate work)?

### 7. Failure classification

- If violations are found, classify:
  - [[role-collapse]]: role boundaries have failed; structural functions are merged.
  - [[normativity-leak]]: prescriptive content in descriptive artifacts.
  - [[function-merge]]: one role absorbing another's function incrementally.
  - [[scope-rigidity]]: over-specification blocking productive work.

## Output format (fill-in block)

### System and scope
- System:
- Artifacts examined:
- Role declarations: (explicit / implicit)

### Role boundaries
- Artifact:
  - Declared role:
  - Actual function:
  - Role-pure: (yes / no — describe violation)

### Normativity leaks
- Artifact:
  - Prescriptive content found:
  - Role boundary violated:

### Function merges
- Artifact:
  - Functions absorbed from:
  - Original role:

### Decomposition depth
- Layers of mechanically enforced separation:
- Layers enforced only by interpretation:

### Refinement stability
- Recent additions eliminate error classes: (yes / no / unclear)
- Scope rigidity indicators:

### Misuse scan (quick)
- Over-decomposition risk:
- Decomposition-as-gatekeeping risk:
- Terminology inflation risk:

## Links

- [[Decomposition]]
- [[role-boundary]]
- [[role-purity]]
- [[role-collapse]]
- [[normativity-leak]]
- [[function-merge]]
- [[decomposition-depth]]
- [[refinement-stability]]
- [[scope-rigidity]]
