"""
Invariant registry for the irrev vault system.

This module defines the 4 kernel invariants that constitute the infrastructure layer:
- Decomposition: Objects/operators separation, bounded scope, explicit accounting
- Governance: No actor exempt from constraints, self-correcting under scale
- Attribution: Explicit responsibility, diagnostics can't prescribe, roles define authority
- Irreversibility: Declared erasure costs, no rollback assumptions, mandatory accounting

Coherence is NOT an invariant - it emerges from joint compliance with the 4 kernel invariants.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Invariant:
    """An infrastructure-level constraint enforced by multiple rules."""
    id: str
    name: str
    statement: str  # The invariant's core principle
    failure_mode: str  # What breaks when this is violated
    rules: List[str]  # Rule IDs that enforce this invariant (ONE rule maps to ONE invariant)


# Canonical invariant order (prevents implicit dict ordering contract)
INVARIANT_ORDER = ["decomposition", "governance", "attribution", "irreversibility"]

# The 4 kernel invariants - these define the infrastructure layer
INVARIANTS = {
    "decomposition": Invariant(
        id="decomposition",
        name="Decomposition",
        statement="Objects and operators must be separated by role; role boundaries must not merge incompatible functions.",
        failure_mode="Category errors, role confusion, function merging",
        rules=["kind-violation", "layer-violation"]
    ),
    "governance": Invariant(
        id="governance",
        name="Governance",
        statement="No actor is exempt from structural constraints; the system self-corrects under scale.",
        failure_mode="Unconstrained authority, silent failures, non-corrigibility",
        rules=["forbidden-edge", "missing-role"]
    ),
    "attribution": Invariant(
        id="attribution",
        name="Attribution",
        statement="Responsibility must be explicit; diagnostics cannot prescribe; roles define authority.",
        failure_mode="Responsibility diffusion, role confusion, hidden prescription",
        rules=["responsibility-scope"]  # Single primary invariant per rule
    ),
    "irreversibility": Invariant(
        id="irreversibility",
        name="Irreversibility",
        statement="Persistence must be tracked; erasure costs must be declared; rollback cannot be assumed; accounting is mandatory.",
        failure_mode="Silent data loss, cost externalization, false reversibility assumptions, hidden state changes",
        rules=["missing-dependencies", "mechanism-missing-residuals", "hub-required-headings"]  # Will expand with future accounting checks
    )
}

# Structural integrity rules that don't map to invariants
# These ensure basic graph coherence - coherence EMERGES from invariant compliance
STRUCTURAL_RULES = {
    "dependency-cycle": "Graph must be acyclic",
    "broken-link": "Wiki-links must resolve",
    "alias-drift": "Use canonical names",
    "registry-drift": "Registry tables must match generated output",
}


def get_invariant_for_rule(rule_id: str) -> Optional[Invariant]:
    """
    Look up which invariant a rule enforces.

    Args:
        rule_id: The rule identifier (e.g., 'kind-violation', 'missing-role')

    Returns:
        The Invariant that this rule enforces, or None if the rule is structural.
    """
    for inv in INVARIANTS.values():
        if rule_id in inv.rules:
            return inv
    return None


# Documentation note about coherence (NOT an invariant)
COHERENCE_NOTE = """
Coherence as a Derived Condition
=================================

Coherence is not enforced directly; it emerges when irreversibility,
decomposition, governance, and attribution are jointly respected.

The structural rules (dependency-cycle, broken-link, alias-drift) ensure
basic graph integrity but do not constitute an invariant themselves.
They verify properties that should naturally hold when the kernel invariants
are satisfied.

Why this matters: Keeping coherence out of the invariant set prevents
kernel inflation and maintains the minimal, non-negotiable nature of the
infrastructure layer.
"""
