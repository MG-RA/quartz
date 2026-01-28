from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Scope = Literal["concept", "graph", "artifact", "ruleset", "vault"]
Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class Selector:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Predicate:
    name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleDef:
    id: str
    scope: Scope
    severity: Severity = "error"
    invariant: str | None = None
    selector: Selector = field(default_factory=lambda: Selector(kind="all"))
    predicate: Predicate = field(default_factory=lambda: Predicate(name="noop"))
    message: str | None = None
    rationale: str | None = None
    boundary: str | None = None
    repair_class: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RulesetDef:
    ruleset_id: str
    version: int
    description: str | None = None
    rules: list[RuleDef] = field(default_factory=list)
