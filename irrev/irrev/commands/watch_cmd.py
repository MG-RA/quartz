"""Watch command - observe vault drift as structural events."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from ..events import (
    ArtifactScope,
    EventKind,
    read_events_log,
    format_event,
)
from ..watcher import run_watch_loop


def run_watch(
    vault_path: Path,
    *,
    include_hash: bool = False,
    include_frontmatter: bool = False,
    scopes: set[str] | None = None,
) -> None:
    """
    Watch vault for file system events and log them.

    This is a blocking command that runs until interrupted (Ctrl+C).
    Events are logged to .irrev/events.log in JSON Lines format.
    """
    console = Console(stderr=True)

    # Convert scope strings to enum
    scope_filter: set[ArtifactScope] | None = None
    if scopes:
        scope_filter = set()
        for s in scopes:
            try:
                scope_filter.add(ArtifactScope(s.lower()))
            except ValueError:
                console.print(f"[yellow]Unknown scope: {s}[/yellow]")

    console.print(f"[bold]Watching[/bold] {vault_path}")
    console.print(f"  Hash tracking: {'on' if include_hash else 'off'}")
    console.print(f"  Frontmatter extraction: {'on' if include_frontmatter else 'off'}")
    if scope_filter:
        console.print(f"  Scopes: {', '.join(s.value for s in scope_filter)}")
    console.print()
    console.print("[dim]Press Ctrl+C to stop watching[/dim]")
    console.print()

    event_count = 0

    def on_event(formatted: str) -> None:
        nonlocal event_count
        event_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(f"[dim]{timestamp}[/dim] {formatted}")

    try:
        run_watch_loop(
            vault_path=vault_path,
            include_hash=include_hash,
            include_frontmatter=include_frontmatter,
            on_event=on_event,
            scopes=scope_filter,
        )
    except KeyboardInterrupt:
        console.print()
        console.print(f"[bold]Stopped.[/bold] Logged {event_count} events.")


def run_events(
    vault_path: Path,
    *,
    last_n: int | None = None,
    event_kinds: list[str] | None = None,
    scopes: list[str] | None = None,
    format: str = "text",
) -> int:
    """
    Read and display events from the events log.

    Returns the number of events displayed.
    """
    console = Console()

    # Convert filter strings to enums
    kind_filter: list[EventKind] | None = None
    if event_kinds:
        kind_filter = []
        for k in event_kinds:
            try:
                kind_filter.append(EventKind(k.lower()))
            except ValueError:
                console.print(f"[yellow]Unknown event kind: {k}[/yellow]", highlight=False)

    scope_filter: list[ArtifactScope] | None = None
    if scopes:
        scope_filter = []
        for s in scopes:
            try:
                scope_filter.append(ArtifactScope(s.lower()))
            except ValueError:
                console.print(f"[yellow]Unknown scope: {s}[/yellow]", highlight=False)

    events = read_events_log(
        vault_path=vault_path,
        last_n=last_n,
        event_kinds=kind_filter,
        scopes=scope_filter,
    )

    if not events:
        console.print("[dim]No events found.[/dim]")
        return 0

    if format == "json":
        import json

        for event in events:
            console.print(json.dumps(event.to_dict()))
    else:
        # Text format
        for event in events:
            console.print(format_event(event))
            console.print()

    return len(events)


def run_events_summary(vault_path: Path) -> int:
    """
    Display a summary of events in the log.

    Returns the total event count.
    """
    console = Console()

    events = read_events_log(vault_path=vault_path)

    if not events:
        console.print("[dim]No events logged yet.[/dim]")
        return 0

    # Count by kind
    kind_counts: dict[EventKind, int] = {}
    scope_counts: dict[ArtifactScope, int] = {}
    erasure_bytes = 0

    for event in events:
        kind_counts[event.event_kind] = kind_counts.get(event.event_kind, 0) + 1
        scope_counts[event.scope] = scope_counts.get(event.scope, 0) + 1
        if event.erasure:
            erasure_bytes += event.erasure.bytes_erased

    # Display summary
    table = Table(title="Event Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total events", str(len(events)))
    table.add_row("", "")

    # By kind
    for kind in EventKind:
        count = kind_counts.get(kind, 0)
        if count:
            icon = {
                EventKind.FILE_CREATED: "+",
                EventKind.FILE_MODIFIED: "~",
                EventKind.FILE_DELETED: "-",
                EventKind.FILE_RENAMED: ">",
            }.get(kind, "?")
            table.add_row(f"  {icon} {kind.value}", str(count))

    table.add_row("", "")

    # By scope
    for scope in ArtifactScope:
        count = scope_counts.get(scope, 0)
        if count:
            table.add_row(f"  [{scope.value}]", str(count))

    if erasure_bytes:
        table.add_row("", "")
        table.add_row("Total bytes erased", f"{erasure_bytes:,}")

    # Time range
    if events:
        first = events[0].timestamp[:19].replace("T", " ")
        last = events[-1].timestamp[:19].replace("T", " ")
        table.add_row("", "")
        table.add_row("First event", first)
        table.add_row("Last event", last)

    console.print(table)

    return len(events)
