"""
Audit log infrastructure for erasure cost accounting.

Per the Irreversibility invariant: "Erasure costs must be declared;
rollback cannot be assumed; accounting is mandatory."

This module provides:
- Structured logging of state-changing operations
- Transformation space tracking (before/after)
- Erasure cost summaries
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ErasureCost:
    """Summary of what was erased in an operation."""
    notes: int = 0
    edges: int = 0
    files: int = 0
    bytes_erased: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CreationSummary:
    """Summary of what was created in an operation."""
    notes: int = 0
    edges: int = 0
    files: int = 0
    bytes_written: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: str
    operation: str
    erased: ErasureCost
    created: CreationSummary
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "erased": asdict(self.erased),
            "created": asdict(self.created),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        """Create from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            operation=data["operation"],
            erased=ErasureCost(**data.get("erased", {})),
            created=CreationSummary(**data.get("created", {})),
            metadata=data.get("metadata", {}),
        )


def get_audit_log_path(vault_path: Path) -> Path:
    """Get the path to the audit log file."""
    irrev_dir = vault_path.parent / ".irrev"
    return irrev_dir / "audit.log"


def ensure_audit_dir(vault_path: Path) -> Path:
    """Ensure the .irrev directory exists and return audit log path."""
    log_path = get_audit_log_path(vault_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def log_operation(
    vault_path: Path,
    operation: str,
    erased: ErasureCost | None = None,
    created: CreationSummary | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEntry:
    """
    Log an operation to the audit log.

    Args:
        vault_path: Path to the vault content directory
        operation: Name of the operation (e.g., "neo4j-rebuild", "registry-in-place")
        erased: Summary of what was erased
        created: Summary of what was created
        metadata: Additional context (e.g., target database, file paths)

    Returns:
        The created audit entry
    """
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        operation=operation,
        erased=erased or ErasureCost(),
        created=created or CreationSummary(),
        metadata=metadata or {},
    )

    log_path = ensure_audit_dir(vault_path)

    # Append as JSON Lines format (one JSON object per line)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry.to_dict()) + "\n")

    return entry


def read_audit_log(vault_path: Path, last_n: int | None = None) -> list[AuditEntry]:
    """
    Read entries from the audit log.

    Args:
        vault_path: Path to the vault content directory
        last_n: If specified, return only the last N entries

    Returns:
        List of audit entries (oldest first unless last_n specified)
    """
    log_path = get_audit_log_path(vault_path)
    if not log_path.exists():
        return []

    entries = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    entries.append(AuditEntry.from_dict(data))
                except json.JSONDecodeError:
                    continue  # Skip malformed lines

    if last_n is not None:
        return entries[-last_n:]
    return entries


def format_audit_entry(entry: AuditEntry) -> str:
    """Format an audit entry for human-readable display."""
    lines = [
        f"[{entry.timestamp}] {entry.operation}",
    ]

    if entry.erased.notes or entry.erased.edges or entry.erased.files:
        erased_parts = []
        if entry.erased.notes:
            erased_parts.append(f"{entry.erased.notes} notes")
        if entry.erased.edges:
            erased_parts.append(f"{entry.erased.edges} edges")
        if entry.erased.files:
            erased_parts.append(f"{entry.erased.files} files")
        lines.append(f"  Erased: {', '.join(erased_parts)}")

    if entry.created.notes or entry.created.edges or entry.created.files:
        created_parts = []
        if entry.created.notes:
            created_parts.append(f"{entry.created.notes} notes")
        if entry.created.edges:
            created_parts.append(f"{entry.created.edges} edges")
        if entry.created.files:
            created_parts.append(f"{entry.created.files} files")
        lines.append(f"  Created: {', '.join(created_parts)}")

    if entry.metadata:
        for key, value in entry.metadata.items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)
