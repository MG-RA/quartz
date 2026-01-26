"""
Hover information providers for LSP.

Provides rich information when hovering over wikilinks:
- Concept layer and role
- Structural dependencies
- Invariant participation
- Last audit events (if available)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .server import IrrevLanguageServer


def get_hover_info(server: "IrrevLanguageServer", target: str) -> str | None:
    """
    Get hover information for a wikilink target.

    Args:
        server: The language server instance
        target: The wikilink target (concept name or alias)

    Returns:
        Markdown-formatted hover content, or None if not found
    """
    concept = server.get_concept_info(target)
    if not concept:
        return None

    lines = []

    # Header
    lines.append(f"## {concept['name']}")
    lines.append("")

    # Layer and role badges
    layer = concept.get("layer", "unknown")
    role = concept.get("role", "concept")
    lines.append(f"**Layer:** `{layer}` | **Role:** `{role}`")
    lines.append("")

    # Dependencies
    deps = concept.get("depends_on", [])
    if deps:
        lines.append("**Structural dependencies:**")
        for dep in deps[:5]:  # Limit to first 5
            lines.append(f"- `{dep}`")
        if len(deps) > 5:
            lines.append(f"- ... and {len(deps) - 5} more")
    else:
        lines.append("**Structural dependencies:** None (primitive)")
    lines.append("")

    # Invariant participation
    invariants = _get_invariant_participation(layer, role)
    if invariants:
        lines.append("**Invariant checks:**")
        for inv in invariants:
            lines.append(f"- {inv}")
        lines.append("")

    # File path
    if concept.get("path"):
        rel_path = concept["path"]
        lines.append(f"*{rel_path}*")

    return "\n".join(lines)


def _get_invariant_participation(layer: str, role: str) -> list[str]:
    """Determine which invariants apply to this concept."""
    invariants = []

    # All concepts participate in basic checks
    invariants.append("Decomposition: role boundaries")

    if role == "concept":
        invariants.append("Irreversibility: dependency tracking")

        # Layer-specific checks
        if layer in ("primitive", "foundational"):
            invariants.append("Attribution: no higher-layer dependencies")
        elif layer in ("mechanism", "accounting"):
            invariants.append("Governance: declared cost surfaces")

    if role == "diagnostic":
        invariants.append("Attribution: no prescription")

    return invariants


def get_file_hover_info(file_path: Path, vault_path: Path) -> str | None:
    """
    Get hover information for a file (not a concept).

    Useful for showing role/layer even for non-concept files.
    """
    import frontmatter

    try:
        content = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(content)
        meta = post.metadata
    except Exception:
        return None

    role = meta.get("role", "unknown")
    layer = meta.get("layer")
    canonical = meta.get("canonical", False)

    lines = []
    lines.append(f"## {file_path.stem}")
    lines.append("")
    lines.append(f"**Role:** `{role}`")
    if layer:
        lines.append(f"**Layer:** `{layer}`")
    if canonical:
        lines.append("**Canonical:** yes")
    lines.append("")

    # Show relative path
    try:
        rel = file_path.relative_to(vault_path)
        lines.append(f"*{rel.as_posix()}*")
    except ValueError:
        lines.append(f"*{file_path}*")

    return "\n".join(lines)
