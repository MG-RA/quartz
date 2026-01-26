"""
Audit logging coverage detection.

This module identifies state-changing operations that should call log_operation
but may not, violating the Irreversibility invariant: "Erasure costs must be
declared; accounting is mandatory."

Detects patterns such as:
- Functions with write operations that don't call log_operation
- execute_* functions without audit logging
- File writes without corresponding log entries

Output is observational: a list of (location, operation, has_logging) tuples.
No corrections or recommendations are produced.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuditCoverageMatch:
    """A detected audit coverage pattern or gap."""

    file: str
    line: int
    function_name: str
    coverage_type: str  # "has_logging", "missing_logging", "indirect_logging"
    write_operations: tuple[str, ...]
    description: str


# Operations that should trigger audit logging
AUDITABLE_WRITE_OPS = {
    "write_text",
    "write_bytes",
    "commit",
    "execute",
    "wipe",
    "upsert",
    "merge",
    "delete",
    "remove",
    "unlink",
    "truncate",
    "create",
}

# Audit logging function names
AUDIT_FUNCTIONS = {
    "log_operation",
    "log_event",
    "log_to_audit",
    "audit_log",
}


class AuditCoverageAnalyzer(ast.NodeVisitor):
    """AST visitor that detects audit logging coverage in functions."""

    def __init__(self):
        self.findings: list[AuditCoverageMatch] = []
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
        # Collect all function calls in this function
        write_ops = []
        has_audit_call = False

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = None
                if isinstance(child.func, ast.Name):
                    func_name = child.func.id
                elif isinstance(child.func, ast.Attribute):
                    func_name = child.func.attr

                if func_name:
                    func_lower = func_name.lower()
                    # Check for write operations
                    for op in AUDITABLE_WRITE_OPS:
                        if op in func_lower:
                            write_ops.append(func_name)
                            break
                    # Check for audit calls
                    for audit_fn in AUDIT_FUNCTIONS:
                        if audit_fn in func_lower:
                            has_audit_call = True
                            break

        # Only report functions that have write operations
        if not write_ops:
            return

        # Filter out test functions and private helpers
        if node.name.startswith("_") and not node.name.startswith("__"):
            return
        if "test" in node.name.lower():
            return

        # Determine coverage type
        func_name_lower = node.name.lower()
        is_execute_function = func_name_lower.startswith("execute") or func_name_lower.startswith(
            "run_"
        )

        if has_audit_call:
            coverage_type = "has_logging"
            description = "Write operations with audit logging"
        elif is_execute_function:
            coverage_type = "missing_logging"
            description = "Execute function without visible audit logging"
        else:
            coverage_type = "indirect_logging"
            description = "Write operations (may be logged at call site)"

        self.findings.append(
            AuditCoverageMatch(
                file=self.current_file,
                line=node.lineno,
                function_name=node.name,
                coverage_type=coverage_type,
                write_operations=tuple(sorted(set(write_ops))),
                description=description,
            )
        )


def scan_file(filepath: Path) -> list[AuditCoverageMatch]:
    """Scan a single Python file for audit coverage patterns."""
    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    analyzer = AuditCoverageAnalyzer()
    analyzer.set_file(str(filepath))
    analyzer.visit(tree)

    return analyzer.findings


def scan_audit_coverage(root: Path) -> list[AuditCoverageMatch]:
    """Scan all Python files under root for audit coverage patterns.

    Returns a list of AuditCoverageMatch observations.
    """
    matches = []

    for py_file in root.rglob("*.py"):
        # Skip test files and __pycache__
        if "__pycache__" in str(py_file) or "test" in py_file.stem.lower():
            continue
        matches.extend(scan_file(py_file))

    return matches


def format_findings(matches: list[AuditCoverageMatch]) -> str:
    """Format findings as a diagnostic report (observations only)."""
    if not matches:
        return "No audit coverage patterns detected."

    lines = ["## Audit Logging Coverage", ""]

    # Group by coverage type
    by_type: dict[str, list[AuditCoverageMatch]] = {}
    for m in matches:
        by_type.setdefault(m.coverage_type, []).append(m)

    type_labels = {
        "has_logging": "Functions with Audit Logging",
        "missing_logging": "Execute Functions Missing Audit Logging",
        "indirect_logging": "Functions with Write Ops (may be logged at call site)",
    }

    # Show missing first, then indirect, then has_logging
    for coverage_type in ["missing_logging", "indirect_logging", "has_logging"]:
        if coverage_type not in by_type:
            continue
        type_matches = by_type[coverage_type]
        label = type_labels.get(coverage_type, coverage_type)
        lines.append(f"### {label}")
        lines.append("")
        for m in sorted(type_matches, key=lambda x: (x.file, x.line)):
            lines.append(f"- {m.file}:{m.line} `{m.function_name}`")
            lines.append(f"  - Write ops: {', '.join(m.write_operations)}")
            lines.append(f"  - {m.description}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    findings = scan_audit_coverage(target)
    print(format_findings(findings))
