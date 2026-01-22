*A diagnostic framework for reasoning about systems under irreversible accumulation.*

This vault contains a **constraint-first diagnostic lens** for analyzing systems that produce persistent effects while operating as if those effects were reversible.

> [!note]
> Non-claim: The framework is not a theory, not normative, and not predictive.

It constrains explanations by tracking what persists, where costs go, and which options disappear over time.

---
## How to Read This Vault

There is **no single correct order**.  
Choose a path based on intent:

- If you want the **core argument** → start with the papers  
- If you want the **conceptual vocabulary** → browse the concepts  
- If you want the **diagnostic tool** → go to diagnostics  
- If you want **limits and guardrails** → read the meta notes  

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

---
## Core Concepts (Lexicon)

These notes define the **minimal vocabulary** of the framework.
They are atomic, non-normative, and reusable across domains.

See [[Decomposition Map]] for the full structural hierarchy.

### Foundational (Non-Primitive)

Foundational concepts have no dependencies but are not primitives because they define the analysis frame rather than the object of analysis.

- [[transformation-space]]

### Primitives

- [[difference]]
- [[persistence]]
- [[erasure-cost]]
- [[erasure-asymmetry]]
- [[asymmetry]]
- [[constraint]]
- [[accumulation]]

### First-Order Composites

- [[persistent-difference]]
- [[irreversibility]]
- [[displacement]]
- [[absorption]]
- [[propagation]]
- [[constraint-load]]
- [[constraint-accumulation]]
- [[persistence-gradient]]

### Accounting-Level

- [[tracking-mechanism]]
- [[accounting-failure]]
- [[collapse-surface]]

### Selector

- [[admissibility]]

### Failure States

- [[brittleness]]
- [[saturation]]

### Mechanisms & Meta-Analytical

- [[rollback]]
- [[lens]]

---
## Diagnostics

These notes define **how to use the lens** without turning it into doctrine.

- [[Failure Modes of the Irreversibility Lens]]
- *(additional diagnostic checklists and lenses live here)*

Diagnostics ask questions.  
They do not propose solutions.

---
## Meta / Guardrails

These notes constrain misuse, overreach, and self-sealing interpretations.

- [[Decomposition Map]] — Structural clarification of primitive vs composed concepts
- *(Non-claims, limits, scope clarifications)*

If the framework starts to feel obvious, total, or morally loaded, return here.

---
## Domains (Applications)

Domain notes apply the lens to specific systems.  
They do not introduce new concepts.

- [[Human History]]
- [[2006-2026 Digital Platforms]]
- [[2008-2026 Financial Infrastructure]]
- [[2010-2026 Software Supply Chains]]
- [[2012-2026 AI Systems]]

If a domain note invents vocabulary, extract it to `/concepts`.

---

## How to Use This with Code / AI Agents

This vault is structured for **constrained reasoning**:

- Folders define *note role*, not meaning
- Links define dependencies
- Concepts are atomic and stable
- Papers are projections over the graph

Effective agent prompts include:
- “Reason only using `/concepts`”
- “Audit this domain note using `/diagnostics`”
- “Check for accounting failure using defined concepts only”
- “Do not introduce new primitives”

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
