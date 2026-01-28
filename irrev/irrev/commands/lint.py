"""Lint command implementation."""

import json
import sys
import hashlib
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..constraints import load_core_ruleset, run_constraints_lint
from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault
from ..vault.rules import RULE_EXPLANATIONS, LintResult, LintRules, get_rule_ids


def run_lint(
    vault_path: Path,
    fail_on: str = "error",
    output_json: bool = False,
    flat: bool = False,
    invariant_filter: str | None = None,
    strict: bool = False,
    summary: bool = False,
) -> int:
    """Run lint checks on the vault.

    Args:
        vault_path: Path to vault content directory
        fail_on: Exit with error if this level or higher found ("error" or "warning")
        output_json: Output results as JSON instead of human-readable
        flat: Use flat output (legacy) instead of invariant-grouped (default)
        invariant_filter: Only run rules for this invariant (e.g., 'decomposition')
        strict: Treat unclassified rules as errors (prevents scope creep in CI)
        summary: Print only invariant status line (for commits/docs)

    Returns:
        Exit code (0 = success, 1 = failures found)
    """
    console = Console(stderr=True)

    # Load vault
    console.print(f"Loading vault from {vault_path}...", style="dim")
    vault = load_vault(vault_path)

    # Build dependency graph
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    # Determine which rules to run
    allowed_rules = None
    if invariant_filter:
        from irrev.vault.invariants import INVARIANTS

        inv = INVARIANTS.get(invariant_filter)
        if not inv:
            console.print(f"Unknown invariant: {invariant_filter}", style="bold red")
            console.print(f"Available: {', '.join(INVARIANTS.keys())}", style="dim")
            return 1

        allowed_rules = set(inv.rules)
        console.print(f"[yellow]⚠ Governance notice:[/] --invariant filter active; other invariants are not being checked.", style="dim")
        console.print(f"Running lint checks for: {inv.name} Invariant", style="dim")

    # Run lint rules
    ruleset = load_core_ruleset(vault_path)
    if ruleset is not None:
        ruleset_path = vault_path / "meta" / "rulesets" / "core.toml"
        ruleset_content_id = None
        if ruleset_path.exists():
            ruleset_content_id = hashlib.sha256(ruleset_path.read_bytes()).hexdigest()
        ruleset_meta = {
            "ruleset_id": ruleset.ruleset_id,
            "version": ruleset.version,
            "path": str(ruleset_path),
            "content_id": ruleset_content_id,
        }

        results = run_constraints_lint(
            vault_path,
            vault=vault,
            graph=graph,
            ruleset=ruleset,
            allowed_rule_ids=allowed_rules,
            invariant_filter=invariant_filter,
        )
    else:
        ruleset_meta = None
        rules = LintRules(vault, graph)
        results = rules.run_all(allowed_rules=allowed_rules)

    # Sort by level (errors first)
    level_order = {"error": 0, "warning": 1, "info": 2}
    results.sort(key=lambda r: (level_order.get(r.level, 99), str(r.file)))

    # Count by level
    counts = {"error": 0, "warning": 0, "info": 0}
    for r in results:
        counts[r.level] = counts.get(r.level, 0) + 1

    # Check for unclassified rules in strict mode
    if strict:
        from irrev.vault.invariants import STRUCTURAL_RULES

        has_unclassified = any(
            r.invariant is None and r.rule not in STRUCTURAL_RULES
            for r in results
        )

        if has_unclassified:
            console.print("\n✗ Strict mode: Unclassified rules detected. Exiting with error.", style="bold red")
            return 1

    if output_json:
        _output_json(results, counts, vault, ruleset_meta=ruleset_meta)
    elif summary:
        _print_summary_output(console, results)
    else:
        if flat:
            _print_human_output(console, results, counts, vault)
        else:
            _print_invariant_grouped_output(console, results, counts, vault)

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
        "invariant": result.invariant,  # NEW: Include invariant metadata
    }


def _output_json(results: list[LintResult], counts: dict[str, int], vault, *, ruleset_meta: dict | None = None) -> None:
    """Output lint results as JSON with invariant grouping."""
    from irrev.vault.invariants import INVARIANTS
    from collections import defaultdict

    # Existing level-based grouping
    by_level = {
        "errors": [_result_to_dict(r) for r in results if r.level == "error"],
        "warnings": [_result_to_dict(r) for r in results if r.level == "warning"],
        "info": [_result_to_dict(r) for r in results if r.level == "info"],
    }

    # NEW: Add invariant-grouped view
    by_invariant = defaultdict(lambda: {"errors": [], "warnings": [], "info": []})
    for r in results:
        if r.invariant:
            entry = _result_to_dict(r)
            # Handle plural correctly (info stays as "info", not "infos")
            level_key = f"{r.level}s" if r.level != "info" else "info"
            by_invariant[r.invariant][level_key].append(entry)

    output = {
        **by_level,
        "by_invariant": dict(by_invariant),  # NEW
        "ruleset": ruleset_meta,
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


def _print_invariant_grouped_output(
    console: Console,
    results: list[LintResult],
    counts: dict[str, int],
    vault,
) -> None:
    """Print invariant-grouped lint output (default)."""
    from irrev.vault.invariants import INVARIANTS, INVARIANT_ORDER, STRUCTURAL_RULES
    from collections import defaultdict

    # Group results by invariant
    by_invariant = defaultdict(list)
    structural_results = []
    unclassified = []

    for result in results:
        if result.invariant:
            by_invariant[result.invariant].append(result)
        elif result.rule in STRUCTURAL_RULES:
            structural_results.append(result)
        else:
            unclassified.append(result)

    # Print invariant sections in canonical order
    for inv_id in INVARIANT_ORDER:
        inv = INVARIANTS[inv_id]
        inv_results = by_invariant.get(inv_id, [])

        # Count violations by level
        errors = sum(1 for r in inv_results if r.level == "error")
        warnings = sum(1 for r in inv_results if r.level == "warning")
        infos = sum(1 for r in inv_results if r.level == "info")

        # Status indicator
        if errors > 0:
            status = "✗"
            status_style = "bold red"
        elif warnings > 0:
            status = "⚠"
            status_style = "yellow"
        else:
            status = "✓"
            status_style = "bold green"

        # Print invariant header
        console.print()
        console.print(f"{status} {inv.name} Invariant", style=status_style)

        if inv_results:
            console.print(f"  {errors} error(s), {warnings} warning(s), {infos} info(s)", style="dim")

            # Print each rule's results under this invariant
            by_rule = defaultdict(list)
            for r in inv_results:
                by_rule[r.rule].append(r)

            for rule_id, rule_results in sorted(by_rule.items()):
                console.print(f"\n  Rule: {rule_id}", style="bold")
                for r in sorted(rule_results, key=lambda x: (str(x.file), x.line or 0)):
                    if r.level == "error":
                        prefix_style = "bold red"
                        prefix = "ERROR"
                    elif r.level == "warning":
                        prefix_style = "yellow"
                        prefix = "WARN"
                    else:
                        prefix_style = "dim"
                        prefix = "INFO"

                    file_ref = r.file.name
                    if r.line:
                        file_ref += f":{r.line}"

                    console.print(f"    {prefix}: {file_ref} - {r.message}", style=prefix_style)
        else:
            console.print(f"  ✓ All rules passing", style="dim green")

    # Print structural integrity section (separate from invariants)
    if structural_results:
        errors = sum(1 for r in structural_results if r.level == "error")
        warnings = sum(1 for r in structural_results if r.level == "warning")
        infos = sum(1 for r in structural_results if r.level == "info")

        if errors > 0:
            status = "✗"
            status_style = "bold red"
        elif warnings > 0:
            status = "⚠"
            status_style = "yellow"
        else:
            status = "✓"
            status_style = "bold green"

        console.print()
        console.print(f"{status} Structural Integrity (supports all invariants)", style=status_style)
        console.print(f"  {errors} error(s), {warnings} warning(s), {infos} info(s)", style="dim")
        console.print(f"  (Graph coherence - emerges when invariants are jointly respected)", style="dim italic")

        by_rule = defaultdict(list)
        for r in structural_results:
            by_rule[r.rule].append(r)

        for rule_id, rule_results in sorted(by_rule.items()):
            console.print(f"\n  Rule: {rule_id}", style="bold")
            for r in sorted(rule_results, key=lambda x: (str(x.file), x.line or 0)):
                if r.level == "error":
                    prefix_style = "bold red"
                    prefix = "ERROR"
                elif r.level == "warning":
                    prefix_style = "yellow"
                    prefix = "WARN"
                else:
                    prefix_style = "dim"
                    prefix = "INFO"

                file_ref = r.file.name
                if r.line:
                    file_ref += f":{r.line}"

                console.print(f"    {prefix}: {file_ref} - {r.message}", style=prefix_style)

    # Print unclassified violations (ANTI-CREEP LOCK)
    if unclassified:
        console.print()
        console.print("⚠ Unclassified Violations (SCOPE CREEP DETECTED)", style="bold yellow")
        console.print("  These rules are not mapped to any invariant or structural category:", style="yellow")

        unclassified_rules = {r.rule for r in unclassified}
        console.print(f"  Unmapped rules: {', '.join(sorted(unclassified_rules))}", style="yellow")

        console.print("\n  Action required:", style="bold yellow")
        console.print("  1. Add to an existing invariant in INVARIANTS (if it enforces that invariant)", style="yellow")
        console.print("  2. Add to STRUCTURAL_RULES (if it's a graph integrity check)", style="yellow")
        console.print("  3. Remove the rule (if it doesn't belong)", style="yellow")
        console.print("  See: irrev/vault/invariants.py\n", style="yellow")

        for r in unclassified:
            if r.level == "error":
                prefix_style = "bold red"
                prefix = "ERROR"
            elif r.level == "warning":
                prefix_style = "yellow"
                prefix = "WARN"
            else:
                prefix_style = "dim"
                prefix = "INFO"

            file_ref = r.file.name
            if r.line:
                file_ref += f":{r.line}"

            console.print(f"  {prefix}: [{r.rule}] {file_ref} - {r.message}", style=prefix_style)

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


def _print_summary_output(console: Console, results: list[LintResult]) -> None:
    """Print compact invariant status line (for commits/docs)."""
    from irrev.vault.invariants import INVARIANTS, INVARIANT_ORDER, STRUCTURAL_RULES
    from collections import defaultdict

    # Group results
    by_invariant = defaultdict(list)
    structural_results = []

    for result in results:
        if result.invariant:
            by_invariant[result.invariant].append(result)
        elif result.rule in STRUCTURAL_RULES:
            structural_results.append(result)

    def get_status(results_list):
        errors = sum(1 for r in results_list if r.level == "error")
        warnings = sum(1 for r in results_list if r.level == "warning")
        infos = sum(1 for r in results_list if r.level == "info")

        if errors > 0:
            return f"✗ ({errors}e)", "bold red"
        elif warnings > 0:
            return f"⚠ ({warnings}w)", "yellow"
        elif infos > 0:
            return f"✓ ({infos}i)", "dim green"
        else:
            return "✓", "bold green"

    # Print each invariant on one line
    for inv_id in INVARIANT_ORDER:
        inv = INVARIANTS[inv_id]
        inv_results = by_invariant.get(inv_id, [])
        status, style = get_status(inv_results)
        console.print(f"{inv.name}: {status}", style=style, end="  ")

    # Structural integrity
    status, style = get_status(structural_results)
    console.print(f"Structural: {status}", style=style)


def _print_human_output(
    console: Console,
    results: list[LintResult],
    counts: dict[str, int],
    vault,
) -> None:
    """Print human-readable lint output (flat/legacy format)."""
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


def run_explain_invariant(invariant_id: str) -> int:
    """Explain a specific invariant and its enforcement rules.

    Args:
        invariant_id: Invariant ID to explain (e.g., 'decomposition', 'governance')

    Returns:
        Exit code (0 = success, 1 = invariant not found)
    """
    from rich.markdown import Markdown
    from irrev.vault.invariants import INVARIANTS

    console = Console()

    # Normalize invariant_id
    invariant_id = invariant_id.lower().strip()

    inv = INVARIANTS.get(invariant_id)
    if not inv:
        console.print(f"Unknown invariant: {invariant_id}", style="bold red")
        console.print()
        console.print("Available invariants:", style="bold")
        for iid in INVARIANTS.keys():
            console.print(f"  - {iid}")
        return 1

    # Build markdown explanation
    explanation = f"""# {inv.name} Invariant

**Statement**: {inv.statement}

**Failure Mode**: {inv.failure_mode}

## Enforcement Rules

"""

    for rule_id in inv.rules:
        explanation += f"- `{rule_id}`"
        if rule_id in RULE_EXPLANATIONS:
            # Show brief rule summary (first line of explanation)
            rule_explanation = RULE_EXPLANATIONS[rule_id].strip()
            first_line = rule_explanation.split("\n")[0].strip()
            explanation += f"\n  {first_line}\n\n"
        else:
            explanation += "\n\n"

    explanation += "\nUse `irrev lint --explain RULE_ID` for detailed rule documentation."

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
