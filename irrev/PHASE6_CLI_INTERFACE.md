# Phase 6: CLI Interface for Artifact Queries

**Date:** 2026-01-27
**Status:** 🚧 IN PROGRESS
**Previous Phase:** [Phase 5: Ledger Query API](PHASE5_QUERY_API_COMPLETE.md) ✅

---

## Objective

Implement user-facing CLI commands that expose the Phase 5 query API as formatted terminal output. Each command is pure formatting over ledger query methods - no complex logic in CLI layer.

---

## Design Principles

### 1. Thin CLI Layer
- CLI commands are **pure formatters** over `ledger.query()` and convenience methods
- No business logic in CLI - all computation in ledger layer
- Each command: call query method → format results → display

### 2. Consistent Output Style
- Use `rich` library for tables and formatted output
- Consistent column ordering and styling across commands
- Support `--json` flag for machine-readable output
- Use stderr for diagnostics, stdout for data

### 3. Error Handling
- Clear error messages for missing artifacts
- Explicit handling of "no data" vs "empty results"
- Use `constraint_data_status` to show appropriate messages

---

## Commands to Implement

### 1. `irrev artifact audit <id>`

**Purpose:** Show full chronological audit trail for an artifact (lifecycle + governance + execution)

**API Call:**
```python
ledger.audit_trail(artifact_id)
```

**Output Format:**
```
Audit Trail: plan-abc123

Timestamp            Event Type              Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2026-01-27 10:00:00  artifact.created        status=created
2026-01-27 10:00:01  constraint.evaluated    ruleset=core, result=allow
2026-01-27 10:00:01  invariant.checked       invariant=content_exists, status=ok
2026-01-27 10:00:02  artifact.validated      status=validated
2026-01-27 10:05:00  artifact.approved       approver=human:alice
2026-01-27 10:10:00  execution.logged        phase=prepare, status=success
2026-01-27 10:10:05  execution.logged        phase=execute, status=success
2026-01-27 10:10:06  execution.logged        phase=commit, status=success
2026-01-27 10:10:06  artifact.executed       status=executed

Events: 9 total
```

**Options:**
- `--json` - Output raw events as JSON array

---

### 2. `irrev artifact execution <id>`

**Purpose:** Show execution logs for an artifact (all executions or specific execution_id)

**API Call:**
```python
ledger.execution_logs(artifact_id=artifact_id)
# or
ledger.execution_logs(execution_id=execution_id)
```

**Output Format:**
```
Execution Logs: plan-abc123

Execution ID    Phase      Status    Handler              Duration    Resources
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
exec-001        prepare    success   vault.mutation       0.5s        cpu=10%, mem=50MB
exec-001        execute    success   vault.mutation       2.3s        cpu=25%, mem=100MB
exec-001        commit     success   vault.mutation       0.2s        cpu=5%, mem=20MB

Executions: 1 total, 1 successful
```

**Options:**
- `--execution-id <id>` - Filter to specific execution
- `--phase <phase>` - Filter to specific phase (prepare|execute|commit)
- `--status <status>` - Filter to specific status (success|failure|skipped)
- `--json` - Output raw logs as JSON array

---

### 3. `irrev artifact constraints <id>`

**Purpose:** Show constraint evaluations and invariant checks for an artifact

**API Call:**
```python
ledger.constraint_evaluations(artifact_id)
ledger.invariant_checks(artifact_id)
```

**Output Format:**
```
Constraints: plan-abc123

Constraint Evaluations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruleset    Invariant          Result    Reason
core       no_destructive     allow     operation=create_note
core       approval_required  allow     risk_class=low

Invariant Checks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Invariant           Status    Violations
content_exists      ok        0
metadata_valid      ok        0

Summary: 2 evaluations (2 allow, 0 deny), 2 checks (2 ok, 0 violated)
```

**Special Cases:**
- If `constraint_data_status == "missing"`:
  ```
  Constraints: plan-abc123

  ℹ No constraint data (artifact predates Phase 3)
  ```
- If `constraint_data_status == "partial"`:
  ```
  Constraints: plan-abc123

  ⚠ Partial constraint data (some rulesets not logged)

  [show available data]
  ```

**Options:**
- `--ruleset <id>` - Filter to specific ruleset
- `--result <allow|deny|error>` - Filter constraint evaluations by result
- `--status <ok|violated>` - Filter invariant checks by status
- `--json` - Output raw evaluations/checks as JSON

---

### 4. `irrev artifact timeline <id>`

**Purpose:** Condensed chronological view (one line per event)

**API Call:**
```python
ledger.audit_trail(artifact_id)
```

**Output Format:**
```
Timeline: plan-abc123

10:00:00  ● created
10:00:01  ✓ constraints passed (core: allow)
10:00:02  ● validated
10:05:00  ✓ approved (human:alice)
10:10:00  ▸ execution started (exec-001)
10:10:05    prepare → execute → commit
10:10:06  ✓ executed

Status: executed | Duration: 10m 6s | Events: 9
```

**Options:**
- `--full` - Show full timestamps (not condensed)
- `--json` - Output events as JSON array

---

### 5. `irrev artifact summary <id>`

**Purpose:** Combined execution + constraint summary (high-level overview)

**API Call:**
```python
ledger.execution_summary(execution_id)  # Need to find execution_id first
ledger.constraint_summary(artifact_id)
ledger.invariant_summary(artifact_id)
```

**Output Format:**
```
Summary: plan-abc123

Execution Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execution ID:     exec-001
Overall Status:   success
Total Duration:   3.0s
Phases:           prepare (0.5s) → execute (2.3s) → commit (0.2s)
Handler:          vault.mutation
Resources:        cpu=25% peak, mem=100MB peak

Constraint Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evaluations:      2 total (2 allow, 0 deny, 0 error)
Invariant Checks: 2 total (2 ok, 0 violated)
Data Status:      present

Lifecycle
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Created:          2026-01-27 10:00:00
Validated:        2026-01-27 10:00:02
Approved:         2026-01-27 10:05:00
Executed:         2026-01-27 10:10:06
```

**Special Cases:**
- If execution failed:
  ```
  Execution Summary
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Overall Status:   failure
  Failure Phase:    execute  ← handler implementation issue
  ...
  ```

**Options:**
- `--json` - Output summary as JSON object

---

## Implementation Plan

### Step 1: Implement CLI Functions (artifact_cmd.py)

Add five new functions to `irrev/commands/artifact_cmd.py`:

1. `run_artifact_audit(vault_path: Path, artifact_id: str, *, output_json: bool) -> int`
2. `run_artifact_execution(vault_path: Path, artifact_id: str, *, execution_id: str | None, phase: str | None, status: str | None, output_json: bool) -> int`
3. `run_artifact_constraints(vault_path: Path, artifact_id: str, *, ruleset: str | None, result: str | None, status: str | None, output_json: bool) -> int`
4. `run_artifact_timeline(vault_path: Path, artifact_id: str, *, full: bool, output_json: bool) -> int`
5. `run_artifact_summary(vault_path: Path, artifact_id: str, *, output_json: bool) -> int`

**Pattern:**
```python
def run_artifact_audit(vault_path: Path, artifact_id: str, *, output_json: bool = False) -> int:
    console = Console(stderr=True)
    mgr = _manager(vault_path)

    # Verify artifact exists
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        console.print(f"Artifact not found: {artifact_id}", style="bold red")
        return 1

    # Call query method
    events = mgr.ledger.audit_trail(artifact_id)

    if output_json:
        # JSON output to stdout
        print(json.dumps([e.__dict__ for e in events], indent=2, default=str))
        return 0

    # Rich formatted output to stderr
    table = Table(title=f"Audit Trail: {artifact_id}")
    table.add_column("Timestamp")
    table.add_column("Event Type")
    table.add_column("Details")

    for event in events:
        table.add_row(
            event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            event.event_type,
            _format_event_details(event),
        )

    console.print(table)
    console.print(f"\nEvents: {len(events)} total")
    return 0
```

### Step 2: Add CLI Command Registrations (cli.py)

Add five new `@artifact.command()` decorators:

```python
@artifact.command("audit")
@click.argument("artifact_id", type=str)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def artifact_audit(ctx: click.Context, artifact_id: str, output_json: bool) -> None:
    """Show full audit trail for an artifact."""
    sys.exit(run_artifact_audit(ctx.obj["vault"], artifact_id, output_json=output_json))
```

### Step 3: Write Tests

Create `tests/test_artifact_cli.py` with tests for:

1. Each command with valid artifact_id
2. Each command with missing artifact_id (error case)
3. Each command with --json flag
4. Filter options for execution/constraints commands
5. Special cases (missing constraint data, failed executions)

**Test structure:**
```python
def test_artifact_audit_command(tmp_path):
    # Setup: create ledger with events
    # Run: invoke CLI command
    # Assert: verify output format
    pass

def test_artifact_audit_json_output(tmp_path):
    # Setup: create ledger with events
    # Run: invoke CLI command with --json
    # Assert: verify JSON structure
    pass

def test_artifact_audit_not_found(tmp_path):
    # Run: invoke CLI command with invalid ID
    # Assert: verify error message and exit code
    pass
```

### Step 4: Integration Testing

Test end-to-end flows:
1. Create artifact → validate → approve → execute → audit (full lifecycle)
2. Create artifact with constraints → verify constraint display
3. Create artifact with failed execution → verify failure display

---

## Output Formatting Utilities

**Helper Functions:**

```python
def _format_event_details(event: ArtifactEvent) -> str:
    """Format event payload as compact key=value string."""
    if event.event_type == "artifact.created":
        return f"status={event.payload.get('status')}"
    elif event.event_type == "constraint.evaluated":
        return f"ruleset={event.payload.get('ruleset_id')}, result={event.payload.get('result')}"
    # ... etc
    return ""

def _format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"

def _format_timestamp_condensed(dt: datetime) -> str:
    """Format timestamp as HH:MM:SS for timeline view."""
    return dt.strftime("%H:%M:%S")

def _format_resources(resources: dict) -> str:
    """Format resource usage as compact string."""
    parts = []
    if "cpu_percent" in resources:
        parts.append(f"cpu={resources['cpu_percent']:.0f}%")
    if "memory_mb" in resources:
        parts.append(f"mem={resources['memory_mb']:.0f}MB")
    return ", ".join(parts)
```

---

## Success Criteria

✅ All five commands implemented and working
✅ Consistent output formatting with rich tables
✅ JSON output mode for all commands
✅ Error handling for missing artifacts
✅ Explicit handling of missing constraint data
✅ Filter options working (execution, constraints)
✅ Comprehensive tests (15+ tests covering all commands)
✅ No regressions in existing tests
✅ Documentation updated

---

## Testing Strategy

### Unit Tests (artifact_cmd.py functions)
- Test each `run_artifact_*()` function directly
- Mock ledger responses
- Verify output format and content

### Integration Tests (CLI commands)
- Use Click's testing utilities (`CliRunner`)
- Test full command invocation
- Verify exit codes and output

### End-to-End Tests
- Real ledger with populated events
- Full lifecycle: create → validate → approve → execute → query
- Verify consistency across all commands

---

## Implementation Checklist

### Core Implementation
- [ ] `run_artifact_audit()` function
- [ ] `run_artifact_execution()` function
- [ ] `run_artifact_constraints()` function
- [ ] `run_artifact_timeline()` function
- [ ] `run_artifact_summary()` function
- [ ] Helper formatting functions

### CLI Registration
- [ ] `@artifact.command("audit")` decorator
- [ ] `@artifact.command("execution")` decorator
- [ ] `@artifact.command("constraints")` decorator
- [ ] `@artifact.command("timeline")` decorator
- [ ] `@artifact.command("summary")` decorator

### Tests
- [ ] `test_artifact_audit_*` (3 tests)
- [ ] `test_artifact_execution_*` (5 tests)
- [ ] `test_artifact_constraints_*` (5 tests)
- [ ] `test_artifact_timeline_*` (3 tests)
- [ ] `test_artifact_summary_*` (4 tests)

### Documentation
- [ ] Update CLI help text
- [ ] Add examples to README
- [ ] Document JSON output schemas

---

## Files to Modify

1. **irrev/commands/artifact_cmd.py** - Add 5 new CLI functions (~200 lines)
2. **irrev/cli.py** - Add 5 new command decorators (~50 lines)
3. **tests/test_artifact_cli.py** - NEW FILE - Comprehensive tests (~400 lines)

**Total:** ~650 lines of new code

---

## Risks and Mitigations

### Risk: Rich formatting is complex
**Mitigation:** Keep formatting simple, use tables for structured data, plain text for summaries

### Risk: JSON output schema drift
**Mitigation:** Use dataclass serialization, document schemas, add schema validation tests

### Risk: Missing constraint data confusion
**Mitigation:** Explicit `constraint_data_status` field, clear messages for each case

### Risk: Performance with large ledgers
**Mitigation:** Phase 5 indexes handle this, CLI just formats results (no additional cost)

---

## Next Phase (Phase 7)

After Phase 6 completes, Phase 7 will add:
- Saved query presets (execution success rate, constraint hotspots)
- Cross-artifact analytics (handler performance, risk distribution)
- Time-series views (execution trends over time)

Phase 6 provides the foundation for these analytics by exposing single-artifact queries.

---

**Estimated Implementation Time:** 4-6 hours
**Test Coverage Target:** 20+ tests
**Lines of Code:** ~650 lines

**Status:** 🚧 Ready to implement
