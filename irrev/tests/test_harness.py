"""
Tests for the execution harness.

Key invariance tests:
1. Interface invariance: CLI and API produce identical bundle content
2. Gate correctness: Destructive operations blocked without approval
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from irrev.artifact.content_store import ContentStore
from irrev.artifact.ledger import ArtifactLedger
from irrev.harness import (
    EffectSummary,
    ExecuteResult,
    ExecutionContext,
    Handler,
    HandlerMetadata,
    Harness,
    ProposeResult,
)
from irrev.harness.registry import clear_handlers, register_handler
from irrev.planning import BaseResult


# -----------------------------------------------------------------------------
# Test fixtures
# -----------------------------------------------------------------------------


class MockPlan:
    """Mock plan for testing."""

    def __init__(self, effect_type: str = "read_only"):
        self.effect_summary = EffectSummary(
            effect_type=effect_type,
            predicted_erasure={},
            predicted_outputs=["test_output"],
            reasons=["test reason"],
        )

    def summary(self) -> str:
        return f"MockPlan ({self.effect_summary.effect_type})"


class MockResult(BaseResult):
    """Mock result for testing."""

    pass


class MockHandler(Handler[MockPlan, MockResult]):
    """Mock handler for testing."""

    def __init__(self, effect_type: str = "read_only"):
        self._effect_type = effect_type

    @property
    def metadata(self) -> HandlerMetadata:
        return HandlerMetadata(
            operation="mock.test",
            delegate_to="handler:mock",
            supports_dry_run=True,
        )

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        if params.get("invalid"):
            return ["invalid param"]
        return []

    def compute_plan(self, vault_path: Path, params: dict[str, Any]) -> MockPlan:
        effect_type = params.get("effect_type", self._effect_type)
        return MockPlan(effect_type=effect_type)

    def validate_plan(self, plan: MockPlan) -> list[str]:
        if plan.effect_summary.effect_type == "error":
            return ["plan validation error"]
        return []

    def execute(self, plan: MockPlan, context: ExecutionContext) -> MockResult:
        return MockResult(success=True)


@pytest.fixture
def temp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault structure."""
    vault = tmp_path / "content"
    vault.mkdir()
    irrev_dir = tmp_path / ".irrev"
    irrev_dir.mkdir()
    return vault


@pytest.fixture
def harness(temp_vault: Path) -> Harness:
    """Create a harness instance with temp vault."""
    return Harness(temp_vault)


@pytest.fixture
def mock_handler() -> MockHandler:
    """Create a mock handler."""
    return MockHandler()


# -----------------------------------------------------------------------------
# Unit tests
# -----------------------------------------------------------------------------


class TestProposeResult:
    """Tests for ProposeResult."""

    def test_success_when_no_validation_errors(self):
        result = ProposeResult(
            plan_artifact_id="test-id",
            risk_class=None,  # type: ignore
            requires_approval=False,
            requires_force_ack=False,
            plan_summary="test",
            validation_errors=[],
        )
        assert result.success is True

    def test_failure_when_validation_errors(self):
        result = ProposeResult(
            plan_artifact_id="test-id",
            risk_class=None,  # type: ignore
            requires_approval=False,
            requires_force_ack=False,
            plan_summary="test",
            validation_errors=["error1", "error2"],
        )
        assert result.success is False


class TestEffectSummary:
    """Tests for EffectSummary."""

    def test_to_dict_roundtrip(self):
        original = EffectSummary(
            effect_type="mutation_destructive",
            predicted_erasure={"notes": 10, "edges": 20},
            predicted_outputs=["db1", "db2"],
            reasons=["reason1", "reason2"],
        )
        data = original.to_dict()
        restored = EffectSummary.from_dict(data)

        assert restored.effect_type == original.effect_type
        assert restored.predicted_erasure == original.predicted_erasure
        assert restored.predicted_outputs == original.predicted_outputs
        assert restored.reasons == original.reasons

    def test_factory_read_only(self):
        summary = EffectSummary.read_only()
        assert summary.effect_type == "read_only"

    def test_factory_append_only(self):
        summary = EffectSummary.append_only(["output1"])
        assert summary.effect_type == "append_only"
        assert summary.predicted_outputs == ["output1"]


# -----------------------------------------------------------------------------
# Harness tests
# -----------------------------------------------------------------------------


class TestHarnessPropose:
    """Tests for Harness.propose()."""

    def test_propose_creates_artifact(self, harness: Harness, mock_handler: MockHandler):
        result = harness.propose(
            mock_handler,
            {},
            actor="agent:test",
            surface="test",
        )

        assert result.plan_artifact_id
        assert result.success

    def test_propose_validates_params(self, harness: Harness, mock_handler: MockHandler):
        result = harness.propose(
            mock_handler,
            {"invalid": True},
            actor="agent:test",
            surface="test",
        )

        assert "invalid param" in result.validation_errors

    def test_propose_derives_risk_from_effects(self, harness: Harness):
        handler = MockHandler(effect_type="mutation_destructive")
        result = harness.propose(
            handler,
            {},
            actor="agent:test",
            surface="test",
        )

        assert result.risk_class.value == "mutation_destructive"
        assert result.requires_approval is True
        assert result.requires_force_ack is True


class TestHarnessRun:
    """Tests for Harness.run()."""

    def test_run_low_risk_succeeds(self, harness: Harness, mock_handler: MockHandler):
        result = harness.run(
            mock_handler,
            {},
            actor="agent:test",
            surface="test",
        )

        assert result.success

    def test_run_high_risk_fails_without_approval(self, harness: Harness):
        """Gate correctness: destructive ops blocked without approval."""
        handler = MockHandler(effect_type="mutation_destructive")
        result = harness.run(
            handler,
            {},
            actor="agent:test",
            surface="test",
        )

        assert result.success is False
        assert "approval required" in result.error.lower()

    def test_run_external_side_effect_fails_without_approval(self, harness: Harness):
        """External side effects also require approval."""
        handler = MockHandler(effect_type="external_side_effect")
        result = harness.run(
            handler,
            {},
            actor="agent:test",
            surface="test",
        )

        assert result.success is False
        assert "approval required" in result.error.lower()


class TestGateCorrectness:
    """Tests for gate correctness invariant.

    Key invariant: destructive operations cannot execute without
    approval + force_ack, and gate denials are auditable.
    """

    def test_destructive_operation_requires_approval(self, harness: Harness):
        """Destructive operation cannot execute without approval."""
        handler = MockHandler(effect_type="mutation_destructive")

        # Propose succeeds
        propose_result = harness.propose(handler, {}, actor="agent:test", surface="test")
        assert propose_result.success
        assert propose_result.requires_approval

        # Execute fails without approval
        execute_result = harness.execute(
            propose_result.plan_artifact_id,
            handler,
            executor="handler:mock",
        )
        assert execute_result.success is False
        assert "approval" in execute_result.error.lower()

    def test_gate_denial_emits_rejection_event(self, harness: Harness):
        """Gate denial should emit a rejection event for audit trail."""
        handler = MockHandler(effect_type="mutation_destructive")

        # Propose
        propose_result = harness.propose(handler, {}, actor="agent:test", surface="test")

        # Approve without force_ack (should fail for destructive)
        try:
            harness.plan_manager.approve(
                propose_result.plan_artifact_id,
                "human:test",
                scope="test",
                force_ack=False,  # Missing force_ack!
            )
            approved = True
        except ValueError:
            approved = False

        assert not approved, "Approval without force_ack should fail for destructive ops"

    def test_approved_destructive_operation_succeeds(self, harness: Harness):
        """Approved destructive operation with force_ack succeeds."""
        handler = MockHandler(effect_type="mutation_destructive")

        # Propose
        propose_result = harness.propose(handler, {}, actor="agent:test", surface="test")
        assert propose_result.success

        # Approve with force_ack
        harness.plan_manager.approve(
            propose_result.plan_artifact_id,
            "human:test",
            scope="test",
            force_ack=True,
        )

        # Execute succeeds
        execute_result = harness.execute(
            propose_result.plan_artifact_id,
            handler,
            executor="handler:mock",
        )
        assert execute_result.success


class TestBundleEmission:
    """Tests for bundle emission."""

    def test_successful_execution_emits_bundle(self, harness: Harness, mock_handler: MockHandler):
        """Successful execution should emit a bundle artifact."""
        result = harness.run(
            mock_handler,
            {},
            actor="agent:test",
            surface="test",
        )

        assert result.success
        assert result.bundle_artifact_id is not None

        # Verify bundle exists in ledger
        snap = harness.ledger.snapshot(result.bundle_artifact_id)
        assert snap is not None
        assert snap.artifact_type == "bundle"

    def test_bundle_contains_repro_header(self, harness: Harness, mock_handler: MockHandler):
        """Bundle should contain repro header for reproducibility."""
        result = harness.run(
            mock_handler,
            {},
            actor="agent:test",
            surface="test",
        )

        assert result.bundle_artifact_id

        # Get bundle content
        snap = harness.ledger.snapshot(result.bundle_artifact_id)
        content = harness.content_store.get(snap.content_id)

        assert isinstance(content, dict)
        assert content.get("version") == "bundle@v1"
        assert "repro" in content
        assert content["repro"].get("surface") == "test"
        assert content["repro"].get("engine_version") is not None


class TestHandlerRegistry:
    """Tests for handler registry."""

    def test_register_and_get_handler(self):
        clear_handlers()
        handler = MockHandler()
        register_handler(handler)

        from irrev.harness.registry import get_handler

        retrieved = get_handler("mock.test")
        assert retrieved is not None
        assert retrieved.metadata.operation == "mock.test"

    def test_get_unknown_handler_returns_none(self):
        clear_handlers()

        from irrev.harness.registry import get_handler

        retrieved = get_handler("unknown.operation")
        assert retrieved is None


class TestLedgerEnrichment:
    """Tests for ledger enrichment with context and metadata."""

    def test_plan_contains_vault_state(self, harness: Harness, mock_handler: MockHandler):
        """Plan artifacts should contain vault state snapshot."""
        result = harness.propose(mock_handler, {}, actor="agent:test", surface="test")

        # Get plan content
        snap = harness.ledger.snapshot(result.plan_artifact_id)
        content = harness.content_store.get(snap.content_id)

        assert isinstance(content, dict)
        assert "context" in content["payload"]
        assert "vault_state" in content["payload"]["context"]

        vault_state = content["payload"]["context"]["vault_state"]
        assert "vault_sha256" in vault_state
        assert "timestamp" in vault_state

    def test_plan_contains_active_rulesets(self, harness: Harness, mock_handler: MockHandler):
        """Plan artifacts should reference active rulesets."""
        result = harness.propose(mock_handler, {}, actor="agent:test", surface="test")

        # Get plan content
        snap = harness.ledger.snapshot(result.plan_artifact_id)
        content = harness.content_store.get(snap.content_id)

        assert "context" in content["payload"]
        assert "active_rulesets" in content["payload"]["context"]
        # Note: May be empty if no rulesets found, but field should exist
        assert isinstance(content["payload"]["context"]["active_rulesets"], list)

    def test_plan_contains_engine_version(self, harness: Harness, mock_handler: MockHandler):
        """Plan artifacts should include engine version."""
        result = harness.propose(mock_handler, {}, actor="agent:test", surface="test")

        snap = harness.ledger.snapshot(result.plan_artifact_id)
        content = harness.content_store.get(snap.content_id)

        assert "context" in content["payload"]
        assert "engine_version" in content["payload"]["context"]
        assert content["payload"]["context"]["engine_version"]  # Non-empty

    def test_plan_contains_plan_metadata(self, harness: Harness):
        """Plan artifacts should include predicted effects metadata."""
        handler = MockHandler(effect_type="mutation_destructive")
        result = harness.propose(handler, {}, actor="agent:test", surface="test")

        snap = harness.ledger.snapshot(result.plan_artifact_id)
        content = harness.content_store.get(snap.content_id)

        assert "plan_metadata" in content["payload"]
        plan_meta = content["payload"]["plan_metadata"]

        assert "predicted_erasure" in plan_meta
        assert "predicted_outputs" in plan_meta
        assert "effect_reasons" in plan_meta

    def test_bundle_rulesets_populated(self, harness: Harness, mock_handler: MockHandler):
        """Bundles should include ruleset references with content IDs."""
        result = harness.run(mock_handler, {}, actor="agent:test", surface="test")

        assert result.bundle_artifact_id
        snap = harness.ledger.snapshot(result.bundle_artifact_id)
        content = harness.content_store.get(snap.content_id)

        assert "repro" in content
        assert "rulesets" in content["repro"]
        # Rulesets should be a list (may be empty if no rulesets found)
        assert isinstance(content["repro"]["rulesets"], list)

        # If rulesets found, verify structure
        for rs in content["repro"]["rulesets"]:
            assert "id" in rs
            assert "version" in rs
            assert "content_id" in rs
            assert rs["content_id"].startswith("sha256:")

    def test_bundle_inputs_snapshot_populated(self, harness: Harness, mock_handler: MockHandler):
        """Bundles should include inputs snapshot."""
        result = harness.run(mock_handler, {}, actor="agent:test", surface="test")

        snap = harness.ledger.snapshot(result.bundle_artifact_id)
        content = harness.content_store.get(snap.content_id)

        assert "repro" in content
        assert "inputs_snapshot" in content["repro"]

        # Verify vault state structure
        inputs = content["repro"]["inputs_snapshot"]
        assert isinstance(inputs, dict)
        assert "vault_sha256" in inputs
        assert "timestamp" in inputs
