"""Self-audit command - meta-lint the linter itself.

Per Failure Mode #10: "The most serious failure mode is assuming the lens
already accounts for its own limitations."

This command runs all self-audit scanners against the irrev codebase to detect:
- Prescriptive language in strings/docstrings
- Role separation violations (object/operator mixing)
- Self-exemption patterns (bypass mechanisms)
- Force gate coverage (destructive ops without --force)
- Audit logging coverage (state changes without logging)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class SelfAuditSummary:
    """Summary of self-audit findings."""

    prescriptive_count: int = 0
    role_separation_count: int = 0
    exemption_count: int = 0
    force_gate_issues: int = 0
    audit_coverage_gaps: int = 0

    @property
    def total_issues(self) -> int:
        return (
            self.prescriptive_count
            + self.role_separation_count
            + self.exemption_count
            + self.force_gate_issues
            + self.audit_coverage_gaps
        )

    def to_dict(self) -> dict:
        return asdict(self)


def run_self_audit(
    target: Path | None = None,
    *,
    output_format: str = "text",
    include_passing: bool = False,
) -> int:
    """
    Run all self-audit scanners against the irrev codebase.

    Args:
        target: Directory to scan (defaults to irrev package directory)
        output_format: "text", "json", or "md"
        include_passing: Whether to include passing checks in output

    Returns:
        Exit code (0 if no issues, 1 if issues found)
    """
    console = Console(stderr=True)

    # Default to the irrev package directory
    if target is None:
        target = Path(__file__).parent.parent

    console.print(f"[bold]Self-auditing[/bold] {target}")
    console.print()

    # Import scanners
    from ..self_audit.prescriptive_scan import scan_prescriptive_language, format_findings as fmt_prescriptive
    from ..self_audit.exemption_detect import scan_exemptions, format_findings as fmt_exemptions
    from ..self_audit.force_gates import scan_force_gates, format_findings as fmt_force_gates
    from ..self_audit.audit_coverage import scan_audit_coverage, format_findings as fmt_audit_coverage

    # Run all scanners
    prescriptive_matches = scan_prescriptive_language(target)
    exemption_matches = scan_exemptions(target)
    force_gate_matches = scan_force_gates(target)
    audit_coverage_matches = scan_audit_coverage(target)

    # Try to import role_separation if it exists
    try:
        from ..self_audit.role_separation import scan_role_separation, format_findings as fmt_role_separation
        role_separation_matches = scan_role_separation(target)
    except ImportError:
        role_separation_matches = []
        fmt_role_separation = lambda x: ""

    # Count issues
    summary = SelfAuditSummary(
        prescriptive_count=len(prescriptive_matches),
        role_separation_count=len(role_separation_matches),
        exemption_count=len(exemption_matches),
        force_gate_issues=len([m for m in force_gate_matches if m.gate_type == "missing_force_param"]),
        audit_coverage_gaps=len([m for m in audit_coverage_matches if m.coverage_type == "missing_logging"]),
    )

    if output_format == "json":
        result = {
            "summary": summary.to_dict(),
            "prescriptive": [
                {"file": m.file, "line": m.line, "type": m.pattern_type, "text": m.matched_text}
                for m in prescriptive_matches
            ],
            "exemptions": [
                {"file": m.file, "line": m.line, "type": m.exemption_type, "description": m.description}
                for m in exemption_matches
            ],
            "force_gates": [
                {"file": m.file, "line": m.line, "function": m.function_name, "type": m.gate_type}
                for m in force_gate_matches
            ],
            "audit_coverage": [
                {"file": m.file, "line": m.line, "function": m.function_name, "type": m.coverage_type}
                for m in audit_coverage_matches
            ],
        }
        print(json.dumps(result, indent=2))
        return 1 if summary.total_issues > 0 else 0

    # Text/Markdown output
    output_console = Console()

    # Summary table
    table = Table(title="Self-Audit Summary")
    table.add_column("Check", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Status")

    checks = [
        ("Prescriptive Language", summary.prescriptive_count),
        ("Role Separation", summary.role_separation_count),
        ("Self-Exemption Patterns", summary.exemption_count),
        ("Force Gate Issues", summary.force_gate_issues),
        ("Audit Coverage Gaps", summary.audit_coverage_gaps),
    ]

    for name, count in checks:
        if count == 0:
            status = "[green]✓[/green]"
        else:
            status = f"[yellow]{count} findings[/yellow]"
        if count > 0 or include_passing:
            table.add_row(name, str(count), status)

    output_console.print(table)
    output_console.print()

    # Detailed findings
    if output_format == "md":
        sections = []

        if prescriptive_matches:
            sections.append(fmt_prescriptive(prescriptive_matches))

        if role_separation_matches:
            sections.append(fmt_role_separation(role_separation_matches))

        if exemption_matches:
            sections.append(fmt_exemptions(exemption_matches))

        if force_gate_matches:
            sections.append(fmt_force_gates(force_gate_matches))

        if audit_coverage_matches:
            sections.append(fmt_audit_coverage(audit_coverage_matches))

        if sections:
            print("\n---\n".join(sections))
    else:
        # Text format - show condensed output
        if prescriptive_matches:
            output_console.print("[bold]Prescriptive Language:[/bold]")
            for m in prescriptive_matches[:10]:
                output_console.print(f"  {m.file}:{m.line} [{m.pattern_type}]")
            if len(prescriptive_matches) > 10:
                output_console.print(f"  ... and {len(prescriptive_matches) - 10} more")
            output_console.print()

        if exemption_matches:
            output_console.print("[bold]Self-Exemption Patterns:[/bold]")
            for m in exemption_matches[:10]:
                output_console.print(f"  {m.file}:{m.line} [{m.exemption_type}]")
            if len(exemption_matches) > 10:
                output_console.print(f"  ... and {len(exemption_matches) - 10} more")
            output_console.print()

        missing_force = [m for m in force_gate_matches if m.gate_type == "missing_force_param"]
        if missing_force:
            output_console.print("[bold]Missing Force Gates:[/bold]")
            for m in missing_force[:10]:
                output_console.print(f"  {m.file}:{m.line} `{m.function_name}`")
            if len(missing_force) > 10:
                output_console.print(f"  ... and {len(missing_force) - 10} more")
            output_console.print()

        missing_audit = [m for m in audit_coverage_matches if m.coverage_type == "missing_logging"]
        if missing_audit:
            output_console.print("[bold]Missing Audit Logging:[/bold]")
            for m in missing_audit[:10]:
                output_console.print(f"  {m.file}:{m.line} `{m.function_name}`")
            if len(missing_audit) > 10:
                output_console.print(f"  ... and {len(missing_audit) - 10} more")
            output_console.print()

    # Final status
    if summary.total_issues == 0:
        output_console.print("[green]All self-audit checks passed.[/green]")
        return 0
    else:
        output_console.print(f"[yellow]Found {summary.total_issues} total issues.[/yellow]")
        return 1
