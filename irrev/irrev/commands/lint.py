"""Lint command implementation."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault
from ..vault.rules import LintResult, LintRules


def run_lint(
    vault_path: Path,
    fail_on: str = "error",
    output_json: bool = False,
) -> int:
    """Run lint checks on the vault.

    Args:
        vault_path: Path to vault content directory
        fail_on: Exit with error if this level or higher found ("error" or "warning")
        output_json: Output results as JSON instead of human-readable

    Returns:
        Exit code (0 = success, 1 = failures found)
    """
    console = Console(stderr=True)

    # Load vault
    console.print(f"Loading vault from {vault_path}...", style="dim")
    vault = load_vault(vault_path)

    # Build dependency graph
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    # Run lint rules
    rules = LintRules(vault, graph)
    results = rules.run_all()

    # Sort by level (errors first)
    level_order = {"error": 0, "warning": 1, "info": 2}
    results.sort(key=lambda r: (level_order.get(r.level, 99), r.file.name))

    # Count by level
    counts = {"error": 0, "warning": 0, "info": 0}
    for r in results:
        counts[r.level] = counts.get(r.level, 0) + 1

    if output_json:
        output = {
            "errors": [_result_to_dict(r) for r in results if r.level == "error"],
            "warnings": [_result_to_dict(r) for r in results if r.level == "warning"],
            "info": [_result_to_dict(r) for r in results if r.level == "info"],
            "summary": {
                "concepts": len(vault.concepts),
                "diagnostics": len(vault.diagnostics),
                "domains": len(vault.domains),
                "projections": len(vault.projections),
                "papers": len(vault.papers),
                "total_notes": len(vault.all_notes),
                "errors": counts["error"],
                "warnings": counts["warning"],
                "info": counts["info"],
            },
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_human_output(console, results, counts, vault)

    # Determine exit code
    if fail_on == "warning":
        if counts["error"] > 0 or counts["warning"] > 0:
            return 1
    else:  # fail_on == "error"
        if counts["error"] > 0:
            return 1

    return 0


def _result_to_dict(result: LintResult) -> dict:
    """Convert LintResult to JSON-serializable dict."""
    return {
        "level": result.level,
        "rule": result.rule,
        "file": str(result.file),
        "message": result.message,
        "line": result.line,
    }


def _print_human_output(
    console: Console,
    results: list[LintResult],
    counts: dict[str, int],
    vault,
) -> None:
    """Print human-readable lint output."""
    # Print results
    for result in results:
        if result.level == "error":
            style = "bold red"
            prefix = "ERROR"
        elif result.level == "warning":
            style = "yellow"
            prefix = "WARN"
        else:
            style = "dim"
            prefix = "INFO"

        file_ref = result.file.name
        if result.line:
            file_ref += f":{result.line}"

        console.print(f"{prefix}: {file_ref} - {result.message}", style=style)

    # Print summary
    console.print()

    table = Table(title="Vault Summary", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")

    table.add_row("Concepts", str(len(vault.concepts)))
    table.add_row("Diagnostics", str(len(vault.diagnostics)))
    table.add_row("Domains", str(len(vault.domains)))
    table.add_row("Projections", str(len(vault.projections)))
    table.add_row("Papers", str(len(vault.papers)))
    table.add_row("Total notes", str(len(vault.all_notes)))

    console.print(table)

    # Print lint summary
    console.print()
    if counts["error"] > 0:
        console.print(f"❌ {counts['error']} error(s)", style="bold red")
    if counts["warning"] > 0:
        console.print(f"⚠️  {counts['warning']} warning(s)", style="yellow")
    if counts["info"] > 0:
        console.print(f"ℹ️  {counts['info']} info(s)", style="dim")

    if counts["error"] == 0 and counts["warning"] == 0:
        console.print("✅ No errors or warnings", style="bold green")
