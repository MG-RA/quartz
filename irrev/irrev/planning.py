"""
Planning infrastructure for decomposition-compliant command execution.

Per the Decomposition invariant: "Objects and operators are separated by role;
role boundaries do not merge incompatible functions."

This module provides:
- Base classes for separating diagnostic (compute) from action (execute) phases
- Plan/Result dataclasses for each command type
- Dry-run capability for all write commands
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, TypeVar

from .audit_log import ErasureCost, CreationSummary, log_operation


# Type variable for plan payloads
T = TypeVar('T')


@dataclass
class BasePlan(ABC):
    """Base class for operation plans (diagnostic output)."""
    vault_path: Path

    @abstractmethod
    def summary(self) -> str:
        """Human-readable summary of what would be done."""
        ...


@dataclass
class BaseResult:
    """Base class for operation results (action output)."""
    erased: ErasureCost = field(default_factory=ErasureCost)
    created: CreationSummary = field(default_factory=CreationSummary)
    success: bool = True
    error: str | None = None

    def log_to_audit(self, vault_path: Path, operation: str, metadata: dict[str, Any] | None = None) -> None:
        """Log this result to the audit trail."""
        log_operation(vault_path, operation, self.erased, self.created, metadata or {})


# Neo4j Load Plan/Result
@dataclass
class Neo4jLoadPlan(BasePlan):
    """Plan for neo4j load operation."""
    mode: str  # "sync" or "rebuild"
    database: str
    http_uri: str
    notes: list[dict[str, Any]] = field(default_factory=list)
    links_to: list[tuple[str, str]] = field(default_factory=list)
    depends_on: list[tuple[str, str]] = field(default_factory=list)
    topology_rows: list[dict[str, Any]] = field(default_factory=list)
    existing_node_count: int = 0
    existing_edge_count: int = 0
    unresolved_links: int = 0

    def summary(self) -> str:
        lines = [
            f"Neo4j Load Plan ({self.mode} mode)",
            f"  Target: {self.http_uri} database={self.database}",
            f"  Notes to upsert: {len(self.notes)}",
            f"  LINKS_TO edges: {len(self.links_to)}",
            f"  DEPENDS_ON edges: {len(self.depends_on)}",
            f"  Topology properties: {len(self.topology_rows)} concepts",
        ]
        if self.mode == "rebuild":
            lines.append(f"  [DESTRUCTIVE] Will erase: {self.existing_node_count} nodes, {self.existing_edge_count} edges")
        if self.unresolved_links:
            lines.append(f"  Unresolved links (skipped): {self.unresolved_links}")
        return "\n".join(lines)


@dataclass
class Neo4jLoadResult(BaseResult):
    """Result of neo4j load execution."""
    notes_loaded: int = 0
    edges_created: int = 0


# Registry Build Plan/Result
@dataclass
class RegistryBuildPlan(BasePlan):
    """Plan for registry build operation."""
    in_place: bool
    target_path: Path | None
    tables_content: str = ""
    existing_content: str = ""
    updated_content: str = ""

    def summary(self) -> str:
        lines = [
            f"Registry Build Plan",
            f"  Mode: {'in-place update' if self.in_place else 'generate new'}",
        ]
        if self.target_path:
            lines.append(f"  Target: {self.target_path}")
        if self.in_place and self.existing_content:
            existing_len = len(self.existing_content.encode("utf-8"))
            updated_len = len(self.updated_content.encode("utf-8"))
            lines.append(f"  Size change: {existing_len} -> {updated_len} bytes")
        return "\n".join(lines)


@dataclass
class RegistryBuildResult(BaseResult):
    """Result of registry build execution."""
    output_path: Path | None = None


# Neo4j Export Plan/Result
@dataclass
class Neo4jExportPlan(BasePlan):
    """Plan for neo4j export operation."""
    out_dir: Path
    queries: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    include_mentions: bool = False
    include_ghost_terms: bool = False
    include_definition_tokens: bool = False
    requires_vault_reread: bool = False

    def summary(self) -> str:
        lines = [
            f"Neo4j Export Plan",
            f"  Output directory: {self.out_dir}",
            f"  Queries to execute: {len(self.queries)}",
            f"  Output files: {len(self.output_files)}",
        ]
        if self.requires_vault_reread:
            reasons = []
            if self.include_mentions:
                reasons.append("mentions")
            if self.include_ghost_terms:
                reasons.append("ghost terms")
            if self.include_definition_tokens:
                reasons.append("definition tokens")
            lines.append(f"  [VAULT RE-READ] Required for: {', '.join(reasons)}")
        return "\n".join(lines)


@dataclass
class Neo4jExportResult(BaseResult):
    """Result of neo4j export execution."""
    files_written: int = 0
    bytes_written: int = 0


# Generic Write Plan/Result for simple file operations
@dataclass
class FileWritePlan(BasePlan):
    """Plan for a file write operation."""
    output_path: Path
    content: str = ""

    def summary(self) -> str:
        return f"File Write Plan\n  Target: {self.output_path}\n  Size: {len(self.content.encode('utf-8'))} bytes"


@dataclass
class FileWriteResult(BaseResult):
    """Result of file write execution."""
    path: Path | None = None
    bytes_written: int = 0
