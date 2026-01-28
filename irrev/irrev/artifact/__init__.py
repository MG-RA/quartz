"""
Unified Artifact Ledger System (Event-Sourced).

This package provides a unified spine for all irrev artifacts (plans, configs,
reports, audit entries, events) with:

- Content-addressed storage (CAS)
- Append-only event ledger (never modified)
- Dual identity: artifact_id (lifecycle) vs content_id (payload hash)
- Risk classification computed from predicted effects
- Plan protocol: propose → validate → approve → execute

Per the 4 kernel invariants:
- Decomposition: artifact_type separates roles; agents propose, handlers execute
- Governance: approvals are separate artifacts; DESTRUCTIVE/EXTERNAL requires force_ack
- Attribution: actor field on every event; producer chain explicit
- Irreversibility: ledger is append-only; risk_class computed not claimed; erasure_cost tracked
"""

from .events import (
    ArtifactEvent,
    ARTIFACT_CREATED,
    ARTIFACT_VALIDATED,
    ARTIFACT_APPROVED,
    ARTIFACT_EXECUTED,
    ARTIFACT_REJECTED,
    ARTIFACT_SUPERSEDED,
)
from .snapshot import ArtifactSnapshot, fold_events
from .ledger import ArtifactLedger
from .content_store import ContentStore
from .risk import RiskClass, compute_risk_class
from .plan_manager import PlanManager
from .util import new_ulid

__all__ = [
    # Events
    "ArtifactEvent",
    "ARTIFACT_CREATED",
    "ARTIFACT_VALIDATED",
    "ARTIFACT_APPROVED",
    "ARTIFACT_EXECUTED",
    "ARTIFACT_REJECTED",
    "ARTIFACT_SUPERSEDED",
    # Snapshot
    "ArtifactSnapshot",
    "fold_events",
    # Storage
    "ArtifactLedger",
    "ContentStore",
    # Risk
    "RiskClass",
    "compute_risk_class",
    # Plan Protocol
    "PlanManager",
    # IDs
    "new_ulid",
]
