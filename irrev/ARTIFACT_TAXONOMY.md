# Artifact Type System: Taxonomy and Enforcement Strategy

**Date:** 2026-01-27
**Status:** DRAFT PROPOSAL
**Context:** Repository architecture + governance diagnostician

---

## Executive Summary

This document proposes a **strict, auditable artifact type system** for the Quartz/irrev repository that:

1. **Clearly defines** what counts as an "artifact" (tracked vs static content)
2. **Assigns stable types** with validation schemas
3. **Specifies enforcement rules** with three severity levels (WARN/FAIL/ENFORCE)
4. **Maps types to ledger/envelope** systems (full tracking vs partial vs none)
5. **Provides low-risk migration plan** with backward compatibility

**Key Design Principle:** Minimize ambiguity through explicit boundaries, not prescriptive restrictions.

---

## Part A: Repository Inventory

### Current Artifact Categories

| Category | Paths | Extensions | Current Usage | Risks | Proposed Type |
|----------|-------|------------|---------------|-------|---------------|
| **Concept notes** | `content/concepts/*.md` | `.md` | 37 canonical definitions with layer/role/deps | Missing frontmatter = silent drift | `vault:concept` |
| **Diagnostic notes** | `content/diagnostics/**/*.md` | `.md` | Diagnostic tools with facets | Unclear when diagnostic vs concept | `vault:diagnostic` |
| **Domain notes** | `content/domains/*.md` | `.md` | 5 domain applications | Overlap with projections? | `vault:domain` |
| **Projection notes** | `content/projections/*.md` | `.md` | 11 re-readings of external work | Encoded vs non-encoded unclear | `vault:projection` |
| **Paper notes** | `content/papers/*.md` | `.md` | 4 core compilations | Role=paper but what's the contract? | `vault:paper` |
| **Invariant notes** | `content/invariants/*.md` | `.md` | 4 invariant definitions | Governance expectations unclear | `vault:invariant` |
| **Meta files** | `content/meta/**/*` | `.toml`, `.yml`, `.md` | Rulesets, hubs, registry overrides | No validation on TOML/YAML schemas | `vault:ruleset`, `vault:config` |
| **Templates** | `content/_templates/*.md` | `.md` | 5 content creation templates | Should templates be artifacts? | `vault:template` |
| **Exports** | `content/exports/**/*` | `.json`, `.svg`, `.html`, `.dot` | Generated graph visualizations | Build artifacts vs tracked artifacts? | `vault:export` (ephemeral) |
| **Support notes** | `content/*.md`, `content/meta/*.md` | `.md` | Index, README, meta docs | No clear contract | `vault:support` |
| **Plan artifacts** | In ledger only (no file) | N/A | Operation + payload + inputs | Has type pack, full validation | `artifact:plan` |
| **Approval artifacts** | In ledger only (no file) | N/A | Approval chain metadata | Has type pack, full validation | `artifact:approval` |
| **Bundle artifacts** | In ledger only (no file) | N/A | Proof packs (plan+approval+result) | Has type pack, full validation | `artifact:bundle` |
| **Execution summaries** | In ledger only (no file) | N/A | Execution results | No type pack | `artifact:execution_summary` |
| **Lint reports** | In ledger only (no file) | N/A | Lint output | No type pack | `artifact:lint_report` |
| **Python modules** | `irrev/irrev/**/*.py` | `.py` | 70+ tool modules | No artifact identity | `code:module` (static) |
| **Tests** | `irrev/tests/*.py` | `.py` | 21 test files | No artifact identity | `code:test` (static) |
| **Build configs** | `pyproject.toml`, `package.json`, `tsconfig.json` | `.toml`, `.json`, `.ts` | Build system files | Version drift risk | `build:config` (static) |
| **Quartz configs** | `quartz.config.ts`, `quartz.layout.ts` | `.ts` | Site generator config | No validation | `build:quartz_config` (static) |
| **Git metadata** | `.gitignore`, `.git/**` | Various | VCS files | Not artifacts | (excluded) |
| **Obsidian metadata** | `content/.obsidian/**` | `.json` | Editor settings | Not artifacts | (excluded) |

**Total Categories:** 20 artifact types proposed (10 vault types, 6 artifact system types, 4 static types)

---

## Part B: Artifact Type Registry (Canonical)

### Registry Design Decision

**Chosen Approach:** **Dual Registry**

- **`irrev/artifact/types/registry.py`** - Python registry for **artifact system types** (plan, approval, bundle, etc.)
  - Programmatic access required
  - Type packs are code (validation logic)
  - Already exists (3 types registered)

- **`content/meta/artifact-types.toml`** - TOML registry for **vault content types** (concept, diagnostic, domain, etc.)
  - Vault-owned policy
  - Human-readable
  - Can be versioned and diffed
  - Loaded by tool, not owned by tool

**Justification:**
- Artifact system types (plan/approval/bundle) are **operational** - require code validation
- Vault content types (concept/diagnostic/domain) are **editorial** - require schema validation only
- Separation of concerns: tool artifacts vs content artifacts
- Content registry can evolve independently (vault policy)
- Tool registry evolves with code (backward compat via type pack protocol)

### Vault Type Registry Schema (TOML)

**File:** `content/meta/artifact-types.toml`

```toml
registry_version = 1
description = "Vault-owned artifact type definitions for content/"

[defaults]
linkable = false  # Vault notes don't get artifact_id by default
requires_frontmatter = true
governance_scope = "vault"

# ============================================================================
# CONCEPT NOTES
# ============================================================================

[[types]]
type_id = "vault:concept"
description = "Canonical concept definition in the irreversibility accounting framework"

[types.locations]
allowed_patterns = ["content/concepts/*.md"]
allowed_extensions = [".md"]
forbidden_patterns = ["content/concepts/_*"]  # No private concepts

[types.metadata]
required = ["role", "layer", "canonical"]
optional = ["aliases", "depends_on", "facets"]

[types.metadata.constraints]
role = { type = "literal", value = "concept" }
layer = { type = "enum", values = ["primitive", "first-order", "mechanism", "accounting", "selector", "foundational", "failure-state", "meta-analytical"] }
canonical = { type = "boolean" }
aliases = { type = "list[string]" }
depends_on = { type = "list[string]" }  # Wiki-link format: [[Note#Section]]
facets = { type = "list[string]", allowed = ["implicit-constraint", "anti-belief", "scale-fragile", "misuse-risk"] }

[types.governance]
linkable = false  # Not artifact system artifacts
requires_envelope = false
invariants = ["decomposition", "irreversibility"]  # From core.toml
required_sections = ["## Structural dependencies"]  # Optional enforcement

[types.validation]
enforce_unique_canonical = true  # Only one canonical=true per concept
enforce_layer_dependencies = true  # Primitives can't depend on first-order

# ============================================================================
# DIAGNOSTIC NOTES
# ============================================================================

[[types]]
type_id = "vault:diagnostic"
description = "Diagnostic tool for applying the irreversibility lens to phenomena"

[types.locations]
allowed_patterns = ["content/diagnostics/**/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role"]
optional = ["depends_on", "facets"]

[types.metadata.constraints]
role = { type = "literal", value = "diagnostic" }
depends_on = { type = "list[string]" }
facets = { type = "list[string]", allowed = ["implicit-constraint", "anti-belief", "scale-fragile", "misuse-risk"] }

[types.governance]
linkable = false
requires_envelope = false
invariants = ["irreversibility"]

# ============================================================================
# DOMAIN NOTES
# ============================================================================

[[types]]
type_id = "vault:domain"
description = "Domain-specific application of the framework"

[types.locations]
allowed_patterns = ["content/domains/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role"]
optional = ["depends_on", "domain"]

[types.metadata.constraints]
role = { type = "literal", value = "domain" }
depends_on = { type = "list[string]" }
domain = { type = "string" }  # E.g., "financial-infrastructure", "ai-systems"

[types.governance]
linkable = false
requires_envelope = false

# ============================================================================
# PROJECTION NOTES
# ============================================================================

[[types]]
type_id = "vault:projection"
description = "Re-reading or projection of external work through the irreversibility lens"

[types.locations]
allowed_patterns = ["content/projections/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role", "type"]
optional = ["canonical", "depends_on", "facets"]

[types.metadata.constraints]
role = { type = "literal", value = "projection" }
type = { type = "enum", values = ["encoded", "reframe", "critique"] }
canonical = { type = "boolean", default = false }
depends_on = { type = "list[string]" }
facets = { type = "list[string]" }

[types.governance]
linkable = false
requires_envelope = false

# ============================================================================
# PAPER NOTES
# ============================================================================

[[types]]
type_id = "vault:paper"
description = "Core paper or compilation defining the framework"

[types.locations]
allowed_patterns = ["content/papers/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role"]
optional = ["version", "authors"]

[types.metadata.constraints]
role = { type = "literal", value = "paper" }
version = { type = "string" }  # E.g., "v1.0"
authors = { type = "list[string]" }

[types.governance]
linkable = false
requires_envelope = false
invariants = ["governance"]

# ============================================================================
# INVARIANT NOTES
# ============================================================================

[[types]]
type_id = "vault:invariant"
description = "Invariant definition (governance/irreversibility/decomposition/attribution)"

[types.locations]
allowed_patterns = ["content/invariants/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role", "invariant_id"]
optional = ["scope"]

[types.metadata.constraints]
role = { type = "literal", value = "invariant" }
invariant_id = { type = "enum", values = ["governance", "irreversibility", "decomposition", "attribution"] }
scope = { type = "enum", values = ["vault", "artifact", "graph", "ruleset"] }

[types.governance]
linkable = false
requires_envelope = false
invariants = ["governance"]

# ============================================================================
# TEMPLATE NOTES
# ============================================================================

[[types]]
type_id = "vault:template"
description = "Template for creating new content"

[types.locations]
allowed_patterns = ["content/_templates/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role"]
optional = ["template_for"]

[types.metadata.constraints]
role = { type = "literal", value = "template" }
template_for = { type = "enum", values = ["concept", "diagnostic", "domain", "projection", "paper"] }

[types.governance]
linkable = false
requires_envelope = false
requires_frontmatter = true  # Templates must show example frontmatter

# ============================================================================
# SUPPORT NOTES
# ============================================================================

[[types]]
type_id = "vault:support"
description = "Supporting documentation (index, README, meta)"

[types.locations]
allowed_patterns = ["content/*.md", "content/meta/*.md"]
allowed_extensions = [".md"]

[types.metadata]
required = ["role"]
optional = ["type"]

[types.metadata.constraints]
role = { type = "literal", value = "support" }
type = { type = "enum", values = ["index", "readme", "meta"], optional = true }

[types.governance]
linkable = false
requires_envelope = false

# ============================================================================
# RULESET FILES
# ============================================================================

[[types]]
type_id = "vault:ruleset"
description = "TOML ruleset defining constraints and invariants"

[types.locations]
allowed_patterns = ["content/meta/rulesets/*.toml"]
allowed_extensions = [".toml"]

[types.metadata]
required = ["ruleset_id", "version"]
optional = ["description", "defaults"]

[types.metadata.constraints]
# TOML root keys, not YAML frontmatter
ruleset_id = { type = "string" }
version = { type = "integer" }

[types.governance]
linkable = false
requires_envelope = false
requires_frontmatter = false  # TOML files don't have frontmatter
invariants = ["governance"]  # Rulesets are governance policy

[types.validation]
enforce_schema = true  # Must match constraints/schema.py RulesetSchema

# ============================================================================
# CONFIG FILES (YAML)
# ============================================================================

[[types]]
type_id = "vault:config"
description = "YAML configuration files (hubs, registry overrides)"

[types.locations]
allowed_patterns = ["content/meta/*.yml", "content/meta/*.yaml"]
allowed_extensions = [".yml", ".yaml"]

[types.metadata]
required = []  # Schema depends on config type

[types.governance]
linkable = false
requires_envelope = false
requires_frontmatter = false  # YAML root structure

# ============================================================================
# EXPORT FILES (Generated)
# ============================================================================

[[types]]
type_id = "vault:export"
description = "Generated export files (graphs, visualizations) - ephemeral, reproducible"

[types.locations]
allowed_patterns = ["content/exports/**/*"]
allowed_extensions = [".json", ".svg", ".html", ".dot"]

[types.metadata]
required = []  # No frontmatter

[types.governance]
linkable = false
requires_envelope = false
requires_frontmatter = false
ephemeral = true  # Can be regenerated, not source of truth

[types.validation]
git_ignore_recommended = true  # Should be in .gitignore
```

---

### Artifact System Type Registry (Python)

**File:** `irrev/artifact/types/registry.py` (EXTENDED)

```python
"""
Artifact system type registry.
Defines types for artifacts tracked in the ledger with envelopes/events.
"""

from typing import Protocol, Any

# ============================================================================
# TYPE PACK PROTOCOL (unchanged)
# ============================================================================

class ArtifactTypePack(Protocol):
    def validate(self, content: dict[str, Any]) -> list[str]:
        """Return list of error strings. Empty list = valid."""
        ...

    def extract_inputs(self, content: dict[str, Any]) -> list[dict[str, str]]:
        """Extract artifact_id references for dependency tracking."""
        ...

    def compute_payload_manifest(self, content: dict[str, Any]) -> list[dict[str, Any]]:
        """Compute file manifest: [{path, bytes, sha256}, ...]"""
        ...

# ============================================================================
# REGISTRY METADATA
# ============================================================================

TYPE_REGISTRY_VERSION = 2  # Increment when adding/removing types

ARTIFACT_TYPE_METADATA = {
    # Operational artifacts (have type packs)
    "plan": {
        "description": "Execution plan with operation + payload + inputs",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created", "artifact.validated"],
        "may_have_events": ["artifact.approved", "artifact.executed", "artifact.rejected"],
        "governance_expectations": ["approval_required_if_destructive", "execution_summary_required"],
        "invariants": ["governance", "attribution"],
    },
    "approval": {
        "description": "Approval chain metadata for plan governance",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created", "artifact.validated"],
        "may_have_events": [],
        "governance_expectations": ["force_ack_required_if_destructive"],
        "invariants": ["governance"],
    },
    "bundle": {
        "description": "Proof pack aggregating plan + approval + result",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created", "artifact.validated"],
        "may_have_events": [],
        "governance_expectations": ["bundle_version_stable"],
        "invariants": ["governance", "attribution"],
    },

    # Result artifacts (no type packs yet)
    "execution_summary": {
        "description": "Execution result from handler",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": ["attribution"],
    },
    "lint_report": {
        "description": "Lint output artifact",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },

    # Low-level artifacts (no type packs)
    "report": {
        "description": "Generic analysis report",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "note": {
        "description": "Free-form note artifact",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "config": {
        "description": "Configuration artifact",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": ["governance"],
    },

    # Event artifacts (low-level)
    "change_event": {
        "description": "VCS change event",
        "linkable": True,
        "requires_envelope": False,  # Events only
        "requires_events": [],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "fs_event": {
        "description": "File system event",
        "linkable": True,
        "requires_envelope": False,  # Events only
        "requires_events": [],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": [],
    },
    "audit_entry": {
        "description": "Audit log entry",
        "linkable": True,
        "requires_envelope": True,
        "requires_events": ["artifact.created"],
        "may_have_events": [],
        "governance_expectations": [],
        "invariants": ["governance"],
    },
}

# ============================================================================
# TYPE PACK REGISTRY (existing)
# ============================================================================

from .plan_pack import PlanTypePack
from .approval_pack import ApprovalTypePack
from .bundle_pack import BundleTypePack

TYPE_PACKS: dict[str, ArtifactTypePack] = {
    "plan": PlanTypePack(),
    "approval": ApprovalTypePack(),
    "bundle": BundleTypePack(),
}

def get_type_pack(artifact_type: str) -> ArtifactTypePack | None:
    """Get type pack for artifact type (case-insensitive, None-safe)."""
    return TYPE_PACKS.get((artifact_type or "").strip().lower())

def get_type_metadata(artifact_type: str) -> dict[str, Any] | None:
    """Get metadata for artifact type."""
    return ARTIFACT_TYPE_METADATA.get((artifact_type or "").strip().lower())

def list_artifact_types() -> list[str]:
    """List all registered artifact types."""
    return sorted(ARTIFACT_TYPE_METADATA.keys())

def has_type_pack(artifact_type: str) -> bool:
    """Check if artifact type has a validation type pack."""
    return get_type_pack(artifact_type) is not None
```

---

## Part C: Mapping to Envelope + Ledger

### The Boundary: What Gets Tracked?

**Key Principle:** Artifacts that **participate in governance** get envelopes and events. Content that is **purely editorial** does not.

| Artifact Category | Envelope? | Events? | Reasoning |
|-------------------|-----------|---------|-----------|
| **Vault content notes** (concept/diagnostic/domain/projection/paper/invariant/support) | **NO** | **NO** | Editorial content; validated by lint rules (core.toml); no execution; tracked by git, not ledger |
| **Vault templates** | **NO** | **NO** | Static templates; no execution; git-tracked only |
| **Vault rulesets** (TOML) | **NO** | **NO** | Policy files; versioned in git; referenced by constraint engine but not executed |
| **Vault configs** (YAML) | **NO** | **NO** | Configuration files; git-tracked; loaded at runtime |
| **Vault exports** | **NO** | **NO** | Ephemeral; regenerable from source; should be .gitignored |
| **Artifact system: plan** | **YES** | **YES** | Operational artifact; requires approval/execution; full governance |
| **Artifact system: approval** | **YES** | **YES** | Governance metadata; tracks approval chain |
| **Artifact system: bundle** | **YES** | **YES** | Proof pack; requires full provenance trail |
| **Artifact system: execution_summary** | **YES** | **YES** | Result artifact; must be linked to plan execution |
| **Artifact system: lint_report** | **YES** | **YES** | Analysis result; artifact for reproducibility |
| **Artifact system: report/note/config** | **YES** | **YES** | Low-level artifacts; tracked for provenance |
| **Artifact system: audit_entry** | **YES** | **YES** | Governance audit trail |
| **Artifact system: change_event/fs_event** | **NO** | **YES** | Events only; no content payload; no envelope needed |
| **Python code** (`irrev/**/*.py`) | **NO** | **NO** | Source code; git-tracked; not governance artifacts |
| **Tests** (`tests/*.py`) | **NO** | **NO** | Test code; git-tracked |
| **Build configs** (pyproject.toml, package.json, tsconfig.json) | **NO** | **NO** | Build system files; git-tracked |
| **Quartz configs** | **NO** | **NO** | Site generator config; git-tracked |

### Envelope Structure (for tracked artifacts)

**Envelope = Identity + Provenance + Governance State**

```python
# Stored as events, projected to snapshot
envelope = {
    # Identity
    "artifact_id": "ulid_123",          # Lifecycle ID
    "content_id": "sha256_abc",         # Content hash
    "artifact_type": "plan",             # Type

    # Provenance (from artifact.created event)
    "producer": {
        "actor": "human:alice",
        "operation": "propose_plan",
        "timestamp": "2026-01-27T10:00:00Z",
        "surface": "cli"  # cli|mcp|lsp|ci
    },
    "inputs": [
        {"artifact_id": "ulid_dep1", "content_id": "sha256_dep1"}
    ],
    "payload_manifest": [
        {"path": "bundle.cypher", "bytes": 1024, "sha256": "..."}
    ],

    # Governance State (from lifecycle events)
    "status": "executed",  # created|validated|approved|executed|rejected|superseded
    "risk_class": "external_side_effect",  # Computed, not claimed
    "risk_reasons": ["writes to external Neo4j"],

    # Approval Chain (if applicable)
    "approval_artifact_id": "ulid_approval_456",
    "force_ack": true,
    "approval_scope": "neo4j-load",

    # Execution Result (if applicable)
    "result_artifact_id": "ulid_result_789",
    "erasure_cost": {...},
    "creation_summary": {...},
    "executor": "handler:neo4j",

    # Timestamps
    "created_at": "2026-01-27T10:00:00Z",
    "validated_at": "2026-01-27T10:00:01Z",
    "approved_at": "2026-01-27T10:05:00Z",
    "executed_at": "2026-01-27T10:10:00Z"
}
```

### Event Bindings by Type

**Required Events:**
- All tracked artifacts: `artifact.created`
- Artifacts with type packs (plan/approval/bundle): `artifact.validated`
- Plans requiring approval: `artifact.approved` (if risk ∈ {MUTATION_DESTRUCTIVE, EXTERNAL_SIDE_EFFECT})
- Executed plans: `artifact.executed`

**Optional Events:**
- `artifact.rejected` - if validation fails or approval denied
- `artifact.superseded` - if newer version replaces this artifact
- `constraint.evaluated` - if constraint engine runs
- `invariant.checked` - if invariant checker runs
- `execution.logged` - if execution phases logged

**Event Absence Semantics:**
- Missing `artifact.validated` → artifact not validated (error)
- Missing `artifact.approved` + risk=destructive → approval required (error)
- Missing `artifact.executed` + status=executed → inconsistent state (error)

---

## Part D: Strictness Levels and Enforcement Rules

### Three Enforcement Levels

| Level | Behavior | Use Case | Exit Code |
|-------|----------|----------|-----------|
| **WARN** | Report violation, continue execution, CI passes | Soft recommendations, future requirements, style issues | 0 |
| **FAIL** | Report violation, block CI, allow local execution | Structural issues, missing metadata, deprecated patterns | 1 (CI only) |
| **ENFORCE** | Report violation, block all execution (local + CI) | Critical governance violations, safety issues | 1 (always) |

### Enforcement Rule Registry

**File:** `irrev/artifact/validation_rules.py` (NEW)

```python
from enum import Enum

class Severity(Enum):
    WARN = "warn"
    FAIL = "fail"
    ENFORCE = "enforce"

VALIDATION_RULES = {
    # ========================================================================
    # VAULT CONTENT RULES
    # ========================================================================

    "vault.concept.missing_frontmatter": {
        "description": "Concept note missing required YAML frontmatter",
        "severity": Severity.FAIL,
        "scope": "vault:concept",
        "applies_to": ["content/concepts/*.md"],
        "check": "has_frontmatter",
        "required_keys": ["role", "layer", "canonical"],
    },

    "vault.concept.invalid_layer": {
        "description": "Concept layer not in allowed set",
        "severity": Severity.FAIL,
        "scope": "vault:concept",
        "check": "frontmatter_enum",
        "field": "layer",
        "allowed_values": ["primitive", "first-order", "mechanism", "accounting", "selector", "foundational", "failure-state", "meta-analytical"],
    },

    "vault.concept.layer_dependency_violation": {
        "description": "Primitive concept depends on non-primitive (layer violation)",
        "severity": Severity.WARN,  # Soft constraint, not blocking
        "scope": "vault:concept",
        "check": "layer_dependencies_valid",
        "rationale": "Primitives should be foundational; cross-layer deps create coupling",
    },

    "vault.diagnostic.missing_role": {
        "description": "Diagnostic note missing 'role: diagnostic' in frontmatter",
        "severity": Severity.FAIL,
        "scope": "vault:diagnostic",
        "check": "frontmatter_literal",
        "field": "role",
        "expected": "diagnostic",
    },

    "vault.template.missing_frontmatter": {
        "description": "Template missing example frontmatter (templates must show structure)",
        "severity": Severity.FAIL,
        "scope": "vault:template",
        "check": "has_frontmatter",
    },

    "vault.export.not_ignored": {
        "description": "Export file not in .gitignore (exports should be ephemeral)",
        "severity": Severity.WARN,
        "scope": "vault:export",
        "check": "gitignored",
        "rationale": "Exports are regenerable; committing them creates diff noise",
    },

    "vault.ruleset.invalid_schema": {
        "description": "Ruleset TOML does not match RulesetSchema",
        "severity": Severity.ENFORCE,  # Blocks execution
        "scope": "vault:ruleset",
        "check": "toml_schema_valid",
        "schema": "constraints.schema.RulesetSchema",
        "rationale": "Invalid rulesets cannot be loaded by constraint engine",
    },

    "vault.config.malformed_yaml": {
        "description": "YAML config file malformed (parse error)",
        "severity": Severity.ENFORCE,
        "scope": "vault:config",
        "check": "yaml_parseable",
    },

    # ========================================================================
    # ARTIFACT SYSTEM RULES
    # ========================================================================

    "artifact.plan.validation_failed": {
        "description": "Plan artifact failed type pack validation",
        "severity": Severity.ENFORCE,
        "scope": "artifact:plan",
        "check": "type_pack_valid",
        "rationale": "Plans with invalid schema cannot be executed",
    },

    "artifact.approval.validation_failed": {
        "description": "Approval artifact failed type pack validation",
        "severity": Severity.ENFORCE,
        "scope": "artifact:approval",
        "check": "type_pack_valid",
    },

    "artifact.bundle.validation_failed": {
        "description": "Bundle artifact failed type pack validation",
        "severity": Severity.ENFORCE,
        "scope": "artifact:bundle",
        "check": "type_pack_valid",
    },

    "artifact.missing_created_event": {
        "description": "Artifact has no artifact.created event (orphaned artifact_id)",
        "severity": Severity.ENFORCE,
        "scope": "artifact:*",
        "check": "has_event",
        "event_type": "artifact.created",
        "rationale": "All artifacts must have creation event for provenance",
    },

    "artifact.missing_validated_event": {
        "description": "Artifact with type pack has no artifact.validated event",
        "severity": Severity.ENFORCE,
        "scope": "artifact:plan|approval|bundle",
        "check": "has_event",
        "event_type": "artifact.validated",
        "rationale": "Type pack artifacts must be validated before approval/execution",
    },

    "artifact.destructive_missing_approval": {
        "description": "Destructive plan executed without approval",
        "severity": Severity.ENFORCE,
        "scope": "artifact:plan",
        "check": "approval_required",
        "risk_classes": ["mutation_destructive", "external_side_effect"],
        "rationale": "Destructive operations require explicit approval (governance invariant)",
    },

    "artifact.destructive_missing_force_ack": {
        "description": "Destructive plan approved without force_ack=true",
        "severity": Severity.ENFORCE,
        "scope": "artifact:approval",
        "check": "force_ack_required",
        "rationale": "Destructive approvals require explicit acknowledgement",
    },

    "artifact.executed_missing_result": {
        "description": "Executed plan has no result_artifact_id",
        "severity": Severity.FAIL,  # Fail but don't block execution (result emitted after execution)
        "scope": "artifact:plan",
        "check": "has_result_artifact",
        "rationale": "Interface invariance: executions emit result artifacts",
    },

    "artifact.executed_missing_surface": {
        "description": "Executed plan has no surface attribution (cli/mcp/lsp/ci)",
        "severity": Severity.FAIL,
        "scope": "artifact:plan",
        "check": "has_surface_attribution",
        "rationale": "Interface invariance: different transports must leave same attribution trail",
    },

    # ========================================================================
    # CROSS-SYSTEM RULES
    # ========================================================================

    "cross.vault_references_missing_artifact": {
        "description": "Vault note references artifact_id that doesn't exist",
        "severity": Severity.WARN,
        "scope": "vault:*",
        "check": "artifact_references_valid",
        "rationale": "Broken references indicate stale content or missing artifacts",
    },

    "cross.artifact_references_missing_vault_note": {
        "description": "Artifact references vault note that doesn't exist (broken wiki-link)",
        "severity": Severity.WARN,
        "scope": "artifact:*",
        "check": "vault_references_valid",
    },
}

def get_rules_for_scope(scope: str) -> list[dict]:
    """Get all validation rules for a given scope (e.g., 'vault:concept')."""
    return [
        {**rule, "rule_id": rule_id}
        for rule_id, rule in VALIDATION_RULES.items()
        if rule["scope"] == scope or rule["scope"].endswith(":*")
    ]

def get_rules_by_severity(severity: Severity) -> list[dict]:
    """Get all validation rules at a given severity level."""
    return [
        {**rule, "rule_id": rule_id}
        for rule_id, rule in VALIDATION_RULES.items()
        if rule["severity"] == severity
    ]
```

### Severity Assignment Strategy

**ENFORCE (blocks execution):**
- Type pack validation failures (plan/approval/bundle)
- Missing required events (artifact.created, artifact.validated)
- Governance violations (destructive without approval/force_ack)
- Malformed config files (cannot be parsed)
- Invalid rulesets (constraint engine cannot load)

**FAIL (blocks CI, allows local):**
- Missing frontmatter on vault content
- Invalid enum values in frontmatter
- Missing result artifacts after execution
- Missing surface attribution
- Structural issues in content

**WARN (report only):**
- Layer dependency soft constraints
- Ephemeral exports not .gitignored
- Cross-system reference staleness
- Style/convention violations

---

## Part E: Migration Plan

### Phase 1: Discovery & Inventory (Week 1)

**Goal:** Understand current state without breaking anything

**Tasks:**
1. ✅ Create `content/meta/artifact-types.toml` (vault type registry)
2. ✅ Extend `irrev/artifact/types/registry.py` with metadata
3. ✅ Add `irrev/artifact/validation_rules.py` (rule registry)
4. ✅ Implement `irrev artifact types` command - list all types
5. ✅ Implement `irrev artifact type-check <path>` - dry-run validation
6. ✅ Run inventory: `irrev artifact type-check content/` (WARN mode only)

**Output:**
- Inventory report showing:
  - Total files per type
  - Violations per rule (WARN/FAIL/ENFORCE counts)
  - Top 5 most common violations
  - Files without detected type

**Success Criteria:**
- No execution blocked
- Inventory completes without crashes
- Report is actionable (shows file paths + violations)

---

### Phase 2: Add Lint Rules (Week 2)

**Goal:** Integrate type checking into existing lint workflow

**Tasks:**
1. ✅ Add `irrev/commands/lint.py` integration:
   - `irrev lint --artifact-types` flag
   - Runs type validation for all vault content
   - Reports WARN + FAIL severity (ENFORCE not checked in lint)
2. ✅ Add auto-fix suggestions (no automatic edits):
   - Missing frontmatter → suggest template
   - Invalid enum value → suggest valid values
   - Layer violation → suggest refactoring
3. ✅ Update CI workflow:
   - Run `irrev lint --artifact-types` in WARN mode
   - Report violations but don't fail build
4. ✅ Document rules in `irrev/docs/ARTIFACT_TYPES.md`

**Success Criteria:**
- Lint output includes type violations
- CI reports violations but passes
- No false positives on valid content

---

### Phase 3: Gradual Enforcement (Week 3-4)

**Goal:** Raise strictness for subsets, fix violations incrementally

**Subphase 3a: Templates (Low Risk)**
1. Enforce FAIL rules on `content/_templates/*.md`
2. Fix 5 templates (add frontmatter if missing)
3. Verify: `irrev lint --artifact-types --fail-on-error content/_templates/`

**Subphase 3b: Rulesets (Critical)**
1. Enforce ENFORCE rules on `content/meta/rulesets/*.toml`
2. Validate `core.toml` against schema
3. Fix any schema violations
4. Block: Tool refuses to load invalid rulesets

**Subphase 3c: Concepts (High Value)**
1. Enforce FAIL rules on `content/concepts/*.md`
2. Audit 37 concept notes for missing frontmatter
3. Fix violations (add role/layer/canonical)
4. Verify layer dependencies
5. Raise to FAIL in CI for concepts only

**Subphase 3d: Remaining Content (Gradual)**
1. diagnostics/ → FAIL mode
2. domains/ → FAIL mode
3. projections/ → FAIL mode
4. papers/, invariants/, meta/ → FAIL mode

**Success Criteria:**
- Subsets migrate without breaking Quartz publishing
- CI fails on new violations in migrated subsets
- Existing content grandfathered (legacy flag)

---

### Phase 4: Full Enforcement (Week 5-6)

**Goal:** All content validated, all rules active

**Tasks:**
1. Enable FAIL mode for all vault content in CI
2. Legacy content flagged (optional):
   - Add `# legacy: true` frontmatter key
   - Legacy files skip strict validation (WARN only)
3. New content requires full validation (no legacy flag)
4. ENFORCE mode active for:
   - Type pack validation (plan/approval/bundle)
   - Malformed configs/rulesets
   - Governance violations
5. Add `irrev artifact fix <path>` auto-repair (interactive):
   - Prompts user to add missing frontmatter
   - Suggests valid enum values
   - Does NOT auto-edit without confirmation

**Success Criteria:**
- All new content passes validation
- Legacy content explicitly marked
- No surprise breakage
- Rollback: set all FAIL → WARN

---

### Rollback Strategy

**Immediate Rollback (if things break):**
1. Set all FAIL rules → WARN in `validation_rules.py`
2. Disable `--artifact-types` flag in CI
3. Continue with WARN-only inventory mode

**Partial Rollback (if subset breaks):**
1. Revert subset to WARN mode (e.g., concepts only)
2. Investigate violations
3. Fix and re-enable

**Data Safety:**
- Vault content is git-tracked (always recoverable)
- Type registry is TOML (can revert commits)
- No destructive edits without user confirmation

---

### Handling Legacy Content

**Strategy:** Explicit, not implicit

**Option 1: Legacy Flag (Recommended)**
```yaml
---
role: concept
layer: primitive
canonical: true
legacy: true  # ← Skip strict validation
---
```

**Option 2: Legacy Folder**
```
content/
  _legacy/  # All files here use WARN-only mode
  concepts/  # Strict validation
```

**Option 3: Per-File Exemptions**
```toml
# In artifact-types.toml
[exemptions]
files = [
  "content/concepts/old-note.md",  # Created before strict validation
]
reason = "Predates type system"
```

**Chosen:** Option 1 (legacy flag) - most granular, doesn't require moving files

---

## Part F: Engineering Plan - Files and Functions

### New Files to Create

#### 1. `content/meta/artifact-types.toml`
**Purpose:** Vault-owned type registry for content artifacts

**Functions:** (loaded by tool, not executed)
- Defines 10 vault types (concept/diagnostic/domain/projection/paper/invariant/template/support/ruleset/config/export)
- Specifies required/optional metadata per type
- Defines location patterns and extensions
- Sets governance expectations

**Tests:** `tests/test_vault_type_registry.py`
- `test_load_vault_type_registry()` - TOML parses correctly
- `test_all_vault_types_defined()` - All expected types present
- `test_type_metadata_schema()` - Each type has required fields

---

#### 2. `irrev/artifact/validation_rules.py`
**Purpose:** Centralized validation rule registry with severity levels

**Functions:**
```python
get_rules_for_scope(scope: str) -> list[dict]
get_rules_by_severity(severity: Severity) -> list[dict]
validate_file(path: str, type_id: str) -> list[ValidationViolation]
```

**Data:**
- `VALIDATION_RULES` dict (30+ rules)
- Severity enum (WARN/FAIL/ENFORCE)

**Tests:** `tests/test_validation_rules.py`
- `test_get_rules_for_scope()` - Filter by scope works
- `test_get_rules_by_severity()` - Filter by severity works
- `test_all_rules_have_required_fields()` - Schema validation

---

#### 3. `irrev/artifact/vault_types.py`
**Purpose:** Load and query vault type registry (TOML)

**Functions:**
```python
load_vault_type_registry(path: str) -> dict
get_vault_type(type_id: str) -> dict | None
infer_vault_type(file_path: str) -> str | None  # By location pattern
validate_vault_artifact(path: str, type_id: str) -> list[str]  # Returns errors
```

**Tests:** `tests/test_vault_types.py`
- `test_load_vault_type_registry()` - Load from TOML
- `test_infer_vault_type()` - Infer from path (concepts/*.md → vault:concept)
- `test_validate_vault_artifact_concept()` - Validate concept note
- `test_validate_vault_artifact_missing_frontmatter()` - Error detection

---

#### 4. `irrev/commands/artifact_types_cmd.py`
**Purpose:** CLI commands for type system introspection

**Functions:**
```python
run_artifact_types_list(vault_path: str) -> int
    # Lists all registered types (vault + artifact system)
    # Output: table with type_id, description, linkable, requires_envelope

run_artifact_type_check(vault_path: str, path: str, severity: str) -> int
    # Dry-run validation on path (file or directory)
    # Severity filter: warn|fail|enforce|all
    # Output: violations per file, grouped by rule_id

run_artifact_type_info(vault_path: str, type_id: str) -> int
    # Show detailed info for one type (schema, rules, examples)
```

**Tests:** `tests/test_artifact_types_cmd.py`
- `test_artifact_types_list()` - List all types
- `test_artifact_type_check_file()` - Check single file
- `test_artifact_type_check_directory()` - Check directory recursively
- `test_artifact_type_info()` - Show type details

---

### Modified Files

#### 5. `irrev/artifact/types/registry.py` (EXTEND)
**Changes:**
- Add `ARTIFACT_TYPE_METADATA` dict with governance expectations
- Add `get_type_metadata()` function
- Add `list_artifact_types()` function
- Add `has_type_pack()` function

**Tests:** `tests/test_artifact_type_registry.py` (NEW)
- `test_get_type_metadata()` - Metadata lookup
- `test_list_artifact_types()` - List all types
- `test_has_type_pack()` - Check for type pack

---

#### 6. `irrev/commands/lint.py` (MODIFY)
**Changes:**
- Add `--artifact-types` flag
- Add `--fail-on-error` flag
- Integrate `validate_vault_artifact()` into lint flow
- Report type violations alongside existing lint violations

**Tests:** `tests/test_lint_artifact_types.py` (NEW)
- `test_lint_with_artifact_types()` - Integration test
- `test_lint_fail_on_error()` - CI mode

---

#### 7. `irrev/cli.py` (MODIFY)
**Changes:**
- Add `@artifact.command("types")` decorator
- Add `@artifact.command("type-check")` decorator
- Add `@artifact.command("type-info")` decorator

**Tests:** (covered by command tests)

---

#### 8. `irrev/commands/artifact_cmd.py` (MODIFY)
**Changes:**
- Extend `irrev artifact audit <id>` to show artifact type
- Add "Type:" row to output table
- Show type metadata (linkable, governance expectations)

**Tests:** `tests/test_artifact_cli.py` (EXTEND)
- `test_artifact_audit_shows_type()` - Verify type displayed

---

### Test Plan Summary

**New Test Files:**
1. `tests/test_vault_type_registry.py` - Vault type registry loading (3 tests)
2. `tests/test_validation_rules.py` - Rule registry (3 tests)
3. `tests/test_vault_types.py` - Vault artifact validation (4 tests)
4. `tests/test_artifact_types_cmd.py` - CLI commands (4 tests)
5. `tests/test_artifact_type_registry.py` - Artifact type metadata (3 tests)
6. `tests/test_lint_artifact_types.py` - Lint integration (2 tests)

**Modified Test Files:**
7. `tests/test_artifact_cli.py` - Add type display test (1 test)

**Total New Tests:** ~20 tests

**Existing Test Regression:** All 71 tests must pass

---

## Part G: Minimal Type Set Analysis

### What is the minimal set of types that yields the biggest reduction in ambiguity?

**Top 5 High-Impact Types (Implement First):**

1. **`vault:concept`** (37 files)
   - **Why:** Core ontology; most referenced; layer violations common
   - **Ambiguity Reduced:** Clarifies primitive vs first-order vs mechanism boundaries
   - **Validation:** Requires role/layer/canonical frontmatter
   - **Impact:** High - prevents concept drift

2. **`artifact:plan`** (operational)
   - **Why:** Already has type pack; executes destructive operations
   - **Ambiguity Reduced:** Separates plans from other artifact types
   - **Validation:** operation/payload/inputs schema enforced
   - **Impact:** Critical - governance safety

3. **`vault:ruleset`** (1 file currently, more expected)
   - **Why:** Defines governance policy; must be valid TOML
   - **Ambiguity Reduced:** Clarifies what's a ruleset vs config vs note
   - **Validation:** Schema must match `RulesetSchema`
   - **Impact:** High - invalid rulesets break constraint engine

4. **`vault:template`** (5 files)
   - **Why:** Low risk; easy to fix; demonstrates type system
   - **Ambiguity Reduced:** Templates vs content notes
   - **Validation:** Must have frontmatter (to show structure)
   - **Impact:** Medium - improves new content quality

5. **`vault:export`** (ephemeral)
   - **Why:** Should not be committed; common mistake
   - **Ambiguity Reduced:** Generated vs source files
   - **Validation:** WARN if not .gitignored
   - **Impact:** Medium - reduces diff noise

**Next 5 (Implement Second):**

6. **`artifact:approval`** - governance metadata
7. **`artifact:bundle`** - proof packs
8. **`vault:diagnostic`** - diagnostic tools
9. **`vault:invariant`** - invariant definitions
10. **`vault:config`** - YAML config files

**Defer (Lower Priority):**

11-15. `vault:domain`, `vault:projection`, `vault:paper`, `vault:support`, `artifact:execution_summary`, etc.

---

## Conclusion

This artifact type system proposal delivers:

✅ **Clear boundaries** - Vault content (editorial) vs artifact system (operational)
✅ **Stable schemas** - Type registry (TOML + Python) with validation rules
✅ **Enforcement levels** - WARN/FAIL/ENFORCE with severity-based blocking
✅ **Envelope mapping** - Governance artifacts get full tracking, content doesn't
✅ **Migration plan** - Phased rollout (discovery → lint → gradual → full) with rollback
✅ **Engineering plan** - 8 files (4 new, 4 modified), ~20 tests, minimal disruption

**Next Action:** Implement Phase 1 (discovery & inventory) with `irrev artifact types` command in WARN-only mode.

---

**Status:** READY FOR REVIEW
