# Ledger Enrichment Design

**Date:** 2026-01-26
**Author:** Claude Sonnet 4.5
**Status:** Design Proposal

---

## Problem Statement

The current ledger implementation captures basic artifact lifecycle events (created, validated, approved, executed, rejected), but lacks:

1. **Ruleset compliance tracking** - Which constraints were evaluated during planning?
2. **Invariant violations** - What invariants were checked and which failed?
3. **Rich metadata** - Contextual information about operations (vault state, dependencies, etc.)
4. **Execution traces** - Detailed logs of what happened during execution
5. **Constraint evaluation results** - Which rules passed/failed during validation

**Current State:**
```jsonl
{"event_type":"artifact.created","artifact_id":"01HX...","timestamp":"2026-01-26T12:00:00Z","actor":"agent:harness","payload":{"operation":"neo4j.load",...},"content_id":"abc123","artifact_type":"plan"}
{"event_type":"artifact.validated","artifact_id":"01HX...","timestamp":"2026-01-26T12:00:01Z","actor":"harness","payload":{"validator":"harness","errors":[]}}
```

**Missing Information:**
- What rulesets were active during validation?
- What constraints were checked?
- What invariants were verified?
- What was the vault state at the time?
- What dependencies were considered?

---

## Design Goals

1. **Audit Completeness** - Every operation must be fully reproducible from ledger
2. **Governance Transparency** - Which rules governed each decision
3. **Forensic Analysis** - Understand why operations succeeded/failed
4. **Constraint Traceability** - Link operations to constraint evaluations
5. **Backward Compatibility** - Existing ledger entries remain valid

---

## Proposed Enhancements

### 1. New Event Types

Add new event types to capture constraint evaluations:

```python
# New event types in events.py
CONSTRAINT_EVALUATED = "constraint.evaluated"
INVARIANT_CHECKED = "invariant.checked"
RULESET_APPLIED = "ruleset.applied"
EXECUTION_LOGGED = "execution.logged"
```

### 2. Enhanced Payload Structure

#### A. `artifact.created` Enhancement

**Current:**
```json
{
  "event_type": "artifact.created",
  "artifact_id": "01HX...",
  "payload": {
    "operation": "neo4j.load",
    "risk_class": "mutation_destructive",
    "inputs": []
  }
}
```

**Enhanced:**
```json
{
  "event_type": "artifact.created",
  "artifact_id": "01HX...",
  "payload": {
    "operation": "neo4j.load",
    "risk_class": "mutation_destructive",
    "inputs": [],

    // NEW: Context metadata
    "context": {
      "vault_state": {
        "concept_count": 1234,
        "link_count": 5678,
        "vault_sha256": "abc...def"  // Hash of vault content
      },
      "active_rulesets": [
        {"id": "core", "version": 1, "content_id": "sha256:..."}
      ],
      "surface": "cli",
      "engine_version": "0.1.0+git.abc123"
    },

    // NEW: Plan details
    "plan_metadata": {
      "predicted_erasure": {"notes": 100, "edges": 200},
      "predicted_outputs": ["neo4j:irrev"],
      "dependencies": ["vault:content", "neo4j:http://localhost:7474"]
    }
  }
}
```

#### B. `artifact.validated` Enhancement

**Current:**
```json
{
  "event_type": "artifact.validated",
  "payload": {
    "validator": "harness",
    "errors": []
  }
}
```

**Enhanced:**
```json
{
  "event_type": "artifact.validated",
  "payload": {
    "validator": "harness",
    "errors": [],

    // NEW: Constraint evaluation results
    "constraint_results": {
      "rulesets_evaluated": ["core"],
      "rules_checked": 15,
      "rules_passed": 15,
      "rules_failed": 0,
      "invariants_verified": [
        {"id": "decomposition", "status": "pass"},
        {"id": "irreversibility", "status": "pass"}
      ],
      "violations": []  // List of RuleDef violations if any
    }
  }
}
```

#### C. New: `constraint.evaluated` Event

Emitted when constraints are evaluated during planning:

```json
{
  "event_type": "constraint.evaluated",
  "artifact_id": "01HX...",  // Links to plan artifact
  "timestamp": "2026-01-26T12:00:01Z",
  "actor": "system:constraint_engine",
  "payload": {
    "ruleset_id": "core",
    "ruleset_version": 1,
    "rule_id": "canonical-form-exists",
    "rule_scope": "concept",
    "invariant": "decomposition",
    "result": "pass",
    "evidence": {
      "item_id": "concept:foo",
      "item_type": "concept",
      "message": null  // null if passed
    }
  }
}
```

#### D. New: `invariant.checked` Event

Emitted when invariants are verified:

```json
{
  "event_type": "invariant.checked",
  "artifact_id": "01HX...",
  "timestamp": "2026-01-26T12:00:02Z",
  "actor": "system:constraint_engine",
  "payload": {
    "invariant_id": "decomposition",
    "status": "pass",
    "rules_checked": 5,
    "violations": 0,
    "affected_items": ["concept:foo", "concept:bar"]
  }
}
```

#### E. New: `execution.logged` Event

Emitted during execution for detailed logging:

```json
{
  "event_type": "execution.logged",
  "artifact_id": "01HX...",  // Links to plan artifact
  "timestamp": "2026-01-26T12:00:03Z",
  "actor": "handler:neo4j",
  "payload": {
    "phase": "execute",  // "prepare" | "execute" | "commit" | "rollback"
    "message": "Loading 100 nodes to Neo4j database 'irrev'",
    "level": "info",  // "debug" | "info" | "warning" | "error"
    "metadata": {
      "batch_number": 1,
      "batch_size": 100,
      "progress": "100/1000"
    }
  }
}
```

#### F. `artifact.executed` Enhancement

**Current:**
```json
{
  "event_type": "artifact.executed",
  "payload": {
    "result_artifact_id": "01HY...",
    "erasure_cost": {"notes": 100, "edges": 200},
    "creation_summary": {"notes": 1000, "edges": 2000}
  }
}
```

**Enhanced:**
```json
{
  "event_type": "artifact.executed",
  "payload": {
    "result_artifact_id": "01HY...",
    "erasure_cost": {"notes": 100, "edges": 200, "bytes_erased": 50000},
    "creation_summary": {"notes": 1000, "edges": 2000, "bytes_written": 500000},

    // NEW: Execution details
    "execution_details": {
      "duration_ms": 1234,
      "phases": [
        {"name": "prepare", "duration_ms": 100},
        {"name": "execute", "duration_ms": 1000},
        {"name": "commit", "duration_ms": 134}
      ],
      "resource_usage": {
        "peak_memory_mb": 256,
        "network_bytes_sent": 1000000,
        "network_bytes_received": 50000
      }
    },

    // NEW: Post-execution validation
    "post_execution_checks": {
      "data_integrity": "pass",
      "constraint_violations": 0,
      "rollback_required": false
    }
  }
}
```

### 3. Bundle Enhancement

**Current bundle.repro:**
```json
{
  "repro": {
    "rulesets": [],  // TODO
    "inputs_snapshot": null,
    "surface": "cli",
    "engine_version": "0.1.0+git.abc123",
    "environment": {"python": "3.11", "platform": "linux"}
  }
}
```

**Enhanced bundle.repro:**
```json
{
  "repro": {
    // NEW: Active rulesets with content IDs
    "rulesets": [
      {
        "id": "core",
        "version": 1,
        "content_id": "sha256:...",
        "path": "content/meta/rulesets/core.toml"
      }
    ],

    // NEW: Input state snapshot
    "inputs_snapshot": {
      "vault_sha256": "abc...def",
      "concept_count": 1234,
      "link_count": 5678,
      "modified_concepts": ["foo.md", "bar.md"]  // If available from git
    },

    "surface": "cli",
    "engine_version": "0.1.0+git.abc123",
    "environment": {"python": "3.11", "platform": "linux"},

    // NEW: Reproducibility metadata
    "reproducibility": {
      "deterministic": true,
      "external_dependencies": [
        {"type": "neo4j", "uri": "http://localhost:7474", "database": "irrev"}
      ],
      "git_context": {
        "branch": "main",
        "commit": "abc123",
        "dirty": false
      }
    }
  }
}
```

---

## Implementation Plan

### Phase 1: Event Type Extensions (Non-Breaking)

1. Add new event types to `events.py`:
   - `CONSTRAINT_EVALUATED`
   - `INVARIANT_CHECKED`
   - `EXECUTION_LOGGED`

2. Update `EVENT_TYPES` frozenset
3. Update `EVENT_PAYLOAD_FIELDS` documentation
4. No breaking changes - existing code continues to work

**Files to modify:**
- `irrev/artifact/events.py`

### Phase 2: Harness Enrichment

1. **Capture vault state during `propose()`:**
   ```python
   def propose(self, handler, params, ...):
       # Compute vault state hash
       vault_state = self._capture_vault_state()

       # Load active rulesets
       active_rulesets = self._load_active_rulesets()

       # Enhanced plan payload
       plan_payload = {
           **params,
           "plan_summary": plan.summary(),
           "effect_summary": effect_summary.to_dict(),
           "context": {
               "vault_state": vault_state,
               "active_rulesets": active_rulesets,
               "surface": surface,
               "engine_version": _get_engine_version(),
           },
           "plan_metadata": {
               "predicted_erasure": effect_summary.predicted_erasure,
               "predicted_outputs": effect_summary.predicted_outputs,
           }
       }
   ```

2. **Emit constraint evaluation events during validation:**
   ```python
   def _validate_with_constraints(self, plan_artifact_id, ruleset):
       for rule in ruleset.rules:
           result = evaluate_rule(rule, context)

           # Emit constraint.evaluated event
           event = create_event(
               CONSTRAINT_EVALUATED,
               artifact_id=plan_artifact_id,
               actor="system:constraint_engine",
               payload={
                   "ruleset_id": ruleset.ruleset_id,
                   "rule_id": rule.id,
                   "invariant": rule.invariant,
                   "result": "pass" if result.is_ok else "fail",
                   "evidence": result.evidence,
               }
           )
           self.ledger.append(event)
   ```

3. **Emit execution logs during handler execution:**
   ```python
   class Handler:
       def execute(self, plan, context):
           # Emit execution.logged events
           self._log_execution(context.plan_artifact_id, "prepare", "Preparing Neo4j load")

           # Do work...
           self._log_execution(context.plan_artifact_id, "execute", f"Loading {len(nodes)} nodes")

           # Commit
           self._log_execution(context.plan_artifact_id, "commit", "Committed to Neo4j")
   ```

4. **Populate bundle rulesets field:**
   ```python
   def _emit_bundle(self, plan_id, ...):
       # Load active rulesets
       active_rulesets = self._load_active_rulesets()

       # Compute vault state
       vault_state = self._capture_vault_state()

       manifest = {
           "version": "bundle@v1",
           "operation": operation,
           "artifacts": {...},
           "repro": {
               "rulesets": [
                   {
                       "id": rs.ruleset_id,
                       "version": rs.version,
                       "content_id": self._hash_ruleset(rs),
                       "path": rs.path,
                   }
                   for rs in active_rulesets
               ],
               "inputs_snapshot": vault_state,
               "surface": surface,
               "engine_version": _get_engine_version(),
               "environment": _get_environment(),
           }
       }
   ```

**Files to modify:**
- `irrev/harness/harness.py`
- `irrev/harness/handler.py` (add logging helper)

### Phase 3: Constraint Engine Integration

1. **Modify constraint engine to emit events:**
   ```python
   def run_constraints_lint(vault_path, *, vault, graph, ruleset, ...):
       ctx = ConstraintContext(...)
       results = []

       for rule in ruleset.rules:
           fn = PREDICATES.get(rule.predicate.name)
           if fn is None:
               continue

           for item in _select_items(rule, ctx, ruleset):
               # Evaluate rule
               rule_results = fn(item, rule, ctx)
               results.extend(rule_results)

               # NEW: Emit constraint.evaluated event for each evaluation
               for result in rule_results:
                   event = create_event(
                       CONSTRAINT_EVALUATED,
                       artifact_id=ctx.current_artifact_id,  # Need to pass this
                       actor="system:constraint_engine",
                       payload={
                           "ruleset_id": ruleset.ruleset_id,
                           "rule_id": rule.id,
                           "invariant": rule.invariant,
                           "result": "fail" if result.severity == "error" else "warning",
                           "evidence": {
                               "item_id": result.concept_id or result.path,
                               "message": result.message,
                           }
                       }
                   )
                   ctx.ledger.append(event)

       # Emit invariant.checked event for each invariant
       invariants_checked = set(r.invariant for r in ruleset.rules if r.invariant)
       for inv in invariants_checked:
           violations = [r for r in results if r.invariant == inv and r.severity == "error"]
           event = create_event(
               INVARIANT_CHECKED,
               artifact_id=ctx.current_artifact_id,
               actor="system:constraint_engine",
               payload={
                   "invariant_id": inv,
                   "status": "fail" if violations else "pass",
                   "violations": len(violations),
               }
           )
           ctx.ledger.append(event)

       return results
   ```

**Files to modify:**
- `irrev/constraints/engine.py`
- `irrev/constraints/predicates.py` (add ledger to ConstraintContext)

### Phase 4: Ledger Query Enhancements

Add query methods to `ArtifactLedger`:

```python
class ArtifactLedger:
    def constraint_evaluations(self, artifact_id: str) -> list[ArtifactEvent]:
        """Get all constraint.evaluated events for an artifact."""
        return [
            e for e in self.events_for(artifact_id)
            if e.event_type == CONSTRAINT_EVALUATED
        ]

    def invariant_checks(self, artifact_id: str) -> list[ArtifactEvent]:
        """Get all invariant.checked events for an artifact."""
        return [
            e for e in self.events_for(artifact_id)
            if e.event_type == INVARIANT_CHECKED
        ]

    def execution_logs(self, artifact_id: str) -> list[ArtifactEvent]:
        """Get all execution.logged events for an artifact."""
        return [
            e for e in self.events_for(artifact_id)
            if e.event_type == EXECUTION_LOGGED
        ]

    def audit_trail(self, artifact_id: str) -> dict[str, Any]:
        """
        Get complete audit trail for an artifact.

        Returns comprehensive view including:
        - Lifecycle events
        - Constraint evaluations
        - Invariant checks
        - Execution logs
        """
        events = self.events_for(artifact_id)
        return {
            "artifact_id": artifact_id,
            "lifecycle": [e for e in events if e.event_type in EVENT_TYPES],
            "constraints": self.constraint_evaluations(artifact_id),
            "invariants": self.invariant_checks(artifact_id),
            "execution": self.execution_logs(artifact_id),
            "snapshot": self.snapshot(artifact_id),
        }
```

**Files to modify:**
- `irrev/artifact/ledger.py`

---

## Helper Implementations

### Vault State Capture

```python
def _capture_vault_state(self) -> dict[str, Any]:
    """Capture current vault state for reproducibility."""
    from ..vault.loader import Vault

    vault = Vault.load(self.vault_path)

    # Compute content hash
    vault_sha256 = self._hash_vault_content()

    return {
        "concept_count": len(vault.concepts),
        "link_count": sum(len(c.links_to) for c in vault.concepts),
        "vault_sha256": vault_sha256,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def _hash_vault_content(self) -> str:
    """Compute deterministic hash of vault content."""
    import hashlib

    hasher = hashlib.sha256()

    # Hash all markdown files in sorted order
    for md_file in sorted(self.vault_path.rglob("*.md")):
        if md_file.is_file():
            hasher.update(md_file.read_bytes())

    return hasher.hexdigest()
```

### Ruleset Loading

```python
def _load_active_rulesets(self) -> list[dict[str, Any]]:
    """Load active rulesets for current operation."""
    from ..constraints.load import load_ruleset

    rulesets = []

    # Load core ruleset
    core_path = self.vault_path.parent / "meta" / "rulesets" / "core.toml"
    if core_path.exists():
        ruleset = load_ruleset(core_path)
        rulesets.append({
            "id": ruleset.ruleset_id,
            "version": ruleset.version,
            "content_id": self._hash_ruleset_file(core_path),
            "path": str(core_path.relative_to(self.vault_path.parent)),
        })

    return rulesets

def _hash_ruleset_file(self, path: Path) -> str:
    """Compute content hash of ruleset file."""
    import hashlib
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
```

---

## Benefits

### 1. Complete Audit Trail

Every operation now has:
- Full context (vault state, rulesets, environment)
- Constraint evaluation results
- Invariant verification status
- Detailed execution logs

### 2. Reproducibility

From a bundle artifact, you can:
- Reconstruct exact vault state
- Identify which rulesets governed the operation
- Verify constraint compliance
- Replay execution with same inputs

### 3. Forensic Analysis

Query ledger to answer:
- "Which constraints failed during this plan?"
- "What invariants were violated?"
- "What was the vault state when this plan was created?"
- "Which rulesets were active?"

### 4. Governance Transparency

Prove compliance by showing:
- Constraint evaluation events
- Invariant verification events
- Ruleset references with content hashes

### 5. Debugging

Execution logs provide:
- Phase-by-phase progress
- Resource usage metrics
- Error context

---

## Migration Strategy

### Backward Compatibility

All enhancements are **additive**:
- Existing events remain valid
- Old code continues to work
- New fields are optional

### Rollout

1. **Phase 1** - Add event types (no behavior change)
2. **Phase 2** - Enhance harness (new events emitted)
3. **Phase 3** - Integrate constraints (constraint events emitted)
4. **Phase 4** - Add query helpers (convenience methods)

Each phase is independently deployable and backward compatible.

---

## Example: Enhanced Ledger Output

**Full lifecycle for a Neo4j load operation:**

```jsonl
{"event_type":"artifact.created","artifact_id":"01HX123","timestamp":"2026-01-26T12:00:00Z","actor":"agent:harness","payload":{"operation":"neo4j.load","risk_class":"mutation_destructive","context":{"vault_state":{"concept_count":1234,"vault_sha256":"abc..."},"active_rulesets":[{"id":"core","version":1,"content_id":"sha256:..."}]}},"content_id":"cid123","artifact_type":"plan"}

{"event_type":"constraint.evaluated","artifact_id":"01HX123","timestamp":"2026-01-26T12:00:00.1Z","actor":"system:constraint_engine","payload":{"ruleset_id":"core","rule_id":"canonical-form-exists","invariant":"decomposition","result":"pass"}}

{"event_type":"constraint.evaluated","artifact_id":"01HX123","timestamp":"2026-01-26T12:00:00.2Z","actor":"system:constraint_engine","payload":{"ruleset_id":"core","rule_id":"no-orphaned-links","invariant":"decomposition","result":"pass"}}

{"event_type":"invariant.checked","artifact_id":"01HX123","timestamp":"2026-01-26T12:00:00.3Z","actor":"system:constraint_engine","payload":{"invariant_id":"decomposition","status":"pass","rules_checked":5,"violations":0}}

{"event_type":"artifact.validated","artifact_id":"01HX123","timestamp":"2026-01-26T12:00:01Z","actor":"harness","payload":{"validator":"harness","errors":[],"constraint_results":{"rulesets_evaluated":["core"],"rules_checked":15,"rules_passed":15,"invariants_verified":[{"id":"decomposition","status":"pass"}]}}}

{"event_type":"artifact.approved","artifact_id":"01HX123","timestamp":"2026-01-26T12:01:00Z","actor":"human:alice","payload":{"approval_artifact_id":"01HX124","force_ack":true,"scope":"neo4j.load"}}

{"event_type":"execution.logged","artifact_id":"01HX123","timestamp":"2026-01-26T12:02:00Z","actor":"handler:neo4j","payload":{"phase":"prepare","message":"Connecting to Neo4j","level":"info"}}

{"event_type":"execution.logged","artifact_id":"01HX123","timestamp":"2026-01-26T12:02:01Z","actor":"handler:neo4j","payload":{"phase":"execute","message":"Loading 100 nodes (batch 1/10)","level":"info","metadata":{"batch":1,"progress":"100/1000"}}}

{"event_type":"execution.logged","artifact_id":"01HX123","timestamp":"2026-01-26T12:02:10Z","actor":"handler:neo4j","payload":{"phase":"commit","message":"Committed to Neo4j","level":"info"}}

{"event_type":"artifact.executed","artifact_id":"01HX123","timestamp":"2026-01-26T12:02:11Z","actor":"handler:neo4j","payload":{"result_artifact_id":"01HX125","erasure_cost":{"notes":100},"creation_summary":{"notes":1000},"execution_details":{"duration_ms":11000,"phases":[{"name":"prepare","duration_ms":1000},{"name":"execute","duration_ms":9000},{"name":"commit","duration_ms":1000}]}}}

{"event_type":"artifact.created","artifact_id":"01HX126","timestamp":"2026-01-26T12:02:12Z","actor":"handler:harness","payload":{"operation":"bundle.emit"},"content_id":"cid126","artifact_type":"bundle"}
```

---

## Testing Strategy

### Unit Tests

```python
def test_constraint_evaluated_event_emission():
    """Test that constraint.evaluated events are emitted during validation."""
    harness = Harness(vault_path)
    handler = MockHandler(effect_type="read_only")

    result = harness.propose(handler, {})

    # Check constraint events
    constraint_events = harness.ledger.constraint_evaluations(result.plan_artifact_id)
    assert len(constraint_events) > 0
    assert all(e.event_type == CONSTRAINT_EVALUATED for e in constraint_events)

def test_invariant_checked_event_emission():
    """Test that invariant.checked events are emitted."""
    harness = Harness(vault_path)
    handler = MockHandler()

    result = harness.propose(handler, {})

    # Check invariant events
    invariant_events = harness.ledger.invariant_checks(result.plan_artifact_id)
    assert len(invariant_events) > 0

def test_bundle_contains_rulesets():
    """Test that bundles include active rulesets."""
    harness = Harness(vault_path)
    handler = MockHandler()

    execute_result = harness.run(handler, {})

    # Get bundle content
    snap = harness.ledger.snapshot(execute_result.bundle_artifact_id)
    content = harness.content_store.get(snap.content_id)

    assert "repro" in content
    assert "rulesets" in content["repro"]
    assert len(content["repro"]["rulesets"]) > 0
    assert all("content_id" in rs for rs in content["repro"]["rulesets"])

def test_execution_logs_captured():
    """Test that execution.logged events are captured."""
    harness = Harness(vault_path)
    handler = MockHandler()

    result = harness.propose(handler, {})
    harness.plan_manager.approve(result.plan_artifact_id, "human:test", scope="test")
    execute_result = harness.execute(result.plan_artifact_id, handler)

    # Check execution logs
    logs = harness.ledger.execution_logs(result.plan_artifact_id)
    assert len(logs) > 0
    assert all(e.event_type == EXECUTION_LOGGED for e in logs)
```

### Integration Tests

```python
def test_full_lifecycle_with_constraints(real_vault_path):
    """Test complete lifecycle with constraint evaluation."""
    harness = Harness(real_vault_path)
    handler = Neo4jLoadHandler()

    # Propose with constraint evaluation
    result = harness.propose(handler, {
        "http_uri": "http://localhost:7474",
        "database": "test",
        "mode": "sync"
    })

    # Verify constraint events
    constraints = harness.ledger.constraint_evaluations(result.plan_artifact_id)
    assert len(constraints) > 0

    # Verify invariant events
    invariants = harness.ledger.invariant_checks(result.plan_artifact_id)
    assert len(invariants) > 0

    # Execute and verify bundle
    harness.plan_manager.approve(result.plan_artifact_id, "human:test", scope="test")
    execute_result = harness.execute(result.plan_artifact_id, handler)

    # Bundle should have full repro data
    snap = harness.ledger.snapshot(execute_result.bundle_artifact_id)
    content = harness.content_store.get(snap.content_id)

    assert content["repro"]["rulesets"]
    assert content["repro"]["inputs_snapshot"]
```

---

## CLI Enhancements

Add commands to query enriched ledger:

```bash
# Show audit trail for an artifact
irrev artifact audit <artifact_id>

# Show constraint evaluations
irrev artifact constraints <artifact_id>

# Show invariant status
irrev artifact invariants <artifact_id>

# Show execution logs
irrev artifact logs <artifact_id>

# Verify reproducibility
irrev artifact verify-repro <bundle_id>
```

---

## Conclusion

This enrichment design provides:

1. **Complete audit trail** - Every operation fully traceable
2. **Governance transparency** - Constraint compliance visible
3. **Reproducibility** - Operations can be replayed
4. **Forensic analysis** - Detailed investigation capabilities
5. **Backward compatibility** - No breaking changes

**Implementation Effort:** ~2-3 days
**Risk:** Low (additive changes only)
**Value:** High (enables full governance transparency)

**Recommendation:** Implement in phases, starting with Phase 1 (event types) and Phase 2 (harness enrichment).
