"""
Change accounting ledger for the irrev vault.

This module treats structural changes as typed events that can be audited,
not just committed. It extends self-audit from static analysis to temporal
tracking.

Components:
- event_types: Canonical change event types (definition_refinement, dependency_change, etc.)
- classifier: Semantic change detection (before/after structural diff)
- ledger: Append-only event storage (.irrev/ledger.jsonl)
- queries: Temporal queries over the change history

Design principles:
- Append-only: events are never rewritten
- Structural: changes are typed by effect, not by file
- Accountable: invariant impact is tracked per change
- Non-prescriptive: surfaces what happened, not what should happen
"""

from .event_types import ChangeEvent, ChangeType
from .classifier import classify_change
from .ledger import ChangeAccountingLedger

__all__ = [
    "ChangeEvent",
    "ChangeType",
    "classify_change",
    "ChangeAccountingLedger",
]
