"""Neo4j export/load commands (derived, rebuildable graph state)."""

from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from rich.console import Console

from ..neo4j.http import Neo4jHttpClient, Neo4jHttpConfig
from ..vault.loader import Vault, load_vault
from ..vault.parser import extract_frontmatter_depends_on, extract_section
from .graph_cmd import LinkGraph, _greedy_modularity_communities  # type: ignore


_WIKILINK_OCCURRENCE_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def _note_id(vault_path: Path, note_path: Path) -> str:
    rel = note_path.relative_to(vault_path)
    return rel.with_suffix("").as_posix()


def _first_h1_title(name: str, content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip() or name
    return name


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def _collect_wikilink_counts(content: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for target in _WIKILINK_OCCURRENCE_PATTERN.findall(content):
        norm = target.lower().strip()
        if not norm:
            continue
        counts[norm] = counts.get(norm, 0) + 1
    return counts


def _role_to_label(role: str | None) -> str | None:
    if not role:
        return None
    role = role.lower().strip()
    return {
        "concept": "Concept",
        "diagnostic": "Diagnostic",
        "domain": "Domain",
        "projection": "Projection",
        "paper": "Paper",
        "invariant": "Invariant",
        "meta": "Meta",
        "report": "Report",
        "support": "Support",
    }.get(role)


def _schema_statements() -> list[dict[str, Any]]:
    # Neo4j 5+ syntax (IF NOT EXISTS). If your server is older, you can disable
    # schema creation and create constraints manually.
    return [
        {
            "statement": "CREATE CONSTRAINT note_id_unique IF NOT EXISTS FOR (n:Note) REQUIRE n.note_id IS UNIQUE",
        },
        {
            "statement": "CREATE INDEX note_role IF NOT EXISTS FOR (n:Note) ON (n.role)",
        },
        {
            "statement": "CREATE INDEX note_layer IF NOT EXISTS FOR (n:Note) ON (n.layer)",
        },
        {
            "statement": "CREATE INDEX note_canonical IF NOT EXISTS FOR (n:Note) ON (n.canonical)",
        },
        {
            "statement": "CREATE INDEX note_community_links IF NOT EXISTS FOR (n:Note) ON (n.community_links_greedy)",
        },
        {
            "statement": "CREATE INDEX note_community_depends IF NOT EXISTS FOR (n:Note) ON (n.community_depends_greedy)",
        },
    ]


def _schema_statements_legacy() -> list[dict[str, Any]]:
    # Neo4j 3.5/4.x legacy syntax (no IF NOT EXISTS).
    # Some statements may fail if the constraint/index already exists.
    return [
        {"statement": "CREATE CONSTRAINT ON (n:Note) ASSERT n.note_id IS UNIQUE"},
        {"statement": "CREATE INDEX ON :Note(role)"},
        {"statement": "CREATE INDEX ON :Note(layer)"},
        {"statement": "CREATE INDEX ON :Note(canonical)"},
        {"statement": "CREATE INDEX ON :Note(community_links_greedy)"},
        {"statement": "CREATE INDEX ON :Note(community_depends_greedy)"},
    ]


def _wipe_statements() -> list[dict[str, Any]]:
    return [{"statement": "MATCH (n) DETACH DELETE n"}]


def _clear_edge_statements() -> list[dict[str, Any]]:
    return [{"statement": "MATCH ()-[r:LINKS_TO|DEPENDS_ON]->() DELETE r"}]


def _upsert_notes_statement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # Dynamic labels without APOC: FOREACH + CASE.
    return {
        "statement": """
UNWIND $rows AS row
MERGE (n:Note {note_id: row.note_id})
SET
  n.path = row.path,
  n.title = row.title,
  n.folder = row.folder,
  n.role = row.role,
  n.type = row.type,
  n.layer = row.layer,
  n.canonical = row.canonical,
  n.tags = row.tags,
  n.aliases = row.aliases,
  n.facets = row.facets,
  n.failure_modes = row.failure_modes,
  n.mtime = row.mtime
FOREACH (_ IN CASE WHEN row.label = 'Concept' THEN [1] ELSE [] END | SET n:Concept)
FOREACH (_ IN CASE WHEN row.label = 'Diagnostic' THEN [1] ELSE [] END | SET n:Diagnostic)
FOREACH (_ IN CASE WHEN row.label = 'Domain' THEN [1] ELSE [] END | SET n:Domain)
FOREACH (_ IN CASE WHEN row.label = 'Projection' THEN [1] ELSE [] END | SET n:Projection)
FOREACH (_ IN CASE WHEN row.label = 'Paper' THEN [1] ELSE [] END | SET n:Paper)
FOREACH (_ IN CASE WHEN row.label = 'Invariant' THEN [1] ELSE [] END | SET n:Invariant)
FOREACH (_ IN CASE WHEN row.label = 'Meta' THEN [1] ELSE [] END | SET n:Meta)
FOREACH (_ IN CASE WHEN row.label = 'Report' THEN [1] ELSE [] END | SET n:Report)
FOREACH (_ IN CASE WHEN row.label = 'Support' THEN [1] ELSE [] END | SET n:Support)
""",
        "parameters": {"rows": rows},
    }


def _upsert_links_statement(edges: list[dict[str, Any]], *, rel_type: str) -> dict[str, Any]:
    if rel_type not in ("LINKS_TO", "DEPENDS_ON"):
        raise ValueError(f"Unsupported relationship type: {rel_type}")

    if rel_type == "LINKS_TO":
        statement = """
 UNWIND $edges AS e
 MATCH (s:Note {note_id: e.src})
 MATCH (t:Note {note_id: e.dst})
 MERGE (s)-[r:LINKS_TO]->(t)
 SET r.count = e.count, r.kinds = e.kinds
 """
    else:
        statement = """
 UNWIND $edges AS e
 MATCH (s:Note {note_id: e.src})
 MATCH (t:Note {note_id: e.dst})
 MERGE (s)-[r:DEPENDS_ON]->(t)
 SET
   r.from_frontmatter = coalesce(r.from_frontmatter, false) OR coalesce(e.from_frontmatter, false),
   r.from_structural = coalesce(r.from_structural, false) OR coalesce(e.from_structural, false)
 """

    return {"statement": statement, "parameters": {"edges": edges}}


def _upsert_concept_topology_statement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "statement": """
UNWIND $rows AS row
MATCH (n:Note {note_id: row.note_id})
SET
  n.community_links_greedy = row.community_links_greedy,
  n.community_depends_greedy = row.community_depends_greedy,
  n.community_both_greedy = row.community_both_greedy,
  n.bridge_links_greedy = row.bridge_links_greedy,
  n.bridge_depends_greedy = row.bridge_depends_greedy,
  n.bridge_both_greedy = row.bridge_both_greedy,
  n.boundary_edges_links_greedy = row.boundary_edges_links_greedy,
  n.boundary_edges_depends_greedy = row.boundary_edges_depends_greedy,
  n.boundary_edges_both_greedy = row.boundary_edges_both_greedy
""",
        "parameters": {"rows": rows},
    }


def _build_rows(vault: Vault, vault_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for note in vault.all_notes:
        rel_id = _note_id(vault_path, note.path)
        fm = note.frontmatter or {}
        role = (fm.get("role") or note.role or "").lower() or None

        tags = _normalize_string_list(fm.get("tags"))
        aliases = _normalize_string_list(fm.get("aliases"))
        facets = _normalize_string_list(fm.get("facets"))
        failure_modes = _normalize_string_list(fm.get("failure_modes"))

        rows.append(
            {
                "note_id": rel_id,
                "path": note.path.relative_to(vault_path).as_posix(),
                "title": _first_h1_title(note.name, note.content),
                "folder": note.path.relative_to(vault_path).parent.as_posix(),
                "role": role,
                "type": fm.get("type"),
                "layer": fm.get("layer"),
                "canonical": bool(fm.get("canonical", False)),
                "tags": tags,
                "aliases": aliases,
                "facets": facets,
                "failure_modes": failure_modes,
                "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(note.path.stat().st_mtime)),
                "label": _role_to_label(role),
            }
        )
    return rows


def _build_edges(
    vault: Vault, vault_path: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    links_to: list[dict[str, Any]] = []
    depends_on: dict[tuple[str, str], dict[str, Any]] = {}
    unresolved = 0

    concept_ids = {_note_id(vault_path, c.path) for c in vault.concepts}

    for note in vault.all_notes:
        src_id = _note_id(vault_path, note.path)

        # Wiki-links (count occurrences)
        counts = _collect_wikilink_counts(note.content)
        for target, count in counts.items():
            dst_note = vault.get(target)
            if not dst_note:
                unresolved += 1
                continue
            dst_id = _note_id(vault_path, dst_note.path)
            links_to.append({"src": src_id, "dst": dst_id, "count": count, "kinds": ["wikilink"]})

        # Structural depends_on (concepts only; promoted into DEPENDS_ON)
        if src_id in concept_ids and hasattr(note, "depends_on"):
            for dep in getattr(note, "depends_on") or []:
                dst_note = vault.get(dep)
                if not dst_note:
                    unresolved += 1
                    continue
                dst_id = _note_id(vault_path, dst_note.path)
                if dst_id in concept_ids:
                    key = (src_id, dst_id)
                    row = depends_on.get(key) or {
                        "src": src_id,
                        "dst": dst_id,
                        "from_frontmatter": False,
                        "from_structural": False,
                    }
                    row["from_structural"] = True
                    depends_on[key] = row

        # Frontmatter depends_on (all roles; promoted into DEPENDS_ON)
        for dep in extract_frontmatter_depends_on(note.frontmatter or {}):
            dst_note = vault.get(dep)
            if not dst_note:
                unresolved += 1
                continue
            dst_id = _note_id(vault_path, dst_note.path)
            key = (src_id, dst_id)
            row = depends_on.get(key) or {
                "src": src_id,
                "dst": dst_id,
                "from_frontmatter": False,
                "from_structural": False,
            }
            row["from_frontmatter"] = True
            depends_on[key] = row

    return links_to, list(depends_on.values()), unresolved


def _concept_topology_rows(
    concept_ids: set[str],
    *,
    links_to: list[dict[str, Any]],
    depends_on: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute community and bridge properties for concept nodes (derived; rebuildable)."""
    g_links = LinkGraph()
    g_depends = LinkGraph()
    g_both = LinkGraph()

    for cid in concept_ids:
        g_links.add_node(cid)
        g_depends.add_node(cid)
        g_both.add_node(cid)

    for e in links_to:
        s = e["src"]
        t = e["dst"]
        if s in concept_ids and t in concept_ids:
            g_links.add_edge(s, t)
            g_both.add_edge(s, t)

    for e in depends_on:
        s = e["src"]
        t = e["dst"]
        if s in concept_ids and t in concept_ids:
            g_depends.add_edge(s, t)
            g_both.add_edge(s, t)

    c_links = _greedy_modularity_communities(g_links)
    c_depends = _greedy_modularity_communities(g_depends)
    c_both = _greedy_modularity_communities(g_both)

    def bridge_metrics(g: LinkGraph, comm: dict[str, str], node: str) -> tuple[int, int]:
        nbrs = g.neighbors_undirected(node)
        self_c = comm.get(node)
        if not self_c or not nbrs:
            return 0, 0
        boundary_edges = 0
        neighbor_communities: set[str] = set()
        for nb in nbrs:
            c = comm.get(nb)
            if not c:
                continue
            if c != self_c:
                boundary_edges += 1
                neighbor_communities.add(c)
        return len(neighbor_communities), boundary_edges

    out: list[dict[str, Any]] = []
    for cid in sorted(concept_ids):
        bridge_l, boundary_l = bridge_metrics(g_links, c_links, cid)
        bridge_d, boundary_d = bridge_metrics(g_depends, c_depends, cid)
        bridge_b, boundary_b = bridge_metrics(g_both, c_both, cid)
        out.append(
            {
                "note_id": cid,
                "community_links_greedy": c_links.get(cid),
                "community_depends_greedy": c_depends.get(cid),
                "community_both_greedy": c_both.get(cid),
                "bridge_links_greedy": bridge_l,
                "bridge_depends_greedy": bridge_d,
                "bridge_both_greedy": bridge_b,
                "boundary_edges_links_greedy": boundary_l,
                "boundary_edges_depends_greedy": boundary_d,
                "boundary_edges_both_greedy": boundary_b,
            }
        )
    return out


# -----------------------------------------------------------------------------
# Decomposition-compliant pattern: compute (diagnostic) / execute (action)
# -----------------------------------------------------------------------------


def compute_neo4j_load_plan(
    vault_path: Path,
    *,
    http_uri: str,
    database: str,
    mode: str,
) -> "Neo4jLoadPlan":
    """
    Compute what would be loaded without executing writes.

    This is the diagnostic phase - pure computation, no side effects.
    """
    from irrev.planning import Neo4jLoadPlan

    vault = load_vault(vault_path)
    rows = _build_rows(vault, vault_path)
    links_to, depends_on, unresolved = _build_edges(vault, vault_path)
    concept_ids = {_note_id(vault_path, c.path) for c in vault.concepts}
    topology_rows = _concept_topology_rows(
        concept_ids,
        links_to=links_to,
        depends_on=depends_on,
    )

    return Neo4jLoadPlan(
        vault_path=vault_path,
        mode=mode,
        database=database,
        http_uri=http_uri,
        notes=rows,
        links_to=[(e["src"], e["dst"]) for e in links_to],
        depends_on=[(e["src"], e["dst"]) for e in depends_on],
        topology_rows=topology_rows,
        unresolved_links=unresolved,
    )


def execute_neo4j_load_plan(
    plan: "Neo4jLoadPlan",
    *,
    user: str,
    password: str,
    ensure_schema: bool,
    batch_size: int,
    console: Console,
) -> "Neo4jLoadResult":
    """
    Execute a neo4j load plan.

    This is the action phase - executes writes and returns result.
    """
    from irrev.planning import Neo4jLoadResult
    from irrev.audit_log import ErasureCost, CreationSummary

    client = Neo4jHttpClient(
        Neo4jHttpConfig(
            http_uri=plan.http_uri,
            user=user,
            password=password,
            database=plan.database,
            allow_default_db_fallback=False,
        )
    )

    erased = ErasureCost()
    created = CreationSummary()

    try:
        if plan.mode == "rebuild":
            # Query current counts before wipe for audit
            try:
                count_query = "MATCH (n) RETURN count(n) as nodes UNION ALL MATCH ()-[r]->() RETURN count(r) as nodes"
                _, count_rows = client.query_rows(count_query)
                if len(count_rows) >= 2:
                    erased.notes = count_rows[0][0] if count_rows[0] else 0
                    erased.edges = count_rows[1][0] if count_rows[1] else 0
            except Exception:
                pass  # Best effort

            console.print("Neo4j: wiping database (rebuild mode)...", style="yellow")
            client.commit(_wipe_statements())
        else:
            console.print("Neo4j: clearing derived relationships (sync mode)...", style="yellow")
            client.commit(_clear_edge_statements())

        if client.resolved_commit_url:
            console.print(f"Neo4j: using endpoint {client.resolved_commit_url}", style="yellow")
            if client.resolved_commit_url.endswith("/db/data/transaction/commit"):
                console.print("Neo4j: legacy single-db HTTP endpoint detected; --database is ignored.", style="yellow")

        if ensure_schema:
            console.print("Neo4j: ensuring schema (constraints/indexes)...", style="yellow")
            try:
                client.commit(_schema_statements())
            except Exception as e:
                console.print(f"Neo4j: schema creation failed ({e}); trying legacy syntax...", style="yellow")
                try:
                    client.commit(_schema_statements_legacy())
                except Exception as e2:
                    console.print(f"Neo4j: schema creation skipped ({e2})", style="yellow")

        console.print(f"Neo4j: upserting {len(plan.notes)} notes...", style="yellow")
        for i in range(0, len(plan.notes), batch_size):
            batch = plan.notes[i : i + batch_size]
            client.commit([_upsert_notes_statement(batch)])

        # Convert tuples back to dicts for the statement builders
        links_to_dicts = [{"src": s, "dst": d} for s, d in plan.links_to]
        depends_on_dicts = [{"src": s, "dst": d} for s, d in plan.depends_on]

        console.print(f"Neo4j: writing {len(links_to_dicts)} LINKS_TO edges...", style="yellow")
        for i in range(0, len(links_to_dicts), batch_size):
            batch = links_to_dicts[i : i + batch_size]
            client.commit([_upsert_links_statement(batch, rel_type="LINKS_TO")])

        console.print(f"Neo4j: writing {len(depends_on_dicts)} DEPENDS_ON edges...", style="yellow")
        for i in range(0, len(depends_on_dicts), batch_size):
            batch = depends_on_dicts[i : i + batch_size]
            client.commit([_upsert_links_statement(batch, rel_type="DEPENDS_ON")])

        console.print("Neo4j: writing derived concept topology properties (communities/bridges)...", style="yellow")
        client.commit([_upsert_concept_topology_statement(plan.topology_rows)])

        created.notes = len(plan.notes)
        created.edges = len(plan.links_to) + len(plan.depends_on)

        return Neo4jLoadResult(
            erased=erased,
            created=created,
            success=True,
            notes_loaded=len(plan.notes),
            edges_created=created.edges,
        )

    except Exception as e:
        return Neo4jLoadResult(
            erased=erased,
            created=created,
            success=False,
            error=str(e),
        )


def run_neo4j_load(
    vault_path: Path,
    *,
    http_uri: str,
    user: str,
    password: str,
    database: str,
    mode: str,
    ensure_schema: bool,
    batch_size: int,
    dry_run: bool = False,
) -> int:
    """
    Load the vault into Neo4j.

    This function orchestrates the compute/execute phases and handles
    dry-run mode for previewing operations.
    """
    console = Console(stderr=True)

    # Phase 1: Compute (diagnostic) - pure, no side effects
    console.print("Computing load plan...", style="dim")
    plan = compute_neo4j_load_plan(
        vault_path,
        http_uri=http_uri,
        database=database,
        mode=mode,
    )

    # Query existing counts if in rebuild mode (for plan summary)
    if mode == "rebuild" and not dry_run:
        try:
            client = Neo4jHttpClient(
                Neo4jHttpConfig(
                    http_uri=http_uri,
                    user=user,
                    password=password,
                    database=database,
                    allow_default_db_fallback=False,
                )
            )
            count_query = "MATCH (n) RETURN count(n) as nodes UNION ALL MATCH ()-[r]->() RETURN count(r) as nodes"
            _, count_rows = client.query_rows(count_query)
            if len(count_rows) >= 2:
                plan.existing_node_count = count_rows[0][0] if count_rows[0] else 0
                plan.existing_edge_count = count_rows[1][0] if count_rows[1] else 0
        except Exception:
            pass

    # Dry-run mode: show plan and exit
    if dry_run:
        console.print("\n[bold]DRY RUN[/bold] - No changes will be made\n")
        console.print(plan.summary())
        return 0

    # Phase 2: Execute (action) - performs writes
    result = execute_neo4j_load_plan(
        plan,
        user=user,
        password=password,
        ensure_schema=ensure_schema,
        batch_size=batch_size,
        console=console,
    )

    if not result.success:
        console.print(str(result.error), style="red")
        return 1

    if plan.unresolved_links:
        console.print(f"Note: {plan.unresolved_links} unresolved link targets skipped.", style="yellow")

    # Audit log
    from irrev.audit_log import log_operation

    log_operation(
        vault_path,
        operation=f"neo4j-{mode}",
        erased=result.erased,
        created=result.created,
        metadata={
            "database": database,
            "http_uri": http_uri,
            "unresolved_links": plan.unresolved_links,
        },
    )

    console.print("Neo4j load complete.", style="green")
    return 0


def run_neo4j_load_propose(
    vault_path: Path,
    *,
    http_uri: str,
    database: str,
    mode: str,
    ensure_schema: bool,
    batch_size: int,
    actor: str = "agent:planner",
) -> int:
    """Create + validate a Neo4j load plan artifact without executing."""
    from ..artifact.plan_manager import PlanManager

    console = Console(stderr=True)
    mgr = PlanManager(vault_path)

    payload = {
        "http_uri": http_uri,
        "database": database,
        "mode": mode,
        "ensure_schema": bool(ensure_schema),
        "batch_size": int(batch_size),
    }

    artifact_id = mgr.propose(
        "neo4j.load",
        payload,
        actor,
        delegate_to="handler:neo4j",
        surface="cli",
        artifact_type="plan",
    )
    ok = mgr.validate(artifact_id, validator="system")
    snap = mgr.ledger.snapshot(artifact_id)

    console.print(f"plan_id: {artifact_id}", style="bold cyan")
    if snap is not None:
        risk = snap.computed_risk_class or snap.risk_class
        console.print(f"status: {snap.status}", style="dim")
        console.print(f"risk_class: {(risk.value if risk else '')}", style="dim")
        if snap.requires_approval():
            console.print("approval required: yes", style="yellow")
            if (risk and risk.value == "mutation_destructive"):
                console.print("force_ack required: yes", style="yellow")
        else:
            console.print("approval required: no", style="dim")

    if not ok:
        console.print("validation failed", style="bold red")
        return 1
    return 0


def run_neo4j_load_from_plan_id(
    vault_path: Path,
    *,
    plan_id: str,
    http_uri: str,
    database: str,
    mode: str,
    ensure_schema: bool,
    batch_size: int,
    user: str,
    password: str,
) -> int:
    """Execute an approved Neo4j load plan artifact."""
    from ..artifact.plan_manager import PlanManager
    from ..audit_log import log_operation

    console = Console(stderr=True)
    mgr = PlanManager(vault_path)

    snap = mgr.ledger.snapshot(plan_id)
    if snap is None:
        console.print(f"Plan not found: {plan_id}", style="bold red")
        return 1
    if snap.artifact_type != "plan":
        console.print(f"Artifact is not a plan (type={snap.artifact_type}): {plan_id}", style="bold red")
        return 1

    content = mgr.content_store.get_json(snap.content_id) if snap.content_id else None
    if not isinstance(content, dict):
        console.print(f"Missing or invalid plan content: {snap.content_id}", style="bold red")
        return 1

    op = str(content.get("operation", "")).strip().lower()
    if op not in {"neo4j.load", "neo4j-load"}:
        console.print(f"Unsupported plan operation: {op}", style="bold red")
        return 1

    payload = content.get("payload")
    if not isinstance(payload, dict):
        console.print("Plan payload must be an object", style="bold red")
        return 1

    # Warn if CLI flags disagree with the approved plan (plan wins).
    plan_http_uri = str(payload.get("http_uri", "")).strip() or http_uri
    plan_database = str(payload.get("database", "")).strip() or database
    plan_mode = str(payload.get("mode", "")).strip() or mode
    plan_ensure_schema = bool(payload.get("ensure_schema", ensure_schema))
    plan_batch_size = int(payload.get("batch_size", batch_size))

    if http_uri != plan_http_uri or database != plan_database or mode != plan_mode:
        console.print("Note: CLI flags differ from plan payload; executing the approved plan payload.", style="dim")

    def _handler(plan_content: dict[str, Any]) -> dict[str, Any]:
        plan_payload = plan_content.get("payload", {})
        plan_payload = plan_payload if isinstance(plan_payload, dict) else {}

        load_plan = compute_neo4j_load_plan(
            vault_path,
            http_uri=plan_http_uri,
            database=plan_database,
            mode=plan_mode,
        )

        result = execute_neo4j_load_plan(
            load_plan,
            user=user,
            password=password,
            ensure_schema=plan_ensure_schema,
            batch_size=plan_batch_size,
            console=console,
        )

        if not result.success:
            raise RuntimeError(result.error or "Neo4j load failed")

        log_operation(
            vault_path,
            operation=f"neo4j-{plan_mode}",
            erased=result.erased,
            created=result.created,
            metadata={
                "database": plan_database,
                "http_uri": plan_http_uri,
                "batch_size": plan_batch_size,
            },
        )

        return {
            "success": True,
            "operation": "neo4j.load",
            "mode": plan_mode,
            "database": plan_database,
            "http_uri": plan_http_uri,
            "notes_loaded": getattr(result, "notes_loaded", 0),
            "edges_created": getattr(result, "edges_created", 0),
            "erasure_cost": asdict(result.erased),
            "creation_summary": asdict(result.created),
        }

    try:
        result_artifact_id = mgr.execute(plan_id, "handler:neo4j", handler=_handler)
    except Exception as e:
        console.print(str(e), style="bold red")
        return 1

    console.print(f"executed: {plan_id}", style="green")
    console.print(f"result_artifact_id: {result_artifact_id}", style="dim")
    return 0


def run_neo4j_ping(
    *,
    http_uri: str,
    user: str,
    password: str,
    database: str,
) -> int:
    """Non-destructive connectivity check.

    This will attempt the requested database first, then fall back to common endpoints
    to help diagnose configuration issues.
    """
    console = Console(stderr=True)

    client = Neo4jHttpClient(
        Neo4jHttpConfig(
            http_uri=http_uri,
            user=user,
            password=password,
            database=database,
            allow_default_db_fallback=True,
        )
    )

    try:
        client.commit([{"statement": "RETURN 1"}])
    except Exception as e:
        console.print(str(e), style="red")
        return 1

    url = client.resolved_commit_url or "<unknown>"
    console.print(f"Neo4j: reachable via {url}", style="green")

    requested = f"/db/{database}/tx/commit"
    if requested not in url:
        console.print(
            f"Neo4j: requested database '{database}' was not used (endpoint differs).",
            style="yellow",
        )
        if "/db/neo4j/tx/commit" in url:
            console.print("Neo4j: default database 'neo4j' is reachable; ensure 'irrev' is created and online.", style="yellow")
        if url.endswith("/db/data/transaction/commit"):
            console.print("Neo4j: legacy single-db endpoint detected; database selection is not supported.", style="yellow")

    return 0


def _resolve_out_dir(vault_path: Path, out_dir: Path) -> Path:
    # If the user passes a relative path, interpret it relative to the vault root.
    return out_dir if out_dir.is_absolute() else (vault_path / out_dir)


def _write_csv(path: Path, columns: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow(r)


def run_neo4j_export(
    vault_path: Path,
    *,
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
) -> int:
    """Export a bundle of inspection artifacts (CSV/JSON) from Neo4j.

    Convenience wrapper around the manual query pack in `content/meta/graphs/Neo4j Manual Queries.md`.
    """
    console = Console(stderr=True)

    out_base = _resolve_out_dir(vault_path, out_dir)
    if stamp:
        out_base = out_base / date.today().isoformat()
    out_base.mkdir(parents=True, exist_ok=True)

    client = Neo4jHttpClient(
        Neo4jHttpConfig(http_uri=http_uri, user=user, password=password, database=database, allow_default_db_fallback=False)
    )

    # Clamp to match MCP row limits.
    top = max(1, min(500, int(top)))

    try:
        # 1) Counts
        q_counts = (
            "MATCH (n:Note) "
            "WITH count(n) AS notes "
            "MATCH ()-[r:LINKS_TO]->() "
            "WITH notes, sum(r.count) AS link_occurrences, count(r) AS link_edges "
            "MATCH ()-[d:DEPENDS_ON]->() "
            "RETURN notes, link_edges, link_occurrences, count(1) AS depends_edges "
            "LIMIT 1"
        )
        cols, rows = client.query_rows(q_counts)
        _write_csv(out_base / "1_counts.csv", cols, rows)

        # 2) Top inbound hubs (LINKS_TO occurrences)
        q_inlinks = (
            "MATCH (s:Note)-[r:LINKS_TO]->(t:Note) "
            "RETURN t.note_id, t.title, sum(r.count) AS inlink_occurrences "
            "ORDER BY inlink_occurrences DESC, t.note_id ASC "
            f"LIMIT {top}"
        )
        cols, rows = client.query_rows(q_inlinks)
        _write_csv(out_base / "2_top_inlinks.csv", cols, rows)

        # 3) Top “requirements hubs” (incoming DEPENDS_ON)
        q_in_dep = (
            "MATCH (:Note)-[:DEPENDS_ON]->(t:Note:Concept) "
            "RETURN t.note_id, t.title, count(1) AS in_depends "
            "ORDER BY in_depends DESC, t.note_id ASC "
            f"LIMIT {top}"
        )
        cols, rows = client.query_rows(q_in_dep)
        _write_csv(out_base / "3_top_in_depends.csv", cols, rows)

        # 4) Mentions without requirements (concept→concept links without DEPENDS_ON)
        q_mentions_without = (
            "MATCH (c:Note:Concept)-[:LINKS_TO]->(t:Note:Concept) "
            "WHERE NOT (c)-[:DEPENDS_ON]->(t) "
            "RETURN c.note_id AS src, t.note_id AS dst "
            "ORDER BY src ASC, dst ASC "
            "LIMIT 500"
        )
        cols, rows = client.query_rows(q_mentions_without)
        _write_csv(out_base / "4_mentions_without_depends.csv", cols, rows)

        # 5) Requirements without mentions
        q_dep_without_mentions = (
            "MATCH (c:Note:Concept)-[:DEPENDS_ON]->(t:Note:Concept) "
            "WHERE NOT (c)-[:LINKS_TO]->(t) "
            "RETURN c.note_id AS src, t.note_id AS dst "
            "ORDER BY src ASC, dst ASC "
            "LIMIT 500"
        )
        cols, rows = client.query_rows(q_dep_without_mentions)
        _write_csv(out_base / "5_depends_without_mentions.csv", cols, rows)

        # 6) Touch vs require for a specific concept (two CSVs)
        q_touch = (
            "MATCH (c:Note:Concept {note_id: $note_id})-[r:LINKS_TO]->(t:Note:Concept) "
            "RETURN t.note_id, t.title, r.count "
            "ORDER BY r.count DESC, t.note_id ASC "
            "LIMIT 500"
        )
        cols, rows = client.query_rows(q_touch, parameters={"note_id": concept_note_id})
        _write_csv(out_base / "6_touch_links_to_concepts.csv", cols, rows)

        q_req = (
            "MATCH (c:Note:Concept {note_id: $note_id})-[r:DEPENDS_ON]->(t:Note:Concept) "
            "RETURN t.note_id, t.title, t.layer, r.from_frontmatter, r.from_structural "
            "ORDER BY t.note_id ASC "
            "LIMIT 500"
        )
        cols, rows = client.query_rows(q_req, parameters={"note_id": concept_note_id})
        _write_csv(out_base / "7_requires_depends_on.csv", cols, rows)

        # 7) Community summary + bridge nodes (links topology)
        q_comm = (
            "MATCH (n:Note:Concept) "
            "WHERE n.community_links_greedy IS NOT NULL "
            "WITH n.community_links_greedy AS community, count(1) AS nodes, "
            "sum(coalesce(n.boundary_edges_links_greedy, 0)) AS boundary_edges "
            "RETURN community, nodes, boundary_edges "
            "ORDER BY nodes DESC, community ASC "
            "LIMIT 50"
        )
        cols, rows = client.query_rows(q_comm)
        _write_csv(out_base / "8_communities_links.csv", cols, rows)

        q_bridge = (
            "MATCH (n:Note:Concept) "
            "WHERE n.community_links_greedy IS NOT NULL AND coalesce(n.boundary_edges_links_greedy, 0) > 0 "
            "RETURN n.note_id, n.title, n.layer, n.community_links_greedy AS community, "
            "n.bridge_links_greedy AS bridge, n.boundary_edges_links_greedy AS boundary_edges "
            "ORDER BY boundary_edges DESC, bridge DESC, n.note_id ASC "
            f"LIMIT {top}"
        )
        cols, rows = client.query_rows(q_bridge)
        _write_csv(out_base / "9_bridge_nodes_links.csv", cols, rows)

        # 8) Projection subgraphs: projection → community counts (links)
        q_proj_comm = (
            "MATCH (p:Note:Projection)-[:LINKS_TO]->(c:Note:Concept) "
            "WHERE c.community_links_greedy IS NOT NULL "
            "WITH p, c.community_links_greedy AS community, count(1) AS n "
            "RETURN p.note_id, p.title, community, n "
            "ORDER BY p.note_id ASC, n DESC, community ASC "
            "LIMIT 500"
        )
        cols, rows = client.query_rows(q_proj_comm)
        _write_csv(out_base / "10_projection_community_counts.csv", cols, rows)

        # 9) Export concept-only two-layer graph (nodes/edges CSV + JSON)
        q_graph = """
MATCH (n:Note:Concept)
WITH collect({
  id: n.note_id,
  label: n.title,
  role: n.role,
  layer: n.layer,
  community: n.community_links_greedy
}) AS nodes
MATCH (s:Note:Concept)-[r:LINKS_TO]->(t:Note:Concept)
WITH nodes, collect({
  source: s.note_id,
  target: t.note_id,
  type: "LINKS_TO",
  weight: r.count
}) AS links
MATCH (s:Note:Concept)-[d:DEPENDS_ON]->(t:Note:Concept)
WITH nodes, links, collect({
  source: s.note_id,
  target: t.note_id,
  type: "DEPENDS_ON",
  weight: 1,
  from_frontmatter: d.from_frontmatter,
  from_structural: d.from_structural
}) AS dep_links
WITH nodes, links + dep_links AS links
RETURN {nodes: nodes, links: links} AS graph
LIMIT 1
"""
        _, graph_rows = client.query_rows(q_graph)
        graph_obj: dict[str, Any] = {}
        if graph_rows and graph_rows[0] and isinstance(graph_rows[0][0], dict):
            graph_obj = graph_rows[0][0]

        (out_base / "11_two_layer_graph.json").write_text(
            json.dumps(graph_obj, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        nodes = graph_obj.get("nodes") if isinstance(graph_obj, dict) else None
        links = graph_obj.get("links") if isinstance(graph_obj, dict) else None
        if isinstance(nodes, list):
            node_cols = ["id", "label", "role", "layer", "community"]
            node_rows = [[n.get(c) for c in node_cols] for n in nodes if isinstance(n, dict)]
            _write_csv(out_base / "11_two_layer_nodes.csv", node_cols, node_rows)
        if isinstance(links, list):
            edge_cols = ["source", "target", "type", "weight", "from_frontmatter", "from_structural"]
            edge_rows = [[e.get(c) for c in edge_cols] for e in links if isinstance(e, dict)]
            _write_csv(out_base / "11_two_layer_edges.csv", edge_cols, edge_rows)

        if include_mentions or include_ghost_terms or include_definition_tokens:
            vault = load_vault(vault_path)
            concepts = list(vault.concepts)

            def concept_note_id_for(c) -> str:
                return _note_id(vault_path, c.path)

            # Build an alias index: canonical concept name -> list of aliases.
            aliases_by_canonical: dict[str, list[str]] = {}
            for alias, canon in (getattr(vault, "_aliases", {}) or {}).items():
                aliases_by_canonical.setdefault(str(canon).lower(), []).append(str(alias).lower())

            concept_by_name: dict[str, Any] = {c.name.lower(): c for c in concepts}

            # Existing structural edges/links from Neo4j export graph.
            existing_links: set[tuple[str, str]] = set()
            existing_depends: set[tuple[str, str]] = set()
            if isinstance(links, list):
                for e in links:
                    if not isinstance(e, dict):
                        continue
                    s = e.get("source")
                    t = e.get("target")
                    typ = e.get("type")
                    if isinstance(s, str) and isinstance(t, str):
                        if typ == "LINKS_TO":
                            existing_links.add((s, t))
                        elif typ == "DEPENDS_ON":
                            existing_depends.add((s, t))

            def _variant_patterns_for_target(target_concept) -> list[re.Pattern[str]]:
                variants: set[str] = set()
                name = (target_concept.name or "").lower().strip()
                if name:
                    variants.add(name)
                    variants.add(name.replace("-", " "))

                title = (getattr(target_concept, "title", "") or "").lower().strip()
                if title:
                    variants.add(title)
                    variants.add(title.replace("-", " "))

                for a in aliases_by_canonical.get(name, []):
                    a = (a or "").lower().strip()
                    if a:
                        variants.add(a)
                        variants.add(a.replace("-", " "))

                pats: list[re.Pattern[str]] = []
                for v in sorted(variants):
                    toks = [t for t in re.split(r"[-\s]+", v) if t]
                    if not toks:
                        continue
                    if any(len(t) < 3 for t in toks) and len(toks) == 1:
                        # Avoid extremely short single-token matches.
                        continue
                    if len(toks) == 1:
                        rx = rf"\b{re.escape(toks[0])}\b"
                    else:
                        rx = r"\b" + r"[-\s]+".join(re.escape(t) for t in toks) + r"\b"
                    pats.append(re.compile(rx, re.IGNORECASE))
                return pats

            patterns_by_target_id: dict[str, list[re.Pattern[str]]] = {}
            for t in concepts:
                patterns_by_target_id[concept_note_id_for(t)] = _variant_patterns_for_target(t)

            def _definition_text(note_content: str) -> str:
                sec = extract_section(note_content, "Definition") or ""
                return sec

            BACKTICK_RE = re.compile(r"`([^`]{2,60})`")

            def _normalize_ghost(term: str) -> str:
                s = term.strip().lower()
                # Drop obviously non-terms.
                if any(ch in s for ch in ("(", ")", "{", "}", "[", "]", "/", "\\")):
                    return ""
                s = re.sub(r"\s+", " ", s)
                return s

            def _ghost_id(term: str) -> str:
                s = term.lower().strip()
                s = re.sub(r"[^0-9a-zA-Z]+", "-", s).strip("-")
                return f"ghost/{s[:64] or 'term'}"

            mention_rows: list[list[Any]] = []
            ghost_rows: list[list[Any]] = []
            token_rows: list[list[Any]] = []
            mention_links: list[dict[str, Any]] = []
            ghost_links: list[dict[str, Any]] = []
            token_links: list[dict[str, Any]] = []
            ghost_nodes: dict[str, dict[str, Any]] = {}
            token_nodes: dict[str, dict[str, Any]] = {}

            # Tokenization config for "ghost vocabulary" probes.
            STOPWORDS: set[str] = {
                "a",
                "an",
                "and",
                "are",
                "as",
                "at",
                "be",
                "but",
                "by",
                "can",
                "could",
                "does",
                "for",
                "from",
                "has",
                "have",
                "how",
                "if",
                "in",
                "into",
                "is",
                "it",
                "its",
                "may",
                "more",
                "most",
                "not",
                "of",
                "on",
                "or",
                "other",
                "our",
                "so",
                "such",
                "than",
                "that",
                "the",
                "their",
                "then",
                "there",
                "these",
                "this",
                "to",
                "under",
                "we",
                "what",
                "when",
                "which",
                "with",
                "without",
                "you",
                "your",
            }

            # Exclude tokens that are already part of the *named* concept vocabulary (names + aliases),
            # so the token graph surfaces "unknown" lexicon rather than duplicating the concept graph.
            known_vocab: set[str] = set()
            for c in concepts:
                for raw in [c.name, getattr(c, "title", "")] + list(getattr(c, "aliases", []) or []):
                    s = (raw or "").lower().strip()
                    if not s:
                        continue
                    for tok in re.split(r"[-\s]+", s):
                        tok = tok.strip()
                        if tok:
                            known_vocab.add(tok)

            FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
            WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z-]{2,}")

            def tokenize_definition(text: str) -> list[str]:
                # Strip code blocks, normalize separators, then extract word-like tokens.
                t = FENCE_RE.sub(" ", text)
                for sep in (
                    "—",
                    "–",
                    "→",
                    "↔",
                    "\u00e2\u20ac\u2014",
                    "\u00e2\u20ac\u2013",
                    "\u00e2\u2020\u2019",
                    "\u00e2\u2020\u201d",
                ):
                    t = t.replace(sep, " ")
                tokens = []
                for m in WORD_RE.findall(t):
                    tok = m.lower().strip("-")
                    if not tok or tok in STOPWORDS:
                        continue
                    if tok in known_vocab:
                        continue
                    tokens.append(tok)
                return tokens

            # First pass: token counts per concept + document frequency.
            token_tf: dict[str, dict[str, int]] = {}
            token_df: dict[str, int] = {}
            if include_definition_tokens:
                for src in concepts:
                    src_id = concept_note_id_for(src)
                    src_def = _definition_text(src.content)
                    if not src_def.strip():
                        continue
                    toks = tokenize_definition(src_def)
                    if not toks:
                        continue
                    counts: dict[str, int] = {}
                    for t in toks:
                        counts[t] = counts.get(t, 0) + 1
                    token_tf[src_id] = counts
                    for t in counts.keys():
                        token_df[t] = token_df.get(t, 0) + 1

            for src in concepts:
                src_id = concept_note_id_for(src)
                src_def = _definition_text(src.content)
                if not src_def.strip():
                    continue

                # Concept mentions in Definition.
                if include_mentions:
                    for dst in concepts:
                        dst_id = concept_note_id_for(dst)
                        if dst_id == src_id:
                            continue
                        pats = patterns_by_target_id.get(dst_id) or []
                        if not pats:
                            continue
                        # Take the max match count across variants to avoid double-counting.
                        count = 0
                        for pat in pats:
                            n = len(pat.findall(src_def))
                            if n > count:
                                count = n
                        if count <= 0:
                            continue

                        has_link = (src_id, dst_id) in existing_links
                        has_depends = (src_id, dst_id) in existing_depends
                        if has_link:
                            # This is already visible in LINKS_TO; the interesting set is unlinked mentions.
                            continue

                        mention_rows.append([src_id, src.title, dst_id, dst.title, count, has_depends])
                        if not has_depends:
                            mention_links.append(
                                {"source": src_id, "target": dst_id, "type": "MENTIONS", "weight": count}
                            )

                # Ghost terms: backticked spans in Definition that don't resolve to any concept.
                if include_ghost_terms:
                    counts: dict[str, int] = {}
                    for raw in BACKTICK_RE.findall(src_def):
                        term = _normalize_ghost(raw)
                        if not term:
                            continue
                        # If it resolves to a known concept (name/alias), skip.
                        cand = term
                        cand2 = term.replace(" ", "-")
                        resolved = vault.get(cand) or vault.get(cand2)
                        if resolved and getattr(resolved, "role", None) == "concept":
                            continue
                        counts[term] = counts.get(term, 0) + 1

                    for term, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:50]:
                        gid = _ghost_id(term)
                        ghost_nodes.setdefault(
                            gid,
                            {"id": gid, "label": term, "role": "ghost", "layer": "ghost", "community": "ghost"},
                        )
                        ghost_rows.append([src_id, src.title, gid, term, n])
                        ghost_links.append({"source": src_id, "target": gid, "type": "GHOST_MENTIONS", "weight": n})

                if include_definition_tokens and src_id in token_tf:
                    # Filter tokens by document frequency range, then keep top per concept by tf-idf.
                    counts = token_tf[src_id]
                    scored: list[tuple[float, str, int, int]] = []
                    for tok, tf in counts.items():
                        df = token_df.get(tok, 0)
                        if df < max(1, int(token_min_df)):
                            continue
                        if int(token_max_df) > 0 and df > int(token_max_df):
                            continue
                        # Simple tf-idf-ish score (no heavy math): tf * log((N+1)/(df+1)).
                        # Keep it monotone and interpretable; this is exploratory.
                        n_docs = max(1, len(token_tf))
                        score = tf * (1.0 + (n_docs / (df + 1.0)) ** 0.5)
                        scored.append((score, tok, tf, df))
                    scored.sort(key=lambda x: (-x[0], x[1]))
                    for score, tok, tf, df in scored[: max(1, int(token_top_per_concept))]:
                        tid = f"token/{tok}"
                        token_nodes.setdefault(
                            tid,
                            {
                                "id": tid,
                                "label": tok,
                                "role": "token",
                                "layer": "token",
                                "community": "token",
                            },
                        )
                        token_rows.append([src_id, src.title, tid, tok, tf, df, round(score, 3)])
                        token_links.append({"source": src_id, "target": tid, "type": "TOKEN", "weight": tf, "df": df})

            if include_mentions:
                _write_csv(
                    out_base / "12_mentions_unlinked_definition.csv",
                    ["source", "source_title", "target", "target_title", "count_in_definition", "has_depends_on"],
                    mention_rows,
                )

            if include_ghost_terms:
                _write_csv(
                    out_base / "12_ghost_terms_definition.csv",
                    ["source", "source_title", "ghost_id", "term", "count_in_definition"],
                    ghost_rows,
                )

            if include_definition_tokens:
                _write_csv(
                    out_base / "13_definition_tokens.csv",
                    ["source", "source_title", "token_id", "token", "tf_in_definition", "df_across_concepts", "score"],
                    token_rows,
                )

            # Optional graph JSON for the d3 viewer (adds ghost nodes + mention edges + token nodes).
            if isinstance(graph_obj, dict):
                base_nodes = list(nodes) if isinstance(nodes, list) else []
                base_links = list(links) if isinstance(links, list) else []

                g_mentions = {"nodes": list(base_nodes), "links": list(base_links)}
                if include_ghost_terms:
                    # Only include ghost nodes that actually appear.
                    g_mentions["nodes"] = list(g_mentions["nodes"]) + list(ghost_nodes.values())
                    g_mentions["links"] = list(g_mentions["links"]) + ghost_links
                if include_mentions:
                    # Only include semantic-implicit mentions (unlinked + undeclared) as edges.
                    g_mentions["links"] = list(g_mentions["links"]) + mention_links

                if include_mentions or include_ghost_terms:
                    (out_base / "12_mentions_graph.json").write_text(
                        json.dumps(g_mentions, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )

                if include_definition_tokens:
                    g_tokens = {"nodes": list(g_mentions["nodes"]), "links": list(g_mentions["links"])}
                    g_tokens["nodes"] = list(g_tokens["nodes"]) + list(token_nodes.values())
                    g_tokens["links"] = list(g_tokens["links"]) + token_links
                    (out_base / "13_definition_tokens_graph.json").write_text(
                        json.dumps(g_tokens, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )

    except Exception as e:
        console.print(str(e), style="red")
        return 1

    # Audit log: count files written
    from irrev.audit_log import log_operation, CreationSummary

    files_written = len(list(out_base.glob("*.csv"))) + len(list(out_base.glob("*.json")))
    bytes_written = sum(f.stat().st_size for f in out_base.iterdir() if f.is_file())

    log_operation(
        vault_path,
        operation="neo4j-export",
        created=CreationSummary(files=files_written, bytes_written=bytes_written),
        metadata={
            "out_dir": str(out_base),
            "database": database,
            "include_mentions": include_mentions,
            "include_ghost_terms": include_ghost_terms,
            "include_definition_tokens": include_definition_tokens,
        },
    )

    console.print(f"Wrote Neo4j export bundle to {out_base}", style="green")
    return 0
