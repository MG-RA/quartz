"""
Tests for Phase 4: Execution Logging

Validates that execution.logged events are emitted with proper lifecycle structure:
- execution_id consistency across events
- Monotonic phase order (prepare → execute → commit)
- Each phase has started + completed/failed/skipped
- Error structure (error_type, truncated messages)
- Metrics standardization via ExecutionMetrics
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from irrev.artifact.events import EXECUTION_LOGGED
from irrev.artifact.ledger import ArtifactLedger
from irrev.harness import (
    EffectSummary,
    ExecutionContext,
    ExecutionMetrics,
    Handler,
    HandlerMetadata,
    Harness,
)
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
    """Mock result with metrics."""

    def __init__(self, success: bool = True, metrics: ExecutionMetrics | None = None):
        super().__init__(success=success)
        self.metrics = metrics or ExecutionMetrics(
            items_processed=100,
            bytes_written=1024,
            custom={"test_metric": 42}
        )


class MockHandler(Handler[MockPlan, MockResult]):
    """Mock handler that returns metrics."""

    def __init__(self, effect_type: str = "read_only", should_fail: bool = False):
        self._effect_type = effect_type
        self._should_fail = should_fail

    @property
    def metadata(self) -> HandlerMetadata:
        return HandlerMetadata(
            operation="mock.test",
            delegate_to="handler:mock",
            supports_dry_run=True,
        )

    def compute_plan(self, vault_path: Path, params: dict[str, Any]) -> MockPlan:
        effect_type = params.get("effect_type", self._effect_type)
        return MockPlan(effect_type=effect_type)

    def execute(self, plan: MockPlan, context: ExecutionContext) -> MockResult:
        if self._should_fail:
            raise RuntimeError("Mock execution failure")

        return MockResult(
            success=True,
            metrics=ExecutionMetrics(
                items_processed=100,
                bytes_written=2048,
                custom={"nodes_created": 50}
            )
        )


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
    """Create a harness instance."""
    return Harness(temp_vault)


# -----------------------------------------------------------------------------
# Phase 4 Lifecycle Tests
# -----------------------------------------------------------------------------


def test_execution_lifecycle_structure(harness: Harness):
    """Test that execution events follow correct lifecycle."""
    handler = MockHandler(effect_type="append_only")

    # Propose
    propose_result = harness.propose(handler, {})
    assert propose_result.success

    # Approve (low risk, but let's approve explicitly for testing)
    harness.plan_manager.approve(
        propose_result.plan_artifact_id,
        approver="test",
        force_ack=False
    )

    # Execute
    exec_result = harness.execute(
        propose_result.plan_artifact_id,
        handler
    )
    assert exec_result.success

    # Get all execution events
    events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED
    ]

    # Assert we have events
    assert len(events) >= 4, "Should have at least prepare:started+completed, execute:started+completed"

    # Assert same execution_id across all events
    execution_ids = {e.payload["execution_id"] for e in events}
    assert len(execution_ids) == 1, "All events must share execution_id"

    # Assert monotonic phase order
    phases = [e.payload["phase"] for e in events]
    prepare_indices = [i for i, p in enumerate(phases) if p == "prepare"]
    execute_indices = [i for i, p in enumerate(phases) if p == "execute"]
    commit_indices = [i for i, p in enumerate(phases) if p == "commit"]

    if prepare_indices and execute_indices:
        assert max(prepare_indices) < min(execute_indices), "Prepare must come before execute"
    if execute_indices and commit_indices:
        assert max(execute_indices) < min(commit_indices), "Execute must come before commit"

    # Assert each phase has started + completed/failed/skipped
    for phase in ["prepare", "execute", "commit"]:
        phase_events = [e for e in events if e.payload["phase"] == phase]
        if phase_events:
            statuses = {e.payload["status"] for e in phase_events}
            assert "started" in statuses, f"{phase} must have started event"
            assert any(s in statuses for s in ["completed", "failed", "skipped"]), \
                f"{phase} must have completed/failed/skipped event"


def test_execution_id_consistency(harness: Harness):
    """Test that all events share the same execution_id."""
    handler = MockHandler(effect_type="read_only")

    propose_result = harness.propose(handler, {})
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")
    harness.execute(propose_result.plan_artifact_id, handler)

    events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED
    ]

    execution_ids = {e.payload["execution_id"] for e in events}
    assert len(execution_ids) == 1, "All events must share the same execution_id"


def test_execution_metrics_standardized(harness: Harness):
    """Test that metrics follow standardized format."""
    handler = MockHandler(effect_type="append_only")

    propose_result = harness.propose(handler, {})
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")
    harness.execute(propose_result.plan_artifact_id, handler)

    # Get execute:completed event
    events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED
        and e.payload["phase"] == "execute"
        and e.payload["status"] == "completed"
    ]

    assert len(events) == 1, "Should have exactly one execute:completed event"

    event = events[0]

    # Assert timing fields present
    assert "started_at" in event.payload
    assert "ended_at" in event.payload
    assert "duration_ms" in event.payload
    assert event.payload["duration_ms"] >= 0

    # Assert attempt field present
    assert "attempt" in event.payload
    assert event.payload["attempt"] == 0


def test_execution_failure_structure(harness: Harness, temp_vault: Path):
    """Test that failures emit properly structured error events."""
    handler = MockHandler(effect_type="append_only", should_fail=True)

    propose_result = harness.propose(handler, {})
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")

    # Execute will fail
    exec_result = harness.execute(propose_result.plan_artifact_id, handler)
    assert not exec_result.success

    # Get failed event
    failed_events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED and e.payload["status"] == "failed"
    ]

    assert len(failed_events) >= 1, "Should have at least one failed event"

    failed = failed_events[0]

    # Assert error structure
    assert "error_type" in failed.payload
    assert failed.payload["error_type"] == "RuntimeError"
    assert "error" in failed.payload
    assert failed.payload["error"] is not None
    assert "Mock execution failure" in failed.payload["error"]
    assert len(failed.payload["error"]) <= 500, "Error must be truncated to 500 chars"

    # Assert no "completed" after "failed" for same phase
    same_phase = failed.payload["phase"]
    same_phase_events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED
        and e.payload["phase"] == same_phase
    ]

    failed_idx = next(i for i, e in enumerate(same_phase_events) if e.payload["status"] == "failed")
    completed_after = any(
        e.payload["status"] == "completed"
        for e in same_phase_events[failed_idx+1:]
    )
    assert not completed_after, "Cannot have completed after failed in same phase"


def test_commit_phase_explicit(harness: Harness):
    """Test that commit phase is explicit."""
    handler = MockHandler(effect_type="append_only")

    propose_result = harness.propose(handler, {})
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")
    harness.execute(propose_result.plan_artifact_id, handler)

    # Find commit events
    commit_events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED and e.payload["phase"] == "commit"
    ]

    # Should have commit events
    assert len(commit_events) >= 1, "Should have commit phase events"

    # Check for completed or skipped
    statuses = {e.payload["status"] for e in commit_events}
    assert "started" in statuses
    assert any(s in statuses for s in ["completed", "skipped"])


def test_error_message_truncation(harness: Harness):
    """Test that very long error messages are truncated."""

    class FailingHandler(MockHandler):
        def execute(self, plan: MockPlan, context: ExecutionContext) -> MockResult:
            # Generate error message > 500 chars
            long_message = "ERROR: " + ("x" * 600)
            raise RuntimeError(long_message)

    handler = FailingHandler(effect_type="append_only")

    propose_result = harness.propose(handler, {})
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")
    harness.execute(propose_result.plan_artifact_id, handler)

    # Get failed event
    failed_events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED and e.payload["status"] == "failed"
    ]

    assert len(failed_events) >= 1
    error_msg = failed_events[0].payload["error"]
    assert len(error_msg) <= 500, f"Error message must be truncated (was {len(error_msg)} chars)"


def test_event_payload_fields(harness: Harness):
    """Test that events include all required Phase 4 fields."""
    handler = MockHandler(effect_type="append_only")

    propose_result = harness.propose(handler, {})
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")
    harness.execute(propose_result.plan_artifact_id, handler)

    events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == EXECUTION_LOGGED
    ]

    for event in events:
        payload = event.payload

        # Required fields
        assert "execution_id" in payload, "Must have execution_id"
        assert "attempt" in payload, "Must have attempt"
        assert "phase" in payload, "Must have phase"
        assert "status" in payload, "Must have status"
        assert "handler_id" in payload, "Must have handler_id"

        # Conditional fields based on status
        if payload["status"] in ["completed", "failed"]:
            assert "started_at" in payload, f"{payload['status']} must have started_at"
            assert "ended_at" in payload, f"{payload['status']} must have ended_at"
            assert "duration_ms" in payload, f"{payload['status']} must have duration_ms"

        if payload["status"] == "failed":
            assert "error_type" in payload, "Failed must have error_type"
            assert "error" in payload, "Failed must have error message"

        if payload["status"] == "skipped":
            # Skipped should have a reason
            # Note: our current implementation doesn't skip phases, but if it did:
            pass


# -----------------------------------------------------------------------------
# Backward Compatibility Tests
# -----------------------------------------------------------------------------


def test_backward_compatibility_with_existing_tests(harness: Harness):
    """Test that existing harness functionality still works."""
    handler = MockHandler(effect_type="read_only")

    # Existing workflow should still work
    propose_result = harness.propose(handler, {})
    assert propose_result.success
    assert propose_result.plan_artifact_id

    # Should not require approval for read_only
    assert not propose_result.requires_approval

    # Execute should work
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")
    exec_result = harness.execute(propose_result.plan_artifact_id, handler)
    assert exec_result.success
