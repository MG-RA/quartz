"""
Structural event logging for vault drift observation.

Per the Irreversibility invariant: "Persistence must be tracked."

This module provides:
- EventEnvelope dataclass for file system events
- Event classification by scope (vault note, registry, rules, config)
- Append-only event logging to .irrev/events.log
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class EventKind(str, Enum):
    """Types of file system events."""

    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_RENAMED = "file_renamed"


class ArtifactScope(str, Enum):
    """Classification of what kind of artifact changed."""

    VAULT_NOTE = "vault_note"  # .md files in content/
    REGISTRY = "registry"  # Registry.md or registry.overrides.yml
    RULES = "rules"  # vault/rules.py, vault/invariants.py
    CONFIG = "config"  # pyproject.toml, hubs.yml, etc.
    UNKNOWN = "unknown"


@dataclass
class ArtifactMetadata:
    """Metadata about a changed artifact."""

    path: str
    size: int = 0
    hash: str | None = None  # SHA-256 of content (optional)
    role: str | None = None  # Frontmatter role if available
    layer: str | None = None  # Frontmatter layer if available

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        d = {"path": self.path, "size": self.size}
        if self.hash:
            d["hash"] = self.hash
        if self.role:
            d["role"] = self.role
        if self.layer:
            d["layer"] = self.layer
        return d


@dataclass
class ErasureFields:
    """Fields specific to deletion events (erasure accounting)."""

    bytes_erased: int = 0
    was_canonical: bool = False  # Was this a canonical definition?
    dependents_affected: int = 0  # How many notes depended on this?

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EventEnvelope:
    """A single file system event with full context."""

    timestamp: str
    event_kind: EventKind
    scope: ArtifactScope
    artifact: ArtifactMetadata
    erasure: ErasureFields | None = None  # Only for deletions
    rename_from: str | None = None  # Original path for renames
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = {
            "timestamp": self.timestamp,
            "event_kind": self.event_kind.value,
            "scope": self.scope.value,
            "artifact": self.artifact.to_dict(),
        }
        if self.erasure:
            d["erasure"] = self.erasure.to_dict()
        if self.rename_from:
            d["rename_from"] = self.rename_from
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "EventEnvelope":
        """Create from dictionary."""
        artifact_data = data.get("artifact", {})
        erasure_data = data.get("erasure")

        return cls(
            timestamp=data["timestamp"],
            event_kind=EventKind(data["event_kind"]),
            scope=ArtifactScope(data["scope"]),
            artifact=ArtifactMetadata(
                path=artifact_data.get("path", ""),
                size=artifact_data.get("size", 0),
                hash=artifact_data.get("hash"),
                role=artifact_data.get("role"),
                layer=artifact_data.get("layer"),
            ),
            erasure=ErasureFields(**erasure_data) if erasure_data else None,
            rename_from=data.get("rename_from"),
            metadata=data.get("metadata", {}),
        )


def classify_scope(path: Path, vault_path: Path) -> ArtifactScope:
    """Classify what kind of artifact a path represents."""
    try:
        rel_path = path.relative_to(vault_path)
        rel_str = str(rel_path).replace("\\", "/").lower()
    except ValueError:
        # Path is not under vault_path, check if it's a config file
        name = path.name.lower()
        if name in ("pyproject.toml", "hubs.yml", "registry.overrides.yml"):
            return ArtifactScope.CONFIG
        if "rules.py" in str(path) or "invariants.py" in str(path):
            return ArtifactScope.RULES
        return ArtifactScope.UNKNOWN

    # Check for registry files
    if "registry" in rel_str and path.suffix in (".md", ".yml", ".yaml"):
        return ArtifactScope.REGISTRY

    # Check for vault notes
    if path.suffix == ".md":
        return ArtifactScope.VAULT_NOTE

    # Check for config files
    if path.suffix in (".yml", ".yaml", ".toml"):
        return ArtifactScope.CONFIG

    return ArtifactScope.UNKNOWN


def compute_file_hash(path: Path) -> str | None:
    """Compute SHA-256 hash of file contents."""
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]  # First 16 chars
    except (OSError, IOError):
        return None


def extract_frontmatter_summary(path: Path) -> tuple[str | None, str | None]:
    """Extract role and layer from frontmatter if present."""
    if path.suffix != ".md":
        return None, None
    try:
        import frontmatter

        post = frontmatter.load(path)
        role = post.metadata.get("role")
        layer = post.metadata.get("layer")
        return role, layer
    except Exception:
        return None, None


def get_events_log_path(vault_path: Path) -> Path:
    """Get the path to the events log file."""
    irrev_dir = vault_path.parent / ".irrev"
    return irrev_dir / "events.log"


def ensure_events_dir(vault_path: Path) -> Path:
    """Ensure the .irrev directory exists and return events log path."""
    log_path = get_events_log_path(vault_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def log_event(
    vault_path: Path,
    event_kind: EventKind,
    file_path: Path,
    scope: ArtifactScope | None = None,
    include_hash: bool = False,
    include_frontmatter: bool = False,
    erasure: ErasureFields | None = None,
    rename_from: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> EventEnvelope:
    """
    Log a file system event.

    Args:
        vault_path: Path to the vault content directory
        event_kind: Type of event (created, modified, deleted, renamed)
        file_path: Path to the affected file
        scope: Classification of artifact (auto-detected if None)
        include_hash: Whether to compute and include file hash
        include_frontmatter: Whether to extract frontmatter summary
        erasure: Erasure accounting fields (for deletions)
        rename_from: Original path (for renames)
        metadata: Additional context

    Returns:
        The created event envelope
    """
    if scope is None:
        scope = classify_scope(file_path, vault_path)

    # Build artifact metadata
    try:
        size = file_path.stat().st_size if file_path.exists() else 0
    except OSError:
        size = 0

    file_hash = None
    if include_hash and file_path.exists():
        file_hash = compute_file_hash(file_path)

    role, layer = None, None
    if include_frontmatter and file_path.exists():
        role, layer = extract_frontmatter_summary(file_path)

    artifact = ArtifactMetadata(
        path=str(file_path),
        size=size,
        hash=file_hash,
        role=role,
        layer=layer,
    )

    envelope = EventEnvelope(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_kind=event_kind,
        scope=scope,
        artifact=artifact,
        erasure=erasure,
        rename_from=rename_from,
        metadata=metadata or {},
    )

    log_path = ensure_events_dir(vault_path)

    # Append as JSON Lines format
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(envelope.to_dict()) + "\n")

    return envelope


def read_events_log(
    vault_path: Path,
    last_n: int | None = None,
    event_kinds: list[EventKind] | None = None,
    scopes: list[ArtifactScope] | None = None,
) -> list[EventEnvelope]:
    """
    Read events from the events log with optional filtering.

    Args:
        vault_path: Path to the vault content directory
        last_n: If specified, return only the last N entries
        event_kinds: Filter to specific event types
        scopes: Filter to specific artifact scopes

    Returns:
        List of event envelopes (oldest first unless last_n specified)
    """
    log_path = get_events_log_path(vault_path)
    if not log_path.exists():
        return []

    entries = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                envelope = EventEnvelope.from_dict(data)

                # Apply filters
                if event_kinds and envelope.event_kind not in event_kinds:
                    continue
                if scopes and envelope.scope not in scopes:
                    continue

                entries.append(envelope)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue  # Skip malformed lines

    if last_n is not None:
        return entries[-last_n:]
    return entries


def format_event(envelope: EventEnvelope) -> str:
    """Format an event envelope for human-readable display."""
    icon = {
        EventKind.FILE_CREATED: "+",
        EventKind.FILE_MODIFIED: "~",
        EventKind.FILE_DELETED: "-",
        EventKind.FILE_RENAMED: ">",
    }.get(envelope.event_kind, "?")

    scope_tag = f"[{envelope.scope.value}]"
    path = envelope.artifact.path

    lines = [f"{icon} {scope_tag} {path}"]

    if envelope.rename_from:
        lines.append(f"  from: {envelope.rename_from}")

    if envelope.artifact.size:
        lines.append(f"  size: {envelope.artifact.size} bytes")

    if envelope.artifact.hash:
        lines.append(f"  hash: {envelope.artifact.hash}")

    if envelope.artifact.role or envelope.artifact.layer:
        parts = []
        if envelope.artifact.role:
            parts.append(f"role={envelope.artifact.role}")
        if envelope.artifact.layer:
            parts.append(f"layer={envelope.artifact.layer}")
        lines.append(f"  {', '.join(parts)}")

    if envelope.erasure:
        if envelope.erasure.bytes_erased:
            lines.append(f"  erased: {envelope.erasure.bytes_erased} bytes")
        if envelope.erasure.was_canonical:
            lines.append("  [CANONICAL]")
        if envelope.erasure.dependents_affected:
            lines.append(f"  dependents affected: {envelope.erasure.dependents_affected}")

    return "\n".join(lines)
