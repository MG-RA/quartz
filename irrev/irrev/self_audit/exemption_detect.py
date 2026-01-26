"""
Self-exemption pattern detection for tool code.

This module identifies places where the tool allows bypassing constraints
it enforces on content, violating the Governance invariant: "No actor is
exempt from structural constraints."

Detects patterns such as:
- allowed_rules parameters that filter enforcement
- --mode options that bypass safety constraints
- Conditional logic that skips checks
- Destructive operations without cost declaration

Output is observational: a list of (location, exemption_type, description) tuples.
No corrections or recommendations are produced.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExemptionMatch:
    """A detected self-exemption pattern in tool code."""

    file: str
    line: int
    exemption_type: str  # "rule_filter", "mode_bypass", "skip_check", "destructive_unaccounted"
    description: str
    code_snippet: str


# Patterns indicating rule filtering
RULE_FILTER_PATTERNS = [
    r"allowed_rules",
    r"skip_rules",
    r"exclude_rules",
    r"disabled_rules",
    r"--invariant",  # CLI flag for invariant filtering
    r"--exclude",
    r"--skip",
]

# Patterns indicating destructive operations
DESTRUCTIVE_PATTERNS = [
    r"wipe",
    r"delete\s+all",
    r"clear\s+all",
    r"truncate",
    r"drop\s+all",
    r"remove\s+all",
    r"rebuild",
    r"--force",
    r"in_place",
]

# Patterns indicating conditional check skipping
SKIP_CHECK_PATTERNS = [
    r"if\s+not\s+\w+:\s*return",
    r"if\s+\w+\s*is\s+None:\s*return",
    r"if\s+skip",
    r"if\s+disable",
    r"if\s+ignore",
]


def _extract_code_context(source: str, line_no: int, context_lines: int = 2) -> str:
    """Extract code context around a line number."""
    lines = source.split("\n")
    start = max(0, line_no - context_lines - 1)
    end = min(len(lines), line_no + context_lines)
    return "\n".join(lines[start:end])


def scan_file(filepath: Path) -> list[ExemptionMatch]:
    """Scan a single Python file for self-exemption patterns."""
    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    matches = []
    rel_path = str(filepath)
    lines = source.split("\n")

    for line_no, line in enumerate(lines, start=1):
        # Check for rule filtering patterns
        for pattern in RULE_FILTER_PATTERNS:
            if re.search(pattern, line, re.I):
                matches.append(
                    ExemptionMatch(
                        file=rel_path,
                        line=line_no,
                        exemption_type="rule_filter",
                        description=f"Rule filtering mechanism: {pattern}",
                        code_snippet=line.strip(),
                    )
                )
                break  # Only one match per line

        # Check for destructive operation patterns
        for pattern in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, line, re.I):
                # Check if there's cost accounting nearby (within 5 lines)
                context_start = max(0, line_no - 6)
                context_end = min(len(lines), line_no + 5)
                context = "\n".join(lines[context_start:context_end]).lower()

                # Look for cost accounting language
                has_accounting = any(
                    term in context
                    for term in ["cost", "warning", "confirm", "backup", "undo", "rollback"]
                )

                if not has_accounting:
                    matches.append(
                        ExemptionMatch(
                            file=rel_path,
                            line=line_no,
                            exemption_type="destructive_unaccounted",
                            description=f"Destructive operation without visible cost accounting: {pattern}",
                            code_snippet=line.strip(),
                        )
                    )
                break

    # AST-based detection for more complex patterns
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return matches

    for node in ast.walk(tree):
        # Detect optional parameters that allow skipping enforcement
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.defaults + node.args.kw_defaults:
                if arg is None:
                    continue
                # Check for default None or False for rule-related parameters
                if isinstance(arg, ast.Constant) and arg.value in (None, False):
                    # Check parameter names
                    for param in node.args.args + node.args.kwonlyargs:
                        if any(
                            skip_word in param.arg.lower()
                            for skip_word in ["skip", "disable", "ignore", "allow", "exclude"]
                        ):
                            matches.append(
                                ExemptionMatch(
                                    file=rel_path,
                                    line=node.lineno,
                                    exemption_type="skip_parameter",
                                    description=f"Function {node.name} has skip/disable parameter: {param.arg}",
                                    code_snippet=f"def {node.name}(..., {param.arg}=...)",
                                )
                            )

    return matches


def scan_exemptions(root: Path) -> list[ExemptionMatch]:
    """Scan all Python files under root for self-exemption patterns.

    Returns a list of ExemptionMatch observations.
    """
    matches = []

    for py_file in root.rglob("*.py"):
        # Skip test files and __pycache__
        if "__pycache__" in str(py_file) or "test" in py_file.stem.lower():
            continue
        matches.extend(scan_file(py_file))

    return matches


def format_findings(matches: list[ExemptionMatch]) -> str:
    """Format findings as a diagnostic report (observations only)."""
    if not matches:
        return "No self-exemption patterns detected."

    lines = ["## Self-Exemption Patterns Detected", ""]

    # Group by type
    by_type: dict[str, list[ExemptionMatch]] = {}
    for m in matches:
        by_type.setdefault(m.exemption_type, []).append(m)

    type_labels = {
        "rule_filter": "Rule Filtering Mechanisms",
        "destructive_unaccounted": "Destructive Operations Without Cost Accounting",
        "skip_parameter": "Skip/Disable Parameters",
        "mode_bypass": "Mode-Based Constraint Bypass",
    }

    for exemption_type, type_matches in sorted(by_type.items()):
        label = type_labels.get(exemption_type, exemption_type)
        lines.append(f"### {label}")
        lines.append("")
        for m in sorted(type_matches, key=lambda x: (x.file, x.line)):
            lines.append(f"- {m.file}:{m.line}")
            lines.append(f"  - {m.description}")
            lines.append(f"  - `{m.code_snippet}`")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    findings = scan_exemptions(target)
    print(format_findings(findings))
