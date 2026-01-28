"""
Immutable event types for the artifact ledger.

Events are the atomic unit of the ledger - each line in artifact.jsonl is one event.
Current state is computed by folding events, never by mutating prior entries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

# Event type constants
ARTIFACT_CREATED = "artifact.created"
ARTIFACT_VALIDATED = "artifact.validated"
ARTIFACT_APPROVED = "artifact.approved"
ARTIFACT_EXECUTED = "artifact.executed"
ARTIFACT_REJECTED = "artifact.rejected"
ARTIFACT_SUPERSEDED = "artifact.superseded"

# Constraint and governance event types
CONSTRAINT_EVALUATED = "constraint.evaluated"
INVARIANT_CHECKED = "invariant.checked"
EXECUTION_LOGGED = "execution.logged"

# All valid event types
EVENT_TYPES = frozenset({
    ARTIFACT_CREATED,
    ARTIFACT_VALIDATED,
    ARTIFACT_APPROVED,
    ARTIFACT_EXECUTED,
    ARTIFACT_REJECTED,
    ARTIFACT_SUPERSEDED,
    CONSTRAINT_EVALUATED,
    INVARIANT_CHECKED,
    EXECUTION_LOGGED,
})

# Artifact types
ArtifactType = Literal[
    "plan",
    "approval",
    "report",
    "execution_summary",
    "lint_report",
    "ruleset",
    "export",
    "config",
    "note",
    "change_event",
    "fs_event",
    "audit_entry",
    "bundle",
]

ARTIFACT_TYPES = frozenset({
    "plan",
    "approval",
    "report",
    "execution_summary",
    "lint_report",
    "ruleset",
    "export",
    "config",
    "note",
    "change_event",
    "fs_event",
    "audit_entry",
    "bundle",
})


@dataclass(frozen=True)
class ArtifactEvent:
    """
    Immutable event in the artifact ledger.

    Events are append-only - once written, they are never modified.
    Each event transitions an artifact through its lifecycle.
    """

    # Required fields for all events
    event_type: str  # One of EVENT_TYPES
    artifact_id: str  # Stable lifecycle ID (ULID)
    timestamp: datetime
    actor: str  # "human:alice", "agent:planner", "handler:neo4j", "system"

    # Event-specific payload (varies by event_type)
    payload: dict[str, Any] = field(default_factory=dict)

    # For "artifact.created" events only
    content_id: str | None = None  # sha256 of payload content
    artifact_type: str | None = None  # One of ARTIFACT_TYPES

    def __post_init__(self) -> None:
        """Validate event structure."""
        if self.event_type not in EVENT_TYPES:
            raise ValueError(f"Invalid event_type: {self.event_type}")
        if self.artifact_type is not None and self.artifact_type not in ARTIFACT_TYPES:
            raise ValueError(f"Invalid artifact_type: {self.artifact_type}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        result: dict[str, Any] = {
            "event_type": self.event_type,
            "artifact_id": self.artifact_id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
        }
        if self.payload:
            result["payload"] = self.payload
        if self.content_id is not None:
            result["content_id"] = self.content_id
        if self.artifact_type is not None:
            result["artifact_type"] = self.artifact_type
        return result

    def to_json(self) -> str:
        """Serialize to JSON string (single line)."""
        return json.dumps(self.to_dict(), separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArtifactEvent:
        """Reconstruct from JSON dict."""
        return cls(
            event_type=data["event_type"],
            artifact_id=data["artifact_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            actor=data["actor"],
            payload=data.get("payload", {}),
            content_id=data.get("content_id"),
            artifact_type=data.get("artifact_type"),
        )

    @classmethod
    def from_json(cls, line: str) -> ArtifactEvent:
        """Parse from JSON string."""
        return cls.from_dict(json.loads(line))


# Payload field documentation for each event type
EVENT_PAYLOAD_FIELDS = {
    ARTIFACT_CREATED: {
        "content_id": "sha256 hash of payload content",
        "artifact_type": "Type of artifact (plan, approval, report, etc.)",
        "risk_class": "Computed risk classification",
        "inputs": "List of {artifact_id, content_id} dependencies",
        "payload_manifest": "List of {path, bytes, sha256} for file payloads",
        "operation": "Operation name (e.g., 'neo4j-load')",
        "delegate_to": "Optional handler/agent to execute",
        "context": "Execution context (vault_state, active_rulesets, surface, engine_version)",
        "plan_metadata": "Plan details (predicted_erasure, predicted_outputs, dependencies)",
    },
    ARTIFACT_VALIDATED: {
        "validator": "Who/what performed validation",
        "errors": "List of validation errors (empty if passed)",
        "computed_risk_class": "Risk class as computed by validator",
        "constraint_results": "Constraint evaluation summary (rulesets_evaluated, rules_checked, etc.)",
    },
    ARTIFACT_APPROVED: {
        "approval_artifact_id": "ID of the approval artifact",
        "force_ack": "Whether force was acknowledged for destructive ops",
        "scope": "What exactly was approved",
    },
    ARTIFACT_EXECUTED: {
        "result_artifact_id": "ID of the result artifact",
        "erasure_cost": "ErasureCost dict (notes, edges, files, bytes_erased)",
        "creation_summary": "CreationSummary dict (notes, edges, files, bytes_written)",
        "executor": "Handler that executed",
        "execution_details": "Execution metrics (duration_ms, phases, resource_usage)",
    },
    ARTIFACT_REJECTED: {
        "reason": "Why the artifact was rejected",
        "stage": "At which stage rejection occurred",
    },
    ARTIFACT_SUPERSEDED: {
        "superseded_by": "artifact_id of the superseding artifact",
    },
    CONSTRAINT_EVALUATED: {
        "ruleset_id": "ID of the ruleset containing the rule",
        "ruleset_version": "Version of the ruleset",
        "rule_id": "ID of the rule being evaluated",
        "rule_scope": "Scope of the rule (concept, graph, artifact, etc.)",
        "invariant": "Invariant ID this rule enforces",
        "result": "pass | fail | warning",
        "evidence": "Evidence for the result (item_id, item_type, message)",
    },
    INVARIANT_CHECKED: {
        "invariant_id": "ID of the invariant",
        "status": "pass | fail",
        "rules_checked": "Number of rules checked for this invariant",
        "violations": "Number of violations found",
        "affected_items": "List of item IDs affected",
    },
    EXECUTION_LOGGED: {
        "execution_id": "Unique ID per run() call (ULID) - enables retry correlation",
        "attempt": "Retry count (0, 1, 2...) - tracks retry attempts",
        "phase": "Execution phase (prepare | execute | commit)",
        "status": "Phase status (started | completed | failed | skipped)",
        "handler_id": "Handler operation name (e.g., 'neo4j.load')",
        "plan_step_id": "Optional: which step in plan (if multi-step)",
        "started_at": "ISO timestamp when phase started",
        "ended_at": "ISO timestamp when phase ended",
        "duration_ms": "Phase duration in milliseconds",
        "resources": "ExecutionMetrics dict (items_processed, bytes_written, custom metrics)",
        "error_type": "Exception class name if failed (e.g., 'TimeoutError')",
        "error": "Truncated error message (max 500 chars) if failed",
        "reason": "Optional: why phase was skipped (e.g., 'logging_disabled', 'no_commit_needed')",
    },
}


def create_event(
    event_type: str,
    artifact_id: str,
    actor: str,
    *,
    payload: dict[str, Any] | None = None,
    content_id: str | None = None,
    artifact_type: str | None = None,
    timestamp: datetime | None = None,
) -> ArtifactEvent:
    """
    Factory function for creating events.

    Ensures consistent timestamp handling and validation.
    """
    return ArtifactEvent(
        event_type=event_type,
        artifact_id=artifact_id,
        timestamp=timestamp or datetime.now(timezone.utc),
        actor=actor,
        payload=payload or {},
        content_id=content_id,
        artifact_type=artifact_type,
    )
