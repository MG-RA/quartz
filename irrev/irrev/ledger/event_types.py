"""
Canonical change event types for structural accounting.

These types capture what a change *did* to structure, not what text changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class ChangeType(str, Enum):
    """Structural change types.

    Each type represents a distinct kind of structural effect:
    - DEFINITION_REFINEMENT: The definition section changed (scope, clarity)
    - DEPENDENCY_ADDITION: A structural dependency was added
    - DEPENDENCY_REMOVAL: A structural dependency was removed
    - LAYER_CHANGE: The concept's layer classification changed
    - ROLE_CHANGE: The note's role changed (concept -> diagnostic, etc.)
    - INVARIANT_VIOLATION_INTRODUCED: A lint violation was introduced
    - INVARIANT_VIOLATION_RESOLVED: A lint violation was resolved
    - SECTION_ADDITION: A structural section was added (## Definition, etc.)
    - SECTION_REMOVAL: A structural section was removed
    - ALIAS_CHANGE: Aliases were added/removed
    - LINK_ADDITION: A wikilink was added (not in Structural dependencies)
    - LINK_REMOVAL: A wikilink was removed
    - TOOLING_CHANGE: A change to irrev tooling (self-referential)
    - UNKNOWN: Change detected but not classifiable
    """
    DEFINITION_REFINEMENT = "definition_refinement"
    DEPENDENCY_ADDITION = "dependency_addition"
    DEPENDENCY_REMOVAL = "dependency_removal"
    LAYER_CHANGE = "layer_change"
    ROLE_CHANGE = "role_change"
    INVARIANT_VIOLATION_INTRODUCED = "invariant_violation_introduced"
    INVARIANT_VIOLATION_RESOLVED = "invariant_violation_resolved"
    SECTION_ADDITION = "section_addition"
    SECTION_REMOVAL = "section_removal"
    ALIAS_CHANGE = "alias_change"
    LINK_ADDITION = "link_addition"
    LINK_REMOVAL = "link_removal"
    TOOLING_CHANGE = "tooling_change"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InvariantImpact:
    """Impact on a specific invariant.

    direction: "improved" | "degraded" | "unchanged"
    """
    invariant: str  # decomposition, governance, attribution, irreversibility
    direction: Literal["improved", "degraded", "unchanged"]
    detail: str = ""  # Optional explanation


@dataclass(frozen=True)
class StructuralEffects:
    """Structural effects of a change."""

    # Dependencies
    dependencies_added: tuple[str, ...] = field(default_factory=tuple)
    dependencies_removed: tuple[str, ...] = field(default_factory=tuple)

    # Links (non-dependency wikilinks)
    links_added: tuple[str, ...] = field(default_factory=tuple)
    links_removed: tuple[str, ...] = field(default_factory=tuple)

    # Sections
    sections_added: tuple[str, ...] = field(default_factory=tuple)
    sections_removed: tuple[str, ...] = field(default_factory=tuple)

    # Role/layer
    role_before: str | None = None
    role_after: str | None = None
    layer_before: str | None = None
    layer_after: str | None = None

    # Invariant effects
    invariant_impacts: tuple[InvariantImpact, ...] = field(default_factory=tuple)

    # Lint violations
    violations_introduced: tuple[str, ...] = field(default_factory=tuple)
    violations_resolved: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ChangeEvent:
    """A single structural change event.

    This is the unit of change accounting - a typed, attributed record
    of what a change did to structure.
    """

    # Identity
    timestamp: datetime
    note_id: str  # vault-relative path (e.g., "concepts/constraint-load")

    # Classification
    change_types: tuple[ChangeType, ...]  # A change may have multiple types

    # Effects
    structural_effects: StructuralEffects

    # Metrics
    ambiguity_delta: int = 0  # Positive = more ambiguous, negative = less

    # Provenance
    git_commit: str | None = None  # Optional git SHA

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "note_id": self.note_id,
            "change_types": [ct.value for ct in self.change_types],
            "structural_effects": {
                "dependencies_added": list(self.structural_effects.dependencies_added),
                "dependencies_removed": list(self.structural_effects.dependencies_removed),
                "links_added": list(self.structural_effects.links_added),
                "links_removed": list(self.structural_effects.links_removed),
                "sections_added": list(self.structural_effects.sections_added),
                "sections_removed": list(self.structural_effects.sections_removed),
                "role_before": self.structural_effects.role_before,
                "role_after": self.structural_effects.role_after,
                "layer_before": self.structural_effects.layer_before,
                "layer_after": self.structural_effects.layer_after,
                "invariant_impacts": [
                    {"invariant": ii.invariant, "direction": ii.direction, "detail": ii.detail}
                    for ii in self.structural_effects.invariant_impacts
                ],
                "violations_introduced": list(self.structural_effects.violations_introduced),
                "violations_resolved": list(self.structural_effects.violations_resolved),
            },
            "ambiguity_delta": self.ambiguity_delta,
            "git_commit": self.git_commit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeEvent":
        """Reconstruct from JSON dict."""
        effects_data = data["structural_effects"]
        effects = StructuralEffects(
            dependencies_added=tuple(effects_data.get("dependencies_added", [])),
            dependencies_removed=tuple(effects_data.get("dependencies_removed", [])),
            links_added=tuple(effects_data.get("links_added", [])),
            links_removed=tuple(effects_data.get("links_removed", [])),
            sections_added=tuple(effects_data.get("sections_added", [])),
            sections_removed=tuple(effects_data.get("sections_removed", [])),
            role_before=effects_data.get("role_before"),
            role_after=effects_data.get("role_after"),
            layer_before=effects_data.get("layer_before"),
            layer_after=effects_data.get("layer_after"),
            invariant_impacts=tuple(
                InvariantImpact(
                    invariant=ii["invariant"],
                    direction=ii["direction"],
                    detail=ii.get("detail", ""),
                )
                for ii in effects_data.get("invariant_impacts", [])
            ),
            violations_introduced=tuple(effects_data.get("violations_introduced", [])),
            violations_resolved=tuple(effects_data.get("violations_resolved", [])),
        )

        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            note_id=data["note_id"],
            change_types=tuple(ChangeType(ct) for ct in data["change_types"]),
            structural_effects=effects,
            ambiguity_delta=data.get("ambiguity_delta", 0),
            git_commit=data.get("git_commit"),
        )
