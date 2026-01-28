"""
Harness handlers for effectful operations.

Each handler implements the Handler protocol:
- validate_params(): Validate operation parameters
- compute_plan(): Compute what would be done (pure)
- validate_plan(): Validate the plan (pure)
- execute(): Perform the operation (impure)

Handlers are registered automatically when imported.
"""

from __future__ import annotations

from .neo4j_handler import Neo4jLoadHandler

__all__ = [
    "Neo4jLoadHandler",
]


def register_all() -> None:
    """Register all handlers with the registry."""
    from ..registry import register_handler

    register_handler(Neo4jLoadHandler())
