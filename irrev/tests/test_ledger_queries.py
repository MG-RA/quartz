"""
Tests for Phase 5: Ledger Query API

Validates the query infrastructure, convenience methods, and derived summaries:
- Core query() method with composable filters
- Stable ordering guarantees
- Cursor-based pagination
- Governance queries (constraint_evaluations, invariant_checks)
- Execution queries (execution_logs, execution_timeline)
- Audit trail
- Derived summaries with blame attribution and explicit absence
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from irrev.artifact.events import (
    ARTIFACT_CREATED,
    ARTIFACT_VALIDATED,
    CONSTRAINT_EVALUATED,
    EXECUTION_LOGGED,
    INVARIANT_CHECKED,
    create_event,
)
from irrev.artifact.ledger import ArtifactLedger


@pytest.fixture
def ledger(tmp_path: Path) -> ArtifactLedger:
    """Create a fresh ledger for testing."""
    irrev_dir = tmp_path / ".irrev"
    return ArtifactLedger(irrev_dir)


@pytest.fixture
def populated_ledger(tmp_path: Path) -> ArtifactLedger:
    """Create a ledger with sample events for multiple artifacts."""
    irrev_dir = tmp_path / ".irrev"
    ledger = ArtifactLedger(irrev_dir)

    base_time = datetime.now(timezone.utc)

    # Artifact 1: plan with execution
    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            "art-001",
            "agent:test",
            artifact_type="plan",
            content_id="content-001",
            timestamp=base_time,
        )
    )
    ledger.append(
        create_event(
            ARTIFACT_VALIDATED,
            "art-001",
            "validator:test",
            payload={"errors": [], "computed_risk_class": "read_only"},
            timestamp=base_time + timedelta(seconds=1),
        )
    )
    ledger.append(
        create_event(
            CONSTRAINT_EVALUATED,
            "art-001",
            "validator:test",
            payload={
                "ruleset_id": "core",
                "rule_id": "rule-1",
                "invariant": "inv-1",
                "result": "pass",
                "evidence": {},
            },
            timestamp=base_time + timedelta(seconds=2),
        )
    )
    ledger.append(
        create_event(
            INVARIANT_CHECKED,
            "art-001",
            "validator:test",
            payload={
                "invariant_id": "inv-1",
                "status": "pass",
                "rules_checked": 1,
                "violations": 0,
                "affected_items": [],
            },
            timestamp=base_time + timedelta(seconds=3),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-001",
            "harness",
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "prepare",
                "status": "started",
                "handler_id": "mock.test",
            },
            timestamp=base_time + timedelta(seconds=4),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-001",
            "harness",
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "prepare",
                "status": "completed",
                "handler_id": "mock.test",
                "duration_ms": 50.0,
            },
            timestamp=base_time + timedelta(seconds=4, milliseconds=50),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-001",
            "harness",
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "execute",
                "status": "started",
                "handler_id": "mock.test",
            },
            timestamp=base_time + timedelta(seconds=5),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-001",
            "harness",
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "execute",
                "status": "completed",
                "handler_id": "mock.test",
                "duration_ms": 150.0,
                "resources": {"items_processed": 100, "bytes_written": 1024},
            },
            timestamp=base_time + timedelta(seconds=5, milliseconds=150),
        )
    )

    # Artifact 2: plan with failed execution
    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            "art-002",
            "agent:test",
            artifact_type="plan",
            content_id="content-002",
            timestamp=base_time + timedelta(seconds=10),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-002",
            "harness",
            payload={
                "execution_id": "exec-002",
                "attempt": 0,
                "phase": "execute",
                "status": "started",
                "handler_id": "mock.test",
            },
            timestamp=base_time + timedelta(seconds=11),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-002",
            "harness",
            payload={
                "execution_id": "exec-002",
                "attempt": 0,
                "phase": "execute",
                "status": "failed",
                "handler_id": "mock.test",
                "duration_ms": 75.0,
                "error_type": "RuntimeError",
                "error": "Mock execution failure",
            },
            timestamp=base_time + timedelta(seconds=11, milliseconds=75),
        )
    )

    return ledger


# -----------------------------------------------------------------------------
# Core Query Tests
# -----------------------------------------------------------------------------


def test_query_by_artifact_id_returns_all_related_events_sorted(populated_ledger: ArtifactLedger):
    """Test that query filters by artifact_id and maintains chronological order."""
    events = populated_ledger.query(artifact_id="art-001")

    # Should have 8 events for art-001
    assert len(events) == 8

    # Verify chronological order (timestamps should be increasing)
    for i in range(len(events) - 1):
        assert events[i].timestamp <= events[i + 1].timestamp

    # Verify all events are for art-001
    assert all(e.artifact_id == "art-001" for e in events)


def test_query_by_execution_id_returns_only_execution_events(populated_ledger: ArtifactLedger):
    """Test that query filters by execution_id from payload."""
    events = populated_ledger.query(execution_id="exec-001")

    # Should have 4 execution events for exec-001
    assert len(events) == 4

    # All should be execution.logged events
    assert all(e.event_type == EXECUTION_LOGGED for e in events)

    # All should have execution_id="exec-001" in payload
    assert all(e.payload.get("execution_id") == "exec-001" for e in events)


def test_query_filters_are_composable(populated_ledger: ArtifactLedger):
    """Test that multiple filters can be combined."""
    # Query for execution.logged events for art-001
    events = populated_ledger.query(
        artifact_id="art-001",
        event_type=EXECUTION_LOGGED,
    )

    assert len(events) == 4
    assert all(e.artifact_id == "art-001" for e in events)
    assert all(e.event_type == EXECUTION_LOGGED for e in events)

    # Add custom predicate to filter completed events only
    completed_events = populated_ledger.query(
        artifact_id="art-001",
        event_type=EXECUTION_LOGGED,
        where=lambda e: e.payload.get("status") == "completed",
    )

    assert len(completed_events) == 2
    assert all(e.payload.get("status") == "completed" for e in completed_events)


def test_query_stable_ordering_across_mixed_event_types(populated_ledger: ArtifactLedger):
    """Test that order="asc" maintains ledger append order across all event types."""
    events_asc = populated_ledger.query(artifact_id="art-001", order="asc")
    events_desc = populated_ledger.query(artifact_id="art-001", order="desc")

    # Ascending should match timestamps
    for i in range(len(events_asc) - 1):
        assert events_asc[i].timestamp <= events_asc[i + 1].timestamp

    # Descending should be reverse
    assert list(reversed(events_asc)) == events_desc

    # Verify mixed event types are present and ordered correctly
    event_types = [e.event_type for e in events_asc]
    assert ARTIFACT_CREATED in event_types
    assert ARTIFACT_VALIDATED in event_types
    assert CONSTRAINT_EVALUATED in event_types
    assert EXECUTION_LOGGED in event_types

    # First event should be artifact.created
    assert events_asc[0].event_type == ARTIFACT_CREATED


def test_query_after_event_id_cursor(ledger: ArtifactLedger):
    """Test that after_event_id cursor skips events until seen."""
    base_time = datetime.now(timezone.utc)

    # Create events with unique artifact_ids to use as cursors
    events_to_add = []
    for i in range(5):
        events_to_add.append(
            create_event(
                ARTIFACT_CREATED,
                f"art-{i:03d}",
                "test",
                artifact_type="plan",
                content_id=f"content-{i:03d}",
                timestamp=base_time + timedelta(seconds=i),
            )
        )

    ledger.append_many(events_to_add)

    # Query with cursor after art-002
    results = ledger.query(after_event_id="art-002")

    # Should get art-003 and art-004 (art-002 is excluded)
    assert len(results) == 2
    assert results[0].artifact_id == "art-003"
    assert results[1].artifact_id == "art-004"


def test_query_limit(populated_ledger: ArtifactLedger):
    """Test that limit parameter restricts results."""
    events = populated_ledger.query(artifact_id="art-001", limit=3)

    assert len(events) == 3


# -----------------------------------------------------------------------------
# Governance Query Tests
# -----------------------------------------------------------------------------


def test_constraint_evaluations(populated_ledger: ArtifactLedger):
    """Test constraint_evaluations() returns structured results."""
    evaluations = populated_ledger.constraint_evaluations("art-001")

    assert len(evaluations) == 1
    eval = evaluations[0]
    assert eval.artifact_id == "art-001"
    assert eval.ruleset_id == "core"
    assert eval.rule_id == "rule-1"
    assert eval.invariant == "inv-1"
    assert eval.result == "pass"


def test_invariant_checks(populated_ledger: ArtifactLedger):
    """Test invariant_checks() returns structured results."""
    checks = populated_ledger.invariant_checks("art-001")

    assert len(checks) == 1
    check = checks[0]
    assert check.artifact_id == "art-001"
    assert check.invariant_id == "inv-1"
    assert check.status == "pass"
    assert check.rules_checked == 1
    assert check.violations == 0


# -----------------------------------------------------------------------------
# Execution Query Tests
# -----------------------------------------------------------------------------


def test_execution_logs(populated_ledger: ArtifactLedger):
    """Test execution_logs() returns structured results."""
    logs = populated_ledger.execution_logs(artifact_id="art-001")

    assert len(logs) == 4

    # Verify structure
    log = logs[0]
    assert log.artifact_id == "art-001"
    assert log.execution_id == "exec-001"
    assert log.handler_id == "mock.test"
    assert log.phase in ["prepare", "execute"]


def test_execution_timeline(populated_ledger: ArtifactLedger):
    """Test execution_timeline() returns events in chronological order."""
    timeline = populated_ledger.execution_timeline("exec-001")

    assert len(timeline) == 4

    # Verify chronological order
    for i in range(len(timeline) - 1):
        assert timeline[i].timestamp <= timeline[i + 1].timestamp

    # Verify phase order
    phases = [log.phase for log in timeline]
    assert phases == ["prepare", "prepare", "execute", "execute"]


# -----------------------------------------------------------------------------
# Audit Trail Tests
# -----------------------------------------------------------------------------


def test_audit_trail_merges_governance_and_execution_events_in_time_order(
    populated_ledger: ArtifactLedger,
):
    """Test audit_trail() returns all events chronologically."""
    trail = populated_ledger.audit_trail("art-001")

    assert len(trail) == 8

    # Verify chronological order
    for i in range(len(trail) - 1):
        assert trail[i].timestamp <= trail[i + 1].timestamp

    # Verify mixed event types
    event_types = {e.event_type for e in trail}
    assert ARTIFACT_CREATED in event_types
    assert ARTIFACT_VALIDATED in event_types
    assert CONSTRAINT_EVALUATED in event_types
    assert INVARIANT_CHECKED in event_types
    assert EXECUTION_LOGGED in event_types


# -----------------------------------------------------------------------------
# Derived Summary Tests
# -----------------------------------------------------------------------------


def test_execution_summary_handles_failed_execute(populated_ledger: ArtifactLedger):
    """Test execution_summary() handles failed execution and extracts failure_phase."""
    summary = populated_ledger.execution_summary("exec-002")

    assert summary is not None
    assert summary.execution_id == "exec-002"
    assert summary.artifact_id == "art-002"
    assert summary.overall_status == "failure"
    assert summary.first_error == "Mock execution failure"
    assert summary.failure_phase == "execute"  # Blame attribution
    assert summary.attempt_count == 1


def test_execution_summary_distinguishes_prepare_vs_execute_failure(ledger: ArtifactLedger):
    """Test that failure_phase correctly identifies where failure occurred."""
    base_time = datetime.now(timezone.utc)

    # Create artifact
    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            "art-fail",
            "test",
            artifact_type="plan",
            content_id="content-fail",
            timestamp=base_time,
        )
    )

    # Fail during prepare phase
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-fail",
            "harness",
            payload={
                "execution_id": "exec-fail",
                "attempt": 0,
                "phase": "prepare",
                "status": "started",
                "handler_id": "mock.test",
            },
            timestamp=base_time + timedelta(seconds=1),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-fail",
            "harness",
            payload={
                "execution_id": "exec-fail",
                "attempt": 0,
                "phase": "prepare",
                "status": "failed",
                "handler_id": "mock.test",
                "duration_ms": 10.0,
                "error_type": "ValueError",
                "error": "Prepare phase failure",
            },
            timestamp=base_time + timedelta(seconds=1, milliseconds=10),
        )
    )

    summary = ledger.execution_summary("exec-fail")

    assert summary is not None
    assert summary.failure_phase == "prepare"  # Structural failure, not handler
    assert summary.overall_status == "failure"


def test_execution_summary_handles_skipped_commit(ledger: ArtifactLedger):
    """Test execution_summary() handles skipped phases."""
    base_time = datetime.now(timezone.utc)

    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            "art-skip",
            "test",
            artifact_type="plan",
            content_id="content-skip",
            timestamp=base_time,
        )
    )

    # Execute with skipped commit
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-skip",
            "harness",
            payload={
                "execution_id": "exec-skip",
                "attempt": 0,
                "phase": "execute",
                "status": "completed",
                "handler_id": "mock.test",
                "duration_ms": 100.0,
            },
            timestamp=base_time + timedelta(seconds=1),
        )
    )
    ledger.append(
        create_event(
            EXECUTION_LOGGED,
            "art-skip",
            "harness",
            payload={
                "execution_id": "exec-skip",
                "attempt": 0,
                "phase": "commit",
                "status": "skipped",
                "handler_id": "mock.test",
                "reason": "no_commit_needed",
            },
            timestamp=base_time + timedelta(seconds=2),
        )
    )

    summary = ledger.execution_summary("exec-skip")

    assert summary is not None
    # Skipped phases should not contribute to duration
    assert "commit" not in summary.phase_durations
    assert summary.overall_status == "success"


def test_constraint_summary_matches_validated_constraint_results(populated_ledger: ArtifactLedger):
    """Test constraint_summary() aggregates constraint evaluations."""
    summary = populated_ledger.constraint_summary("art-001")

    assert summary.artifact_id == "art-001"
    assert summary.constraint_data_status == "present"
    assert "core" in summary.rulesets_evaluated
    assert summary.total_rules_checked == 1
    assert summary.passed == 1
    assert summary.failed == 0
    assert summary.warnings == 0
    assert len(summary.violated_invariants) == 0


def test_constraint_summary_data_status_missing_for_old_artifacts(ledger: ArtifactLedger):
    """Test constraint_data_status="missing" for artifacts without constraint events."""
    base_time = datetime.now(timezone.utc)

    # Create artifact without constraint events (predates Phase 3)
    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            "art-old",
            "test",
            artifact_type="plan",
            content_id="content-old",
            timestamp=base_time,
        )
    )

    summary = ledger.constraint_summary("art-old")

    assert summary.constraint_data_status == "missing"
    assert summary.total_rules_checked == 0
    assert len(summary.rulesets_evaluated) == 0


def test_constraint_summary_data_status_present_for_new_artifacts(populated_ledger: ArtifactLedger):
    """Test constraint_data_status="present" for artifacts with full constraint data."""
    summary = populated_ledger.constraint_summary("art-001")

    assert summary.constraint_data_status == "present"


def test_constraint_summary_data_status_partial(ledger: ArtifactLedger):
    """Test constraint_data_status="partial" when only some constraint data present."""
    base_time = datetime.now(timezone.utc)

    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            "art-partial",
            "test",
            artifact_type="plan",
            content_id="content-partial",
            timestamp=base_time,
        )
    )

    # Add constraint evaluation but no invariant check
    ledger.append(
        create_event(
            CONSTRAINT_EVALUATED,
            "art-partial",
            "validator:test",
            payload={
                "ruleset_id": "core",
                "rule_id": "rule-1",
                "invariant": "inv-1",
                "result": "pass",
                "evidence": {},
            },
            timestamp=base_time + timedelta(seconds=1),
        )
    )

    summary = ledger.constraint_summary("art-partial")

    assert summary.constraint_data_status == "partial"


# -----------------------------------------------------------------------------
# Index Consistency Tests
# -----------------------------------------------------------------------------


def test_indexes_updated_on_append(ledger: ArtifactLedger):
    """Test that indexes are updated when appending events."""
    base_time = datetime.now(timezone.utc)

    # Trigger index build
    ledger._ensure_indexed()
    assert ledger._indexed

    # Append new event
    event = create_event(
        ARTIFACT_CREATED,
        "art-new",
        "test",
        artifact_type="plan",
        content_id="content-new",
        timestamp=base_time,
    )
    ledger.append(event)

    # Verify index updated
    assert "art-new" in ledger._by_artifact_id
    assert ARTIFACT_CREATED in ledger._by_event_type

    # Query should find the new event
    events = ledger.query(artifact_id="art-new")
    assert len(events) == 1


def test_indexes_updated_on_append_many(ledger: ArtifactLedger):
    """Test that indexes are updated when appending multiple events."""
    base_time = datetime.now(timezone.utc)

    # Trigger index build
    ledger._ensure_indexed()
    assert ledger._indexed

    # Append multiple events
    events = [
        create_event(
            ARTIFACT_CREATED,
            f"art-{i}",
            "test",
            artifact_type="plan",
            content_id=f"content-{i}",
            timestamp=base_time + timedelta(seconds=i),
        )
        for i in range(3)
    ]
    ledger.append_many(events)

    # Verify indexes updated
    for i in range(3):
        assert f"art-{i}" in ledger._by_artifact_id

    # Query should find all events
    results = ledger.query(event_type=ARTIFACT_CREATED)
    assert len(results) == 3
