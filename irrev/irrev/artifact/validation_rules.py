"""
Validation rule registry with severity levels.

This module defines validation rules for both vault content and artifact system types.
Rules are organized by scope and severity (WARN/FAIL/ENFORCE).
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class Severity(Enum):
    """Validation severity levels."""

    WARN = "warn"  # Report only, CI passes
    FAIL = "fail"  # Block CI, allow local
    ENFORCE = "enforce"  # Block all execution


# ============================================================================
# VALIDATION RULE REGISTRY
# ============================================================================

VALIDATION_RULES: dict[str, dict[str, Any]] = {
    # ========================================================================
    # VAULT CONTENT RULES
    # ========================================================================
    "vault.concept.missing_frontmatter": {
        "description": "Concept note missing required YAML frontmatter",
        "severity": Severity.FAIL,
        "scope": "vault:concept",
        "applies_to": ["content/concepts/*.md"],
        "check": "has_frontmatter",
        "required_keys": ["role", "layer", "canonical"],
    },
    "vault.concept.invalid_layer": {
        "description": "Concept layer not in allowed set",
        "severity": Severity.FAIL,
        "scope": "vault:concept",
        "check": "frontmatter_enum",
        "field": "layer",
        "allowed_values": [
            "primitive",
            "first-order",
            "mechanism",
            "accounting",
            "selector",
            "foundational",
            "failure-state",
            "meta-analytical",
        ],
    },
    "vault.concept.layer_dependency_violation": {
        "description": "Primitive concept depends on non-primitive (layer violation)",
        "severity": Severity.WARN,
        "scope": "vault:concept",
        "check": "layer_dependencies_valid",
        "rationale": "Primitives should be foundational; cross-layer deps create coupling",
    },
    "vault.diagnostic.missing_role": {
        "description": "Diagnostic note missing 'role: diagnostic' in frontmatter",
        "severity": Severity.FAIL,
        "scope": "vault:diagnostic",
        "check": "frontmatter_literal",
        "field": "role",
        "expected": "diagnostic",
    },
    "vault.template.missing_frontmatter": {
        "description": "Template missing example frontmatter (templates must show structure)",
        "severity": Severity.FAIL,
        "scope": "vault:template",
        "check": "has_frontmatter",
    },
    "vault.export.not_ignored": {
        "description": "Export file not in .gitignore (exports should be ephemeral)",
        "severity": Severity.WARN,
        "scope": "vault:export",
        "check": "gitignored",
        "rationale": "Exports are regenerable; committing them creates diff noise",
    },
    "vault.ruleset.invalid_schema": {
        "description": "Ruleset TOML does not match RulesetSchema",
        "severity": Severity.ENFORCE,
        "scope": "vault:ruleset",
        "check": "toml_schema_valid",
        "schema": "constraints.schema.RulesetSchema",
        "rationale": "Invalid rulesets cannot be loaded by constraint engine",
    },
    "vault.config.malformed_yaml": {
        "description": "YAML config file malformed (parse error)",
        "severity": Severity.ENFORCE,
        "scope": "vault:config",
        "check": "yaml_parseable",
    },
    # ========================================================================
    # ARTIFACT SYSTEM RULES
    # ========================================================================
    "artifact.plan.validation_failed": {
        "description": "Plan artifact failed type pack validation",
        "severity": Severity.ENFORCE,
        "scope": "artifact:plan",
        "check": "type_pack_valid",
        "rationale": "Plans with invalid schema cannot be executed",
    },
    "artifact.approval.validation_failed": {
        "description": "Approval artifact failed type pack validation",
        "severity": Severity.ENFORCE,
        "scope": "artifact:approval",
        "check": "type_pack_valid",
    },
    "artifact.bundle.validation_failed": {
        "description": "Bundle artifact failed type pack validation",
        "severity": Severity.ENFORCE,
        "scope": "artifact:bundle",
        "check": "type_pack_valid",
    },
    "artifact.missing_created_event": {
        "description": "Artifact has no artifact.created event (orphaned artifact_id)",
        "severity": Severity.ENFORCE,
        "scope": "artifact:*",
        "check": "has_event",
        "event_type": "artifact.created",
        "rationale": "All artifacts must have creation event for provenance",
    },
    "artifact.missing_validated_event": {
        "description": "Artifact with type pack has no artifact.validated event",
        "severity": Severity.ENFORCE,
        "scope": "artifact:plan|approval|bundle",
        "check": "has_event",
        "event_type": "artifact.validated",
        "rationale": "Type pack artifacts must be validated before approval/execution",
    },
    "artifact.destructive_missing_approval": {
        "description": "Destructive plan executed without approval",
        "severity": Severity.ENFORCE,
        "scope": "artifact:plan",
        "check": "approval_required",
        "risk_classes": ["mutation_destructive", "external_side_effect"],
        "rationale": "Destructive operations require explicit approval (governance invariant)",
    },
    "artifact.destructive_missing_force_ack": {
        "description": "Destructive plan approved without force_ack=true",
        "severity": Severity.ENFORCE,
        "scope": "artifact:approval",
        "check": "force_ack_required",
        "rationale": "Destructive approvals require explicit acknowledgement",
    },
    "artifact.executed_missing_result": {
        "description": "Executed plan has no result_artifact_id",
        "severity": Severity.FAIL,
        "scope": "artifact:plan",
        "check": "has_result_artifact",
        "rationale": "Interface invariance: executions emit result artifacts",
    },
    "artifact.executed_missing_surface": {
        "description": "Executed plan has no surface attribution (cli/mcp/lsp/ci)",
        "severity": Severity.FAIL,
        "scope": "artifact:plan",
        "check": "has_surface_attribution",
        "rationale": "Interface invariance: different transports must leave same attribution trail",
    },
    # ========================================================================
    # CROSS-SYSTEM RULES
    # ========================================================================
    "cross.vault_references_missing_artifact": {
        "description": "Vault note references artifact_id that doesn't exist",
        "severity": Severity.WARN,
        "scope": "vault:*",
        "check": "artifact_references_valid",
        "rationale": "Broken references indicate stale content or missing artifacts",
    },
    "cross.artifact_references_missing_vault_note": {
        "description": "Artifact references vault note that doesn't exist (broken wiki-link)",
        "severity": Severity.WARN,
        "scope": "artifact:*",
        "check": "vault_references_valid",
    },
}


# ============================================================================
# QUERY FUNCTIONS
# ============================================================================


def get_rules_for_scope(scope: str) -> list[dict[str, Any]]:
    """Get all validation rules for a given scope (e.g., 'vault:concept')."""
    return [
        {**rule, "rule_id": rule_id}
        for rule_id, rule in VALIDATION_RULES.items()
        if _scope_matches(rule["scope"], scope)
    ]


def get_rules_by_severity(severity: Severity) -> list[dict[str, Any]]:
    """Get all validation rules at a given severity level."""
    return [
        {**rule, "rule_id": rule_id}
        for rule_id, rule in VALIDATION_RULES.items()
        if rule["severity"] == severity
    ]


def _scope_matches(rule_scope: str, target_scope: str) -> bool:
    """Check if rule scope matches target scope (supports wildcards)."""
    if rule_scope == target_scope:
        return True
    if rule_scope.endswith(":*"):
        prefix = rule_scope[:-2]
        return target_scope.startswith(prefix + ":")
    if "|" in rule_scope:
        return target_scope in rule_scope.split("|")
    return False
