"""Declarative constraint engine (rules as data, predicates as code)."""

from .load import load_core_ruleset
from .engine import run_constraints_lint

__all__ = ["load_core_ruleset", "run_constraints_lint"]

