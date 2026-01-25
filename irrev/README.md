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
