"""Golden tests for all lint rules."""

from pathlib import Path

import pytest

from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import Vault
from irrev.vault.rules import LintRules


def test_layer_violation(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test layer-violation rule catches primitive depending on accounting."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_layer_violations()

    violations = [r for r in results if r.rule == "layer-violation"]
    # Should catch: primitive-bad-dep (primitive→accounting) and object-bad-operator (accounting→selector)
    assert len(violations) >= 1

    # Check that primitive-bad-dep violation is present
    primitive_violations = [v for v in violations if v.file.name == "primitive-bad-dep.md"]
    assert len(primitive_violations) == 1
    assert primitive_violations[0].level == "error"
    assert "accounting" in primitive_violations[0].message.lower()


def test_kind_violation(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test kind-violation rule catches object depending on operator."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_kind_violations()

    violations = [r for r in results if r.rule == "kind-violation"]
    assert len(violations) == 1
    assert violations[0].file.name == "object-bad-operator.md"
    assert violations[0].level == "error"
    assert "operator" in violations[0].message.lower()


def test_dependency_cycle(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test dependency-cycle rule detects circular dependencies."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_cycles()

    cycles = [r for r in results if r.rule == "dependency-cycle"]
    assert len(cycles) >= 1
    assert cycles[0].level == "error"
    # Should mention both cycle-a and cycle-b
    assert "cycle" in cycles[0].message.lower()


def test_missing_dependencies_section(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test missing-dependencies rule catches concepts without Structural dependencies."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_missing_structural_dependencies()

    missing = [r for r in results if r.rule == "missing-dependencies"]
    assert len(missing) == 1
    assert missing[0].file.name == "missing-deps-section.md"
    assert missing[0].level == "error"


def test_broken_link(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test broken-link rule detects links to non-existent notes."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_broken_links()

    broken = [r for r in results if r.rule == "broken-link"]
    assert len(broken) >= 1
    # Should detect non-existent-note
    assert any("non-existent" in r.message.lower() for r in broken)
    assert all(r.level == "warning" for r in broken)


def test_forbidden_edge_concept_to_paper(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test forbidden-edge rule catches concept linking to paper."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_forbidden_edges()

    forbidden = [r for r in results if r.rule == "forbidden-edge" and "concept" in r.message.lower()]
    assert len(forbidden) >= 1
    assert any("test-paper" in r.message.lower() for r in forbidden)
    # Concept → paper should be warning
    assert all(r.level == "warning" for r in forbidden)


def test_missing_role(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test missing-role rule detects notes without role frontmatter."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_missing_role()

    missing = [r for r in results if r.rule == "missing-role"]
    assert len(missing) >= 1
    assert any("missing-role.md" in str(r.file) for r in missing)
    assert all(r.level == "warning" for r in missing)


def test_alias_drift_not_in_minimal_vault(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test alias-drift rule (should have no violations in minimal vault)."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.check_alias_drift()

    # Minimal vault has no aliases, so no drift
    assert all(r.rule != "alias-drift" for r in results)


def test_run_all_rules(fixture_vault: Vault, fixture_graph: DependencyGraph):
    """Test run_all collects findings from all rules."""
    rules = LintRules(fixture_vault, fixture_graph)
    results = rules.run_all()

    # Should have errors from multiple rules
    rule_names = {r.rule for r in results}

    # Expected rules that should fire
    assert "layer-violation" in rule_names
    assert "kind-violation" in rule_names
    assert "dependency-cycle" in rule_names
    assert "missing-dependencies" in rule_names
    assert "broken-link" in rule_names
    assert "forbidden-edge" in rule_names
    assert "missing-role" in rule_names

    # Count errors vs warnings
    errors = [r for r in results if r.level == "error"]
    warnings = [r for r in results if r.level == "warning"]

    assert len(errors) >= 4  # layer, kind, cycle, missing-deps
    assert len(warnings) >= 2  # broken-link, missing-role


def test_fixture_vault_structure(fixture_vault: Vault):
    """Test fixture vault loads correctly with expected structure."""
    # Check all note types present
    assert len(fixture_vault.concepts) >= 10
    assert len(fixture_vault.diagnostics) >= 2
    assert len(fixture_vault.domains) >= 1
    assert len(fixture_vault.projections) >= 1
    assert len(fixture_vault.papers) >= 1

    # Check operator notes present (3+ required)
    operators = [c for c in fixture_vault.concepts
                 if c.frontmatter.get("note_kind") == "operator"]
    assert len(operators) >= 3

    # Check specific operators exist
    operator_names = {op.name for op in operators}
    assert "admissibility" in operator_names
    assert "displacement-check" in operator_names
    assert "erasure-cost-check" in operator_names


def test_fixture_vault_graph_construction(fixture_graph: DependencyGraph):
    """Test dependency graph builds correctly from fixture vault."""
    # Should have nodes
    assert len(fixture_graph.nodes) >= 10

    # Should have edges
    assert len(fixture_graph.edges) > 0

    # Test specific dependency exists
    assert "primitive-ok" in fixture_graph.nodes

    # accounting-concept should depend on primitive-ok
    deps = fixture_graph.get_dependencies("accounting-concept")
    assert "primitive-ok" in deps
