from pathlib import Path

from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import load_vault
from irrev.vault.rules import LintRules


def _write_mechanism(path: Path, *, with_residuals: bool) -> None:
    residuals = ""
    if with_residuals:
        residuals = "\n".join(
            [
                "## Residuals",
                "",
                "Residual text.",
                "",
            ]
        )

    path.write_text(
        "\n".join(
            [
                "---",
                "layer: mechanism",
                "role: concept",
                "canonical: true",
                "note_kind: operator",
                "---",
                "",
                f"# {path.stem}",
                "",
                "## Definition",
                "",
                "Definition text.",
                "",
                residuals.rstrip(),
                "## Structural dependencies",
                "- None",
                "",
            ]
        ).replace("\n\n\n", "\n\n"),
        encoding="utf-8",
    )


def test_mechanism_missing_residuals_rule(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)

    _write_mechanism(vault / "concepts" / "good-mechanism.md", with_residuals=True)
    _write_mechanism(vault / "concepts" / "bad-mechanism.md", with_residuals=False)

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, loaded._aliases)

    rules = LintRules(loaded, graph)
    results = rules.check_mechanism_missing_residuals()

    assert len(results) == 1
    assert results[0].rule == "mechanism-missing-residuals"
    assert results[0].level == "error"
    assert results[0].file.name == "bad-mechanism.md"

