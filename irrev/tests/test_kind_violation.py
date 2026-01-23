from pathlib import Path

import pytest

from irrev.vault.graph import DependencyGraph
from irrev.vault.loader import load_vault
from irrev.vault.rules import LintRules


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_kind_violation_object_depends_on_operator(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    concepts = vault / "concepts"

    _write(
        concepts / "operator.md",
        """---
layer: selector
role: concept
canonical: true
note_kind: operator
---

# Operator

## Structural dependencies
- [[constraint]]
""",
    )

    _write(
        concepts / "object.md",
        """---
layer: accounting
role: concept
canonical: true
note_kind: object
---

# Object

## Structural dependencies
- [[operator]]
""",
    )

    _write(
        concepts / "constraint.md",
        """---
layer: primitive
role: concept
canonical: true
note_kind: object
---

# Constraint

## Structural dependencies
None (primitive)
""",
    )

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, aliases=loaded._aliases)
    results = LintRules(loaded, graph).run_all()

    kinds = [r for r in results if r.rule == "kind-violation"]
    assert len(kinds) == 1
    assert kinds[0].file.name == "object.md"


def test_kind_violation_only_applies_when_typed(tmp_path: Path) -> None:
    vault = tmp_path / "content"
    concepts = vault / "concepts"

    _write(
        concepts / "operator.md",
        """---
layer: selector
role: concept
canonical: true
note_kind: operator
---

# Operator

## Structural dependencies
None (primitive)
""",
    )

    _write(
        concepts / "untyped.md",
        """---
layer: accounting
role: concept
canonical: true
---

# Untyped

## Structural dependencies
- [[operator]]
""",
    )

    loaded = load_vault(vault)
    graph = DependencyGraph.from_concepts(loaded.concepts, aliases=loaded._aliases)
    results = LintRules(loaded, graph).run_all()

    assert not [r for r in results if r.rule == "kind-violation"]

