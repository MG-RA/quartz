"""
Tests for artifact type system (Phase 1: Discovery & Inventory).

These tests verify:
- Vault type registry loading
- Artifact type metadata
- Type inference from file paths
- Basic validation
"""

from pathlib import Path

import pytest

from irrev.artifact.types import (
    ARTIFACT_TYPE_METADATA,
    get_type_metadata,
    has_type_pack,
    list_artifact_types,
)
from irrev.artifact.validation_rules import (
    VALIDATION_RULES,
    Severity,
    get_rules_by_severity,
    get_rules_for_scope,
)
from irrev.artifact.vault_types import (
    get_vault_type,
    infer_vault_type,
    load_vault_type_registry,
    validate_vault_artifact,
)


# ============================================================================
# ARTIFACT TYPE REGISTRY TESTS
# ============================================================================


def test_artifact_type_metadata_exists():
    """Artifact type metadata registry is populated."""
    assert len(ARTIFACT_TYPE_METADATA) > 0
    assert "plan" in ARTIFACT_TYPE_METADATA
    assert "approval" in ARTIFACT_TYPE_METADATA
    assert "bundle" in ARTIFACT_TYPE_METADATA


def test_get_type_metadata():
    """get_type_metadata returns metadata for artifact types."""
    plan_meta = get_type_metadata("plan")
    assert plan_meta is not None
    assert plan_meta["description"] == "Execution plan with operation + payload + inputs"
    assert plan_meta["linkable"] is True
    assert plan_meta["requires_envelope"] is True

    # Case insensitive
    assert get_type_metadata("PLAN") == plan_meta
    assert get_type_metadata("  plan  ") == plan_meta


def test_list_artifact_types():
    """list_artifact_types returns sorted list of types."""
    types = list_artifact_types()
    assert len(types) > 0
    assert "plan" in types
    assert "approval" in types
    assert types == sorted(types)  # Should be sorted


def test_has_type_pack():
    """has_type_pack correctly identifies types with validation packs."""
    assert has_type_pack("plan") is True
    assert has_type_pack("approval") is True
    assert has_type_pack("bundle") is True
    assert has_type_pack("execution_summary") is False
    assert has_type_pack("lint_report") is False


# ============================================================================
# VALIDATION RULES TESTS
# ============================================================================


def test_validation_rules_exist():
    """Validation rules registry is populated."""
    assert len(VALIDATION_RULES) > 0
    assert "vault.concept.missing_frontmatter" in VALIDATION_RULES
    assert "artifact.plan.validation_failed" in VALIDATION_RULES


def test_get_rules_for_scope():
    """get_rules_for_scope filters by scope pattern."""
    concept_rules = get_rules_for_scope("vault:concept")
    assert len(concept_rules) > 0
    assert all("vault:concept" in r["scope"] or r["scope"] == "vault:*" for r in concept_rules)

    plan_rules = get_rules_for_scope("artifact:plan")
    assert len(plan_rules) > 0
    assert all(
        "artifact:plan" in r["scope"] or r["scope"] == "artifact:*" for r in plan_rules
    )


def test_get_rules_by_severity():
    """get_rules_by_severity filters by severity level."""
    enforce_rules = get_rules_by_severity(Severity.ENFORCE)
    assert len(enforce_rules) > 0
    assert all(r["severity"] == Severity.ENFORCE for r in enforce_rules)

    fail_rules = get_rules_by_severity(Severity.FAIL)
    assert len(fail_rules) > 0
    assert all(r["severity"] == Severity.FAIL for r in fail_rules)


# ============================================================================
# VAULT TYPE REGISTRY TESTS
# ============================================================================


def test_load_vault_type_registry(tmp_path: Path):
    """load_vault_type_registry parses TOML correctly."""
    registry_file = tmp_path / "artifact-types.toml"
    registry_file.write_text(
        """
registry_version = 1
description = "Test registry"

[[types]]
type_id = "vault:test"
description = "Test type"

[types.locations]
allowed_patterns = ["test/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role"]

[types.governance]
linkable = false
requires_envelope = false
"""
    )

    registry = load_vault_type_registry(registry_file)
    assert registry["registry_version"] == 1
    assert len(registry["types"]) == 1
    assert registry["types"][0]["type_id"] == "vault:test"


def test_load_vault_type_registry_missing_file(tmp_path: Path):
    """load_vault_type_registry raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_vault_type_registry(tmp_path / "nonexistent.toml")


def test_get_vault_type(tmp_path: Path):
    """get_vault_type retrieves type definition by type_id."""
    registry_file = tmp_path / "artifact-types.toml"
    registry_file.write_text(
        """
registry_version = 1

[[types]]
type_id = "vault:concept"
description = "Concept definition"

[[types]]
type_id = "vault:diagnostic"
description = "Diagnostic tool"
"""
    )

    registry = load_vault_type_registry(registry_file)
    concept = get_vault_type(registry, "vault:concept")
    assert concept is not None
    assert concept["description"] == "Concept definition"

    diagnostic = get_vault_type(registry, "vault:diagnostic")
    assert diagnostic is not None
    assert diagnostic["description"] == "Diagnostic tool"

    missing = get_vault_type(registry, "vault:missing")
    assert missing is None


def test_infer_vault_type(tmp_path: Path):
    """infer_vault_type matches file paths to type patterns."""
    registry_file = tmp_path / "artifact-types.toml"
    registry_file.write_text(
        """
registry_version = 1

[[types]]
type_id = "vault:concept"
description = "Concept"

[types.locations]
allowed_patterns = ["content/concepts/*.md"]
allowed_extensions = [".md"]

[[types]]
type_id = "vault:diagnostic"
description = "Diagnostic"

[types.locations]
allowed_patterns = ["content/diagnostics/**/*.md"]
allowed_extensions = [".md"]
"""
    )

    registry = load_vault_type_registry(registry_file)

    # Create vault structure
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    (vault_root / "content" / "concepts").mkdir(parents=True)
    (vault_root / "content" / "diagnostics").mkdir(parents=True)

    concept_file = vault_root / "content" / "concepts" / "irreversibility.md"
    concept_file.touch()

    diagnostic_file = vault_root / "content" / "diagnostics" / "failure-modes.md"
    diagnostic_file.touch()

    # Test inference
    concept_type = infer_vault_type(registry, concept_file, vault_root)
    assert concept_type == "vault:concept"

    diagnostic_type = infer_vault_type(registry, diagnostic_file, vault_root)
    assert diagnostic_type == "vault:diagnostic"

    # Non-matching file
    other_file = vault_root / "content" / "other.md"
    other_file.touch()
    other_type = infer_vault_type(registry, other_file, vault_root)
    assert other_type is None


def test_validate_vault_artifact_missing_frontmatter(tmp_path: Path):
    """validate_vault_artifact detects missing required frontmatter."""
    type_def = {
        "type_id": "vault:concept",
        "types": {
            "locations": {"allowed_extensions": [".md"]},
            "metadata": {"required": ["role", "layer"]},
            "governance": {"requires_frontmatter": True},
        },
    }

    # Create markdown file without frontmatter
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n\nNo frontmatter here.")

    errors = validate_vault_artifact(md_file, type_def)
    assert len(errors) > 0
    assert any("Missing required frontmatter" in e for e in errors)


def test_validate_vault_artifact_valid_frontmatter(tmp_path: Path):
    """validate_vault_artifact passes with valid frontmatter."""
    type_def = {
        "type_id": "vault:concept",
        "types": {
            "locations": {"allowed_extensions": [".md"]},
            "metadata": {
                "required": ["role", "layer"],
                "constraints": {
                    "role": {"type": "literal", "value": "concept"},
                    "layer": {"type": "enum", "values": ["primitive", "first-order"]},
                },
            },
            "governance": {"requires_frontmatter": True},
        },
    }

    # Create markdown file with valid frontmatter
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """---
role: concept
layer: primitive
---

# Test Concept
"""
    )

    errors = validate_vault_artifact(md_file, type_def)
    assert len(errors) == 0


def test_validate_vault_artifact_invalid_enum(tmp_path: Path):
    """validate_vault_artifact detects invalid enum values."""
    type_def = {
        "type_id": "vault:concept",
        "types": {
            "locations": {"allowed_extensions": [".md"]},
            "metadata": {
                "required": ["role", "layer"],
                "constraints": {
                    "role": {"type": "literal", "value": "concept"},
                    "layer": {"type": "enum", "values": ["primitive", "first-order"]},
                },
            },
            "governance": {"requires_frontmatter": True},
        },
    }

    # Create markdown file with invalid layer value
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """---
role: concept
layer: invalid-layer
---

# Test
"""
    )

    errors = validate_vault_artifact(md_file, type_def)
    assert len(errors) > 0
    assert any("must be one of" in e and "invalid-layer" in e for e in errors)
