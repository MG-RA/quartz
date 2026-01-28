"""
Legacy compatibility helpers (bounded migration window).

The artifact ledger is the long-term spine. During migration, legacy logs may
coexist; migration should be explicit and logged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def legacy_paths(vault_path: Path) -> dict[str, Path]:
    """Return known legacy log paths under .irrev."""
    irrev_dir = vault_path.parent / ".irrev"
    return {
        "ledger_jsonl": irrev_dir / "ledger.jsonl",
        "audit_log": irrev_dir / "audit.log",
        "events_log": irrev_dir / "events.log",
        "artifact_jsonl": irrev_dir / "artifact.jsonl",
    }


def migration_report(*, migrated: int, skipped: int, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "migrated": int(migrated),
        "skipped": int(skipped),
        "errors": errors or [],
    }

