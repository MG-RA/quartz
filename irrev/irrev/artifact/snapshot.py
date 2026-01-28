"""
Artifact snapshot projection from event stream.

Snapshots are computed state - they are derived by folding events,
never stored as the source of truth. This maintains the append-only
property of the ledger while providing efficient state queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Sequence

from .risk import RiskClass
from .events import (
    ArtifactEvent,
    ARTIFACT_CREATED,
    ARTIFACT_VALIDATED,
    ARTIFACT_APPROVED,
    ARTIFACT_EXECUTED,
    ARTIFACT_REJECTED,
    ARTIFACT_SUPERSEDED,
)


# Lifecycle states
STATUS_CREATED = "created"
STATUS_VALIDATED = "validated"
STATUS_APPROVED = "approved"
STATUS_EXECUTED = "executed"
STATUS_REJECTED = "rejected"
STATUS_SUPERSEDED = "superseded"


@dataclass
class ArtifactSnapshot:
    """
    Computed state of an artifact by folding its event history.

    This is a projection, not stored data. It can always be recomputed
    from the event stream.
    """

    # Identity
    artifact_id: str
    content_id: str
    artifact_type: str

    # Current lifecycle state
    status: str = STATUS_CREATED

    # Risk classification (computed, not claimed)
    risk_class: RiskClass | None = None

    # Provenance
    inputs: list[dict[str, str]] = field(default_factory=list)  # [{artifact_id, content_id}]
    producer: dict[str, Any] = field(default_factory=dict)  # {actor, operation, timestamp}

    # Payload manifest (for file artifacts)
    payload_manifest: list[dict[str, Any]] = field(default_factory=list)  # [{path, bytes, sha256}]

    # Delegation
    delegate_to: str | None = None

    # Validation
    validation_errors: list[str] = field(default_factory=list)
    computed_risk_class: RiskClass | None = None

    # Approval
    approval_artifact_id: str | None = None
    force_ack: bool = False
    approval_scope: str | None = None

    # Execution
    result_artifact_id: str | None = None
    erasure_cost: dict[str, Any] | None = None
    creation_summary: dict[str, Any] | None = None
    executor: str | None = None

    # Rejection
    rejection_reason: str | None = None
    rejection_stage: str | None = None

    # Supersession
    superseded_by: str | None = None

    # Timestamps
    created_at: datetime | None = None
    validated_at: datetime | None = None
    approved_at: datetime | None = None
    executed_at: datetime | None = None

    # Full event history (optional, for debugging)
    events: list[ArtifactEvent] = field(default_factory=list)

    def is_terminal(self) -> bool:
        """Check if artifact is in a terminal state."""
        return self.status in {STATUS_EXECUTED, STATUS_REJECTED, STATUS_SUPERSEDED}

    def requires_approval(self) -> bool:
        """Check if artifact requires approval before execution."""
        # DESTRUCTIVE and EXTERNAL_SIDE_EFFECT require approval
        risk = self.computed_risk_class or self.risk_class
        return risk in {RiskClass.MUTATION_DESTRUCTIVE, RiskClass.EXTERNAL_SIDE_EFFECT}

    def can_execute(self) -> bool:
        """Check if artifact can be executed."""
        if self.status != STATUS_APPROVED:
            return False
        if self.requires_approval() and not self.approval_artifact_id:
            return False
        return True


def fold_events(events: Sequence[ArtifactEvent]) -> ArtifactSnapshot | None:
    """
    Compute current artifact state by folding event history.

    Events must be for the same artifact_id and in chronological order.
    Returns None if no events provided.
    """
    if not events:
        return None

    # Verify all events are for the same artifact
    artifact_id = events[0].artifact_id
    if not all(e.artifact_id == artifact_id for e in events):
        raise ValueError("All events must be for the same artifact_id")

    # Initialize from first event (must be ARTIFACT_CREATED)
    first = events[0]
    if first.event_type != ARTIFACT_CREATED:
        raise ValueError(f"First event must be {ARTIFACT_CREATED}, got {first.event_type}")

    snapshot = ArtifactSnapshot(
        artifact_id=artifact_id,
        content_id=first.content_id or "",
        artifact_type=first.artifact_type or "",
        status=STATUS_CREATED,
        created_at=first.timestamp,
        events=list(events),
    )

    # Extract fields from created payload
    payload = first.payload
    claimed = payload.get("risk_class")
    if claimed:
        try:
            snapshot.risk_class = RiskClass(claimed)
        except ValueError:
            snapshot.risk_class = None
    snapshot.inputs = payload.get("inputs", [])
    snapshot.payload_manifest = payload.get("payload_manifest", [])
    snapshot.delegate_to = payload.get("delegate_to")
    snapshot.producer = {
        "actor": first.actor,
        "operation": payload.get("operation", ""),
        "timestamp": first.timestamp.isoformat(),
    }
    if payload.get("surface") is not None:
        snapshot.producer["surface"] = payload.get("surface")

    # Fold remaining events
    for event in events[1:]:
        _apply_event(snapshot, event)

    return snapshot


def _apply_event(snapshot: ArtifactSnapshot, event: ArtifactEvent) -> None:
    """Apply a single event to update snapshot state."""
    payload = event.payload

    if event.event_type == ARTIFACT_VALIDATED:
        snapshot.status = STATUS_VALIDATED
        snapshot.validated_at = event.timestamp
        snapshot.validation_errors = payload.get("errors", [])
        computed = payload.get("computed_risk_class")
        if computed:
            try:
                snapshot.computed_risk_class = RiskClass(computed)
            except ValueError:
                snapshot.computed_risk_class = None

        # If validation failed, mark as rejected
        if snapshot.validation_errors:
            snapshot.status = STATUS_REJECTED
            snapshot.rejection_reason = "; ".join(snapshot.validation_errors)
            snapshot.rejection_stage = "validation"

    elif event.event_type == ARTIFACT_APPROVED:
        snapshot.status = STATUS_APPROVED
        snapshot.approved_at = event.timestamp
        snapshot.approval_artifact_id = payload.get("approval_artifact_id")
        snapshot.force_ack = payload.get("force_ack", False)
        snapshot.approval_scope = payload.get("scope")

    elif event.event_type == ARTIFACT_EXECUTED:
        snapshot.status = STATUS_EXECUTED
        snapshot.executed_at = event.timestamp
        snapshot.result_artifact_id = payload.get("result_artifact_id")
        snapshot.erasure_cost = payload.get("erasure_cost")
        snapshot.creation_summary = payload.get("creation_summary")
        snapshot.executor = payload.get("executor")

    elif event.event_type == ARTIFACT_REJECTED:
        snapshot.status = STATUS_REJECTED
        snapshot.rejection_reason = payload.get("reason")
        snapshot.rejection_stage = payload.get("stage")

    elif event.event_type == ARTIFACT_SUPERSEDED:
        snapshot.status = STATUS_SUPERSEDED
        snapshot.superseded_by = payload.get("superseded_by")


def project_artifact(
    artifact_id: str,
    events: Sequence[ArtifactEvent],
) -> ArtifactSnapshot | None:
    """
    Project a single artifact's state from a stream of events.

    Filters events for the given artifact_id and folds them.
    """
    artifact_events = [e for e in events if e.artifact_id == artifact_id]
    if not artifact_events:
        return None

    # Preserve append order from the ledger; timestamp is informational.
    return fold_events(artifact_events)
