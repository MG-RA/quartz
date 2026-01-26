from pathlib import Path

from irrev.commands.junctions import run_domain_audit, run_implicit_audit


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


def _write_domain(path: Path, *, links: list[str]) -> None:
    body = "\n".join(f"- [[{l}]]" for l in links)
    path.write_text(
        "\n".join(
            [
                "---",
                "role: domain",
                "---",
                "",
                f"# {path.stem}",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_domain_audit_reports_implied_deps(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)
    (vault / "domains").mkdir(parents=True)

    _write_concept(vault / "concepts" / "accumulation.md", layer="primitive", deps=[])
    _write_concept(vault / "concepts" / "constraint-load.md", layer="first-order", deps=["accumulation"])

    _write_domain(vault / "domains" / "Digital Platforms.md", links=["constraint-load"])

    out = tmp_path / "domain-audit.md"
    code = run_domain_audit(vault, out=out, fmt="md")
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert "Domain Implied Dependency Audit" in text
    assert "[[constraint-load]]" in text
    assert "[[accumulation]]" in text


def test_implicit_audit_runs_for_projection_role(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "concepts").mkdir(parents=True)
    (vault / "projections").mkdir(parents=True)

    _write_concept(vault / "concepts" / "accumulation.md", layer="primitive", deps=[])
    _write_concept(vault / "concepts" / "constraint-load.md", layer="first-order", deps=["accumulation"])

    # Projection links to constraint-load, which implies accumulation.
    (vault / "projections" / "OpenAI.md").write_text(
        "\n".join(["---", "role: projection", "---", "", "# OpenAI", "", "- [[constraint-load]]", ""]),
        encoding="utf-8",
    )

    out = tmp_path / "implicit.md"
    code = run_implicit_audit(vault, role="projection", include_all=True, out=out, fmt="md")
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert "Implicit Dependency Audit" in text
    assert "[[accumulation]]" in text
