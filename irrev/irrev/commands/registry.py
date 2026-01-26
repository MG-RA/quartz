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
    ("Mechanisms", ["mechanism"]),
    ("Accounting", ["accounting"]),
    ("Failure states", ["failure-state"]),
    ("Diagnostic apparatus", ["selector", "meta-analytical"]),
]

START_MARKER = "<!-- GENERATED: Dependency tables below are generated from /concepts -->"
END_MARKER = "<!-- END GENERATED -->"


# -----------------------------------------------------------------------------
# Decomposition-compliant pattern: compute (diagnostic) / execute (action)
# -----------------------------------------------------------------------------


def compute_registry_plan(
    vault_path: Path,
    in_place: bool = False,
    overrides: Path | None = None,
    allow_unknown_layers: bool = False,
    registry_path: Path | None = None,
) -> "RegistryBuildPlan":
    """
    Compute what the registry build would produce without writing.

    This is the diagnostic phase - pure computation, no side effects.
    """
    from irrev.planning import RegistryBuildPlan

    console = Console(stderr=True)

    # Load vault
    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    overrides_data = _load_overrides(overrides, console)

    # Generate registry tables
    tables = _generate_dependency_tables(
        vault,
        graph,
        overrides_data=overrides_data,
        allow_unknown_layers=allow_unknown_layers,
    )

    target_path = None
    existing_content = ""
    updated_content = ""

    if in_place:
        target_path = registry_path or _find_registry_path(vault, console)
        if target_path:
            existing_content = target_path.read_text(encoding="utf-8")
            updated_content = _upsert_generated_region(existing_content, tables)

    return RegistryBuildPlan(
        vault_path=vault_path,
        in_place=in_place,
        target_path=target_path,
        tables_content=tables,
        existing_content=existing_content,
        updated_content=updated_content,
    )


def execute_registry_plan(
    plan: "RegistryBuildPlan",
    out: str | None = None,
    console: Console | None = None,
) -> "RegistryBuildResult":
    """
    Execute a registry build plan.

    This is the action phase - performs writes and returns result.
    """
    from irrev.planning import RegistryBuildResult
    from irrev.audit_log import ErasureCost, CreationSummary

    console = console or Console(stderr=True)

    if plan.in_place:
        if not plan.target_path:
            return RegistryBuildResult(success=False, error="No registry path found for in-place update")

        existing_len = len(plan.existing_content.encode("utf-8"))
        updated_len = len(plan.updated_content.encode("utf-8"))
        plan.target_path.write_text(plan.updated_content, encoding="utf-8")

        return RegistryBuildResult(
            erased=ErasureCost(files=1, bytes_erased=existing_len),
            created=CreationSummary(files=1, bytes_written=updated_len),
            success=True,
            output_path=plan.target_path,
        )

    # Generate standalone registry content
    content = _wrap_registry_document(plan.tables_content)

    if out:
        out_path = Path(out)
        out_path.write_text(content, encoding="utf-8")
        return RegistryBuildResult(
            created=CreationSummary(files=1, bytes_written=len(content.encode("utf-8"))),
            success=True,
            output_path=out_path,
        )
    else:
        print(content)
        return RegistryBuildResult(success=True)


def run_build(
    vault_path: Path,
    out: str | None = None,
    in_place: bool = False,
    overrides: Path | None = None,
    allow_unknown_layers: bool = False,
    registry_path: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Build registry from vault concepts.

    Args:
        vault_path: Path to vault content directory
        out: Output file path (None = stdout)
        in_place: Update an existing registry note in-place (preserves narrative)
        overrides: Optional YAML overrides file for ordering/roles
        allow_unknown_layers: Allow concepts with unknown/unconfigured layers
        registry_path: Optional explicit registry markdown path for in-place updates
        dry_run: If True, show what would be done without writing

    Returns:
        Exit code
    """
    console = Console(stderr=True)

    # Phase 1: Compute (diagnostic) - pure, no side effects
    try:
        plan = compute_registry_plan(
            vault_path,
            in_place=in_place,
            overrides=overrides,
            allow_unknown_layers=allow_unknown_layers,
            registry_path=registry_path,
        )
    except ValueError as e:
        console.print(str(e), style="yellow")
        return 1

    # Dry-run mode: show plan and exit
    if dry_run:
        console.print("\n[bold]DRY RUN[/bold] - No changes will be made\n")
        console.print(plan.summary())
        if in_place and plan.updated_content:
            console.print("\n[dim]Preview of generated tables:[/dim]")
            console.print(plan.tables_content[:500] + "..." if len(plan.tables_content) > 500 else plan.tables_content)
        return 0

    # Phase 2: Execute (action) - performs writes
    result = execute_registry_plan(plan, out=out, console=console)

    if not result.success:
        console.print(str(result.error), style="red")
        return 1

    # Audit log for in-place updates
    if in_place and result.output_path:
        from irrev.audit_log import log_operation

        log_operation(
            vault_path,
            operation="registry-in-place",
            erased=result.erased,
            created=result.created,
            metadata={
                "target_path": str(result.output_path),
                "previous_size": result.erased.bytes_erased,
                "new_size": result.created.bytes_written,
            },
        )
        console.print(f"Registry updated in-place at {result.output_path}", style="green")
    elif result.output_path:
        console.print(f"Registry written to {result.output_path}", style="green")

    return 0


def run_diff(
    vault_path: Path,
    overrides: Path | None = None,
    allow_unknown_layers: bool = False,
    registry_path: Path | None = None,
) -> int:
    """Compare generated registry with existing Registry file.

    Args:
        vault_path: Path to vault content directory
        overrides: Optional YAML overrides file for ordering/roles
        allow_unknown_layers: Allow concepts with unknown/unconfigured layers
        registry_path: Optional explicit registry markdown path

    Returns:
        Exit code (0 = no diff, 1 = differences found)
    """
    console = Console(stderr=True)

    # Load vault
    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    # Find existing registry
    existing_registry_path = registry_path or _find_registry_path(vault, console)

    if not existing_registry_path:
        return 1

    existing_content = existing_registry_path.read_text(encoding="utf-8")

    overrides_data = _load_overrides(overrides, console)

    # Generate new registry
    try:
        generated_tables = _generate_dependency_tables(
            vault,
            graph,
            overrides_data=overrides_data,
            allow_unknown_layers=allow_unknown_layers,
        )
    except ValueError as e:
        console.print(str(e), style="yellow")
        return 1

    # Extract dependency tables from existing registry
    existing_tables = _extract_dependency_tables(existing_content)

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


def _wrap_registry_document(tables: str) -> str:
    """Wrap generated tables in a standalone document."""
    lines = [START_MARKER, "", "## Dependency classes (by layer)", "", tables, "", END_MARKER]
    return "\n".join(lines).strip() + "\n"


def _generate_dependency_tables(vault, graph: DependencyGraph, overrides_data: dict, allow_unknown_layers: bool) -> str:
    """Generate the dependency table sections for insertion into a registry note."""
    by_layer: dict[str, list] = {}
    layers_present: set[str] = set()

    for concept in vault.concepts:
        layer = (concept.layer or "unknown").strip().lower()
        layers_present.add(layer)
        by_layer.setdefault(layer, []).append(concept)

    configured_layers = {k for _, keys in LAYER_ORDER for k in keys}
    unknown_layers = sorted(layers_present - configured_layers)
    if unknown_layers and not allow_unknown_layers:
        raise ValueError(
            "Unknown concept layers present (update LAYER_ORDER or pass --allow-unknown-layers): "
            + ", ".join(unknown_layers)
        )

    concept_overrides = {
        str(k).strip().lower(): (v or {}) for k, v in (overrides_data.get("concept_overrides") or {}).items()
    }
    section_orders = {str(k).strip().lower(): (v or []) for k, v in (overrides_data.get("section_orders") or {}).items()}

    lines: list[str] = []

    for section_name, layer_keys in LAYER_ORDER:
        concepts_in_section: list = []
        for layer_key in layer_keys:
            concepts_in_section.extend(by_layer.get(layer_key, []))

        if not concepts_in_section:
            continue

        order_list = section_orders.get(section_name.strip().lower())
        if order_list:
            index = {str(name).strip().lower(): i for i, name in enumerate(order_list)}

            def sort_key(c):
                pos = index.get(c.name.lower())
                return (0, pos) if pos is not None else (1, c.name.lower())

            concepts_in_section.sort(key=sort_key)
        else:
            concepts_in_section.sort(key=lambda c: c.name.lower())

        lines.append(f"### Concepts :: {section_name}")
        lines.append("")
        lines.append("| Concept | Role | Depends On |")
        lines.append("|---|---|---|")

        for concept in concepts_in_section:
            name = f"[[{concept.name}]]"

            override = concept_overrides.get(concept.name.lower(), {})
            role = (override.get("role") or "").strip()
            hub_class = (override.get("hub_class") or "").strip()
            if not role:
                role = _extract_role(concept)
            if hub_class:
                role = f"{role} (hub: {hub_class})"

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

    if unknown_layers and allow_unknown_layers:
        # Not silent: emit as a final section so review catches it.
        for layer in unknown_layers:
            concepts = sorted(by_layer.get(layer, []), key=lambda c: c.name.lower())
            if not concepts:
                continue
            lines.append(f"### Concepts :: Unclassified ({layer})")
            lines.append("")
            lines.append("| Concept | Role | Depends On |")
            lines.append("|---|---|---|")
            for concept in concepts:
                name = f"[[{concept.name}]]"
                role = _extract_role(concept)
                deps = ", ".join(f"[[{d}]]" for d in sorted(concept.depends_on)) if concept.depends_on else "None"
                lines.append(f"| {name} | {role} | {deps} |")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def _extract_role(concept) -> str:
    """Extract role description from concept."""
    # Prefer explicit frontmatter fields.
    fm = getattr(concept, "frontmatter", {}) or {}
    for key in ("description", "summary", "blurb"):
        val = fm.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().lower()

    content = concept.content or ""

    # Prefer first paragraph under Definition/Summary.
    for heading in ("## Definition", "## Summary"):
        paragraph = _first_paragraph_under_heading(content, heading)
        if paragraph:
            cleaned = _strip_md(paragraph).strip()
            if cleaned:
                sentence = cleaned.split(".")[0].strip()
                if 0 < len(sentence) <= 140:
                    return sentence.lower()
                if len(cleaned) <= 140:
                    return cleaned.lower()
                return cleaned[:137].rstrip() + "…"

    # Fallback: first non-heading paragraph in body.
    paragraph = _first_body_paragraph(content)
    if paragraph:
        cleaned = _strip_md(paragraph).strip()
        if cleaned:
            return (cleaned[:137].rstrip() + "…") if len(cleaned) > 140 else cleaned.lower()

    return concept.name.replace("-", " ")


def _strip_md(text: str) -> str:
    return (
        text.replace("**", "")
        .replace("*", "")
        .replace("`", "")
        .replace("[!note]", "")
        .replace("[!warning]", "")
        .replace("[!info]", "")
    )


def _first_paragraph_under_heading(content: str, heading: str) -> str | None:
    if heading not in content:
        return None
    start = content.index(heading) + len(heading)
    end = content.find("\n## ", start)
    if end == -1:
        end = len(content)
    block = content[start:end].strip()
    for para in block.split("\n\n"):
        candidate = para.strip()
        if not candidate:
            continue
        if candidate.startswith(">"):
            continue
        return candidate
    return None


def _first_body_paragraph(content: str) -> str | None:
    lines = content.splitlines()
    paras: list[str] = []
    buf: list[str] = []
    for line in lines:
        if line.strip().startswith("#"):
            continue
        if not line.strip():
            if buf:
                paras.append("\n".join(buf).strip())
                buf = []
            continue
        buf.append(line)
    if buf:
        paras.append("\n".join(buf).strip())
    for para in paras:
        if para and not para.startswith(">"):
            return para
    return None


def _load_overrides(path: Path | None, console: Console) -> dict:
    if not path:
        return {}
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:
        console.print(f"Overrides requested but PyYAML not available: {path}", style="yellow")
        return {}

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data or {}
    except Exception as e:
        console.print(f"Failed to load overrides {path}: {e}", style="yellow")
        return {}


def _find_registry_path(vault, console: Console) -> Path | None:
    """Find a single registry note in the vault papers."""
    registry_notes = [p for p in vault.papers if (p.role or "").strip().lower() == "registry"]
    if not registry_notes:
        registry_notes = [p for p in vault.papers if "registry" in p.name.lower()]

    if not registry_notes:
        console.print("No existing registry found", style="yellow")
        return None

    if len(registry_notes) > 1:
        console.print(
            "Multiple registry candidates found; pass --registry-path to disambiguate:\n"
            + "\n".join(f"- {p.path}" for p in registry_notes),
            style="yellow",
        )
        return None

    return registry_notes[0].path


def _upsert_generated_region(existing: str, tables: str) -> str:
    """Insert or replace the generated tables region in an existing registry note."""
    if START_MARKER in existing and END_MARKER in existing:
        before, rest = existing.split(START_MARKER, 1)
        _, after = rest.split(END_MARKER, 1)
        return before.rstrip() + "\n\n" + START_MARKER + "\n" + tables.rstrip() + "\n" + END_MARKER + after

    # Insert markers around the first Concepts block.
    lines = existing.splitlines()
    first = None
    for i, line in enumerate(lines):
        if line.strip().startswith("### Concepts ::"):
            first = i
            break

    if first is None:
        # No Concepts blocks: append at end.
        return existing.rstrip() + "\n\n" + START_MARKER + "\n" + tables.rstrip() + "\n" + END_MARKER + "\n"

    # Find end of table block: first top-level heading after the concepts region.
    end = len(lines)
    for j in range(first + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break

    new_lines = []
    new_lines.extend(lines[:first])
    if new_lines and new_lines[-1].strip() != "":
        new_lines.append("")
    new_lines.append(START_MARKER)
    new_lines.extend(tables.rstrip().splitlines())
    new_lines.append(END_MARKER)
    new_lines.extend(lines[end:])
    return "\n".join(new_lines).rstrip() + "\n"


def _extract_dependency_tables(content: str) -> str:
    """Extract just the dependency table sections from content."""
    lines = []
    in_table_section = False

    for line in content.split("\n"):
        if line.strip() in (START_MARKER, END_MARKER):
            in_table_section = False
            continue
        if "### Concepts ::" in line:
            in_table_section = True
        elif line.startswith("## ") and "Concepts" not in line:
            in_table_section = False

        if in_table_section:
            lines.append(line)

    return "\n".join(lines).strip() + "\n"
