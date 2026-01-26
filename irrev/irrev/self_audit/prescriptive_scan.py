"""
Prescriptive language detection for tool artifacts.

This module applies the same prescriptive language detection patterns from
junctions.py to the tool's own source code: CLI help strings, error messages,
docstrings, and comments.

Detects patterns such as:
- "Fix: do X" in error messages
- "should", "must", "recommend" with agentive subjects
- Prescriptive framing in help text

Output is observational: a list of (file, line, matched_text) tuples.
No corrections or recommendations are produced.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


# Same patterns from junctions.py, applied to tool artifacts
PRESCRIPTIVE_SUBJECT_PATTERN = re.compile(
    r"\b(we|one|users?|systems?|agents?|operators?|you)\s+(should|must|require)", re.I
)

# "Fix:" pattern common in lint rule explanations
FIX_PATTERN = re.compile(r"\bFix:\s*", re.I)

# Recommendation language
RECOMMEND_PATTERN = re.compile(
    r"\b(recommend|suggestion|advised|consider|try to|make sure)\b", re.I
)

# Bare prescriptive modals without clear descriptive framing
BARE_PRESCRIPTIVE = re.compile(r"\b(should|must|need to|have to)\b", re.I)


@dataclass(frozen=True)
class PrescriptiveMatch:
    """A detected prescriptive language pattern in tool source."""

    file: str
    line: int
    pattern_type: str  # "prescriptive_subject", "fix_directive", "recommendation", "bare_modal"
    matched_text: str
    context: str  # surrounding text for reference


def _extract_strings_from_ast(source: str, filepath: str) -> Iterator[tuple[int, str, str]]:
    """Extract string literals from Python source with line numbers and context.

    Yields (line_number, string_content, context_type) tuples.
    context_type is one of: "docstring", "help", "error_message", "other"
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        # Docstrings (first statement in module/class/function if it's a string)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                expr = node.body[0]
                if isinstance(expr.value, ast.Constant) and isinstance(expr.value.value, str):
                    yield (expr.lineno, expr.value.value, "docstring")

        # String constants in general
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
            # Heuristic: CLI help strings often contain "help="
            # Error messages often contain "Error" or are in console.print
            context = "other"
            if len(text) > 20:  # Skip short strings
                yield (node.lineno, text, context)

        # f-strings
        if isinstance(node, ast.JoinedStr):
            # Reconstruct f-string parts that are constant
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
            if parts:
                yield (node.lineno, " ".join(parts), "fstring")

        # Call arguments (often help= in Click decorators)
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "help" and isinstance(keyword.value, ast.Constant):
                    if isinstance(keyword.value.value, str):
                        yield (keyword.value.lineno, keyword.value.value, "help")


def _scan_string(
    text: str, line: int, filepath: str, context_type: str
) -> list[PrescriptiveMatch]:
    """Scan a string for prescriptive patterns."""
    matches = []

    # Prescriptive subject pattern
    for m in PRESCRIPTIVE_SUBJECT_PATTERN.finditer(text):
        matches.append(
            PrescriptiveMatch(
                file=filepath,
                line=line,
                pattern_type="prescriptive_subject",
                matched_text=m.group(0),
                context=context_type,
            )
        )

    # Fix: directive
    for m in FIX_PATTERN.finditer(text):
        # Extract the sentence containing "Fix:"
        start = max(0, m.start() - 20)
        end = min(len(text), m.end() + 80)
        snippet = text[start:end].replace("\n", " ").strip()
        matches.append(
            PrescriptiveMatch(
                file=filepath,
                line=line,
                pattern_type="fix_directive",
                matched_text=snippet,
                context=context_type,
            )
        )

    # Recommendation language
    for m in RECOMMEND_PATTERN.finditer(text):
        matches.append(
            PrescriptiveMatch(
                file=filepath,
                line=line,
                pattern_type="recommendation",
                matched_text=m.group(0),
                context=context_type,
            )
        )

    return matches


def scan_file(filepath: Path) -> list[PrescriptiveMatch]:
    """Scan a single Python file for prescriptive language patterns."""
    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    matches = []
    rel_path = str(filepath)

    for line_no, text, context_type in _extract_strings_from_ast(source, rel_path):
        matches.extend(_scan_string(text, line_no, rel_path, context_type))

    return matches


def scan_prescriptive_language(root: Path) -> list[PrescriptiveMatch]:
    """Scan all Python files under root for prescriptive language patterns.

    Returns a list of PrescriptiveMatch observations.
    """
    matches = []

    for py_file in root.rglob("*.py"):
        # Skip test files and __pycache__
        if "__pycache__" in str(py_file) or "test" in py_file.stem.lower():
            continue
        matches.extend(scan_file(py_file))

    return matches


def format_findings(matches: list[PrescriptiveMatch]) -> str:
    """Format findings as a diagnostic report (observations only)."""
    if not matches:
        return "No prescriptive language patterns detected."

    lines = ["## Prescriptive Language Detected", ""]

    # Group by file
    by_file: dict[str, list[PrescriptiveMatch]] = {}
    for m in matches:
        by_file.setdefault(m.file, []).append(m)

    for filepath, file_matches in sorted(by_file.items()):
        lines.append(f"### {filepath}")
        for m in sorted(file_matches, key=lambda x: x.line):
            lines.append(f"- Line {m.line} [{m.pattern_type}]: `{m.matched_text}`")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    findings = scan_prescriptive_language(target)
    print(format_findings(findings))
