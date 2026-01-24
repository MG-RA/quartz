from pathlib import Path

from irrev.commands.hubs import compute_hub_candidates
from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import load_vault


def _write_concept(path: Path, *, layer: str, deps: list[str] | None = None) -> None:
    deps = deps or []
    deps_lines = "\n".join(f"- [[{d}]]" for d in deps) if deps else "- None"
    path.write_text(
        "\n".join(
            [
                "---",
                f"layer: {layer}",
                "role: concept",
                "canonical: true",
                "---",
                "",
                f"# {path.stem}",
                "",
                "## Definition",
                "",
                "Definition text.",
                "",
                "## Structural dependencies",
                deps_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_hub_candidate_cross_layer(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)

    # Hub target
    _write_concept(vault / "concepts" / "hub.md", layer="first-order", deps=[])

    # Cross-layer dependents
    _write_concept(vault / "concepts" / "m1.md", layer="mechanism", deps=["hub"])
    _write_concept(vault / "concepts" / "a1.md", layer="accounting", deps=["hub"])
    _write_concept(vault / "concepts" / "f1.md", layer="failure-state", deps=["hub"])

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)

    candidates = compute_hub_candidates(
        graph,
        top=10,
        min_mechanisms=1,
        min_accounting=1,
        min_failure_states=1,
        candidates_only=True,
        exclude_layers={"mechanism", "failure-state"},
        rank="legacy",
    )

    hub = next(c for c in candidates if c.name == "hub")
    assert hub.mechanism_dependents == 1
    assert hub.accounting_dependents == 1
    assert hub.failure_state_dependents == 1
    assert hub.hub_class in {"Cross-layer hub", "Hub-adjacent", "Mechanism-output hub"}


def test_hub_counts_other_dependents(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)
    (vault / "projections").mkdir(parents=True)

    _write_concept(vault / "concepts" / "hub.md", layer="first-order", deps=[])
    _write_concept(vault / "concepts" / "m1.md", layer="mechanism", deps=["hub"])
    _write_concept(vault / "concepts" / "a1.md", layer="accounting", deps=["hub"])
    _write_concept(vault / "concepts" / "f1.md", layer="failure-state", deps=["hub"])

    # A non-concept note linking to hub should count as "other" when supplied via dependents_by_node.
    (vault / "projections" / "p1.md").write_text(
        "\n".join(
            [
                "---",
                "role: projection",
                "canonical: false",
                "---",
                "",
                "# P1",
                "",
                "Links [[hub]].",
                "",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)

    dependents_by_node = {
        "hub": {"m1", "a1", "f1", "p1"},
    }

    candidates = compute_hub_candidates(
        graph,
        top=10,
        min_mechanisms=1,
        min_accounting=1,
        min_failure_states=1,
        candidates_only=True,
        exclude_layers={"mechanism", "failure-state"},
        dependents_by_node=dependents_by_node,
        rank="legacy",
    )

    hub = next(c for c in candidates if c.name == "hub")
    assert hub.total_dependents == 4
    assert hub.other_dependents == 1


def test_hub_excludes_mechanism_and_failure_state_by_default(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)

    _write_concept(vault / "concepts" / "mech.md", layer="mechanism", deps=[])
    _write_concept(vault / "concepts" / "fail.md", layer="failure-state", deps=[])
    _write_concept(vault / "concepts" / "x.md", layer="accounting", deps=["mech", "fail"])

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)

    candidates = compute_hub_candidates(
        graph,
        top=10,
        min_mechanisms=0,
        min_accounting=0,
        min_failure_states=0,
        candidates_only=False,
        exclude_layers={"mechanism", "failure-state"},
        rank="legacy",
    )

    names = {c.name for c in candidates}
    assert "mech" not in names
    assert "fail" not in names
