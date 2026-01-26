"""
Convert irrev lint results to LSP diagnostics.

Provides single-file linting for real-time feedback without loading
the entire vault on every keystroke.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter


@dataclass
class LintDiagnostic:
    """A single lint diagnostic for LSP."""

    line: int
    column: int
    length: int
    message: str
    severity: str  # "error", "warning", "info"
    rule_id: str
    invariant: str | None = None


# Wikilink pattern
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def lint_file(
    file_path: Path,
    vault_path: Path,
    content: str | None = None,
) -> list[LintDiagnostic]:
    """
    Run lint checks on a single file.

    This is a lightweight version of the full vault lint that can run
    on individual files for real-time feedback.

    Args:
        file_path: Path to the file to lint
        vault_path: Path to vault content directory
        content: File content (if None, reads from disk)

    Returns:
        List of diagnostics for this file
    """
    if content is None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []

    diagnostics: list[LintDiagnostic] = []

    # Parse frontmatter
    try:
        post = frontmatter.loads(content)
        meta = post.metadata
        body = post.content
    except Exception:
        meta = {}
        body = content

    role = meta.get("role", "").lower()
    layer = meta.get("layer", "").lower()

    # Get line offset for body (after frontmatter)
    frontmatter_lines = 0
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_lines = parts[1].count("\n") + 2  # +2 for the --- lines

    lines = body.split("\n")

    # Check for concepts
    if role == "concept":
        diagnostics.extend(_lint_concept(lines, meta, frontmatter_lines, file_path))

    # Check wikilinks for all files
    diagnostics.extend(_lint_wikilinks(lines, vault_path, frontmatter_lines))

    return diagnostics


def _lint_concept(
    lines: list[str],
    meta: dict[str, Any],
    line_offset: int,
    file_path: Path,
) -> list[LintDiagnostic]:
    """Lint concept-specific rules."""
    diagnostics = []

    # Check for required sections
    has_definition = False
    has_dependencies = False
    has_what_not = False

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if line_lower.startswith("## definition"):
            has_definition = True
        elif line_lower.startswith("## structural dependencies"):
            has_dependencies = True
        elif line_lower.startswith("## what this is not"):
            has_what_not = True

    if not has_dependencies:
        diagnostics.append(
            LintDiagnostic(
                line=0,
                column=0,
                length=len(file_path.stem),
                message="Concept lacks '## Structural dependencies' section",
                severity="error",
                rule_id="missing-dependencies",
                invariant="irreversibility",
            )
        )

    if not has_definition:
        diagnostics.append(
            LintDiagnostic(
                line=0,
                column=0,
                length=len(file_path.stem),
                message="Concept lacks '## Definition' section",
                severity="warning",
                rule_id="missing-section",
                invariant="decomposition",
            )
        )

    if not has_what_not:
        diagnostics.append(
            LintDiagnostic(
                line=0,
                column=0,
                length=len(file_path.stem),
                message="Concept lacks '## What this is NOT' section",
                severity="info",
                rule_id="missing-section",
                invariant="decomposition",
            )
        )

    return diagnostics


def _lint_wikilinks(
    lines: list[str],
    vault_path: Path,
    line_offset: int,
) -> list[LintDiagnostic]:
    """Check wikilinks for broken links."""
    diagnostics = []

    # Build a set of valid targets (note names without extension)
    valid_targets = set()
    for md_file in vault_path.rglob("*.md"):
        # Add the file stem as a valid target
        valid_targets.add(md_file.stem.lower())
        # Also add with parent folder for disambiguation
        rel = md_file.relative_to(vault_path)
        valid_targets.add(rel.with_suffix("").as_posix().lower())

    for i, line in enumerate(lines):
        for match in WIKILINK_PATTERN.finditer(line):
            target = match.group(1).strip().lower()
            # Normalize: remove any path components for simple lookup
            target_simple = target.split("/")[-1] if "/" in target else target

            if target_simple not in valid_targets and target not in valid_targets:
                diagnostics.append(
                    LintDiagnostic(
                        line=line_offset + i,
                        column=match.start(),
                        length=match.end() - match.start(),
                        message=f"Broken link: [[{match.group(1)}]] not found in vault",
                        severity="warning",
                        rule_id="broken-link",
                        invariant=None,  # Structural rule
                    )
                )

    return diagnostics


def full_vault_lint(vault_path: Path) -> list[tuple[Path, list[LintDiagnostic]]]:
    """
    Run full vault lint and return per-file diagnostics.

    This is used for initial workspace scan.
    """
    from ..vault.graph import DependencyGraph
    from ..vault.loader import load_vault
    from ..vault.rules import LintRules

    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)
    rules = LintRules(vault, graph)
    results = rules.run_all()

    # Group by file
    by_file: dict[Path, list[LintDiagnostic]] = {}

    for r in results:
        path = r.file
        diag = LintDiagnostic(
            line=0,  # Full vault lint doesn't track line numbers
            column=0,
            length=0,
            message=r.message,
            severity=r.level,
            rule_id=r.rule,
            invariant=r.invariant,
        )
        by_file.setdefault(path, []).append(diag)

    return list(by_file.items())
