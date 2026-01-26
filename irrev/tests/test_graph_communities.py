import json
from pathlib import Path

from irrev.commands.graph_cmd import run_communities


def _write_concept(path: Path, *, layer: str, links: list[str] | None = None) -> None:
    links = links or []
    body = "\n".join(f"- [[{l}]]" for l in links)
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
                body,
                "",
                "## Structural dependencies",
                "- None",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_communities_perfectly_align_with_layers_in_two_components(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)

    # Two disconnected pairs; each pair is a single layer.
    _write_concept(vault / "concepts" / "a.md", layer="primitive", links=["b"])
    _write_concept(vault / "concepts" / "b.md", layer="primitive", links=["a"])
    _write_concept(vault / "concepts" / "c.md", layer="first-order", links=["d"])
    _write_concept(vault / "concepts" / "d.md", layer="first-order", links=["c"])

    out = tmp_path / "communities.json"
    code = run_communities(vault, mode="links", algorithm="greedy", fmt="json", out=out, max_iter=20)
    assert code == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert summary["purity"] == 1.0
    assert summary["nmi"] == 1.0
