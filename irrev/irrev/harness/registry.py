"""
Handler registry for operation name → Handler lookup.

Handlers register themselves by operation name. The harness uses
this registry to look up the appropriate handler for an operation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .handler import Handler

# Global registry: operation name → handler instance
_HANDLERS: dict[str, "Handler"] = {}


def register_handler(handler: "Handler") -> None:
    """
    Register a handler by its operation name.

    Args:
        handler: Handler instance to register
    """
    operation = handler.metadata.operation
    _HANDLERS[operation] = handler


def get_handler(operation: str) -> "Handler | None":
    """
    Look up a handler by operation name.

    Args:
        operation: Operation name (e.g., "neo4j.load")

    Returns:
        Handler instance, or None if not registered
    """
    return _HANDLERS.get(operation)


def list_handlers() -> list[str]:
    """
    List all registered operation names.

    Returns:
        List of registered operation names
    """
    return list(_HANDLERS.keys())


def clear_handlers() -> None:
    """Clear all registered handlers (for testing)."""
    _HANDLERS.clear()
