"""
Content-addressed storage (CAS) for artifact payloads.

Payloads are stored by their sha256 hash, enabling deduplication
and integrity verification. The content store is separate from
the ledger - the ledger references content by content_id.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ContentStore:
    """
    Content-addressed storage for artifact payloads.

    Payloads are stored in a two-level directory structure using
    the first 2 characters of the hash as the prefix:

        .irrev/content/ab/ab1234...json

    This prevents directory bloat while maintaining fast lookups.
    """

    def __init__(self, irrev_dir: Path):
        """
        Initialize content store.

        Args:
            irrev_dir: Path to .irrev directory
        """
        self.irrev_dir = irrev_dir
        self.content_dir = irrev_dir / "content"

    def _ensure_dir(self, prefix: str) -> Path:
        """Ensure content directory and prefix subdirectory exist."""
        dir_path = self.content_dir / prefix
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def _content_path(self, content_id: str) -> Path:
        """Get path for a content blob."""
        prefix = content_id[:2]
        return self.content_dir / prefix / f"{content_id}.json"

    @staticmethod
    def compute_hash(content: bytes | str | dict[str, Any]) -> str:
        """
        Compute sha256 hash of content.

        Args:
            content: Raw bytes, string, or dict to hash

        Returns:
            Hex-encoded sha256 hash
        """
        if isinstance(content, dict):
            # Canonical JSON serialization for deterministic hashing
            content = json.dumps(content, sort_keys=True, separators=(",", ":"))
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def store(self, content: bytes | str | dict[str, Any]) -> str:
        """
        Store content and return its content_id.

        If content already exists, this is a no-op (idempotent).

        Args:
            content: Content to store

        Returns:
            content_id (sha256 hash)
        """
        content_id = self.compute_hash(content)

        # Check if already exists (deduplication)
        content_path = self._content_path(content_id)
        if content_path.exists():
            return content_id

        # Ensure directory exists
        self._ensure_dir(content_id[:2])

        # Serialize content
        if isinstance(content, dict):
            serialized = json.dumps(content, indent=2, sort_keys=True)
        elif isinstance(content, bytes):
            # For raw bytes, store as base64 in JSON wrapper
            import base64
            serialized = json.dumps({
                "_type": "binary",
                "_encoding": "base64",
                "data": base64.b64encode(content).decode("ascii"),
            }, indent=2)
        else:
            # String content
            serialized = json.dumps({
                "_type": "text",
                "data": content,
            }, indent=2)

        # Write atomically (write to temp, then rename)
        temp_path = content_path.with_suffix(".tmp")
        temp_path.write_text(serialized, encoding="utf-8")
        temp_path.rename(content_path)

        return content_id

    def get(self, content_id: str) -> dict[str, Any] | bytes | str | None:
        """
        Retrieve content by content_id.

        Args:
            content_id: sha256 hash of content

        Returns:
            Original content (dict, bytes, or str), or None if not found
        """
        content_path = self._content_path(content_id)
        if not content_path.exists():
            return None

        data = json.loads(content_path.read_text(encoding="utf-8"))

        # Handle wrapped types
        if isinstance(data, dict):
            if data.get("_type") == "binary":
                import base64
                return base64.b64decode(data["data"])
            elif data.get("_type") == "text":
                return data["data"]

        return data

    def get_json(self, content_id: str) -> dict[str, Any] | None:
        """
        Retrieve content as JSON dict.

        Args:
            content_id: sha256 hash of content

        Returns:
            Content as dict, or None if not found
        """
        content = self.get(content_id)
        if isinstance(content, dict):
            return content
        return None

    def exists(self, content_id: str) -> bool:
        """Check if content exists."""
        return self._content_path(content_id).exists()

    def verify(self, content_id: str) -> bool:
        """
        Verify content integrity.

        Recomputes hash and compares to content_id.

        Args:
            content_id: Expected hash

        Returns:
            True if content exists and hash matches
        """
        content = self.get(content_id)
        if content is None:
            return False
        return self.compute_hash(content) == content_id

    def list_content_ids(self) -> list[str]:
        """List all content IDs in the store."""
        content_ids = []
        if not self.content_dir.exists():
            return content_ids

        for prefix_dir in self.content_dir.iterdir():
            if prefix_dir.is_dir() and len(prefix_dir.name) == 2:
                for content_file in prefix_dir.glob("*.json"):
                    content_ids.append(content_file.stem)

        return content_ids

    def size(self) -> int:
        """Get total size of content store in bytes."""
        total = 0
        if not self.content_dir.exists():
            return total

        for prefix_dir in self.content_dir.iterdir():
            if prefix_dir.is_dir():
                for content_file in prefix_dir.glob("*.json"):
                    total += content_file.stat().st_size

        return total

    def count(self) -> int:
        """Count items in content store."""
        return len(self.list_content_ids())


def compute_payload_manifest(
    files: dict[str, bytes | str],
) -> list[dict[str, Any]]:
    """
    Compute payload manifest for a set of files.

    Args:
        files: Dict mapping path to content

    Returns:
        List of {path, bytes, sha256} entries
    """
    manifest = []
    for path, content in files.items():
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        manifest.append({
            "path": path,
            "bytes": len(content_bytes),
            "sha256": hashlib.sha256(content_bytes).hexdigest(),
        })

    return manifest
