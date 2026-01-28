"""
Execution harness: single chokepoint for all effectful operations.

The harness enforces governance invariants architecturally - operations
cannot bypass gates without leaving audit scars.

Key principle: "the tool cannot bypass invariants without leaving a scar."
"""

from __future__ import annotations

from .handler import (
    EffectSummary,
    EffectType,
    ExecutionContext,
    ExecutionMetrics,
    Handler,
    HandlerMetadata,
    HarnessPlan,
)
from .harness import (
    ExecuteResult,
    Harness,
    ProposeResult,
)
from .registry import get_handler, register_handler
from .secrets import EnvSecretsProvider, SecretsProvider

__all__ = [
    # Handler protocol
    "EffectSummary",
    "EffectType",
    "ExecutionContext",
    "ExecutionMetrics",
    "Handler",
    "HandlerMetadata",
    "HarnessPlan",
    # Harness
    "ExecuteResult",
    "Harness",
    "ProposeResult",
    # Registry
    "get_handler",
    "register_handler",
    # Secrets
    "EnvSecretsProvider",
    "SecretsProvider",
]
