"""
Role separation detection for tool functions.

This module identifies functions that mix diagnostic (read) and action (write)
operations, violating the Decomposition invariant: "Objects and operators must
be separated by role."

Detects patterns such as:
- Functions that both load_vault() and write to Neo4j/filesystem
- Functions that both analyze and modify state in a single call

Output is observational: a list of (function_name, read_ops, write_ops) tuples.
No corrections or recommendations are produced.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# Read operations (diagnostic)
READ_PATTERNS = {
    "load_vault",
    "load_concept",
    "load_diagnostic",
    "read_text",
    "read_bytes",
    "open.*r",
    "get",
    "fetch",
    "query",
    "select",
    "find",
    "search",
    "glob",
    "rglob",
    "iterdir",
    "exists",
    "is_file",
    "is_dir",
    "stat",
}

# Write operations (action)
WRITE_PATTERNS = {
    "write_text",
    "write_bytes",
    "open.*w",
    "commit",
    "execute",
    "run",
    "create",
    "delete",
    "remove",
    "unlink",
    "mkdir",
    "rmdir",
    "rename",
    "replace",
    "truncate",
    "wipe",
    "clear",
    "insert",
    "update",
    "upsert",
    "merge",
    "set",
}


@dataclass(frozen=True)
class RoleMixingMatch:
    """A detected role mixing pattern in a function."""

    file: str
    function_name: str
    line: int
    read_ops: tuple[str, ...]
    write_ops: tuple[str, ...]


class FunctionAnalyzer(ast.NodeVisitor):
    """AST visitor that detects read and write operations in a function."""

    def __init__(self):
        self.read_ops: list[str] = []
        self.write_ops: list[str] = []

    def visit_Call(self, node: ast.Call):
        # Get the function name being called
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr

        if name:
            name_lower = name.lower()
            for pattern in READ_PATTERNS:
                if re.search(pattern, name_lower):
                    self.read_ops.append(name)
                    break
            for pattern in WRITE_PATTERNS:
                if re.search(pattern, name_lower):
                    self.write_ops.append(name)
                    break

        self.generic_visit(node)


def _analyze_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef, filepath: str
) -> RoleMixingMatch | None:
    """Analyze a function for role mixing."""
    analyzer = FunctionAnalyzer()
    analyzer.visit(node)

    # Only report if both read and write operations are present
    if analyzer.read_ops and analyzer.write_ops:
        return RoleMixingMatch(
            file=filepath,
            function_name=node.name,
            line=node.lineno,
            read_ops=tuple(sorted(set(analyzer.read_ops))),
            write_ops=tuple(sorted(set(analyzer.write_ops))),
        )
    return None


def scan_file(filepath: Path) -> list[RoleMixingMatch]:
    """Scan a single Python file for role mixing patterns."""
    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    matches = []
    rel_path = str(filepath)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            match = _analyze_function(node, rel_path)
            if match:
                matches.append(match)

    return matches


def scan_role_separation(root: Path) -> list[RoleMixingMatch]:
    """Scan all Python files under root for role mixing patterns.

    Returns a list of RoleMixingMatch observations.
    """
    matches = []

    for py_file in root.rglob("*.py"):
        # Skip test files and __pycache__
        if "__pycache__" in str(py_file) or "test" in py_file.stem.lower():
            continue
        matches.extend(scan_file(py_file))

    return matches


def format_findings(matches: list[RoleMixingMatch]) -> str:
    """Format findings as a diagnostic report (observations only)."""
    if not matches:
        return "No role separation violations detected."

    lines = ["## Role Separation Violations", ""]
    lines.append("Functions that mix read (diagnostic) and write (action) operations:")
    lines.append("")

    for m in sorted(matches, key=lambda x: (x.file, x.line)):
        lines.append(f"### {m.file}:{m.line} - `{m.function_name}`")
        lines.append(f"- Read operations: {', '.join(m.read_ops)}")
        lines.append(f"- Write operations: {', '.join(m.write_ops)}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    findings = scan_role_separation(target)
    print(format_findings(findings))
