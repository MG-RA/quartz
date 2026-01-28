"""
CLI commands for artifact type system introspection and validation.

Commands:
- irrev artifact types        - List all registered types
- irrev artifact type-check   - Validate files against type registry
- irrev artifact type-info    - Show detailed info for one type
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ..artifact.types import (
    ARTIFACT_TYPE_METADATA,
    get_type_metadata,
    has_type_pack,
    list_artifact_types,
)
from ..artifact.validation_rules import VALIDATION_RULES, Severity, get_rules_for_scope
from ..artifact.vault_types import (
    get_vault_type,
    infer_vault_type,
    load_vault_type_registry,
    validate_vault_artifact,
)

console = Console()
err = Console(stderr=True)


# ============================================================================
# irrev artifact types
# ============================================================================


def run_artifact_types_list(vault_path: str, json_output: bool = False) -> int:
    """
    List all registered artifact types (vault + artifact system).

    Args:
        vault_path: Path to vault root
        json_output: Output as JSON

    Returns:
        Exit code (0 = success)
    """
    import json

    vault_root = Path(vault_path)
    registry_path = vault_root / "content" / "meta" / "artifact-types.toml"

    # Load vault types
    vault_types: list[dict[str, Any]] = []
    if registry_path.exists():
        try:
            registry = load_vault_type_registry(registry_path)
            vault_types = registry.get("types", [])
        except Exception as e:
            err.print(f"Warning: Failed to load vault type registry: {e}", style="yellow")

    # Load artifact system types
    artifact_types = list_artifact_types()

    if json_output:
        output = {
            "vault_types": [
                {
                    "type_id": t.get("type_id"),
                    "description": t.get("description"),
                    "linkable": t.get("types", {}).get("governance", {}).get("linkable", False),
                    "requires_envelope": t.get("types", {})
                    .get("governance", {})
                    .get("requires_envelope", False),
                }
                for t in vault_types
            ],
            "artifact_types": [
                {
                    "type_id": type_id,
                    "description": ARTIFACT_TYPE_METADATA[type_id]["description"],
                    "linkable": ARTIFACT_TYPE_METADATA[type_id]["linkable"],
                    "requires_envelope": ARTIFACT_TYPE_METADATA[type_id]["requires_envelope"],
                    "has_type_pack": has_type_pack(type_id),
                }
                for type_id in artifact_types
            ],
        }
        print(json.dumps(output, indent=2))
        return 0

    # Table output
    table = Table(title="Artifact Types Registry")
    table.add_column("Type ID", style="cyan")
    table.add_column("Description")
    table.add_column("Linkable")
    table.add_column("Envelope")
    table.add_column("Type Pack")

    # Vault types
    for t in vault_types:
        governance = t.get("types", {}).get("governance", {})
        table.add_row(
            t.get("type_id", "?"),
            t.get("description", ""),
            "Yes" if governance.get("linkable") else "No",
            "Yes" if governance.get("requires_envelope") else "No",
            "-",
            style="dim",
        )

    # Artifact system types
    for type_id in artifact_types:
        meta = ARTIFACT_TYPE_METADATA[type_id]
        table.add_row(
            type_id,
            meta["description"],
            "Yes" if meta["linkable"] else "No",
            "Yes" if meta["requires_envelope"] else "No",
            "Yes" if has_type_pack(type_id) else "No",
        )

    console.print(table)
    console.print(
        f"\n[dim]Total: {len(vault_types)} vault types, {len(artifact_types)} artifact types[/dim]"
    )
    return 0


# ============================================================================
# irrev artifact type-check
# ============================================================================


def run_artifact_type_check(
    vault_path: str,
    path: str,
    severity_filter: str = "all",
    json_output: bool = False,
) -> int:
    """
    Dry-run validation on file or directory.

    Args:
        vault_path: Path to vault root
        path: Path to file or directory to check
        severity_filter: Filter by severity (warn|fail|enforce|all)
        json_output: Output as JSON

    Returns:
        Exit code (0 = success, 1 = violations found)
    """
    import json

    vault_root = Path(vault_path)
    registry_path = vault_root / "content" / "meta" / "artifact-types.toml"
    target = Path(path)

    if not target.exists():
        err.print(f"Path not found: {target}", style="bold red")
        return 1

    # Load registry
    try:
        registry = load_vault_type_registry(registry_path)
    except Exception as e:
        err.print(f"Failed to load vault type registry: {e}", style="bold red")
        return 1

    # Collect files to check
    files = []
    if target.is_file():
        files = [target]
    else:
        files = list(target.rglob("*.md")) + list(target.rglob("*.toml")) + list(target.rglob("*.y*ml"))

    # Validate each file
    results: dict[str, Any] = {}
    total_violations = 0

    for file in files:
        type_id = infer_vault_type(registry, file, vault_root)
        if type_id is None:
            continue  # No type match, skip

        type_def = get_vault_type(registry, type_id)
        if type_def is None:
            continue

        errors = validate_vault_artifact(file, type_def)
        if errors:
            results[str(file.relative_to(vault_root))] = {"type": type_id, "errors": errors}
            total_violations += len(errors)

    if json_output:
        print(json.dumps(results, indent=2))
        return 1 if total_violations > 0 else 0

    # Table output
    if not results:
        console.print("[green]✓[/green] No violations found")
        return 0

    console.print(f"\n[yellow]⚠[/yellow] Found {total_violations} violations:\n")

    for file_path, data in results.items():
        console.print(f"[cyan]{file_path}[/cyan] ({data['type']})")
        for error in data["errors"]:
            console.print(f"  [red]✗[/red] {error}")
        console.print()

    return 1


# ============================================================================
# irrev artifact type-info
# ============================================================================


def run_artifact_type_info(vault_path: str, type_id: str, json_output: bool = False) -> int:
    """
    Show detailed info for one artifact type.

    Args:
        vault_path: Path to vault root
        type_id: Type identifier (e.g., 'vault:concept' or 'plan')
        json_output: Output as JSON

    Returns:
        Exit code (0 = success, 1 = type not found)
    """
    import json

    vault_root = Path(vault_path)
    registry_path = vault_root / "content" / "meta" / "artifact-types.toml"

    # Try artifact system type first
    if type_id in ARTIFACT_TYPE_METADATA:
        meta = ARTIFACT_TYPE_METADATA[type_id]

        if json_output:
            output = {
                "type_id": type_id,
                "category": "artifact_system",
                "description": meta["description"],
                "linkable": meta["linkable"],
                "requires_envelope": meta["requires_envelope"],
                "requires_events": meta["requires_events"],
                "may_have_events": meta["may_have_events"],
                "governance_expectations": meta["governance_expectations"],
                "invariants": meta["invariants"],
                "has_type_pack": has_type_pack(type_id),
                "rules": [r for r in get_rules_for_scope(f"artifact:{type_id}")],
            }
            print(json.dumps(output, indent=2))
            return 0

        # Table output
        console.print(f"\n[bold cyan]{type_id}[/bold cyan] (Artifact System Type)\n")
        console.print(f"[dim]Description:[/dim] {meta['description']}")
        console.print(f"[dim]Linkable:[/dim] {meta['linkable']}")
        console.print(f"[dim]Requires Envelope:[/dim] {meta['requires_envelope']}")
        console.print(f"[dim]Has Type Pack:[/dim] {has_type_pack(type_id)}")
        console.print(f"\n[dim]Required Events:[/dim] {', '.join(meta['requires_events'])}")
        console.print(f"[dim]Optional Events:[/dim] {', '.join(meta['may_have_events'])}")
        console.print(
            f"[dim]Governance:[/dim] {', '.join(meta['governance_expectations']) or 'None'}"
        )
        console.print(f"[dim]Invariants:[/dim] {', '.join(meta['invariants']) or 'None'}")

        # Show validation rules
        rules = get_rules_for_scope(f"artifact:{type_id}")
        if rules:
            console.print(f"\n[bold]Validation Rules:[/bold]")
            for rule in rules:
                console.print(
                    f"  [{_severity_color(rule['severity'])}]•[/] {rule['rule_id']}: {rule['description']}"
                )

        return 0

    # Try vault type
    if not registry_path.exists():
        err.print("Vault type registry not found", style="bold red")
        return 1

    try:
        registry = load_vault_type_registry(registry_path)
    except Exception as e:
        err.print(f"Failed to load registry: {e}", style="bold red")
        return 1

    type_def = get_vault_type(registry, type_id)
    if type_def is None:
        err.print(f"Type not found: {type_id}", style="bold red")
        return 1

    if json_output:
        print(json.dumps(type_def, indent=2))
        return 0

    # Table output
    console.print(f"\n[bold cyan]{type_id}[/bold cyan] (Vault Content Type)\n")
    console.print(f"[dim]Description:[/dim] {type_def.get('description', 'N/A')}")

    locations = type_def.get("types", {}).get("locations", {})
    console.print(f"[dim]Allowed Patterns:[/dim] {', '.join(locations.get('allowed_patterns', []))}")

    metadata = type_def.get("types", {}).get("metadata", {})
    console.print(f"[dim]Required Fields:[/dim] {', '.join(metadata.get('required', []))}")
    console.print(f"[dim]Optional Fields:[/dim] {', '.join(metadata.get('optional', []))}")

    governance = type_def.get("types", {}).get("governance", {})
    console.print(f"[dim]Linkable:[/dim] {governance.get('linkable', False)}")
    console.print(f"[dim]Requires Envelope:[/dim] {governance.get('requires_envelope', False)}")
    console.print(
        f"[dim]Invariants:[/dim] {', '.join(governance.get('invariants', [])) or 'None'}"
    )

    # Show validation rules
    rules = get_rules_for_scope(type_id)
    if rules:
        console.print(f"\n[bold]Validation Rules:[/bold]")
        for rule in rules:
            console.print(
                f"  [{_severity_color(rule['severity'])}]•[/] {rule['rule_id']}: {rule['description']}"
            )

    return 0


def _severity_color(severity: Severity) -> str:
    """Get color for severity level."""
    if severity == Severity.ENFORCE:
        return "red"
    elif severity == Severity.FAIL:
        return "yellow"
    else:
        return "dim"
