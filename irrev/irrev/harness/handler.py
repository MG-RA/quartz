"""
Handler protocol for effectful operations.

Handlers separate planning (diagnostic, pure) from execution (action, impure).
The harness orchestrates calling these methods with proper governance.

Key design decisions:
- Risk is derived from EffectSummary, not claimed by handlers
- Plans must include predicted effects for governance derivation
- Secrets are passed as references, never raw values
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, Literal, Protocol, TypeVar, runtime_checkable

# Effect type literals - matches RiskClass but expressed as operation semantics
EffectType = Literal[
    "read_only",
    "append_only",
    "mutation_reversible",
    "mutation_destructive",
    "external_side_effect",
]


@dataclass(frozen=True)
class EffectSummary:
    """
    Predicted effects of an operation.

    Risk classification is DERIVED from this, not claimed.
    This is the key to preventing governance bypass: handlers must
    predict their effects, and the harness derives risk from predictions.
    """

    effect_type: EffectType
    predicted_erasure: dict[str, int] = field(default_factory=dict)
    # Expected keys: notes, edges, files, bytes
    predicted_outputs: list[str] = field(default_factory=list)
    # Paths or target identifiers (e.g., database names)
    reasons: list[str] = field(default_factory=list)
    # Human-readable explanations for the effect classification

    def to_dict(self) -> dict[str, Any]:
        """Serialize for artifact storage."""
        return {
            "effect_type": self.effect_type,
            "predicted_erasure": dict(self.predicted_erasure),
            "predicted_outputs": list(self.predicted_outputs),
            "reasons": list(self.reasons),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EffectSummary:
        """Deserialize from artifact storage."""
        return cls(
            effect_type=data.get("effect_type", "external_side_effect"),
            predicted_erasure=dict(data.get("predicted_erasure", {})),
            predicted_outputs=list(data.get("predicted_outputs", [])),
            reasons=list(data.get("reasons", [])),
        )

    @classmethod
    def read_only(cls, reasons: list[str] | None = None) -> EffectSummary:
        """Factory for read-only operations."""
        return cls(
            effect_type="read_only",
            reasons=reasons or ["read-only operation"],
        )

    @classmethod
    def append_only(
        cls,
        predicted_outputs: list[str] | None = None,
        reasons: list[str] | None = None,
    ) -> EffectSummary:
        """Factory for append-only operations (logging, artifacts)."""
        return cls(
            effect_type="append_only",
            predicted_outputs=predicted_outputs or [],
            reasons=reasons or ["append-only operation"],
        )


@dataclass
class ExecutionMetrics:
    """
    Standardized execution metrics reported by handlers.

    Handlers should return these metrics to enable structured logging
    and performance analysis. Prevents brittle hasattr() probing.

    Generic counters are standardized; domain-specific metrics go in custom.
    """

    # Generic counters (standardized across all handlers)
    items_processed: int = 0
    bytes_written: int = 0
    bytes_read: int = 0

    # Domain-specific (handler decides what to include)
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for event payload."""
        result = {
            "items_processed": self.items_processed,
            "bytes_written": self.bytes_written,
            "bytes_read": self.bytes_read,
        }
        result.update(self.custom)
        return result


@dataclass(frozen=True)
class HandlerMetadata:
    """Static metadata about a handler's capabilities."""

    operation: str  # e.g., "neo4j.load"
    delegate_to: str  # e.g., "handler:neo4j"
    supports_dry_run: bool = True


@runtime_checkable
class HarnessPlan(Protocol):
    """
    Protocol for plans that can be executed through the harness.

    All plans must include an effect_summary for governance derivation.
    """

    effect_summary: EffectSummary

    def summary(self) -> str:
        """Human-readable summary of what this plan will do."""
        ...


TPlan = TypeVar("TPlan", bound=HarnessPlan)
TResult = TypeVar("TResult")


@dataclass
class ExecutionContext:
    """
    Context passed to handlers during execution.

    Note: secrets_ref is a reference (e.g., "env:PASSWORD"), not the secret value.
    This prevents accidental logging/bundling of sensitive data.
    """

    vault_path: Path
    executor: str  # e.g., "handler:neo4j"
    plan_artifact_id: str
    approval_artifact_id: str | None = None
    dry_run: bool = False
    secrets_ref: str | None = None  # Reference to secrets, not raw values


class Handler(ABC, Generic[TPlan, TResult]):
    """
    Protocol for effectful operations.

    Handlers implement two phases:
    1. Pure phase: validate_params → compute_plan → validate_plan
    2. Impure phase: execute

    The harness orchestrates these phases with proper governance.
    """

    @property
    @abstractmethod
    def metadata(self) -> HandlerMetadata:
        """Return static handler metadata."""
        ...

    # -------------------------------------------------------------------------
    # Pure phase: no side effects
    # -------------------------------------------------------------------------

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """
        Validate operation parameters before planning.

        Returns list of validation errors (empty = valid).
        Override to add parameter validation.
        """
        return []

    @abstractmethod
    def compute_plan(
        self,
        vault_path: Path,
        params: dict[str, Any],
    ) -> TPlan:
        """
        Compute what would be done (diagnostic phase).

        MUST be pure - no side effects. Returns a plan that:
        - Includes effect_summary for governance derivation
        - Can be serialized to the artifact ledger
        - Can be executed later via execute()
        """
        ...

    def validate_plan(self, plan: TPlan) -> list[str]:
        """
        Validate the computed plan before execution.

        Use this for domain-specific invariants that aren't
        expressible in the generic ruleset.

        Returns list of validation errors (empty = valid).
        Override to add plan validation.
        """
        return []

    # -------------------------------------------------------------------------
    # Impure phase: side effects allowed
    # -------------------------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        plan: TPlan,
        context: ExecutionContext,
    ) -> TResult:
        """
        Execute the plan (action phase).

        Called only after governance gates pass.
        Must return a result with erasure_cost and creation_summary.
        """
        ...
