from pathlib import Path

from irrev.commands.graph_cmd import run_graph


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


def test_graph_dot_includes_layer_and_hub_styling(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    (vault / "concepts").mkdir(parents=True)
    (vault / "meta").mkdir(parents=True)

    (vault / "meta" / "hubs.yml").write_text(
        "\n".join(
            [
                "hubs:",
                "  hub:",
                "    class: Primitive hub",
                "    required_headings: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _write_concept(vault / "concepts" / "hub.md", layer="primitive", deps=[])
    _write_concept(vault / "concepts" / "user.md", layer="first-order", deps=["hub"])

    out = tmp_path / "g.dot"
    run_graph(vault, concepts_only=True, fmt="dot", out=out, styled=True, top=10)

    dot = out.read_text(encoding="utf-8")
    assert "fillcolor" in dot
    assert "hub: Primitive hub" in dot
    assert "shape=\"doublecircle\"" in dot


def test_graph_svg_includes_layer_and_hub_styling(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    (vault / "concepts").mkdir(parents=True)
    (vault / "meta").mkdir(parents=True)

    (vault / "meta" / "hubs.yml").write_text(
        "\n".join(
            [
                "hubs:",
                "  hub:",
                "    class: Primitive hub",
                "    required_headings: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _write_concept(vault / "concepts" / "hub.md", layer="primitive", deps=[])
    _write_concept(vault / "concepts" / "user.md", layer="first-order", deps=["hub"])

    out = tmp_path / "g.svg"
    run_graph(vault, concepts_only=True, fmt="svg", out=out, styled=True, top=10)

    svg = out.read_text(encoding="utf-8")
    assert svg.strip().startswith("<svg")
    assert "hub: Primitive hub" in svg
