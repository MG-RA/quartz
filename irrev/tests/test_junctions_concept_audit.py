from pathlib import Path

from irrev.commands.junctions import run_concept_audit


def _write_concept(path: Path, *, layer: str, deps: list[str] | None = None, extra: str = "") -> None:
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
                extra,
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_concept_audit_runs_and_outputs_md(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)

    _write_concept(vault / "concepts" / "a.md", layer="primitive", deps=[])
    _write_concept(vault / "concepts" / "b.md", layer="first-order", deps=["a"])
    _write_concept(vault / "concepts" / "c.md", layer="first-order", deps=["a"])

    out = tmp_path / "audit.md"
    code = run_concept_audit(vault, out=out, top=10, fmt="md")
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert "Concept audit" in text
    assert "[[a]]" in text

