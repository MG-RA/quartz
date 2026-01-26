"""
File system watcher for structural event logging.

Per the Irreversibility invariant: "Persistence must be tracked."

This module provides:
- Watchdog-based file monitoring
- Rename detection (same hash = rename, not delete+create)
- Debounced event emission
- Configurable scope filtering
"""

import time
from collections import defaultdict
from pathlib import Path
from typing import Callable

from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
)
from watchdog.observers import Observer

from .events import (
    EventKind,
    ArtifactScope,
    ErasureFields,
    log_event,
    classify_scope,
    compute_file_hash,
    format_event,
)


class PendingEvent:
    """Tracks a pending event for debouncing."""

    def __init__(
        self,
        event_kind: EventKind,
        path: Path,
        timestamp: float,
        old_hash: str | None = None,
        old_size: int = 0,
    ):
        self.event_kind = event_kind
        self.path = path
        self.timestamp = timestamp
        self.old_hash = old_hash
        self.old_size = old_size


class VaultEventHandler(FileSystemEventHandler):
    """
    Handles file system events and logs them as structural events.

    Key behaviors:
    - Debounces rapid modifications (e.g., editor save cycles)
    - Detects renames by comparing hashes of deleted/created files
    - Filters to relevant file types (.md, .yml, .yaml, .py, .toml)
    - Logs to .irrev/events.log
    """

    RELEVANT_EXTENSIONS = {".md", ".yml", ".yaml", ".py", ".toml"}
    DEBOUNCE_SECONDS = 1.0

    def __init__(
        self,
        vault_path: Path,
        include_hash: bool = False,
        include_frontmatter: bool = False,
        on_event: Callable[[str], None] | None = None,
        scopes: set[ArtifactScope] | None = None,
    ):
        """
        Initialize the event handler.

        Args:
            vault_path: Path to vault content directory
            include_hash: Whether to compute file hashes
            include_frontmatter: Whether to extract frontmatter metadata
            on_event: Callback for event notifications (receives formatted string)
            scopes: Filter to specific artifact scopes (None = all)
        """
        super().__init__()
        self.vault_path = vault_path
        self.include_hash = include_hash
        self.include_frontmatter = include_frontmatter
        self.on_event = on_event
        self.scopes = scopes

        # Pending events for debouncing
        self.pending: dict[str, PendingEvent] = {}

        # Track deleted file hashes for rename detection
        self.deleted_hashes: dict[str, tuple[str, float]] = {}  # hash -> (path, timestamp)

        # Track file hashes for modification detection
        self.file_hashes: dict[str, str] = {}  # path -> hash

    def _is_relevant(self, path: str) -> bool:
        """Check if the file is relevant for tracking."""
        p = Path(path)

        # Skip hidden files and directories
        if any(part.startswith(".") for part in p.parts):
            return False

        # Check extension
        if p.suffix.lower() not in self.RELEVANT_EXTENSIONS:
            return False

        # Check scope filter
        if self.scopes:
            scope = classify_scope(p, self.vault_path)
            if scope not in self.scopes:
                return False

        return True

    def _emit_event(
        self,
        event_kind: EventKind,
        path: Path,
        rename_from: str | None = None,
        erasure: ErasureFields | None = None,
    ) -> None:
        """Log an event and notify callback."""
        envelope = log_event(
            vault_path=self.vault_path,
            event_kind=event_kind,
            file_path=path,
            include_hash=self.include_hash,
            include_frontmatter=self.include_frontmatter,
            erasure=erasure,
            rename_from=rename_from,
        )

        if self.on_event:
            self.on_event(format_event(envelope))

    def _check_rename(self, path: Path, new_hash: str | None) -> str | None:
        """
        Check if a newly created file is actually a rename.

        Returns the original path if this is a rename, None otherwise.
        """
        if not new_hash:
            return None

        now = time.time()
        # Look for a recent deletion with the same hash
        if new_hash in self.deleted_hashes:
            old_path, timestamp = self.deleted_hashes[new_hash]
            # Within 5 seconds = likely a rename
            if now - timestamp < 5.0:
                del self.deleted_hashes[new_hash]
                return old_path

        return None

    def flush_pending(self) -> None:
        """Flush any pending events that have passed debounce window."""
        now = time.time()
        to_emit = []

        for path_str, pending in list(self.pending.items()):
            if now - pending.timestamp >= self.DEBOUNCE_SECONDS:
                to_emit.append((path_str, pending))
                del self.pending[path_str]

        for path_str, pending in to_emit:
            path = pending.path

            if pending.event_kind == EventKind.FILE_CREATED:
                # Check for rename
                new_hash = compute_file_hash(path) if path.exists() else None
                rename_from = self._check_rename(path, new_hash)

                if rename_from:
                    self._emit_event(EventKind.FILE_RENAMED, path, rename_from=rename_from)
                else:
                    self._emit_event(EventKind.FILE_CREATED, path)

                # Track hash for future modifications
                if new_hash:
                    self.file_hashes[path_str] = new_hash

            elif pending.event_kind == EventKind.FILE_MODIFIED:
                # Check if content actually changed
                new_hash = compute_file_hash(path) if path.exists() else None
                old_hash = self.file_hashes.get(path_str)

                if new_hash != old_hash:
                    self._emit_event(EventKind.FILE_MODIFIED, path)
                    if new_hash:
                        self.file_hashes[path_str] = new_hash

            elif pending.event_kind == EventKind.FILE_DELETED:
                # Store hash for rename detection
                if pending.old_hash:
                    self.deleted_hashes[pending.old_hash] = (path_str, now)

                erasure = ErasureFields(bytes_erased=pending.old_size)
                self._emit_event(EventKind.FILE_DELETED, path, erasure=erasure)

                # Remove from tracked hashes
                self.file_hashes.pop(path_str, None)

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation."""
        if event.is_directory or not self._is_relevant(event.src_path):
            return

        path_str = event.src_path
        self.pending[path_str] = PendingEvent(
            event_kind=EventKind.FILE_CREATED,
            path=Path(path_str),
            timestamp=time.time(),
        )

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification."""
        if event.is_directory or not self._is_relevant(event.src_path):
            return

        path_str = event.src_path

        # Don't override pending creation with modification
        if path_str in self.pending and self.pending[path_str].event_kind == EventKind.FILE_CREATED:
            return

        self.pending[path_str] = PendingEvent(
            event_kind=EventKind.FILE_MODIFIED,
            path=Path(path_str),
            timestamp=time.time(),
        )

    def on_deleted(self, event: FileDeletedEvent) -> None:
        """Handle file deletion."""
        if event.is_directory or not self._is_relevant(event.src_path):
            return

        path_str = event.src_path
        path = Path(path_str)

        # Get hash before deletion for rename detection
        old_hash = self.file_hashes.get(path_str)
        old_size = 0

        # Cancel any pending creation/modification
        if path_str in self.pending:
            pending = self.pending[path_str]
            if pending.event_kind == EventKind.FILE_CREATED:
                # File created then deleted before flush - no event
                del self.pending[path_str]
                return

        self.pending[path_str] = PendingEvent(
            event_kind=EventKind.FILE_DELETED,
            path=path,
            timestamp=time.time(),
            old_hash=old_hash,
            old_size=old_size,
        )

    def on_moved(self, event: FileMovedEvent) -> None:
        """Handle file rename/move."""
        if event.is_directory:
            return

        src_relevant = self._is_relevant(event.src_path)
        dest_relevant = self._is_relevant(event.dest_path)

        if src_relevant and dest_relevant:
            # Both paths relevant - emit rename
            self._emit_event(
                EventKind.FILE_RENAMED,
                Path(event.dest_path),
                rename_from=event.src_path,
            )
            # Update hash tracking
            if event.src_path in self.file_hashes:
                self.file_hashes[event.dest_path] = self.file_hashes.pop(event.src_path)

        elif src_relevant:
            # Moved out of watched area - treat as delete
            old_hash = self.file_hashes.pop(event.src_path, None)
            erasure = ErasureFields()
            self._emit_event(EventKind.FILE_DELETED, Path(event.src_path), erasure=erasure)

        elif dest_relevant:
            # Moved into watched area - treat as create
            self._emit_event(EventKind.FILE_CREATED, Path(event.dest_path))


def watch_vault(
    vault_path: Path,
    include_hash: bool = False,
    include_frontmatter: bool = False,
    on_event: Callable[[str], None] | None = None,
    scopes: set[ArtifactScope] | None = None,
    recursive: bool = True,
) -> tuple[Observer, VaultEventHandler]:
    """
    Start watching a vault for file system events.

    Args:
        vault_path: Path to vault content directory
        include_hash: Whether to compute file hashes
        include_frontmatter: Whether to extract frontmatter metadata
        on_event: Callback for event notifications
        scopes: Filter to specific artifact scopes
        recursive: Whether to watch subdirectories

    Returns:
        Tuple of (observer, handler) - caller should call observer.stop() to stop watching
    """
    handler = VaultEventHandler(
        vault_path=vault_path,
        include_hash=include_hash,
        include_frontmatter=include_frontmatter,
        on_event=on_event,
        scopes=scopes,
    )

    observer = Observer()
    observer.schedule(handler, str(vault_path), recursive=recursive)
    observer.start()

    return observer, handler


def run_watch_loop(
    vault_path: Path,
    include_hash: bool = False,
    include_frontmatter: bool = False,
    on_event: Callable[[str], None] | None = None,
    scopes: set[ArtifactScope] | None = None,
) -> None:
    """
    Run the watch loop until interrupted.

    This is a blocking function that watches for events and flushes
    pending events periodically.
    """
    observer, handler = watch_vault(
        vault_path=vault_path,
        include_hash=include_hash,
        include_frontmatter=include_frontmatter,
        on_event=on_event,
        scopes=scopes,
    )

    try:
        while True:
            time.sleep(0.5)
            handler.flush_pending()
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
