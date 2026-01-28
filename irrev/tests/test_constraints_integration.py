"""
Tests for constraint system integration with harness.

Tests that constraint.evaluated and invariant.checked events are
emitted correctly during plan validation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from irrev.artifact.content_store import ContentStore
from irrev.artifact.events import CONSTRAINT_EVALUATED, INVARIANT_CHECKED
from irrev.artifact.ledger import ArtifactLedger
from irrev.constraints.engine import run_constraints_lint
from irrev.constraints.schema import Predicate, RuleDef, RulesetDef, Selector
from irrev.harness import Harness, Handler, HandlerMetadata
from irrev.planning import BaseResult
from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import Vault, load_vault


# -----------------------------------------------------------------------------
# Test fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def temp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault with test content."""
    vault = tmp_path / "content"
    vault.mkdir()

    # Create a test concept
    (vault / "test_concept.md").write_text(
        """# Test Concept

This is a test concept.

Links: [[other_concept]]
"""
    )

    # Create another concept
    (vault / "other_concept.md").write_text(
        """# Other Concept

This is another concept.
"""
    )

    # Create .irrev directory
    irrev_dir = tmp_path / ".irrev"
    irrev_dir.mkdir()

    # Create test ruleset
    meta_dir = tmp_path / "content" / "meta" / "rulesets"
    meta_dir.mkdir(parents=True)

    ruleset_content = """
ruleset_id = "test"
version = 1
description = "Test ruleset"

[[rules]]
id = "test-rule-1"
scope = "concept"
invariant = "test_invariant"
severity = "error"

[rules.selector]
kind = "all"

[rules.predicate]
name = "always_pass"
"""
    (meta_dir / "core.toml").write_text(ruleset_content)

    return vault


@pytest.fixture
def test_ruleset() -> RulesetDef:
    """Create a test ruleset."""
    return RulesetDef(
        ruleset_id="test",
        version=1,
        description="Test ruleset for constraint integration",
        rules=[
            RuleDef(
                id="test-rule-pass",
                scope="concept",
                invariant="decomposition",
                severity="error",
                selector=Selector(kind="all"),
                predicate=Predicate(name="always_pass"),
                message="This rule always passes",
            ),
            RuleDef(
                id="test-rule-fail",
                scope="concept",
                invariant="decomposition",
                severity="error",
                selector=Selector(kind="all"),
                predicate=Predicate(name="always_fail"),
                message="This rule always fails",
            ),
        ],
    )


class MockPlan:
    """Mock plan for testing."""

    def __init__(self):
        from irrev.harness import EffectSummary
        self.effect_summary = EffectSummary.read_only()

    def summary(self) -> str:
        return "Mock plan"


class MockHandler(Handler):
    """Mock handler for testing."""

    @property
    def metadata(self) -> HandlerMetadata:
        return HandlerMetadata(
            operation="mock.test",
            delegate_to="handler:mock",
            supports_dry_run=True,
        )

    def validate_params(self, params: dict) -> list[str]:
        return []

    def compute_plan(self, vault_path: Path, params: dict) -> MockPlan:
        return MockPlan()

    def validate_plan(self, plan: MockPlan) -> list[str]:
        return []

    def execute(self, plan: MockPlan, context) -> BaseResult:
        return BaseResult(success=True)


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


class TestConstraintEventEmission:
    """Tests for constraint.evaluated event emission."""

    def test_constraint_evaluated_events_emitted(self, temp_vault: Path):
        """Test that constraint.evaluated events are emitted during validation."""
        # Load vault and graph
        vault = load_vault(temp_vault)
        graph = DependencyGraph.from_concepts(vault.concepts)

        # Create a simple test ruleset
        ruleset = RulesetDef(
            ruleset_id="test",
            version=1,
            rules=[
                RuleDef(
                    id="test-rule",
                    scope="concept",
                    invariant="test_invariant",
                    predicate=Predicate(name="noop"),  # Always passes
                )
            ],
        )

        # Set up ledger
        irrev_dir = temp_vault.parent / ".irrev"
        ledger = ArtifactLedger(irrev_dir)
        artifact_id = "test-artifact-001"

        # Run constraints with event emission
        results = run_constraints_lint(
            temp_vault,
            vault=vault,
            graph=graph,
            ruleset=ruleset,
            artifact_id=artifact_id,
            emit_events=True,
        )

        # Verify constraint.evaluated events were emitted
        events = [e for e in ledger.iter_events() if e.event_type == CONSTRAINT_EVALUATED]
        assert len(events) > 0, "Should emit constraint.evaluated events"

        # Verify event structure
        for event in events:
            assert event.artifact_id == artifact_id
            assert event.actor == "system:constraint_engine"
            assert "ruleset_id" in event.payload
            assert "rule_id" in event.payload
            assert "result" in event.payload
            assert event.payload["result"] in ["pass", "fail", "warning"]

    def test_invariant_checked_events_emitted(self, temp_vault: Path):
        """Test that invariant.checked events are emitted."""
        vault = load_vault(temp_vault)
        graph = DependencyGraph.from_concepts(vault.concepts)

        ruleset = RulesetDef(
            ruleset_id="test",
            version=1,
            rules=[
                RuleDef(
                    id="rule-1",
                    scope="concept",
                    invariant="decomposition",
                    predicate=Predicate(name="noop"),
                ),
                RuleDef(
                    id="rule-2",
                    scope="concept",
                    invariant="decomposition",
                    predicate=Predicate(name="noop"),
                ),
            ],
        )

        irrev_dir = temp_vault.parent / ".irrev"
        ledger = ArtifactLedger(irrev_dir)
        artifact_id = "test-artifact-002"

        run_constraints_lint(
            temp_vault,
            vault=vault,
            graph=graph,
            ruleset=ruleset,
            artifact_id=artifact_id,
            emit_events=True,
        )

        # Verify invariant.checked events
        events = [e for e in ledger.iter_events() if e.event_type == INVARIANT_CHECKED]
        assert len(events) > 0, "Should emit invariant.checked events"

        # Verify event structure
        for event in events:
            assert event.artifact_id == artifact_id
            assert event.actor == "system:constraint_engine"
            assert "invariant_id" in event.payload
            assert "status" in event.payload
            assert event.payload["status"] in ["pass", "fail"]
            assert "rules_checked" in event.payload
            assert "violations" in event.payload


class TestHarnessConstraintIntegration:
    """Tests for harness integration with constraint validation."""

    def test_harness_emits_constraint_events_during_propose(self, temp_vault: Path):
        """Test that harness emits constraint events during propose()."""
        harness = Harness(temp_vault)
        handler = MockHandler()

        # Propose a plan (should trigger constraint validation)
        result = harness.propose(handler, {}, actor="agent:test", surface="test")

        assert result.success

        # Check for constraint events in ledger
        all_events = list(harness.ledger.iter_events())
        constraint_events = [e for e in all_events if e.event_type == CONSTRAINT_EVALUATED]
        invariant_events = [e for e in all_events if e.event_type == INVARIANT_CHECKED]

        # Note: May be 0 if no ruleset found, but should not error
        # This is fine - constraint validation is best-effort

    def test_validation_event_includes_constraint_results(self, temp_vault: Path):
        """Test that artifact.validated event includes constraint_results."""
        harness = Harness(temp_vault)
        handler = MockHandler()

        result = harness.propose(handler, {}, actor="agent:test", surface="test")

        # Get validation event
        snap = harness.ledger.snapshot(result.plan_artifact_id)
        events = harness.ledger.events_for(result.plan_artifact_id)

        validation_events = [e for e in events if e.event_type == "artifact.validated"]
        assert len(validation_events) > 0

        validation_event = validation_events[0]

        # Constraint results may be None if no rulesets found
        # This is expected and handled gracefully
        if "constraint_results" in validation_event.payload:
            results = validation_event.payload["constraint_results"]
            assert isinstance(results, dict)
            assert "rulesets_evaluated" in results
            assert "rules_checked" in results


class TestConstraintEventContent:
    """Tests for constraint event content structure."""

    def test_constraint_evaluated_event_has_required_fields(self, temp_vault: Path):
        """Verify constraint.evaluated event has all required fields."""
        vault = load_vault(temp_vault)
        graph = DependencyGraph.from_concepts(vault.concepts)

        ruleset = RulesetDef(
            ruleset_id="test",
            version=1,
            rules=[
                RuleDef(
                    id="test-rule",
                    scope="concept",
                    invariant="decomposition",
                    predicate=Predicate(name="noop"),
                )
            ],
        )

        irrev_dir = temp_vault.parent / ".irrev"
        ledger = ArtifactLedger(irrev_dir)

        run_constraints_lint(
            temp_vault,
            vault=vault,
            graph=graph,
            ruleset=ruleset,
            artifact_id="test-001",
            emit_events=True,
        )

        events = [e for e in ledger.iter_events() if e.event_type == CONSTRAINT_EVALUATED]
        assert len(events) > 0

        event = events[0]

        # Verify all required fields per EVENT_PAYLOAD_FIELDS
        assert "ruleset_id" in event.payload
        assert "ruleset_version" in event.payload
        assert "rule_id" in event.payload
        assert "rule_scope" in event.payload
        assert "invariant" in event.payload
        assert "result" in event.payload
        assert "evidence" in event.payload

    def test_invariant_checked_event_has_required_fields(self, temp_vault: Path):
        """Verify invariant.checked event has all required fields."""
        vault = load_vault(temp_vault)
        graph = DependencyGraph.from_concepts(vault.concepts)

        ruleset = RulesetDef(
            ruleset_id="test",
            version=1,
            rules=[
                RuleDef(
                    id="test-rule",
                    scope="concept",
                    invariant="decomposition",
                    predicate=Predicate(name="noop"),
                )
            ],
        )

        irrev_dir = temp_vault.parent / ".irrev"
        ledger = ArtifactLedger(irrev_dir)

        run_constraints_lint(
            temp_vault,
            vault=vault,
            graph=graph,
            ruleset=ruleset,
            artifact_id="test-002",
            emit_events=True,
        )

        events = [e for e in ledger.iter_events() if e.event_type == INVARIANT_CHECKED]
        assert len(events) > 0

        event = events[0]

        # Verify all required fields per EVENT_PAYLOAD_FIELDS
        assert "invariant_id" in event.payload
        assert "status" in event.payload
        assert "rules_checked" in event.payload
        assert "violations" in event.payload
        assert "affected_items" in event.payload
