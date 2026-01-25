from pathlib import Path

from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import load_vault
from irrev.vault.rules import LintRules


def test_broken_link_allows_existing_svg_asset(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    (vault / "concepts").mkdir(parents=True)
    (vault / "meta" / "graphs").mkdir(parents=True)

    (vault / "meta" / "graphs" / "a.svg").write_text("<svg></svg>\n", encoding="utf-8")
    (vault / "meta" / "note.md").write_text(
        "\n".join(
            [
                "---",
                "role: meta",
                "canonical: false",
                "---",
                "",
                "# Graph Note",
                "",
                "![[meta/graphs/a.svg]]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (vault / "concepts" / "thing.md").write_text(
        "\n".join(
            [
                "---",
                "role: concept",
                "layer: primitive",
                "canonical: true",
                "---",
                "",
                "# thing",
                "",
                "## Definition",
                "",
                "Definition text.",
                "",
                "## Structural dependencies",
                "- None",
                "",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)
    results = LintRules(loaded, graph).check_broken_links()

    assert results == []

