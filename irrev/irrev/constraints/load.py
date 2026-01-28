from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import Predicate, RuleDef, RulesetDef, Selector


def _coerce_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_ruleset(path: Path) -> RulesetDef:
    """
    Load a ruleset from TOML.

    The schema is intentionally small: rules are data, evaluation is code.
    """
    import tomllib

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    ruleset_id = str(data.get("ruleset_id", "")).strip()
    if not ruleset_id:
        raise ValueError("ruleset_id is required")

    version = int(data.get("version", 0))
    if version <= 0:
        raise ValueError("version must be a positive integer")

    defaults = _coerce_dict(data.get("defaults"))
    default_scope = str(defaults.get("scope", "concept")).strip() or "concept"
    default_severity = str(defaults.get("severity", "error")).strip() or "error"

    rules: list[RuleDef] = []
    for raw in data.get("rules", []):
        if not isinstance(raw, dict):
            continue

        rule_id = str(raw.get("id", "")).strip()
        if not rule_id:
            continue

        scope = str(raw.get("scope", default_scope)).strip() or default_scope
        severity = str(raw.get("severity", default_severity)).strip() or default_severity

        invariant = raw.get("invariant")
        invariant_str = str(invariant).strip() if isinstance(invariant, str) else None
        if invariant_str == "":
            invariant_str = None

        selector_raw = _coerce_dict(raw.get("selector"))
        selector_kind = str(selector_raw.get("kind", "all")).strip() or "all"
        selector_params = {k: v for k, v in selector_raw.items() if k != "kind"}

        pred_raw = _coerce_dict(raw.get("predicate"))
        pred_name = str(pred_raw.get("name", "noop")).strip() or "noop"
        pred_params = _coerce_dict(pred_raw.get("params"))

        message = raw.get("message")
        message_str = str(message) if isinstance(message, str) else None

        rationale = raw.get("rationale")
        rationale_str = str(rationale) if isinstance(rationale, str) else None

        boundary = raw.get("boundary")
        boundary_str = str(boundary) if isinstance(boundary, str) else None

        repair_class = raw.get("repair_class")
        repair_class_str = str(repair_class) if isinstance(repair_class, str) else None

        evidence = _coerce_dict(raw.get("evidence"))

        rules.append(
            RuleDef(
                id=rule_id,
                scope=scope,  # type: ignore[arg-type]
                severity=severity,  # type: ignore[arg-type]
                invariant=invariant_str,
                selector=Selector(kind=selector_kind, params=selector_params),
                predicate=Predicate(name=pred_name, params=pred_params),
                message=message_str,
                rationale=rationale_str,
                boundary=boundary_str,
                repair_class=repair_class_str,
                evidence=evidence,
            )
        )

    return RulesetDef(
        ruleset_id=ruleset_id,
        version=version,
        description=(str(data.get("description")) if isinstance(data.get("description"), str) else None),
        rules=rules,
    )


def load_core_ruleset(vault_path: Path) -> RulesetDef | None:
    """Load the vault-owned core ruleset, if present."""
    ruleset_path = vault_path / "meta" / "rulesets" / "core.toml"
    if not ruleset_path.exists():
        return None
    return load_ruleset(ruleset_path)
