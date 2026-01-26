"""
LSP server for live invariant awareness.

Per the Governance invariant: diagnostics should be ambient, not gated.

This module provides:
- LSP server for Obsidian/VSCode integration
- Real-time lint diagnostics
- Hover information for concepts
- Code actions phrased as suggestions (not commands)
"""

from .server import create_server, start_server

__all__ = ["create_server", "start_server"]
