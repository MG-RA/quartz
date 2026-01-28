from __future__ import annotations

from pathlib import Path

from ..artifact.plan_manager import PlanManager
from ..vault.graph import DependencyGraph
from ..vault.loader import Vault
from ..vault.rules import LintResult
from .predicates import ConstraintContext, PREDICATES
from .schema import RuleDef, RulesetDef


def _select_items(rule: RuleDef, ctx: ConstraintContext, ruleset: RulesetDef):
    kind = (rule.selector.kind or "all").strip().lower()
    params = rule.selector.params

    if rule.scope == "concept":
        canonical_only = bool(params.get("canonical_only", False))
        exclude_tags = params.get("exclude_tags", [])
        exclude_roles = params.get("exclude_roles", [])

        excluded_tags: set[str] = set()
        if isinstance(exclude_tags, list):
            excluded_tags = {str(t).lower().strip() for t in exclude_tags if str(t).strip()}

        excluded_roles: set[str] = set()
        if isinstance(exclude_roles, list):
            excluded_roles = {str(r).lower().strip() for r in exclude_roles if str(r).strip()}

        concepts = ctx.vault.concepts
        if canonical_only:
            concepts = [c for c in concepts if getattr(c, "canonical", False)]

        if excluded_roles:
            concepts = [c for c in concepts if (getattr(c, "role", "") or "").lower().strip() not in excluded_roles]

        if excluded_tags:
            filtered = []
            for c in concepts:
                tags = c.frontmatter.get("tags") if hasattr(c, "frontmatter") else None
                tag_list: list[str] = []
                if isinstance(tags, str):
                    tag_list = [tags]
                elif isinstance(tags, list):
                    tag_list = [str(t) for t in tags if t is not None]
                tag_set = {t.lower().strip() for t in tag_list if t.strip()}
                if tag_set.intersection(excluded_tags):
                    continue
                filtered.append(c)
            concepts = filtered
        return concepts

    if rule.scope == "graph":
        return [ctx.graph]

    if rule.scope == "artifact":
        status = params.get("status")
        artifact_type = params.get("type")
        snaps = list(ctx.plan_manager.ledger.all_snapshots().values())
        if isinstance(status, str) and status.strip():
            snaps = [s for s in snaps if s.status == status.strip()]
        if isinstance(artifact_type, str) and artifact_type.strip():
            snaps = [s for s in snaps if s.artifact_type == artifact_type.strip()]
        return snaps

    if rule.scope == "ruleset":
        return [ruleset]

    # "vault" and unknown scopes: evaluate once with context-only item.
    return [None]


def run_constraints_lint(
    vault_path: Path,
    *,
    vault: Vault,
    graph: DependencyGraph,
    ruleset: RulesetDef,
    allowed_rule_ids: set[str] | None = None,
    invariant_filter: str | None = None,
    artifact_id: str | None = None,
    emit_events: bool = False,
) -> list[LintResult]:
    """
    Evaluate a ruleset against the vault.

    Output is expressed as LintResult to reuse existing CLI rendering.

    Args:
        vault_path: Path to vault
        vault: Loaded vault
        graph: Dependency graph
        ruleset: Ruleset to evaluate
        allowed_rule_ids: Optional set of rule IDs to filter
        invariant_filter: Optional invariant ID to filter
        artifact_id: Artifact ID to link constraint events to
        emit_events: If True, emit constraint.evaluated and invariant.checked events
    """
    ctx = ConstraintContext(
        vault_path=vault_path,
        vault=vault,
        graph=graph,
        plan_manager=PlanManager(vault_path),
        current_artifact_id=artifact_id,
        emit_events=emit_events,
    )

    results: list[LintResult] = []

    for rule in ruleset.rules:
        if allowed_rule_ids is not None and rule.id not in allowed_rule_ids:
            continue
        if invariant_filter and rule.invariant != invariant_filter:
            continue

        fn = PREDICATES.get(rule.predicate.name)
        if fn is None:
            continue

        for item in _select_items(rule, ctx, ruleset):
            rule_results = fn(item, rule, ctx)
            results.extend(rule_results)

            # NEW: Emit constraint.evaluated event if enabled
            if emit_events and artifact_id:
                _emit_constraint_events(
                    ctx.plan_manager.ledger,
                    artifact_id,
                    ruleset,
                    rule,
                    rule_results,
                )

    # NEW: Emit invariant.checked events
    if emit_events and artifact_id:
        _emit_invariant_events(
            ctx.plan_manager.ledger,
            artifact_id,
            ruleset,
            results,
        )

    return results


def _emit_constraint_events(
    ledger,
    artifact_id: str,
    ruleset: RulesetDef,
    rule: RuleDef,
    rule_results: list[LintResult],
) -> None:
    """Emit constraint.evaluated events for each rule evaluation."""
    from ..artifact.events import CONSTRAINT_EVALUATED, create_event

    # Emit one event per rule evaluation
    # If no results, the rule passed
    if not rule_results:
        event = create_event(
            CONSTRAINT_EVALUATED,
            artifact_id=artifact_id,
            actor="system:constraint_engine",
            payload={
                "ruleset_id": ruleset.ruleset_id,
                "ruleset_version": ruleset.version,
                "rule_id": rule.id,
                "rule_scope": rule.scope,
                "invariant": rule.invariant or "unclassified",
                "result": "pass",
                "evidence": {},
            },
        )
        ledger.append(event)
    else:
        # Emit event for each violation
        for result in rule_results:
            event = create_event(
                CONSTRAINT_EVALUATED,
                artifact_id=artifact_id,
                actor="system:constraint_engine",
                payload={
                    "ruleset_id": ruleset.ruleset_id,
                    "ruleset_version": ruleset.version,
                    "rule_id": rule.id,
                    "rule_scope": rule.scope,
                    "invariant": rule.invariant or "unclassified",
                    "result": "fail" if result.level == "error" else "warning",
                    "evidence": {
                        "item_id": getattr(result, "concept_id", None) or str(result.file),
                        "item_type": "concept" if hasattr(result, "concept_id") else "file",
                        "message": result.message,
                        "line": result.line,
                    },
                },
            )
            ledger.append(event)


def _emit_invariant_events(
    ledger,
    artifact_id: str,
    ruleset: RulesetDef,
    all_results: list[LintResult],
) -> None:
    """Emit invariant.checked events summarizing invariant status."""
    from ..artifact.events import INVARIANT_CHECKED, create_event

    # Group results by invariant
    invariants_checked: dict[str, list[LintResult]] = {}
    for rule in ruleset.rules:
        inv_id = rule.invariant or "unclassified"
        if inv_id not in invariants_checked:
            invariants_checked[inv_id] = []

    for result in all_results:
        inv_id = result.invariant or "unclassified"
        if inv_id in invariants_checked:
            invariants_checked[inv_id].append(result)

    # Emit event for each invariant
    for inv_id, results in invariants_checked.items():
        violations = [r for r in results if r.level == "error"]
        affected_items = list({
            getattr(r, "concept_id", None) or str(r.file)
            for r in results
        })

        event = create_event(
            INVARIANT_CHECKED,
            artifact_id=artifact_id,
            actor="system:constraint_engine",
            payload={
                "invariant_id": inv_id,
                "status": "fail" if violations else "pass",
                "rules_checked": len([r for r in ruleset.rules if (r.invariant or "unclassified") == inv_id]),
                "violations": len(violations),
                "affected_items": affected_items,
            },
        )
        ledger.append(event)
