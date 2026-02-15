---
aliases:
  - "prescriptive leak"
  - "hidden normativity"
layer: failure-state
role: concept
canonical: true
invariants:
  - decomposition
---

# Normativity Leak

## Definition

**Normativity leak** is a failure state in which prescriptive, evaluative, or action-directing content appears in artifacts whose declared role is descriptive. It is the specific form of [[role-collapse]] where the object/operator boundary is violated from the object side: descriptions carry implicit "should" claims that are not declared as operator output.

Normativity leaks are particularly difficult to detect because they often use structural or technical language. Common patterns:

- "The correct interpretation is..." (authority claim in a definition)
- "This naturally leads to..." (prescription disguised as consequence)
- "Best practice is..." (evaluation embedded in description)
- Definitions that select for specific outcomes without declaring evaluative criteria.

The structural hazard: once normativity leaks into descriptions, the descriptions become load-bearing for specific outcomes. Subsequent refinement cannot distinguish between improving accuracy and changing prescription.

## Structural dependencies

- [[role-boundary]]

## What this is NOT

- Not strong language (forceful descriptions can be role-pure; mild prescriptions are still normativity leaks)
- Not opinion (stating an opinion in an opinion-bearing artifact is not a leak; embedding evaluation in a descriptive artifact is)
- Not consequence (describing structural consequences is not normative; implying that those consequences mandate action is)

## Structural role

Normativity leak is a failure state detectable by scanning descriptive artifacts for prescriptive, evaluative, or action-directing language patterns. The existing lint rules (prescriptive language detection in concept definitions) are direct implementations of normativity leak detection. Where leaks are found, the diagnostic identifies what prescriptive content exists and which [[role-boundary]] it violates.
