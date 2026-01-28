"""
Vault type registry loader and validator.

Loads vault-owned artifact-types.toml and provides validation for vault content.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

import frontmatter


# ============================================================================
# VAULT TYPE REGISTRY LOADING
# ============================================================================


def load_vault_type_registry(registry_path: str | Path) -> dict[str, Any]:
    """
    Load vault type registry from TOML file.

    Args:
        registry_path: Path to artifact-types.toml

    Returns:
        Parsed registry dict with 'types' list and metadata

    Raises:
        FileNotFoundError: If registry file not found
        ValueError: If TOML is malformed
    """
    path = Path(registry_path)
    if not path.exists():
        raise FileNotFoundError(f"Vault type registry not found: {path}")

    with open(path, "rb") as f:
        try:
            registry = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse registry TOML: {e}") from e

    if "types" not in registry:
        raise ValueError("Registry missing 'types' key")

    return registry


def get_vault_type(registry: dict[str, Any], type_id: str) -> dict[str, Any] | None:
    """
    Get vault type definition by type_id.

    Args:
        registry: Loaded registry dict
        type_id: Type identifier (e.g., 'vault:concept')

    Returns:
        Type definition dict or None if not found
    """
    for type_def in registry.get("types", []):
        if type_def.get("type_id") == type_id:
            return type_def
    return None


def infer_vault_type(
    registry: dict[str, Any], file_path: str | Path, vault_root: str | Path
) -> str | None:
    """
    Infer vault type from file path by matching location patterns.

    Args:
        registry: Loaded registry dict
        file_path: Path to file to classify
        vault_root: Root of vault directory

    Returns:
        type_id (e.g., 'vault:concept') or None if no match
    """
    path = Path(file_path)
    root = Path(vault_root)

    try:
        rel_path = path.relative_to(root)
    except ValueError:
        return None

    rel_path_str = rel_path.as_posix()

    for type_def in registry.get("types", []):
        locations = type_def.get("types", {}).get("locations", {})
        allowed_patterns = locations.get("allowed_patterns", [])
        forbidden_patterns = locations.get("forbidden_patterns", [])

        # Check forbidden patterns first
        if any(fnmatch.fnmatch(rel_path_str, pattern) for pattern in forbidden_patterns):
            continue

        # Check allowed patterns
        if any(fnmatch.fnmatch(rel_path_str, pattern) for pattern in allowed_patterns):
            return type_def.get("type_id")

    return None


# ============================================================================
# VAULT ARTIFACT VALIDATION
# ============================================================================


def validate_vault_artifact(
    file_path: str | Path, type_def: dict[str, Any]
) -> list[str]:
    """
    Validate a vault artifact against its type definition.

    Args:
        file_path: Path to markdown/TOML/YAML file
        type_def: Type definition dict from registry

    Returns:
        List of error strings (empty = valid)
    """
    errors: list[str] = []
    path = Path(file_path)

    if not path.exists():
        return [f"File not found: {path}"]

    type_id = type_def.get("type_id", "unknown")
    governance = type_def.get("types", {}).get("governance", {})
    metadata_def = type_def.get("types", {}).get("metadata", {})
    requires_frontmatter = governance.get("requires_frontmatter", True)

    # Check file extension
    allowed_extensions = type_def.get("types", {}).get("locations", {}).get("allowed_extensions", [])
    if allowed_extensions and path.suffix not in allowed_extensions:
        errors.append(
            f"{type_id}: Invalid extension '{path.suffix}', expected one of {allowed_extensions}"
        )

    # Skip frontmatter checks for non-markdown files
    if path.suffix == ".md":
        errors.extend(_validate_frontmatter(path, type_id, metadata_def, requires_frontmatter))

    return errors


def _validate_frontmatter(
    path: Path, type_id: str, metadata_def: dict[str, Any], required: bool
) -> list[str]:
    """Validate YAML frontmatter in markdown file."""
    errors: list[str] = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
    except Exception as e:
        if required:
            return [f"{type_id}: Failed to parse frontmatter: {e}"]
        return []

    fm = post.metadata

    if not fm and required:
        errors.append(f"{type_id}: Missing required frontmatter")
        return errors

    if not fm:
        return []

    # Check required fields
    required_fields = metadata_def.get("required", [])
    for field in required_fields:
        if field not in fm:
            errors.append(f"{type_id}: Missing required frontmatter field '{field}'")

    # Validate field constraints
    constraints = metadata_def.get("constraints", {})
    for field, constraint in constraints.items():
        if field not in fm:
            continue  # Only validate if present

        value = fm[field]
        constraint_type = constraint.get("type")

        if constraint_type == "literal":
            expected = constraint.get("value")
            if value != expected:
                errors.append(
                    f"{type_id}: Field '{field}' must be '{expected}', got '{value}'"
                )

        elif constraint_type == "enum":
            allowed = constraint.get("values", [])
            if value not in allowed:
                errors.append(
                    f"{type_id}: Field '{field}' must be one of {allowed}, got '{value}'"
                )

        elif constraint_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"{type_id}: Field '{field}' must be boolean, got {type(value).__name__}")

        elif constraint_type == "string":
            if not isinstance(value, str):
                errors.append(f"{type_id}: Field '{field}' must be string, got {type(value).__name__}")

        elif constraint_type == "integer":
            if not isinstance(value, int):
                errors.append(f"{type_id}: Field '{field}' must be integer, got {type(value).__name__}")

        elif constraint_type == "list":
            if not isinstance(value, list):
                errors.append(f"{type_id}: Field '{field}' must be list, got {type(value).__name__}")
            else:
                # Check list item types if specified
                item_type = constraint.get("item_type")
                if item_type == "string":
                    for i, item in enumerate(value):
                        if not isinstance(item, str):
                            errors.append(
                                f"{type_id}: Field '{field}[{i}]' must be string, got {type(item).__name__}"
                            )

                # Check allowed values for list items
                allowed = constraint.get("allowed")
                if allowed:
                    for item in value:
                        if item not in allowed:
                            errors.append(
                                f"{type_id}: Field '{field}' contains invalid value '{item}', allowed: {allowed}"
                            )

    return errors


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def validate_vault_file(
    file_path: str | Path, vault_root: str | Path, registry_path: str | Path
) -> tuple[str | None, list[str]]:
    """
    Validate a vault file by inferring its type and checking against registry.

    Args:
        file_path: Path to file to validate
        vault_root: Root of vault directory
        registry_path: Path to artifact-types.toml

    Returns:
        (type_id, errors) tuple
        - type_id: Inferred type or None if no match
        - errors: List of validation errors (empty = valid)
    """
    try:
        registry = load_vault_type_registry(registry_path)
    except (FileNotFoundError, ValueError) as e:
        return (None, [f"Registry error: {e}"])

    type_id = infer_vault_type(registry, file_path, vault_root)
    if type_id is None:
        return (None, [])  # No type match, not an error

    type_def = get_vault_type(registry, type_id)
    if type_def is None:
        return (type_id, [f"Type definition not found: {type_id}"])

    errors = validate_vault_artifact(file_path, type_def)
    return (type_id, errors)
