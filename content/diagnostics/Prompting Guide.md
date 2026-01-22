# Prompting Guide

Tags: #diagnostic #meta

This note defines prompt patterns for using AI/code agents with this vault while preserving scope, avoiding invention of new primitives, and preventing self-sealing explanations.

> [!info]
> Orientation: Prompt patterns for using AI/code agents with this vault.

---

## Core rule

> [!note]
> Constraint: `/concepts` are the source of truth for definitions; do not introduce new primitives.

Agents must treat `/concepts` as the source of truth for definitions.
They may summarize, cross-link, and apply concepts, but must not introduce new primitives without explicit extraction.

---

## Agent quick start

If you are an AI agent reading this vault for the first time:

1. Read: `INDEX.md` (orientation)
2. Load: `Prompting Guide.md` (this file)
3. Load: `Failure Modes of the Irreversibility Lens.md`
4. Default mode: "Concept-locked" boilerplate

You now have sufficient context for most tasks.

---

## Context loading strategies

Different tasks require different context loads. Choose based on task type:

### Minimal load (quick checks)

Load only: `persistent-difference`, `erasure-cost`, `accounting-failure`

Use for: definition checks, simple audits, quick validation

### Core concepts load

Load: `persistent-difference`, `erasure-cost`, `erasure-asymmetry`, `displacement`, `absorption`, `constraint-load`, `accounting-failure`

Use for: most diagnostic work, reasoning about cost routing

### Full diagnostic load

Load: all `/concepts` + `Failure Modes of the Irreversibility Lens`

Use for: comprehensive audits, paper-level analysis, domain application

### Application load

Load: `/concepts` + relevant domain note + [[Domain Template]]

Use for: applying the framework to specific systems

### Loading order for concept chains

When a concept depends on others, load dependencies first:

- `transformation-space` → `persistent-difference` → `erasure-cost` → `displacement`
- `constraint-load` → `constraint-accumulation` → `collapse-surface`

### Layer-aware loading

Concepts are organized by structural layer (see [[Decomposition Map]]):

**Primitives:** `difference`, `persistence`, `persistent-difference`, `erasure-cost`, `erasure-asymmetry`, `asymmetry`, `constraint`, `accumulation`

**First-order composites:** `irreversibility`, `displacement`, `absorption`, `propagation`, `constraint-load`, `constraint-accumulation`, `persistence-gradient`

**Accounting-level:** `tracking-mechanism`, `accounting-failure`, `collapse-surface`

**Selector-level:** `admissibility`

**Meta-analytical:** `lens`, `transformation-space`

**Failure states:** `brittleness`, `saturation`

Load primitives first when building understanding from scratch. Load accounting-level concepts when diagnosing specific failures.

---

## Preferred context selection

Use one of these context scopes:

- **Concept-only reasoning:** `/concepts` only  
  Use when you want precise definitions and clean application.

- **Diagnostics-only auditing:** `/diagnostics` + `/concepts`  
  Use when you want checks, failure modes, and scope enforcement.

- **Paper-based orientation:** `/papers` + `/concepts`  
  Use when you want narrative structure, but definitions still come from concepts.

- **Domain application:** `/domains` + `/concepts` + `/diagnostics`  
  Use when analyzing a real system and guarding against overreach.

---

## Gold-standard prompt patterns

### 1) Definition fidelity check
**Goal:** verify a note uses concepts correctly.

Prompt:
- “Using only `/concepts`, check whether this note uses [[persistent-difference]], [[erasure-cost]], and [[displacement]] correctly. List any mismatches and propose minimal edits. Do not add new concepts.”

Output format:
- Misuse → why → minimal correction

---

### 2) Link integrity and missing dependencies
**Goal:** find unl inked concept mentions and missing prerequisites.

Prompt:
- “Scan this note and identify terms that match existing concepts but are unlinked. Suggest links. If the note uses a concept that requires prerequisites (e.g. persistence without transformation space), flag it.”

---

### 3) Overreach audit (diagnostic vs normative)
**Goal:** catch prescription creep.

Prompt:
- “Audit this text for normativity or prescriptions. Replace prescriptive sentences with diagnostic equivalents, preserving meaning. If value judgments are unavoidable, mark them explicitly as values.”

---

### 4) False positive / misuse audit
**Goal:** prevent self-sealing explanations.

Prompt:
- “Using [[Failure Modes of the Irreversibility Lens]], identify where this analysis might be over-applied. Provide 3 plausible alternative interpretations that do not assume accounting failure.”

---

### 5) Domain diagnosis template fill
**Goal:** apply the framework without improvising.

Prompt:
- “Fill [[Domain Template]] using only the existing concept notes. Any claim not supported by the vault should be labeled as an assumption.”

---

## Red-flag prompt patterns (avoid)

- “Extend the framework with new concepts” (unless you are intentionally doing extraction work)
- “Prove the framework explains X” (invites self-sealing)
- “Optimize constraint load” (invites metric reification and prescription drift)
- “Translate everything into a single model” (invites totalizing explanation)

---

## Output discipline

When an agent answers, require:

- **Citations by link:** reference concepts as `[[...]]`
- **Scope tags:** label sentences as:
  - (Definition) derived from concept notes
  - (Inference) reasonable inference
  - (Assumption) requires external facts
- **No new primitives:** if needed, propose candidates in a separate section titled “Possible extractions”

---

## Minimal prompt boilerplates

Each boilerplate includes output discipline requirements.

### "Concept-locked" boilerplate

> Use only `/concepts` for definitions. If a term is not in `/concepts`, treat it as undefined. Do not invent new primitives.
>
> **Output format:** Use `[[concept-name]]` links. Tag claims as (Definition), (Inference), or (Assumption). No new terms without "Possible extractions" section.

### "Diagnostic-only" boilerplate

> You are auditing for scope, misuse, and false positives. Do not propose actions or solutions.
>
> **Output format:** List findings as: Issue → Evidence → Correction. Reference failure modes by number.

### "Application mode" boilerplate

> Apply the framework to the domain. Separate observations from assumptions. Identify displacement and erasure costs explicitly.
>
> **Output format:** Follow the domain template structure. Mark each claim with (Definition), (Inference), or (Assumption).

---

## Recovery prompts

Use these when an agent drifts off-track mid-conversation:

- "Stop. Re-read [[persistent-difference]]. Does your last claim match the definition?"
- "You introduced a term not in `/concepts`. Retract or extract."
- "Check your output against [[Failure Modes of the Irreversibility Lens]] #2 (totalizing explanation)."
- "You proposed an action. Restate as a diagnostic observation only."
- "Your explanation cannot be falsified. Provide 2 alternative interpretations."

---

## Maintenance

If this guide stops changing, that is a warning sign.
Update it whenever an agent produces:
- a self-sealing explanation
- a reified metric
- a hidden prescription
- a new primitive that should have been a link
