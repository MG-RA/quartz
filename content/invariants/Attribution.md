---
role: invariant
invariant_id: attribution
status: structural
canonical: true
---

# Attribution

> [!note]
> Scope: Structural clarification only. This is not a theory, diagnostic, projection, or advice.

## Invariant statements

1) **Agency is layered**  
2) **Responsibility is role-dependent**  
3) **Maturity without structure is a trap**

## Governance vs attribution (orthogonal)

- **Governance** answers: Who is constrained by the rules they impose? ([[Governance]])
- **Attribution** answers: Where can responsibility be meaningfully assigned (by agency layer and controlled degrees of freedom)?

These concerns interact but do not reduce to each other:

| Axis | Question | Constrains |
| --- | --- | --- |
| Power / enforcement | Who can impose or enforce constraints? | actors, tools, rule surfaces |
| Explanation / attribution | Where is responsibility assignable? | claims about actors/roles |

## Independence cases (structural)

- Governance holds, attribution fails: no exemptions, but responsibility claims are assigned to roles that do not control the relevant degrees of freedom.
- Attribution holds, governance fails: responsibility claims are correctly assigned, but responsible roles are exempt from the constraints they impose.
- Both fail: exemptions exist and responsibility claims are misassigned.

## Levels of agency (minimal)

### 1) Causal agency

The capacity for a system or component to produce effects in the world (changes, differences, constraints) regardless of intent.

### 2) Intentional agency

The capacity for an actor to form intentions and select actions within perceived options and constraints.

### 3) Structural / governance agency

The capacity for a role (human or tool) to shape the constraint landscape by defining, enforcing, or changing rules, interfaces, incentives, and enforcement mechanisms.

## Responsibility mapped to agency levels

This vault treats "responsibility" as an attribution surface that varies by role and layer. A responsibility claim is only meaningful at the agency layer that controls the relevant degrees of freedom.

### Causal responsibility (causal layer)

Attribution that a mechanism produced a difference (independent of intent).

### Intentional responsibility (intentional layer)

Attribution that an actor selected an action among options (relative to constraints and available information).

### Governance responsibility (structural layer)

Attribution that a role controlled (or failed to control) the rules and enforcement surfaces that shape admissible transitions and error visibility.

## What this prevents

- Attribution of structural effects to individual intent in place of structure tracking
- Over-attribution to individuals for effects produced by governance surfaces
- Authority inflation via "maturity" claims without mechanical constraints
- Collapsing object claims into operator judgments (and vice versa)

## What this does NOT claim

- No claim of superiority, rank, or virtue by agency layer
- No claim that responsibility is total, singular, or stable across contexts
- No claim that "maturity" is an individual property independent of structure
- No claim that attribution implies punishment, praise, or prescriptions

## Minimal decomposition

- [[control-surface]] declares where control can vary for a given role.
- [[agency-layer]] indexes the type of control being claimed (causal / intentional / structural).
- [[degrees-of-freedom]] names what the role could actually vary — the operational test for meaningful attribution.
- [[responsibility-claim]] binds role, layer, degrees of freedom, and effect into an auditable unit.
- [[attribution-admissibility]] determines whether a responsibility claim is structurally valid.

## Structural consequences (non-normative)

- Responsibility claims that exceed available degrees of freedom are structurally empty ([[over-attribution]]).
- Responsibility gaps where control existed produce unaccounted effects ([[under-attribution]]).
- Conflating agency layers makes attribution claims unevaluable ([[layer-collapse]]).
- Responsibility can route away from control surfaces ([[attribution-displacement]]).
- Responsibility bindings can outlive the control surfaces they were indexed to ([[attribution-residual]]).

## Summary (links)

- See [[Decomposition]] for the object/operator/boundary/governance decomposition this supports.
- See [[Governance]] for the non-exemption constraint that stabilizes governance responsibility.
- See [[Irreversibility (Invariant)]] for the structural condition that makes cost-routing and option loss non-trivial under scale.
