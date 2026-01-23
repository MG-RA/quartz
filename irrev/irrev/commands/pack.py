"""Pack command implementation - generate context packs."""

import json
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

from ..vault.graph import DependencyGraph
from ..vault.loader import Vault, load_vault


def run_pack(
    vault_path: Path,
    kind: str,
    target: str,
    output_format: str = "md",
    include_diagnostics: bool = False,
    explain: bool = False,
) -> int:
    """Generate a context pack for a concept, domain, or projection.

    Args:
        vault_path: Path to vault content directory
        kind: Type of pack ("concept", "domain", "projection")
        target: Name of the target note
        output_format: Output format ("md", "json", "txt")
        include_diagnostics: Include diagnostic notes in pack
        explain: Show why each file is included

    Returns:
        Exit code (0 = success, 1 = target not found)
    """
    console = Console(stderr=True)

    # Load vault
    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    # Find target note
    target_note = _find_target(vault, kind, target)
    if not target_note:
        console.print(f"Error: {kind} '{target}' not found", style="bold red")
        return 1

    # Build pack
    pack = _build_pack(vault, graph, target_note, kind, include_diagnostics, explain)

    # Output
    if output_format == "json":
        print(json.dumps(pack, indent=2, default=str))
    elif output_format == "txt":
        _print_txt(pack)
    else:
        _print_md(pack, console)

    return 0


def _find_target(vault: Vault, kind: str, target: str):
    """Find the target note by kind and name."""
    normalized = target.lower()

    if kind == "concept":
        for c in vault.concepts:
            if c.name.lower() == normalized:
                return c
            if normalized in [a.lower() for a in c.aliases]:
                return c
    elif kind == "domain":
        for d in vault.domains:
            if normalized in d.name.lower() or d.name.lower() in normalized:
                return d
    elif kind == "projection":
        for p in vault.projections:
            if normalized in p.name.lower() or p.name.lower() in normalized:
                return p

    # Fallback: try vault.get
    return vault.get(target)


def _build_pack(
    vault: Vault,
    graph: DependencyGraph,
    target,
    kind: str,
    include_diagnostics: bool,
    explain: bool,
) -> dict:
    """Build the context pack dictionary."""
    pack = {
        "kind": kind,
        "target": {
            "name": target.name,
            "path": str(target.path),
            "content": target.content,
        },
        "concepts": [],
        "diagnostics": [],
        "excluded": [],
        "explanations": [] if explain else None,
    }

    # Get concepts to include
    if kind == "concept":
        # Include the concept and all its dependencies
        concept_names = graph.transitive_closure(target.name)
    else:
        # For domain/projection, include all linked concepts and their deps
        concept_names = set()
        for link in target.links:
            normalized = vault.normalize_name(link)
            if normalized in graph.nodes:
                concept_names.update(graph.transitive_closure(normalized))

    # Sort concepts by dependency order
    topo_order = graph.topological_sort()
    sorted_concepts = []
    for name in topo_order:
        if name in concept_names and name in graph.nodes:
            sorted_concepts.append(name)

    # Add remaining concepts not in topo order
    for name in concept_names:
        if name not in sorted_concepts and name in graph.nodes:
            sorted_concepts.append(name)

    # Build concept list
    for name in sorted_concepts:
        concept = graph.nodes.get(name)
        if concept:
            pack["concepts"].append(
                {
                    "name": concept.name,
                    "layer": concept.layer,
                    "path": str(concept.path),
                }
            )

            if explain:
                reason = _explain_inclusion(graph, name, target.name if kind == "concept" else None)
                pack["explanations"].append({"name": name, "reason": reason})

    # Include diagnostics if requested
    if include_diagnostics:
        for diag in vault.diagnostics:
            pack["diagnostics"].append(
                {
                    "name": diag.name,
                    "path": str(diag.path),
                }
            )

    # Note excluded papers
    for paper in vault.papers:
        pack["excluded"].append(
            {
                "name": paper.name,
                "reason": "Papers excluded by rule",
            }
        )

    return pack


def _explain_inclusion(graph: DependencyGraph, name: str, root: str | None) -> str:
    """Generate explanation for why a concept was included."""
    if root and name == root.lower():
        return "Target concept"

    # Find what depends on this concept
    dependents = graph.get_dependents(name)
    if dependents:
        dependent_list = ", ".join(sorted(dependents)[:3])
        if len(dependents) > 3:
            dependent_list += f" and {len(dependents) - 3} more"
        return f"Required by {dependent_list}"

    return "Linked from target"


def _print_md(pack: dict, console: Console) -> None:
    """Print pack as markdown."""
    lines = []
    lines.append(f"# Context Pack: {pack['kind'].title()} - {pack['target']['name']}")
    lines.append("")

    # Concepts
    lines.append("## Concepts (dependency-closed)")
    lines.append("")
    for i, concept in enumerate(pack["concepts"], 1):
        lines.append(f"{i}. [[{concept['name']}]] ({concept['layer']})")
    lines.append("")

    # Diagnostics
    if pack["diagnostics"]:
        lines.append("## Diagnostics")
        lines.append("")
        for diag in pack["diagnostics"]:
            lines.append(f"- [[{diag['name']}]]")
        lines.append("")

    # Target
    lines.append("## Target")
    lines.append("")
    lines.append(f"- [[{pack['target']['name']}]]")
    lines.append("")

    # Excluded
    if pack["excluded"]:
        lines.append("## Excluded")
        lines.append("")
        for item in pack["excluded"]:
            lines.append(f"- {item['name']} ({item['reason']})")
        lines.append("")

    # Explanations
    if pack.get("explanations"):
        lines.append("## Inclusion Explanations")
        lines.append("")
        for exp in pack["explanations"]:
            lines.append(f"- **{exp['name']}**: {exp['reason']}")
        lines.append("")

    md = "\n".join(lines)
    console.print(Markdown(md))


def _print_txt(pack: dict) -> None:
    """Print pack as plain text."""
    print(f"Context Pack: {pack['kind']} - {pack['target']['name']}")
    print()
    print("Concepts:")
    for concept in pack["concepts"]:
        print(f"  - {concept['name']} ({concept['layer']})")
    print()
    if pack["diagnostics"]:
        print("Diagnostics:")
        for diag in pack["diagnostics"]:
            print(f"  - {diag['name']}")
        print()
    print(f"Target: {pack['target']['name']}")
