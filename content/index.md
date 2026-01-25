---
role: support
type: index
canonical: true
---

*A diagnostic framework for reasoning about systems under irreversible accumulation.*

This vault contains a **constraint-first diagnostic lens** for analyzing systems that produce persistent effects while operating as if those effects were reversible.

> [!note]
> Non-claim: The framework is not a theory, not normative, and not predictive.

It constrains explanations by tracking what persists, where costs go, and which options disappear over time.

> [!note]
> Naming note: “Accounting” is used in the literal sense — keeping a ledger of residuals, erasure costs, and constraint accumulation — not in the finance-only sense.

---
## How to Read This Vault

There is **no single correct order**.  
Choose a path based on intent:

- If you want the **core argument** -> start with the papers
- If you want the **conceptual vocabulary** -> browse the concepts
- If you want the **diagnostic tool** -> go to diagnostics
- If you want **limits and guardrails** -> read the meta notes

Links, not sequence, carry meaning.

---
## Core Papers

These are *compiled views* over the concept graph.

- [[Irreversibility Accounting (Paper)]]
  - Introduces the diagnostic lens
  - Defines the failure mode of accounting failure
  - Explains how systems lose options over time

- [[The Structure of Agency (Derived)]]
  - Interprets agency under irreversible accumulation
  - Reclassifies agency as navigation under constraint
  - Depends on Irreversibility Accounting

- [[Ontology of Irreversibility]]
  - Frozen orientation note from concept-only graph + hub detection
  - Clarifies the ontology vs. operator boundary

---
## Concept Vocabulary

Canonical concept definitions live in `/concepts`.

- Core spine / hubs:
  - [[persistent-difference]]
  - [[erasure-cost]]
  - [[residual]]
  - [[constraint-load]]
  - [[admissibility]]
  - [[feasible-set]]

- Layer bundles / dependency classes: [[Irreversibility Accounting (Registry)#Dependency classes (by layer)]]
- Structural hierarchy: [[Decomposition]]

---
## Diagnostics

These notes define **how to use the lens** without turning it into doctrine.

- [[Failure Modes of the Irreversibility Lens]]
- [[Irreversibility Accounting (Registry)#Operator (diagnostic sequence)]]
- *(additional diagnostic checklists and lenses live here)*

Diagnostics ask questions.  
They do not propose solutions.

---
## Meta / Guardrails

These notes constrain misuse, overreach, and self-sealing interpretations.

- [[Decomposition]] - Structural clarification of primitive vs composed concepts
- *(Non-claims, limits, scope clarifications)*

If the framework starts to feel obvious, total, or morally loaded, return here.

---
## Structural Maps (Graphs)

- [[Concept Graphs]]
  - Concepts-only (structural dependencies)
  - All-notes (wiki-links across vault)
  - Includes interactive pan/zoom versions for web + local

---
## Domains (Applications)

Domain notes apply the lens to specific systems.  
They do not introduce new concepts.

- [[Human History]]
- [[2006-2026 Digital Platforms]]
- [[2008-2026 Financial Infrastructure]]
- [[2010-2026 Software Supply Chains]]
- [[2012-2026 AI Systems]]

When a domain note invents vocabulary, it indicates a candidate extraction to `/concepts`.

---

## How to Use This with Code / AI Agents

This vault is structured for **constrained reasoning**:

- Folders define *note role*, not meaning
- Links define dependencies
- Concepts are atomic and stable
- Papers are projections over the graph

Effective agent prompts include:
- "Reason only using `/concepts`"
- "Audit this domain note using `/diagnostics`"
- "Check for accounting failure using defined concepts only"
- "Do not introduce new primitives"

[[Prompting Guide]]

This structure minimizes hallucination by **removing ambiguity at the ontology layer**.

---

## Design Principles (Explicit)

- Links over hierarchy
- Few primitives, many relations
- Diagnostics before prescriptions
- Scope before scale
- Accounting before optimization

---
## Status

This vault is a **thinking environment**, not a publication.  
If the origin is forgotten and the concepts remain usable, it has succeeded.
