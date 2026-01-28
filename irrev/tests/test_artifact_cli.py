"""
Tests for Phase 6 artifact CLI commands.

Tests the user-facing CLI commands that format Phase 5 query API results.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from irrev.artifact.content_store import ContentStore
from irrev.artifact.events import (
    ARTIFACT_APPROVED,
    ARTIFACT_CREATED,
    ARTIFACT_EXECUTED,
    ARTIFACT_VALIDATED,
    CONSTRAINT_EVALUATED,
    EXECUTION_LOGGED,
    INVARIANT_CHECKED,
    create_event,
)
from irrev.artifact.ledger import ArtifactLedger
from irrev.artifact.plan_manager import PlanManager
from irrev.commands.artifact_cmd import (
    run_artifact_audit,
    run_artifact_constraints,
    run_artifact_execution,
    run_artifact_summary,
    run_artifact_timeline,
)


@pytest.fixture
def vault_with_populated_ledger(tmp_path: Path) -> Path:
    """Create a vault with a full lifecycle artifact including governance and execution events."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir(parents=True)
    irrev_dir = tmp_path / ".irrev"
    irrev_dir.mkdir(parents=True)

    ledger = ArtifactLedger(irrev_dir)
    content_store = ContentStore(irrev_dir)

    # Create artifact content
    plan_content = {
        "operation": "create_note",
        "payload": {"path": "test.md", "content": "Hello"},
    }
    content_id = content_store.store(plan_content)

    artifact_id = "plan-test001"
    now = datetime.now(timezone.utc)

    # Full lifecycle events
    events = [
        # Created
        create_event(
            ARTIFACT_CREATED,
            artifact_id,
            "agent:planner",
            timestamp=now,
            content_id=content_id,
            artifact_type="plan",
            payload={
                "status": "created",
                "artifact_type": "plan",
                "operation": "create_note",
            },
        ),
        # Constraint evaluation
        create_event(
            CONSTRAINT_EVALUATED,
            artifact_id,
            "system",
            timestamp=now + timedelta(seconds=1),
            payload={
                "ruleset_id": "core",
                "rule_id": "no_destructive",
                "invariant": "no_erasure",
                "result": "pass",
                "evidence": {"message": "operation is safe"},
            },
        ),
        # Invariant check
        create_event(
            INVARIANT_CHECKED,
            artifact_id,
            "system",
            timestamp=now + timedelta(seconds=2),
            payload={
                "invariant_id": "content_exists",
                "status": "pass",
                "rules_checked": 1,
                "violations": 0,
                "affected_items": [],
            },
        ),
        # Validated
        create_event(
            ARTIFACT_VALIDATED,
            artifact_id,
            "system",
            timestamp=now + timedelta(seconds=3),
            payload={
                "validator": "constraint_engine",
                "errors": [],
            },
        ),
        # Approved
        create_event(
            ARTIFACT_APPROVED,
            artifact_id,
            "human:alice",
            timestamp=now + timedelta(minutes=5),
            payload={
                "approval_artifact_id": "approval-001",
                "scope": "test approval",
            },
        ),
        # Execution: prepare phase
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:vault.mutation",
            timestamp=now + timedelta(minutes=10),
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "prepare",
                "status": "started",
                "handler_id": "vault.mutation",
                "started_at": (now + timedelta(minutes=10)).isoformat(),
            },
        ),
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:vault.mutation",
            timestamp=now + timedelta(minutes=10, milliseconds=500),
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "prepare",
                "status": "completed",
                "handler_id": "vault.mutation",
                "started_at": (now + timedelta(minutes=10)).isoformat(),
                "ended_at": (now + timedelta(minutes=10, milliseconds=500)).isoformat(),
                "duration_ms": 500,
                "resources": {"cpu_percent": 10, "memory_mb": 50},
            },
        ),
        # Execution: execute phase
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:vault.mutation",
            timestamp=now + timedelta(minutes=10, milliseconds=500),
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "execute",
                "status": "started",
                "handler_id": "vault.mutation",
                "started_at": (now + timedelta(minutes=10, milliseconds=500)).isoformat(),
            },
        ),
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:vault.mutation",
            timestamp=now + timedelta(minutes=10, seconds=3),
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "execute",
                "status": "completed",
                "handler_id": "vault.mutation",
                "started_at": (now + timedelta(minutes=10, milliseconds=500)).isoformat(),
                "ended_at": (now + timedelta(minutes=10, seconds=3)).isoformat(),
                "duration_ms": 2500,
                "resources": {"cpu_percent": 25, "memory_mb": 100},
            },
        ),
        # Execution: commit phase
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:vault.mutation",
            timestamp=now + timedelta(minutes=10, seconds=3),
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "commit",
                "status": "started",
                "handler_id": "vault.mutation",
                "started_at": (now + timedelta(minutes=10, seconds=3)).isoformat(),
            },
        ),
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:vault.mutation",
            timestamp=now + timedelta(minutes=10, seconds=3, milliseconds=200),
            payload={
                "execution_id": "exec-001",
                "attempt": 0,
                "phase": "commit",
                "status": "completed",
                "handler_id": "vault.mutation",
                "started_at": (now + timedelta(minutes=10, seconds=3)).isoformat(),
                "ended_at": (now + timedelta(minutes=10, seconds=3, milliseconds=200)).isoformat(),
                "duration_ms": 200,
                "resources": {"cpu_percent": 5, "memory_mb": 20},
            },
        ),
        # Executed
        create_event(
            ARTIFACT_EXECUTED,
            artifact_id,
            "handler:vault.mutation",
            timestamp=now + timedelta(minutes=10, seconds=4),
            payload={
                "executor": "vault.mutation",
                "result_artifact_id": "report-001",
            },
        ),
    ]

    ledger.append_many(events)
    return vault_path


def test_artifact_audit_success(vault_with_populated_ledger: Path, capsys) -> None:
    """Test audit command shows all events in chronological order."""
    result = run_artifact_audit(vault_with_populated_ledger, "plan-test001", output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    # Check for key substrings (not full table matching)
    assert "Audit Trail: plan-test001" in output
    assert "artifact.created" in output
    assert "constraint.evaluated" in output
    assert "invariant.checked" in output
    assert "artifact.validated" in output
    assert "artifact.approved" in output
    assert "execution.logged" in output
    assert "artifact.executed" in output
    assert "Events: 12 total" in output


def test_artifact_audit_json_output(vault_with_populated_ledger: Path, capsys) -> None:
    """Test audit command with --json flag."""
    result = run_artifact_audit(vault_with_populated_ledger, "plan-test001", output_json=True)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    # Parse JSON
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 12
    assert all("event_type" in event for event in data)
    assert all("artifact_id" in event for event in data)
    assert all("timestamp" in event for event in data)
    assert data[0]["event_type"] == "artifact.created"
    assert data[-1]["event_type"] == "artifact.executed"


def test_artifact_audit_with_limit(vault_with_populated_ledger: Path, capsys) -> None:
    """Test audit command with --limit option."""
    result = run_artifact_audit(vault_with_populated_ledger, "plan-test001", output_json=False, limit=5)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Events: 5 total" in output


def test_artifact_audit_not_found(vault_with_populated_ledger: Path, capsys) -> None:
    """Test audit command with invalid artifact_id."""
    result = run_artifact_audit(vault_with_populated_ledger, "plan-invalid", output_json=False)

    assert result == 1
    captured = capsys.readouterr()
    # Error goes to stderr
    assert "Artifact not found: plan-invalid" in captured.err


def test_artifact_execution_success(vault_with_populated_ledger: Path, capsys) -> None:
    """Test execution command shows execution logs."""
    result = run_artifact_execution(vault_with_populated_ledger, "plan-test001", output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Execution Logs: plan-test001" in output
    assert "exec-001" in output
    assert "prepare" in output
    assert "execute" in output
    assert "commit" in output
    # Check handler is present (might be truncated)
    assert "vault" in output
    # Check status mapping
    assert "success" in output or "completed" in output
    assert "Executions: 6 total" in output  # 6 execution.logged events


def test_artifact_execution_json_output(vault_with_populated_ledger: Path, capsys) -> None:
    """Test execution command with --json flag."""
    result = run_artifact_execution(vault_with_populated_ledger, "plan-test001", output_json=True)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 6
    assert all("execution_id" in log for log in data)
    assert all("phase" in log for log in data)
    assert all("status" in log for log in data)


def test_artifact_execution_with_filters(vault_with_populated_ledger: Path, capsys) -> None:
    """Test execution command with phase and status filters."""
    result = run_artifact_execution(
        vault_with_populated_ledger,
        "plan-test001",
        phase="execute",
        status="completed",
        output_json=False,
    )

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "execute" in output
    # Should only show 1 log (execute phase completed)
    assert "Executions: 1 total" in output


def test_artifact_constraints_success(vault_with_populated_ledger: Path, capsys) -> None:
    """Test constraints command shows evaluations and checks."""
    result = run_artifact_constraints(vault_with_populated_ledger, "plan-test001", output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Constraint Evaluations" in output
    assert "Invariant Checks" in output
    assert "core" in output  # ruleset_id
    assert "no_erasure" in output  # invariant
    assert "content_exists" in output  # invariant_id
    assert "Summary:" in output


def test_artifact_constraints_json_output(vault_with_populated_ledger: Path, capsys) -> None:
    """Test constraints command with --json flag."""
    result = run_artifact_constraints(vault_with_populated_ledger, "plan-test001", output_json=True)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    data = json.loads(output)
    assert "constraint_data_status" in data
    assert data["constraint_data_status"] == "present"
    assert "evaluations" in data
    assert "checks" in data
    assert isinstance(data["evaluations"], list)
    assert isinstance(data["checks"], list)


def test_artifact_constraints_missing_data(tmp_path: Path, capsys) -> None:
    """Test constraints command with artifact predating Phase 3."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir(parents=True)
    irrev_dir = tmp_path / ".irrev"
    irrev_dir.mkdir(parents=True)

    ledger = ArtifactLedger(irrev_dir)
    content_store = ContentStore(irrev_dir)

    # Create artifact without constraint data
    content_id = content_store.store({"operation": "test"})
    artifact_id = "plan-old"
    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            artifact_id,
            "system",
            content_id=content_id,
            artifact_type="plan",
            payload={"status": "created"},
        )
    )

    result = run_artifact_constraints(vault_path, artifact_id, output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "No constraint data (artifact predates Phase 3)" in output


def test_artifact_timeline_success(vault_with_populated_ledger: Path, capsys) -> None:
    """Test timeline command shows condensed view."""
    result = run_artifact_timeline(vault_with_populated_ledger, "plan-test001", output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Timeline: plan-test001" in output
    # Check for symbols
    assert "●" in output or "✓" in output or "▸" in output
    # Check for condensed event types
    assert "created" in output or "validated" in output or "approved" in output
    assert "Status: executed" in output
    assert "Events: 12" in output


def test_artifact_timeline_full_timestamps(vault_with_populated_ledger: Path, capsys) -> None:
    """Test timeline command with --full flag."""
    result = run_artifact_timeline(vault_with_populated_ledger, "plan-test001", full=True, output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    # Full timestamps should include date
    assert "2026-" in output or "2025-" in output or "2024-" in output


def test_artifact_summary_success(vault_with_populated_ledger: Path, capsys) -> None:
    """Test summary command shows combined view."""
    result = run_artifact_summary(vault_with_populated_ledger, "plan-test001", output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Summary: plan-test001" in output
    assert "Execution Summary" in output
    assert "Constraint Summary" in output
    assert "Lifecycle" in output
    assert "exec-001" in output
    assert "vault.mutation" in output
    # Check status mapping
    assert "success" in output or "completed" in output


def test_artifact_summary_json_output(vault_with_populated_ledger: Path, capsys) -> None:
    """Test summary command with --json flag."""
    result = run_artifact_summary(vault_with_populated_ledger, "plan-test001", output_json=True)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    data = json.loads(output)
    assert "artifact_id" in data
    assert "snapshot" in data
    assert "execution_summary" in data
    assert "constraint_summary" in data
    assert "invariant_summary" in data
    assert data["execution_summary"] is not None
    assert data["constraint_summary"]["constraint_data_status"] == "present"


def test_artifact_summary_with_failure(tmp_path: Path, capsys) -> None:
    """Test summary command with failed execution."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir(parents=True)
    irrev_dir = tmp_path / ".irrev"
    irrev_dir.mkdir(parents=True)

    ledger = ArtifactLedger(irrev_dir)
    content_store = ContentStore(irrev_dir)

    content_id = content_store.store({"operation": "test"})
    artifact_id = "plan-fail"
    now = datetime.now(timezone.utc)

    events = [
        create_event(
            ARTIFACT_CREATED,
            artifact_id,
            "system",
            timestamp=now,
            content_id=content_id,
            artifact_type="plan",
            payload={"status": "created"},
        ),
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:test",
            timestamp=now + timedelta(seconds=1),
            payload={
                "execution_id": "exec-fail",
                "attempt": 0,
                "phase": "execute",
                "status": "started",
                "handler_id": "test",
                "started_at": (now + timedelta(seconds=1)).isoformat(),
            },
        ),
        create_event(
            EXECUTION_LOGGED,
            artifact_id,
            "handler:test",
            timestamp=now + timedelta(seconds=2),
            payload={
                "execution_id": "exec-fail",
                "attempt": 0,
                "phase": "execute",
                "status": "failed",
                "handler_id": "test",
                "started_at": (now + timedelta(seconds=1)).isoformat(),
                "ended_at": (now + timedelta(seconds=2)).isoformat(),
                "duration_ms": 1000,
                "error_type": "RuntimeError",
                "error": "Something went wrong",
            },
        ),
    ]

    ledger.append_many(events)

    result = run_artifact_summary(vault_path, artifact_id, output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    # Should show failure prominently
    assert "failure" in output or "failed" in output
    assert "execute" in output  # failure_phase


def test_artifact_summary_no_execution(tmp_path: Path, capsys) -> None:
    """Test summary command with artifact that hasn't been executed."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir(parents=True)
    irrev_dir = tmp_path / ".irrev"
    irrev_dir.mkdir(parents=True)

    ledger = ArtifactLedger(irrev_dir)
    content_store = ContentStore(irrev_dir)

    content_id = content_store.store({"operation": "test"})
    artifact_id = "plan-no-exec"
    ledger.append(
        create_event(
            ARTIFACT_CREATED,
            artifact_id,
            "system",
            content_id=content_id,
            artifact_type="plan",
            payload={"status": "created"},
        )
    )

    result = run_artifact_summary(vault_path, artifact_id, output_json=False)

    assert result == 0
    captured = capsys.readouterr()
    output = captured.out

    # Should still show constraint and lifecycle summaries
    assert "Summary: plan-no-exec" in output
    assert "Constraint Summary" in output
    assert "Lifecycle" in output
