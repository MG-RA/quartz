# irrev

Semantic compiler for the irreversibility vault. Lint, pack, and generate registry artifacts.

## Installation

```bash
cd irrev
uv sync
```

## Commands

### `irrev lint`

Check vault for structural violations.

```bash
uv run irrev -v ../content lint
uv run irrev -v ../content lint --json
uv run irrev -v ../content lint --fail-on warning
```

Checks:
- **layer-violation**: Concepts depending on higher-layer concepts (e.g., accounting → selector)
- **dependency-cycle**: Circular dependencies among concepts
- **missing-dependencies**: Concepts without `## Structural dependencies` section
- **broken-link**: Wiki-links pointing to non-existent notes
- **forbidden-edge**: Concepts linking directly to papers
- **alias-drift**: Using non-canonical names instead of canonical concept names
- **missing-role**: Notes without `role` in frontmatter

### `irrev pack`

Generate dependency-closed context packs for agents.

```bash
uv run irrev -v ../content pack concept irreversibility
uv run irrev -v ../content pack concept irreversibility --explain
uv run irrev -v ../content pack domain "2012-2026 AI Systems" --include-diagnostics
uv run irrev -v ../content pack projection Stoicism --format json
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

## Development

```bash
uv sync --dev
uv run pytest
```
