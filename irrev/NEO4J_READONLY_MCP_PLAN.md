---
role: plan
status: draft
canonical: false
---

# Plan: Read-only Neo4j MCP server + vault → graph loader

## Goal

Provide a **read-only** MCP server that can answer **Cypher read queries** over a Neo4j graph built from the Quartz/Obsidian vault (`content/`), using a deterministic loader that maps notes + links + frontmatter into a graph model.

Primary outcomes:
- A repeatable **vault loader** that produces a Neo4j database representing the vault’s structure.
- An MCP server exposing **read-only** query capabilities (Cypher + a few safe, typed “helper tools”).

## Non-goals

- No write/mutate tools via MCP (no `CREATE`, `MERGE`, `SET`, `DELETE`, `CALL … write`, etc.).
- No “auto-fix the vault” workflows (that stays in `irrev`).
- No new concept invention or ontology changes implied by the graph schema.
- No “LLM agent with free-form Cypher” in production without guardrails (safety posture is “query templates first”).

## Assumptions / constraints

- Vault is authoritative in Markdown (`content/`), and `irrev` already provides parsing and invariants.
- Graph is *derived state* and can be regenerated; it must not become a second source of truth.
- Read-only must be enforced by **defense in depth**:
  1) Neo4j user permissions restricted to read,
  2) driver sessions opened in read mode,
  3) server-side query validation/allowlisting.

## High-level architecture

1) **Loader (offline / batch)**
   - Input: vault directory (`content/`)
   - Output: Neo4j database (or a named database) containing nodes/edges for notes + links + metadata

2) **MCP Server (online / on-demand)**
   - Connects to Neo4j using a read-only credential
   - Exposes tools:
     - `cypher_read(query, params)` (optionally restricted)
     - “canned” queries for common vault questions (recommended)

## Graph model (schema)

### Node labels

Base node:
- `:Note`

Role labels (derived from frontmatter `role` and/or folder):
- `:Concept`, `:Projection`, `:Domain`, `:Diagnostic`, `:Paper`, `:Invariant`, `:Meta`, `:Report`

Optional auxiliary nodes:
- `:Tag` (if tags should be first-class)
- `:Folder` (optional; often simpler to store folder path on `:Note`)

### Node identity and core properties

Use a stable ID so reloads are idempotent:
- `Note.note_id`: vault-relative path without extension (e.g. `concepts/constraint-load`)

Recommended properties (all derived):
- `path` (relative path with extension)
- `title` (from first `#` heading or file stem)
- `folder`
- `role` (frontmatter)
- `type` (frontmatter)
- `layer` (concept frontmatter)
- `canonical` (frontmatter boolean)
- `tags` (list, from Obsidian tags)
- `aliases` (list, from frontmatter)
- `mtime` (file modified time, ISO string)

### Relationships

Core edges:
- `(:Note)-[:LINKS_TO {count, kinds}]->(:Note)`
  - `count`: number of occurrences of wikilinks in the source note
  - `kinds`: optional set like `["wikilink", "md_link"]`
  - `contexts` (optional): coarse usage contexts like `["definition", "not", "example", "failure-mode"]`

Frontmatter-derived edges (optional but useful):
- `(:Note)-[:DEPENDS_ON]->(:Note)` from `depends_on` lists

Tag edges (optional):
- `(:Note)-[:TAGGED_WITH]->(:Tag {name})`

Folder edges (optional):
- `(:Note)-[:IN_FOLDER]->(:Folder {path})`

### Constraints and indexes (Neo4j)

- Uniqueness constraint: `:Note(note_id)` unique
- Indexes on commonly filtered properties:
  - `:Note(role)`, `:Note(layer)`, `:Note(canonical)`
  - `:Tag(name)` (if tags are nodes)

## Loader design

### Source of truth for parsing

Prefer using `irrev`’s existing parsing code (wikilinks + frontmatter) rather than writing a second parser.

Loader steps:
1) Enumerate vault Markdown notes under `content/` (respect current role folders).
2) Parse:
   - frontmatter (YAML)
   - heading/title
   - tags
   - outbound links (wikilinks, and optionally markdown links)
3) Resolve links:
   - map wikilinks to target `note_id` using the same resolution rules as the vault tooling
   - record unresolved links separately (optional `:Unresolved` nodes or a property on the relationship)
4) Write into Neo4j:
   - `MERGE` nodes by `note_id`
   - `MERGE` relationships by `(src, dst, type)` and update `count`

### Output modes

Choose one:
- **Direct write** via Neo4j Bolt driver (simplest)
- **CSV export + `neo4j-admin import`** (fast for large vaults, but heavier operationally)

For this vault size, direct write is likely sufficient.

### Idempotency and drift handling

- Loader is rerunnable; it should:
  - Upsert nodes/edges for current files
  - Remove nodes/edges for deleted files (optional “full refresh” mode)

Two loader modes:
- `sync` (incremental-ish): upsert; optionally prune missing
- `rebuild` (clean slate): wipe target database then import

## Read-only enforcement (must-have)

### Neo4j-level permissions

- Create a dedicated Neo4j user with **read-only** role privileges (no write privileges).
- If multi-db is used, restrict to a single database.

### Driver-level enforcement

- Open sessions/transactions in read mode:
  - use Neo4j driver read transaction API (language-specific)

### Query-level enforcement (MCP server)

Implement a validator that rejects anything outside a safe subset.

Minimum safe subset:
- Allow only queries that begin with `MATCH` or `OPTIONAL MATCH` (and then `RETURN`)
- Allow `WITH` clauses
- Allow `WHERE`, `ORDER BY`, `LIMIT`, `SKIP`
- Reject:
  - `CALL` (procedures can write or leak environment info)
  - `LOAD CSV`
  - `CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`, `DROP`, `ALTER`
  - `apoc.*` (unless explicitly allowlisted and confirmed read-only)
  - variable-length patterns without explicit bounds (reject `*` and `*..` forms)
  - upper bounds above a fixed maximum (e.g. `*1..6`)

Defense-in-depth principle: even if the validator misses something, Neo4j permissions still prevent writes.

## MCP server design

### Minimal tool surface

Recommended tools (read-only):
1) `cypher_read(query: string, params?: object) -> {columns, rows}`
   - gated by validator
   - per-request timeout + row limit
   - request must include `intent` (see “Safety controls”)

2) Typed “canned” queries (preferred for everyday use; easier to secure):
   - `note_by_id(note_id)`
   - `outlinks(note_id, limit)`
   - `inlinks(note_id, limit)`
   - `hub_notes(min_outlinks, role?, layer?)`
   - `missing_failure_modes()` (based on frontmatter list or link presence)
   - `path_between(a_note_id, b_note_id, max_hops)`

3) `schema_summary()` (static, not introspective)

### Safety controls

- Request contract (required):
  - `intent`: one of `analysis | audit | inspection | exploration` (extensible, but always present)
  - log `intent` + query/template + timing + row count

- Hard limits:
  - max query time (e.g. 2–5s)
  - max returned rows (e.g. 500)
  - max hops for variable-length traversals (hard cap; not per-request configurable)
- Observability:
  - log query templates used
  - log blocked queries (for tuning the validator)

### Traversal closure lock (must-have)

Treat unbounded graph traversal as a form of “search for meaning”. Enforce a structural closure constraint:

- Reject variable-length patterns without an explicit upper bound (e.g. reject `-[:LINKS_TO*]->`)
- Reject upper bounds above a fixed maximum (e.g. clamp to `*1..6`)
- Prefer canned traversals that declare `max_hops` and clamp to the same hard maximum

## Vault → graph mapping choices (open decisions)

1) **Link resolution**
   - Use vault’s canonical resolution rules (avoid ambiguous basenames).
   - Store unresolved link targets explicitly to surface hygiene problems.

2) **Header/section links**
   - Option A: ignore and treat as note-level edges only (simplest)
   - Option B: model `:Section` nodes and `:LINKS_TO_SECTION` edges (more expressive)

3) **Tags**
   - Option A: keep `tags` as a list property on `:Note`
   - Option B: make `:Tag` nodes to support tag traversal queries

4) **Role source**
   - Prefer frontmatter `role`
   - Fallback to folder-based inference only if missing

5) **Link context capture** (optional, but high leverage)
   - Minimal version: capture the nearest heading path for each link occurrence (e.g. `["Definition"]`, `["What this is NOT"]`).
   - Coarse version (recommended if you add any context at all): map heading names into a small allowlist:
     - `definition`, `not`, `role`, `mechanism`, `failure-mode`, `example`, `notes`
   - Store as a set on the `LINKS_TO.contexts` relationship property (keep it descriptive; do not infer semantics beyond headings).

## Implementation plan (phased)

### Phase 0: Spec + interfaces
- Freeze graph schema (labels, properties, relationships, constraints).
- Decide whether `:Tag` and `:Section` exist.

### Phase 1: Loader MVP (local)
- Implement `irrev` subcommand: `irrev graph export-neo4j …` or similar.
- Connect to Neo4j; create constraints/indexes; import nodes and `LINKS_TO` edges.
- Confirm idempotent reruns on unchanged vault.

### Phase 2: MCP read-only server MVP
- Implement MCP server process that connects to Neo4j read-only.
- Add `cypher_read` + 3–5 canned queries.
- Add validator + timeouts + row limits.

### Phase 3: Integrity + invariants integration
- Validate that loader respects the “avoid duplicate basenames” constraint (surface collisions).
- Optionally add “lint views” as canned queries (orphans, high-link hubs, missing role, missing failure_modes).

### Phase 4: Ops hardening
- Document:
  - how to run Neo4j locally
  - how to run loader
  - how to run MCP server
- Add a minimal “smoke test” query set.

## Testing strategy

- Loader unit tests (if `irrev` already has a test harness):
  - stable `note_id` generation
  - wikilink resolution parity with existing tooling
  - edge count aggregation
- Integration tests (optional):
  - spin up Neo4j (local/dev) and verify a few canonical queries return expected shapes

## Risks / failure modes

- Query validator bypass → mitigated by Neo4j read-only permissions.
- Drift between vault tooling and loader parsing → mitigated by reusing `irrev` parsing code.
- Ambiguous link resolution (duplicate basenames) → treat as a first-class error surfaced by loader.
- Graph becomes “more trusted” than the vault → enforce policy: graph is derived, rebuildable, and never edited by MCP.

## Open questions to answer before building

1) Which MCP runtime/language do you want (Python to match `irrev`, or Node)?
2) Should Cypher be free-form (validated) or template-only in the first iteration?
3) Do you want section-level granularity (`:Section`), or is note-level sufficient?
4) Should the loader store link contexts (line numbers / headers), or counts only?
5) Do you want separate databases per vault snapshot date, or overwrite in-place?
