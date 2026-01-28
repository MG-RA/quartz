"""CLI entrypoint for irrev."""

import sys
from pathlib import Path

import click

from . import __version__

def _auto_detect_vault(start: Path) -> Path | None:
    """Find a ./content vault folder by walking up from `start`."""
    cur = start.resolve()
    for p in (cur, *cur.parents):
        if p.is_dir() and p.name.lower() == "content":
            return p
        candidate = p / "content"
        if candidate.is_dir():
            return candidate
    return None


@click.group()
@click.version_option(__version__, prog_name="irrev")
@click.option(
    "--vault",
    "-v",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Path to vault content directory (defaults to auto-detected ./content)",
)
@click.pass_context
def cli(ctx: click.Context, vault: Path | None) -> None:
    """irrev - Semantic compiler for the irreversibility vault.

    Lint, pack, and generate registry artifacts from your vault.
    """
    ctx.ensure_object(dict)
    if vault is None:
        detected = _auto_detect_vault(Path.cwd())
        if detected is None:
            raise click.ClickException("Vault not found. Pass --vault /path/to/content or run from inside the repo.")
        vault = detected

    if not vault.exists() or not vault.is_dir():
        raise click.BadParameter(f"Directory '{vault}' does not exist.", param_hint="--vault / -v")

    ctx.obj["vault"] = vault.resolve()


@cli.command()
@click.option(
    "--fail-on",
    type=click.Choice(["error", "warning"]),
    default="error",
    help="Exit with error if this level or higher found",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON",
)
@click.option(
    "--flat",
    is_flag=True,
    help="Use flat output (legacy) instead of invariant-grouped (default)",
)
@click.option(
    "--invariant",
    "invariant_filter",
    type=str,
    default=None,
    metavar="INVARIANT_ID",
    help="Only run rules for this invariant (e.g., --invariant decomposition)",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat unclassified rules as errors (prevents scope creep in CI)",
)
@click.option(
    "--summary",
    is_flag=True,
    help="Print only invariant status line (for commits/docs)",
)
@click.option(
    "--explain",
    "explain_rule",
    type=str,
    default=None,
    metavar="RULE_ID",
    help="Explain a specific rule and exit (e.g., --explain layer-violation)",
)
@click.option(
    "--explain-invariant",
    "explain_invariant_id",
    type=str,
    default=None,
    metavar="INVARIANT_ID",
    help="Explain an invariant and its rules (e.g., --explain-invariant decomposition)",
)
@click.option(
    "--trace",
    "trace_note",
    type=str,
    default=None,
    metavar="NOTE",
    help="Show dependency chain for a specific note (e.g., --trace admissibility)",
)
@click.pass_context
def lint(
    ctx: click.Context,
    fail_on: str,
    output_json: bool,
    flat: bool,
    invariant_filter: str | None,
    strict: bool,
    summary: bool,
    explain_rule: str | None,
    explain_invariant_id: str | None,
    trace_note: str | None,
) -> None:
    """Check vault for structural violations.

    By default, results are grouped by invariant to surface infrastructure-level
    failure modes. Use --flat for legacy file-based output.

    The 4 kernel invariants:
    - decomposition: Objects/operators separation, role boundaries, no function merging
    - governance: Non-exemption, enforceability, self-correction surfaces
    - attribution: Responsibility mapping, diagnostics can't prescribe, no misplaced blame
    - irreversibility: Persistence, erasure cost declaration, accounting requirements, rollback denial

    Structural rules (dependency-cycle, broken-link, alias-drift) ensure graph coherence,
    which emerges from joint invariant compliance.

    Use --explain RULE_ID to see detailed documentation for a rule.
    Use --explain-invariant INVARIANT_ID to see what an invariant enforces.
    Use --trace NOTE to see the dependency chain for a specific note.
    """
    from .commands.lint import run_explain, run_explain_invariant, run_lint, run_trace

    # Handle --explain-invariant mode
    if explain_invariant_id:
        exit_code = run_explain_invariant(explain_invariant_id)
        sys.exit(exit_code)

    # Handle --explain mode
    if explain_rule:
        exit_code = run_explain(explain_rule)
        sys.exit(exit_code)

    # Handle --trace mode
    if trace_note:
        exit_code = run_trace(ctx.obj["vault"], trace_note)
        sys.exit(exit_code)

    exit_code = run_lint(ctx.obj["vault"], fail_on, output_json, flat, invariant_filter, strict, summary)
    sys.exit(exit_code)


@cli.command()
@click.argument("kind", type=click.Choice(["domain", "concept", "projection"]))
@click.argument("target")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "json", "txt"]),
    default="md",
    help="Output format",
)
@click.option(
    "--include-diagnostics",
    is_flag=True,
    help="Include diagnostic notes in pack",
)
@click.option(
    "--explain",
    is_flag=True,
    help="Explain why each file is included",
)
@click.pass_context
def pack(
    ctx: click.Context,
    kind: str,
    target: str,
    output_format: str,
    include_diagnostics: bool,
    explain: bool,
) -> None:
    """Generate context packs deterministically.

    Examples:

        irrev pack domain "2012-2026 AI Systems"

        irrev pack concept irreversibility --explain

        irrev pack projection Stoicism --include-diagnostics
    """
    from .commands.pack import run_pack

    exit_code = run_pack(
        ctx.obj["vault"],
        kind,
        target,
        output_format,
        include_diagnostics,
        explain,
    )
    sys.exit(exit_code)


@cli.group()
def registry() -> None:
    """Registry generation commands."""
    pass


@registry.command("build")
@click.option(
    "--out",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--in-place",
    is_flag=True,
    help="Update existing registry note in-place (preserves narrative; replaces generated region)",
)
@click.option(
    "--overrides",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default=None,
    help="Optional YAML overrides file for ordering/roles (default: <vault>/meta/registry.overrides.yml if present)",
)
@click.option(
    "--allow-unknown-layers",
    is_flag=True,
    help="Allow concepts with layers not present in LAYER_ORDER (emits an Unclassified section)",
)
@click.option(
    "--registry-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Explicit registry markdown path (for in-place updates or diffs)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without executing (diagnostic only)",
)
@click.pass_context
def registry_build(
    ctx: click.Context,
    out: Path | None,
    in_place: bool,
    overrides: Path | None,
    allow_unknown_layers: bool,
    registry_path: Path | None,
    dry_run: bool,
) -> None:
    """Generate registry from vault concepts.

    Reads concept layers and dependencies, produces markdown tables
    matching the Registry format.

    Examples:

        irrev registry build

        irrev registry build --out Registry.generated.md
    """
    from rich.console import Console
    from .commands.registry import run_build

    console = Console(stderr=True)

    # Governance: in-place modification is a write operation
    if in_place:
        console.print("[yellow]⚠ Governance notice:[/] --in-place will modify the Registry note directly.", style="dim")

    default_overrides = (ctx.obj["vault"] / "meta" / "registry.overrides.yml").resolve()
    overrides_path = overrides or (default_overrides if default_overrides.exists() else None)

    exit_code = run_build(
        ctx.obj["vault"],
        str(out) if out else None,
        in_place=in_place,
        overrides=overrides_path,
        allow_unknown_layers=allow_unknown_layers,
        registry_path=registry_path,
        dry_run=dry_run,
    )
    sys.exit(exit_code)


@registry.command("diff")
@click.option(
    "--overrides",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default=None,
    help="Optional YAML overrides file for ordering/roles (default: <vault>/meta/registry.overrides.yml if present)",
)
@click.option(
    "--allow-unknown-layers",
    is_flag=True,
    help="Allow concepts with layers not present in LAYER_ORDER (emits an Unclassified section)",
)
@click.option(
    "--registry-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Explicit registry markdown path to compare against",
)
@click.pass_context
def registry_diff(
    ctx: click.Context,
    overrides: Path | None,
    allow_unknown_layers: bool,
    registry_path: Path | None,
) -> None:
    """Compare generated registry with existing Registry file.

    Shows differences between what the concepts define and what
    the Registry file contains.
    """
    from .commands.registry import run_diff

    default_overrides = (ctx.obj["vault"] / "meta" / "registry.overrides.yml").resolve()
    overrides_path = overrides or (default_overrides if default_overrides.exists() else None)

    exit_code = run_diff(
        ctx.obj["vault"],
        overrides=overrides_path,
        allow_unknown_layers=allow_unknown_layers,
        registry_path=registry_path,
    )
    sys.exit(exit_code)


@cli.command()
@click.argument(
    "csv_folder",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write output to a file (default: stdout)",
)
def audit(csv_folder: Path, out: Path | None) -> None:
    """Generate structural vault report from CSV exports.

    Parses Obsidian Bases CSV exports and generates a Markdown report
    using the irreversibility accounting framework vocabulary.

    CSV_FOLDER should contain exports like:

    \b
    - Concept topology.csv
    - Dependency audit.csv
    - Primitive coverage audit.csv
    - Diagnostics inventory.csv
    - Projections.csv
    - Invariants inventory.csv
    - Full vault audit.csv

    Examples:

        irrev audit "./content/exports bases"

        irrev audit "./content/exports bases" --out report.md
    """
    from .commands.audit import run_audit

    exit_code = run_audit(csv_folder, out=out)
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--concepts-only/--all-notes",
    "concepts_only",
    default=True,
    show_default=True,
    help="Use concept structural dependencies only, or include all-note wiki-links as additional dependents",
)
@click.option("--top", type=int, default=25, show_default=True, help="Max candidates to display")
@click.option("--min-mechanisms", type=int, default=1, show_default=True, help="Min mechanism-layer dependents")
@click.option("--min-accounting", type=int, default=1, show_default=True, help="Min accounting-layer dependents")
@click.option("--min-failure-states", type=int, default=1, show_default=True, help="Min failure-state dependents")
@click.option(
    "--rank",
    type=click.Choice(["legacy", "score"]),
    default="legacy",
    show_default=True,
    help="Ranking strategy (legacy keeps current ordering; score uses weighted score)",
)
@click.option("--w-mechanism", type=float, default=1.0, show_default=True, help="Weight for mechanism-layer refs")
@click.option("--w-accounting", type=float, default=1.0, show_default=True, help="Weight for accounting-layer refs")
@click.option("--w-failure", type=float, default=1.0, show_default=True, help="Weight for failure-state refs")
@click.option("--w-selector", type=float, default=1.0, show_default=True, help="Weight for selector/meta refs")
@click.option("--w-layers", type=float, default=1.0, show_default=True, help="Weight for distinct dependent layers")
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    default=False,
    help="Show all concepts (ignore min thresholds)",
)
@click.option(
    "--exclude-layer",
    "exclude_layers",
    multiple=True,
    default=("mechanism", "failure-state"),
    show_default=True,
    help="Exclude concepts of this layer from being candidates (repeatable)",
)
@click.pass_context
def hubs(
    ctx: click.Context,
    concepts_only: bool,
    top: int,
    min_mechanisms: int,
    min_accounting: int,
    min_failure_states: int,
    rank: str,
    w_mechanism: float,
    w_accounting: float,
    w_failure: float,
    w_selector: float,
    w_layers: float,
    show_all: bool,
    exclude_layers: tuple[str, ...],
) -> None:
    """Detect latent hub candidates from cross-layer dependency concentration."""
    from rich.console import Console
    from .commands.hubs import run_hubs

    console = Console(stderr=True)

    # Governance: notify when exclusion filters are active
    if exclude_layers:
        console.print(f"[yellow]⚠ Governance notice:[/] --exclude-layer active; layers {exclude_layers} are excluded from candidates.", style="dim")

    exit_code = run_hubs(
        ctx.obj["vault"],
        concepts_only=concepts_only,
        top=top,
        min_mechanisms=min_mechanisms,
        min_accounting=min_accounting,
        min_failure_states=min_failure_states,
        candidates_only=not show_all,
        exclude_layers=set(exclude_layers),
        rank=rank,
        w_mechanism=w_mechanism,
        w_accounting=w_accounting,
        w_failure=w_failure,
        w_selector=w_selector,
        w_layers=w_layers,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--concepts-only/--all-notes",
    "concepts_only",
    default=True,
    show_default=True,
    help="Use concept structural dependencies only, or include all-note wiki-links",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["rich", "md", "json", "dot", "svg", "html"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option(
    "--styled/--plain",
    "styled",
    default=True,
    show_default=True,
    help="For dot/svg/html output: annotate nodes with layer colors and hub class badges",
)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Write output to a file")
@click.option("--top", type=int, default=25, show_default=True, help="How many nodes to show in top lists")
@click.pass_context
def graph(
    ctx: click.Context,
    concepts_only: bool,
    fmt: str,
    styled: bool,
    out: Path | None,
    top: int,
) -> None:
    """Inspect dependency/link graph structure."""
    from .commands.graph_cmd import run_graph

    exit_code = run_graph(ctx.obj["vault"], concepts_only=concepts_only, fmt=fmt, out=out, top=top, styled=styled)
    sys.exit(exit_code)


@cli.command("communities")
@click.option(
    "--mode",
    type=click.Choice(["links", "depends_on", "both"]),
    default="links",
    show_default=True,
    help="How to build the concept graph before community detection",
)
@click.option(
    "--algorithm",
    type=click.Choice(["greedy", "lpa"]),
    default="greedy",
    show_default=True,
    help="Community detection algorithm",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["md", "json"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Write output to a file")
@click.option("--max-iter", type=int, default=50, show_default=True, help="Label propagation iterations")
@click.pass_context
def communities(ctx: click.Context, mode: str, algorithm: str, fmt: str, out: Path | None, max_iter: int) -> None:
    """Run community detection on concepts and compare to declared layers."""
    from .commands.graph_cmd import run_communities

    sys.exit(run_communities(ctx.obj["vault"], mode=mode, algorithm=algorithm, out=out, fmt=fmt, max_iter=max_iter))


@cli.group()
def junctions() -> None:
    """Detect routing pressure and candidate missing concepts."""
    pass


@junctions.command("concept-audit")
@click.option("--top", type=int, default=25, show_default=True, help="How many concepts to audit (by in-degree)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "json"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Write output to a file")
@click.option("--all", "include_all", is_flag=True, default=False, help="Audit all concepts (ignores --top)")
@click.pass_context
def junctions_concept_audit(
    ctx: click.Context,
    top: int,
    output_format: str,
    out: Path | None,
    include_all: bool,
) -> None:
    """Generate a concept audit report (Phase 1)."""
    from .commands.junctions import run_concept_audit

    exit_code = run_concept_audit(ctx.obj["vault"], out=out, top=top, fmt=output_format, include_all=include_all)
    sys.exit(exit_code)


@junctions.command("definition-analysis")
@click.option("--top", type=int, default=25, show_default=True, help="How many concepts to analyze (by in-degree)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "json"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Write output to a file")
@click.option("--all", "include_all", is_flag=True, default=False, help="Analyze all concepts (ignores --top)")
@click.pass_context
def junctions_definition_analysis(
    ctx: click.Context,
    top: int,
    output_format: str,
    out: Path | None,
    include_all: bool,
) -> None:
    """Analyze definition semantics: verbs, patterns, implicit deps (Phase 1b).

    Examines concept definitions for:

    \b
    - Verb patterns (state/action/modal/causal)
    - Negation density and operational framing
    - Cost language and spatial metaphors
    - Implicit dependencies (mentioned but not linked)
    - Role purity (prescriptive vs descriptive)
    - Definition scope metrics (sentences vs NOT items)

    Examples:

        irrev junctions definition-analysis --top 10

        irrev junctions definition-analysis --all --format json
    """
    from .commands.junctions import run_definition_analysis

    exit_code = run_definition_analysis(ctx.obj["vault"], out=out, top=top, fmt=output_format, include_all=include_all)
    sys.exit(exit_code)


@junctions.command("domain-audit")
@click.option(
    "--domain",
    "domain_filter",
    type=str,
    default=None,
    metavar="DOMAIN",
    help='Limit to a single domain (matches name/title; e.g., --domain "Digital Platforms")',
)
@click.option(
    "--via",
    "via_mode",
    type=click.Choice(["links", "depends_on", "both"]),
    default="links",
    show_default=True,
    help="How to compute the concept -> concept hop (links mirrors Neo4j LINKS_TO)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "json"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Write output to a file")
@click.pass_context
def junctions_domain_audit(
    ctx: click.Context,
    domain_filter: str | None,
    via_mode: str,
    output_format: str,
    out: Path | None,
) -> None:
    """Audit domains for implied concept dependencies (2-hop via concept depends_on)."""
    from .commands.junctions import run_domain_audit

    exit_code = run_domain_audit(ctx.obj["vault"], domain=domain_filter, via=via_mode, out=out, fmt=output_format)
    sys.exit(exit_code)


@junctions.command("implicit")
@click.option(
    "--role",
    "role_name",
    type=click.Choice(["domain", "projection", "paper", "diagnostic", "concept", "meta", "support", "invariant"]),
    default="domain",
    show_default=True,
    help="Which note role to audit",
)
@click.option(
    "--note",
    "note_filter",
    type=str,
    default=None,
    metavar="NOTE",
    help='Limit to a single note (matches name/title; e.g., --note "OpenAI")',
)
@click.option(
    "--via",
    "via_mode",
    type=click.Choice(["links", "depends_on", "both"]),
    default="links",
    show_default=True,
    help="How to compute the concept -> concept hop (links mirrors Neo4j LINKS_TO)",
)
@click.option("--top", type=int, default=25, show_default=True, help="How many notes to include (by implied count)")
@click.option("--all", "include_all", is_flag=True, default=False, help="Audit all notes (ignores --top)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["md", "json"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=None, help="Write output to a file")
@click.pass_context
def junctions_implicit(
    ctx: click.Context,
    role_name: str,
    note_filter: str | None,
    via_mode: str,
    top: int,
    include_all: bool,
    output_format: str,
    out: Path | None,
) -> None:
    """Audit any note role for implied concept dependencies (2-hop) not declared by direct links."""
    from .commands.junctions import run_implicit_audit

    exit_code = run_implicit_audit(
        ctx.obj["vault"],
        role=role_name,
        note=note_filter,
        via=via_mode,
        top=top,
        include_all=include_all,
        out=out,
        fmt=output_format,
    )
    sys.exit(exit_code)


@cli.group()
def artifact() -> None:
    """Artifact ledger utilities (event-sourced)."""
    pass


@artifact.command("list")
@click.option("--type", "artifact_type", type=str, default=None, help="Filter by artifact type (plan, approval, report)")
@click.option("--status", type=str, default=None, help="Filter by status (created, validated, approved, executed, rejected)")
@click.pass_context
def artifact_list(ctx: click.Context, artifact_type: str | None, status: str | None) -> None:
    """List artifacts from the append-only artifact ledger."""
    from .commands.artifact_cmd import run_artifact_list

    sys.exit(run_artifact_list(ctx.obj["vault"], artifact_type=artifact_type, status=status))


@artifact.command("show")
@click.argument("artifact_id", type=str)
@click.option("--json", "output_json", is_flag=True, help="Include stored content in JSON output")
@click.pass_context
def artifact_show(ctx: click.Context, artifact_id: str, output_json: bool) -> None:
    """Show an artifact snapshot (and optionally its stored content)."""
    from .commands.artifact_cmd import run_artifact_show

    sys.exit(run_artifact_show(ctx.obj["vault"], artifact_id, output_json=output_json))


@artifact.command("status")
@click.argument("artifact_id", type=str)
@click.pass_context
def artifact_status(ctx: click.Context, artifact_id: str) -> None:
    """Show lifecycle status and next required gate."""
    from .commands.artifact_cmd import run_artifact_status

    sys.exit(run_artifact_status(ctx.obj["vault"], artifact_id))


@artifact.command("explain")
@click.argument("artifact_id", type=str)
@click.pass_context
def artifact_explain(ctx: click.Context, artifact_id: str) -> None:
    """Explain computed risk and approval requirements."""
    from .commands.artifact_cmd import run_artifact_explain

    sys.exit(run_artifact_explain(ctx.obj["vault"], artifact_id))


@artifact.command("approve")
@click.argument("artifact_id", type=str)
@click.option("--approver", type=str, default="human:local", show_default=True, help="Approver identity")
@click.option("--scope", type=str, default=None, help="Approval scope string")
@click.option("--force", is_flag=True, help="Acknowledge destructive approval (force_ack)")
@click.pass_context
def artifact_approve(ctx: click.Context, artifact_id: str, approver: str, scope: str | None, force: bool) -> None:
    """Approve a validated artifact by creating an approval artifact."""
    from .commands.artifact_cmd import run_artifact_approve

    sys.exit(run_artifact_approve(ctx.obj["vault"], artifact_id, approver=approver, force=force, scope=scope))


@artifact.command("audit")
@click.argument("artifact_id", type=str)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--limit", type=int, default=None, help="Limit number of events")
@click.pass_context
def artifact_audit(ctx: click.Context, artifact_id: str, output_json: bool, limit: int | None) -> None:
    """Show full chronological audit trail for an artifact."""
    from .commands.artifact_cmd import run_artifact_audit

    sys.exit(run_artifact_audit(ctx.obj["vault"], artifact_id, output_json=output_json, limit=limit))


@artifact.command("execution")
@click.argument("artifact_id", type=str, required=False)
@click.option("--execution-id", type=str, default=None, help="Filter by execution ID")
@click.option("--phase", type=str, default=None, help="Filter by phase (prepare|execute|commit)")
@click.option("--status", type=str, default=None, help="Filter by status (started|completed|failed|skipped)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_execution(ctx: click.Context, artifact_id: str | None, execution_id: str | None, phase: str | None, status: str | None, output_json: bool) -> None:
    """Show execution logs for an artifact or execution_id."""
    from .commands.artifact_cmd import run_artifact_execution

    sys.exit(run_artifact_execution(ctx.obj["vault"], artifact_id, execution_id=execution_id, phase=phase, status=status, output_json=output_json))


@artifact.command("constraints")
@click.argument("artifact_id", type=str)
@click.option("--ruleset", type=str, default=None, help="Filter by ruleset ID")
@click.option("--result", type=str, default=None, help="Filter by result (pass|fail|warning)")
@click.option("--status", type=str, default=None, help="Filter invariant checks by status (pass|fail)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_constraints(ctx: click.Context, artifact_id: str, ruleset: str | None, result: str | None, status: str | None, output_json: bool) -> None:
    """Show constraint evaluations and invariant checks for an artifact."""
    from .commands.artifact_cmd import run_artifact_constraints

    sys.exit(run_artifact_constraints(ctx.obj["vault"], artifact_id, ruleset=ruleset, result=result, status=status, output_json=output_json))


@artifact.command("timeline")
@click.argument("artifact_id", type=str)
@click.option("--full", is_flag=True, help="Show full timestamps (not condensed)")
@click.option("--limit", type=int, default=None, help="Limit number of events")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_timeline(ctx: click.Context, artifact_id: str, full: bool, limit: int | None, output_json: bool) -> None:
    """Show condensed chronological timeline for an artifact."""
    from .commands.artifact_cmd import run_artifact_timeline

    sys.exit(run_artifact_timeline(ctx.obj["vault"], artifact_id, full=full, limit=limit, output_json=output_json))


@artifact.command("summary")
@click.argument("artifact_id", type=str)
@click.option("--execution-id", type=str, default=None, help="Specific execution ID (defaults to latest)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_summary(ctx: click.Context, artifact_id: str, execution_id: str | None, output_json: bool) -> None:
    """Show combined execution + constraint summary for an artifact."""
    from .commands.artifact_cmd import run_artifact_summary

    sys.exit(run_artifact_summary(ctx.obj["vault"], artifact_id, execution_id=execution_id, output_json=output_json))


@artifact.command("types")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_types(ctx: click.Context, output_json: bool) -> None:
    """List all registered artifact types (vault + artifact system)."""
    from .commands.artifact_types_cmd import run_artifact_types_list

    sys.exit(run_artifact_types_list(ctx.obj["vault"], json_output=output_json))


@artifact.command("type-check")
@click.argument("path", type=str)
@click.option("--severity", type=click.Choice(["warn", "fail", "enforce", "all"]), default="all", help="Filter by severity level")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_type_check(ctx: click.Context, path: str, severity: str, output_json: bool) -> None:
    """Dry-run validation on file or directory against type registry."""
    from .commands.artifact_types_cmd import run_artifact_type_check

    sys.exit(run_artifact_type_check(ctx.obj["vault"], path, severity_filter=severity, json_output=output_json))


@artifact.command("type-info")
@click.argument("type_id", type=str)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_type_info(ctx: click.Context, type_id: str, output_json: bool) -> None:
    """Show detailed information for one artifact type."""
    from .commands.artifact_types_cmd import run_artifact_type_info

    sys.exit(run_artifact_type_info(ctx.obj["vault"], type_id, json_output=output_json))


@cli.group()
def neo4j() -> None:
    """Neo4j export/load utilities (derived graph state)."""
    pass


@neo4j.command("ping")
@click.option(
    "--http-uri",
    type=str,
    default="http://localhost:7474",
    show_default=True,
    help="Neo4j HTTP base URL (transactional endpoint uses /db/<db>/tx/commit)",
)
@click.option("--user", type=str, default="neo4j", show_default=True, help="Neo4j username")
@click.option(
    "--password",
    type=str,
    envvar="NEO4J_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Neo4j password (or set NEO4J_PASSWORD)",
)
@click.option("--database", type=str, default="irrev", show_default=True, help="Neo4j database name")
def neo4j_ping(http_uri: str, user: str, password: str, database: str) -> None:
    """Check Neo4j connectivity (non-destructive)."""
    from .commands.neo4j_cmd import run_neo4j_ping

    sys.exit(run_neo4j_ping(http_uri=http_uri, user=user, password=password, database=database))


@neo4j.command("load")
@click.option(
    "--http-uri",
    type=str,
    default="http://localhost:7474",
    show_default=True,
    help="Neo4j HTTP base URL (transactional endpoint uses /db/<db>/tx/commit)",
)
@click.option("--user", type=str, default="neo4j", show_default=True, help="Neo4j username")
@click.option(
    "--password",
    type=str,
    envvar="NEO4J_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Neo4j password (or set NEO4J_PASSWORD)",
)
@click.option("--database", type=str, default="irrev", show_default=True, help="Neo4j database name")
@click.option(
    "--mode",
    type=click.Choice(["sync", "rebuild"]),
    default="sync",
    show_default=True,
    help="sync clears derived edges; rebuild wipes the database first",
)
@click.option(
    "--ensure-schema/--no-ensure-schema",
    default=True,
    show_default=True,
    help="Create constraints/indexes (Neo4j 5+ syntax)",
)
@click.option("--batch-size", type=int, default=500, show_default=True, help="Statements batch size")
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation for destructive operations (required for --mode rebuild in non-interactive contexts)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without executing (diagnostic only)",
)
@click.option(
    "--propose-only",
    is_flag=True,
    help="Create + validate an artifact plan, but do not execute",
)
@click.option(
    "--plan-id",
    type=str,
    default=None,
    metavar="ARTIFACT_ID",
    help="Execute an approved artifact plan",
)
@click.pass_context
def neo4j_load(
    ctx: click.Context,
    http_uri: str,
    user: str,
    password: str,
    database: str,
    mode: str,
    ensure_schema: bool,
    batch_size: int,
    force: bool,
    dry_run: bool,
    propose_only: bool,
    plan_id: str | None,
) -> None:
    """Load the vault into Neo4j as a derived graph.

    Examples:

        irrev -v content neo4j load --database irrev

        $env:NEO4J_PASSWORD="adminroot"; irrev -v content neo4j load --database irrev --mode rebuild --force
    """
    from rich.console import Console
    from .commands.neo4j_cmd import run_neo4j_load, run_neo4j_load_from_plan_id, run_neo4j_load_propose

    console = Console(stderr=True)

    if propose_only and plan_id:
        raise click.BadParameter("--propose-only and --plan-id are mutually exclusive")
    if propose_only and dry_run:
        raise click.BadParameter("--propose-only and --dry-run are mutually exclusive")

    if plan_id:
        sys.exit(
            run_neo4j_load_from_plan_id(
                ctx.obj["vault"],
                plan_id=plan_id,
                http_uri=http_uri,
                database=database,
                mode=mode,
                ensure_schema=ensure_schema,
                batch_size=batch_size,
                user=user,
                password=password,
            )
        )

    if propose_only:
        sys.exit(
            run_neo4j_load_propose(
                ctx.obj["vault"],
                http_uri=http_uri,
                database=database,
                mode=mode,
                ensure_schema=ensure_schema,
                batch_size=batch_size,
                actor="agent:planner",
            )
        )

    # Governance: destructive operations require explicit acknowledgment
    if mode == "rebuild" and not dry_run:
        console.print("[yellow]⚠ Governance notice:[/] --mode rebuild will wipe the database before loading.", style="dim")
        console.print(f"  Target: {http_uri} database={database}", style="dim")
        if not force:
            if not click.confirm("Proceed with database wipe?"):
                console.print("Aborted.", style="dim")
                sys.exit(1)

    exit_code = run_neo4j_load(
        ctx.obj["vault"],
        http_uri=http_uri,
        user=user,
        password=password,
        database=database,
        mode=mode,
        ensure_schema=ensure_schema,
        batch_size=batch_size,
        dry_run=dry_run,
    )
    sys.exit(exit_code)


@neo4j.command("export")
@click.option(
    "--http-uri",
    type=str,
    default="http://localhost:7474",
    show_default=True,
    help="Neo4j HTTP base URL (transactional endpoint uses /db/<db>/tx/commit)",
)
@click.option("--user", type=str, default="neo4j", show_default=True, help="Neo4j username")
@click.option(
    "--password",
    type=str,
    envvar="NEO4J_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Neo4j password (or set NEO4J_PASSWORD)",
)
@click.option("--database", type=str, default="irrev", show_default=True, help="Neo4j database name")
@click.option(
    "--out-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("exports/export"),
    show_default=True,
    help="Output directory (relative to the vault root unless absolute)",
)
@click.option(
    "--stamp/--no-stamp",
    default=True,
    show_default=True,
    help="Write into a dated subfolder (YYYY-MM-DD) for repeatable snapshots",
)
@click.option("--top", type=int, default=50, show_default=True, help="Row count for top-N exports")
@click.option(
    "--concept",
    "concept_note_id",
    type=str,
    default="concepts/erasure-cost",
    show_default=True,
    help="Concept note_id used for touch/require exports",
)
@click.option(
    "--include-mentions/--no-include-mentions",
    default=True,
    show_default=True,
    help="Detect definition mentions and export semantic-implicit MENTIONS edges",
)
@click.option(
    "--include-ghost-terms/--no-include-ghost-terms",
    default=True,
    show_default=True,
    help="Detect unknown backticked terms in definitions and export ghost nodes",
)
@click.option(
    "--include-definition-tokens/--no-include-definition-tokens",
    default=False,
    show_default=True,
    help="Tokenize definitions into a filtered token graph (ghost vocabulary probe)",
)
@click.option("--token-min-df", type=int, default=2, show_default=True, help="Minimum concepts a token must appear in")
@click.option("--token-max-df", type=int, default=8, show_default=True, help="Maximum concepts a token may appear in (0=unbounded)")
@click.option("--token-top-per-concept", type=int, default=20, show_default=True, help="How many tokens to keep per concept")
@click.pass_context
def neo4j_export(
    ctx: click.Context,
    http_uri: str,
    user: str,
    password: str,
    database: str,
    out_dir: Path,
    stamp: bool,
    top: int,
    concept_note_id: str,
    include_mentions: bool,
    include_ghost_terms: bool,
    include_definition_tokens: bool,
    token_min_df: int,
    token_max_df: int,
    token_top_per_concept: int,
) -> None:
    """Export a bundle of inspection artifacts (CSV/JSON) from Neo4j.

    This is the “automatic way” to run the manual query pack and write files into
    `content/exports/export/…` for your own inspection.
    """
    from .commands.neo4j_cmd import run_neo4j_export

    exit_code = run_neo4j_export(
        ctx.obj["vault"],
        http_uri=http_uri,
        user=user,
        password=password,
        database=database,
        out_dir=out_dir,
        stamp=stamp,
        top=top,
        concept_note_id=concept_note_id,
        include_mentions=include_mentions,
        include_ghost_terms=include_ghost_terms,
        include_definition_tokens=include_definition_tokens,
        token_min_df=token_min_df,
        token_max_df=token_max_df,
        token_top_per_concept=token_top_per_concept,
    )
    sys.exit(exit_code)


# -----------------------------------------------------------------------------
# Change accounting commands
# -----------------------------------------------------------------------------


@cli.group()
def changes() -> None:
    """Change accounting - structural event tracking.

    Treats structural changes as typed events that can be audited.
    Per Failure Mode #10: account for what the lens itself displaces.
    """
    pass


@changes.command("summary")
@click.pass_context
def changes_summary(ctx: click.Context) -> None:
    """Show summary of structural changes over time."""
    from .ledger import ChangeAccountingLedger

    ledger = ChangeAccountingLedger(ctx.obj["vault"])
    print(ledger.format_summary())


@changes.command("record")
@click.argument("note_id", type=str)
@click.option("--before", type=click.Path(exists=True, path_type=Path), help="Path to before-state file")
@click.option("--after", type=click.Path(exists=True, path_type=Path), help="Path to after-state file")
@click.option("--commit", type=str, default=None, help="Git commit SHA for provenance")
@click.pass_context
def changes_record(
    ctx: click.Context,
    note_id: str,
    before: Path | None,
    after: Path | None,
    commit: str | None,
) -> None:
    """Record a structural change event.

    Compare before/after content and append a typed event to the ledger.
    """
    from .ledger import classify_change, ChangeAccountingLedger

    before_content = before.read_text(encoding="utf-8") if before else None
    after_content = after.read_text(encoding="utf-8") if after else None

    event = classify_change(note_id, before_content, after_content, git_commit=commit)

    ledger = ChangeAccountingLedger(ctx.obj["vault"])
    ledger.append(event)

    from rich.console import Console
    console = Console(stderr=True)
    console.print(f"Recorded: {note_id}", style="green")
    console.print(f"  Types: {[ct.value for ct in event.change_types]}")
    console.print(f"  Ambiguity delta: {event.ambiguity_delta:+d}")


@changes.command("show")
@click.option("--note", type=str, default=None, help="Filter by note ID")
@click.option("--type", "change_type", type=str, default=None, help="Filter by change type")
@click.option("--limit", type=int, default=20, help="Max events to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def changes_show(
    ctx: click.Context,
    note: str | None,
    change_type: str | None,
    limit: int,
    output_json: bool,
) -> None:
    """Show recent change events from the ledger."""
    import json as json_module
    from .ledger import ChangeAccountingLedger, ChangeType

    ledger = ChangeAccountingLedger(ctx.obj["vault"])

    events = ledger.read_all()

    # Apply filters
    if note:
        events = [e for e in events if note.lower() in e.note_id.lower()]
    if change_type:
        try:
            ct = ChangeType(change_type)
            events = [e for e in events if ct in e.change_types]
        except ValueError:
            from rich.console import Console
            Console(stderr=True).print(f"Unknown change type: {change_type}", style="red")
            sys.exit(1)

    # Take most recent
    events = events[-limit:]

    if output_json:
        print(json_module.dumps([e.to_dict() for e in events], indent=2))
    else:
        for e in events:
            print(f"{e.timestamp.isoformat()} {e.note_id}")
            print(f"  Types: {[ct.value for ct in e.change_types]}")
            if e.structural_effects.dependencies_added:
                print(f"  Deps added: {', '.join(e.structural_effects.dependencies_added)}")
            if e.structural_effects.dependencies_removed:
                print(f"  Deps removed: {', '.join(e.structural_effects.dependencies_removed)}")
            print(f"  Ambiguity: {e.ambiguity_delta:+d}")
            print()


# -----------------------------------------------------------------------------
# Watch commands - structural event logging
# -----------------------------------------------------------------------------


@cli.group()
def watch() -> None:
    """Observe vault drift as structural events.

    Watches for file system changes and logs them to .irrev/events.log.
    Per the Irreversibility invariant: "Persistence must be tracked."
    """
    pass


@watch.command("start")
@click.option(
    "--hash/--no-hash",
    "include_hash",
    default=False,
    show_default=True,
    help="Compute and log file content hashes",
)
@click.option(
    "--frontmatter/--no-frontmatter",
    "include_frontmatter",
    default=False,
    show_default=True,
    help="Extract and log frontmatter role/layer",
)
@click.option(
    "--scope",
    "scopes",
    multiple=True,
    default=None,
    help="Filter to specific scopes (vault_note, registry, rules, config). Repeatable.",
)
@click.pass_context
def watch_start(
    ctx: click.Context,
    include_hash: bool,
    include_frontmatter: bool,
    scopes: tuple[str, ...],
) -> None:
    """Start watching the vault for file changes.

    Runs until interrupted (Ctrl+C). Events are logged to .irrev/events.log.

    Examples:

        irrev watch start

        irrev watch start --hash --frontmatter

        irrev watch start --scope vault_note --scope registry
    """
    from .commands.watch_cmd import run_watch

    run_watch(
        ctx.obj["vault"],
        include_hash=include_hash,
        include_frontmatter=include_frontmatter,
        scopes=set(scopes) if scopes else None,
    )


@watch.command("events")
@click.option("--last", "last_n", type=int, default=None, help="Show only the last N events")
@click.option(
    "--kind",
    "event_kinds",
    multiple=True,
    default=None,
    help="Filter by event kind (file_created, file_modified, file_deleted, file_renamed). Repeatable.",
)
@click.option(
    "--scope",
    "scopes",
    multiple=True,
    default=None,
    help="Filter by artifact scope (vault_note, registry, rules, config). Repeatable.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.pass_context
def watch_events(
    ctx: click.Context,
    last_n: int | None,
    event_kinds: tuple[str, ...],
    scopes: tuple[str, ...],
    output_format: str,
) -> None:
    """Read and display events from the events log.

    Examples:

        irrev watch events --last 10

        irrev watch events --kind file_deleted --format json
    """
    from .commands.watch_cmd import run_events

    count = run_events(
        ctx.obj["vault"],
        last_n=last_n,
        event_kinds=list(event_kinds) if event_kinds else None,
        scopes=list(scopes) if scopes else None,
        format=output_format,
    )
    sys.exit(0 if count > 0 else 1)


@watch.command("summary")
@click.pass_context
def watch_summary(ctx: click.Context) -> None:
    """Display summary of logged events."""
    from .commands.watch_cmd import run_events_summary

    count = run_events_summary(ctx.obj["vault"])
    sys.exit(0 if count > 0 else 1)


# -----------------------------------------------------------------------------
# Self-audit command - meta-lint the linter
# -----------------------------------------------------------------------------


@cli.command("self-audit")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "md"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--include-passing",
    is_flag=True,
    help="Include passing checks in output",
)
@click.option(
    "--target",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory to scan (defaults to irrev package)",
)
def self_audit(
    output_format: str,
    include_passing: bool,
    target: Path | None,
) -> None:
    """Meta-lint the linter itself.

    Runs self-audit scanners against the irrev codebase to detect:

    \b
    - Prescriptive language in strings/docstrings
    - Self-exemption patterns (bypass mechanisms)
    - Force gate coverage (destructive ops without --force)
    - Audit logging coverage (state changes without logging)

    Per Failure Mode #10: "The most serious failure mode is assuming
    the lens already accounts for its own limitations."

    Examples:

        irrev self-audit

        irrev self-audit --format md

        irrev self-audit --format json > findings.json
    """
    from .commands.self_audit_cmd import run_self_audit

    exit_code = run_self_audit(
        target=target,
        output_format=output_format,
        include_passing=include_passing,
    )
    sys.exit(exit_code)


# -----------------------------------------------------------------------------
# LSP server command
# -----------------------------------------------------------------------------


@cli.command("lsp")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "tcp"]),
    default="stdio",
    show_default=True,
    help="Transport method (stdio for editors, tcp for debugging)",
)
@click.pass_context
def lsp(ctx: click.Context, transport: str) -> None:
    """Start the LSP server for live invariant awareness.

    The LSP server provides:

    \b
    - Real-time lint diagnostics (on save)
    - Hover info for wikilinks (concept layer, dependencies)
    - Code actions as suggestions (not auto-apply)

    For VSCode, configure the extension to use:

        irrev lsp --transport stdio

    For debugging with a TCP connection:

        irrev lsp --transport tcp

    Examples:

        irrev -v ../content lsp

        irrev -v ../content lsp --transport tcp
    """
    from .lsp import start_server

    vault_path = ctx.obj.get("vault")
    start_server(vault_path=vault_path, transport=transport)


# -----------------------------------------------------------------------------
# Harness commands (unified execution chokepoint)
# -----------------------------------------------------------------------------


@cli.group()
def harness() -> None:
    """Execution harness - single chokepoint for all effectful operations.

    The harness enforces governance invariants architecturally:

    \b
    - propose: Compute plan, derive risk, create artifact (pure)
    - execute: Verify approval, execute handler, emit bundle (impure)
    - run: Convenience wrapper (propose + execute if no approval required)

    Key principle: operations cannot bypass gates without leaving audit scars.
    """
    pass


@harness.command("propose")
@click.argument("operation", type=str)
@click.option("--params", type=str, default="{}", help="JSON params for operation")
@click.option("--actor", type=str, default="agent:cli", help="Actor identity")
@click.pass_context
def harness_propose(ctx: click.Context, operation: str, params: str, actor: str) -> None:
    """Compute plan and create artifact (pure, no execution).

    Examples:

        irrev harness propose neo4j.load --params '{"http_uri":"http://localhost:7474","database":"irrev","mode":"sync"}'

        irrev harness propose neo4j.load --params '{"http_uri":"http://localhost:7474","database":"irrev","mode":"rebuild"}'

    Returns the plan_id, risk_class, and whether approval is required.
    """
    import json

    from rich.console import Console

    from .harness import Harness
    from .harness.registry import get_handler
    from .harness.handlers import register_all

    console = Console(stderr=True)

    # Register all handlers
    register_all()

    # Get handler
    handler = get_handler(operation)
    if handler is None:
        console.print(f"Unknown operation: {operation}", style="bold red")
        console.print("Available operations: neo4j.load", style="dim")
        sys.exit(1)

    # Parse params
    try:
        params_dict = json.loads(params)
    except json.JSONDecodeError as e:
        console.print(f"Invalid JSON params: {e}", style="bold red")
        sys.exit(1)

    # Run propose
    harness_instance = Harness(ctx.obj["vault"], console=console)
    result = harness_instance.propose(handler, params_dict, actor=actor, surface="cli")

    if not result.success:
        console.print(f"Validation failed: {'; '.join(result.validation_errors)}", style="bold red")
        sys.exit(1)

    sys.exit(0)


@harness.command("execute")
@click.argument("plan_id", type=str)
@click.option("--secrets-ref", type=str, default=None, help="Secrets reference (e.g., 'env:NEO4J_PASSWORD')")
@click.option("--dry-run", is_flag=True, help="Show plan but don't execute")
@click.pass_context
def harness_execute(ctx: click.Context, plan_id: str, secrets_ref: str | None, dry_run: bool) -> None:
    """Execute an approved plan artifact.

    Requires the plan to be approved first:

        irrev artifact approve <plan_id> --approver human:alice --force

    Examples:

        irrev harness execute 01HYK... --secrets-ref env:NEO4J_PASSWORD

        irrev harness execute 01HYK... --dry-run
    """
    from rich.console import Console

    from .harness import Harness
    from .harness.registry import get_handler
    from .harness.handlers import register_all

    console = Console(stderr=True)

    # Register all handlers
    register_all()

    # Create harness
    harness_instance = Harness(ctx.obj["vault"], console=console)

    # Get plan snapshot to determine handler
    snap = harness_instance.plan_manager.ledger.snapshot(plan_id)
    if snap is None:
        console.print(f"Plan not found: {plan_id}", style="bold red")
        sys.exit(1)

    # Get operation from plan
    content = harness_instance.content_store.get(snap.content_id)
    if not isinstance(content, dict):
        console.print(f"Invalid plan content: {snap.content_id}", style="bold red")
        sys.exit(1)

    operation = str(content.get("operation", "")).strip()
    handler = get_handler(operation)
    if handler is None:
        console.print(f"Unknown operation: {operation}", style="bold red")
        sys.exit(1)

    # Execute
    result = harness_instance.execute(
        plan_id,
        handler,
        executor=handler.metadata.delegate_to,
        secrets_ref=secrets_ref,
        dry_run=dry_run,
    )

    if not result.success:
        console.print(f"Execution failed: {result.error}", style="bold red")
        sys.exit(1)

    sys.exit(0)


@harness.command("run")
@click.argument("operation", type=str)
@click.option("--params", type=str, default="{}", help="JSON params for operation")
@click.option("--actor", type=str, default="agent:cli", help="Actor identity")
@click.option("--secrets-ref", type=str, default=None, help="Secrets reference (e.g., 'env:NEO4J_PASSWORD')")
@click.option("--dry-run", is_flag=True, help="Show plan but don't execute")
@click.pass_context
def harness_run(
    ctx: click.Context,
    operation: str,
    params: str,
    actor: str,
    secrets_ref: str | None,
    dry_run: bool,
) -> None:
    """Propose + execute in one call (only if no approval required).

    For operations that require approval (destructive/external), this
    will fail with an error - use propose + approve + execute instead.

    Examples:

        irrev harness run neo4j.load --params '{"http_uri":"...","database":"irrev","mode":"sync"}' --dry-run

        # This will fail for mode=rebuild (requires approval):
        irrev harness run neo4j.load --params '{"mode":"rebuild",...}'
        # Error: Approval required (risk=mutation_destructive)
    """
    import json

    from rich.console import Console

    from .harness import Harness
    from .harness.registry import get_handler
    from .harness.handlers import register_all

    console = Console(stderr=True)

    # Register all handlers
    register_all()

    # Get handler
    handler = get_handler(operation)
    if handler is None:
        console.print(f"Unknown operation: {operation}", style="bold red")
        console.print("Available operations: neo4j.load", style="dim")
        sys.exit(1)

    # Parse params
    try:
        params_dict = json.loads(params)
    except json.JSONDecodeError as e:
        console.print(f"Invalid JSON params: {e}", style="bold red")
        sys.exit(1)

    # Run
    harness_instance = Harness(ctx.obj["vault"], console=console)
    result = harness_instance.run(
        handler,
        params_dict,
        actor=actor,
        surface="cli",
        executor=handler.metadata.delegate_to,
        secrets_ref=secrets_ref,
        dry_run=dry_run,
    )

    if not result.success:
        console.print(f"Failed: {result.error}", style="bold red")
        sys.exit(1)

    sys.exit(0)


def main() -> None:
    """Main entrypoint."""
    cli()


if __name__ == "__main__":
    main()
