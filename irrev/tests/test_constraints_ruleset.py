from __future__ import annotations

from pathlib import Path

from irrev.constraints.engine import run_constraints_lint
from irrev.constraints.load import load_ruleset
from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import load_vault


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_constraints_ruleset_custom_predicate(tmp_path: Path) -> None:
    vault_path = tmp_path / "content"

    _write(
        vault_path / "concepts" / "ConceptA.md",
        """---
canonical: true
---

# ConceptA

See [[PaperOne]].
""",
    )
    _write(
        vault_path / "papers" / "PaperOne.md",
        "# PaperOne\n",
    )

    ruleset_path = tmp_path / "ruleset.toml"
    _write(
        ruleset_path,
        """
ruleset_id = "ruleset/test"
version = 1

[[rules]]
id = "concept.no_paper_depends"
invariant = "decomposition"
scope = "concept"
severity = "error"
selector = { kind = "all_concepts", canonical_only = true }
predicate = { name = "no_outlinks_to_roles", params = { roles = ["paper"] } }
message = "Concept links to a paper."
""",
    )

    ruleset = load_ruleset(ruleset_path)
    vault = load_vault(vault_path)
    graph = DependencyGraph.from_concepts(vault.concepts, vault._aliases)

    results = run_constraints_lint(vault_path, vault=vault, graph=graph, ruleset=ruleset)
    assert any(r.rule == "concept.no_paper_depends" for r in results)

