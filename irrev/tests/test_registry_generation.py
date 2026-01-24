from pathlib import Path

import pytest

from irrev.commands.registry import _generate_dependency_tables
from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import load_vault


def _write_concept(path: Path, *, layer: str, deps: list[str] | None = None) -> None:
    deps = deps or []
    deps_lines = "\n".join(f"- [[{d}]]" for d in deps) if deps else "- None (primitive)"
    path.write_text(
        "\n".join(
            [
                "---",
                f"layer: {layer}",
                "role: concept",
                "canonical: true",
                "---",
                "",
                f"# {path.stem.replace('-', ' ').title()}",
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


def test_registry_includes_mechanism_layer(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    (vault / "concepts").mkdir(parents=True)
    (vault / "papers").mkdir(parents=True)

    _write_concept(vault / "concepts" / "transformation-space.md", layer="foundational", deps=[])
    _write_concept(vault / "concepts" / "constraint.md", layer="primitive", deps=[])
    _write_concept(vault / "concepts" / "persistent-difference.md", layer="first-order", deps=["constraint"])
    _write_concept(vault / "concepts" / "rollback.md", layer="mechanism", deps=["persistent-difference"])
    _write_concept(vault / "concepts" / "tracking-mechanism.md", layer="accounting", deps=["persistent-difference"])

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)

    tables = _generate_dependency_tables(loaded, graph, overrides_data={}, allow_unknown_layers=False)
    assert "### Concepts :: Mechanisms" in tables
    assert "| [[rollback]]" in tables


def test_registry_unknown_layer_is_error_by_default(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    (vault / "concepts").mkdir(parents=True)

    _write_concept(vault / "concepts" / "mystery.md", layer="mystery", deps=[])

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)

    with pytest.raises(ValueError):
        _generate_dependency_tables(loaded, graph, overrides_data={}, allow_unknown_layers=False)


def test_registry_unknown_layer_can_be_emitted(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    (vault / "concepts").mkdir(parents=True)

    _write_concept(vault / "concepts" / "mystery.md", layer="mystery", deps=[])

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)

    tables = _generate_dependency_tables(loaded, graph, overrides_data={}, allow_unknown_layers=True)
    assert "### Concepts :: Unclassified (mystery)" in tables
