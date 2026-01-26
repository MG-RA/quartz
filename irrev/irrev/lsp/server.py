"""
LSP server implementation for irrev vault linting.

Provides:
- Real-time diagnostics from irrev lint
- Hover info for concepts (layer, dependencies, invariants)
- Code actions as suggestions (not auto-apply)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer

from .diagnostics import lint_file, LintDiagnostic
from .hover import get_hover_info

logger = logging.getLogger(__name__)


class IrrevLanguageServer(LanguageServer):
    """Language server for irrev vault files."""

    def __init__(self, vault_path: Path | None = None):
        super().__init__(name="irrev-lsp", version="0.1.0")
        self.vault_path = vault_path
        self._concept_cache: dict[str, dict[str, Any]] = {}
        self._alias_cache: dict[str, str] = {}
        if vault_path:
            self._load_vault_cache()

    def set_vault_path(self, path: Path) -> None:
        """Set the vault path for this server."""
        self.vault_path = path
        self._load_vault_cache()

    def _load_vault_cache(self) -> None:
        """Load concept and alias cache from vault."""
        if not self.vault_path:
            return

        try:
            from ..vault.loader import load_vault

            vault = load_vault(self.vault_path)
            self._concept_cache = {
                c.name.lower(): {
                    "name": c.name,
                    "layer": c.layer,
                    "role": c.role,
                    "depends_on": list(c.depends_on),
                    "path": str(c.path),
                }
                for c in vault.concepts
            }
            self._alias_cache = dict(vault._aliases)
        except Exception as e:
            logger.warning(f"Failed to load vault cache: {e}")

    def get_concept_info(self, name: str) -> dict[str, Any] | None:
        """Get cached concept info by name or alias."""
        normalized = name.lower().strip()
        # Check aliases first
        if normalized in self._alias_cache:
            normalized = self._alias_cache[normalized]
        return self._concept_cache.get(normalized)


def uri_to_path(uri: str) -> Path:
    """Convert a file URI to a Path."""
    parsed = urlparse(uri)
    # Handle Windows paths
    path = unquote(parsed.path)
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]  # Remove leading slash for Windows paths
    return Path(path)


def create_server(vault_path: Path | None = None) -> IrrevLanguageServer:
    """Create and configure the LSP server."""
    server = IrrevLanguageServer(vault_path)

    @server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: lsp.DidOpenTextDocumentParams) -> None:
        """Handle document open - run initial lint."""
        _validate_document(server, params.text_document.uri, params.text_document.text)

    @server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
    def did_save(params: lsp.DidSaveTextDocumentParams) -> None:
        """Handle document save - re-run lint."""
        # Read the saved content
        path = uri_to_path(params.text_document.uri)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            _validate_document(server, params.text_document.uri, content)

    @server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: lsp.DidChangeTextDocumentParams) -> None:
        """Handle document change - debounced lint on significant changes."""
        # For now, only lint on save to avoid performance issues
        # Could add debouncing here for live updates
        pass

    @server.feature(lsp.TEXT_DOCUMENT_HOVER)
    def hover(params: lsp.HoverParams) -> lsp.Hover | None:
        """Provide hover information for wikilinks."""
        path = uri_to_path(params.text_document.uri)
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Find if cursor is within a wikilink
        lines = content.split("\n")
        if params.position.line >= len(lines):
            return None

        line = lines[params.position.line]
        col = params.position.character

        # Find wikilink at position
        wikilink_pattern = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
        for match in wikilink_pattern.finditer(line):
            if match.start() <= col <= match.end():
                target = match.group(1).strip()
                hover_info = get_hover_info(server, target)
                if hover_info:
                    return lsp.Hover(
                        contents=lsp.MarkupContent(
                            kind=lsp.MarkupKind.Markdown,
                            value=hover_info,
                        ),
                        range=lsp.Range(
                            start=lsp.Position(line=params.position.line, character=match.start()),
                            end=lsp.Position(line=params.position.line, character=match.end()),
                        ),
                    )
        return None

    @server.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)
    def code_action(params: lsp.CodeActionParams) -> list[lsp.CodeAction]:
        """Provide code actions for diagnostics.

        Actions are phrased as suggestions, not commands.
        Per Governance: suggestions require explicit user confirmation.
        """
        actions = []

        for diagnostic in params.context.diagnostics:
            if diagnostic.source != "irrev":
                continue

            # Extract rule_id from diagnostic data
            rule_id = None
            if diagnostic.data and isinstance(diagnostic.data, dict):
                rule_id = diagnostic.data.get("rule_id")

            if rule_id == "broken-link":
                # Suggest checking for typos or creating the target
                actions.append(
                    lsp.CodeAction(
                        title="Possible repair: verify target exists or check spelling",
                        kind=lsp.CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                        # No edit - this is a suggestion only
                    )
                )
            elif rule_id == "alias-drift":
                actions.append(
                    lsp.CodeAction(
                        title="Possible repair: update alias in frontmatter",
                        kind=lsp.CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                    )
                )
            elif rule_id == "layer-violation":
                actions.append(
                    lsp.CodeAction(
                        title="Possible repair: review dependency direction",
                        kind=lsp.CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                    )
                )

        return actions

    @server.feature(lsp.INITIALIZE)
    def initialize(params: lsp.InitializeParams) -> None:
        """Handle initialize - detect vault path from workspace."""
        if params.root_uri:
            root = uri_to_path(params.root_uri)
            # Look for content directory
            content_path = root / "content"
            if content_path.is_dir():
                server.set_vault_path(content_path)
            elif root.name == "content":
                server.set_vault_path(root)

    return server


def _validate_document(server: IrrevLanguageServer, uri: str, content: str) -> None:
    """Run lint on document and publish diagnostics."""
    path = uri_to_path(uri)

    # Only lint markdown files
    if path.suffix.lower() != ".md":
        return

    # Get vault path from server or try to detect
    vault_path = server.vault_path
    if not vault_path:
        # Try to detect from file path
        for parent in path.parents:
            if parent.name == "content":
                vault_path = parent
                server.set_vault_path(vault_path)
                break

    if not vault_path:
        return

    # Run lint
    diagnostics = lint_file(path, vault_path, content)

    # Convert to LSP diagnostics
    lsp_diagnostics = []
    for diag in diagnostics:
        severity = {
            "error": lsp.DiagnosticSeverity.Error,
            "warning": lsp.DiagnosticSeverity.Warning,
            "info": lsp.DiagnosticSeverity.Information,
        }.get(diag.severity, lsp.DiagnosticSeverity.Warning)

        lsp_diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=diag.line, character=diag.column),
                    end=lsp.Position(line=diag.line, character=diag.column + diag.length),
                ),
                message=diag.message,
                severity=severity,
                source="irrev",
                code=diag.rule_id,
                data={"rule_id": diag.rule_id, "invariant": diag.invariant},
            )
        )

    server.publish_diagnostics(uri, lsp_diagnostics)


def start_server(vault_path: Path | None = None, transport: str = "stdio") -> None:
    """Start the LSP server.

    Args:
        vault_path: Path to vault content directory
        transport: Transport method ("stdio" or "tcp")
    """
    server = create_server(vault_path)

    if transport == "stdio":
        server.start_io()
    else:
        # TCP transport for debugging
        server.start_tcp("localhost", 2087)
