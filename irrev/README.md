# irrev

Semantic compiler for the irreversibility vault. Lint, pack, and generate registry artifacts.

## Installation

```bash
cd irrev
uv sync
```

This creates a virtual environment at `irrev/.venv/` and installs the `irrev` CLI into it.

## Commands

### `irrev lint`

Check vault for structural violations.

```bash
uv run irrev -v ../content lint
uv run irrev -v ../content lint --json
uv run irrev -v ../content lint --fail-on warning
uv run irrev -v ../content lint --summary
uv run irrev -v ../content lint --invariant decomposition
uv run irrev -v ../content lint --explain layer-violation
uv run irrev -v ../content lint --trace admissibility
```

Notes:
- Default output is grouped by invariant (decomposition/governance/attribution/irreversibility) to keep failures interpretable.
- Use `--explain RULE_ID` for authoritative rule docs instead of relying on a hardcoded list here.

### `irrev pack`

Generate dependency-closed context packs for agents.

```bash
uv run irrev -v ../content pack concept irreversibility
uv run irrev -v ../content pack concept irreversibility --explain
uv run irrev -v ../content pack domain "2012-2026 AI Systems" --include-diagnostics
uv run irrev -v ../content pack projection Stoicism --format json
uv run irrev -v ../content pack projection OpenAI --include-diagnostics --format md --explain > openai.pack.md
```

Options:
- `--format md|json|txt`: Output format (default: md)
- `--include-diagnostics`: Include diagnostic notes in pack
- `--explain`: Show why each file is included

### `irrev registry`

Generate and compare registry tables.

```bash
uv run irrev -v ../content registry build
uv run irrev -v ../content registry build --out Registry.generated.md
uv run irrev -v ../content registry build --in-place
uv run irrev -v ../content registry diff
```

### `irrev hubs`

Detect latent hub candidates by cross-layer dependency concentration (mechanisms + accounting + failure states).

```bash
uv run irrev -v ../content hubs
uv run irrev -v ../content hubs --top 50
uv run irrev -v ../content hubs --all
uv run irrev -v ../content hubs --all-notes
uv run irrev -v ../content hubs --rank score --w-mechanism 1.5 --w-failure 1.25
uv run irrev -v ../content hubs --min-mechanisms 2 --min-accounting 2 --min-failure-states 1
```

### Hub policy (`content/meta/hubs.yml`)

If `content/meta/hubs.yml` exists, lint enforces that hub concepts include required headings
(`hub-required-headings`). This is intended to keep load-bearing concepts structurally explicit
without changing the layer system.

### `irrev graph`

Inspect graph structure (concept dependencies vs full vault wiki-links).

```bash
uv run irrev -v ../content graph --concepts-only
uv run irrev -v ../content graph --all-notes --format dot --out vault.dot
uv run irrev -v ../content graph --concepts-only --format svg --out concepts-only.svg
uv run irrev -v ../content graph --all-notes --format html --out all-notes.htm
uv run irrev -v ../content graph --all-notes --format svg --plain --out all-notes.plain.svg
```

### `irrev audit`

Generate a structural vault report from Obsidian Bases CSV exports.

```bash
uv run irrev audit "./content/exports bases"
uv run irrev audit "./content/exports bases" --out report.md
```

This command parses CSV files exported from Obsidian Bases and generates a Markdown report using the irreversibility accounting framework vocabulary.

**Expected CSV files** (all optional; uses what's available):

- `Concept topology.csv` - layer distribution
- `Dependency audit.csv` - hub spine (high-outlink concepts)
- `Primitive coverage audit.csv` - domain primitive gaps
- `Diagnostics inventory.csv` - diagnostics without dependencies
- `Projections.csv` - projection concept coverage
- `Invariants inventory.csv` - invariant integrity
- `Full vault audit.csv` - orphan/high-link detection

**Report sections:**

1. Executive Summary - key findings (orphans, hub candidates, primitive gaps)
2. Concept Graph Topology - layer distribution, hub spine
3. Domain Primitive Coverage - missing foundational concept links
4. Orphan and High-Link Notes - unintegrated content, reference hubs
5. Diagnostics Inventory - grouped by subfolder, dependency gaps
6. Projections Coverage - core concept linkage matrix
7. Invariants Integrity - structural invariant status
8. Constraint-Load Summary - where cost accumulates, routing pressure points
9. Recommended Actions - prioritized fixes

The report uses framework vocabulary: constraint-load, routing pressure, accounting-failure, residual, displacement, etc.

## Neo4j read-only MCP server

This repo also includes a small **read-only** MCP server for querying a Neo4j-backed vault graph over stdio (intended for Codex/agents).

Docs + sample queries: `irrev/MCP_NEO4J_READONLY.md`.

### `irrev junctions concept-audit`

Generate a concept audit report (Phase 1 of junctions detection).

```bash
uv run irrev -v ../content junctions concept-audit
uv run irrev -v ../content junctions concept-audit --top 10
uv run irrev -v ../content junctions concept-audit --all --format json
uv run irrev -v ../content junctions concept-audit --out audit.md
```

Audits load-bearing concepts for:

- Role purity (no operator/prescription bleed)
- Dependency fidelity (deps actually used in body)
- Structural completeness (Definition, Structural dependencies, What this is NOT sections)

### `irrev junctions definition-analysis`

Analyze concept definition semantics (Phase 1b): operational framing, negation density, and implicit dependencies.

```bash
uv run irrev -v ../content junctions definition-analysis
uv run irrev -v ../content junctions definition-analysis --all --format json
```

### `irrev junctions domain-audit`

Audit domains for implied concept dependencies (2-hop: domain → concept → concept) that aren’t declared as direct links.

```bash
uv run irrev -v ../content junctions domain-audit
uv run irrev -v ../content junctions domain-audit --domain "Digital Platforms"
uv run irrev -v ../content junctions domain-audit --via links   # mirrors Neo4j LINKS_TO
uv run irrev -v ../content junctions domain-audit --via depends_on
```

### `irrev junctions implicit`

Generalize the 2-hop implied-dependency audit beyond domains.

```bash
uv run irrev -v ../content junctions implicit --role projection --top 10
uv run irrev -v ../content junctions implicit --role paper --all --format json
```

## Community detection (layers vs emergent structure)

Before enforcing layers as schema, you can compare **emergent communities** in the concept graph to the declared `layer` labels:

```bash
uv run irrev -v ../content communities --mode links
uv run irrev -v ../content communities --mode depends_on
uv run irrev -v ../content communities --mode both --format json
```

## Integration with vault workflow

Run lint before committing changes:

```bash
uv run irrev -v ../content lint --fail-on warning
```

Generate context packs for AI agents:

```bash
uv run irrev -v ../content pack concept persistent-difference --explain > context.md
```

Check registry drift after modifying concepts:

```bash
uv run irrev -v ../content registry diff
```

Update the checked-in graph artifacts (SVG + HTML) under `content/meta/graphs/`:

```powershell
.\scripts\update-graphs.ps1
```

## Git pre-commit hook (registry + lint)

This repo includes a versioned hook script in `.githooks/pre-commit` that:
- regenerates the Registry tables in-place
- runs `irrev lint`

Enable it for this repo:

```powershell
.\scripts\setup-githooks.ps1
```

## Layer hierarchy

The linter enforces this dependency hierarchy (lower cannot depend on higher):

1. **primitive / foundational**: `transformation-space`, `difference`, `persistence`, `erasure-cost`, `asymmetry`, `constraint`, `accumulation`
2. **first-order**: `persistent-difference`, `irreversibility`, `displacement`, `absorption`, etc.
3. **mechanism**: `rollback`, etc.
4. **accounting**: `tracking-mechanism`, `accounting-failure`, `collapse-surface`
5. **selector / failure-state / meta-analytical**: `admissibility`, `brittleness`, `saturation`, `lens`

## Windows shortcut (no `uv run`)

After `uv sync`, you can run the CLI directly (from the repo root):

```powershell
.\irrev\.venv\Scripts\irrev.exe -v .\content lint
.\irrev\.venv\Scripts\irrev.exe -v .\content registry diff
.\irrev\.venv\Scripts\irrev.exe -v .\content pack projection "OpenAI" --include-diagnostics --format md --explain
```

## Development

```bash
uv sync --dev
uv run pytest
```
