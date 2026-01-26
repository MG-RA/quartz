---
role: doc
status: draft
canonical: false
---

# Read-only Neo4j MCP server (irrev)

This repo includes a small **read-only** MCP server that exposes a Neo4j-backed vault graph over stdio.

Implementation: `irrev/irrev/mcp/neo4j_readonly_server.py`.

## What it exposes

MCP tools:
- `note_by_id(intent, note_id)`
- `outlinks(intent, note_id, limit?)`
- `inlinks(intent, note_id, limit?)`
- `missing_failure_modes(intent, limit?)`
- `cypher_read(intent, query, params?)` (validated, bounded read-only Cypher)

Intents (required on every call):
- `analysis` | `audit` | `inspection` | `exploration`

## Running it locally (manual)

If your Neo4j is available on `http://localhost:7474`:

```powershell
.\irrev\.venv\Scripts\python.exe -m irrev.mcp.neo4j_readonly_server `
  --database irrev `
  --password $env:NEO4J_PASSWORD
```

Optional connection flags:
- `--http-uri` (default `http://localhost:7474`)
- `--user` (default `neo4j`)
- `--database` (default `irrev`)

## Using it from Codex (MCP)

Example `~/.codex/config.toml` entry (Windows):

```toml
[mcp_servers.irrev-neo4j]
command = 'C:\Users\user\code\obsidian\quartz\irrev\.venv\Scripts\python.exe'
args = ["-m", "irrev.mcp.neo4j_readonly_server", "--database", "irrev", "--password", "…"]
enabled = true
```

After updating config, restart Codex so it reloads MCP server config.

## Sample tool queries

### Fetch a note

- `note_by_id`
  - `intent`: `inspection`
  - `note_id`: `concepts/erasure-cost`

### Outbound links (top 25 by count)

- `outlinks`
  - `intent`: `inspection`
  - `note_id`: `concepts/erasure-cost`
  - `limit`: `25`

### Inbound links (top 25 by count)

- `inlinks`
  - `intent`: `inspection`
  - `note_id`: `concepts/erasure-cost`
  - `limit`: `25`

### Projections missing failure modes

- `missing_failure_modes`
  - `intent`: `audit`
  - `limit`: `200`

## Sample Cypher queries (`cypher_read`)

Validator requirements:
- Must start with `MATCH` / `OPTIONAL MATCH` / `WITH`
- Must include `RETURN`
- Must include `LIMIT <= 500`
- Rejects write-ish tokens (`CREATE`, `MERGE`, `SET`, `DELETE`, `CALL`, `LOAD CSV`, `apoc.`, …)
- Variable-length traversals must be bounded (`*1..6` max)

### Find canonical concepts (first 50)

```cypher
MATCH (n:Note:Concept)
WHERE n.canonical = true
RETURN n.note_id, n.title, n.layer
ORDER BY n.note_id
LIMIT 50
```

### Top “inlink hubs” among concepts

```cypher
MATCH (s:Note)-[r:LINKS_TO]->(t:Note:Concept)
RETURN t.note_id, t.title, sum(r.count) AS inlink_count
ORDER BY inlink_count DESC, t.note_id ASC
LIMIT 25
```

### Notes that mention a concept (direct inlinks)

```cypher
MATCH (s:Note)-[r:LINKS_TO]->(t:Note {note_id: $note_id})
RETURN s.note_id, s.title, r.count
ORDER BY r.count DESC, s.note_id ASC
LIMIT 50
```

Params:
```json
{ "note_id": "concepts/erasure-cost" }
```

### Bounded path search (≤ 4 hops)

```cypher
MATCH p=(a:Note {note_id: $a})-[:LINKS_TO*1..4]->(b:Note {note_id: $b})
RETURN length(p) AS hops, [n IN nodes(p) | n.note_id] AS note_ids
ORDER BY hops ASC
LIMIT 10
```

Params:
```json
{ "a": "concepts/erasure-cost", "b": "concepts/irreversibility" }
```

## Bases- and invariants-inspired query pack

The vault includes Obsidian Bases definitions under `content/meta/bases/` and an audit report under
`content/exports bases/Vault Structural Audit Report.md`. The queries below mirror those views using the
Neo4j-derived graph.

Note: the current Neo4j graph exposes `LINKS_TO` (wiki-link) edges. Frontmatter-only relationships like
`depends_on` are not currently ingested, so “has_dependencies” is approximated via links to concept notes.
Link counts may differ from Obsidian Bases exports because the Neo4j graph counts resolved note-to-note links
(and can track per-edge occurrences via `r.count`), while Bases uses Obsidian’s `file.links`.

### Full vault audit (like “Base - Full Vault Audit”)

#### Notes by most outbound links (weighted by occurrences)

```cypher
MATCH (n:Note)-[r:LINKS_TO]->()
RETURN n.note_id, n.title, n.folder, sum(r.count) AS outlink_occurrences
ORDER BY outlink_occurrences DESC, n.note_id ASC
LIMIT 50
```

#### Notes by most distinct outbound targets

```cypher
MATCH (n:Note)-[:LINKS_TO]->(t:Note)
RETURN n.note_id, n.title, n.folder, count(DISTINCT t) AS outlink_targets
ORDER BY outlink_targets DESC, n.note_id ASC
LIMIT 50
```

#### Orphan notes (no outlinks)

```cypher
MATCH (n:Note)
WHERE NOT (n)-[:LINKS_TO]->()
RETURN n.note_id, n.title, n.folder
ORDER BY n.note_id ASC
LIMIT 200
```

#### Isolated notes (no inlinks and no outlinks)

```cypher
MATCH (n:Note)
WHERE NOT (n)-[:LINKS_TO]->() AND NOT ()-[:LINKS_TO]->(n)
RETURN n.note_id, n.title, n.folder
ORDER BY n.note_id ASC
LIMIT 200
```

#### High-link notes (20+ distinct outbound targets)

```cypher
MATCH (n:Note)
OPTIONAL MATCH (n)-[:LINKS_TO]->(t:Note)
WITH n, count(DISTINCT t) AS outlink_targets
WHERE outlink_targets >= 20
RETURN n.note_id, n.title, n.folder, outlink_targets
ORDER BY outlink_targets DESC, n.note_id ASC
LIMIT 200
```

### Concept topology (like “Base - Concepts by Layer”)

#### Layer distribution

```cypher
MATCH (c:Note:Concept)
RETURN c.layer AS layer, count(c) AS concepts
ORDER BY concepts DESC, layer ASC
LIMIT 50
```

#### Dependency audit (top concepts by distinct outlinks to concepts)

```cypher
MATCH (c:Note:Concept)
OPTIONAL MATCH (c)-[:LINKS_TO]->(d:Note:Concept)
WITH c, count(DISTINCT d) AS deps
RETURN c.note_id, c.title, c.layer, deps
ORDER BY deps DESC, c.note_id ASC
LIMIT 50
```

#### Primitives and foundational concepts

```cypher
MATCH (c:Note:Concept)
WHERE c.layer IN ["primitive", "foundational"]
RETURN c.note_id, c.title, c.layer
ORDER BY c.layer ASC, c.note_id ASC
LIMIT 200
```

### Domain primitive coverage (like “Base - Domain Concept Dependencies”)

#### Primitive coverage table (yes/no columns)

```cypher
MATCH (d:Note:Domain)
WITH
  d,
  EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/transformation-space"}) } AS transformation_space,
  EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/erasure-cost"}) } AS erasure_cost,
  EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/persistence"}) } AS persistence,
  EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/constraint-load"}) } AS constraint_load,
  EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/difference"}) } AS difference,
  EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/constraint"}) } AS constraint,
  EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/residual"}) } AS residual
RETURN
  d.note_id,
  d.title,
  transformation_space,
  erasure_cost,
  persistence,
  constraint_load,
  difference,
  constraint,
  residual
ORDER BY d.note_id ASC
LIMIT 50
```

#### Domains missing any of the primitives

```cypher
MATCH (d:Note:Domain)
WITH
  d,
  [
    ["concepts/transformation-space", EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/transformation-space"}) }],
    ["concepts/erasure-cost", EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/erasure-cost"}) }],
    ["concepts/persistence", EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/persistence"}) }],
    ["concepts/constraint-load", EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/constraint-load"}) }],
    ["concepts/difference", EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/difference"}) }],
    ["concepts/constraint", EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/constraint"}) }],
    ["concepts/residual", EXISTS { (d)-[:LINKS_TO]->(:Note {note_id: "concepts/residual"}) }]
  ] AS checks
WITH d, [c IN checks WHERE c[1] = false | c[0]] AS missing
WHERE size(missing) > 0
RETURN d.note_id, d.title, missing
ORDER BY size(missing) DESC, d.note_id ASC
LIMIT 50
```

### Diagnostics inventory (like “Base - Diagnostics Inventory”)

#### Diagnostics with no links to concepts (proxy for “no dependencies”)

```cypher
MATCH (d:Note:Diagnostic)
OPTIONAL MATCH (d)-[:LINKS_TO]->(c:Note:Concept)
WITH d, count(DISTINCT c) AS concept_links
WHERE concept_links = 0
RETURN d.note_id, d.title, d.folder
ORDER BY d.note_id ASC
LIMIT 100
```

#### Diagnostics with very low outlink targets

```cypher
MATCH (d:Note:Diagnostic)
OPTIONAL MATCH (d)-[:LINKS_TO]->(t:Note)
WITH d, count(DISTINCT t) AS outlink_targets
RETURN d.note_id, d.title, d.folder, outlink_targets
ORDER BY outlink_targets ASC, d.note_id ASC
LIMIT 50
```

### Projections coverage (like “Base - Projections”)

#### Coverage table (core links + failure mode fields)

```cypher
MATCH (p:Note:Projection)
WITH
  p,
  (p.failure_modes IS NULL OR size(p.failure_modes) = 0) AS missing_failure_modes,
  EXISTS { (p)-[:LINKS_TO]->(:Note {note_id: "diagnostics/Failure Modes of the Irreversibility Lens"}) } AS has_failure_modes_note,
  EXISTS { (p)-[:LINKS_TO]->(:Note {note_id: "concepts/rollback"}) } AS has_rollback,
  EXISTS { (p)-[:LINKS_TO]->(:Note {note_id: "concepts/lens"}) } AS has_lens,
  EXISTS { (p)-[:LINKS_TO]->(:Note {note_id: "concepts/displacement"}) } AS has_displacement,
  EXISTS { (p)-[:LINKS_TO]->(:Note {note_id: "concepts/constraint-load"}) } AS has_constraint_load,
  EXISTS { (p)-[:LINKS_TO]->(:Note {note_id: "concepts/residual"}) } AS has_residual
RETURN
  p.note_id,
  p.title,
  missing_failure_modes,
  has_failure_modes_note,
  has_rollback,
  has_lens,
  has_displacement,
  has_constraint_load,
  has_residual
ORDER BY p.note_id ASC
LIMIT 50
```

#### Projections missing a “Failure Modes…” link

```cypher
MATCH (p:Note:Projection)
WHERE NOT (p)-[:LINKS_TO]->(:Note {note_id: "diagnostics/Failure Modes of the Irreversibility Lens"})
RETURN p.note_id, p.title
ORDER BY p.note_id ASC
LIMIT 200
```

### Invariants integrity (like “Base - Invariants”)

#### Invariants inventory (role/status/canonical)

```cypher
MATCH (i:Note:Invariant)
RETURN i.note_id, i.title, i.role, i.status, i.canonical
ORDER BY i.note_id ASC
LIMIT 50
```

#### Missing invariant cross-references (should be empty if clique-complete)

```cypher
MATCH (a:Note:Invariant), (b:Note:Invariant)
WHERE a.note_id <> b.note_id AND NOT (a)-[:LINKS_TO]->(b)
RETURN a.note_id AS missing_from, b.note_id AS missing_to
ORDER BY missing_from ASC, missing_to ASC
LIMIT 200
```

### Papers index (like “Base - Papers Index”)

#### Papers by number of distinct links

```cypher
MATCH (p:Note:Paper)
OPTIONAL MATCH (p)-[:LINKS_TO]->(t:Note)
WITH p, count(DISTINCT t) AS outlink_targets
RETURN p.note_id, p.title, outlink_targets
ORDER BY outlink_targets DESC, p.note_id ASC
LIMIT 50
```

### Link integrity / hygiene extras

#### Tag usage (notes with any tags)

```cypher
MATCH (n:Note)
WHERE n.tags IS NOT NULL AND size(n.tags) > 0
RETURN n.note_id, n.title, n.tags
ORDER BY n.note_id ASC
LIMIT 200
```

#### Duplicate basenames (ambiguous wikilink risk)

```cypher
MATCH (n:Note)
WITH last(split(n.note_id, "/")) AS stem, collect(n.note_id) AS note_ids
WHERE size(note_ids) > 1
RETURN stem, note_ids
ORDER BY stem ASC
LIMIT 200
```

#### Top inbound hubs (reference hubs)

```cypher
MATCH (s:Note)-[r:LINKS_TO]->(t:Note)
RETURN t.note_id, t.title, t.folder, sum(r.count) AS inlink_occurrences
ORDER BY inlink_occurrences DESC, t.note_id ASC
LIMIT 50
```
