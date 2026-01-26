"""
Semantic change classifier.

Compares before/after versions of a note and emits typed change events.
This is structural diff, not text diff.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .event_types import (
    ChangeEvent,
    ChangeType,
    InvariantImpact,
    StructuralEffects,
)


def _extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter as dict."""
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    try:
        import yaml
        return yaml.safe_load(content[4:end]) or {}
    except Exception:
        return {}


def _extract_sections(content: str) -> set[str]:
    """Extract ## headings from markdown."""
    return set(re.findall(r"^## (.+)$", content, re.M))


def _extract_links(content: str) -> set[str]:
    """Extract all wikilinks from content."""
    return set(re.findall(r"\[\[([^\]|#]+)", content))


def _extract_structural_deps(content: str) -> set[str]:
    """Extract dependencies from ## Structural dependencies section."""
    lowered = content.lower()
    marker = "## structural dependencies"
    idx = lowered.find(marker)
    if idx == -1:
        return set()
    start = idx + len(marker)
    end = lowered.find("\n## ", start)
    if end == -1:
        end = len(content)
    section = content[start:end]
    # Extract wikilinks from section
    return set(re.findall(r"\[\[([^\]|#]+)", section))


def _compute_ambiguity_delta(
    before_deps: set[str],
    after_deps: set[str],
    before_sections: set[str],
    after_sections: set[str],
) -> int:
    """Estimate ambiguity change.

    Heuristic:
    - More explicit dependencies -> less ambiguous (-1 per dep added)
    - Fewer dependencies -> more ambiguous (+1 per dep removed)
    - Structural sections added -> less ambiguous (-1)
    - Structural sections removed -> more ambiguous (+1)
    """
    delta = 0
    delta -= len(after_deps - before_deps)  # deps added
    delta += len(before_deps - after_deps)  # deps removed

    key_sections = {"Definition", "What this is NOT", "Structural dependencies"}
    before_key = before_sections & key_sections
    after_key = after_sections & key_sections

    delta -= len(after_key - before_key)  # key sections added
    delta += len(before_key - after_key)  # key sections removed

    return delta


def classify_change(
    note_id: str,
    before_content: Optional[str],
    after_content: Optional[str],
    git_commit: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> ChangeEvent:
    """Classify a change by comparing before and after content.

    Args:
        note_id: Vault-relative path (e.g., "concepts/constraint-load")
        before_content: Content before change (None if new file)
        after_content: Content after change (None if deleted)
        git_commit: Optional git SHA for provenance
        timestamp: Optional timestamp (defaults to now)

    Returns:
        A ChangeEvent capturing the structural effects
    """
    ts = timestamp or datetime.now()
    change_types: list[ChangeType] = []

    # Handle file creation/deletion
    if before_content is None:
        before_content = ""
    if after_content is None:
        after_content = ""

    # Extract structural elements
    before_fm = _extract_frontmatter(before_content)
    after_fm = _extract_frontmatter(after_content)

    before_sections = _extract_sections(before_content)
    after_sections = _extract_sections(after_content)

    before_deps = _extract_structural_deps(before_content)
    after_deps = _extract_structural_deps(after_content)

    before_links = _extract_links(before_content)
    after_links = _extract_links(after_content)

    # Classify by structural effects

    # Dependency changes
    deps_added = after_deps - before_deps
    deps_removed = before_deps - after_deps
    if deps_added:
        change_types.append(ChangeType.DEPENDENCY_ADDITION)
    if deps_removed:
        change_types.append(ChangeType.DEPENDENCY_REMOVAL)

    # Link changes (non-dependency)
    non_dep_before = before_links - before_deps
    non_dep_after = after_links - after_deps
    links_added = non_dep_after - non_dep_before
    links_removed = non_dep_before - non_dep_after
    if links_added:
        change_types.append(ChangeType.LINK_ADDITION)
    if links_removed:
        change_types.append(ChangeType.LINK_REMOVAL)

    # Section changes
    sections_added = after_sections - before_sections
    sections_removed = before_sections - after_sections
    if sections_added:
        change_types.append(ChangeType.SECTION_ADDITION)
    if sections_removed:
        change_types.append(ChangeType.SECTION_REMOVAL)

    # Definition changes
    if "Definition" in before_sections or "Definition" in after_sections:
        before_def = _extract_section_content(before_content, "Definition")
        after_def = _extract_section_content(after_content, "Definition")
        if before_def != after_def:
            change_types.append(ChangeType.DEFINITION_REFINEMENT)

    # Role changes
    role_before = before_fm.get("role")
    role_after = after_fm.get("role")
    if role_before != role_after:
        change_types.append(ChangeType.ROLE_CHANGE)

    # Layer changes
    layer_before = before_fm.get("layer")
    layer_after = after_fm.get("layer")
    if layer_before != layer_after:
        change_types.append(ChangeType.LAYER_CHANGE)

    # Alias changes
    aliases_before = set(before_fm.get("aliases", []) or [])
    aliases_after = set(after_fm.get("aliases", []) or [])
    if aliases_before != aliases_after:
        change_types.append(ChangeType.ALIAS_CHANGE)

    # Tooling changes (self-referential)
    if note_id.startswith("irrev/") or note_id.endswith(".py"):
        change_types.append(ChangeType.TOOLING_CHANGE)

    # If no specific type detected
    if not change_types:
        change_types.append(ChangeType.UNKNOWN)

    # Build invariant impacts (placeholder - can be enhanced with lint diff)
    invariant_impacts: list[InvariantImpact] = []

    # Heuristic: more explicit deps -> better decomposition
    if deps_added:
        invariant_impacts.append(
            InvariantImpact(
                invariant="decomposition",
                direction="improved",
                detail=f"Added explicit dependencies: {', '.join(sorted(deps_added))}",
            )
        )

    # Compute ambiguity delta
    ambiguity_delta = _compute_ambiguity_delta(
        before_deps, after_deps, before_sections, after_sections
    )

    # Build effects
    effects = StructuralEffects(
        dependencies_added=tuple(sorted(deps_added)),
        dependencies_removed=tuple(sorted(deps_removed)),
        links_added=tuple(sorted(links_added)),
        links_removed=tuple(sorted(links_removed)),
        sections_added=tuple(sorted(sections_added)),
        sections_removed=tuple(sorted(sections_removed)),
        role_before=role_before,
        role_after=role_after,
        layer_before=layer_before,
        layer_after=layer_after,
        invariant_impacts=tuple(invariant_impacts),
        violations_introduced=(),  # Requires lint comparison
        violations_resolved=(),  # Requires lint comparison
    )

    return ChangeEvent(
        timestamp=ts,
        note_id=note_id,
        change_types=tuple(change_types),
        structural_effects=effects,
        ambiguity_delta=ambiguity_delta,
        git_commit=git_commit,
    )


def _extract_section_content(content: str, heading: str) -> str:
    """Extract content of a specific section."""
    lowered = content.lower()
    marker = f"## {heading.lower()}"
    idx = lowered.find(marker)
    if idx == -1:
        return ""
    start = idx + len(marker)
    end = lowered.find("\n## ", start)
    if end == -1:
        end = len(content)
    return content[start:end].strip()
