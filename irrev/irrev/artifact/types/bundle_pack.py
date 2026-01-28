"""
Type pack for bundle@v1 artifacts.

Bundles are compact proof packs that reference the full artifact chain:
plan → approval → result

They include a repro header for reproducibility:
- rulesets used
- surface (cli/mcp/lsp/ci)
- engine version
- environment fingerprint
"""

from __future__ import annotations

from typing import Any


class BundleTypePack:
    """
    Type pack for bundle@v1 artifacts.

    Bundles are ~100 bytes (references only). The full proof chain
    is reconstructable from the ledger using the artifact IDs.
    """

    def validate(self, content: dict[str, Any]) -> list[str]:
        """
        Validate bundle content structure.

        Required fields:
        - version: must be "bundle@v1"
        - operation: non-empty string
        - timestamp: ISO timestamp
        - artifacts.plan: plan artifact ID
        - artifacts.result: result artifact ID
        - repro.surface: calling surface
        - repro.engine_version: engine version string
        """
        errors: list[str] = []

        # Version check
        version = content.get("version")
        if version != "bundle@v1":
            errors.append(f"version must be 'bundle@v1', got {version!r}")

        # Operation check
        operation = content.get("operation")
        if not isinstance(operation, str) or not operation.strip():
            errors.append("operation must be a non-empty string")

        # Timestamp check
        timestamp = content.get("timestamp")
        if not isinstance(timestamp, str) or not timestamp.strip():
            errors.append("timestamp must be a non-empty ISO timestamp")

        # Artifacts check
        artifacts = content.get("artifacts")
        if not isinstance(artifacts, dict):
            errors.append("artifacts must be an object")
        else:
            if not artifacts.get("plan"):
                errors.append("artifacts.plan is required")
            if not artifacts.get("result"):
                errors.append("artifacts.result is required")
            # approval can be None for low-risk operations

        # Repro header check
        repro = content.get("repro")
        if not isinstance(repro, dict):
            errors.append("repro must be an object")
        else:
            if not repro.get("surface"):
                errors.append("repro.surface is required")
            if not repro.get("engine_version"):
                errors.append("repro.engine_version is required")

        return errors

    def extract_inputs(self, content: dict[str, Any]) -> list[dict[str, str]]:
        """
        Extract input artifact references from bundle content.

        Returns list of {artifact_id, content_id} dicts for:
        - plan artifact
        - approval artifact (if present)
        - result artifact
        """
        artifacts = content.get("artifacts", {})
        inputs: list[dict[str, str]] = []

        for key in ("plan", "approval", "result"):
            artifact_id = artifacts.get(key)
            if isinstance(artifact_id, str) and artifact_id.strip():
                inputs.append({"artifact_id": artifact_id, "content_id": ""})

        return inputs

    def compute_payload_manifest(self, content: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Compute payload manifest for bundle.

        Bundles don't have file payloads - they're just references.
        Returns empty list.
        """
        return []
