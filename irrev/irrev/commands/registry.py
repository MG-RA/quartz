"""Registry command implementation - generate registry skeletons."""

import difflib
from pathlib import Path

from rich.console import Console
from rich.syntax import Syntax

from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault


# Layer ordering for registry output
LAYER_ORDER = [
    ("Primitives", ["primitive", "foundational"]),
    ("First-order composites", ["first-order"]),
    ("Accounting", ["accounting"]),
    ("Failure states", ["failure-state"]),
    ("Diagnostic apparatus", ["selector", "meta-analytical"]),
]


def run_build(vault_path: Path, out: str | None = None) -> int:
    """Build registry from vault concepts.

    Args:
        vault_path: Path to vault content directory
        out: Output file path (None = stdout)

    Returns:
        Exit code
    """
    console = Console(stderr=True)

    # Load vault
    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    # Generate registry content
    content = _generate_registry(vault, graph)

    if out:
        out_path = Path(out)
        out_path.write_text(content, encoding="utf-8")
        console.print(f"Registry written to {out_path}", style="green")
    else:
        print(content)

    return 0


def run_diff(vault_path: Path) -> int:
    """Compare generated registry with existing Registry file.

    Args:
        vault_path: Path to vault content directory

    Returns:
        Exit code (0 = no diff, 1 = differences found)
    """
    console = Console(stderr=True)

    # Load vault
    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    # Find existing registry
    existing_registry = None
    for paper in vault.papers:
        if "registry" in paper.name.lower():
            existing_registry = paper
            break

    if not existing_registry:
        console.print("No existing registry found", style="yellow")
        return 1

    # Generate new registry
    generated = _generate_registry(vault, graph)

    # Extract dependency tables from existing registry
    existing_tables = _extract_dependency_tables(existing_registry.content)
    generated_tables = _extract_dependency_tables(generated)

    # Compare
    diff = list(
        difflib.unified_diff(
            existing_tables.splitlines(keepends=True),
            generated_tables.splitlines(keepends=True),
            fromfile="existing",
            tofile="generated",
            lineterm="",
        )
    )

    if diff:
        console.print("Differences found:", style="yellow")
        diff_text = "".join(diff)
        syntax = Syntax(diff_text, "diff", theme="monokai")
        console.print(syntax)
        return 1
    else:
        console.print("Registry is in sync with concepts", style="green")
        return 0


def _generate_registry(vault, graph: DependencyGraph) -> str:
    """Generate registry markdown content."""
    lines = []
    lines.append("<!-- GENERATED: Dependency tables below are generated from /concepts -->")
    lines.append("")
    lines.append("## Dependency classes (by layer)")
    lines.append("")

    # Group concepts by layer
    by_layer = {}
    for concept in vault.concepts:
        layer = concept.layer
        if layer not in by_layer:
            by_layer[layer] = []
        by_layer[layer].append(concept)

    # Output tables by layer order
    for section_name, layer_keys in LAYER_ORDER:
        concepts_in_section = []
        for layer_key in layer_keys:
            concepts_in_section.extend(by_layer.get(layer_key, []))

        if not concepts_in_section:
            continue

        lines.append(f"### Concepts :: {section_name}")
        lines.append("")
        lines.append("| Concept | Role | Depends On |")
        lines.append("|---|---|---|")

        # Sort by name
        concepts_in_section.sort(key=lambda c: c.name.lower())

        for concept in concepts_in_section:
            name = f"[[{concept.name}]]"

            # Get role from structural role section or title
            role = _extract_role(concept)

            # Format dependencies
            if not concept.depends_on:
                if concept.layer in ["primitive", "foundational"]:
                    deps = "None (primitive)" if concept.layer == "primitive" else "None (axiomatic)"
                else:
                    deps = "None"
            else:
                deps = ", ".join(f"[[{d}]]" for d in sorted(concept.depends_on))

            lines.append(f"| {name} | {role} | {deps} |")

        lines.append("")

    lines.append("<!-- END GENERATED -->")
    return "\n".join(lines)


def _extract_role(concept) -> str:
    """Extract role description from concept."""
    # Try to get from first sentence of definition
    content = concept.content

    # Find Definition section
    if "## Definition" in content:
        start = content.index("## Definition") + len("## Definition")
        end = content.find("##", start)
        if end == -1:
            end = len(content)
        definition = content[start:end].strip()

        # Get first sentence
        for delim in [".", "\n\n"]:
            if delim in definition:
                first = definition.split(delim)[0].strip()
                # Clean up
                first = first.replace("**", "").replace("*", "")
                if len(first) < 100:
                    return first.lower()
                break

    return concept.name.replace("-", " ")


def _extract_dependency_tables(content: str) -> str:
    """Extract just the dependency table sections from content."""
    lines = []
    in_table_section = False

    for line in content.split("\n"):
        if "### Concepts ::" in line:
            in_table_section = True
        elif line.startswith("## ") and "Concepts" not in line:
            in_table_section = False

        if in_table_section:
            lines.append(line)

    return "\n".join(lines)
