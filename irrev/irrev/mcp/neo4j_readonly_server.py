"""Read-only MCP server for Neo4j vault graph.

Implements a minimal MCP-over-stdio JSON-RPC loop with LSP-style framing.

This server is intentionally strict:
- requires an `intent` field on calls
- rejects any Cypher that isn't clearly read-only and bounded
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from ..neo4j.http import Neo4jHttpClient, Neo4jHttpConfig


_INTENTS = ("analysis", "audit", "inspection", "exploration")
_MAX_ROWS = 500
_MAX_HOPS = 6
_TOPOLOGY_MODES = ("links", "depends_on", "both")


_FORBIDDEN_TOKENS = (
    "call",
    "load csv",
    "create",
    "merge",
    "set",
    "delete",
    "detach delete",
    "remove",
    "drop",
    "alter",
    "apoc.",
)


def _jsonrpc_error(code: int, message: str, *, request_id: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _jsonrpc_result(result: Any, *, request_id: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


# MCP clients vary on stdio framing. Some use LSP-style Content-Length headers,
# others send newline-delimited JSON. We autodetect based on the first message
# received and respond in the same framing for compatibility.
_USE_LSP_FRAMING: bool | None = None


def _read_message(stdin: Any) -> dict[str, Any] | None:
    """Read one JSON-RPC message.

    Supports:
    - LSP-style framing with Content-Length headers
    - newline-delimited JSON (best-effort)
    """
    first = stdin.readline()
    if not first:
        return None

    global _USE_LSP_FRAMING

    # LSP-style framing (case-insensitive).
    if first.lower().startswith(b"content-length:"):
        if _USE_LSP_FRAMING is None:
            _USE_LSP_FRAMING = True
        headers: dict[str, str] = {}
        line = first
        while line and line.strip():
            try:
                k, v = line.decode("ascii", errors="ignore").split(":", 1)
                headers[k.strip().lower()] = v.strip()
            except ValueError:
                pass
            line = stdin.readline()

        try:
            length = int(headers.get("content-length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            return None
        body = stdin.read(length)
        return json.loads(body.decode("utf-8"))

    # Assume JSON on this line
    if _USE_LSP_FRAMING is None:
        _USE_LSP_FRAMING = False
    return json.loads(first.decode("utf-8"))


def _write_message(stdout: Any, message: dict[str, Any]) -> None:
    body = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    # Default to LSP framing if we haven't yet seen a request (should be rare).
    use_lsp = True if _USE_LSP_FRAMING is None else _USE_LSP_FRAMING

    if use_lsp:
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        stdout.write(header)
        stdout.write(body)
    else:
        stdout.write(body + b"\n")
    stdout.flush()


def _require_intent(arguments: dict[str, Any]) -> str:
    intent = arguments.get("intent")
    if not isinstance(intent, str) or intent.strip() == "":
        raise ValueError("Missing required argument: intent")
    intent = intent.strip().lower()
    if intent not in _INTENTS:
        raise ValueError(f"Invalid intent (expected one of {', '.join(_INTENTS)}): {intent}")
    return intent


_LIMIT_RE = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)
_STAR_SEGMENT_RE = re.compile(r"\*\s*(\d+)(?:\s*\.\.\s*(\d+))?")


def _validate_read_cypher(query: str) -> None:
    q = query.strip()
    if not q:
        raise ValueError("Empty query")
    if ";" in q:
        raise ValueError("Multiple statements are not allowed (semicolon found)")

    ql = q.lower()
    if "return" not in ql:
        raise ValueError("Query must contain RETURN")

    # Read-ish entrypoints.
    if not (ql.startswith("match") or ql.startswith("optional match") or ql.startswith("with")):
        raise ValueError("Query must start with MATCH / OPTIONAL MATCH / WITH")

    # Strip string literals / identifiers / comments before keyword scans so note_ids like
    # "concepts/feasible-set" don't trigger the forbidden "set" clause check.
    q_scan = q
    q_scan = re.sub(r"//.*?$", "", q_scan, flags=re.MULTILINE)
    q_scan = re.sub(r"/\*.*?\*/", "", q_scan, flags=re.DOTALL)
    q_scan = re.sub(r"`[^`]*`", "``", q_scan)
    q_scan = re.sub(r"\"[^\"]*\"", "\"\"", q_scan)
    q_scan = re.sub(r"'(?:\\'|[^'])*'", "''", q_scan)
    ql_scan = q_scan.lower()

    forbidden_patterns: list[tuple[str, re.Pattern[str]]] = [
        ("load csv", re.compile(r"\bload\s+csv\b", re.IGNORECASE)),
        ("detach delete", re.compile(r"\bdetach\s+delete\b", re.IGNORECASE)),
        ("apoc.", re.compile(r"\bapoc\.", re.IGNORECASE)),
        ("call", re.compile(r"\bcall\b", re.IGNORECASE)),
        ("create", re.compile(r"\bcreate\b", re.IGNORECASE)),
        ("merge", re.compile(r"\bmerge\b", re.IGNORECASE)),
        ("set", re.compile(r"\bset\b", re.IGNORECASE)),
        ("delete", re.compile(r"\bdelete\b", re.IGNORECASE)),
        ("remove", re.compile(r"\bremove\b", re.IGNORECASE)),
        ("drop", re.compile(r"\bdrop\b", re.IGNORECASE)),
        ("alter", re.compile(r"\balter\b", re.IGNORECASE)),
    ]

    for tok, pat in forbidden_patterns:
        if pat.search(ql_scan):
            raise ValueError(f"Forbidden token in query: {tok}")

    # Must be bounded.
    m = _LIMIT_RE.search(q)
    if not m:
        raise ValueError(f"Query must include LIMIT (<= {_MAX_ROWS})")
    limit = int(m.group(1))
    if limit <= 0 or limit > _MAX_ROWS:
        raise ValueError(f"LIMIT must be between 1 and {_MAX_ROWS} (got {limit})")

    # Variable-length traversal closure lock.
    if "*" in q:
        for i, ch in enumerate(q):
            if ch != "*":
                continue
            segment = q[i : i + 20]
            sm = _STAR_SEGMENT_RE.match(segment)
            if not sm:
                raise ValueError("Unbounded variable-length traversal is not allowed; use *1..N with N bounded")
            upper = sm.group(2)
            if upper is None:
                # *N (exact) is okay if <= max hops.
                n = int(sm.group(1))
                if n > _MAX_HOPS:
                    raise ValueError(f"Traversal bound exceeds max hops ({_MAX_HOPS}): {n}")
            else:
                n2 = int(upper)
                if n2 > _MAX_HOPS:
                    raise ValueError(f"Traversal upper bound exceeds max hops ({_MAX_HOPS}): {n2}")


def _tool_defs() -> list[dict[str, Any]]:
    def cypher_tool(name: str, description: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {"name": name, "description": description, "inputSchema": schema}

    return [
        cypher_tool(
            "cypher_read",
            "Run a validated, bounded Cypher read query (requires intent; rejects writes/unbounded traversals).",
            {
                "type": "object",
                "required": ["intent", "query"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "query": {"type": "string"},
                    "params": {"type": "object"},
                },
            },
        ),
        cypher_tool(
            "note_by_id",
            "Fetch a note node by note_id.",
            {
                "type": "object",
                "required": ["intent", "note_id"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "note_id": {"type": "string"},
                },
            },
        ),
        cypher_tool(
            "outlinks",
            "List outbound LINKS_TO edges for a note.",
            {
                "type": "object",
                "required": ["intent", "note_id"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "note_id": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_ROWS, "default": 50},
                },
            },
        ),
        cypher_tool(
            "inlinks",
            "List inbound LINKS_TO edges for a note.",
            {
                "type": "object",
                "required": ["intent", "note_id"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "note_id": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_ROWS, "default": 50},
                },
            },
        ),
        cypher_tool(
            "missing_failure_modes",
            "List projections with empty/absent failure_modes frontmatter.",
            {
                "type": "object",
                "required": ["intent"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_ROWS, "default": 200},
                },
            },
        ),
        cypher_tool(
            "community_summary",
            "Summarize greedy communities for Concept nodes (requires neo4j load with topology properties).",
            {
                "type": "object",
                "required": ["intent", "mode"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "mode": {"type": "string", "enum": list(_TOPOLOGY_MODES)},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_ROWS, "default": 50},
                },
            },
        ),
        cypher_tool(
            "community_members",
            "List members of a greedy community for Concept nodes.",
            {
                "type": "object",
                "required": ["intent", "mode", "community"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "mode": {"type": "string", "enum": list(_TOPOLOGY_MODES)},
                    "community": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_ROWS, "default": 100},
                },
            },
        ),
        cypher_tool(
            "bridge_nodes",
            "List top bridge nodes (Concepts connecting multiple communities).",
            {
                "type": "object",
                "required": ["intent", "mode"],
                "properties": {
                    "intent": {"type": "string", "enum": list(_INTENTS)},
                    "mode": {"type": "string", "enum": list(_TOPOLOGY_MODES)},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_ROWS, "default": 50},
                },
            },
        ),
    ]


def _as_tool_text(obj: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False, indent=2)}]}


def _run_canned_query(client: Neo4jHttpClient, query: str, params: dict[str, Any]) -> dict[str, Any]:
    columns, rows = client.query_rows(query, parameters=params)
    return {"columns": columns, "rows": rows}


def _handle_tool_call(client: Neo4jHttpClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    _require_intent(arguments)

    if name == "cypher_read":
        query = arguments.get("query")
        if not isinstance(query, str):
            raise ValueError("query must be a string")
        _validate_read_cypher(query)
        params = arguments.get("params") or {}
        if not isinstance(params, dict):
            raise ValueError("params must be an object")
        result = _run_canned_query(client, query, params)
        return _as_tool_text(result)

    if name == "note_by_id":
        note_id = arguments.get("note_id")
        if not isinstance(note_id, str) or not note_id.strip():
            raise ValueError("note_id must be a non-empty string")
        q = (
            "MATCH (n:Note {note_id: $note_id}) "
            "RETURN n.note_id, n.title, n.role, n.layer, n.canonical, n.tags, n.path, n.folder, "
            "n.community_links_greedy, n.community_depends_greedy, n.community_both_greedy, "
            "n.bridge_links_greedy, n.bridge_depends_greedy, n.bridge_both_greedy, "
            "n.boundary_edges_links_greedy, n.boundary_edges_depends_greedy, n.boundary_edges_both_greedy "
            "LIMIT 1"
        )
        return _as_tool_text(_run_canned_query(client, q, {"note_id": note_id}))

    if name == "outlinks":
        note_id = arguments.get("note_id")
        if not isinstance(note_id, str) or not note_id.strip():
            raise ValueError("note_id must be a non-empty string")
        limit = int(arguments.get("limit") or 50)
        limit = max(1, min(_MAX_ROWS, limit))
        q = (
            "MATCH (s:Note {note_id: $note_id})-[r:LINKS_TO]->(t:Note) "
            "RETURN t.note_id, t.title, r.count "
            "ORDER BY r.count DESC, t.note_id ASC "
            "LIMIT $limit"
        )
        return _as_tool_text(_run_canned_query(client, q, {"note_id": note_id, "limit": limit}))

    if name == "inlinks":
        note_id = arguments.get("note_id")
        if not isinstance(note_id, str) or not note_id.strip():
            raise ValueError("note_id must be a non-empty string")
        limit = int(arguments.get("limit") or 50)
        limit = max(1, min(_MAX_ROWS, limit))
        q = (
            "MATCH (s:Note)-[r:LINKS_TO]->(t:Note {note_id: $note_id}) "
            "RETURN s.note_id, s.title, r.count "
            "ORDER BY r.count DESC, s.note_id ASC "
            "LIMIT $limit"
        )
        return _as_tool_text(_run_canned_query(client, q, {"note_id": note_id, "limit": limit}))

    if name == "missing_failure_modes":
        limit = int(arguments.get("limit") or 200)
        limit = max(1, min(_MAX_ROWS, limit))
        q = (
            "MATCH (p:Note:Projection) "
            "WHERE p.failure_modes IS NULL OR size(p.failure_modes) = 0 "
            "RETURN p.note_id, p.title "
            "ORDER BY p.note_id ASC "
            "LIMIT $limit"
        )
        return _as_tool_text(_run_canned_query(client, q, {"limit": limit}))

    if name in {"community_summary", "community_members", "bridge_nodes"}:
        mode = arguments.get("mode")
        if mode not in _TOPOLOGY_MODES:
            raise ValueError(f"mode must be one of: {', '.join(_TOPOLOGY_MODES)}")
        prop_community = {
            "links": "community_links_greedy",
            "depends_on": "community_depends_greedy",
            "both": "community_both_greedy",
        }[mode]
        prop_bridge = {
            "links": "bridge_links_greedy",
            "depends_on": "bridge_depends_greedy",
            "both": "bridge_both_greedy",
        }[mode]
        prop_boundary = {
            "links": "boundary_edges_links_greedy",
            "depends_on": "boundary_edges_depends_greedy",
            "both": "boundary_edges_both_greedy",
        }[mode]

        if name == "community_summary":
            limit = int(arguments.get("limit") or 50)
            limit = max(1, min(_MAX_ROWS, limit))
            q = (
                "MATCH (n:Note:Concept) "
                f"WHERE n.{prop_community} IS NOT NULL "
                f"WITH n.{prop_community} AS community, "
                f"count(*) AS node_count, "
                f"avg(coalesce(n.{prop_bridge}, 0.0)) AS avg_bridge, "
                f"sum(coalesce(n.{prop_boundary}, 0)) AS boundary_edges "
                "RETURN community, node_count, avg_bridge, boundary_edges "
                "ORDER BY node_count DESC, community ASC "
                "LIMIT $limit"
            )
            return _as_tool_text(_run_canned_query(client, q, {"limit": limit}))

        if name == "community_members":
            community = arguments.get("community")
            if not isinstance(community, int) or community < 0:
                raise ValueError("community must be an integer >= 0")
            limit = int(arguments.get("limit") or 100)
            limit = max(1, min(_MAX_ROWS, limit))
            q = (
                "MATCH (n:Note:Concept) "
                f"WHERE n.{prop_community} = $community "
                f"RETURN n.note_id, n.title, n.layer, n.{prop_bridge} AS bridge, n.{prop_boundary} AS boundary_edges "
                "ORDER BY boundary_edges DESC, bridge DESC, n.note_id ASC "
                "LIMIT $limit"
            )
            return _as_tool_text(_run_canned_query(client, q, {"community": community, "limit": limit}))

        if name == "bridge_nodes":
            limit = int(arguments.get("limit") or 50)
            limit = max(1, min(_MAX_ROWS, limit))
            q = (
                "MATCH (n:Note:Concept) "
                f"WHERE n.{prop_community} IS NOT NULL AND coalesce(n.{prop_boundary}, 0) > 0 "
                f"RETURN n.note_id, n.title, n.layer, n.{prop_community} AS community, "
                f"n.{prop_bridge} AS bridge, n.{prop_boundary} AS boundary_edges "
                "ORDER BY boundary_edges DESC, bridge DESC, n.note_id ASC "
                "LIMIT $limit"
            )
            return _as_tool_text(_run_canned_query(client, q, {"limit": limit}))

    raise ValueError(f"Unknown tool: {name}")


def _server_info() -> dict[str, Any]:
    return {"name": "irrev-neo4j-readonly", "version": "0.1.0"}


def _resource_defs() -> list[dict[str, Any]]:
    return [
        {
            "uri": "irrev-neo4j:///schema",
            "name": "Vault Graph Schema (static)",
            "description": "Static schema summary for the derived Neo4j vault graph.",
            "mimeType": "application/json",
        },
    ]


def _resource_template_defs() -> list[dict[str, Any]]:
    return [
        {
            "uriTemplate": "irrev-neo4j:///cypher?intent={intent}&query={query}",
            "name": "cypher_read",
            "description": "Run a validated, bounded Cypher read query; query must be URL-encoded; params not supported.",
            "mimeType": "application/json",
        }
    ]


def _schema_summary() -> dict[str, Any]:
    return {
        "nodeLabels": ["Note"],
        "roleLabels": [
            "Concept",
            "Projection",
            "Domain",
            "Diagnostic",
            "Paper",
            "Invariant",
            "Meta",
            "Report",
        ],
        "relationships": [
            {"type": "LINKS_TO", "from": "Note", "to": "Note", "properties": ["count"]},
            {"type": "STRUCTURAL_DEPENDS_ON", "from": "Note", "to": "Note", "properties": []},
            {"type": "FRONTMATTER_DEPENDS_ON", "from": "Note", "to": "Note", "properties": []},
        ],
        "derivedProperties": [
            "community_links_greedy",
            "community_depends_greedy",
            "community_both_greedy",
            "bridge_links_greedy",
            "bridge_depends_greedy",
            "bridge_both_greedy",
            "boundary_edges_links_greedy",
            "boundary_edges_depends_greedy",
            "boundary_edges_both_greedy",
        ],
        "noteIdentity": {"property": "note_id", "example": "concepts/constraint-load"},
    }


def _handle_resource_read(client: Neo4jHttpClient, uri: str) -> dict[str, Any]:
    parsed = urlparse(uri)
    if parsed.scheme != "irrev-neo4j":
        raise ValueError("Unsupported resource URI scheme (expected irrev-neo4j)")

    if parsed.path == "/schema":
        payload = _schema_summary()
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2),
                }
            ]
        }

    if parsed.path == "/cypher":
        qs = parse_qs(parsed.query or "")
        intent = (qs.get("intent") or [""])[0]
        query = (qs.get("query") or [""])[0]
        if not intent:
            raise ValueError("Missing required query parameter: intent")
        if not query:
            raise ValueError("Missing required query parameter: query")
        _require_intent({"intent": intent})
        _validate_read_cypher(query)
        columns, rows = client.query_rows(query, parameters={})
        payload = {"columns": columns, "rows": rows}
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2),
                }
            ]
        }

    raise ValueError("Unknown resource URI")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only MCP server for Neo4j vault graph")
    parser.add_argument("--http-uri", default=os.getenv("NEO4J_HTTP_URI", "http://localhost:7474"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "irrev"))
    parser.add_argument(
        "--password",
        default=os.getenv("NEO4J_PASSWORD"),
        help="Neo4j password (prefer env var NEO4J_PASSWORD; avoid passing on CLI history)",
    )
    args = parser.parse_args(argv)

    if not args.password:
        print("NEO4J_PASSWORD is required for MCP server (refusing to prompt on stdio).", file=sys.stderr)
        return 2

    client = Neo4jHttpClient(
        Neo4jHttpConfig(
            http_uri=args.http_uri,
            user=args.user,
            password=args.password,
            database=args.database,
            allow_default_db_fallback=False,
        )
    )

    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    initialized = False

    while True:
        msg = _read_message(stdin)
        if msg is None:
            return 0

        request_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params") or {}

        # Notifications (no id) must not receive responses.
        if request_id is None:
            if method == "exit":
                return 0
            continue

        try:
            if method == "initialize":
                initialized = True
                requested_version = None
                if isinstance(params, dict):
                    requested_version = params.get("protocolVersion")
                protocol_version = (
                    requested_version.strip()
                    if isinstance(requested_version, str) and requested_version.strip()
                    else "2024-11-05"
                )
                result = {
                    "protocolVersion": protocol_version,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": _server_info(),
                }
                _write_message(stdout, _jsonrpc_result(result, request_id=request_id))
                continue

            if method == "shutdown":
                _write_message(stdout, _jsonrpc_result(None, request_id=request_id))
                continue

            if method == "tools/list":
                _write_message(stdout, _jsonrpc_result({"tools": _tool_defs()}, request_id=request_id))
                continue

            if method == "tools/call":
                if not initialized:
                    raise ValueError("Server not initialized")
                if not isinstance(params, dict):
                    raise ValueError("params must be an object")
                tool_name = params.get("name")
                arguments = params.get("arguments") or {}
                if not isinstance(tool_name, str):
                    raise ValueError("tools/call requires name")
                if not isinstance(arguments, dict):
                    raise ValueError("tools/call arguments must be an object")
                result = _handle_tool_call(client, tool_name, arguments)
                _write_message(stdout, _jsonrpc_result(result, request_id=request_id))
                continue

            if method == "resources/list":
                _write_message(stdout, _jsonrpc_result({"resources": _resource_defs()}, request_id=request_id))
                continue

            if method in ("resources/templates/list", "resourceTemplates/list"):
                _write_message(
                    stdout,
                    _jsonrpc_result({"resourceTemplates": _resource_template_defs()}, request_id=request_id),
                )
                continue

            if method in ("resources/read", "resource/read"):
                if not initialized:
                    raise ValueError("Server not initialized")
                if not isinstance(params, dict):
                    raise ValueError("params must be an object")
                uri = params.get("uri")
                if not isinstance(uri, str) or not uri.strip():
                    raise ValueError("resources/read requires uri")
                result = _handle_resource_read(client, uri)
                _write_message(stdout, _jsonrpc_result(result, request_id=request_id))
                continue

            _write_message(stdout, _jsonrpc_error(-32601, f"Method not found: {method}", request_id=request_id))

        except ValueError as e:
            _write_message(stdout, _jsonrpc_error(-32602, str(e), request_id=request_id))
        except Exception as e:
            _write_message(stdout, _jsonrpc_error(-32603, str(e), request_id=request_id))


if __name__ == "__main__":
    raise SystemExit(main())
