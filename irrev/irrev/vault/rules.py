"""Lint rules for vault validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .graph import DependencyGraph
    from .loader import Vault


@dataclass
class LintResult:
    """A single lint finding."""

    level: Literal["error", "warning", "info"]
    rule: str
    file: Path
    message: str
    line: int | None = None

    def __str__(self) -> str:
        loc = f"{self.file.name}"
        if self.line:
            loc += f":{self.line}"
        return f"{self.level.upper()}: [{self.rule}] {loc} - {self.message}"


class LintRules:
    """Collection of lint rules for vault validation."""

    def __init__(self, vault: "Vault", graph: "DependencyGraph"):
        self.vault = vault
        self.graph = graph

    def run_all(self) -> list[LintResult]:
        """Run all lint checks and return findings."""
        results = []
        results.extend(self.check_forbidden_edges())
        results.extend(self.check_missing_structural_dependencies())
        results.extend(self.check_alias_drift())
        results.extend(self.check_cycles())
        results.extend(self.check_missing_role())
        results.extend(self.check_broken_links())
        results.extend(self.check_layer_violations())
        return results

    def check_forbidden_edges(self) -> list[LintResult]:
        """Check for forbidden link patterns.

        Rules:
        - concept → paper (concepts should be self-contained)
        - diagnostic → paper (diagnostics reference registry, not papers)
        """
        results = []

        paper_names = {p.name.lower() for p in self.vault.papers}

        # Check concepts
        for concept in self.vault.concepts:
            for link in concept.links:
                if link in paper_names:
                    results.append(
                        LintResult(
                            level="warning",
                            rule="forbidden-edge",
                            file=concept.path,
                            message=f"Concept links to paper '{link}' - concepts should be self-contained",
                        )
                    )

        # Check diagnostics
        for diag in self.vault.diagnostics:
            for link in diag.links:
                if link in paper_names:
                    # Allow links to registry and specific papers
                    if "registry" not in link.lower():
                        results.append(
                            LintResult(
                                level="info",
                                rule="forbidden-edge",
                                file=diag.path,
                                message=f"Diagnostic links to paper '{link}'",
                            )
                        )

        return results

    def check_missing_structural_dependencies(self) -> list[LintResult]:
        """Check that concepts have a Structural dependencies section."""
        results = []

        for concept in self.vault.concepts:
            if "## Structural dependencies" not in concept.content:
                results.append(
                    LintResult(
                        level="error",
                        rule="missing-dependencies",
                        file=concept.path,
                        message="Concept missing '## Structural dependencies' section",
                    )
                )

        return results

    def check_alias_drift(self) -> list[LintResult]:
        """Check for inconsistent alias usage across the vault.

        Warns when a non-canonical alias is used instead of the canonical name.
        """
        results = []

        # Build reverse alias map: alias -> canonical
        alias_to_canonical = {}
        for concept in self.vault.concepts:
            canonical = concept.name.lower()
            for alias in concept.aliases:
                alias_to_canonical[alias.lower()] = canonical

        # Check all notes for alias usage
        for note in self.vault.all_notes:
            for link in note.links:
                if link in alias_to_canonical:
                    canonical = alias_to_canonical[link]
                    if link != canonical:
                        results.append(
                            LintResult(
                                level="info",
                                rule="alias-drift",
                                file=note.path,
                                message=f"Uses alias '{link}' instead of canonical '{canonical}'",
                            )
                        )

        return results

    def check_cycles(self) -> list[LintResult]:
        """Check for dependency cycles among concepts."""
        results = []

        cycles = self.graph.find_cycles()
        for cycle in cycles:
            cycle_str = " → ".join(cycle)
            # Report on first node in cycle
            if cycle and cycle[0] in self.graph.nodes:
                concept = self.graph.nodes[cycle[0]]
                results.append(
                    LintResult(
                        level="error",
                        rule="dependency-cycle",
                        file=concept.path,
                        message=f"Dependency cycle detected: {cycle_str}",
                    )
                )

        return results

    def check_missing_role(self) -> list[LintResult]:
        """Check that notes have role in frontmatter."""
        results = []

        for note in self.vault.all_notes:
            if not note.frontmatter.get("role"):
                results.append(
                    LintResult(
                        level="warning",
                        rule="missing-role",
                        file=note.path,
                        message="Note missing 'role' in frontmatter",
                    )
                )

        return results

    def check_broken_links(self) -> list[LintResult]:
        """Check for wiki-links that don't resolve to existing notes."""
        results = []

        # Build set of all known note names
        known_names = set()
        for note in self.vault.all_notes:
            known_names.add(note.name.lower())
            if hasattr(note, "aliases"):
                for alias in note.aliases:
                    known_names.add(alias.lower())

        # Check all links
        for note in self.vault.all_notes:
            for link in note.links:
                normalized = self.vault.normalize_name(link)
                if normalized not in known_names and link not in known_names:
                    results.append(
                        LintResult(
                            level="warning",
                            rule="broken-link",
                            file=note.path,
                            message=f"Broken link to '{link}' - note not found",
                        )
                    )

        return results

    def check_layer_violations(self) -> list[LintResult]:
        """Check that primitives don't depend on non-primitives.

        Layer hierarchy (lower can't depend on higher):
        1. primitive / foundational (no deps or only other primitives)
        2. first-order (can depend on primitives)
        3. accounting (can depend on primitives and first-order)
        4. selector / failure-state / meta-analytical (can depend on anything)
        """
        results = []

        # Define layer ordering (lower number = more primitive)
        layer_order = {
            "primitive": 0,
            "foundational": 0,
            "first-order": 1,
            "accounting": 2,
            "selector": 3,
            "failure-state": 3,
            "meta-analytical": 3,
            "unknown": 99,
        }

        for concept in self.vault.concepts:
            concept_layer = layer_order.get(concept.layer, 99)

            for dep_name in concept.depends_on:
                dep_concept = self.vault.get(dep_name)
                if dep_concept and hasattr(dep_concept, "layer"):
                    dep_layer = layer_order.get(dep_concept.layer, 99)
                    if dep_layer > concept_layer:
                        results.append(
                            LintResult(
                                level="error",
                                rule="layer-violation",
                                file=concept.path,
                                message=f"'{concept.layer}' concept depends on '{dep_concept.layer}' concept '{dep_name}'",
                            )
                        )

        return results
