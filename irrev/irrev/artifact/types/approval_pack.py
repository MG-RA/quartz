from __future__ import annotations

from typing import Any


class ApprovalTypePack:
    def validate(self, content: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        target = content.get("target_artifact_id")
        approved = content.get("approved_content_ids")
        scope = content.get("scope")
        approver = content.get("approver")

        if not isinstance(target, str) or not target.strip():
            errors.append("approval.target_artifact_id must be a non-empty string")
        if not isinstance(approved, list) or not approved or not all(isinstance(x, str) and x for x in approved):
            errors.append("approval.approved_content_ids must be a non-empty list of strings")
        if not isinstance(scope, str) or not scope.strip():
            errors.append("approval.scope must be a non-empty string")
        if not isinstance(approver, str) or not approver.strip():
            errors.append("approval.approver must be a non-empty string")

        force_ack = content.get("force_ack", False)
        if not isinstance(force_ack, bool):
            errors.append("approval.force_ack must be boolean when provided")

        return errors

    def extract_inputs(self, content: dict[str, Any]) -> list[dict[str, str]]:
        # Approvals are inputs-only via their target reference; content_id binding is in payload.
        target = content.get("target_artifact_id")
        if isinstance(target, str) and target.strip():
            return [{"artifact_id": target, "content_id": ""}]
        return []

    def compute_payload_manifest(self, content: dict[str, Any]) -> list[dict[str, Any]]:
        return []

