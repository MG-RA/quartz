"""Lint rules for vault validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .graph import DependencyGraph
    from .loader import Vault


# Rule explanations for --explain flag
RULE_EXPLANATIONS: dict[str, str] = {
    "forbidden-edge": """# forbidden-edge

**Invariant**: Governance

**What it checks:** Links from concepts or diagnostics to papers.

**Why it matters:**
- Concepts should be self-contained and not depend on paper-specific content.
- Diagnostics should reference the Registry (canonical definitions), not papers.
- This prevents authority bypass by ensuring papers don't become hidden dependencies.

**Allowed:** Diagnostics may link to the Registry paper.

**Fix:** Remove direct paper links from concepts. In diagnostics, link to Registry sections instead of papers.

**Level:** warning (concept→paper), info (diagnostic→paper except registry)
""",
    "missing-dependencies": """# missing-dependencies

**Invariant**: Irreversibility

**What it checks:** Concepts must have a `## Structural dependencies` section.

**Why it matters:**
- Explicit dependencies enable:
  - Dependency graph construction
  - Layer violation detection
  - Pack generation (transitive closure)
- Missing sections break tooling and hide accounting costs.
- Erasure costs cannot be declared without explicit dependency tracking.

**Fix:** Add `## Structural dependencies` section with either:
- `None (primitive)` or `None (axiomatic)` for foundational concepts
- List of `[[concept]]` links for composite concepts

**Level:** error
""",
    "alias-drift": """# alias-drift

**Structural Rule** (not an invariant - ensures graph coherence)

**What it checks:** Notes using non-canonical aliases instead of canonical concept names.

**Why it matters:**
- Canonical names ensure consistent linking and searching.
- Alias drift can cause confusion about which concept is referenced.
- This is basic graph hygiene that supports all invariants.

**Example:**
- Canonical: `persistent-difference`
- Alias: `persistent difference` (space instead of hyphen)
- Finding: "Uses alias 'persistent difference' instead of canonical 'persistent-difference'"

**Fix:** Replace alias with canonical name, or update the alias list if the usage is intentional.

**Level:** info
""",
    "dependency-cycle": """# dependency-cycle

**Structural Rule** (not an invariant - ensures graph coherence)

**What it checks:** Circular dependencies among concepts.

**Why it matters:**
- Cycles prevent topological sorting for packs.
- Cycles indicate definitional circularity (A depends on B depends on A).
- The concept graph must be a DAG (directed acyclic graph).
- This is foundational to all reasoning about the vault structure.

**Example:** `A → B → C → A` is a cycle.

**Fix:** Break the cycle by:
- Extracting a common dependency into a new primitive
- Re-examining which concept truly depends on which

**Level:** error
""",
    "missing-role": """# missing-role

**Invariant**: Governance

**What it checks:** Notes without `role` in frontmatter.

**Why it matters:**
- Role determines how the note is categorized (concept, diagnostic, domain, etc.).
- Missing role falls back to path-based inference, which may be incorrect.
- Every note must declare its role - no actor is exempt from structural constraints.
- Roles define authority and prevent silent failures in categorization.

**Fix:** Add `role: <type>` to frontmatter. Valid roles:
- `concept`, `diagnostic`, `domain`, `projection`, `paper`, `meta`, `support`, `template`

**Level:** warning
""",
    "broken-link": """# broken-link

**Structural Rule** (not an invariant - ensures graph coherence)

**What it checks:** Wiki-links (`[[target]]`) pointing to non-existent notes.

**Why it matters:**
- Broken links indicate missing content or typos.
- They break navigation and pack generation.
- This is basic reference integrity that enables all other tooling.

**Fix:**
- Create the missing note
- Fix the typo in the link
- Remove the link if the reference is no longer needed

**Level:** warning
""",
    "registry-drift": """# registry-drift

**Structural Rule** (not an invariant - prevents registry drift)

**What it checks:** The committed Registry dependency tables are out of sync with the generated tables.

**Why it matters:**
- Concepts are the source of truth for layers and structural dependencies.
- The Registry is an interface artifact; drift creates two competing vocabularies.
- Treating the Registry tables as generated prevents silent exclusion and stale snapshots.

**Fix:** Regenerate the tables in-place:

- `irrev -v <vault> registry build --in-place`

**Level:** error
""",
    "mechanism-missing-residuals": """# mechanism-missing-residuals

**Invariant**: Irreversibility

**What it checks:** Mechanism-layer concepts must include a `## Residuals` section.

**Why it matters:**
- Mechanisms are the operational bridge where persistence becomes concrete.
- Without explicit residuals, mechanism notes tend to imply “clean” operations and hide accumulation.

**Fix:** Add a `## Residuals` section describing what persists after the mechanism completes (no prescription).

**Level:** error
""",
    "hub-required-headings": """# hub-required-headings

**Invariant**: Irreversibility

**What it checks:** Hub concepts must include required sections to prevent drift.

**Why it matters:**
- Hubs are concepts explanations repeatedly converge through.
- Missing structural sections tends to reintroduce metaphor, scope creep, and hand-waving where the vault is load-bearing.

**Config:** `content/meta/hubs.yml` defines which concepts are hubs and which headings are required.

**Fix:** Add the missing headings (short, structural content is enough; avoid prescription).

**Level:** error
""",
    "layer-violation": """# layer-violation

**Invariant**: Decomposition

**What it checks:** Concepts depending on higher-layer concepts.

**Why it matters:**
The layer hierarchy ensures primitives are self-contained and scope is bounded:
1. **primitive/foundational** (layer 0): No deps or only other primitives
2. **first-order** (layer 1): Can depend on primitives
3. **mechanism** (layer 2): Can depend on primitives and first-order
4. **accounting** (layer 3): Can depend on primitives, first-order, and mechanisms
5. **selector/failure-state/meta-analytical** (layer 4): Can depend on anything

A primitive depending on an accounting concept violates this hierarchy and creates unbounded scope.

**Example:**
- `constraint` (primitive) depending on `collapse-surface` (accounting) is a violation.

**Fix:** Re-examine the dependency. Either:
- The dependency is incorrect and should be removed
- The concept's layer is misclassified

**Level:** error
""",
    "kind-violation": """# kind-violation

**Invariant**: Decomposition

**What it checks:** Object concepts depending on operator concepts.

**Why it matters:**
This is the object/operator seam for vault hygiene - the Decomposition invariant in action:
- **Object notes** (descriptive): Name structures in the world-model (nouns)
- **Operator notes** (procedural): Name tests/selectors applied to objects (verbs)

Objects should depend only on other objects (structural substrate).
Operators may depend on objects freely (they consume the substrate).

This separation prevents category errors and maintains clear role boundaries.

**Opt-in:** Only applies when `note_kind: object` or `note_kind: operator` is declared.

**Example:**
- `feasible-set` (object) depending on `admissibility` (operator) is a violation.
- `admissibility` (operator) depending on `feasible-set` (object) is allowed.

**Fix:** Re-examine the dependency. If an object truly depends on an operator, one of them is likely misclassified.

**Level:** error
""",
    "responsibility-scope": """# responsibility-scope

**Invariant**: Attribution

**What it checks:** Responsibility assignments in note content that lack explicit scope.

**Why it matters:**
- Responsibility must be explicit - vague assignments lead to diffusion.
- Diagnostics cannot prescribe - they can only describe failure modes.
- Roles define authority - responsibility without scope creates unbounded authority.

**Example:**
- "X is responsible for Y" without declaring the scope/context is a violation.
- Diagnostic notes prescribing solutions rather than describing failure modes.

**Fix:** Make responsibility assignments explicit with clear scope:
- Who is responsible
- For what
- Under what conditions
- What authority they have

**Level:** info
""",
}


def get_rule_ids() -> list[str]:
    """Return all known rule IDs."""
    return list(RULE_EXPLANATIONS.keys())


@dataclass
class LintResult:
    """A single lint finding."""

    level: Literal["error", "warning", "info"]
    rule: str
    file: Path
    message: str
    line: int | None = None
    invariant: str | None = None  # Which invariant this rule enforces (None for structural rules)

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

    def run_all(self, allowed_rules: set[str] | None = None) -> list[LintResult]:
        """
        Run all lint checks and return findings with invariant metadata attached.

        Args:
            allowed_rules: If provided, only run rules in this set. If None, run all rules.

        Returns:
            List of lint results with invariant metadata attached.
        """
        from irrev.vault.invariants import get_invariant_for_rule, STRUCTURAL_RULES

        # Rule ID to method mapping
        rule_checks = {
            "forbidden-edge": self.check_forbidden_edges,
            "missing-dependencies": self.check_missing_structural_dependencies,
            "mechanism-missing-residuals": self.check_mechanism_missing_residuals,
            "hub-required-headings": self.check_hub_required_headings,
            "alias-drift": self.check_alias_drift,
            "dependency-cycle": self.check_cycles,
            "missing-role": self.check_missing_role,
            "broken-link": self.check_broken_links,
            "registry-drift": self.check_registry_drift,
            "layer-violation": self.check_layer_violations,
            "kind-violation": self.check_kind_violations,
            "responsibility-scope": self.check_responsibility_without_scope,
        }

        # Execute rules (filtered if needed)
        results = []
        for rule_id, check_method in rule_checks.items():
            if allowed_rules is None or rule_id in allowed_rules:
                results.extend(check_method())

        # Attach invariant metadata to each result
        for result in results:
            inv = get_invariant_for_rule(result.rule)
            if inv:
                result.invariant = inv.id
            elif result.rule not in STRUCTURAL_RULES:
                # ANTI-CREEP LOCK: Unclassified rules are flagged
                # This should never happen in a well-maintained codebase
                result.invariant = None  # Explicitly mark as unclassified

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

    def check_mechanism_missing_residuals(self) -> list[LintResult]:
        """Check that mechanism-layer concepts explicitly declare residuals."""
        results: list[LintResult] = []

        for concept in self.vault.concepts:
            if (concept.layer or "").strip().lower() != "mechanism":
                continue

            if "## Residuals" not in (concept.content or ""):
                results.append(
                    LintResult(
                        level="error",
                        rule="mechanism-missing-residuals",
                        file=concept.path,
                        message="Mechanism concept missing '## Residuals' section",
                    )
                )

        return results

    def check_hub_required_headings(self) -> list[LintResult]:
        """Check that hub concepts include required headings (configured by the vault)."""
        hubs_path = (self.vault.path / "meta" / "hubs.yml").resolve()
        if not hubs_path.exists():
            return []

        try:
            import yaml  # type: ignore
        except Exception:
            return [
                LintResult(
                    level="error",
                    rule="hub-required-headings",
                    file=hubs_path,
                    message="Hub policy file present but PyYAML not available to parse it",
                )
            ]

        try:
            data = yaml.safe_load(hubs_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return [
                LintResult(
                    level="error",
                    rule="hub-required-headings",
                    file=hubs_path,
                    message=f"Failed to parse hub policy file: {e}",
                )
            ]

        hubs = data.get("hubs") or {}
        if not isinstance(hubs, dict):
            return []

        results: list[LintResult] = []

        for concept_key, spec in hubs.items():
            if not isinstance(concept_key, str) or not isinstance(spec, dict):
                continue

            concept = self.vault.get(concept_key)
            if not concept or not hasattr(concept, "content"):
                continue

            required = spec.get("required_headings") or []
            if not isinstance(required, list):
                continue

            for heading in required:
                if not isinstance(heading, str) or not heading.strip():
                    continue
                if heading not in concept.content:
                    results.append(
                        LintResult(
                            level="error",
                            rule="hub-required-headings",
                            file=concept.path,
                            message=f"Hub concept missing required heading: {heading}",
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

    def check_registry_drift(self) -> list[LintResult]:
        """Check that registry dependency tables are kept in sync."""
        registry_notes = [p for p in self.vault.papers if (p.role or "").strip().lower() == "registry"]
        if not registry_notes:
            registry_notes = [p for p in self.vault.papers if "registry" in p.name.lower()]

        if not registry_notes:
            return []

        if len(registry_notes) > 1:
            return [
                LintResult(
                    level="error",
                    rule="registry-drift",
                    file=registry_notes[0].path,
                    message="Multiple registry candidates found; pass --registry-path to `irrev registry build --in-place`",
                )
            ]

        registry_path = registry_notes[0].path
        existing_content = registry_path.read_text(encoding="utf-8")

        overrides_path = (self.vault.path / "meta" / "registry.overrides.yml").resolve()
        overrides_data: dict = {}
        if overrides_path.exists():
            try:
                import yaml  # type: ignore

                overrides_data = yaml.safe_load(overrides_path.read_text(encoding="utf-8")) or {}
            except Exception as e:
                return [
                    LintResult(
                        level="error",
                        rule="registry-drift",
                        file=overrides_path,
                        message=f"Failed to load registry overrides: {e}",
                    )
                ]

        from irrev.commands.registry import _extract_dependency_tables, _generate_dependency_tables

        try:
            generated_tables = _generate_dependency_tables(
                self.vault,
                self.graph,
                overrides_data=overrides_data,
                allow_unknown_layers=False,
            )
        except ValueError as e:
            return [LintResult(level="error", rule="registry-drift", file=registry_path, message=str(e))]

        existing_tables = _extract_dependency_tables(existing_content)
        if existing_tables != generated_tables:
            return [
                LintResult(
                    level="error",
                    rule="registry-drift",
                    file=registry_path,
                    message="Registry tables out of sync; run `irrev -v <vault> registry build --in-place`",
                )
            ]

        return []

    def check_layer_violations(self) -> list[LintResult]:
        """Check that primitives don't depend on non-primitives.

        Layer hierarchy (lower can't depend on higher):
        1. primitive / foundational (no deps or only other primitives)
        2. first-order (can depend on primitives)
        3. mechanism (can depend on primitives and first-order)
        4. accounting (can depend on primitives, first-order, and mechanisms)
        5. selector / failure-state / meta-analytical (can depend on anything)
        """
        results = []

        # Define layer ordering (lower number = more primitive)
        layer_order = {
            "primitive": 0,
            "foundational": 0,
            "first-order": 1,
            "mechanism": 2,
            "accounting": 3,
            "selector": 4,
            "failure-state": 4,
            "meta-analytical": 4,
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

    def check_kind_violations(self) -> list[LintResult]:
        """Check that object concepts don't depend on operator concepts.

        This is an orthogonal hygiene rule to prevent "object/operator seam" drift:
        a descriptive (object) note must not depend on a procedural/predicate (operator) note.

        The rule is opt-in via frontmatter:
        - note_kind: object|operator
        """
        results: list[LintResult] = []

        for concept in self.vault.concepts:
            concept_kind = (concept.frontmatter.get("note_kind") or "").strip().lower()
            if concept_kind != "object":
                continue

            for dep_name in concept.depends_on:
                dep_note = self.vault.get(dep_name)
                if not dep_note or not hasattr(dep_note, "frontmatter"):
                    continue

                dep_kind = (dep_note.frontmatter.get("note_kind") or "").strip().lower()
                if dep_kind == "operator":
                    results.append(
                        LintResult(
                            level="error",
                            rule="kind-violation",
                            file=concept.path,
                            message=f"'object' concept depends on 'operator' concept '{dep_name}'",
                        )
                    )

        return results

    def check_responsibility_without_scope(self) -> list[LintResult]:
        """Info-level check for responsibility assignment without explicit scope.

        Flags diagnostic/projection notes that appear to assign responsibility
        (e.g., "X is responsible for Y") but do not declare scope.

        Non-blocking by design: this is hygiene, not enforcement.
        """
        results: list[LintResult] = []

        def has_scope(note) -> bool:
            if "scope" in note.frontmatter:
                return True
            return "scope:" in note.content.lower()

        patterns = (
            "responsible for",
            "responsibility for",
            "who is responsible",
            "is responsible",
        )

        for note in list(self.vault.diagnostics) + list(self.vault.projections):
            text = note.content.lower()
            if any(p in text for p in patterns) and not has_scope(note):
                results.append(
                    LintResult(
                        level="info",
                        rule="responsibility-scope",
                        file=note.path,
                        message="Assigns responsibility without an explicit scope declaration",
                    )
                )

        return results
