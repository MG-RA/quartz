"""
Append-only change ledger.

Stores structural change events in .irrev/ledger.jsonl.
Key property: append-only, never rewritten.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from .event_types import ChangeEvent, ChangeType


class ChangeAccountingLedger:
    """Append-only ledger for structural change events.

    Storage format: JSON Lines (.jsonl) - one event per line
    Location: .irrev/ledger.jsonl relative to vault root
    """

    def __init__(self, vault_path: Path):
        """Initialize ledger for a vault.

        Args:
            vault_path: Path to vault content directory
        """
        self.vault_path = vault_path.resolve()
        self.irrev_dir = self.vault_path.parent / ".irrev"
        self.ledger_path = self.irrev_dir / "ledger.jsonl"

    def _ensure_dir(self) -> None:
        """Ensure .irrev directory exists."""
        self.irrev_dir.mkdir(parents=True, exist_ok=True)

    def append(self, event: ChangeEvent) -> None:
        """Append a change event to the ledger.

        This is the only write operation. Events are never modified or deleted.
        """
        self._ensure_dir()
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), separators=(",", ":")) + "\n")

    def read_all(self) -> list[ChangeEvent]:
        """Read all events from the ledger."""
        if not self.ledger_path.exists():
            return []
        events = []
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(ChangeEvent.from_dict(json.loads(line)))
        return events

    def iter_events(self) -> Iterator[ChangeEvent]:
        """Iterate over events (memory-efficient for large ledgers)."""
        if not self.ledger_path.exists():
            return
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield ChangeEvent.from_dict(json.loads(line))

    def count(self) -> int:
        """Count total events in ledger."""
        if not self.ledger_path.exists():
            return 0
        count = 0
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    # --- Query methods ---

    def events_for_note(self, note_id: str) -> list[ChangeEvent]:
        """Get all events for a specific note."""
        return [e for e in self.iter_events() if e.note_id == note_id]

    def events_by_type(self, change_type: ChangeType) -> list[ChangeEvent]:
        """Get all events of a specific type."""
        return [e for e in self.iter_events() if change_type in e.change_types]

    def events_in_range(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[ChangeEvent]:
        """Get events within a time range."""
        events = []
        for e in self.iter_events():
            if start and e.timestamp < start:
                continue
            if end and e.timestamp > end:
                continue
            events.append(e)
        return events

    def events_affecting_invariant(self, invariant: str) -> list[ChangeEvent]:
        """Get events that affected a specific invariant."""
        events = []
        for e in self.iter_events():
            for impact in e.structural_effects.invariant_impacts:
                if impact.invariant == invariant:
                    events.append(e)
                    break
        return events

    # --- Summary methods ---

    def summary(self) -> dict:
        """Generate a summary of the ledger.

        Returns statistics about change patterns.
        """
        events = self.read_all()
        if not events:
            return {"total_events": 0}

        type_counts: dict[str, int] = {}
        note_counts: dict[str, int] = {}
        invariant_improved: dict[str, int] = {}
        invariant_degraded: dict[str, int] = {}
        total_ambiguity_delta = 0

        for e in events:
            for ct in e.change_types:
                type_counts[ct.value] = type_counts.get(ct.value, 0) + 1
            note_counts[e.note_id] = note_counts.get(e.note_id, 0) + 1
            total_ambiguity_delta += e.ambiguity_delta

            for impact in e.structural_effects.invariant_impacts:
                if impact.direction == "improved":
                    invariant_improved[impact.invariant] = (
                        invariant_improved.get(impact.invariant, 0) + 1
                    )
                elif impact.direction == "degraded":
                    invariant_degraded[impact.invariant] = (
                        invariant_degraded.get(impact.invariant, 0) + 1
                    )

        # Most changed notes
        most_changed = sorted(note_counts.items(), key=lambda x: -x[1])[:10]

        return {
            "total_events": len(events),
            "change_type_counts": type_counts,
            "most_changed_notes": most_changed,
            "total_ambiguity_delta": total_ambiguity_delta,
            "invariant_improvements": invariant_improved,
            "invariant_degradations": invariant_degraded,
            "time_range": {
                "earliest": events[0].timestamp.isoformat() if events else None,
                "latest": events[-1].timestamp.isoformat() if events else None,
            },
        }

    def format_summary(self) -> str:
        """Format summary as markdown."""
        s = self.summary()
        if s["total_events"] == 0:
            return "No change events recorded."

        lines = [
            "# Change Accounting Summary",
            "",
            f"- Total events: {s['total_events']}",
            f"- Time range: {s['time_range']['earliest']} to {s['time_range']['latest']}",
            f"- Net ambiguity delta: {s['total_ambiguity_delta']:+d}",
            "",
            "## Change Types",
            "",
            "| Type | Count |",
            "|------|------:|",
        ]
        for ct, count in sorted(s["change_type_counts"].items(), key=lambda x: -x[1]):
            lines.append(f"| {ct} | {count} |")

        lines.extend([
            "",
            "## Most Changed Notes",
            "",
            "| Note | Events |",
            "|------|-------:|",
        ])
        for note_id, count in s["most_changed_notes"]:
            lines.append(f"| {note_id} | {count} |")

        if s["invariant_improvements"] or s["invariant_degradations"]:
            lines.extend([
                "",
                "## Invariant Impact",
                "",
                "| Invariant | Improved | Degraded |",
                "|-----------|----------|----------|",
            ])
            all_invariants = set(s["invariant_improvements"].keys()) | set(
                s["invariant_degradations"].keys()
            )
            for inv in sorted(all_invariants):
                improved = s["invariant_improvements"].get(inv, 0)
                degraded = s["invariant_degradations"].get(inv, 0)
                lines.append(f"| {inv} | {improved} | {degraded} |")

        return "\n".join(lines) + "\n"
