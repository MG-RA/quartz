---
role: doc
status: draft
canonical: false
tags:
  - neo4j
  - queries
  - graph
---

# Neo4j manual query pack (irrev vault graph)

This is a copy/paste query pack for Neo4j Browser (or the MCP `cypher_read` tool). It's organized around the "two-layer glasses" idea:

- `LINKS_TO` = what the text touches (mentions / references)
- `DEPENDS_ON` = what the structure requires (declared dependencies)

## Refresh the derived graph (loader)

```powershell
$env:NEO4J_PASSWORD="adminroot"
.\irrev\.venv\Scripts\irrev.exe -v .\content neo4j load --database irrev --mode sync
```

## Automatic export bundle (recommended)

If you don’t want to copy/paste queries, run the exporter:

```powershell
$env:NEO4J_PASSWORD="adminroot"
.\irrev\.venv\Scripts\irrev.exe -v .\content neo4j export --database irrev
```

This writes a dated snapshot under `content/exports/export/YYYY-MM-DD/` including:

- `*_counts.csv`
- `*_top_inlinks.csv`
- `*_top_in_depends.csv`
- `*_mentions_without_depends.csv` (empty is good)
- `*_depends_without_mentions.csv` (empty is good)
- `*_projection_community_counts.csv`
- `*_two_layer_graph.json` + `*_two_layer_nodes.csv` + `*_two_layer_edges.csv` (for `irrev/d3_graph_viewer.html`)
- `*_mentions_unlinked_definition.csv` (MENTIONS edges: definition text, unlinked + undeclared)
- `*_ghost_terms_definition.csv` + `*_mentions_graph.json` (ghost nodes from backticked terms; optional)
- `*_definition_tokens.csv` + `*_definition_tokens_graph.json` (TOKEN nodes/edges; optional; definition vocabulary probe)

## Sanity checks

### Counts (nodes, edges by type)

```cypher
MATCH (n:Note)
WITH count(n) AS notes
MATCH ()-[r:LINKS_TO]->()
WITH notes, sum(r.count) AS link_occurrences, count(r) AS link_edges
MATCH ()-[d:DEPENDS_ON]->()
RETURN notes, link_edges, link_occurrences, count(d) AS depends_edges
LIMIT 1
```

### Top inbound hubs (by `LINKS_TO` occurrences)

```cypher
MATCH (s:Note)-[r:LINKS_TO]->(t:Note)
RETURN t.note_id, t.title, sum(r.count) AS inlink_occurrences
ORDER BY inlink_occurrences DESC, t.note_id ASC
LIMIT 50
```

### Top "requirements hubs" (most incoming `DEPENDS_ON`)

```cypher
MATCH (:Note)-[:DEPENDS_ON]->(t:Note:Concept)
RETURN t.note_id, t.title, count(1) AS in_depends
ORDER BY in_depends DESC, t.note_id ASC
LIMIT 50
```

## Two-layer glasses (touch vs require)

### For a concept: what it *touches* (direct links to concepts)

```cypher
MATCH (c:Note:Concept {note_id: $note_id})-[r:LINKS_TO]->(t:Note:Concept)
RETURN t.note_id, t.title, r.count
ORDER BY r.count DESC, t.note_id ASC
LIMIT 200
```

Params:
```json
{ "note_id": "concepts/erasure-cost" }
```

### For a concept: what it *requires* (declared dependencies)

```cypher
MATCH (c:Note:Concept {note_id: $note_id})-[r:DEPENDS_ON]->(t:Note:Concept)
RETURN t.note_id, t.title, t.layer, r.from_frontmatter, r.from_structural
ORDER BY t.note_id ASC
LIMIT 200
```

### Mentions without requirements (linked, but not declared)

```cypher
MATCH (c:Note:Concept)-[:LINKS_TO]->(t:Note:Concept)
WHERE NOT (c)-[:DEPENDS_ON]->(t)
RETURN c.note_id AS src, t.note_id AS dst
ORDER BY src ASC, dst ASC
LIMIT 200
```

### Requirements without mentions (declared, but not linked in text)

```cypher
MATCH (c:Note:Concept)-[:DEPENDS_ON]->(t:Note:Concept)
WHERE NOT (c)-[:LINKS_TO]->(t)
RETURN c.note_id AS src, t.note_id AS dst
ORDER BY src ASC, dst ASC
LIMIT 200
```

## Community / bridge inspection

### Community summary (by `LINKS_TO` topology)

```cypher
MATCH (n:Note:Concept)
WHERE n.community_links_greedy IS NOT NULL
WITH n.community_links_greedy AS community, count(1) AS nodes, sum(coalesce(n.boundary_edges_links_greedy, 0)) AS boundary_edges
RETURN community, nodes, boundary_edges
ORDER BY nodes DESC, community ASC
LIMIT 50
```

### Bridge nodes (top concepts connecting communities)

```cypher
MATCH (n:Note:Concept)
WHERE n.community_links_greedy IS NOT NULL AND coalesce(n.boundary_edges_links_greedy, 0) > 0
RETURN n.note_id, n.title, n.layer, n.community_links_greedy AS community, n.bridge_links_greedy AS bridge, n.boundary_edges_links_greedy AS boundary_edges
ORDER BY boundary_edges DESC, bridge DESC, n.note_id ASC
LIMIT 50
```

## Export a graph JSON (for a local d3 viewer)

Open `irrev/d3_graph_viewer.html` in your browser, then load a JSON file produced from one of these queries.

### Export concept-only "two-layer glasses" graph

```cypher
MATCH (n:Note:Concept)
WITH collect({
  id: n.note_id,
  label: n.title,
  role: n.role,
  layer: n.layer,
  community: n.community_links_greedy
}) AS nodes
MATCH (s:Note:Concept)-[r:LINKS_TO]->(t:Note:Concept)
WITH nodes, collect({
  source: s.note_id,
  target: t.note_id,
  type: "LINKS_TO",
  weight: r.count
}) AS links
MATCH (s:Note:Concept)-[d:DEPENDS_ON]->(t:Note:Concept)
WITH nodes, links, collect({
  source: s.note_id,
  target: t.note_id,
  type: "DEPENDS_ON",
  weight: 1,
  from_frontmatter: d.from_frontmatter,
  from_structural: d.from_structural
}) AS dep_links
WITH nodes, links + dep_links AS links
RETURN {nodes: nodes, links: links} AS graph
LIMIT 1
```

In Neo4j Browser, download the single `graph` value as JSON and load it in the viewer.
