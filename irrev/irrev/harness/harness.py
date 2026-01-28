"""
Unified execution harness for all effectful operations.

Orchestrates: propose() → validate() → [approval gate] → execute() → bundle

Key invariants:
- No auto-approval: approval is an act, not a convenience
- Risk derived from plan effects, not from params
- Gate denial is auditable (rejection events emitted)
- All operations pass through this single chokepoint
"""

from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

from ..artifact.content_store import ContentStore
from ..artifact.events import ARTIFACT_CREATED, ARTIFACT_REJECTED, create_event
from ..artifact.ledger import ArtifactLedger
from ..artifact.plan_manager import ApprovalPolicy, PlanManager
from ..artifact.risk import RiskClass
from ..artifact.util import new_ulid
from ..audit_log import CreationSummary, ErasureCost, log_operation

from .handler import EffectSummary, EffectType, ExecutionContext, Handler, HarnessPlan
from .secrets import CompositeSecretsProvider, SecretsProvider


def _effect_type_to_risk(effect_type: EffectType) -> RiskClass:
    """Map EffectType to RiskClass."""
    mapping: dict[EffectType, RiskClass] = {
        "read_only": RiskClass.READ_ONLY,
        "append_only": RiskClass.APPEND_ONLY,
        "mutation_reversible": RiskClass.MUTATION_REVERSIBLE,
        "mutation_destructive": RiskClass.MUTATION_DESTRUCTIVE,
        "external_side_effect": RiskClass.EXTERNAL_SIDE_EFFECT,
    }
    return mapping.get(effect_type, RiskClass.EXTERNAL_SIDE_EFFECT)


def _get_engine_version() -> str:
    """Get engine version string for repro header."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            sha = result.stdout.strip()
            return f"0.1.0+git.{sha}"
    except Exception:
        pass
    return "0.1.0"


def _get_environment() -> dict[str, str]:
    """Get environment fingerprint for repro header."""
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "platform": platform.system().lower(),
    }


def _hash_file(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    import hashlib
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return f"sha256:{hasher.hexdigest()}"


def _hash_vault_content(vault_path: Path) -> str:
    """Compute deterministic hash of vault content."""
    import hashlib
    hasher = hashlib.sha256()

    # Hash all markdown files in sorted order
    md_files = sorted(vault_path.rglob("*.md"))
    for md_file in md_files:
        if md_file.is_file():
            # Hash relative path + content
            rel_path = str(md_file.relative_to(vault_path))
            hasher.update(rel_path.encode("utf-8"))
            hasher.update(md_file.read_bytes())

    return hasher.hexdigest() if md_files else "empty"


@dataclass
class ProposeResult:
    """Result of harness.propose()."""

    plan_artifact_id: str
    risk_class: RiskClass
    requires_approval: bool
    requires_force_ack: bool
    plan_summary: str
    validation_errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.validation_errors


@dataclass
class ExecuteResult:
    """Result of harness.execute()."""

    success: bool
    plan_artifact_id: str
    result_artifact_id: str | None = None
    bundle_artifact_id: str | None = None
    error: str | None = None
    dry_run: bool = False


class Harness:
    """
    Unified execution harness for all effectful operations.

    Provides three entry points:
    - propose(): Pure - compute plan, derive risk, create artifact
    - execute(): Impure - verify approval, execute, emit bundle
    - run(): Convenience - propose + execute (only if no approval required)

    Key design: NO auto-approval. If an operation requires approval,
    it must be explicitly approved via `artifact approve` before execute().
    """

    def __init__(
        self,
        vault_path: Path,
        *,
        console: Console | None = None,
        policy: ApprovalPolicy | None = None,
        secrets_provider: SecretsProvider | None = None,
    ):
        self.vault_path = vault_path.resolve()
        self.irrev_dir = self.vault_path.parent / ".irrev"
        self.plan_manager = PlanManager(vault_path, policy=policy)
        self.content_store = ContentStore(self.irrev_dir)
        self.ledger = ArtifactLedger(self.irrev_dir)
        self.console = console or Console(stderr=True)
        self.secrets_provider = secrets_provider or CompositeSecretsProvider()
        self.policy = policy or ApprovalPolicy()

    # -------------------------------------------------------------------------
    # propose(): Pure phase
    # -------------------------------------------------------------------------

    def propose(
        self,
        handler: Handler,
        params: dict[str, Any],
        *,
        actor: str = "agent:harness",
        surface: str = "cli",
    ) -> ProposeResult:
        """
        Compute plan, derive risk, create plan artifact.

        This is the pure phase - no side effects beyond artifact creation.

        Args:
            handler: Handler for the operation
            params: Operation parameters
            actor: Actor identity (e.g., "agent:cli", "human:alice")
            surface: Calling surface ("cli" | "mcp" | "lsp" | "ci")

        Returns:
            ProposeResult with plan_artifact_id and gate requirements
        """
        meta = handler.metadata
        errors: list[str] = []

        # Step 1: Validate params
        param_errors = handler.validate_params(params)
        if param_errors:
            errors.extend(param_errors)

        # Step 2: Compute plan (pure)
        self.console.print(f"Computing {meta.operation} plan...", style="dim")
        try:
            plan = handler.compute_plan(self.vault_path, params)
        except Exception as e:
            return ProposeResult(
                plan_artifact_id="",
                risk_class=RiskClass.EXTERNAL_SIDE_EFFECT,
                requires_approval=True,
                requires_force_ack=False,
                plan_summary="",
                validation_errors=[f"compute_plan failed: {e}"],
            )

        # Step 3: Validate plan (pure)
        plan_errors = handler.validate_plan(plan)
        errors.extend(plan_errors)

        # Step 4: Derive risk from effect_summary
        effect_summary = plan.effect_summary
        risk_class = _effect_type_to_risk(effect_summary.effect_type)

        # Step 5: Determine gate requirements
        requires_approval = risk_class in {
            RiskClass.MUTATION_DESTRUCTIVE,
            RiskClass.EXTERNAL_SIDE_EFFECT,
        }
        requires_force_ack = risk_class == RiskClass.MUTATION_DESTRUCTIVE

        # Step 6: Capture execution context
        vault_state = self._capture_vault_state()
        active_rulesets = self._load_active_rulesets()

        # Step 7: Prepare plan payload for artifact
        plan_payload: dict[str, Any] = {
            **params,
            "plan_summary": plan.summary(),
            "effect_summary": effect_summary.to_dict(),
            # NEW: Context metadata for reproducibility
            "context": {
                "vault_state": vault_state,
                "active_rulesets": active_rulesets,
                "surface": surface,
                "engine_version": _get_engine_version(),
                "environment": _get_environment(),
            },
            # NEW: Plan metadata for governance
            "plan_metadata": {
                "predicted_erasure": effect_summary.predicted_erasure,
                "predicted_outputs": effect_summary.predicted_outputs,
                "effect_reasons": effect_summary.reasons,
            },
        }

        # Step 8: Propose plan artifact
        plan_artifact_id = self.plan_manager.propose(
            meta.operation,
            plan_payload,
            actor,
            delegate_to=meta.delegate_to,
            surface=surface,
            artifact_type="plan",
        )

        # Step 9: Run constraint validation and emit events
        constraint_results = self._validate_with_constraints(plan_artifact_id, active_rulesets)

        # Step 10: Validate artifact with constraint results
        valid = self.plan_manager.validate(
            plan_artifact_id,
            validator="harness",
            constraint_results=constraint_results,
        )
        if not valid:
            snap = self.plan_manager.ledger.snapshot(plan_artifact_id)
            if snap and snap.validation_errors:
                errors.extend(snap.validation_errors)

        # Include validation errors from earlier steps
        if errors and not self.plan_manager.ledger.snapshot(plan_artifact_id):
            # Artifact validation failed early - still emit result
            pass

        self.console.print(f"plan_id: {plan_artifact_id}", style="bold cyan")
        self.console.print(f"risk_class: {risk_class.value}", style="dim")
        if requires_approval:
            self.console.print("approval required: yes", style="yellow")
        if requires_force_ack:
            self.console.print("force_ack required: yes", style="yellow")

        return ProposeResult(
            plan_artifact_id=plan_artifact_id,
            risk_class=risk_class,
            requires_approval=requires_approval,
            requires_force_ack=requires_force_ack,
            plan_summary=plan.summary(),
            validation_errors=errors,
        )

    # -------------------------------------------------------------------------
    # execute(): Impure phase
    # -------------------------------------------------------------------------

    def execute(
        self,
        plan_artifact_id: str,
        handler: Handler,
        *,
        executor: str = "handler:harness",
        secrets_ref: str | None = None,
        dry_run: bool = False,
    ) -> ExecuteResult:
        """
        Execute an approved plan artifact.

        This is the impure phase - performs actual side effects.

        IMPORTANT: No auto-approval. If approval is required and not present,
        this method emits a rejection event and returns an error.

        Args:
            plan_artifact_id: ID of the plan artifact to execute
            handler: Handler for the operation
            executor: Executor identity
            secrets_ref: Reference to secrets (e.g., "env:NEO4J_PASSWORD")
            dry_run: If True, skip actual execution but emit bundle

        Returns:
            ExecuteResult with result and bundle artifact IDs
        """
        meta = handler.metadata

        # Step 1: Load plan artifact
        snap = self.plan_manager.ledger.snapshot(plan_artifact_id)
        if snap is None:
            return ExecuteResult(
                success=False,
                plan_artifact_id=plan_artifact_id,
                error=f"Plan artifact not found: {plan_artifact_id}",
            )

        # Step 2: Verify artifact status and approval chain
        # NO auto-approval: if approval is required, it must be explicitly granted
        if snap.status == "validated" and snap.requires_approval():
            # Emit rejection event for audit trail
            self._emit_gated_rejection(plan_artifact_id, executor, "approval_required")
            return ExecuteResult(
                success=False,
                plan_artifact_id=plan_artifact_id,
                error=f"Approval required but not granted. Use 'irrev artifact approve {plan_artifact_id}' first.",
            )

        if snap.status != "approved":
            if snap.status == "created":
                return ExecuteResult(
                    success=False,
                    plan_artifact_id=plan_artifact_id,
                    error="Plan not validated. Run validation first.",
                )
            if snap.status in ("executed", "rejected", "superseded"):
                return ExecuteResult(
                    success=False,
                    plan_artifact_id=plan_artifact_id,
                    error=f"Plan already {snap.status}. Cannot execute again.",
                )
            return ExecuteResult(
                success=False,
                plan_artifact_id=plan_artifact_id,
                error=f"Unexpected plan status: {snap.status}",
            )

        # Step 3: Load plan content
        content = self.content_store.get(snap.content_id)
        if not isinstance(content, dict):
            return ExecuteResult(
                success=False,
                plan_artifact_id=plan_artifact_id,
                error=f"Missing or invalid plan content: {snap.content_id}",
            )

        # Step 4: Reconstruct plan from params
        params = content.get("payload", {})
        if not isinstance(params, dict):
            params = {}

        try:
            plan = handler.compute_plan(self.vault_path, params)
        except Exception as e:
            return ExecuteResult(
                success=False,
                plan_artifact_id=plan_artifact_id,
                error=f"Failed to reconstruct plan: {e}",
            )

        # Step 5: Create execution context
        context = ExecutionContext(
            vault_path=self.vault_path,
            executor=executor,
            plan_artifact_id=plan_artifact_id,
            approval_artifact_id=snap.approval_artifact_id,
            dry_run=dry_run,
            secrets_ref=secrets_ref,
        )

        # Step 6: Dry run check
        if dry_run:
            self.console.print("\n[bold]DRY RUN[/bold] - No execution", style="yellow")
            self.console.print(plan.summary())
            return ExecuteResult(
                success=True,
                plan_artifact_id=plan_artifact_id,
                dry_run=True,
            )

        # Step 7: Execute handler with execution logging
        from ..artifact.util import new_ulid
        execution_id = new_ulid()  # Unique per execution

        self.console.print(f"Executing {meta.operation}...", style="dim")

        def _handler_wrapper(plan_content: dict[str, Any]) -> dict[str, Any]:
            result = handler.execute(plan, context)
            # Extract erased/created from result
            erased = getattr(result, "erased", ErasureCost())
            created = getattr(result, "created", CreationSummary())
            success = getattr(result, "success", True)
            error = getattr(result, "error", None)

            return {
                "success": success,
                "error": error,
                "erasure_cost": asdict(erased) if hasattr(erased, "__dataclass_fields__") else {},
                "creation_summary": asdict(created) if hasattr(created, "__dataclass_fields__") else {},
            }

        try:
            # Phase 1: Prepare (context creation already done above, just log it)
            def _prepare_phase() -> None:
                # Preparation already completed (context creation)
                pass

            self._run_phase(
                plan_artifact_id,
                execution_id,
                "prepare",
                meta.operation,
                _prepare_phase
            )

            # Phase 2: Execute
            def _execute_phase() -> str:
                return self.plan_manager.execute(
                    plan_artifact_id,
                    meta.delegate_to,
                    handler=_handler_wrapper,
                )

            result_artifact_id = self._run_phase(
                plan_artifact_id,
                execution_id,
                "execute",
                meta.operation,
                _execute_phase
            )

            # Phase 3: Commit (emit bundle is the commit phase)
            def _commit_phase() -> None:
                # Commit phase is the bundle emission (happens next)
                pass

            self._run_phase(
                plan_artifact_id,
                execution_id,
                "commit",
                meta.operation,
                _commit_phase
            )

        except Exception as e:
            return ExecuteResult(
                success=False,
                plan_artifact_id=plan_artifact_id,
                error=str(e),
            )

        # Step 8: Emit bundle with repro header
        # Get surface from the artifact snapshot's producer info
        surface = snap.producer.get("surface", "cli")
        bundle_artifact_id = self._emit_bundle(
            plan_artifact_id,
            snap.approval_artifact_id,
            result_artifact_id,
            meta.operation,
            executor,
            surface,
        )

        # Step 9: Audit log
        result_snap = self.plan_manager.ledger.snapshot(result_artifact_id)
        result_content = {}
        if result_snap and result_snap.content_id:
            rc = self.content_store.get(result_snap.content_id)
            if isinstance(rc, dict):
                result_content = rc

        erased = self._extract_erasure(result_content)
        created = self._extract_creation(result_content)

        log_operation(
            self.vault_path,
            operation=meta.operation,
            erased=erased,
            created=created,
            metadata={
                "plan_artifact_id": plan_artifact_id,
                "result_artifact_id": result_artifact_id,
                "bundle_artifact_id": bundle_artifact_id,
                "harness_version": "1.0",
            },
        )

        self.console.print(f"{meta.operation} complete.", style="green")
        return ExecuteResult(
            success=True,
            plan_artifact_id=plan_artifact_id,
            result_artifact_id=result_artifact_id,
            bundle_artifact_id=bundle_artifact_id,
        )

    # -------------------------------------------------------------------------
    # run(): Convenience wrapper
    # -------------------------------------------------------------------------

    def run(
        self,
        handler: Handler,
        params: dict[str, Any],
        *,
        actor: str = "agent:harness",
        surface: str = "cli",
        executor: str | None = None,
        secrets_ref: str | None = None,
        dry_run: bool = False,
    ) -> ExecuteResult:
        """
        Propose + execute in one call (only if no approval required).

        This is a convenience method. If the operation requires approval,
        it returns an error - you must use propose() + approve + execute().

        Args:
            handler: Handler for the operation
            params: Operation parameters
            actor: Actor identity
            surface: Calling surface
            executor: Executor identity (defaults to handler.metadata.delegate_to)
            secrets_ref: Reference to secrets
            dry_run: If True, skip actual execution

        Returns:
            ExecuteResult
        """
        # Step 1: Propose
        propose_result = self.propose(handler, params, actor=actor, surface=surface)

        if not propose_result.success:
            return ExecuteResult(
                success=False,
                plan_artifact_id=propose_result.plan_artifact_id,
                error=f"Validation failed: {'; '.join(propose_result.validation_errors)}",
            )

        # Step 2: Check if approval required
        if propose_result.requires_approval:
            # Cannot auto-approve - return gated result
            force_note = " (with --force)" if propose_result.requires_force_ack else ""
            return ExecuteResult(
                success=False,
                plan_artifact_id=propose_result.plan_artifact_id,
                error=(
                    f"Approval required (risk={propose_result.risk_class.value}). "
                    f"Use 'irrev artifact approve {propose_result.plan_artifact_id}'{force_note} first."
                ),
            )

        # Step 3: Auto-approve for low-risk operations
        # Note: This is NOT auto-approval in the governance sense.
        # Low-risk operations (read_only, append_only, mutation_reversible)
        # don't require explicit approval, so we proceed.
        self.plan_manager.approve(
            propose_result.plan_artifact_id,
            actor,
            scope=handler.metadata.operation,
        )

        # Step 4: Execute
        executor = executor or handler.metadata.delegate_to
        return self.execute(
            propose_result.plan_artifact_id,
            handler,
            executor=executor,
            secrets_ref=secrets_ref,
            dry_run=dry_run,
        )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _emit_gated_rejection(
        self,
        artifact_id: str,
        actor: str,
        reason: str,
    ) -> None:
        """Emit a rejection event for gate denials (audit trail)."""
        event = create_event(
            ARTIFACT_REJECTED,
            artifact_id=artifact_id,
            actor=actor,
            payload={"reason": reason, "stage": "execution_gate"},
        )
        self.ledger.append(event)

    def _emit_execution_event(
        self,
        artifact_id: str,
        execution_id: str,
        phase: str,
        handler_id: str,
        status: str,
        *,
        attempt: int = 0,
        plan_step_id: str | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
        duration_ms: float | None = None,
        resources: dict[str, Any] | None = None,
        error_type: str | None = None,
        error: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Emit an execution.logged event with full context."""
        from ..artifact.events import EXECUTION_LOGGED, create_event

        payload: dict[str, Any] = {
            "execution_id": execution_id,
            "attempt": attempt,
            "phase": phase,
            "status": status,
            "handler_id": handler_id,
        }

        # Optional fields
        if plan_step_id:
            payload["plan_step_id"] = plan_step_id
        if started_at:
            payload["started_at"] = started_at
        if ended_at:
            payload["ended_at"] = ended_at
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        if resources:
            payload["resources"] = resources
        if error_type:
            payload["error_type"] = error_type
        if error:
            # Truncate error message to prevent bloat
            payload["error"] = error[:500] if len(error) > 500 else error
        if reason:
            payload["reason"] = reason

        event = create_event(
            EXECUTION_LOGGED,
            artifact_id=artifact_id,
            actor="harness",
            payload=payload,
        )
        self.ledger.append(event)

    def _run_phase(
        self,
        artifact_id: str,
        execution_id: str,
        phase: str,
        handler_id: str,
        fn: callable,
        *,
        attempt: int = 0,
        enable_logging: bool = True,
    ) -> Any:
        """
        Run a phase with automatic event emission.

        Emits started/completed/failed automatically, handles exceptions.
        Returns the result of fn().
        """
        import time

        if not enable_logging:
            # Emit single suppressed event
            self._emit_execution_event(
                artifact_id, execution_id, phase, handler_id,
                "skipped", attempt=attempt, reason="logging_disabled"
            )
            return fn()

        # Emit started
        started_at = datetime.now(timezone.utc).isoformat()
        self._emit_execution_event(
            artifact_id, execution_id, phase, handler_id,
            "started", attempt=attempt, started_at=started_at
        )

        start_time = time.time()

        try:
            result = fn()

            # Emit completed
            ended_at = datetime.now(timezone.utc).isoformat()
            duration = (time.time() - start_time) * 1000

            # Extract metrics if available
            resources = None
            if hasattr(result, "metrics"):
                from .handler import ExecutionMetrics
                if isinstance(result.metrics, ExecutionMetrics):
                    resources = result.metrics.to_dict()

            self._emit_execution_event(
                artifact_id, execution_id, phase, handler_id,
                "completed", attempt=attempt,
                started_at=started_at, ended_at=ended_at,
                duration_ms=duration,
                resources=resources
            )

            return result

        except Exception as e:
            # Emit failed
            ended_at = datetime.now(timezone.utc).isoformat()
            duration = (time.time() - start_time) * 1000

            self._emit_execution_event(
                artifact_id, execution_id, phase, handler_id,
                "failed", attempt=attempt,
                started_at=started_at, ended_at=ended_at,
                duration_ms=duration,
                error_type=type(e).__name__,
                error=str(e)
            )

            raise

    def _emit_bundle(
        self,
        plan_id: str,
        approval_id: str | None,
        result_id: str,
        operation: str,
        actor: str,
        surface: str,
    ) -> str:
        """Emit a bundle@v1 artifact with repro header."""
        # Load active rulesets and vault state
        active_rulesets = self._load_active_rulesets()
        vault_state = self._capture_vault_state()

        manifest: dict[str, Any] = {
            "version": "bundle@v1",
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "artifacts": {
                "plan": plan_id,
                "approval": approval_id,
                "result": result_id,
            },
            "repro": {
                "rulesets": active_rulesets,
                "inputs_snapshot": vault_state,
                "surface": surface,
                "engine_version": _get_engine_version(),
                "environment": _get_environment(),
            },
        }

        content_id = self.content_store.store(manifest)
        bundle_id = new_ulid()

        event = create_event(
            ARTIFACT_CREATED,
            artifact_id=bundle_id,
            actor=actor,
            payload={
                "risk_class": RiskClass.APPEND_ONLY.value,
                "operation": "bundle.emit",
                "inputs": [
                    {"artifact_id": plan_id, "content_id": ""},
                    {"artifact_id": result_id, "content_id": ""},
                ],
            },
            content_id=content_id,
            artifact_type="bundle",
        )
        self.ledger.append(event)

        self.console.print(f"bundle_id: {bundle_id}", style="dim")
        return bundle_id

    def _extract_erasure(self, content: dict[str, Any]) -> ErasureCost:
        """Extract ErasureCost from result content."""
        ec = content.get("erasure_cost", {})
        if not isinstance(ec, dict):
            return ErasureCost()
        return ErasureCost(
            notes=ec.get("notes", 0),
            edges=ec.get("edges", 0),
            files=ec.get("files", 0),
            bytes_erased=ec.get("bytes_erased", 0),
            details=ec.get("details", {}),
        )

    def _extract_creation(self, content: dict[str, Any]) -> CreationSummary:
        """Extract CreationSummary from result content."""
        cs = content.get("creation_summary", {})
        if not isinstance(cs, dict):
            return CreationSummary()
        return CreationSummary(
            notes=cs.get("notes", 0),
            edges=cs.get("edges", 0),
            files=cs.get("files", 0),
            bytes_written=cs.get("bytes_written", 0),
            details=cs.get("details", {}),
        )

    def _capture_vault_state(self) -> dict[str, Any]:
        """Capture current vault state for reproducibility."""
        try:
            from ..vault.loader import load_vault

            vault = load_vault(self.vault_path)
            concept_count = len(vault.concepts)
            link_count = sum(len(c.links_to) for c in vault.concepts)
        except Exception:
            # If vault loading fails, return minimal state
            concept_count = 0
            link_count = 0

        # Compute content hash
        vault_sha256 = _hash_vault_content(self.vault_path)

        return {
            "concept_count": concept_count,
            "link_count": link_count,
            "vault_sha256": vault_sha256,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _validate_with_constraints(
        self,
        plan_artifact_id: str,
        active_rulesets: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Run constraint validation and emit events.

        Returns constraint_results dict for inclusion in validation event.
        """
        if not active_rulesets:
            return None

        try:
            from ..constraints.engine import run_constraints_lint
            from ..constraints.load import load_ruleset
            from ..vault.loader import load_vault
            from ..vault.graph import DependencyGraph

            # Load vault and graph
            vault = load_vault(self.vault_path)
            graph = DependencyGraph.from_concepts(vault.concepts)

            # Load first active ruleset
            ruleset_info = active_rulesets[0]
            ruleset_path = self.vault_path.parent / ruleset_info["path"]

            if not ruleset_path.exists():
                return None

            ruleset = load_ruleset(ruleset_path)

            # Run constraints with event emission
            lint_results = run_constraints_lint(
                self.vault_path,
                vault=vault,
                graph=graph,
                ruleset=ruleset,
                artifact_id=plan_artifact_id,
                emit_events=True,  # Enable event emission
            )

            # Count invariants
            invariants_checked = set(r.invariant for r in ruleset.rules if r.invariant)
            invariants_verified = []
            for inv_id in invariants_checked:
                violations = [r for r in lint_results if r.invariant == inv_id and r.level == "error"]
                invariants_verified.append({
                    "id": inv_id,
                    "status": "fail" if violations else "pass",
                })

            # Build constraint_results summary
            violations = [
                {
                    "rule_id": r.invariant or "unclassified",
                    "severity": r.level,
                    "message": r.message,
                    "item_id": getattr(r, "concept_id", None) or str(r.file),
                }
                for r in lint_results
                if r.level == "error"
            ]

            return {
                "rulesets_evaluated": [ruleset.ruleset_id],
                "rules_checked": len(ruleset.rules),
                "rules_passed": len(ruleset.rules) - len([r for r in lint_results if r.level == "error"]),
                "rules_failed": len([r for r in lint_results if r.level == "error"]),
                "invariants_verified": invariants_verified,
                "violations": violations,
            }

        except Exception as e:
            # If constraint validation fails, log but don't block
            self.console.print(f"[yellow]Warning: Constraint validation failed: {e}[/yellow]")
            return None

    def _load_active_rulesets(self) -> list[dict[str, Any]]:
        """Load active rulesets for current operation."""
        rulesets = []

        # Look for rulesets in standard locations
        possible_locations = [
            self.vault_path.parent / "meta" / "rulesets" / "core.toml",
            self.vault_path / "meta" / "rulesets" / "core.toml",
            self.irrev_dir.parent / "content" / "meta" / "rulesets" / "core.toml",
        ]

        for ruleset_path in possible_locations:
            if ruleset_path.exists():
                try:
                    from ..constraints.load import load_ruleset

                    ruleset = load_ruleset(ruleset_path)
                    rulesets.append({
                        "id": ruleset.ruleset_id,
                        "version": ruleset.version,
                        "content_id": _hash_file(ruleset_path),
                        "path": str(ruleset_path.relative_to(self.vault_path.parent)),
                    })
                    break  # Only load first found ruleset
                except Exception:
                    # If loading fails, continue to next location
                    continue

        return rulesets
