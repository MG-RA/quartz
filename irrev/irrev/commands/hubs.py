"""Hub detection command - find cross-layer dependency concentrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from ..vault.graph import DependencyGraph
from ..vault.loader import load_vault


@dataclass(frozen=True)
class HubCandidate:
    name: str
    layer: str
    total_dependents: int
    other_dependents: int
    distinct_dependent_layers: int
    mechanism_dependents: int
    accounting_dependents: int
    failure_state_dependents: int
    selector_dependents: int
    hub_class: str
    score: float


def run_hubs(
    vault_path: Path,
    *,
    concepts_only: bool = True,
    top: int = 25,
    min_mechanisms: int = 1,
    min_accounting: int = 1,
    min_failure_states: int = 1,
    candidates_only: bool = True,
    exclude_layers: set[str] | None = None,
    rank: str = "legacy",
    w_mechanism: float = 1.0,
    w_accounting: float = 1.0,
    w_failure: float = 1.0,
    w_selector: float = 1.0,
    w_layers: float = 1.0,
) -> int:
    """Report latent hub candidates based on cross-layer dependency concentration."""
    console = Console(stderr=True)

    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    exclude_layers = {l.strip().lower() for l in (exclude_layers or {"mechanism", "failure-state"})}

    dependents_by_node: dict[str, set[str]] | None = None
    if not concepts_only:
        # Build a concept-targeted reverse index from all-note wiki links.
        dependents_by_node = {}
        for note in vault.all_notes:
            src = note.name.lower()
            for link in note.links:
                dst = vault.normalize_name(link)
                if dst in graph.nodes:
                    dependents_by_node.setdefault(dst, set()).add(src)

    candidates = compute_hub_candidates(
        graph,
        top=top,
        min_mechanisms=min_mechanisms,
        min_accounting=min_accounting,
        min_failure_states=min_failure_states,
        candidates_only=candidates_only,
        exclude_layers=exclude_layers,
        dependents_by_node=dependents_by_node,
        rank=rank,
        w_mechanism=w_mechanism,
        w_accounting=w_accounting,
        w_failure=w_failure,
        w_selector=w_selector,
        w_layers=w_layers,
    )

    if not candidates:
        console.print("No hub candidates found for the given thresholds.", style="yellow")
        return 0

    # Markdown table (stdout) so it can be pasted into notes/PRs.
    print("## Latent hub candidates (cross-layer concentration)\n")
    print(
        "| Concept | Hub class | Layer | Mech refs | Acct refs | Failure refs | Selector refs | Distinct layers |"
        " Total refs | Other refs | Score |"
    )
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for c in candidates:
        print(
            f"| [[{c.name}]] | {c.hub_class} | {c.layer} | {c.mechanism_dependents} | {c.accounting_dependents} |"
            f" {c.failure_state_dependents} | {c.selector_dependents} | {c.distinct_dependent_layers} |"
            f" {c.total_dependents} | {c.other_dependents} | {c.score:.2f} |"
        )

    return 0


def compute_hub_candidates(
    graph: DependencyGraph,
    *,
    top: int,
    min_mechanisms: int,
    min_accounting: int,
    min_failure_states: int,
    candidates_only: bool,
    exclude_layers: set[str],
    dependents_by_node: dict[str, set[str]] | None = None,
    rank: str = "legacy",
    w_mechanism: float = 1.0,
    w_accounting: float = 1.0,
    w_failure: float = 1.0,
    w_selector: float = 1.0,
    w_layers: float = 1.0,
) -> list[HubCandidate]:
    """Compute ranked hub candidates from a concept dependency graph."""
    rows: list[HubCandidate] = []

    def count_by_layer(dependents: set[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for dep in dependents:
            node = graph.nodes.get(dep)
            if not node:
                continue
            layer = (node.layer or "unknown").strip().lower()
            counts[layer] = counts.get(layer, 0) + 1
        return counts

    for name, concept in graph.nodes.items():
        layer = (concept.layer or "unknown").strip().lower()
        if layer in exclude_layers:
            continue

        dependents_all = set((dependents_by_node or {}).get(name, graph.get_dependents(name)))
        concept_dependents = {d for d in dependents_all if d in graph.nodes}
        other_dependents = len(dependents_all) - len(concept_dependents)

        counts = count_by_layer(concept_dependents)

        mech = counts.get("mechanism", 0)
        acct = counts.get("accounting", 0)
        failure = counts.get("failure-state", 0)
        selector = counts.get("selector", 0) + counts.get("meta-analytical", 0)
        distinct_layers = len({(graph.nodes[d].layer or "unknown").strip().lower() for d in concept_dependents})

        hub_class = _classify_hub(
            name=concept.name,
            layer=layer,
            mechanism_dependents=mech,
            accounting_dependents=acct,
            failure_state_dependents=failure,
            selector_dependents=selector,
        )

        score = (
            (w_mechanism * mech)
            + (w_accounting * acct)
            + (w_failure * failure)
            + (w_selector * selector)
            + (w_layers * distinct_layers)
        )

        candidate = HubCandidate(
            name=concept.name,
            layer=layer,
            total_dependents=len(dependents_all),
            other_dependents=other_dependents,
            distinct_dependent_layers=distinct_layers,
            mechanism_dependents=mech,
            accounting_dependents=acct,
            failure_state_dependents=failure,
            selector_dependents=selector,
            hub_class=hub_class,
            score=score,
        )

        if candidates_only:
            if mech < min_mechanisms or acct < min_accounting or failure < min_failure_states:
                continue

        rows.append(candidate)

    if rank == "score":
        rows.sort(
            key=lambda c: (
                c.score,
                c.distinct_dependent_layers,
                c.total_dependents,
                c.mechanism_dependents,
                c.accounting_dependents,
                c.failure_state_dependents,
                c.selector_dependents,
                c.name.lower(),
            ),
            reverse=True,
        )
    else:
        # Rank: cross-layer first, then volume.
        rows.sort(
            key=lambda c: (
                c.mechanism_dependents > 0,
                c.accounting_dependents > 0,
                c.failure_state_dependents > 0,
                c.distinct_dependent_layers,
                c.mechanism_dependents,
                c.accounting_dependents,
                c.failure_state_dependents,
                c.total_dependents,
                c.name.lower(),
            ),
            reverse=True,
        )

    return rows[: max(0, top)]


def _classify_hub(
    *,
    name: str,
    layer: str,
    mechanism_dependents: int,
    accounting_dependents: int,
    failure_state_dependents: int,
    selector_dependents: int,
) -> str:
    """Lightweight labels for teaching/reading hub output.

    This is heuristic and intentionally conservative: it should be readable, not authoritative.
    """
    if layer in {"primitive", "foundational"}:
        return "Primitive hub"

    lowered = name.strip().lower()
    if "load" in lowered or lowered.endswith("-set"):
        return "Aggregation hub"

    if mechanism_dependents >= 2 and (accounting_dependents + failure_state_dependents + selector_dependents) >= 2:
        return "Mechanism-output hub"

    if mechanism_dependents > 0 and accounting_dependents > 0 and failure_state_dependents > 0:
        return "Cross-layer hub"

    return "Hub-adjacent"
