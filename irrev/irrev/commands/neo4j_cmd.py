"""Neo4j export/load commands (derived, rebuildable graph state)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from rich.console import Console

from ..neo4j.http import Neo4jHttpClient, Neo4jHttpConfig
from ..vault.loader import Vault, load_vault
from ..vault.parser import extract_frontmatter_depends_on


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
    ]


def _schema_statements_legacy() -> list[dict[str, Any]]:
    # Neo4j 3.5/4.x legacy syntax (no IF NOT EXISTS).
    # Some statements may fail if the constraint/index already exists.
    return [
        {"statement": "CREATE CONSTRAINT ON (n:Note) ASSERT n.note_id IS UNIQUE"},
        {"statement": "CREATE INDEX ON :Note(role)"},
        {"statement": "CREATE INDEX ON :Note(layer)"},
        {"statement": "CREATE INDEX ON :Note(canonical)"},
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
"""

    return {"statement": statement, "parameters": {"edges": edges}}


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


def _build_edges(vault: Vault, vault_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    links_to: list[dict[str, Any]] = []
    depends_on: list[dict[str, Any]] = []
    unresolved = 0

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

        # Frontmatter depends_on (dedup)
        for dep in extract_frontmatter_depends_on(note.frontmatter or {}):
            dst_note = vault.get(dep)
            if not dst_note:
                unresolved += 1
                continue
            dst_id = _note_id(vault_path, dst_note.path)
            depends_on.append({"src": src_id, "dst": dst_id})

    return links_to, depends_on, unresolved


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
) -> int:
    console = Console(stderr=True)

    vault = load_vault(vault_path)
    rows = _build_rows(vault, vault_path)
    links_to, depends_on, unresolved = _build_edges(vault, vault_path)

    client = Neo4jHttpClient(
        Neo4jHttpConfig(http_uri=http_uri, user=user, password=password, database=database, allow_default_db_fallback=False)
    )

    try:
        if mode == "rebuild":
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

        console.print(f"Neo4j: upserting {len(rows)} notes...", style="yellow")
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            client.commit([_upsert_notes_statement(batch)])

        console.print(f"Neo4j: writing {len(links_to)} LINKS_TO edges...", style="yellow")
        for i in range(0, len(links_to), batch_size):
            batch = links_to[i : i + batch_size]
            client.commit([_upsert_links_statement(batch, rel_type="LINKS_TO")])

        console.print(f"Neo4j: writing {len(depends_on)} DEPENDS_ON edges...", style="yellow")
        for i in range(0, len(depends_on), batch_size):
            batch = depends_on[i : i + batch_size]
            client.commit([_upsert_links_statement(batch, rel_type="DEPENDS_ON")])

    except Exception as e:
        console.print(str(e), style="red")
        return 1

    if unresolved:
        console.print(f"Note: {unresolved} unresolved link targets skipped.", style="yellow")

    console.print("Neo4j load complete.", style="green")
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
