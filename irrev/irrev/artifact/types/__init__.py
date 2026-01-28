"""
Artifact type packs.

Type packs validate payload schemas and extract dependency/input references.
"""

from __future__ import annotations

from typing import Any, Protocol


class ArtifactTypePack(Protocol):
    def validate(self, content: dict[str, Any]) -> list[str]:
        ...

    def extract_inputs(self, content: dict[str, Any]) -> list[dict[str, str]]:
        ...

    def compute_payload_manifest(self, content: dict[str, Any]) -> list[dict[str, Any]]:
        ...


from .plan_pack import PlanTypePack
from .approval_pack import ApprovalTypePack
from .bundle_pack import BundleTypePack


TYPE_PACKS: dict[str, ArtifactTypePack] = {
    "plan": PlanTypePack(),
    "approval": ApprovalTypePack(),
    "bundle": BundleTypePack(),
}


# ============================================================================
# ARTIFACT TYPE METADATA REGISTRY
# ============================================================================

TYPE_REGISTRY_VERSION = 2  # Increment when adding/removing types

ARTIFACT_TYPE_METADATA: dict[str, dict[str, Any]] = {
    # Operational artifacts (have type packs)
    "plan": {
        "description": "Execution plan with operation + payload + inputs",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created", "artifact.validated"],
        "may_have_events": ["artifact.approved", "artifact.executed", "artifact.rejected"],
        "governance_expectations": ["approval_required_if_destructive", "execution_summary_required"],
        "invariants": ["governance", "attribution"],
    },
    "approval": {
        "description": "Approval chain metadata for plan governance",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created", "artifact.validated"],
        "may_have_events": [],
        "governance_expectations": ["force_ack_required_if_destructive"],
        "invariants": ["governance"],
    },
    "bundle": {
        "description": "Proof pack aggregating plan + approval + result",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created", "artifact.validated"],
        "may_have_events": [],
        "governance_expectations": ["bundle_version_stable"],
        "invariants": ["governance", "attribution"],
    },
    # Result artifacts (no type packs yet)
    "execution_summary": {
        "description": "Execution result from handler",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": ["attribution"],
    },
    "lint_report": {
        "description": "Lint output artifact",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    # Low-level artifacts (no type packs)
    "report": {
        "description": "Generic analysis report",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "note": {
        "description": "Free-form note artifact",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "config": {
        "description": "Configuration artifact",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": ["governance"],
    },
    # Event artifacts (low-level)
    "change_event": {
        "description": "VCS change event",
        "linkable": True,
        "requires_envelope": False,
        "requires_events": [],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "fs_event": {
        "description": "File system event",
        "linkable": True,
        "requires_envelope": False,
        "requires_events": [],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "audit_entry": {
        "description": "Audit log entry",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": ["governance"],
    },
}


# ============================================================================
# REGISTRY QUERY FUNCTIONS
# ============================================================================

def get_type_pack(artifact_type: str) -> ArtifactTypePack | None:
    """Get type pack for artifact type (case-insensitive, None-safe)."""
    return TYPE_PACKS.get((artifact_type or "").strip().lower())


def get_type_metadata(artifact_type: str) -> dict[str, Any] | None:
    """Get metadata for artifact type."""
    return ARTIFACT_TYPE_METADATA.get((artifact_type or "").strip().lower())


def list_artifact_types() -> list[str]:
    """List all registered artifact types."""
    return sorted(ARTIFACT_TYPE_METADATA.keys())


def has_type_pack(artifact_type: str) -> bool:
    """Check if artifact type has a validation type pack."""
    return get_type_pack(artifact_type) is not None

