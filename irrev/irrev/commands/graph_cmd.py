"""Graph command - inspect vault dependency/link structure."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault


@dataclass
class LinkGraph:
    nodes: set[str] = field(default_factory=set)
    edges: dict[str, set[str]] = field(default_factory=dict)  # src -> dsts
    reverse_edges: dict[str, set[str]] = field(default_factory=dict)  # dst -> srcs

    def add_node(self, name: str) -> None:
        self.nodes.add(name)

    def add_edge(self, src: str, dst: str) -> None:
        self.nodes.add(src)
        self.nodes.add(dst)
        self.edges.setdefault(src, set()).add(dst)
        self.reverse_edges.setdefault(dst, set()).add(src)

    def out_degree(self, name: str) -> int:
        return len(self.edges.get(name, set()))

    def in_degree(self, name: str) -> int:
        return len(self.reverse_edges.get(name, set()))


def run_graph(
    vault_path: Path,
    *,
    concepts_only: bool = True,
    fmt: str = "md",
    out: Path | None = None,
    top: int = 25,
) -> int:
    """Output a graph summary for either concept dependencies or all-note links."""
    console = Console(stderr=True)

    vault = load_vault(vault_path)

    if concepts_only:
        graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)
        data = _graph_from_concept_dependencies(graph)
        title = "Concept dependency graph (concepts-only)"
    else:
        data = _graph_from_all_note_links(vault)
        title = "Vault link graph (all notes)"

    payload = _summarize_graph(data, title=title, top=top)

    text: str
    if fmt == "json":
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    elif fmt == "dot":
        text = _to_dot(data, title=title)
    else:
        text = _to_markdown(payload)

    if out:
        out.write_text(text, encoding="utf-8")
        console.print(f"Wrote graph output to {out}", style="green")
    else:
        print(text, end="" if text.endswith("\n") else "\n")

    return 0


def _graph_from_concept_dependencies(graph: DependencyGraph) -> LinkGraph:
    """Build a graph from Concept.depends_on edges (concepts-only)."""
    g = LinkGraph()
    for src in graph.nodes:
        g.add_node(src)
    for src, deps in graph.edges.items():
        for dep in deps:
            if dep in graph.nodes:
                g.add_edge(src, dep)
    return g


def _graph_from_all_note_links(vault) -> LinkGraph:
    """Build a graph from wiki-links across all notes (all-notes)."""
    g = LinkGraph()

    # Index all notes by canonical name (lower)
    known = {n.name.lower(): n for n in vault.all_notes}

    def resolve(name: str) -> str | None:
        normalized = vault.normalize_name(name)
        if normalized in known:
            return normalized
        if name.lower() in known:
            return name.lower()
        return None

    for note in vault.all_notes:
        src = note.name.lower()
        g.add_node(src)
        for link in note.links:
            dst = resolve(link)
            if dst:
                g.add_edge(src, dst)

    return g


def _summarize_graph(g: LinkGraph, *, title: str, top: int) -> dict:
    nodes = sorted(g.nodes)

    def top_list(kind: str):
        rows = []
        for n in nodes:
            rows.append(
                {
                    "name": n,
                    "in_degree": g.in_degree(n),
                    "out_degree": g.out_degree(n),
                }
            )
        key = "in_degree" if kind == "in" else "out_degree"
        rows.sort(key=lambda r: (r[key], r["name"]), reverse=True)
        return rows[: max(0, top)]

    return {
        "title": title,
        "node_count": len(nodes),
        "edge_count": sum(len(v) for v in g.edges.values()),
        "top_in_degree": top_list("in"),
        "top_out_degree": top_list("out"),
    }


def _to_markdown(payload: dict) -> str:
    lines: list[str] = []
    lines.append(f"## {payload['title']}")
    lines.append("")
    lines.append(f"- Nodes: {payload['node_count']}")
    lines.append(f"- Edges: {payload['edge_count']}")
    lines.append("")

    def table(title: str, rows: list[dict]) -> None:
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| Node | In-degree | Out-degree |")
        lines.append("|---|---:|---:|")
        for r in rows:
            lines.append(f"| `{r['name']}` | {r['in_degree']} | {r['out_degree']} |")
        lines.append("")

    table("Top in-degree", payload["top_in_degree"])
    table("Top out-degree", payload["top_out_degree"])

    return "\n".join(lines).rstrip() + "\n"


def _to_dot(g: LinkGraph, *, title: str) -> str:
    lines = ["digraph vault {", f'  label="{title}";', "  labelloc=t;", "  node [shape=box];"]
    for src, dsts in sorted(g.edges.items()):
        for dst in sorted(dsts):
            lines.append(f'  "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines) + "\n"

