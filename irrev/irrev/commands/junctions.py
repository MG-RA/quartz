"""Junctions command group - detect routing pressure and missing concepts.

Phase 1 focuses on an inside-out concept audit: surface load-bearing concepts and
definition hygiene issues from the existing concept graph.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault


@dataclass(frozen=True)
class ConceptAuditItem:
    name: str
    title: str
    layer: str
    in_degree: int
    out_degree: int
    hub_class: str
    has_definition: bool
    has_structural_dependencies: bool
    has_what_not: bool
    role_purity_flags: list[str]
    deps: list[str]
    deps_only_in_deps_section: list[str]


def run_concept_audit(
    vault_path: Path,
    *,
    out: Path | None = None,
    top: int = 25,
    fmt: str = "md",
    include_all: bool = False,
) -> int:
    """Generate a concept audit report (Phase 1).

    Args:
        vault_path: Path to vault content directory (e.g., ./content)
        out: Optional output file path; prints to stdout if None
        top: Number of top in-degree concepts to include (unless include_all)
        fmt: md|json
        include_all: If true, audit all concepts (not just top list)
    """
    console = Console(stderr=True)

    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)
    hub_class_by_concept = _load_hub_classes(vault_path)

    concepts = _select_concepts_for_audit(graph, hub_class_by_concept, top=top, include_all=include_all)
    items = [_audit_concept(graph, name, hub_class_by_concept.get(name, "")) for name in concepts]

    payload = {
        "title": "Concept audit (inside-out)",
        "vault": str(vault_path),
        "top": top,
        "include_all": include_all,
        "concept_count": len(graph.nodes),
        "audited_count": len(items),
        "items": [item.__dict__ for item in items],
    }

    if fmt == "json":
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    else:
        text = _to_markdown(payload)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        console.print(f"Wrote concept audit to {out}", style="green")
    else:
        print(text, end="" if text.endswith("\n") else "\n")

    return 0


def _select_concepts_for_audit(
    graph: DependencyGraph,
    hub_class_by_concept: dict[str, str],
    *,
    top: int,
    include_all: bool,
) -> list[str]:
    if include_all:
        return sorted(graph.nodes.keys())

    # Always include hubs.yml concepts, plus top in-degree nodes.
    hub_names = sorted(hub_class_by_concept.keys())

    ranked = sorted(
        graph.nodes.keys(),
        key=lambda n: (len(graph.reverse_edges.get(n, set())), n),
        reverse=True,
    )
    top_names = ranked[: max(0, top)]

    seen: set[str] = set()
    out: list[str] = []
    for name in hub_names + top_names:
        if name not in graph.nodes:
            continue
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _audit_concept(graph: DependencyGraph, name: str, hub_class: str) -> ConceptAuditItem:
    concept = graph.nodes[name]
    content = concept.content
    lowered = content.lower()

    has_definition = "\n## definition" in ("\n" + lowered)
    has_structural_deps = "\n## structural dependencies" in ("\n" + lowered)
    has_what_not = "\n## what this is not" in ("\n" + lowered)

    role_purity_flags: list[str] = []
    suspicious_headings = ("## operation", "## procedure", "## checklist", "## how to use", "## steps")
    for h in suspicious_headings:
        if h in lowered:
            role_purity_flags.append(f"Contains operator-like section heading: {h.strip('# ').title()}")
            break
    if "you should" in lowered or "do not" in lowered:
        role_purity_flags.append("Contains prescriptive language (possible operator/policy bleed)")

    deps = [graph.normalize(d) for d in concept.depends_on]
    deps_only_in_deps_section = _deps_only_in_deps_section(content, deps)

    return ConceptAuditItem(
        name=name,
        title=concept.title,
        layer=(concept.layer or "unknown"),
        in_degree=len(graph.reverse_edges.get(name, set())),
        out_degree=len(graph.edges.get(name, set())),
        hub_class=hub_class,
        has_definition=has_definition,
        has_structural_dependencies=has_structural_deps,
        has_what_not=has_what_not,
        role_purity_flags=role_purity_flags,
        deps=deps,
        deps_only_in_deps_section=deps_only_in_deps_section,
    )


def _deps_only_in_deps_section(content: str, deps: list[str]) -> list[str]:
    """Return deps that appear only in the Structural dependencies section."""
    if not deps:
        return []

    # Split into "deps section" and "rest of document" by heading boundaries.
    lowered = content.lower()
    marker = "## structural dependencies"
    idx = lowered.find(marker)
    deps_section = ""
    rest = content
    if idx != -1:
        end = lowered.find("\n## ", idx + len(marker))
        if end == -1:
            end = len(content)
        deps_section = content[idx:end]
        rest = content[:idx] + content[end:]

    only: list[str] = []
    for d in deps:
        needle = f"[[{d}]]".lower()
        in_deps = needle in deps_section.lower()
        in_rest = needle in rest.lower()
        if in_deps and not in_rest:
            only.append(d)
    return only


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


def _to_markdown(payload: dict) -> str:
    items = [ConceptAuditItem(**d) for d in payload["items"]]

    def yesno(v: bool) -> str:
        return "yes" if v else "no"

    lines: list[str] = []
    lines.append(f"# {payload['title']}")
    lines.append("")
    lines.append(f"- Vault: `{payload['vault']}`")
    lines.append(f"- Concepts: {payload['concept_count']}")
    lines.append(f"- Audited: {payload['audited_count']}")
    lines.append("")
    lines.append("## Top candidates")
    lines.append("")
    lines.append("| Concept | Layer | In-degree | Hub class |")
    lines.append("|---|---:|---:|---|")
    for it in sorted(items, key=lambda x: (x.in_degree, x.name), reverse=True):
        hub = it.hub_class or ""
        lines.append(f"| [[{it.name}]] | {it.layer} | {it.in_degree} | {hub} |")

    lines.append("")
    lines.append("## Audit details")
    lines.append("")
    for it in sorted(items, key=lambda x: (x.in_degree, x.name), reverse=True):
        lines.append(f"### {it.title} (`{it.name}`)")
        lines.append("")
        lines.append(f"- Layer: `{it.layer}`")
        lines.append(f"- In-degree: `{it.in_degree}`  Out-degree: `{it.out_degree}`")
        if it.hub_class:
            lines.append(f"- Hub class: `{it.hub_class}`")
        lines.append(f"- Has `## Definition`: {yesno(it.has_definition)}")
        lines.append(f"- Has `## Structural dependencies`: {yesno(it.has_structural_dependencies)}")
        lines.append(f"- Has `## What this is NOT`: {yesno(it.has_what_not)}")
        if it.role_purity_flags:
            for f in it.role_purity_flags:
                lines.append(f"- Role purity flag: {f}")
        if it.deps:
            lines.append(f"- Declared deps: {', '.join(f'[[{d}]]' for d in it.deps)}")
        if it.deps_only_in_deps_section:
            lines.append(
                "- Dependency fidelity note: these deps appear only in the Structural dependencies section: "
                + ", ".join(f"[[{d}]]" for d in it.deps_only_in_deps_section)
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
