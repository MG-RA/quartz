"""Graph command - inspect vault dependency/link structure."""

from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table

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
    styled: bool = True,
) -> int:
    """Output a graph summary for either concept dependencies or all-note links."""
    console = Console(stderr=True)

    vault = load_vault(vault_path)

    hub_class_by_concept = _load_hub_classes(vault_path)

    if concepts_only:
        graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)
        data = _graph_from_concept_dependencies(graph)
        title = "Concept dependency graph (concepts-only)"
        node_meta = _node_meta_for_concepts(graph, hub_class_by_concept)
    else:
        data = _graph_from_all_note_links(vault)
        title = "Vault link graph (all notes)"
        node_meta = _node_meta_for_all_notes(vault, hub_class_by_concept)

    payload = _summarize_graph(data, title=title, top=top)

    if fmt == "rich":
        if out:
            rich_console = Console(record=True)
            _print_rich(payload, console=rich_console)
            out.write_text(rich_console.export_text(), encoding="utf-8")
            console.print(f"Wrote graph output to {out}", style="green")
        else:
            _print_rich(payload, console=Console())
        return 0

    text: str
    if fmt == "json":
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    elif fmt == "dot":
        text = _to_dot(data, title=title, node_meta=node_meta if styled else None)
    elif fmt == "svg":
        text = _to_svg(data, title=title, node_meta=node_meta if styled else None)
    elif fmt == "html":
        svg = _to_svg(data, title=title, node_meta=node_meta if styled else None)
        text = _wrap_html(svg, title=title)
    else:
        text = _to_markdown(payload)

    if out:
        out.write_text(text, encoding="utf-8")
        console.print(f"Wrote graph output to {out}", style="green")
    else:
        print(text, end="" if text.endswith("\n") else "\n")

    return 0


def _print_rich(payload: dict, *, console: Console) -> None:
    console.print(f"[bold]{payload['title']}[/bold]")
    console.print(f"Nodes: {payload['node_count']}  Edges: {payload['edge_count']}")
    console.print()

    def render_table(title: str, rows: list[dict]) -> None:
        t = Table(title=title, show_header=True, header_style="bold")
        t.add_column("Node", style="cyan", no_wrap=True)
        t.add_column("In", justify="right")
        t.add_column("Out", justify="right")
        for r in rows:
            t.add_row(str(r["name"]), str(r["in_degree"]), str(r["out_degree"]))
        console.print(t)
        console.print()

    render_table("Top in-degree", payload["top_in_degree"])
    render_table("Top out-degree", payload["top_out_degree"])


def _load_hub_classes(vault_path: Path) -> dict[str, str]:
    hubs_path = (vault_path / "meta" / "hubs.yml").resolve()
    if not hubs_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        return {}
    try:
        data = yaml.safe_load(hubs_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    hubs = data.get("hubs") or {}
    if not isinstance(hubs, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in hubs.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        cls = v.get("class")
        if isinstance(cls, str) and cls.strip():
            out[k.strip().lower()] = cls.strip()
    return out


def _node_meta_for_concepts(graph: DependencyGraph, hub_class_by_concept: dict[str, str]) -> dict[str, dict]:
    meta: dict[str, dict] = {}
    for name, concept in graph.nodes.items():
        meta[name] = {
            "role": "concept",
            "layer": (concept.layer or "unknown").strip().lower(),
            "hub_class": hub_class_by_concept.get(name, ""),
        }
    return meta


def _node_meta_for_all_notes(vault, hub_class_by_concept: dict[str, str]) -> dict[str, dict]:
    meta: dict[str, dict] = {}
    for note in vault.all_notes:
        name = note.name.lower()
        m = {"role": (note.role or "unknown").strip().lower()}
        if m["role"] == "concept" and hasattr(note, "layer"):
            m["layer"] = (getattr(note, "layer") or "unknown").strip().lower()
            m["hub_class"] = hub_class_by_concept.get(name, "")
        meta[name] = m
    return meta


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


def _to_dot(g: LinkGraph, *, title: str, node_meta: dict[str, dict] | None = None) -> str:
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    lines = [
        "digraph vault {",
        f'  label="{esc(title)}";',
        "  labelloc=t;",
        "  rankdir=LR;",
        "  bgcolor=\"#0f1115\";",
        "  graph [fontname=\"Helvetica\"];",
        "  node [fontname=\"Helvetica\", fontsize=10, style=filled, fillcolor=\"#1b1f2a\", color=\"#3a4154\", fontcolor=\"#e6e6e6\"];",
        "  edge [color=\"#3a4154\", penwidth=0.8];",
    ]

    if node_meta:
        # Styled nodes
        for name in sorted(g.nodes):
            meta = node_meta.get(name, {})
            role = (meta.get("role") or "unknown").strip().lower()
            layer = (meta.get("layer") or "unknown").strip().lower()
            hub_class = (meta.get("hub_class") or "").strip()
            in_deg = g.in_degree(name)

            attrs = _dot_node_attrs(role=role, layer=layer, hub_class=hub_class, in_degree=in_deg)
            label = name
            if hub_class:
                label = f"{name}\\n(hub: {hub_class})"

            attr_str = "; ".join([f'{k}="{esc(v)}"' for k, v in attrs.items() if v != ""])
            lines.append(f'  "{esc(name)}" [label="{esc(label)}"; {attr_str}];')
    else:
        # Plain nodes (still sets global defaults)
        for name in sorted(g.nodes):
            lines.append(f'  "{esc(name)}";')

    for src, dsts in sorted(g.edges.items()):
        for dst in sorted(dsts):
            lines.append(f'  "{esc(src)}" -> "{esc(dst)}";')

    lines.append("}")
    return "\n".join(lines) + "\n"


def _dot_node_attrs(*, role: str, layer: str, hub_class: str, in_degree: int) -> dict[str, str]:
    layer_colors = {
        "primitive": "#f9d65c",
        "foundational": "#f9d65c",
        "first-order": "#8ecae6",
        "mechanism": "#90be6d",
        "accounting": "#f4a261",
        "failure-state": "#e76f51",
        "selector": "#b5179e",
        "meta-analytical": "#b5179e",
        "unknown": "#9aa0a6",
    }

    fill = layer_colors.get(layer, layer_colors["unknown"])
    shape = "ellipse"
    border = "#3a4154"
    penwidth = 1.0

    if hub_class.lower().startswith("primitive hub"):
        shape = "doublecircle"
        penwidth = 2.2
        border = "#e6e6e6"
    elif hub_class.lower().startswith("aggregation hub"):
        shape = "box"
        penwidth = 2.0
        border = "#e6e6e6"
    elif hub_class.lower().startswith("mechanism-output hub"):
        shape = "octagon"
        penwidth = 2.0
        border = "#e6e6e6"

    if role != "concept":
        fill = "#1b1f2a"

    fontsize = str(10 + min(8, max(0, in_degree)))

    return {
        "shape": shape,
        "fillcolor": fill,
        "color": border,
        "penwidth": f"{penwidth:.1f}",
        "fontsize": fontsize,
    }


def _to_svg(g: LinkGraph, *, title: str, node_meta: dict[str, dict] | None = None) -> str:
    """Render a lightweight SVG with a deterministic layered layout (no external deps)."""

    # Layer order -> x coordinate (concept graphs); all-notes fall back to a single column.
    layer_order = [
        "foundational",
        "primitive",
        "first-order",
        "mechanism",
        "accounting",
        "failure-state",
        "selector",
        "meta-analytical",
        "unknown",
    ]
    layer_x = {layer: i for i, layer in enumerate(layer_order)}

    def get_layer(name: str) -> str:
        if not node_meta:
            return "unknown"
        return (node_meta.get(name, {}).get("layer") or "unknown").strip().lower()

    def get_role(name: str) -> str:
        if not node_meta:
            return "unknown"
        return (node_meta.get(name, {}).get("role") or "unknown").strip().lower()

    def get_hub(name: str) -> str:
        if not node_meta:
            return ""
        return (node_meta.get(name, {}).get("hub_class") or "").strip()

    layer_colors = {
        "primitive": "#f9d65c",
        "foundational": "#f9d65c",
        "first-order": "#8ecae6",
        "mechanism": "#90be6d",
        "accounting": "#f4a261",
        "failure-state": "#e76f51",
        "selector": "#b5179e",
        "meta-analytical": "#b5179e",
        "unknown": "#9aa0a6",
    }

    bg = "#0f1115"
    edge_color = "#3a4154"
    text_color = "#e6e6e6"
    border_default = "#3a4154"
    border_hub = "#e6e6e6"

    nodes = sorted(g.nodes)
    # Group nodes by layer (concepts), else by role.
    groups: dict[str, list[str]] = {}
    for n in nodes:
        key = get_layer(n) if get_role(n) == "concept" else get_role(n)
        groups.setdefault(key, []).append(n)

    # Layout constants
    col_w = 220
    row_h = 56
    margin_x = 40
    margin_y = 70

    # Compute column order
    ordered_cols = sorted(
        groups.keys(),
        key=lambda k: (layer_x.get(k, 999), k),
    )

    positions: dict[str, tuple[float, float]] = {}
    max_rows = max((len(groups[c]) for c in ordered_cols), default=0)
    width = margin_x * 2 + col_w * max(1, len(ordered_cols))
    height = margin_y * 2 + row_h * max(6, max_rows)

    for col_idx, col in enumerate(ordered_cols):
        xs = margin_x + col_idx * col_w + col_w / 2
        for row_idx, n in enumerate(sorted(groups[col])):
            ys = margin_y + row_idx * row_h + row_h / 2
            positions[n] = (xs, ys)

    def node_radius(n: str) -> float:
        base = 14.0
        return base + min(14.0, float(g.in_degree(n)) * 1.0)

    # SVG helpers
    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    def bezier(x1: float, y1: float, x2: float, y2: float) -> str:
        dx = x2 - x1
        ctrl = max(40.0, abs(dx) * 0.35)
        c1x = x1 + ctrl
        c1y = y1
        c2x = x2 - ctrl
        c2y = y2
        return f"M {x1:.1f},{y1:.1f} C {c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {x2:.1f},{y2:.1f}"

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" style="background:{bg}">'
    )
    parts.append(
        f'<text x="{margin_x}" y="{margin_y - 28}" fill="{text_color}" font-family="Helvetica" font-size="16">{esc(title)}</text>'
    )

    # Legend
    lx = margin_x
    ly = height - 22
    legend_items = [("primitive", "Primitives"), ("first-order", "First-order"), ("mechanism", "Mechanisms"), ("accounting", "Accounting"), ("failure-state", "Failure"), ("selector", "Diagnostic")]
    dx = 140
    for i, (layer, label) in enumerate(legend_items):
        x = lx + i * dx
        c = layer_colors.get(layer, layer_colors["unknown"])
        parts.append(f'<rect x="{x}" y="{ly - 10}" width="10" height="10" fill="{c}" stroke="{border_default}"/>')
        parts.append(f'<text x="{x + 14}" y="{ly}" fill="{text_color}" font-family="Helvetica" font-size="11">{esc(label)}</text>')

    # Edges first (under nodes)
    parts.append('<g id="edges" stroke-linecap="round" fill="none">')
    for src, dsts in sorted(g.edges.items()):
        for dst in sorted(dsts):
            if src not in positions or dst not in positions:
                continue
            x1, y1 = positions[src]
            x2, y2 = positions[dst]
            # Slight vertical jitter to reduce overlap deterministically
            jitter = (hash((src, dst)) % 9 - 4) * 1.5
            path_d = bezier(x1 + node_radius(src), y1 + jitter, x2 - node_radius(dst), y2 - jitter)
            parts.append(f'<path d="{path_d}" stroke="{edge_color}" stroke-width="1.0" opacity="0.8"/>')
    parts.append("</g>")

    # Nodes
    parts.append('<g id="nodes">')
    for n in nodes:
        if n not in positions:
            continue
        x, y = positions[n]
        role = get_role(n)
        layer = get_layer(n) if role == "concept" else "unknown"
        hub = get_hub(n)
        r = node_radius(n)

        fill = layer_colors.get(layer, layer_colors["unknown"]) if role == "concept" else "#1b1f2a"
        stroke = border_hub if hub else border_default
        sw = 2.2 if hub else 1.0

        # hub shapes
        if hub.lower().startswith("primitive hub"):
            # double ring
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{(r-5):.1f}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>')
        elif hub.lower().startswith("aggregation hub"):
            w = r * 2.2
            h = r * 1.6
            parts.append(f'<rect x="{(x-w/2):.1f}" y="{(y-h/2):.1f}" width="{w:.1f}" height="{h:.1f}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        elif hub.lower().startswith("mechanism-output hub"):
            # octagon
            s = r * 1.2
            pts = []
            for k in range(8):
                ang = math.pi / 4 * k + math.pi / 8
                px = x + s * math.cos(ang)
                py = y + s * math.sin(ang)
                pts.append(f"{px:.1f},{py:.1f}")
            parts.append(f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        else:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

        label = n + (f" (hub: {hub})" if hub else "")
        parts.append(
            f'<text x="{x:.1f}" y="{(y + r + 14):.1f}" fill="{text_color}" font-family="Helvetica" '
            f'font-size="11" text-anchor="middle">{esc(label)}</text>'
        )

    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _wrap_html(svg: str, *, title: str) -> str:
    """Wrap SVG in a standalone HTML page with basic pan/zoom (no external deps)."""
    t = html.escape(title, quote=True)
    return (
        "<!doctype html>\n"
        "<html>\n"
        "<head>\n"
        f"  <meta charset=\"utf-8\" />\n  <title>{t}</title>\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "  <style>\n"
        "    html, body { height: 100%; }\n"
        "    body { margin: 0; background: #0f1115; color: #e6e6e6; font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }\n"
        "    .wrap { padding: 12px; height: 100vh; box-sizing: border-box; display: flex; flex-direction: column; }\n"
        "    .toolbar { display: flex; gap: 8px; align-items: center; margin: 0 0 10px 0; }\n"
        "    .btn { background: #1b1f2a; color: #e6e6e6; border: 1px solid #3a4154; border-radius: 8px; padding: 6px 10px; cursor: pointer; }\n"
        "    .btn:hover { border-color: #5b6782; }\n"
        "    .hint { color: #9aa4b2; font-size: 12px; }\n"
        "    .viewport { border: 1px solid #3a4154; border-radius: 10px; overflow: hidden; flex: 1; min-height: 0; }\n"
        "    svg { width: 100%; height: 100%; display: block; touch-action: none; user-select: none; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"wrap\">\n"
        "    <div class=\"toolbar\">\n"
        "      <button class=\"btn\" id=\"resetBtn\" type=\"button\">Reset</button>\n"
        "      <button class=\"btn\" id=\"zoomInBtn\" type=\"button\">Zoom +</button>\n"
        "      <button class=\"btn\" id=\"zoomOutBtn\" type=\"button\">Zoom -</button>\n"
        "      <span class=\"hint\">Drag to pan • Scroll to zoom</span>\n"
        "    </div>\n"
        "    <div class=\"viewport\" id=\"viewport\">\n"
        f"{svg}\n"
        "    </div>\n"
        "  </div>\n"
        "  <script>\n"
        "    (function () {\n"
        "      const viewportEl = document.getElementById('viewport');\n"
        "      const svg = viewportEl.querySelector('svg');\n"
        "      if (!svg) return;\n"
        "      if (!svg.getAttribute('viewBox')) {\n"
        "        const w = svg.getAttribute('width') || 1000;\n"
        "        const h = svg.getAttribute('height') || 800;\n"
        "        svg.setAttribute('viewBox', `0 0 ${w} ${h}`);\n"
        "      }\n"
        "\n"
        "      const vb = svg.viewBox.baseVal;\n"
        "      const initial = { x: vb.x, y: vb.y, width: vb.width, height: vb.height };\n"
        "\n"
        "      const clamp = (v, min, max) => Math.max(min, Math.min(max, v));\n"
        "      const zoomAt = (clientX, clientY, factor) => {\n"
        "        const rect = svg.getBoundingClientRect();\n"
        "        const px = (clientX - rect.left) / rect.width;\n"
        "        const py = (clientY - rect.top) / rect.height;\n"
        "\n"
        "        const newW = vb.width / factor;\n"
        "        const newH = vb.height / factor;\n"
        "\n"
        "        const dx = (vb.width - newW) * px;\n"
        "        const dy = (vb.height - newH) * py;\n"
        "\n"
        "        vb.x += dx;\n"
        "        vb.y += dy;\n"
        "        vb.width = newW;\n"
        "        vb.height = newH;\n"
        "      };\n"
        "\n"
        "      let isPanning = false;\n"
        "      let start = { x: 0, y: 0, vbX: 0, vbY: 0 };\n"
        "\n"
        "      svg.addEventListener('pointerdown', (e) => {\n"
        "        isPanning = true;\n"
        "        svg.setPointerCapture(e.pointerId);\n"
        "        start = { x: e.clientX, y: e.clientY, vbX: vb.x, vbY: vb.y };\n"
        "      });\n"
        "      svg.addEventListener('pointerup', () => { isPanning = false; });\n"
        "      svg.addEventListener('pointercancel', () => { isPanning = false; });\n"
        "      svg.addEventListener('pointermove', (e) => {\n"
        "        if (!isPanning) return;\n"
        "        const rect = svg.getBoundingClientRect();\n"
        "        const dx = (e.clientX - start.x) * (vb.width / rect.width);\n"
        "        const dy = (e.clientY - start.y) * (vb.height / rect.height);\n"
        "        vb.x = start.vbX - dx;\n"
        "        vb.y = start.vbY - dy;\n"
        "      });\n"
        "\n"
        "      svg.addEventListener('wheel', (e) => {\n"
        "        e.preventDefault();\n"
        "        const direction = e.deltaY > 0 ? -1 : 1;\n"
        "        const factor = direction > 0 ? 1.15 : 1 / 1.15;\n"
        "\n"
        "        const minW = initial.width * 0.08;\n"
        "        const maxW = initial.width * 3.5;\n"
        "        const beforeW = vb.width;\n"
        "        zoomAt(e.clientX, e.clientY, factor);\n"
        "        vb.width = clamp(vb.width, minW, maxW);\n"
        "        vb.height = vb.width * (initial.height / initial.width);\n"
        "        // If clamped, keep center stable-ish.\n"
        "        if (vb.width !== beforeW / factor) {\n"
        "          const cx = vb.x + vb.width / 2;\n"
        "          const cy = vb.y + vb.height / 2;\n"
        "          vb.x = cx - vb.width / 2;\n"
        "          vb.y = cy - vb.height / 2;\n"
        "        }\n"
        "      }, { passive: false });\n"
        "\n"
        "      const reset = () => {\n"
        "        vb.x = initial.x;\n"
        "        vb.y = initial.y;\n"
        "        vb.width = initial.width;\n"
        "        vb.height = initial.height;\n"
        "      };\n"
        "      document.getElementById('resetBtn')?.addEventListener('click', reset);\n"
        "      document.getElementById('zoomInBtn')?.addEventListener('click', () => zoomAt(window.innerWidth / 2, 140, 1.2));\n"
        "      document.getElementById('zoomOutBtn')?.addEventListener('click', () => zoomAt(window.innerWidth / 2, 140, 1 / 1.2));\n"
        "    })();\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )
