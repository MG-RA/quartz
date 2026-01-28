"""Artifact ledger CLI commands."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ..artifact.events import ArtifactEvent
from ..artifact.plan_manager import PlanManager
from ..artifact.risk import compute_risk


def _manager(vault_path: Path) -> PlanManager:
    return PlanManager(vault_path)


def run_artifact_list(
    vault_path: Path,
    *,
    artifact_type: str | None = None,
    status: str | None = None,
) -> int:
    console = Console()
    mgr = _manager(vault_path)
    snapshots = list(mgr.ledger.all_snapshots().values())

    if artifact_type:
        snapshots = [s for s in snapshots if s.artifact_type == artifact_type]
    if status:
        snapshots = [s for s in snapshots if s.status == status]

    snapshots.sort(key=lambda s: (s.created_at.isoformat() if s.created_at else "", s.artifact_id))

    table = Table(title="Artifacts")
    table.add_column("artifact_id", style="cyan", no_wrap=True)
    table.add_column("type", style="magenta")
    table.add_column("status")
    table.add_column("risk")
    table.add_column("operation")
    table.add_column("content_id", style="dim")

    for s in snapshots:
        risk = s.computed_risk_class or s.risk_class
        table.add_row(
            s.artifact_id,
            s.artifact_type,
            s.status,
            risk.value if risk else "",
            str(s.producer.get("operation", "")),
            (s.content_id[:12] + "…") if s.content_id else "",
        )

    console.print(table)
    return 0


def run_artifact_show(vault_path: Path, artifact_id: str, *, output_json: bool = False) -> int:
    err = Console(stderr=True)
    mgr = _manager(vault_path)
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    content = mgr.content_store.get(snap.content_id) if snap.content_id else None
    data: dict[str, Any] = {
        "snapshot": {
            "artifact_id": snap.artifact_id,
            "content_id": snap.content_id,
            "artifact_type": snap.artifact_type,
            "status": snap.status,
            "risk_class": (snap.risk_class.value if snap.risk_class else None),
            "computed_risk_class": (snap.computed_risk_class.value if snap.computed_risk_class else None),
            "inputs": snap.inputs,
            "producer": snap.producer,
            "delegate_to": snap.delegate_to,
            "payload_manifest": snap.payload_manifest,
            "approval_artifact_id": snap.approval_artifact_id,
            "result_artifact_id": snap.result_artifact_id,
            "erasure_cost": snap.erasure_cost,
            "creation_summary": snap.creation_summary,
            "executor": snap.executor,
            "rejection_reason": snap.rejection_reason,
            "rejection_stage": snap.rejection_stage,
            "superseded_by": snap.superseded_by,
            "created_at": snap.created_at.isoformat() if snap.created_at else None,
            "validated_at": snap.validated_at.isoformat() if snap.validated_at else None,
            "approved_at": snap.approved_at.isoformat() if snap.approved_at else None,
            "executed_at": snap.executed_at.isoformat() if snap.executed_at else None,
        },
        "content": content,
    }

    if output_json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(json.dumps(data["snapshot"], indent=2, sort_keys=True))
    return 0


def run_artifact_status(vault_path: Path, artifact_id: str) -> int:
    err = Console(stderr=True)
    console = Console()
    mgr = _manager(vault_path)
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    next_gate = {
        "created": "validate",
        "validated": "approve" if snap.requires_approval() else "execute",
        "approved": "execute",
        "executed": "done",
        "rejected": "done",
        "superseded": "done",
    }.get(snap.status, "unknown")

    console.print(f"{snap.artifact_id}: {snap.status} (next: {next_gate})")
    if snap.requires_approval():
        console.print("  approval required", style="dim")
    if snap.approval_artifact_id:
        console.print(f"  approval: {snap.approval_artifact_id}", style="dim")
    return 0


def run_artifact_explain(vault_path: Path, artifact_id: str) -> int:
    err = Console(stderr=True)
    console = Console()
    mgr = _manager(vault_path)
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    content = mgr.content_store.get_json(snap.content_id) if snap.content_id else None
    operation = str(snap.producer.get("operation", "")) or (str(content.get("operation")) if content else "")
    payload = content.get("payload") if isinstance(content, dict) else {}
    payload = payload if isinstance(payload, dict) else {}
    risk, reasons = compute_risk(operation, payload)

    console.print(f"artifact_id: {snap.artifact_id}")
    console.print(f"type: {snap.artifact_type}  status: {snap.status}")
    console.print(f"operation: {operation}")
    console.print(f"risk_class: {risk.value}")
    for r in reasons:
        console.print(f"  - {r}", style="dim")
    if snap.requires_approval():
        console.print("approval required", style="yellow")
    return 0


def run_artifact_approve(
    vault_path: Path,
    artifact_id: str,
    *,
    approver: str,
    force: bool,
    scope: str | None,
) -> int:
    err = Console(stderr=True)
    mgr = _manager(vault_path)
    try:
        approval_id = mgr.approve(artifact_id, approver, scope=scope, force_ack=force)
    except Exception as e:
        err.print(str(e), style="bold red")
        return 1
    err.print(f"approved: {artifact_id}", style="green")
    err.print(f"approval_artifact_id: {approval_id}", style="dim")
    return 0


# -----------------------------------------------------------------------------
# Formatting Helpers for Phase 6 CLI Commands
# -----------------------------------------------------------------------------


def _format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"


def _format_timestamp_condensed(dt: datetime) -> str:
    """Format timestamp as HH:MM:SS for timeline view."""
    return dt.strftime("%H:%M:%S")


def _format_resources(resources: dict[str, Any] | None) -> str:
    """Format resource usage as compact string."""
    if not resources:
        return ""
    parts = []
    # Common keys
    if "cpu_percent" in resources:
        parts.append(f"cpu={resources['cpu_percent']:.0f}%")
    if "memory_mb" in resources:
        parts.append(f"mem={resources['memory_mb']:.0f}MB")
    if "items_processed" in resources:
        parts.append(f"items={resources['items_processed']}")
    if "bytes_written" in resources:
        mb = resources["bytes_written"] / (1024 * 1024)
        parts.append(f"written={mb:.1f}MB")
    return ", ".join(parts) if parts else ""


def _truncate(text: str, max_len: int = 80) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


def _format_event_details(event: ArtifactEvent) -> str:
    """
    Format event payload as compact key=value string.

    Whitelists important keys per event type for readability.
    """
    event_type = event.event_type
    payload = event.payload

    if event_type == "artifact.created":
        parts = [f"status={payload.get('status', 'created')}"]
        if "artifact_type" in payload:
            parts.append(f"type={payload['artifact_type']}")
        return ", ".join(parts)

    elif event_type == "artifact.validated":
        validator = payload.get("validator", "unknown")
        errors = payload.get("errors", [])
        if errors:
            return f"validator={validator}, errors={len(errors)}"
        return f"validator={validator}"

    elif event_type == "artifact.approved":
        approver = event.actor
        scope = payload.get("scope", "")
        if scope:
            return f"approver={approver}, scope={_truncate(scope, 40)}"
        return f"approver={approver}"

    elif event_type == "artifact.executed":
        executor = payload.get("executor", "unknown")
        return f"executor={executor}"

    elif event_type == "artifact.rejected":
        reason = _truncate(payload.get("reason", ""), 50)
        stage = payload.get("stage", "unknown")
        return f"stage={stage}, reason={reason}"

    elif event_type == "artifact.superseded":
        superseded_by = payload.get("superseded_by", "")
        return f"superseded_by={superseded_by}"

    elif event_type == "constraint.evaluated":
        ruleset_id = payload.get("ruleset_id", "?")
        result = payload.get("result", "?")
        invariant = payload.get("invariant", "")
        if invariant:
            return f"ruleset={ruleset_id}, result={result}, invariant={invariant}"
        return f"ruleset={ruleset_id}, result={result}"

    elif event_type == "invariant.checked":
        invariant_id = payload.get("invariant_id", "?")
        status = payload.get("status", "?")
        violations = payload.get("violations", 0)
        if violations > 0:
            return f"invariant={invariant_id}, status={status}, violations={violations}"
        return f"invariant={invariant_id}, status={status}"

    elif event_type == "execution.logged":
        phase = payload.get("phase", "?")
        status = payload.get("status", "?")
        handler_id = payload.get("handler_id", "?")
        return f"phase={phase}, status={status}, handler={handler_id}"

    # Fallback: safe scalar keys
    safe_keys = [k for k, v in payload.items() if isinstance(v, (str, int, float, bool)) and k not in {"timestamp", "event_id"}]
    if safe_keys:
        parts = [f"{k}={payload[k]}" for k in safe_keys[:3]]
        return ", ".join(parts)

    return ""


def _map_status_friendly(status: str) -> str:
    """Map internal status to friendly CLI display."""
    mapping = {
        "completed": "success",
        "failed": "failure",
        "pass": "ok",
        "fail": "violated",
        "skipped": "skipped",
        "started": "started",
    }
    return mapping.get(status, status)


# -----------------------------------------------------------------------------
# Phase 6 CLI Command Implementations
# -----------------------------------------------------------------------------


def run_artifact_audit(
    vault_path: Path,
    artifact_id: str,
    *,
    output_json: bool = False,
    limit: int | None = None,
) -> int:
    """Show full chronological audit trail for an artifact."""
    err = Console(stderr=True)
    mgr = _manager(vault_path)

    # Verify artifact exists
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    # Call query method
    events = mgr.ledger.audit_trail(artifact_id)
    if limit and limit > 0:
        events = events[:limit]

    if output_json:
        # JSON output to stdout
        print(json.dumps([e.to_dict() for e in events], indent=2))
        return 0

    # Rich formatted output to stdout
    console = Console()
    table = Table(title=f"Audit Trail: {artifact_id}")
    table.add_column("Timestamp", style="dim")
    table.add_column("Event Type", style="cyan")
    table.add_column("Details")

    for event in events:
        table.add_row(
            event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            event.event_type,
            _format_event_details(event),
        )

    console.print(table)
    console.print(f"\nEvents: {len(events)} total")
    return 0


def run_artifact_execution(
    vault_path: Path,
    artifact_id: str | None = None,
    *,
    execution_id: str | None = None,
    phase: str | None = None,
    status: str | None = None,
    output_json: bool = False,
) -> int:
    """Show execution logs for an artifact or execution_id."""
    err = Console(stderr=True)
    mgr = _manager(vault_path)

    # At least one ID must be provided
    if not artifact_id and not execution_id:
        err.print("Error: Must provide either --artifact-id or --execution-id", style="bold red")
        return 1

    # Verify artifact exists if artifact_id provided
    if artifact_id:
        snap = mgr.ledger.snapshot(artifact_id)
        if snap is None:
            err.print(f"Artifact not found: {artifact_id}", style="bold red")
            return 1

    # Call query method
    logs = mgr.ledger.execution_logs(
        artifact_id=artifact_id,
        execution_id=execution_id,
        phase=phase,
        status=status,
    )

    if output_json:
        # JSON output to stdout
        print(json.dumps([log.to_dict() for log in logs], indent=2))
        return 0

    # Rich formatted output to stdout
    console = Console()
    title = f"Execution Logs: {artifact_id or execution_id}"
    table = Table(title=title)
    table.add_column("Execution ID", style="cyan", no_wrap=True)
    table.add_column("Phase", style="magenta")
    table.add_column("Status")
    table.add_column("Handler", style="dim")
    table.add_column("Duration", justify="right")
    table.add_column("Resources")

    for log in logs:
        duration_str = _format_duration(log.duration_ms / 1000) if log.duration_ms else ""
        status_display = _map_status_friendly(log.status)
        table.add_row(
            log.execution_id[:12] + "…" if len(log.execution_id) > 12 else log.execution_id,
            log.phase,
            status_display,
            log.handler_id,
            duration_str,
            _format_resources(log.resources),
        )

    console.print(table)

    # Summary
    total = len(logs)
    successful = len([log for log in logs if log.status == "completed"])
    console.print(f"\nExecutions: {total} total, {successful} successful")

    return 0


def run_artifact_constraints(
    vault_path: Path,
    artifact_id: str,
    *,
    ruleset: str | None = None,
    result: str | None = None,
    status: str | None = None,
    output_json: bool = False,
) -> int:
    """Show constraint evaluations and invariant checks for an artifact."""
    err = Console(stderr=True)
    mgr = _manager(vault_path)

    # Verify artifact exists
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    # Get constraint summary to check data status
    constraint_summary = mgr.ledger.constraint_summary(artifact_id)

    # Call query methods
    evaluations = mgr.ledger.constraint_evaluations(
        artifact_id,
        ruleset_id=ruleset,
        result=result,
    )
    checks = mgr.ledger.invariant_checks(
        artifact_id,
        status=status,
    )

    if output_json:
        # JSON output to stdout
        data = {
            "constraint_data_status": constraint_summary.constraint_data_status,
            "evaluations": [e.to_dict() for e in evaluations],
            "checks": [c.to_dict() for c in checks],
        }
        print(json.dumps(data, indent=2))
        return 0

    # Rich formatted output to stdout
    console = Console()

    # Handle missing constraint data
    if constraint_summary.constraint_data_status == "missing":
        console.print(f"[bold]Constraints: {artifact_id}[/bold]")
        console.print("\n[cyan]ℹ[/cyan] No constraint data (artifact predates Phase 3)")
        return 0

    if constraint_summary.constraint_data_status == "partial":
        console.print(f"[bold]Constraints: {artifact_id}[/bold]")
        console.print("\n[yellow]⚠[/yellow] Partial constraint data (some rulesets not logged)\n")

    # Constraint Evaluations table
    if evaluations:
        table1 = Table(title="Constraint Evaluations")
        table1.add_column("Ruleset", style="cyan")
        table1.add_column("Invariant")
        table1.add_column("Result")
        table1.add_column("Evidence", style="dim")

        for ev in evaluations:
            result_style = "green" if ev.result == "pass" else ("red" if ev.result == "fail" else "yellow")
            evidence_str = str(ev.evidence.get("message", ""))[:50]
            table1.add_row(
                ev.ruleset_id,
                ev.invariant,
                f"[{result_style}]{_map_status_friendly(ev.result)}[/{result_style}]",
                evidence_str,
            )

        console.print(table1)

    # Invariant Checks table
    if checks:
        table2 = Table(title="\nInvariant Checks")
        table2.add_column("Invariant", style="cyan")
        table2.add_column("Status")
        table2.add_column("Violations", justify="right")

        for check in checks:
            status_style = "green" if check.status == "pass" else "red"
            table2.add_row(
                check.invariant_id,
                f"[{status_style}]{_map_status_friendly(check.status)}[/{status_style}]",
                str(check.violations),
            )

        console.print(table2)

    # Summary
    total_evals = len(evaluations)
    passed = len([e for e in evaluations if e.result == "pass"])
    failed = len([e for e in evaluations if e.result == "fail"])
    warnings = len([e for e in evaluations if e.result == "warning"])

    total_checks = len(checks)
    checks_ok = len([c for c in checks if c.status == "pass"])
    checks_violated = len([c for c in checks if c.status == "fail"])

    console.print(f"\nSummary: {total_evals} evaluations ({passed} allow, {failed} deny, {warnings} warning), " +
                  f"{total_checks} checks ({checks_ok} ok, {checks_violated} violated)")

    return 0


def run_artifact_timeline(
    vault_path: Path,
    artifact_id: str,
    *,
    full: bool = False,
    limit: int | None = None,
    output_json: bool = False,
) -> int:
    """Show condensed chronological timeline for an artifact."""
    err = Console(stderr=True)
    mgr = _manager(vault_path)

    # Verify artifact exists
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    # Call query method
    events = mgr.ledger.audit_trail(artifact_id)
    if limit and limit > 0:
        events = events[:limit]

    if output_json:
        # JSON output to stdout
        print(json.dumps([e.to_dict() for e in events], indent=2))
        return 0

    # Rich formatted output to stdout
    console = Console()
    console.print(f"[bold]Timeline: {artifact_id}[/bold]\n")

    # Map event types to symbols
    symbols = {
        "artifact.created": "●",
        "artifact.validated": "✓",
        "artifact.approved": "✓",
        "artifact.executed": "✓",
        "artifact.rejected": "✗",
        "artifact.superseded": "⇢",
        "constraint.evaluated": "▹",
        "invariant.checked": "▹",
        "execution.logged": "▸",
    }

    for event in events:
        symbol = symbols.get(event.event_type, "·")
        if full:
            timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp = _format_timestamp_condensed(event.timestamp)

        # Condense event type display
        event_display = event.event_type.replace("artifact.", "").replace("constraint.", "").replace("invariant.", "").replace("execution.", "")
        details = _format_event_details(event)

        if details:
            console.print(f"{timestamp}  {symbol} {event_display} ({details})")
        else:
            console.print(f"{timestamp}  {symbol} {event_display}")

    # Summary
    if events:
        first = events[0].timestamp
        last = events[-1].timestamp
        duration = (last - first).total_seconds()
        console.print(f"\nStatus: {snap.status} | Duration: {_format_duration(duration)} | Events: {len(events)}")

    return 0


def run_artifact_summary(
    vault_path: Path,
    artifact_id: str,
    *,
    execution_id: str | None = None,
    output_json: bool = False,
) -> int:
    """Show combined execution + constraint summary for an artifact."""
    err = Console(stderr=True)
    mgr = _manager(vault_path)

    # Verify artifact exists
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    # Determine execution_id: user-provided or latest
    if not execution_id:
        execution_id = mgr.ledger.latest_execution_id(artifact_id)

    # Get summaries
    exec_summary = mgr.ledger.execution_summary(execution_id) if execution_id else None
    constraint_summary = mgr.ledger.constraint_summary(artifact_id)
    invariant_summary = mgr.ledger.invariant_summary(artifact_id)

    if output_json:
        # JSON output to stdout
        data: dict[str, Any] = {
            "artifact_id": artifact_id,
            "snapshot": {
                "status": snap.status,
                "artifact_type": snap.artifact_type,
                "created_at": snap.created_at.isoformat() if snap.created_at else None,
                "validated_at": snap.validated_at.isoformat() if snap.validated_at else None,
                "approved_at": snap.approved_at.isoformat() if snap.approved_at else None,
                "executed_at": snap.executed_at.isoformat() if snap.executed_at else None,
            },
            "execution_summary": exec_summary.to_dict() if exec_summary else None,
            "constraint_summary": constraint_summary.to_dict(),
            "invariant_summary": invariant_summary.to_dict(),
        }
        print(json.dumps(data, indent=2))
        return 0

    # Rich formatted output to stdout
    console = Console()
    console.print(f"[bold]Summary: {artifact_id}[/bold]\n")

    # Execution Summary
    if exec_summary:
        table1 = Table(title="Execution Summary")
        table1.add_column("Field", style="cyan")
        table1.add_column("Value")

        overall_status_display = _map_status_friendly(exec_summary.overall_status)
        status_style = "green" if exec_summary.overall_status == "success" else "red"

        table1.add_row("Execution ID", exec_summary.execution_id[:12] + "…")
        table1.add_row("Overall Status", f"[{status_style}]{overall_status_display}[/{status_style}]")
        table1.add_row("Total Duration", _format_duration(exec_summary.total_duration_ms / 1000))

        # Phase breakdown
        phases_str = " → ".join([f"{phase} ({_format_duration(dur/1000)})" for phase, dur in exec_summary.phase_durations.items()])
        table1.add_row("Phases", phases_str)
        table1.add_row("Handler", exec_summary.handler_id)

        # Show failure phase prominently if failure
        if exec_summary.failure_phase:
            table1.add_row("Failure Phase", f"[red]{exec_summary.failure_phase}[/red] ← check this phase")

        # Resources summary
        resources_str = _format_resources(exec_summary.resources)
        if resources_str:
            table1.add_row("Resources", resources_str)

        console.print(table1)
        console.print()

    # Constraint Summary
    table2 = Table(title="Constraint Summary")
    table2.add_column("Field", style="cyan")
    table2.add_column("Value")

    table2.add_row("Evaluations", f"{constraint_summary.total_rules_checked} total " +
                   f"({constraint_summary.passed} allow, {constraint_summary.failed} deny, {constraint_summary.warnings} warning)")
    table2.add_row("Invariant Checks", f"{len(invariant_summary.invariants_checked)} total " +
                   f"({len([v for v in invariant_summary.violations if v])} violated)")

    data_status_style = "green" if constraint_summary.constraint_data_status == "present" else "yellow"
    table2.add_row("Data Status", f"[{data_status_style}]{constraint_summary.constraint_data_status}[/{data_status_style}]")

    console.print(table2)
    console.print()

    # Lifecycle
    table3 = Table(title="Lifecycle")
    table3.add_column("Stage", style="cyan")
    table3.add_column("Timestamp")

    if snap.created_at:
        table3.add_row("Created", snap.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    if snap.validated_at:
        table3.add_row("Validated", snap.validated_at.strftime("%Y-%m-%d %H:%M:%S"))
    if snap.approved_at:
        table3.add_row("Approved", snap.approved_at.strftime("%Y-%m-%d %H:%M:%S"))
    if snap.executed_at:
        table3.add_row("Executed", snap.executed_at.strftime("%Y-%m-%d %H:%M:%S"))

    console.print(table3)

    return 0

