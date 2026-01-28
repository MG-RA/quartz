"""
Neo4j load handler for the execution harness.

Wraps existing compute_neo4j_load_plan() and execute_neo4j_load_plan()
functions with the Handler protocol, adding:
- EffectSummary derivation (risk is computed from effects)
- Plan validation
- Secrets reference support
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console

from ...commands.neo4j_cmd import compute_neo4j_load_plan, execute_neo4j_load_plan
from ...planning import Neo4jLoadPlan, Neo4jLoadResult
from ..handler import EffectSummary, ExecutionContext, Handler, HandlerMetadata
from ..secrets import resolve_secrets


@dataclass
class Neo4jLoadPlanWithEffects:
    """
    Neo4jLoadPlan wrapper that includes EffectSummary.

    This satisfies the HarnessPlan protocol requirement.
    """

    inner: Neo4jLoadPlan
    effect_summary: EffectSummary

    @property
    def vault_path(self) -> Path:
        return self.inner.vault_path

    @property
    def mode(self) -> str:
        return self.inner.mode

    @property
    def database(self) -> str:
        return self.inner.database

    @property
    def http_uri(self) -> str:
        return self.inner.http_uri

    @property
    def notes(self) -> list[dict[str, Any]]:
        return self.inner.notes

    @property
    def links_to(self) -> list[tuple[str, str]]:
        return self.inner.links_to

    @property
    def depends_on(self) -> list[tuple[str, str]]:
        return self.inner.depends_on

    @property
    def topology_rows(self) -> list[dict[str, Any]]:
        return self.inner.topology_rows

    @property
    def existing_node_count(self) -> int:
        return self.inner.existing_node_count

    @property
    def existing_edge_count(self) -> int:
        return self.inner.existing_edge_count

    @property
    def unresolved_links(self) -> int:
        return self.inner.unresolved_links

    def summary(self) -> str:
        return self.inner.summary()


class Neo4jLoadHandler(Handler[Neo4jLoadPlanWithEffects, Neo4jLoadResult]):
    """
    Handler for neo4j.load operation.

    Wraps the existing neo4j load infrastructure with the harness protocol.
    """

    @property
    def metadata(self) -> HandlerMetadata:
        return HandlerMetadata(
            operation="neo4j.load",
            delegate_to="handler:neo4j",
            supports_dry_run=True,
        )

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate operation parameters."""
        errors: list[str] = []

        if not params.get("http_uri"):
            errors.append("http_uri is required")
        if not params.get("database"):
            errors.append("database is required")

        mode = params.get("mode", "sync")
        if mode not in ("sync", "rebuild"):
            errors.append(f"mode must be 'sync' or 'rebuild', got {mode!r}")

        return errors

    def compute_plan(
        self,
        vault_path: Path,
        params: dict[str, Any],
    ) -> Neo4jLoadPlanWithEffects:
        """Compute neo4j load plan with effect summary."""
        inner = compute_neo4j_load_plan(
            vault_path,
            http_uri=str(params.get("http_uri", "")),
            database=str(params.get("database", "")),
            mode=str(params.get("mode", "sync")),
        )

        effect_summary = self._derive_effects(inner, params)
        return Neo4jLoadPlanWithEffects(inner=inner, effect_summary=effect_summary)

    def _derive_effects(
        self,
        plan: Neo4jLoadPlan,
        params: dict[str, Any],
    ) -> EffectSummary:
        """Derive effect summary from plan and params."""
        mode = str(params.get("mode", "sync")).lower().strip()
        database = str(params.get("database", ""))

        if mode == "rebuild":
            return EffectSummary(
                effect_type="mutation_destructive",
                predicted_erasure={
                    "notes": plan.existing_node_count,
                    "edges": plan.existing_edge_count,
                },
                predicted_outputs=[database],
                reasons=["rebuild mode wipes all nodes and edges before loading"],
            )

        return EffectSummary(
            effect_type="external_side_effect",
            predicted_erasure={},
            predicted_outputs=[database],
            reasons=["writes to external Neo4j database"],
        )

    def validate_plan(self, plan: Neo4jLoadPlanWithEffects) -> list[str]:
        """Validate the computed plan."""
        errors: list[str] = []

        if not plan.notes:
            errors.append("No notes to load (empty vault?)")

        return errors

    def execute(
        self,
        plan: Neo4jLoadPlanWithEffects,
        context: ExecutionContext,
    ) -> Neo4jLoadResult:
        """Execute the neo4j load plan."""
        console = Console(stderr=True)

        # Resolve secrets
        secrets: dict[str, str] = {}
        if context.secrets_ref:
            # Parse secrets ref - expecting format like "env:NEO4J_USER,env:NEO4J_PASSWORD"
            refs = {}
            for part in context.secrets_ref.split(","):
                part = part.strip()
                if "=" in part:
                    name, ref = part.split("=", 1)
                    refs[name.strip()] = ref.strip()
                elif part.startswith("env:"):
                    # Default mapping: env:FOO -> foo=FOO
                    var_name = part[4:]
                    refs[var_name.lower()] = part
            secrets = resolve_secrets(refs)

        user = secrets.get("neo4j_user", secrets.get("user", "neo4j"))
        password = secrets.get("neo4j_password", secrets.get("password", ""))

        # Get optional params with defaults
        ensure_schema = True
        batch_size = 500

        return execute_neo4j_load_plan(
            plan.inner,
            user=user,
            password=password,
            ensure_schema=ensure_schema,
            batch_size=batch_size,
            console=console,
        )
