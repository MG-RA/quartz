"""
Append-only artifact event ledger.

The ledger is the source of truth for all artifact state. It contains
only ArtifactEvent entries, written once and never modified. Current
state is computed by projecting events into snapshots.

Per the Irreversibility invariant: "Persistence must be tracked;
erasure costs must be declared; rollback cannot be assumed."
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator, Literal, Sequence

from .events import ArtifactEvent
from .snapshot import ArtifactSnapshot, fold_events, project_artifact


# -----------------------------------------------------------------------------
# Typed Query Result Classes
# -----------------------------------------------------------------------------


@dataclass
class ConstraintEvaluation:
    """Structured view of constraint.evaluated event."""

    artifact_id: str
    timestamp: datetime
    ruleset_id: str
    rule_id: str
    invariant: str
    result: str  # "pass" | "fail" | "warning"
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "artifact_id": self.artifact_id,
            "timestamp": self.timestamp.isoformat(),
            "ruleset_id": self.ruleset_id,
            "rule_id": self.rule_id,
            "invariant": self.invariant,
            "result": self.result,
            "evidence": self.evidence,
        }


@dataclass
class InvariantCheck:
    """Structured view of invariant.checked event."""

    artifact_id: str
    timestamp: datetime
    invariant_id: str
    status: str  # "pass" | "fail"
    rules_checked: int
    violations: int
    affected_items: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "artifact_id": self.artifact_id,
            "timestamp": self.timestamp.isoformat(),
            "invariant_id": self.invariant_id,
            "status": self.status,
            "rules_checked": self.rules_checked,
            "violations": self.violations,
            "affected_items": self.affected_items,
        }


@dataclass
class ExecutionLog:
    """Structured view of execution.logged event."""

    artifact_id: str
    timestamp: datetime
    execution_id: str
    attempt: int
    phase: str
    status: str
    handler_id: str
    duration_ms: float | None = None
    resources: dict[str, Any] | None = None
    error_type: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        result: dict[str, Any] = {
            "artifact_id": self.artifact_id,
            "timestamp": self.timestamp.isoformat(),
            "execution_id": self.execution_id,
            "attempt": self.attempt,
            "phase": self.phase,
            "status": self.status,
            "handler_id": self.handler_id,
        }
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.resources is not None:
            result["resources"] = self.resources
        if self.error_type is not None:
            result["error_type"] = self.error_type
        if self.error is not None:
            result["error"] = self.error
        return result


# -----------------------------------------------------------------------------
# Derived Summary Classes
# -----------------------------------------------------------------------------


@dataclass
class ExecutionSummary:
    """
    Derived summary of execution events for a single execution_id.

    Computed from execution.logged events, not stored.
    """

    execution_id: str
    artifact_id: str
    handler_id: str
    overall_status: str  # "success" | "failure" | "partial"
    phase_durations: dict[str, float]  # {"prepare": 50.2, "execute": 150.7}
    attempt_count: int
    total_duration_ms: float
    resources: dict[str, Any]  # Merged metrics across phases
    first_error: str | None  # First error encountered (if any)
    failure_phase: str | None  # "prepare" | "execute" | "commit" - where failure occurred
    plan_step_ids: list[str]  # All steps executed
    started_at: datetime
    ended_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        result: dict[str, Any] = {
            "execution_id": self.execution_id,
            "artifact_id": self.artifact_id,
            "handler_id": self.handler_id,
            "overall_status": self.overall_status,
            "phase_durations": self.phase_durations,
            "attempt_count": self.attempt_count,
            "total_duration_ms": self.total_duration_ms,
            "resources": self.resources,
            "plan_step_ids": self.plan_step_ids,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
        }
        if self.first_error is not None:
            result["first_error"] = self.first_error
        if self.failure_phase is not None:
            result["failure_phase"] = self.failure_phase
        return result


@dataclass
class ConstraintSummary:
    """
    Derived summary of constraint evaluation events.

    Computed from constraint.evaluated + invariant.checked events, not stored.
    """

    artifact_id: str
    constraint_data_status: str  # "present" | "missing" | "partial"
    rulesets_evaluated: list[str]
    total_rules_checked: int
    passed: int
    failed: int
    warnings: int
    violated_invariants: list[str]
    evaluation_time: datetime | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        result: dict[str, Any] = {
            "artifact_id": self.artifact_id,
            "constraint_data_status": self.constraint_data_status,
            "rulesets_evaluated": self.rulesets_evaluated,
            "total_rules_checked": self.total_rules_checked,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "violated_invariants": self.violated_invariants,
        }
        if self.evaluation_time is not None:
            result["evaluation_time"] = self.evaluation_time.isoformat()
        return result


@dataclass
class InvariantSummary:
    """
    Derived summary of invariant check events.

    Computed from invariant.checked events, not stored.
    """

    artifact_id: str
    invariants_checked: list[str]
    violations: dict[str, list[str]]  # invariant_id -> affected_items
    overall_status: str  # "pass" | "fail"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "artifact_id": self.artifact_id,
            "invariants_checked": self.invariants_checked,
            "violations": self.violations,
            "overall_status": self.overall_status,
        }


class ArtifactLedger:
    """
    Append-only event ledger for artifacts.

    INVARIANT: This class NEVER modifies existing ledger lines.
    The only write operation is append().
    """

    def __init__(self, irrev_dir: Path):
        """
        Initialize ledger.

        Args:
            irrev_dir: Path to .irrev directory
        """
        self.irrev_dir = irrev_dir
        self.ledger_path = irrev_dir / "artifact.jsonl"

        # Query indexes (lazy-loaded)
        self._events: list[ArtifactEvent] = []  # Cache of loaded events
        self._by_artifact_id: dict[str, list[int]] = {}  # artifact_id -> event indices
        self._by_execution_id: dict[str, list[int]] = {}  # execution_id -> event indices
        self._by_event_type: dict[str, list[int]] = {}  # event_type -> event indices
        self._indexed: bool = False  # Whether indexes have been built

    def _ensure_dir(self) -> None:
        """Ensure .irrev directory exists."""
        self.irrev_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_indexed(self) -> None:
        """
        Build indexes on first use (lazy loading).

        This method is idempotent - calling it multiple times is safe.
        """
        if self._indexed:
            return

        # Load all events into cache
        self._events = list(self.iter_events())

        # Build indexes
        for idx, event in enumerate(self._events):
            # Index by artifact_id
            self._by_artifact_id.setdefault(event.artifact_id, []).append(idx)

            # Index by event_type
            self._by_event_type.setdefault(event.event_type, []).append(idx)

            # Index by execution_id (if present in payload)
            if event.event_type == "execution.logged":
                execution_id = event.payload.get("execution_id")
                if execution_id:
                    self._by_execution_id.setdefault(execution_id, []).append(idx)

        self._indexed = True

    def _update_indexes(self, event: ArtifactEvent, idx: int) -> None:
        """
        Update indexes for a newly appended event.

        Args:
            event: The event that was appended
            idx: The index of the event in self._events
        """
        # Index by artifact_id
        self._by_artifact_id.setdefault(event.artifact_id, []).append(idx)

        # Index by event_type
        self._by_event_type.setdefault(event.event_type, []).append(idx)

        # Index by execution_id (if present in payload)
        if event.event_type == "execution.logged":
            execution_id = event.payload.get("execution_id")
            if execution_id:
                self._by_execution_id.setdefault(execution_id, []).append(idx)

    def append(self, event: ArtifactEvent) -> None:
        """
        Append an event to the ledger.

        This is the ONLY write operation. Events are never modified
        or deleted once written.

        Args:
            event: The event to append
        """
        self._ensure_dir()
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")

        # Update indexes if already built
        if self._indexed:
            idx = len(self._events)
            self._events.append(event)
            self._update_indexes(event, idx)

    def append_many(self, events: Sequence[ArtifactEvent]) -> None:
        """
        Append multiple events atomically.

        All events are written in a single file operation.
        """
        if not events:
            return
        self._ensure_dir()
        with self.ledger_path.open("a", encoding="utf-8") as f:
            for event in events:
                f.write(event.to_json() + "\n")

        # Update indexes if already built
        if self._indexed:
            start_idx = len(self._events)
            for i, event in enumerate(events):
                self._events.append(event)
                self._update_indexes(event, start_idx + i)

    def iter_events(self) -> Iterator[ArtifactEvent]:
        """
        Iterate over all events in the ledger.

        Events are returned in chronological order (append order).
        """
        if not self.ledger_path.exists():
            return

        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield ArtifactEvent.from_json(line)

    def query(
        self,
        *,
        artifact_id: str | None = None,
        execution_id: str | None = None,
        event_type: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        actor: str | None = None,
        where: Callable[[ArtifactEvent], bool] | None = None,
        limit: int | None = None,
        order: Literal["asc", "desc"] = "asc",
        after_event_id: str | None = None,
    ) -> list[ArtifactEvent]:
        """
        Query events with composable filters.

        This is the core query primitive - all convenience methods compile to this.

        Args:
            artifact_id: Filter by artifact ID
            execution_id: Filter by execution ID (from execution.logged payload)
            event_type: Filter by event type
            since: Filter events on or after this timestamp
            until: Filter events on or before this timestamp
            actor: Filter by actor
            where: Custom filter predicate
            limit: Maximum number of events to return
            order: Sort order ("asc" = chronological/append order, "desc" = reverse)
            after_event_id: Cursor for pagination (skip until this event_id seen)

        Returns:
            List of matching events in specified order

        Notes:
            - Default order="asc" guarantees ledger append order (chronological)
            - Uses indexes when possible for fast lookups
            - after_event_id enables pagination without API changes
        """
        # Ensure indexes are built
        self._ensure_indexed()

        # Use indexes for fast lookups when possible
        candidate_indices: set[int] | None = None

        if artifact_id is not None:
            indices = set(self._by_artifact_id.get(artifact_id, []))
            candidate_indices = indices if candidate_indices is None else candidate_indices & indices

        if execution_id is not None:
            indices = set(self._by_execution_id.get(execution_id, []))
            candidate_indices = indices if candidate_indices is None else candidate_indices & indices

        if event_type is not None:
            indices = set(self._by_event_type.get(event_type, []))
            candidate_indices = indices if candidate_indices is None else candidate_indices & indices

        # If no index filters, use all events
        if candidate_indices is None:
            candidate_indices = set(range(len(self._events)))

        # Convert to sorted list (maintains append order)
        sorted_indices = sorted(candidate_indices)

        # Apply remaining filters
        results: list[ArtifactEvent] = []
        cursor_passed = after_event_id is None

        for idx in sorted_indices:
            event = self._events[idx]

            # Handle cursor (skip until after_event_id seen)
            if not cursor_passed:
                if event.artifact_id == after_event_id:
                    cursor_passed = True
                continue

            # Apply timestamp filters
            if since is not None and event.timestamp < since:
                continue
            if until is not None and event.timestamp > until:
                continue

            # Apply actor filter
            if actor is not None and event.actor != actor:
                continue

            # Apply custom predicate
            if where is not None and not where(event):
                continue

            results.append(event)

            # Apply limit
            if limit is not None and len(results) >= limit:
                break

        # Apply ordering
        if order == "desc":
            results.reverse()

        return results

    def events_for(self, artifact_id: str) -> list[ArtifactEvent]:
        """
        Get all events for a specific artifact.

        Args:
            artifact_id: The artifact to get events for

        Returns:
            List of events in chronological order
        """
        return [e for e in self.iter_events() if e.artifact_id == artifact_id]

    def snapshot(self, artifact_id: str) -> ArtifactSnapshot | None:
        """
        Compute current state of an artifact by folding its events.

        Args:
            artifact_id: The artifact to get state for

        Returns:
            ArtifactSnapshot or None if artifact not found
        """
        events = self.events_for(artifact_id)
        if not events:
            return None
        return fold_events(events)

    def all_snapshots(self) -> dict[str, ArtifactSnapshot]:
        """
        Compute current state of all artifacts.

        Returns:
            Dict mapping artifact_id to ArtifactSnapshot
        """
        # Group events by artifact_id
        events_by_id: dict[str, list[ArtifactEvent]] = {}
        for event in self.iter_events():
            events_by_id.setdefault(event.artifact_id, []).append(event)

        # Fold each artifact's events
        snapshots = {}
        for artifact_id, events in events_by_id.items():
            snapshot = fold_events(events)
            if snapshot:
                snapshots[artifact_id] = snapshot

        return snapshots

    def list_by_status(self, status: str) -> list[ArtifactSnapshot]:
        """
        List all artifacts with a given status.

        Args:
            status: Status to filter by (created, validated, approved, executed, rejected)

        Returns:
            List of matching snapshots
        """
        return [s for s in self.all_snapshots().values() if s.status == status]

    def list_by_type(self, artifact_type: str) -> list[ArtifactSnapshot]:
        """
        List all artifacts of a given type.

        Args:
            artifact_type: Type to filter by (plan, approval, report, etc.)

        Returns:
            List of matching snapshots
        """
        return [s for s in self.all_snapshots().values() if s.artifact_type == artifact_type]

    def pending_approvals(self) -> list[ArtifactSnapshot]:
        """
        List artifacts awaiting approval.

        Returns validated artifacts that require approval (DESTRUCTIVE/EXTERNAL).
        """
        return [
            s for s in self.list_by_status("validated")
            if s.requires_approval()
        ]

    def exists(self, artifact_id: str) -> bool:
        """Check if an artifact exists."""
        return any(e.artifact_id == artifact_id for e in self.iter_events())

    def count(self) -> int:
        """Count total events in ledger."""
        return sum(1 for _ in self.iter_events())

    def artifact_count(self) -> int:
        """Count unique artifacts in ledger."""
        artifact_ids = set()
        for event in self.iter_events():
            artifact_ids.add(event.artifact_id)
        return len(artifact_ids)

    # -------------------------------------------------------------------------
    # Governance Query Methods
    # -------------------------------------------------------------------------

    def constraint_evaluations(
        self,
        artifact_id: str,
        *,
        ruleset_id: str | None = None,
        invariant: str | None = None,
        result: str | None = None,
    ) -> list[ConstraintEvaluation]:
        """
        Get constraint evaluation events for an artifact.

        Args:
            artifact_id: The artifact to query
            ruleset_id: Optional filter by ruleset ID
            invariant: Optional filter by invariant ID
            result: Optional filter by result ("pass" | "fail" | "warning")

        Returns:
            List of structured constraint evaluations
        """
        events = self.query(artifact_id=artifact_id, event_type="constraint.evaluated")

        evaluations = []
        for event in events:
            payload = event.payload

            # Apply optional filters
            if ruleset_id and payload.get("ruleset_id") != ruleset_id:
                continue
            if invariant and payload.get("invariant") != invariant:
                continue
            if result and payload.get("result") != result:
                continue

            evaluations.append(
                ConstraintEvaluation(
                    artifact_id=event.artifact_id,
                    timestamp=event.timestamp,
                    ruleset_id=payload.get("ruleset_id", ""),
                    rule_id=payload.get("rule_id", ""),
                    invariant=payload.get("invariant", ""),
                    result=payload.get("result", ""),
                    evidence=payload.get("evidence", {}),
                )
            )

        return evaluations

    def invariant_checks(
        self,
        artifact_id: str,
        *,
        invariant_id: str | None = None,
        status: str | None = None,
    ) -> list[InvariantCheck]:
        """
        Get invariant check events for an artifact.

        Args:
            artifact_id: The artifact to query
            invariant_id: Optional filter by invariant ID
            status: Optional filter by status ("pass" | "fail")

        Returns:
            List of structured invariant checks
        """
        events = self.query(artifact_id=artifact_id, event_type="invariant.checked")

        checks = []
        for event in events:
            payload = event.payload

            # Apply optional filters
            if invariant_id and payload.get("invariant_id") != invariant_id:
                continue
            if status and payload.get("status") != status:
                continue

            checks.append(
                InvariantCheck(
                    artifact_id=event.artifact_id,
                    timestamp=event.timestamp,
                    invariant_id=payload.get("invariant_id", ""),
                    status=payload.get("status", ""),
                    rules_checked=payload.get("rules_checked", 0),
                    violations=payload.get("violations", 0),
                    affected_items=payload.get("affected_items", []),
                )
            )

        return checks

    # -------------------------------------------------------------------------
    # Execution Query Methods
    # -------------------------------------------------------------------------

    def execution_logs(
        self,
        artifact_id: str | None = None,
        execution_id: str | None = None,
        *,
        phase: str | None = None,
        status: str | None = None,
        handler_id: str | None = None,
    ) -> list[ExecutionLog]:
        """
        Get execution log events.

        At least one of artifact_id or execution_id must be provided.

        Args:
            artifact_id: Optional filter by artifact ID
            execution_id: Optional filter by execution ID
            phase: Optional filter by phase ("prepare" | "execute" | "commit")
            status: Optional filter by status ("started" | "completed" | "failed" | "skipped")
            handler_id: Optional filter by handler ID

        Returns:
            List of structured execution logs
        """
        events = self.query(
            artifact_id=artifact_id,
            execution_id=execution_id,
            event_type="execution.logged",
        )

        logs = []
        for event in events:
            payload = event.payload

            # Apply optional filters
            if phase and payload.get("phase") != phase:
                continue
            if status and payload.get("status") != status:
                continue
            if handler_id and payload.get("handler_id") != handler_id:
                continue

            logs.append(
                ExecutionLog(
                    artifact_id=event.artifact_id,
                    timestamp=event.timestamp,
                    execution_id=payload.get("execution_id", ""),
                    attempt=payload.get("attempt", 0),
                    phase=payload.get("phase", ""),
                    status=payload.get("status", ""),
                    handler_id=payload.get("handler_id", ""),
                    duration_ms=payload.get("duration_ms"),
                    resources=payload.get("resources"),
                    error_type=payload.get("error_type"),
                    error=payload.get("error"),
                )
            )

        return logs

    def execution_timeline(self, execution_id: str) -> list[ExecutionLog]:
        """
        Get execution timeline for a specific execution_id.

        Returns all execution.logged events for the execution in chronological order.

        Args:
            execution_id: The execution ID to query

        Returns:
            List of execution logs in chronological order
        """
        return self.execution_logs(execution_id=execution_id)

    # -------------------------------------------------------------------------
    # Audit Trail
    # -------------------------------------------------------------------------

    def audit_trail(self, artifact_id: str) -> list[ArtifactEvent]:
        """
        Get complete audit trail for an artifact.

        Returns all events (lifecycle + governance + execution) in chronological order.
        This is the canonical "single story" for an artifact.

        Args:
            artifact_id: The artifact to query

        Returns:
            List of all events for the artifact in chronological order
        """
        return self.query(artifact_id=artifact_id)

    # -------------------------------------------------------------------------
    # Derived Summaries
    # -------------------------------------------------------------------------

    def execution_summary(self, execution_id: str) -> ExecutionSummary | None:
        """
        Compute execution summary from execution.logged events.

        This is a derived summary - computed on-demand, not stored.

        Args:
            execution_id: The execution ID to summarize

        Returns:
            ExecutionSummary or None if no events found
        """
        logs = self.execution_logs(execution_id=execution_id)
        if not logs:
            return None

        # Extract basic info from first log
        artifact_id = logs[0].artifact_id
        handler_id = logs[0].handler_id

        # Compute phase durations
        phase_durations: dict[str, float] = {}
        for log in logs:
            if log.status == "completed" and log.duration_ms is not None:
                phase_durations[log.phase] = log.duration_ms

        # Determine overall status and first error
        has_failure = any(log.status == "failed" for log in logs)
        first_error = None
        failure_phase = None
        for log in logs:
            if log.status == "failed":
                if first_error is None:
                    first_error = log.error
                    failure_phase = log.phase
                break

        overall_status = "failure" if has_failure else "success"

        # Count attempts (max attempt number + 1)
        attempt_count = max(log.attempt for log in logs) + 1

        # Compute total duration
        total_duration_ms = sum(phase_durations.values())

        # Merge resources across phases
        merged_resources: dict[str, Any] = {}
        for log in logs:
            if log.resources:
                for key, value in log.resources.items():
                    if isinstance(value, (int, float)):
                        merged_resources[key] = merged_resources.get(key, 0) + value
                    elif key not in merged_resources:
                        merged_resources[key] = value

        # Extract plan step IDs
        plan_step_ids = [
            log.handler_id for log in logs if log.status == "completed"
        ]

        # Get start and end times
        started_at = min(log.timestamp for log in logs)
        ended_at = max(log.timestamp for log in logs)

        return ExecutionSummary(
            execution_id=execution_id,
            artifact_id=artifact_id,
            handler_id=handler_id,
            overall_status=overall_status,
            phase_durations=phase_durations,
            attempt_count=attempt_count,
            total_duration_ms=total_duration_ms,
            resources=merged_resources,
            first_error=first_error,
            failure_phase=failure_phase,
            plan_step_ids=plan_step_ids,
            started_at=started_at,
            ended_at=ended_at,
        )

    def constraint_summary(self, artifact_id: str) -> ConstraintSummary:
        """
        Compute constraint summary from constraint evaluation events.

        This is a derived summary - computed on-demand, not stored.

        Args:
            artifact_id: The artifact to summarize

        Returns:
            ConstraintSummary (never None, may indicate "missing" status)
        """
        evaluations = self.constraint_evaluations(artifact_id)
        invariant_checks = self.invariant_checks(artifact_id)

        # Determine data status
        if not evaluations and not invariant_checks:
            constraint_data_status = "missing"
        elif evaluations and invariant_checks:
            constraint_data_status = "present"
        else:
            constraint_data_status = "partial"

        # Extract rulesets
        rulesets_evaluated = list(set(ev.ruleset_id for ev in evaluations))

        # Count results
        passed = sum(1 for ev in evaluations if ev.result == "pass")
        failed = sum(1 for ev in evaluations if ev.result == "fail")
        warnings = sum(1 for ev in evaluations if ev.result == "warning")

        # Extract violated invariants
        violated_invariants = list(
            set(
                check.invariant_id
                for check in invariant_checks
                if check.status == "fail"
            )
        )

        # Get evaluation time (from first evaluation)
        evaluation_time = evaluations[0].timestamp if evaluations else None

        return ConstraintSummary(
            artifact_id=artifact_id,
            constraint_data_status=constraint_data_status,
            rulesets_evaluated=rulesets_evaluated,
            total_rules_checked=len(evaluations),
            passed=passed,
            failed=failed,
            warnings=warnings,
            violated_invariants=violated_invariants,
            evaluation_time=evaluation_time,
        )

    def invariant_summary(self, artifact_id: str) -> InvariantSummary:
        """
        Compute invariant summary from invariant check events.

        This is a derived summary - computed on-demand, not stored.

        Args:
            artifact_id: The artifact to summarize

        Returns:
            InvariantSummary
        """
        checks = self.invariant_checks(artifact_id)

        invariants_checked = list(set(check.invariant_id for check in checks))

        # Build violations map
        violations: dict[str, list[str]] = {}
        for check in checks:
            if check.status == "fail":
                violations[check.invariant_id] = check.affected_items

        # Determine overall status
        overall_status = "fail" if violations else "pass"

        return InvariantSummary(
            artifact_id=artifact_id,
            invariants_checked=invariants_checked,
            violations=violations,
            overall_status=overall_status,
        )

    def latest_execution_id(self, artifact_id: str) -> str | None:
        """
        Get the most recent execution_id for an artifact.

        Returns the execution_id from the chronologically last execution.logged event.

        Args:
            artifact_id: The artifact ID

        Returns:
            execution_id or None if no execution logs exist
        """
        logs = self.execution_logs(artifact_id=artifact_id)
        if not logs:
            return None
        # logs are in chronological order (asc), so last is most recent
        return logs[-1].execution_id
