from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from ..artifact.plan_manager import PlanManager
from ..artifact.risk import RiskClass
from ..vault.graph import DependencyGraph
from ..vault.loader import Vault
from ..vault.rules import LintResult, LintRules
from .schema import RuleDef, RulesetDef


@dataclass(frozen=True)
class ConstraintContext:
    vault_path: Path
    vault: Vault
    graph: DependencyGraph
    plan_manager: PlanManager
    # NEW: For emitting constraint evaluation events
    current_artifact_id: str | None = None
    emit_events: bool = False  # Set to True to emit constraint.evaluated events


PredicateFn = Callable[[Any, RuleDef, ConstraintContext], list[LintResult]]


def _lint_result(
    *,
    level: str,
    rule: str,
    file: Path,
    message: str,
    invariant: str | None,
    line: int | None = None,
) -> LintResult:
    return LintResult(
        level=level,  # type: ignore[arg-type]
        rule=rule,
        file=file,
        message=message,
        line=line,
        invariant=invariant,
    )


def predicate_legacy_lint_rule(item: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    rule_id = str(rule.predicate.params.get("rule_id", rule.id)).strip()
    checks = LintRules(ctx.vault, ctx.graph)

    # Mirror LintRules mapping to avoid reaching into private structure.
    rule_checks: dict[str, Callable[[], list[LintResult]]] = {
        "forbidden-edge": checks.check_forbidden_edges,
        "missing-dependencies": checks.check_missing_structural_dependencies,
        "mechanism-missing-residuals": checks.check_mechanism_missing_residuals,
        "hub-required-headings": checks.check_hub_required_headings,
        "alias-drift": checks.check_alias_drift,
        "dependency-cycle": checks.check_cycles,
        "missing-role": checks.check_missing_role,
        "broken-link": checks.check_broken_links,
        "registry-drift": checks.check_registry_drift,
        "layer-violation": checks.check_layer_violations,
        "kind-violation": checks.check_kind_violations,
        "responsibility-scope": checks.check_responsibility_without_scope,
    }

    fn = rule_checks.get(rule_id)
    if fn is None:
        return [
            _lint_result(
                level="error",
                rule=rule.id,
                file=ctx.vault_path,
                message=f"Condition observed: unknown legacy lint rule_id={rule_id!r}",
                invariant=rule.invariant,
            )
        ]

    results = fn()
    # Override invariant attribution from the ruleset, if provided.
    if rule.invariant is not None:
        for r in results:
            r.invariant = rule.invariant
    return results


def predicate_frontmatter_has_keys(concept: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    keys = rule.predicate.params.get("keys", [])
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        return []

    missing = [k for k in keys if not concept.frontmatter.get(k)]
    if not missing:
        return []

    msg = rule.message or f"Condition observed: missing frontmatter keys: {', '.join(missing)}"
    return [_lint_result(level=rule.severity, rule=rule.id, file=concept.path, message=msg, invariant=rule.invariant)]


def predicate_has_headings(concept: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    headings = rule.predicate.params.get("headings", [])
    if not isinstance(headings, list) or not all(isinstance(h, str) for h in headings):
        return []

    present: set[str] = set()
    for line in concept.content.splitlines():
        if line.startswith("## "):
            present.add(line[3:].strip())

    missing = [h for h in headings if h not in present]
    if not missing:
        return []

    msg = rule.message or f"Condition observed: missing headings: {', '.join(missing)}"
    return [_lint_result(level=rule.severity, rule=rule.id, file=concept.path, message=msg, invariant=rule.invariant)]


def predicate_no_outlinks_to_roles(concept: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    roles = rule.predicate.params.get("roles", [])
    if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
        return []
    target_roles = {r.lower().strip() for r in roles if r.strip()}
    if not target_roles:
        return []

    offenders: list[str] = []
    for link in getattr(concept, "links", []) or []:
        note = ctx.vault.get(str(link))
        if note and (note.role or "").lower().strip() in target_roles:
            offenders.append(note.name)

    if not offenders:
        return []

    msg = rule.message or "Condition observed: outlinks to forbidden roles"
    msg = f"{msg} ({', '.join(sorted(set(offenders)))})"
    return [_lint_result(level=rule.severity, rule=rule.id, file=concept.path, message=msg, invariant=rule.invariant)]


def predicate_no_prescriptive_tokens(concept: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    tokens = rule.predicate.params.get("tokens", [])
    if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
        return []
    lowered = concept.content.lower()

    hits: list[str] = []
    for token in tokens:
        t = token.lower()
        if t and t in lowered:
            hits.append(token)

    if not hits:
        return []

    msg = rule.message or "Condition observed: prescriptive tokens detected"
    msg = f"{msg} ({', '.join(sorted(set(hits)))})"
    return [_lint_result(level=rule.severity, rule=rule.id, file=concept.path, message=msg, invariant=rule.invariant)]


def predicate_no_cycles(graph: DependencyGraph, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    cycles = graph.find_simple_cycles()
    if not cycles:
        return []
    cycle = cycles[0]
    msg = rule.message or "Condition observed: dependency cycle detected"
    msg = f"{msg} ({' -> '.join(cycle)})"
    return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]


def predicate_executed_has_required_approval(snapshot: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    risk_requires = rule.predicate.params.get("risk_requires_approval", [])
    required = {str(r).strip().lower() for r in risk_requires} if isinstance(risk_requires, list) else set()

    risk = snapshot.computed_risk_class or snapshot.risk_class
    if risk is None:
        return []

    if required and risk.value not in required:
        return []

    if snapshot.requires_approval() and not snapshot.approval_artifact_id:
        msg = rule.message or "Condition observed: missing approval artifact"
        return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]
    return []


def predicate_approval_requires_force_ack(snapshot: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    risk_value = str(rule.predicate.params.get("risk", "")).strip().lower()
    if not risk_value:
        return []
    risk = snapshot.computed_risk_class or snapshot.risk_class
    if risk is None or risk.value != risk_value:
        return []
    if snapshot.force_ack:
        return []
    msg = rule.message or "Condition observed: destructive approval missing force acknowledgement"
    return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]


def predicate_executed_has_result_artifact(snapshot: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    expected_type = rule.predicate.params.get("result_type")
    expected = str(expected_type).strip().lower() if isinstance(expected_type, str) else None

    result_id = getattr(snapshot, "result_artifact_id", None)
    if not result_id:
        msg = rule.message or "Condition observed: executed plan is missing result_artifact_id"
        return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]

    result_snap = ctx.plan_manager.ledger.snapshot(str(result_id))
    if result_snap is None:
        msg = rule.message or "Condition observed: result artifact not found"
        return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]

    if expected and (result_snap.artifact_type or "").lower().strip() != expected:
        msg = rule.message or "Condition observed: result artifact type mismatch"
        msg = f"{msg} (expected={expected}, got={result_snap.artifact_type})"
        return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]

    return []


def predicate_producer_metadata_has_keys(snapshot: Any, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    keys = rule.predicate.params.get("keys", [])
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        return []

    producer = getattr(snapshot, "producer", None)
    if not isinstance(producer, dict):
        return []

    missing = [k for k in keys if not producer.get(k)]
    if not missing:
        return []

    msg = rule.message or f"Condition observed: producer metadata missing keys: {', '.join(missing)}"
    return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]


_PRESCRIPTIVE_RE = re.compile(r"\b(must|should|fix:|todo:)\b", flags=re.IGNORECASE)


def predicate_ruleset_messages_non_prescriptive(ruleset: RulesetDef, rule: RuleDef, ctx: ConstraintContext) -> list[LintResult]:
    hits: list[str] = []
    for r in ruleset.rules:
        for field in (r.message, r.rationale, r.boundary):
            if not field:
                continue
            if _PRESCRIPTIVE_RE.search(field):
                hits.append(r.id)
                break

    if not hits:
        return []

    msg = rule.message or "Condition observed: prescriptive language in rule messages"
    msg = f"{msg} ({', '.join(sorted(set(hits)))})"
    return [_lint_result(level=rule.severity, rule=rule.id, file=ctx.vault_path, message=msg, invariant=rule.invariant)]


PREDICATES: dict[str, PredicateFn] = {
    "legacy_lint_rule": predicate_legacy_lint_rule,
    "frontmatter_has_keys": predicate_frontmatter_has_keys,
    "has_headings": predicate_has_headings,
    "no_outlinks_to_roles": predicate_no_outlinks_to_roles,
    "no_prescriptive_tokens": predicate_no_prescriptive_tokens,
    "no_cycles": predicate_no_cycles,
    "executed_has_required_approval": predicate_executed_has_required_approval,
    "approval_requires_force_ack": predicate_approval_requires_force_ack,
    "executed_has_result_artifact": predicate_executed_has_result_artifact,
    "producer_metadata_has_keys": predicate_producer_metadata_has_keys,
    "ruleset_messages_non_prescriptive": predicate_ruleset_messages_non_prescriptive,
}
