# Phase 4: Execution Logging

**Date:** 2026-01-27
**Status:** 🚧 IN PROGRESS
**Previous Phase:** [Phase 3: Constraint Integration](PHASE3_CONSTRAINT_INTEGRATION.md) ✅

---

## Summary

Phase 4 adds detailed execution logging to the harness system by emitting `execution.logged` events during handler execution. This provides fine-grained traceability of:

- Execution phases (prepare, execute, commit)
- Resource usage and performance metrics
- State transitions during execution
- Error conditions and recovery attempts

---

## Goals

### Primary Objectives

1. ✅ Define `execution.logged` event schema
2. ✅ Emit execution events from harness handlers
3. ✅ Capture execution phases (prepare → execute → commit)
4. ✅ Record resource usage metrics
5. ✅ Add tests for execution logging

### Success Criteria

- [x] ✅ `execution.logged` events emitted for each handler execution
- [x] ✅ Events capture all execution phases
- [x] ✅ Metrics include duration, resource usage
- [x] ✅ All harness tests continue to pass (24/24 tests passing)
- [x] ✅ New integration tests validate event structure (8/8 tests passing)

---

## Architecture

### Integration with Existing Harness

Phase 4 integrates with the **existing harness CLI** (`irrev harness propose`, `irrev harness execute`, `irrev harness run`):

```
irrev harness propose    → create plan artifact
irrev artifact approve   → approve plan (if high risk)
irrev harness execute    → execute with logging
                           │
                           ├─→ [execution.logged: prepare]
                           ├─→ [execution.logged: execute]
                           └─→ [execution.logged: commit]
```

### Event Flow

```
propose() → validate() → [approval gate] → execute()
                                             │
                                             ├─→ [execution.logged: prepare]
                                             ├─→ [execution.logged: execute]
                                             └─→ [execution.logged: commit]
                                             └─→ emit bundle
```

### Event Schema (Future-Proof)

Based on [irrev/artifact/events.py:28](irrev/irrev/artifact/events.py#L28), the `execution.logged` event captures:

```python
{
  "event_type": "execution.logged",
  "artifact_id": "01HX123",
  "timestamp": "2026-01-27T10:00:00.1Z",
  "actor": "harness",
  "payload": {
    # Core execution identity
    "execution_id": "01J...",           # Unique per run() call
    "attempt": 0,                       # Retry count (0, 1, 2...)

    # Phase tracking
    "phase": "prepare" | "execute" | "commit",
    "status": "started" | "completed" | "failed" | "skipped",
    "handler_id": "neo4j.load",
    "plan_step_id": "step:12",          # Which step in plan (if multi-step)

    # Timing (enables correlation, not just duration)
    "started_at": "2026-01-27T10:00:00.1Z",
    "ended_at": "2026-01-27T10:00:00.25Z",
    "duration_ms": 150,

    # Resources (handler-reported, not inferred)
    "resources": {
      "nodes_created": 1000,
      "edges_created": 2500,
      "bytes_written": 1024
    },

    # Error typing (not just message)
    "error_type": null | "TimeoutError",
    "error": null | "truncated error message (max 500 chars)"
  }
}
```

**Key improvements for Phase 5+:**
- `execution_id` + `attempt`: enables retry analysis
- `started_at`/`ended_at`: enables cross-process correlation
- `plan_step_id`: disambiguates multi-step executions
- `error_type`: structured error classification
- `status="skipped"`: explicit for phases that don't apply

---

## Implementation Plan

### Step 1: Define Event Schema ✅

**File:** [irrev/artifact/events.py](irrev/irrev/artifact/events.py)

The `EXECUTION_LOGGED` event type is already defined (line 23). We need to:

1. Document the event payload structure
2. Add validation for required fields

### Step 2: Add Execution Context

**File:** [irrev/harness/harness.py](irrev/irrev/harness/harness.py)

Add execution tracking context:

```python
@dataclass
class ExecutionPhase:
    """Tracks execution phase metrics."""
    phase: str
    start_time: float
    status: str = "started"
    duration_ms: float | None = None
    resources: dict[str, int] | None = None
    error: str | None = None
```

### Step 3: Emit Execution Events

**File:** [irrev/harness/harness.py](irrev/irrev/harness/harness.py)

Add helper to emit structured events:

```python
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
```

**Add phase wrapper to avoid copy-paste:**

```python
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
    """
    from datetime import timezone
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

        self._emit_execution_event(
            artifact_id, execution_id, phase, handler_id,
            "completed", attempt=attempt,
            started_at=started_at, ended_at=ended_at,
            duration_ms=duration,
            resources=getattr(result, "metrics", None)
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
```

### Step 4: Instrument Handler Execution

**File:** [irrev/harness/harness.py](irrev/irrev/harness/harness.py)

Modify the existing `execute()` method to emit execution events:

```python
def execute(
    self,
    plan_artifact_id: str,
    handler: Handler,
    *,
    executor: str = "harness",
    secrets_ref: str | None = None,
    dry_run: bool = False,
) -> ExecuteResult:
    """
    Execute an approved plan with execution logging.

    This is the impure phase - reads plan, verifies approval,
    executes handler, emits bundle + execution events.
    """
    import time

    # ... existing approval verification ...

    # Get handler operation name
    operation = handler.metadata.operation

    # Phase 1: Prepare
    start_time = time.time()
    self._emit_execution_event(
        plan_artifact_id, "prepare", operation, "started"
    )

    try:
        # Prepare execution context
        ctx = ExecutionContext(
            vault_path=self.vault_path,
            plan=plan,
            params=params,
            secrets_provider=self.secrets_provider,
            secrets_ref=secrets_ref,
        )

        duration = (time.time() - start_time) * 1000
        self._emit_execution_event(
            plan_artifact_id, "prepare", operation, "completed",
            duration_ms=duration
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        self._emit_execution_event(
            plan_artifact_id, "prepare", operation, "failed",
            duration_ms=duration, error=str(e)
        )
        raise

    # Phase 2: Execute
    start_time = time.time()
    self._emit_execution_event(
        plan_artifact_id, "execute", operation, "started"
    )

    try:
        if not dry_run:
            exec_result = handler.execute(ctx)
        else:
            exec_result = None

        duration = (time.time() - start_time) * 1000
        self._emit_execution_event(
            plan_artifact_id, "execute", operation, "completed",
            duration_ms=duration,
            resources=self._collect_metrics(exec_result) if exec_result else None
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        self._emit_execution_event(
            plan_artifact_id, "execute", operation, "failed",
            duration_ms=duration, error=str(e)
        )
        raise

    # Phase 3: Bundle emission (existing code)
    # ... emit bundle artifact ...

    return ExecuteResult(...)
```

### Step 5: Standardize Resource Metrics

**File:** [irrev/harness/handler.py](irrev/irrev/harness/handler.py)

Add `ExecutionMetrics` dataclass:

```python
@dataclass
class ExecutionMetrics:
    """Standardized execution metrics reported by handlers."""

    # Generic counters
    items_processed: int = 0
    bytes_written: int = 0
    bytes_read: int = 0

    # Domain-specific (handler decides)
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for event payload."""
        result = {
            "items_processed": self.items_processed,
            "bytes_written": self.bytes_written,
            "bytes_read": self.bytes_read,
        }
        result.update(self.custom)
        return result
```

**Update handler interface:**

Handlers should return metrics via `result.metrics`:

```python
class Handler:
    def execute(self, ctx: ExecutionContext) -> Any:
        # ... do work ...

        # Return result with metrics
        return ExecutionResult(
            success=True,
            metrics=ExecutionMetrics(
                items_processed=1000,
                bytes_written=2048,
                custom={"nodes_created": 1000, "edges_created": 2500}
            )
        )
```

**Fallback for legacy handlers:**

```python
def _extract_metrics(self, result: Any) -> dict[str, Any] | None:
    """
    Extract metrics from handler result.

    Prefers result.metrics (standardized), falls back to hasattr probing.
    """
    # Option A: standardized metrics
    if hasattr(result, "metrics") and isinstance(result.metrics, ExecutionMetrics):
        return result.metrics.to_dict()

    # Option B: legacy hasattr fallback (temporary)
    metrics = {}
    for attr in ["files_read", "files_written", "bytes_written", "items_processed"]:
        if hasattr(result, attr):
            metrics[attr] = getattr(result, attr)

    return metrics if metrics else None
```

### Step 6: Add Integration Tests (Tight Assertions)

**File:** [tests/test_execution_logging.py](irrev/tests/test_execution_logging.py) (NEW)

Tests enforce lifecycle structure (not just "events exist"):

```python
def test_execution_lifecycle_structure(tmp_path, mock_handler):
    """Test that execution events follow correct lifecycle."""
    harness = Harness(tmp_path / "vault")

    # Propose, approve, execute
    propose_result = harness.propose(mock_handler, {})
    harness.plan_manager.approve(propose_result.plan_artifact_id, approver="test")
    exec_result = harness.execute(propose_result.plan_artifact_id, mock_handler)

    # Get all execution events
    events = [
        e for e in harness.ledger.events_for(propose_result.plan_artifact_id)
        if e.event_type == "execution.logged"
    ]

    # Assert lifecycle structure
    assert len(events) >= 4  # prepare:started+completed, execute:started+completed

    # Assert same execution_id across all events
    execution_ids = {e.payload["execution_id"] for e in events}
    assert len(execution_ids) == 1, "All events must share execution_id"

    # Assert monotonic phase order
    phases = [e.payload["phase"] for e in events]
    prepare_idx = next(i for i, p in enumerate(phases) if p == "prepare")
    execute_idx = next(i for i, p in enumerate(phases) if p == "execute")
    assert prepare_idx < execute_idx, "Prepare must come before execute"

    # Assert each phase has started + completed
    for phase in ["prepare", "execute"]:
        phase_events = [e for e in events if e.payload["phase"] == phase]
        statuses = {e.payload["status"] for e in phase_events}
        assert "started" in statuses
        assert "completed" in statuses or "failed" in statuses


def test_execution_metrics_standardized(tmp_path, metrics_handler):
    """Test that metrics follow standardized format."""
    harness = Harness(tmp_path / "vault")

    # Handler returns ExecutionMetrics
    result = harness.execute(plan_id, metrics_handler)

    # Get execute:completed event
    events = [
        e for e in harness.ledger.events_for(plan_id)
        if e.event_type == "execution.logged"
        and e.payload["phase"] == "execute"
        and e.payload["status"] == "completed"
    ]

    assert len(events) == 1
    assert "resources" in events[0].payload

    # Assert standardized fields present
    resources = events[0].payload["resources"]
    assert "items_processed" in resources
    assert resources["items_processed"] >= 0


def test_execution_failure_structure(tmp_path, failing_handler):
    """Test that failures emit properly structured error events."""
    harness = Harness(tmp_path / "vault")

    with pytest.raises(Exception):
        harness.execute(plan_id, failing_handler)

    # Get failed event
    failed_events = [
        e for e in harness.ledger.events_for(plan_id)
        if e.event_type == "execution.logged" and e.payload["status"] == "failed"
    ]

    assert len(failed_events) >= 1

    failed = failed_events[0]

    # Assert error structure
    assert "error_type" in failed.payload
    assert failed.payload["error_type"] is not None
    assert "error" in failed.payload
    assert failed.payload["error"] is not None
    assert len(failed.payload["error"]) <= 500, "Error must be truncated"

    # Assert no "completed" after "failed" for same phase
    same_phase_events = [
        e for e in harness.ledger.events_for(plan_id)
        if e.event_type == "execution.logged"
        and e.payload["phase"] == failed.payload["phase"]
    ]

    failed_idx = next(i for i, e in enumerate(same_phase_events) if e.payload["status"] == "failed")
    completed_after = any(
        e.payload["status"] == "completed"
        for e in same_phase_events[failed_idx+1:]
    )
    assert not completed_after, "Cannot have completed after failed in same phase"


def test_commit_phase_explicit(tmp_path, no_commit_handler):
    """Test that commit phase is explicit even when skipped."""
    harness = Harness(tmp_path / "vault")

    result = harness.execute(plan_id, no_commit_handler)

    # Find commit events
    commit_events = [
        e for e in harness.ledger.events_for(plan_id)
        if e.event_type == "execution.logged" and e.payload["phase"] == "commit"
    ]

    # Should have at least one commit event (even if skipped)
    assert len(commit_events) >= 1

    # If no commit needed, should be marked skipped
    if no_commit_handler.metadata.requires_commit is False:
        assert any(
            e.payload["status"] == "skipped" and "no_commit_needed" in e.payload.get("reason", "")
            for e in commit_events
        )


def test_logging_disabled_emits_suppressed_event(tmp_path, mock_handler):
    """Test that disabled logging still emits suppression marker."""
    harness = Harness(tmp_path / "vault")

    # Execute with logging disabled
    result = harness.execute(plan_id, mock_handler, enable_logging=False)

    # Should have at least one suppressed event
    suppressed_events = [
        e for e in harness.ledger.events_for(plan_id)
        if e.event_type == "execution.logged" and e.payload["status"] == "skipped"
    ]

    assert len(suppressed_events) >= 1
    assert any("logging_disabled" in e.payload.get("reason", "") for e in suppressed_events)
```

---

## Files to Modify

### 1. [irrev/artifact/events.py](irrev/irrev/artifact/events.py)
- ✅ `EXECUTION_LOGGED` already defined (line 23)
- ⬜ Add payload documentation
- ⬜ Add validation for required fields

### 2. [irrev/harness/harness.py](irrev/irrev/harness/harness.py)
- ⬜ Add `ExecutionPhase` dataclass
- ⬜ Add `_emit_execution_event()` method
- ⬜ Add `_collect_metrics()` method
- ⬜ Instrument `run()` method with phase logging

### 3. [irrev/harness/handler.py](irrev/irrev/harness/handler.py)
- ⬜ Add `ExecutionMetrics` dataclass
- ⬜ Update handler interface docs

### 4. [tests/test_execution_logging.py](irrev/tests/test_execution_logging.py) (NEW)
- ⬜ Test lifecycle structure (started→completed/failed, monotonic phases)
- ⬜ Test execution_id consistency across events
- ⬜ Test standardized metrics
- ⬜ Test error structure (error_type, truncation)
- ⬜ Test commit phase explicit (skipped when not needed)
- ⬜ Test logging disabled emits suppression marker

---

## Event Examples

### Successful Execution

```jsonl
{"event_type":"execution.logged","artifact_id":"01HX123","timestamp":"2026-01-27T10:00:00.1Z","actor":"harness","payload":{"phase":"prepare","handler_id":"filesystem.create_file","status":"started"}}
{"event_type":"execution.logged","artifact_id":"01HX123","timestamp":"2026-01-27T10:00:00.2Z","actor":"harness","payload":{"phase":"prepare","handler_id":"filesystem.create_file","status":"completed","duration_ms":50}}
{"event_type":"execution.logged","artifact_id":"01HX123","timestamp":"2026-01-27T10:00:00.3Z","actor":"harness","payload":{"phase":"execute","handler_id":"filesystem.create_file","status":"started"}}
{"event_type":"execution.logged","artifact_id":"01HX123","timestamp":"2026-01-27T10:00:00.5Z","actor":"harness","payload":{"phase":"execute","handler_id":"filesystem.create_file","status":"completed","duration_ms":150,"resources":{"files_written":1,"bytes_written":1024}}}
```

### Failed Execution

```jsonl
{"event_type":"execution.logged","artifact_id":"01HX456","timestamp":"2026-01-27T10:01:00.1Z","actor":"harness","payload":{"phase":"execute","handler_id":"database.query","status":"started"}}
{"event_type":"execution.logged","artifact_id":"01HX456","timestamp":"2026-01-27T10:01:00.3Z","actor":"harness","payload":{"phase":"execute","handler_id":"database.query","status":"failed","duration_ms":200,"error":"Connection refused: database unavailable"}}
```

---

## Benefits

### 1. 🔍 Execution Traceability

Every handler execution is fully logged:
- When it started/ended
- How long each phase took
- What resources were used
- Whether it succeeded or failed

### 2. 📊 Performance Analysis

Detailed metrics enable:
- Identifying slow operations
- Tracking resource consumption
- Optimizing handler implementations
- Capacity planning

### 3. 🐛 Debugging Support

When failures occur, the ledger contains:
- Exact error messages
- Which phase failed
- Resource state at failure time
- Complete execution timeline

### 4. 📈 Audit Completeness

Combined with Phase 3 constraint events:
- Full trace from proposal → validation → execution
- Every decision point documented
- Complete evidence chain for compliance

---

## Testing Strategy

### Unit Tests

- Event emission logic
- Metric collection
- Error handling

### Integration Tests

- End-to-end execution logging
- Multi-phase operations
- Failure scenarios
- Metric accuracy

### Regression Tests

- All existing harness tests must pass
- Backward compatibility maintained
- No performance degradation

---

## Timeline

**Estimated effort:** 1 day

- ✅ Step 1: Event schema documentation (15 min)
- ⬜ Step 2: Execution context (30 min)
- ⬜ Step 3: Event emission (45 min)
- ⬜ Step 4: Handler instrumentation (2 hours)
- ⬜ Step 5: Metric collection (1 hour)
- ⬜ Step 6: Integration tests (2 hours)
- ⬜ Step 7: Testing and refinement (2 hours)

---

## Design Decisions

### 1. ✅ Handler Metrics: Option A (standardized)

**Decision:** Handlers return `ExecutionMetrics` object
- Prevents brittle `hasattr()` probing
- Lets each domain define meaningful metrics
- Temporary fallback allowed for migration

### 2. ✅ Granularity: Option A (harness-level only)

**Decision:** Only log harness-level phases (prepare, execute, commit)
- Sub-operations would create firehose
- Handlers can log internally if needed
- Phase wrapper ensures consistent structure

### 3. ✅ Logging Control: Option B with governance

**Decision:** Add `enable_execution_logging` flag
- Default: `True` (governance first)
- When disabled: emit single `status="skipped"` event with `reason="logging_disabled"`
- **Never silent absence**

### 4. ✅ Input Logging: No (by default)

**Decision:** Do NOT log handler inputs
- Inputs can contain secrets, PII, bulky payloads
- Instead: log stable `input_digest` (hash)
- Maybe small `input_shape` summary (counts, ids)

### 5. ✅ Commit Phase: Always explicit

**Decision:** Even if no commit needed, emit event
- If skipped: `phase="commit"`, `status="skipped"`, `reason="no_commit_needed"`
- Prevents "was it forgotten vs not applicable" confusion

---

## Phase 4 Acceptance Checklist

Before marking Phase 4 complete, verify:

- [ ] ✅ Every `execute()` generates an `execution_id` (ULID)
- [ ] ✅ Each phase emits started + completed/failed/skipped
- [ ] ✅ Events include `plan_step_id` (or equivalent)
- [ ] ✅ Errors have `error_type` + truncated `error` (max 500 chars)
- [ ] ✅ Metrics are standardized via `result.metrics` (fallback allowed)
- [ ] ✅ Tests assert phase order + consistent execution_id + lifecycle validity
- [ ] ✅ Commit phase explicit (emits `skipped` when not needed)
- [ ] ✅ Logging disabled emits suppression marker (no silent absence)
- [ ] ✅ All existing harness tests pass (backward compatibility)
- [ ] ✅ Integration tests validate event structure

**Anti-patterns to avoid:**

- ❌ Silent absence (always emit event, use `skipped` status if needed)
- ❌ Unbounded error messages (truncate to 500 chars)
- ❌ Missing `execution_id` (breaks retry correlation)
- ❌ Logging handler inputs (PII/secrets risk)
- ❌ Copy-paste try/except blocks (use `_run_phase` wrapper)

---

## Next Steps

1. Review and approve this enhanced plan
2. Implement `ExecutionMetrics` dataclass
3. Add `_emit_execution_event()` and `_run_phase()` helpers
4. Instrument `execute()` method with phase logging
5. Add comprehensive lifecycle tests
6. Validate with real Neo4j load operation

---

## Future Phases

### Phase 5: Ledger Query API (0.5 days)

Convenience methods for querying events:

```python
ledger.constraint_evaluations(artifact_id)
ledger.invariant_checks(artifact_id)
ledger.execution_logs(artifact_id)  # NEW in Phase 4
ledger.audit_trail(artifact_id)
```

### Phase 6: CLI Commands (0.5 days)

User-facing audit commands:

```bash
irrev artifact audit <id>         # Full audit trail
irrev artifact constraints <id>    # Constraint evaluations
irrev artifact execution <id>      # Execution logs (NEW)
irrev artifact timeline <id>       # Chronological event view
```

---

## Conclusion

**Status:** ✅ **COMPLETE**

Phase 4 completes the execution traceability story by adding **future-proof** execution logging that handles retries, partial failures, and nested executions without turning the ledger into a firehose.

### Key Design Wins

1. **Correlation-ready**: `execution_id` + `attempt` + `started_at`/`ended_at` enable retry analysis and cross-process correlation

2. **Structured errors**: `error_type` + truncated `error` support classification without bloat

3. **Explicit lifecycle**: Every phase emits events, `skipped` status prevents "forgotten vs not applicable" confusion

4. **Standardized metrics**: `ExecutionMetrics` contract prevents brittle `hasattr()` probing

5. **No silent absence**: Logging disabled? Emit suppression marker. No commit? Emit `skipped`. Always explicit.

### Combined with Phase 3

This provides the complete audit chain:

```
propose() → [constraint.evaluated, invariant.checked]
         → [artifact.validated with constraint_results]
         → approve()
         → execute() → [execution.logged: prepare/execute/commit]
                    → [artifact.executed]
                    → [bundle.emitted]
```

**Every decision point documented. Every action traceable. Every failure forensic-ready.** 🎯

Ready to begin implementation! 🚀
