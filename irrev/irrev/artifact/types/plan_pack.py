from __future__ import annotations

from typing import Any

from ..content_store import compute_payload_manifest


class PlanTypePack:
    def validate(self, content: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        op = content.get("operation")
        payload = content.get("payload")
        if not isinstance(op, str) or not op.strip():
            errors.append("plan.operation must be a non-empty string")
        if payload is None or not isinstance(payload, dict):
            errors.append("plan.payload must be a JSON object")

        inputs = content.get("inputs", [])
        if inputs is not None:
            if not isinstance(inputs, list):
                errors.append("plan.inputs must be a list")
            else:
                for i, item in enumerate(inputs):
                    if not isinstance(item, dict):
                        errors.append(f"plan.inputs[{i}] must be an object")
                        continue
                    if not item.get("artifact_id") or not item.get("content_id"):
                        errors.append(f"plan.inputs[{i}] must include artifact_id and content_id")

        delegate_to = content.get("delegate_to")
        if delegate_to is not None and (not isinstance(delegate_to, str) or not delegate_to.strip()):
            errors.append("plan.delegate_to must be a non-empty string when provided")

        return errors

    def extract_inputs(self, content: dict[str, Any]) -> list[dict[str, str]]:
        inputs = content.get("inputs", [])
        if not isinstance(inputs, list):
            return []
        out: list[dict[str, str]] = []
        for item in inputs:
            if not isinstance(item, dict):
                continue
            artifact_id = item.get("artifact_id")
            content_id = item.get("content_id")
            if isinstance(artifact_id, str) and isinstance(content_id, str):
                out.append({"artifact_id": artifact_id, "content_id": content_id})
        return out

    def compute_payload_manifest(self, content: dict[str, Any]) -> list[dict[str, Any]]:
        payload = content.get("payload")
        if not isinstance(payload, dict):
            return []

        files = payload.get("files")
        if not isinstance(files, dict):
            return []

        normalized: dict[str, bytes | str] = {}
        for path, data in files.items():
            if not isinstance(path, str) or not path:
                continue
            if isinstance(data, (bytes, str)):
                normalized[path] = data
        return compute_payload_manifest(normalized)

