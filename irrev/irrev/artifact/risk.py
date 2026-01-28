"""
Risk classification for artifact operations.

Risk class is computed authoritatively from operation semantics, not from user claims.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class RiskClass(str, Enum):
    READ_ONLY = "read_only"  # No state change, no approval
    APPEND_ONLY = "append_only"  # Adds artifacts/logs only
    MUTATION_REVERSIBLE = "mutation_reversible"  # Patchable, rollbackable locally
    MUTATION_DESTRUCTIVE = "mutation_destructive"  # Deletes/wipes/overwrites
    EXTERNAL_SIDE_EFFECT = "external_side_effect"  # Network calls, DB writes, etc.


def compute_risk(operation: str, payload: dict[str, Any]) -> tuple[RiskClass, list[str]]:
    """
    Compute risk class and a short explanation list.

    This function is intentionally conservative: unknown operations are treated
    as EXTERNAL_SIDE_EFFECT to avoid silent governance gaps.
    """
    op = (operation or "").strip().lower()
    reasons: list[str] = []

    destructive = False
    external = False
    reversible = False
    append_only = False

    # --- Known operations -------------------------------------------------
    if op in {"lint", "registry.diff", "pack"}:
        reasons.append("diagnostic-only operation")
        return (RiskClass.READ_ONLY, reasons)

    if op in {"artifact.approve", "artifact.created", "artifact.append"}:
        reasons.append("append-only governance event")
        return (RiskClass.APPEND_ONLY, reasons)

    if op in {"registry.build", "registry.build.in_place"}:
        reversible = True
        reasons.append("writes registry output (reversible local mutation)")

    if op in {"neo4j.load", "neo4j-load", "neo4j.load.sync", "neo4j.load.rebuild"}:
        external = True
        reasons.append("writes to external Neo4j (external side effect)")
        mode = str(payload.get("mode", "")).lower().strip()
        if mode == "rebuild":
            destructive = True
            reasons.append("rebuild mode wipes database (destructive)")

    # --- Generic predicted-effects hook ----------------------------------
    effects = payload.get("effects")
    if isinstance(effects, dict):
        if effects.get("network") is True:
            external = True
            reasons.append("declared network effect")
        if effects.get("destructive") is True:
            destructive = True
            reasons.append("declared destructive effect")
        if effects.get("writes") is True:
            reversible = True
            reasons.append("declared reversible write effect")
        if effects.get("append_only") is True:
            append_only = True
            reasons.append("declared append-only effect")

    # --- Harness effect_summary hook --------------------------------------
    # The harness includes an effect_summary in the plan payload that
    # provides authoritative risk classification derived from the plan.
    effect_summary = payload.get("effect_summary")
    if isinstance(effect_summary, dict):
        effect_type = str(effect_summary.get("effect_type", "")).lower().strip()
        summary_reasons = effect_summary.get("reasons", [])
        if isinstance(summary_reasons, list):
            reasons.extend(str(r) for r in summary_reasons)

        if effect_type == "mutation_destructive":
            destructive = True
        elif effect_type == "external_side_effect":
            external = True
        elif effect_type == "mutation_reversible":
            reversible = True
        elif effect_type == "append_only":
            append_only = True
        elif effect_type == "read_only":
            # read_only takes precedence if explicitly set
            return (RiskClass.READ_ONLY, reasons or ["read-only operation"])

    # --- Decision ---------------------------------------------------------
    if destructive:
        return (RiskClass.MUTATION_DESTRUCTIVE, reasons or ["destructive mutation"])
    if external:
        return (RiskClass.EXTERNAL_SIDE_EFFECT, reasons or ["external side effect"])
    if reversible:
        return (RiskClass.MUTATION_REVERSIBLE, reasons or ["reversible mutation"])
    if append_only:
        return (RiskClass.APPEND_ONLY, reasons or ["append-only"])

    # Unknown: conservative default.
    return (RiskClass.EXTERNAL_SIDE_EFFECT, reasons or ["unknown operation; treated as external side effect"])


def compute_risk_class(operation: str, payload: dict[str, Any]) -> RiskClass:
    """Compute only the RiskClass (no explanation)."""
    risk, _ = compute_risk(operation, payload)
    return risk

