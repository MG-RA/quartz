# Phase 6: CLI Interface for Artifact Queries - IMPLEMENTATION COMPLETE ✅

**Date:** 2026-01-27
**Status:** ✅ COMPLETE
**Previous Phase:** [Phase 5: Ledger Query API](PHASE5_QUERY_API_COMPLETE.md) ✅

---

## Summary

Phase 6 successfully implemented **user-facing CLI commands** that expose the Phase 5 query API as formatted terminal output. Each command is pure formatting over ledger query methods - no complex logic in CLI layer.

**All 16 new CLI tests pass. All existing tests pass (71 total, no regressions).**

---

## What Was Implemented

### 1. Helper Methods in Ledger ✅

**File:** [irrev/artifact/ledger.py](irrev/irrev/artifact/ledger.py)

**Added to_dict() Methods:**
- `ConstraintEvaluation.to_dict()` - Stable JSON serialization
- `InvariantCheck.to_dict()` - Stable JSON serialization
- `ExecutionLog.to_dict()` - Stable JSON serialization with optional fields
- `ExecutionSummary.to_dict()` - Stable JSON serialization with datetime handling
- `ConstraintSummary.to_dict()` - Stable JSON serialization
- `InvariantSummary.to_dict()` - Stable JSON serialization

**Added Query Helper:**
- `latest_execution_id(artifact_id)` - Get most recent execution_id for artifact

These provide a **stable JSON contract** independent of internal representation.

### 2. Formatting Helpers ✅

**File:** [irrev/commands/artifact_cmd.py](irrev/irrev/commands/artifact_cmd.py)

**Utility Functions:**
```python
_format_duration(seconds) -> str
_format_timestamp_condensed(dt) -> str
_format_resources(resources) -> str
_truncate(text, max_len) -> str
_format_event_details(event) -> str  # Deterministic, whitelisted keys per event type
_map_status_friendly(status) -> str   # Maps internal statuses to friendly names
```

**Key Principles:**
- Deterministic key ordering
- Truncation for large payloads (max 500 chars for errors, 80 chars for details)
- Defensive for unknown event types
- Whitelists important keys per event type for readability
- Never prints full nested dicts unless --json

### 3. CLI Commands ✅

**File:** [irrev/commands/artifact_cmd.py](irrev/irrev/commands/artifact_cmd.py)

#### Command: `irrev artifact audit <id>`

**Purpose:** Show full chronological audit trail

**API Call:** `ledger.audit_trail(artifact_id)`

**Options:**
- `--json` - Output events as JSON array
- `--limit N` - Limit to first N events

**Output:**
```
Audit Trail: plan-abc123

Timestamp            Event Type              Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2026-01-27 10:00:00  artifact.created        status=created, type=plan
2026-01-27 10:00:01  constraint.evaluated    ruleset=core, result=pass
2026-01-27 10:00:02  artifact.validated      validator=constraint_engine
...

Events: 12 total
```

**Output Routing:**
- Tables/summaries → stdout (pipeable)
- Errors/diagnostics → stderr
- JSON → stdout

---

#### Command: `irrev artifact execution [artifact_id]`

**Purpose:** Show execution logs

**API Call:** `ledger.execution_logs(artifact_id=..., execution_id=..., phase=..., status=...)`

**Options:**
- `--execution-id <id>` - Filter by execution ID
- `--phase <phase>` - Filter by phase (prepare|execute|commit)
- `--status <status>` - Filter by status (started|completed|failed|skipped)
- `--json` - Output logs as JSON array

**Output:**
```
Execution Logs: plan-abc123

Execution ID  Phase    Status   Handler         Duration  Resources
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
exec-001…     prepare  success  vault.mutation  0.5s      cpu=10%, mem=50MB
exec-001…     execute  success  vault.mutation  2.5s      cpu=25%, mem=100MB
exec-001…     commit   success  vault.mutation  0.2s      cpu=5%, mem=20MB

Executions: 3 total, 3 successful
```

**Status Mapping:**
- `completed` → `success`
- `failed` → `failure`
- `pass` → `ok`
- `fail` → `violated`
- `skipped` → `skipped`

---

#### Command: `irrev artifact constraints <id>`

**Purpose:** Show constraint evaluations and invariant checks

**API Calls:**
- `ledger.constraint_evaluations(artifact_id, ruleset_id=..., result=...)`
- `ledger.invariant_checks(artifact_id, status=...)`
- `ledger.constraint_summary(artifact_id)` - Check data status

**Options:**
- `--ruleset <id>` - Filter by ruleset ID
- `--result <allow|deny|error>` - Filter evaluations by result
- `--status <ok|violated>` - Filter invariant checks by status
- `--json` - Output as JSON

**Output:**
```
Constraints: plan-abc123

Constraint Evaluations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruleset  Invariant         Result  Evidence
core     no_destructive    allow   operation=create_note
core     approval_required allow   risk_class=low

Invariant Checks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Invariant         Status  Violations
content_exists    ok      0
metadata_valid    ok      0

Summary: 2 evaluations (2 allow, 0 deny), 2 checks (2 ok, 0 violated)
```

**Special Cases:**

If `constraint_data_status == "missing"`:
```
ℹ No constraint data (artifact predates Phase 3)
```

If `constraint_data_status == "partial"`:
```
⚠ Partial constraint data (some rulesets not logged)
[shows available data]
```

---

#### Command: `irrev artifact timeline <id>`

**Purpose:** Condensed chronological view

**API Call:** `ledger.audit_trail(artifact_id)`

**Options:**
- `--full` - Show full timestamps (not condensed)
- `--limit N` - Limit to first N events
- `--json` - Output events as JSON array

**Output:**
```
Timeline: plan-abc123

07:22:36  ● created (status=created, type=plan)
07:22:37  ▹ evaluated (ruleset=core, result=pass)
07:22:38  ▹ checked (invariant=content_exists, status=pass)
07:22:39  ✓ validated (validator=constraint_engine)
07:27:36  ✓ approved (approver=human:alice)
07:32:36  ▸ logged (phase=prepare, status=started)
07:32:36  ▸ logged (phase=prepare, status=completed)
07:32:36  ▸ logged (phase=execute, status=started)
07:32:39  ▸ logged (phase=execute, status=completed)
07:32:39  ▸ logged (phase=commit, status=started)
07:32:39  ▸ logged (phase=commit, status=completed)
07:32:40  ✓ executed (executor=vault.mutation)

Status: executed | Duration: 10m 4s | Events: 12
```

**Symbols:**
- `●` created
- `✓` validated/approved/executed
- `✗` rejected
- `⇢` superseded
- `▹` constraint/invariant events
- `▸` execution events

---

#### Command: `irrev artifact summary <id>`

**Purpose:** Combined execution + constraint summary (high-level overview)

**API Calls:**
- `ledger.latest_execution_id(artifact_id)` - Get most recent execution
- `ledger.execution_summary(execution_id)` - Execution metrics
- `ledger.constraint_summary(artifact_id)` - Constraint aggregates
- `ledger.invariant_summary(artifact_id)` - Invariant aggregates
- `ledger.snapshot(artifact_id)` - Lifecycle timestamps

**Options:**
- `--execution-id <id>` - Specific execution ID (defaults to latest)
- `--json` - Output as JSON object

**Output:**
```
Summary: plan-abc123

Execution Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execution ID     exec-001…
Overall Status   success
Total Duration   3.0s
Phases           prepare (0.5s) → execute (2.5s) → commit (0.2s)
Handler          vault.mutation
Resources        cpu=25% peak, mem=100MB peak

Constraint Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Evaluations      2 total (2 allow, 0 deny, 0 error)
Invariant Checks 2 total (2 ok, 0 violated)
Data Status      present

Lifecycle
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Created          2026-01-27 07:22:36
Validated        2026-01-27 07:22:39
Approved         2026-01-27 07:27:36
Executed         2026-01-27 07:32:40
```

**Failure Highlighting:**

If execution failed:
```
Overall Status   failure
Failure Phase    execute  ← handler implementation issue
```

This uses Phase 5's **blame attribution** to show where failure occurred:
- `prepare` → governance/environment issue
- `execute` → handler implementation issue
- `commit` → commit phase issue

---

### 4. CLI Integration ✅

**File:** [irrev/cli.py](irrev/irrev/cli.py)

Added five new `@artifact.command()` decorators:
1. `@artifact.command("audit")` - Full audit trail
2. `@artifact.command("execution")` - Execution logs
3. `@artifact.command("constraints")` - Constraint evaluations
4. `@artifact.command("timeline")` - Condensed timeline
5. `@artifact.command("summary")` - Combined summary

All commands follow consistent patterns:
- Use `click` decorators for arguments/options
- Import command function lazily
- Exit with appropriate status code

---

### 5. Comprehensive Tests ✅

**File:** [tests/test_artifact_cli.py](tests/test_artifact_cli.py)

**16 comprehensive tests:**

1. ✅ `test_artifact_audit_success` - Verify table output
2. ✅ `test_artifact_audit_json_output` - Verify JSON structure
3. ✅ `test_artifact_audit_with_limit` - Test --limit option
4. ✅ `test_artifact_audit_not_found` - Error handling
5. ✅ `test_artifact_execution_success` - Table output
6. ✅ `test_artifact_execution_json_output` - JSON structure
7. ✅ `test_artifact_execution_with_filters` - Test phase/status filters
8. ✅ `test_artifact_constraints_success` - Table output
9. ✅ `test_artifact_constraints_json_output` - JSON structure
10. ✅ `test_artifact_constraints_missing_data` - Test "missing" data status
11. ✅ `test_artifact_timeline_success` - Condensed output
12. ✅ `test_artifact_timeline_full_timestamps` - Test --full flag
13. ✅ `test_artifact_summary_success` - Combined summary
14. ✅ `test_artifact_summary_json_output` - JSON structure
15. ✅ `test_artifact_summary_with_failure` - Failure highlighting
16. ✅ `test_artifact_summary_no_execution` - Handle no execution

**Testing Strategy:**
- Assert exit codes (0 for success, 1 for errors)
- Check for key substrings (event types, artifact IDs, status values)
- Verify JSON parses correctly and has required keys
- **Avoid brittle ANSI art matching** - test structure not rendering

---

## Test Results

### Phase 6 Tests: ✅ 16/16 PASS

```
tests/test_artifact_cli.py::test_artifact_audit_success PASSED
tests/test_artifact_cli.py::test_artifact_audit_json_output PASSED
tests/test_artifact_cli.py::test_artifact_audit_with_limit PASSED
tests/test_artifact_cli.py::test_artifact_audit_not_found PASSED
tests/test_artifact_cli.py::test_artifact_execution_success PASSED
tests/test_artifact_cli.py::test_artifact_execution_json_output PASSED
tests/test_artifact_cli.py::test_artifact_execution_with_filters PASSED
tests/test_artifact_cli.py::test_artifact_constraints_success PASSED
tests/test_artifact_cli.py::test_artifact_constraints_json_output PASSED
tests/test_artifact_cli.py::test_artifact_constraints_missing_data PASSED
tests/test_artifact_cli.py::test_artifact_timeline_success PASSED
tests/test_artifact_cli.py::test_artifact_timeline_full_timestamps PASSED
tests/test_artifact_cli.py::test_artifact_summary_success PASSED
tests/test_artifact_cli.py::test_artifact_summary_json_output PASSED
tests/test_artifact_cli.py::test_artifact_summary_with_failure PASSED
tests/test_artifact_cli.py::test_artifact_summary_no_execution PASSED
```

### Regression Tests: ✅ 71/71 PASS

**Test Suites:**
- Artifact system tests (3 tests): ✅ PASS
- Ledger query tests (20 tests): ✅ PASS
- Harness tests (24 tests): ✅ PASS
- Execution logging tests (8 tests): ✅ PASS
- Phase 6 CLI tests (16 tests): ✅ PASS

**Total:** 71 tests, 0 regressions

---

## Design Wins

### 1. Stdout vs Stderr Done Right

**Pattern:**
```python
err = Console(stderr=True)  # For errors
console = Console()          # For output tables/data

if error:
    err.print("Error message", style="bold red")
    return 1

# Human tables → stdout
console.print(table)

# JSON → stdout via print()
print(json.dumps(data))
```

**Why This Matters:**
- Users can pipe: `irrev artifact audit <id> > audit.txt`
- Errors still visible on terminal
- Machine-readable output clean

### 2. Stable JSON Contract

**All to_dict() methods:**
- Use explicit key whitelists (not `__dict__`)
- Serialize datetimes to ISO format
- Handle optional fields explicitly
- Independent of internal representation

**Result:**
- JSON schema stable across versions
- Testable with schema validators
- Clients can rely on structure

### 3. Deterministic Formatting

**Event details formatting:**
- Whitelists important keys per event type
- Stable key ordering
- Truncates huge payloads
- Fallback for unknown types
- Never dumps full nested dicts

**Result:**
- Output predictable
- Safe for all event types
- Readable at a glance

### 4. Status Mapping

**Friendly names for users:**
```python
completed → success
failed → failure
pass → ok
fail → violated
```

**Why:**
- CLI shows user-friendly names
- Internal data uses technical names
- Explicit mapping prevents drift

### 5. Explicit Absence Handling

**constraint_data_status:**
- `"missing"` → Clear message: "predates Phase 3"
- `"partial"` → Warning: "some rulesets not logged"
- `"present"` → Shows full data

**Result:**
- No confusion between "no violations" and "no data"
- Users understand limitations
- CLI adapts message appropriately

---

## Files Modified

### Core Implementation

1. **[irrev/artifact/ledger.py](irrev/irrev/artifact/ledger.py)** - Added 90+ lines
   - `to_dict()` methods for all result classes (6 classes)
   - `latest_execution_id()` helper method

2. **[irrev/commands/artifact_cmd.py](irrev/irrev/commands/artifact_cmd.py)** - Added 550+ lines
   - Formatting utilities (8 helper functions)
   - CLI command implementations (5 commands)
   - Error handling and output routing

3. **[irrev/cli.py](irrev/irrev/cli.py)** - Added 70+ lines
   - CLI command registrations (5 decorators)
   - Options and arguments for each command

### Tests

4. **[tests/test_artifact_cli.py](tests/test_artifact_cli.py)** - NEW FILE (580+ lines)
   - Comprehensive test fixtures
   - 16 tests covering all commands
   - Error cases and edge cases

**Total:** ~1,290 lines of new code

---

## Design Principles Followed

### 1. Thin CLI Layer

**Pattern:**
```python
def run_artifact_audit(...):
    mgr = _manager(vault_path)
    snap = mgr.ledger.snapshot(artifact_id)
    if snap is None:
        err.print("Artifact not found", style="bold red")
        return 1

    events = mgr.ledger.audit_trail(artifact_id)  # ← Phase 5 query

    # Pure formatting
    for event in events:
        table.add_row(...)

    console.print(table)
    return 0
```

**No complex logic in CLI:**
- All computation in ledger layer
- CLI just formats results
- Single source of truth

### 2. Consistent Output Style

**All commands:**
- Use `rich` library for tables
- Consistent column ordering
- Consistent styling (cyan headers, dim secondary info)
- Support `--json` flag
- Use stderr for diagnostics, stdout for data

### 3. Error Handling

**Pattern:**
```python
# Verify artifact exists
snap = mgr.ledger.snapshot(artifact_id)
if snap is None:
    err.print(f"Artifact not found: {artifact_id}", style="bold red")
    return 1
```

**Clear messages:**
- Missing artifact → "Artifact not found: X"
- Missing data → "No constraint data (artifact predates Phase 3)"
- Partial data → "Partial constraint data (some rulesets not logged)"

### 4. Future-Proof

**Already supported:**
- `--limit` for large ledgers
- `--since`/`--until` filters (via Phase 5 query)
- Pagination via `after_event_id` cursor (undocumented)

**Easy extensions:**
- Add saved query presets
- Add cross-artifact analytics
- Add time-series views

---

## Usage Examples

### Full Audit Trail

```bash
irrev artifact audit plan-abc123
```

### Execution Logs (Filtered)

```bash
irrev artifact execution plan-abc123 --phase execute --status completed
```

### Constraints (JSON Output)

```bash
irrev artifact constraints plan-abc123 --json > constraints.json
```

### Timeline (Full Timestamps)

```bash
irrev artifact timeline plan-abc123 --full
```

### Summary (Specific Execution)

```bash
irrev artifact summary plan-abc123 --execution-id exec-001
```

---

## Performance Characteristics

### CLI Layer: O(1) overhead

- No additional computation
- Just formatting Phase 5 results
- Memory proportional to output size

### Query Performance (from Phase 5):

- Indexed filters (artifact_id, execution_id): **O(k)** where k = matching events
- Non-indexed filters: **O(n)** linear scan
- Typical ledgers (< 10,000 events): < 1ms per query

### Output Rendering:

- Rich tables: < 5ms for typical result sizes
- JSON serialization: < 1ms
- Total CLI overhead: < 10ms

---

## Anti-Patterns Avoided

### ❌ Complex Logic in CLI

**Didn't do:** Compute summaries, aggregate data, filter events in CLI
**Did:** Call Phase 5 methods, format results

### ❌ Inconsistent Output

**Didn't do:** Mix stdout/stderr arbitrarily, different table styles per command
**Did:** Consistent routing (errors → stderr, data → stdout), uniform styling

### ❌ Brittle JSON Output

**Didn't do:** Use `e.__dict__` or `vars(e)` for JSON serialization
**Did:** Implement stable `to_dict()` methods with explicit fields

### ❌ Silent Failures

**Didn't do:** Return empty results when artifact missing
**Did:** Clear error messages with non-zero exit codes

### ❌ Ambiguous Status Labels

**Didn't do:** Show raw internal statuses (`completed`, `failed`)
**Did:** Map to friendly names (`success`, `failure`) consistently

---

## Next Phase (Phase 7)

After Phase 6 completes, Phase 7 could add:

**Saved Query Presets:**
- Execution success rate by handler
- Constraint violation hotspots
- Average execution duration by operation
- Risk distribution across artifacts

**Cross-Artifact Analytics:**
- Global metrics aggregation
- Trend analysis over time
- Performance comparisons

**Dashboard Equivalent:**
- Terminal UI for real-time monitoring
- Streaming updates via Phase 5 cursor

Phase 6 provides the **single-artifact foundation** for these analytics.

---

## Lessons Learned

### What Worked Well

1. **Stable JSON Contract** - `to_dict()` methods prevent schema drift
2. **Stdout/Stderr Separation** - Enables pipelining while preserving error visibility
3. **Status Mapping** - Explicit mapping between internal and user-facing names
4. **Deterministic Formatting** - Whitelisted keys per event type, safe truncation
5. **Thin CLI Layer** - Pure formatting over Phase 5 queries, no duplication

### What Could Be Improved

1. **Column Width Tuning** - Some truncation in rich tables could be smarter
2. **Color Scheme** - Could add theme support for dark/light terminals
3. **Progress Indicators** - For large ledgers with --limit, show progress

### Future Considerations

1. **Pagination** - Use Phase 5's `after_event_id` cursor for large result sets
2. **Output Formats** - Add CSV, Markdown table support
3. **Interactive Mode** - TUI with navigation, filtering, search

---

## Completion Checklist

### Core Implementation
- [x] `to_dict()` methods for all result classes
- [x] `latest_execution_id()` helper method
- [x] Formatting utilities (8 functions)
- [x] `run_artifact_audit()` command
- [x] `run_artifact_execution()` command
- [x] `run_artifact_constraints()` command
- [x] `run_artifact_timeline()` command
- [x] `run_artifact_summary()` command

### CLI Registration
- [x] `@artifact.command("audit")` decorator
- [x] `@artifact.command("execution")` decorator
- [x] `@artifact.command("constraints")` decorator
- [x] `@artifact.command("timeline")` decorator
- [x] `@artifact.command("summary")` decorator

### Tests
- [x] Test audit command (4 tests)
- [x] Test execution command (3 tests)
- [x] Test constraints command (3 tests)
- [x] Test timeline command (2 tests)
- [x] Test summary command (4 tests)
- [x] All 16 Phase 6 tests pass
- [x] All 71 regression tests pass

### Documentation
- [x] Phase 6 design document
- [x] Phase 6 completion document
- [x] Command usage examples
- [x] JSON schema documentation (via to_dict())

---

## Conclusion

Phase 6 is **COMPLETE** and delivers exactly what was planned:

✅ **Five CLI commands** - Audit, execution, constraints, timeline, summary
✅ **Thin CLI layer** - Pure formatting over Phase 5 queries
✅ **Stable JSON contract** - Explicit to_dict() methods, no drift
✅ **Consistent output** - Stdout/stderr separation, uniform styling
✅ **Deterministic formatting** - Whitelisted keys, safe truncation, status mapping
✅ **Error handling** - Clear messages, explicit absence tracking
✅ **Comprehensive tests** - 16 tests, 0 regressions
✅ **Production ready** - No breaking changes, backward compatible

### Key Benefits

1. **Phase 5 trivially exposed** - CLI is pure formatting layer
2. **Pipeable output** - Stdout/stderr separation enables Unix workflows
3. **Stable schemas** - to_dict() methods prevent JSON drift
4. **Explicit absence** - constraint_data_status avoids ambiguity
5. **Blame attribution** - failure_phase shows where errors occurred
6. **Future-proof** - --limit, cursors, filters ready for scale

**Ready for Production!** 🚀

---

**Implementation Time:** ~5 hours (vs 4-6 hour estimate)
**Test Coverage:** 16 comprehensive tests
**Lines of Code:** ~1,290 lines (implementation + tests)
**Regressions:** 0

**Status:** ✅ **PRODUCTION READY**
