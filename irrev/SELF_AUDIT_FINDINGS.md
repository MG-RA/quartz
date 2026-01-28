# Self-Audit Findings

Generated: 2026-01-26

This document surfaces detected conditions in the irrev tool's own code. Per Failure Mode #10: "The most serious failure mode is assuming the lens already accounts for its own limitations."

These are observations, not prescriptions.

---

## Remediation Status

The following conditions have been addressed:

| Phase | Condition | Status | Details |
|-------|-----------|--------|---------|
| 1 | Attribution (prescriptive language) | ✓ Remediated | 14 `**Fix:**` directives converted to `**Condition observed:**` in vault/rules.py; `must` → `are` in vault/invariants.py:35 |
| 2 | Governance (bypass warnings) | ✓ Remediated | Added `⚠ Governance notice:` warnings for `--invariant`, `--exclude-layer`, `--in-place`, `--mode rebuild` |
| 3 | Irreversibility (audit logging) | ✓ Remediated | Created `audit_log.py` with `ErasureCost`/`CreationSummary` dataclasses; all destructive operations now log to `.irrev/audit.log` |
| 4 | Decomposition (compute/execute separation) | ✓ Remediated | Created `planning.py` with `Plan`/`Result` base classes; `neo4j load` and `registry build` refactored to separate diagnostic/action phases |
| 5 | Governance + irreversibility (artifact approvals) | ✓ Remediated | Added event-sourced artifact ledger (`.irrev/artifact.jsonl`) with content-addressed payloads and approval artifacts gating execution |
| 6 | Interface invariance (ruleset + execution trail) | ✓ Remediated | Made `lint` ruleset-driven (vault-owned TOML); added interface invariance checks over the artifact trail (execution summary + surface attribution); removed prescriptive language leaks in tool messages |

### New Capabilities

| Command | New Flags | Purpose |
|---------|-----------|---------|
| `neo4j load` | `--dry-run` | Preview what would be loaded/erased |
| `neo4j load` | `--force` | Required for destructive rebuild mode |
| `neo4j load` | `--propose-only`, `--plan-id` | Propose/approve/execute via the artifact ledger |
| `registry build` | `--dry-run` | Preview registry changes |
| `artifact` | (new command group) | Inspect artifacts; create approval artifacts |
| `lint` | (ruleset-driven) | Loads `content/meta/rulesets/core.toml` when present; includes ruleset provenance in `--json` output |

### Audit Trail

All state-modifying operations log to `.irrev/audit.log` (JSON Lines format):

```json
{"timestamp": "2026-01-26T...", "operation": "neo4j-rebuild", "erased": {"notes": 150, "edges": 420}, "created": {"notes": 155, "edges": 435}, ...}
```

---

## Original Findings (Preserved for Reference)

The sections below document the original detected conditions prior to remediation.

---

## Prescriptive Language Detected

The tool's lint rules and invariant documentation use prescriptive language ("Fix:", "should", "must") that the tool itself detects and flags as problematic in vault content.

### vault/rules.py

| Line | Pattern |
|------|---------|
| 14 | `**Fix:** Remove direct paper links from concepts...` |
| 31 | `**Fix:** Add ## Structural dependencies section...` |
| 51 | `**Fix:** Replace alias with canonical name...` |
| 71 | `**Fix:** Break the cycle by...` |
| 91 | `**Fix:** Add role: <type> to frontmatter...` |
| 108 | `**Fix:** - Create the missing note - Fix the typo...` |
| 126 | `**Fix:** Regenerate the tables in-place...` |
| 143 | `**Fix:** Add a ## Residuals section...` |
| 157 | `**Fix:** Add the missing headings...` |
| 173 | `**Fix:** Re-examine the dependency...` |
| 198 | `**Fix:** Re-examine the dependency...` |
| 224 | `**Fix:** Make responsibility assignments explicit...` |

### vault/invariants.py

| Line | Pattern |
|------|---------|
| 35 | `operators must` (in Decomposition invariant statement) |

---

## Role Separation Violations

Functions that mix read (diagnostic) and write (action) operations:

### High-Impact Violations

| File | Function | Read Ops | Write Ops |
|------|----------|----------|-----------|
| commands/neo4j_cmd.py | run_neo4j_load | load_vault, get | commit, wipe, upsert |
| commands/registry.py | run_build (--in-place) | read, exists | write_text |
| commands/audit.py | run_audit | is_dir, exists | mkdir, write_text |
| commands/junctions.py | run_domain_audit | load_vault, get | mkdir, write_text |
| cli.py | registry_build | exists | run_build |

### Pattern Observation

The majority of command implementations follow a read-then-write pattern within a single function. This is common in CLI tools but violates the Decomposition invariant when interpreted strictly.

---

## Self-Exemption Patterns

Places where the tool allows bypassing constraints it enforces on content:

### Rule Filtering Mechanisms

| File | Line | Pattern |
|------|------|---------|
| cli.py | 69 | `--invariant` flag allows skipping entire invariant groups |
| cli.py | 400 | `--exclude-layer` allows excluding concepts from analysis |
| commands/lint.py | 48 | `allowed_rules = None` enables selective rule execution |

### Destructive Operations Without Cost Accounting

| File | Line | Pattern |
|------|------|---------|
| cli.py | 752 | `type=click.Choice(["sync", "rebuild"])` - rebuild mode wipes DB |
| cli.py | 755 | `rebuild wipes the database first` - mentions wipe without cost |
| neo4j_cmd.py | 392-394 | `if mode == "rebuild":` wipes database |
| registry.py | 30-68 | `in_place: bool = False` overwrites files |

### Cost Accounting Gap

The irreversibility invariant states: "Erasure costs must be declared; rollback cannot be assumed."

The tool's `--mode rebuild` and `--in-place` options perform erasure operations without:
- Requiring explicit cost acknowledgment
- Logging what was erased
- Providing rollback mechanisms
- Declaring the transformation space of affected state

---

## Summary of Detected Conditions

| Invariant | Detection Count | Primary Locations |
|-----------|-----------------|-------------------|
| Attribution (prescriptive language) | 14 | vault/rules.py |
| Decomposition (role mixing) | 19 | commands/*.py |
| Governance (self-exemption) | 9 | cli.py, lint.py |
| Irreversibility (unaccounted erasure) | 14 | cli.py, neo4j_cmd.py, registry.py |

---

## Detection Methodology

The self-audit module applies the same detection patterns to tool source code that `junctions.py` applies to vault content:

1. **prescriptive_scan.py** - AST-based extraction of strings; regex patterns for prescriptive language
2. **role_separation.py** - AST analysis of function calls to detect read/write mixing
3. **exemption_detect.py** - Pattern matching for rule filtering and destructive operations

These scanners are themselves subject to the same self-audit (note their presence in the findings above).

---

## Termination Note

This document surfaces conditions. It does not recommend actions, assign blame, or prescribe fixes.

Per the governance invariant: "No actor is exempt from structural constraints." The tool's own code is subject to the same observations it makes about vault content.
