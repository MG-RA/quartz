"""CLI entrypoint for irrev."""

import sys
from pathlib import Path

import click

from . import __version__


@click.group()
@click.version_option(__version__, prog_name="irrev")
@click.option(
    "--vault",
    "-v",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default="./content",
    help="Path to vault content directory",
)
@click.pass_context
def cli(ctx: click.Context, vault: Path) -> None:
    """irrev - Semantic compiler for the irreversibility vault.

    Lint, pack, and generate registry artifacts from your vault.
    """
    ctx.ensure_object(dict)
    ctx.obj["vault"] = vault.resolve()


@cli.command()
@click.option(
    "--fail-on",
    type=click.Choice(["error", "warning"]),
    default="error",
    help="Exit with error if this level or higher found",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON",
)
@click.option(
    "--flat",
    is_flag=True,
    help="Use flat output (legacy) instead of invariant-grouped (default)",
)
@click.option(
    "--invariant",
    "invariant_filter",
    type=str,
    default=None,
    metavar="INVARIANT_ID",
    help="Only run rules for this invariant (e.g., --invariant decomposition)",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat unclassified rules as errors (prevents scope creep in CI)",
)
@click.option(
    "--summary",
    is_flag=True,
    help="Print only invariant status line (for commits/docs)",
)
@click.option(
    "--explain",
    "explain_rule",
    type=str,
    default=None,
    metavar="RULE_ID",
    help="Explain a specific rule and exit (e.g., --explain layer-violation)",
)
@click.option(
    "--explain-invariant",
    "explain_invariant_id",
    type=str,
    default=None,
    metavar="INVARIANT_ID",
    help="Explain an invariant and its rules (e.g., --explain-invariant decomposition)",
)
@click.option(
    "--trace",
    "trace_note",
    type=str,
    default=None,
    metavar="NOTE",
    help="Show dependency chain for a specific note (e.g., --trace admissibility)",
)
@click.pass_context
def lint(
    ctx: click.Context,
    fail_on: str,
    output_json: bool,
    flat: bool,
    invariant_filter: str | None,
    strict: bool,
    summary: bool,
    explain_rule: str | None,
    explain_invariant_id: str | None,
    trace_note: str | None,
) -> None:
    """Check vault for structural violations.

    By default, results are grouped by invariant to surface infrastructure-level
    failure modes. Use --flat for legacy file-based output.

    The 4 kernel invariants:
    - decomposition: Objects/operators separation, role boundaries, no function merging
    - governance: Non-exemption, enforceability, self-correction surfaces
    - attribution: Responsibility mapping, diagnostics can't prescribe, no misplaced blame
    - irreversibility: Persistence, erasure cost declaration, accounting requirements, rollback denial

    Structural rules (dependency-cycle, broken-link, alias-drift) ensure graph coherence,
    which emerges from joint invariant compliance.

    Use --explain RULE_ID to see detailed documentation for a rule.
    Use --explain-invariant INVARIANT_ID to see what an invariant enforces.
    Use --trace NOTE to see the dependency chain for a specific note.
    """
    from .commands.lint import run_explain, run_explain_invariant, run_lint, run_trace

    # Handle --explain-invariant mode
    if explain_invariant_id:
        exit_code = run_explain_invariant(explain_invariant_id)
        sys.exit(exit_code)

    # Handle --explain mode
    if explain_rule:
        exit_code = run_explain(explain_rule)
        sys.exit(exit_code)

    # Handle --trace mode
    if trace_note:
        exit_code = run_trace(ctx.obj["vault"], trace_note)
        sys.exit(exit_code)

    exit_code = run_lint(ctx.obj["vault"], fail_on, output_json, flat, invariant_filter, strict, summary)
    sys.exit(exit_code)


@cli.command()
@click.argument("kind", type=click.Choice(["domain", "concept", "projection"]))
@click.argument("target")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "json", "txt"]),
    default="md",
    help="Output format",
)
@click.option(
    "--include-diagnostics",
    is_flag=True,
    help="Include diagnostic notes in pack",
)
@click.option(
    "--explain",
    is_flag=True,
    help="Explain why each file is included",
)
@click.pass_context
def pack(
    ctx: click.Context,
    kind: str,
    target: str,
    output_format: str,
    include_diagnostics: bool,
    explain: bool,
) -> None:
    """Generate context packs deterministically.

    Examples:

        irrev pack domain "2012-2026 AI Systems"

        irrev pack concept irreversibility --explain

        irrev pack projection Stoicism --include-diagnostics
    """
    from .commands.pack import run_pack

    exit_code = run_pack(
        ctx.obj["vault"],
        kind,
        target,
        output_format,
        include_diagnostics,
        explain,
    )
    sys.exit(exit_code)


@cli.group()
def registry() -> None:
    """Registry generation commands."""
    pass


@registry.command("build")
@click.option(
    "--out",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path (default: stdout)",
)
@click.pass_context
def registry_build(ctx: click.Context, out: Path | None) -> None:
    """Generate registry from vault concepts.

    Reads concept layers and dependencies, produces markdown tables
    matching the Registry format.

    Examples:

        irrev registry build

        irrev registry build --out Registry.generated.md
    """
    from .commands.registry import run_build

    exit_code = run_build(ctx.obj["vault"], str(out) if out else None)
    sys.exit(exit_code)


@registry.command("diff")
@click.pass_context
def registry_diff(ctx: click.Context) -> None:
    """Compare generated registry with existing Registry file.

    Shows differences between what the concepts define and what
    the Registry file contains.
    """
    from .commands.registry import run_diff

    exit_code = run_diff(ctx.obj["vault"])
    sys.exit(exit_code)


def main() -> None:
    """Main entrypoint."""
    cli()


if __name__ == "__main__":
    main()
