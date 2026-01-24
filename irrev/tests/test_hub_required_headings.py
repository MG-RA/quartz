from pathlib import Path

from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import load_vault
from irrev.vault.rules import LintRules


def test_hub_required_headings_rule(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)
    (vault / "meta").mkdir(parents=True)

    # Hub policy requires a custom heading.
    (vault / "meta" / "hubs.yml").write_text(
        "\n".join(
            [
                "hubs:",
                "  hub:",
                "    class: Test hub",
                "    required_headings:",
                "      - \"## Required\"",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Concept exists but lacks the heading.
    (vault / "concepts" / "hub.md").write_text(
        "\n".join(
            [
                "---",
                "layer: first-order",
                "role: concept",
                "canonical: true",
                "---",
                "",
                "# Hub",
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

    rules = LintRules(loaded, graph)
    results = rules.check_hub_required_headings()

    assert len(results) == 1
    assert results[0].rule == "hub-required-headings"
    assert results[0].level == "error"
    assert "## Required" in results[0].message

