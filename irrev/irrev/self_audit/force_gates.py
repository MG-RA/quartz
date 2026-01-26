"""
Force gate detection for destructive operations.

This module identifies destructive operations that should require --force
but may not be gated properly, violating the Governance invariant.

Detects patterns such as:
- Functions with "wipe", "rebuild", "delete" in name without force parameter
- CLI commands with destructive modes that don't check force flag
- Operations that modify/erase state without confirmation

Output is observational: a list of (location, operation, gate_status) tuples.
No corrections or recommendations are produced.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ForceGateMatch:
    """A detected force gate pattern or missing gate."""

    file: str
    line: int
    function_name: str
    gate_type: str  # "missing_force_param", "ungated_destructive", "properly_gated"
    description: str


# Keywords that indicate destructive operations
DESTRUCTIVE_KEYWORDS = {
    "wipe",
    "rebuild",
    "delete",
    "remove",
    "clear",
    "truncate",
    "drop",
    "erase",
    "destroy",
    "reset",
    "purge",
}

# Keywords that indicate a force gate is present
FORCE_GATE_KEYWORDS = {
    "force",
    "confirm",
    "yes",
    "acknowledge",
    "accept",
}


class ForceGateAnalyzer(ast.NodeVisitor):
    """AST visitor that detects force gate patterns in functions."""

    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.findings: list[ForceGateMatch] = []
        self.current_file = ""

    def set_file(self, filepath: str) -> None:
        self.current_file = filepath

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        func_name = node.name.lower()

        # Check if function name suggests destructive operation
        is_destructive = any(kw in func_name for kw in DESTRUCTIVE_KEYWORDS)

        if not is_destructive:
            # Check docstring for destructive language
            if node.body and isinstance(node.body[0], ast.Expr):
                if isinstance(node.body[0].value, ast.Constant):
                    docstring = str(node.body[0].value.value).lower()
                    is_destructive = any(kw in docstring for kw in DESTRUCTIVE_KEYWORDS)

        if not is_destructive:
            return

        # Check if function has force-related parameter
        param_names = {arg.arg.lower() for arg in node.args.args + node.args.kwonlyargs}
        has_force_param = any(kw in name for name in param_names for kw in FORCE_GATE_KEYWORDS)

        # Check if function body checks force flag
        body_source = "\n".join(
            self.source_lines[node.lineno - 1 : node.end_lineno] if node.end_lineno else []
        ).lower()
        checks_force = any(
            f"if {kw}" in body_source or f"if not {kw}" in body_source
            for kw in FORCE_GATE_KEYWORDS
        )

        if has_force_param and checks_force:
            self.findings.append(
                ForceGateMatch(
                    file=self.current_file,
                    line=node.lineno,
                    function_name=node.name,
                    gate_type="properly_gated",
                    description=f"Destructive function with force gate",
                )
            )
        elif has_force_param:
            self.findings.append(
                ForceGateMatch(
                    file=self.current_file,
                    line=node.lineno,
                    function_name=node.name,
                    gate_type="unchecked_force",
                    description=f"Has force parameter but no visible check in body",
                )
            )
        else:
            self.findings.append(
                ForceGateMatch(
                    file=self.current_file,
                    line=node.lineno,
                    function_name=node.name,
                    gate_type="missing_force_param",
                    description=f"Destructive function without force parameter",
                )
            )


def scan_file(filepath: Path) -> list[ForceGateMatch]:
    """Scan a single Python file for force gate patterns."""
    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    analyzer = ForceGateAnalyzer(source.split("\n"))
    analyzer.set_file(str(filepath))
    analyzer.visit(tree)

    return analyzer.findings


def scan_force_gates(root: Path) -> list[ForceGateMatch]:
    """Scan all Python files under root for force gate patterns.

    Returns a list of ForceGateMatch observations.
    """
    matches = []

    for py_file in root.rglob("*.py"):
        # Skip test files and __pycache__
        if "__pycache__" in str(py_file) or "test" in py_file.stem.lower():
            continue
        matches.extend(scan_file(py_file))

    return matches


def format_findings(matches: list[ForceGateMatch]) -> str:
    """Format findings as a diagnostic report (observations only)."""
    if not matches:
        return "No force gate patterns detected."

    lines = ["## Force Gate Analysis", ""]

    # Group by gate type
    by_type: dict[str, list[ForceGateMatch]] = {}
    for m in matches:
        by_type.setdefault(m.gate_type, []).append(m)

    type_labels = {
        "properly_gated": "Properly Gated (force parameter + check)",
        "unchecked_force": "Has Force Parameter (no visible check)",
        "missing_force_param": "Missing Force Parameter",
    }

    for gate_type in ["missing_force_param", "unchecked_force", "properly_gated"]:
        if gate_type not in by_type:
            continue
        type_matches = by_type[gate_type]
        label = type_labels.get(gate_type, gate_type)
        lines.append(f"### {label}")
        lines.append("")
        for m in sorted(type_matches, key=lambda x: (x.file, x.line)):
            lines.append(f"- {m.file}:{m.line} `{m.function_name}`")
            lines.append(f"  - {m.description}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    findings = scan_force_gates(target)
    print(format_findings(findings))
