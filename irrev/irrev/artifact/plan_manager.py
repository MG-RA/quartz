"""
Plan protocol management for the artifact ledger.

Agents propose/validate/approve/execute plans via append-only ledger events.
Handlers perform the actual side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .content_store import ContentStore
from .events import (
    ARTIFACT_APPROVED,
    ARTIFACT_CREATED,
    ARTIFACT_EXECUTED,
    ARTIFACT_REJECTED,
    ARTIFACT_VALIDATED,
    ArtifactEvent,
    create_event,
)
from .ledger import ArtifactLedger
from .risk import RiskClass, compute_risk
from .snapshot import ArtifactSnapshot
from .types import get_type_pack
from .util import new_ulid


ExecutionHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ApprovalPolicy:
    require_force_ack_for: frozenset[RiskClass] = frozenset({RiskClass.MUTATION_DESTRUCTIVE})


class PlanManager:
    def __init__(self, vault_path: Path, *, policy: ApprovalPolicy | None = None):
        self.vault_path = vault_path.resolve()
        self.irrev_dir = self.vault_path.parent / ".irrev"
        self.ledger = ArtifactLedger(self.irrev_dir)
        self.content_store = ContentStore(self.irrev_dir)
        self.policy = policy or ApprovalPolicy()

    def _get_content_dict(self, content_id: str) -> dict[str, Any] | None:
        data = self.content_store.get(content_id)
        return data if isinstance(data, dict) else None

    def propose(
        self,
        operation: str,
        payload: dict[str, Any],
        actor: str,
        *,
        delegate_to: str | None = None,
        inputs: list[dict[str, str]] | None = None,
        surface: str | None = None,
        artifact_type: str = "plan",
    ) -> str:
        content: dict[str, Any] = {
            "operation": operation,
            "payload": payload,
        }
        if delegate_to is not None:
            content["delegate_to"] = delegate_to
        if inputs:
            content["inputs"] = inputs

        content_id = self.content_store.store(content)
        artifact_id = new_ulid()

        risk, reasons = compute_risk(operation, payload)
        pack = get_type_pack(artifact_type)
        payload_manifest = pack.compute_payload_manifest(content) if pack else []
        extracted_inputs = pack.extract_inputs(content) if pack else (inputs or [])

        created_payload: dict[str, Any] = {
            "risk_class": risk.value,
            "risk_reasons": reasons,
            "inputs": extracted_inputs,
            "payload_manifest": payload_manifest,
            "operation": operation,
        }
        if delegate_to is not None:
            created_payload["delegate_to"] = delegate_to
        if surface is not None:
            created_payload["surface"] = surface

        self.ledger.append(
            create_event(
                ARTIFACT_CREATED,
                artifact_id=artifact_id,
                actor=actor,
                payload=created_payload,
                content_id=content_id,
                artifact_type=artifact_type,
            )
        )
        return artifact_id

    def validate(
        self,
        artifact_id: str,
        *,
        validator: str = "system",
        constraint_results: dict[str, Any] | None = None,
    ) -> bool:
        snapshot = self.ledger.snapshot(artifact_id)
        if snapshot is None:
            raise ValueError(f"Unknown artifact: {artifact_id}")
        if snapshot.status != "created":
            raise ValueError(f"Artifact not in created state: {snapshot.status}")

        content = self._get_content_dict(snapshot.content_id)
        if content is None:
            errors = [f"missing content: {snapshot.content_id}"]
            self._append_validation_events(
                artifact_id, validator, errors, RiskClass.EXTERNAL_SIDE_EFFECT, [], constraint_results
            )
            return False

        pack = get_type_pack(snapshot.artifact_type)
        errors = pack.validate(content) if pack else [f"no type pack for artifact_type={snapshot.artifact_type!r}"]

        operation = str(content.get("operation", snapshot.producer.get("operation", "")))
        payload = content.get("payload") if isinstance(content.get("payload"), dict) else {}
        computed_risk, reasons = compute_risk(operation, payload)  # authoritative

        self._append_validation_events(artifact_id, validator, errors, computed_risk, reasons, constraint_results)
        return not errors

    def _append_validation_events(
        self,
        artifact_id: str,
        validator: str,
        errors: list[str],
        computed_risk: RiskClass,
        reasons: list[str],
        constraint_results: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "validator": validator,
            "errors": errors,
            "computed_risk_class": computed_risk.value,
            "risk_reasons": reasons,
        }

        # NEW: Include constraint results if available
        if constraint_results:
            payload["constraint_results"] = constraint_results

        events: list[ArtifactEvent] = [
            create_event(
                ARTIFACT_VALIDATED,
                artifact_id=artifact_id,
                actor=validator,
                payload=payload,
            )
        ]
        if errors:
            events.append(
                create_event(
                    ARTIFACT_REJECTED,
                    artifact_id=artifact_id,
                    actor=validator,
                    payload={"reason": "; ".join(errors), "stage": "validation"},
                )
            )
        self.ledger.append_many(events)

    def approve(
        self,
        artifact_id: str,
        approver: str,
        *,
        scope: str | None = None,
        force_ack: bool = False,
    ) -> str:
        snapshot = self.ledger.snapshot(artifact_id)
        if snapshot is None:
            raise ValueError(f"Unknown artifact: {artifact_id}")
        if snapshot.status != "validated" or snapshot.validation_errors:
            raise ValueError("Artifact must be validated with no errors before approval")

        risk = snapshot.computed_risk_class or snapshot.risk_class or RiskClass.EXTERNAL_SIDE_EFFECT
        if risk in self.policy.require_force_ack_for and not force_ack:
            raise ValueError(f"Approval requires force_ack for risk_class={risk.value}")

        approval_payload: dict[str, Any] = {
            "target_artifact_id": artifact_id,
            "approved_content_ids": [snapshot.content_id],
            "scope": scope or snapshot.producer.get("operation", ""),
            "approver": approver,
            "force_ack": bool(force_ack),
        }

        approval_content_id = self.content_store.store(approval_payload)
        approval_artifact_id = new_ulid()

        approval_created = create_event(
            ARTIFACT_CREATED,
            artifact_id=approval_artifact_id,
            actor=approver,
            payload={
                "risk_class": RiskClass.APPEND_ONLY.value,
                "inputs": [{"artifact_id": artifact_id, "content_id": snapshot.content_id}],
                "operation": "artifact.approve",
            },
            content_id=approval_content_id,
            artifact_type="approval",
        )

        target_approved = create_event(
            ARTIFACT_APPROVED,
            artifact_id=artifact_id,
            actor=approver,
            payload={
                "approval_artifact_id": approval_artifact_id,
                "force_ack": bool(force_ack),
                "scope": scope or snapshot.producer.get("operation", ""),
            },
        )

        self.ledger.append_many([approval_created, target_approved])
        return approval_artifact_id

    def execute(
        self,
        artifact_id: str,
        executor: str,
        *,
        handler: ExecutionHandler,
    ) -> str:
        snapshot = self.ledger.snapshot(artifact_id)
        if snapshot is None:
            raise ValueError(f"Unknown artifact: {artifact_id}")
        if snapshot.status != "approved":
            raise ValueError(f"Artifact must be approved before execution (status={snapshot.status})")

        if snapshot.requires_approval():
            if not snapshot.approval_artifact_id:
                raise ValueError("Missing approval_artifact_id on approved artifact")
            if not self._approval_satisfies(snapshot.approval_artifact_id, snapshot):
                raise ValueError("Approval artifact does not satisfy policy (content_id mismatch)")

        if snapshot.delegate_to and snapshot.delegate_to != executor:
            raise ValueError(f"Executor mismatch: delegate_to={snapshot.delegate_to} executor={executor}")

        content = self._get_content_dict(snapshot.content_id)
        if content is None:
            raise ValueError(f"Missing content: {snapshot.content_id}")

        result = handler(content)
        result_artifact_id = new_ulid()
        result_content_id = self.content_store.store(result)

        result_created = create_event(
            ARTIFACT_CREATED,
            artifact_id=result_artifact_id,
            actor=executor,
            payload={
                "risk_class": RiskClass.APPEND_ONLY.value,
                "inputs": [{"artifact_id": artifact_id, "content_id": snapshot.content_id}],
                "operation": f"result:{snapshot.producer.get('operation', '')}".strip(":"),
            },
            content_id=result_content_id,
            artifact_type="execution_summary",
        )

        executed = create_event(
            ARTIFACT_EXECUTED,
            artifact_id=artifact_id,
            actor=executor,
            payload={
                "result_artifact_id": result_artifact_id,
                "erasure_cost": result.get("erasure_cost"),
                "creation_summary": result.get("creation_summary"),
                "executor": executor,
            },
        )

        self.ledger.append_many([result_created, executed])
        return result_artifact_id

    def _approval_satisfies(self, approval_artifact_id: str, snapshot: ArtifactSnapshot) -> bool:
        approval_snapshot = self.ledger.snapshot(approval_artifact_id)
        if approval_snapshot is None:
            return False
        approval_content = self._get_content_dict(approval_snapshot.content_id)
        if approval_content is None:
            return False
        if approval_content.get("target_artifact_id") != snapshot.artifact_id:
            return False
        approved_content_ids = approval_content.get("approved_content_ids", [])
        if not isinstance(approved_content_ids, list) or snapshot.content_id not in approved_content_ids:
            return False
        return True
