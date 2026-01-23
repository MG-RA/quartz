"""Lint command implementation."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault
from ..vault.rules import RULE_EXPLANATIONS, LintResult, LintRules, get_rule_ids


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


def run_explain(rule_id: str) -> int:
    """Explain a specific lint rule.

    Args:
        rule_id: Rule ID to explain

    Returns:
        Exit code (0 = success, 1 = rule not found)
    """
    console = Console()

    # Normalize rule_id
    rule_id = rule_id.lower().strip()

    if rule_id not in RULE_EXPLANATIONS:
        console.print(f"Unknown rule: {rule_id}", style="bold red")
        console.print()
        console.print("Known rules:", style="bold")
        for rid in sorted(get_rule_ids()):
            console.print(f"  - {rid}")
        return 1

    # Print explanation
    from rich.markdown import Markdown

    explanation = RULE_EXPLANATIONS[rule_id]
    console.print(Markdown(explanation))
    return 0


def run_trace(vault_path: Path, note_name: str) -> int:
    """Show dependency chain for a specific note.

    Args:
        vault_path: Path to vault content directory
        note_name: Name of the note to trace

    Returns:
        Exit code (0 = success, 1 = note not found)
    """
    console = Console(stderr=True)

    # Load vault
    console.print(f"Loading vault from {vault_path}...", style="dim")
    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    # Find the note
    normalized = vault.normalize_name(note_name.lower())
    note = vault.get(note_name)

    if not note:
        console.print(f"Note not found: {note_name}", style="bold red")
        return 1

    # Check if it's a concept
    if not hasattr(note, "depends_on"):
        console.print(f"{note.name} is not a concept (no dependencies)", style="yellow")
        return 0

    console.print()
    console.print(f"Dependency trace for: {note.name}", style="bold cyan")
    console.print()

    # Show direct dependencies with source attribution
    if not note.depends_on:
        console.print("  No dependencies (primitive or foundational)", style="dim")
    else:
        console.print(f"  Direct dependencies ({len(note.depends_on)}):", style="bold")

        # Extract line numbers from Structural dependencies section
        dep_lines = _extract_dependency_lines(note.content)

        for dep_name in sorted(note.depends_on):
            dep_note = vault.get(dep_name)
            line_info = dep_lines.get(dep_name.lower(), "?")

            # Format: note.md:line (section) -> target.md
            source_ref = f"{note.path.name}:{line_info}"
            section = "(Structural dependencies)"

            if dep_note:
                console.print(f"    {source_ref} {section} → {dep_name}", style="green")
            else:
                console.print(f"    {source_ref} {section} → {dep_name} [missing]", style="red")

    # Show transitive closure
    console.print()
    closure = graph.transitive_closure(normalized)
    closure.discard(normalized)  # Remove self

    if closure:
        console.print(f"  Transitive closure ({len(closure)} concepts):", style="bold")
        topo = graph.topological_sort()
        for name in topo:
            if name in closure:
                console.print(f"    - {name}", style="dim")
    else:
        console.print("  No transitive dependencies", style="dim")

    return 0


def _extract_dependency_lines(content: str) -> dict[str, int]:
    """Extract line numbers where dependencies are declared.

    Returns dict mapping dependency name -> line number.
    """
    lines = content.split("\n")
    dep_lines = {}
    in_structural_deps = False

    for i, line in enumerate(lines, start=1):
        if "## Structural dependencies" in line:
            in_structural_deps = True
            continue

        if in_structural_deps:
            # Stop at next section
            if line.startswith("## "):
                break

            # Extract wiki-links
            import re
            for match in re.finditer(r'\[\[([^\]|#]+)', line):
                link_target = match.group(1).lower().strip()
                dep_lines[link_target] = i

    return dep_lines
