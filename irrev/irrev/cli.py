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
@click.pass_context
def registry_build(
    ctx: click.Context,
    out: Path | None,
    in_place: bool,
    overrides: Path | None,
    allow_unknown_layers: bool,
    registry_path: Path | None,
) -> None:
    """Generate registry from vault concepts.

    Reads concept layers and dependencies, produces markdown tables
    matching the Registry format.

    Examples:

        irrev registry build

        irrev registry build --out Registry.generated.md
    """
    from .commands.registry import run_build

    default_overrides = (ctx.obj["vault"] / "meta" / "registry.overrides.yml").resolve()
    overrides_path = overrides or (default_overrides if default_overrides.exists() else None)

    exit_code = run_build(
        ctx.obj["vault"],
        str(out) if out else None,
        in_place=in_place,
        overrides=overrides_path,
        allow_unknown_layers=allow_unknown_layers,
        registry_path=registry_path,
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
    from .commands.hubs import run_hubs

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
) -> None:
    """Load the vault into Neo4j as a derived graph.

    Examples:

        irrev -v content neo4j load --database irrev

        $env:NEO4J_PASSWORD="adminroot"; irrev -v content neo4j load --database irrev --mode rebuild
    """
    from .commands.neo4j_cmd import run_neo4j_load

    exit_code = run_neo4j_load(
        ctx.obj["vault"],
        http_uri=http_uri,
        user=user,
        password=password,
        database=database,
        mode=mode,
        ensure_schema=ensure_schema,
        batch_size=batch_size,
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
    )
    sys.exit(exit_code)


def main() -> None:
    """Main entrypoint."""
    cli()


if __name__ == "__main__":
    main()
