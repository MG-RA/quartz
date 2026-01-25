# Plan: `irrev junctions` (Ollama + Chroma)

Purpose: surface candidate “missing concepts” by detecting **routing pressure** in conversation logs (LLM transcripts + vault conversation notes), then overlaying candidates onto the existing vault dependency graph.

This is an **assistive** tool: it produces evidence and ranked candidates, not promotions. “Promotion” stays a human-gated step.

---

## Priority 1: Concept definition analysis (inside-out)

Before analyzing conversations for “missing concepts”, first mine the vault’s **existing concept definitions** for hidden structure and enforcement points.

Rationale:
- The vault’s leverage comes from a small, stable **core vocabulary**.
- If core concepts are role-pure and boundary-clear, “missing concept” detection becomes cleaner (fewer false positives that are just definition drift).
- The concept-only graph already contains routing-pressure signals (in-degree hubs, shortest-path spine); those are usually the “hidden gems”.

Treat this as the first deliverable.

### What to analyze (per concept)

For a targeted set of load-bearing concepts (start with top in-degree / hub-class candidates):

1. **Role purity**: definition doesn’t smuggle operators/prescriptions (Decomposition discipline).
2. **Dependency fidelity**: dependencies are necessary + actually used; missing dependencies are added explicitly.
3. **Boundary clarity**: “What this is NOT” prevents common conflations and reification.
4. **Ontological status** (when relevant): clarify whether the concept is an object, aggregation, operator-pattern, or diagnostic label.

### Suggested outputs

- `concept_audit.md`: per-concept checklist findings + suggested edits (human review).
- Optional later: `concept_audit.json` for tooling/CI integration.

## Goals

- Make the core concept vocabulary more explicit before hunting for new concepts.
- Deterministically ingest a corpus of conversations into a normalized local store.
- Extract “concept-shaped” phrases and filter against the vault’s canonical concept names + aliases.
- Cluster paraphrases into semantic roles (using local embeddings via Ollama).
- Overlay clusters onto the concept graph to estimate “ghost edges” + routing impact.
- Generate a Markdown/JSON report that is copy/paste-ready for concept creation workflows.

## Non-goals

- No automatic concept creation in `/content/concepts/` without an explicit user command.
- No “truth” claims; scores are heuristics.
- No remote services required (default: local-only via Ollama + local Chroma persistence).

---

## CLI shape (fits current `irrev` style)

Add a new command group:

- `irrev junctions ingest <path>` (and optional `--glob`, `--role conversation`)
- `irrev junctions extract`
- `irrev junctions embed`
- `irrev junctions cluster`
- `irrev junctions overlay`
- `irrev junctions report`
- `irrev junctions promote <cluster-id|phrase>` (optional later; generates a stub concept note, never commits)

Suggested top-level behavior:

```bash
uv run irrev -v ../content junctions ingest ./conversations/
uv run irrev -v ../content junctions extract --min-freq 3
uv run irrev -v ../content junctions embed --ollama-model nomic-embed-text
uv run irrev -v ../content junctions cluster --threshold 0.85
uv run irrev -v ../content junctions overlay --score betweenness
uv run irrev -v ../content junctions report --top 20 --format md
```

---

## Data layout (local, deterministic)

Convention: write state under the **vault root** (the directory passed via `-v/--vault`), not the repo root.

Rationale:
- keeps multiple vaults isolated
- keeps reproducibility local to the vault
- makes deletion/archival clean (vault folder is self-contained)

This should be a convention, not a hard requirement: allow an override like `--state-dir` later if needed.

Write in a single tool directory:

- `<vault>/.irrev/`
  - `corpus/`
    - `docs.jsonl` (normalized documents; append-only with stable IDs)
  - `junctions/`
    - `candidates.json` (phrase-level stats + contexts)
    - `clusters.json` (cluster → variants + representative)
    - `overlay.json` (cluster → ghost edges + scores)
    - `report.md` / `report.json`
  - `chroma/` (Chroma persistence directory)

Notes:
- Use stable document IDs: hash of normalized text + source path + timestamp bucket (or just hash(path+content)).
- Keep the entire pipeline re-runnable; outputs should be fully reproducible given the same corpus + settings.

---

## Stage 1: Corpus ingestion

### Inputs

- Markdown chat exports (ChatGPT/Claude) in a folder.
- Vault-internal notes with `role: conversation` (optional, later).
- Optional: provider APIs (paged sync) for chats you explicitly mark as “dataset”.

### Normalization

For each document:
- Strip frontmatter (store separately).
- Keep plaintext content.
- Record metadata:
  - `source_path`
  - `source_kind` (`md_export`, `vault_note`, …)
  - `created_at` (best-effort)
  - `title` (from first heading or filename)

### Output format (`docs.jsonl`)

One JSON object per line:

```json
{
  "doc_id": "sha256:…",
  "source_path": "conversations/foo.md",
  "title": "Foo",
  "text": "…normalized body…",
  "frontmatter": { "role": "conversation" }
}
```

---

## Stage 1b (optional): API ingestion (paged sync)

If you want to fetch long conversations directly from APIs, design this as a **separate ingestion source** that produces the same normalized `docs.jsonl` rows as file-based ingestion.

### Requirements

- **Allowlist-only**: only fetch chats you explicitly mark (IDs in a file) or that match an explicit query/tag filter.
- **Paged fetching**: handle cursor/page-token/offset pagination without loading everything in memory.
- **Checkpointing**: persist per-provider sync state so runs are resumable and idempotent.
- **Rate limiting**: respect provider limits with backoff + `Retry-After` when available.
- **Local-first**: keep tokens in env vars, never write secrets to `.irrev/`.

### CLI sketch

```bash
# Fetch only explicitly approved chats
uv run irrev -v ../content junctions ingest api --provider <provider> --allowlist ./allowlist.json

# Incremental sync (provider-specific semantics)
uv run irrev -v ../content junctions ingest api --provider <provider> --allowlist ./allowlist.json --since 2026-01-01
```

Suggested flags:
- `--provider <name>` (e.g. `openai`, `anthropic`, `slack`, `discord`, `github`, …)
- `--allowlist <file>` (JSON/YAML containing chat/thread IDs and optional labels)
- `--page-size <n>` (best-effort; provider may ignore)
- `--since / --until` (time-bounded sync, if supported)
- `--resume` (default on; use checkpoint files)
- `--dry-run` (list what would be fetched without storing)

### Allowlist format

Keep it simple and auditable (example JSON):

```json
{
  "provider": "example",
  "chats": [
    { "id": "chat_123", "label": "junctions-dataset", "notes": "ok to embed" },
    { "id": "chat_456", "label": "debug-session" }
  ]
}
```

### Implementation sketch

- Add a `ConversationSource` abstraction:
  - `iter_conversations() -> Iterator[Conversation]`
  - `iter_messages(conversation_id) -> Iterator[Message]` (paged internally)
- Add a `Paginator` helper that supports common patterns:
  - cursor token (next page token)
  - offset + limit
  - “before/after” timestamps
- Persist checkpoint state in `.irrev/corpus/sync_state.json`:
  - last completed conversation ID
  - per-conversation last message cursor/timestamp
  - provider + config hash (so changing auth/model/filter doesn’t silently reuse stale cursors)

### Normalization for long conversations

For very long chats, store both:

- a conversation-level document (`doc_id = sha256(conversation_id + full_text)`), and
- message/turn-level segments (recommended for extraction + retrieval later), e.g.:
  - `parent_doc_id`
  - `segment_id`
  - `speaker` / `role`
  - `timestamp`

This keeps phrase extraction windowed (“same turn / same paragraph”) while still allowing whole-conversation review in the report.

### Practical note: “Research folder” / curated datasets

If you’re pressure-testing in a curated folder (e.g., a “research” folder) and only want *some* chats included:

- Prefer exports you can treat as plain Markdown (or JSON you can losslessly convert to Markdown-ish text).
- Keep a vault-local allowlist file (IDs or filenames) that defines the dataset boundary.
- Ingest should remain “dumb”: it’s fine if the source is just files you manually exported into `content/conversations/` (or similar).

## Stage 2: Phrase extraction (MVP first)

### MVP extraction (no NLP deps)

Start with a deterministic heuristic extractor:
- Extract candidate phrases from:
  - Markdown headings
  - bolded terms
  - quoted “X is …” / “call this X” patterns
  - `[[wikilinks]]` (if present in logs)
- Extract nouny sequences via regex:
  - `([a-z][a-z0-9]+(?:[- ][a-z0-9]+){0,4})` with stopword filtering

Keep parsing intentionally minimal. Only extract structure you can justify structurally (headings/emphasis/quotes/definitional frames). Anything more risks false precision; adapters can come later.

### Filter known concepts

Load from vault:
- canonical concept names from `content/concepts/*.md` (basename)
- aliases from frontmatter `aliases:` (already supported by `load_vault`)

Drop candidates that match:
- concept name (case-insensitive)
- alias (case-insensitive)

### Stats to compute

- frequency (document count + total mentions)
- co-occurrence with known concepts (windowed: same paragraph / same turn)
- contexts: store N short snippets with doc_id + line offsets

### Output

- `candidates.json` list of:
  - `phrase`
  - `freq_total`, `freq_docs`
  - `contexts[]`
  - `cooccurs[]`

---

## Stage 3: Embeddings via Ollama

### Ollama integration

Assume a local Ollama server is running (default URL: `http://localhost:11434`).

Config flags:
- `--ollama-url`
- `--ollama-model` (default: `nomic-embed-text`)
- `--batch-size`
- `--embed-dim` (optional; when supported by the model/provider)
- `--embed-instruction` (optional; instruction-tuned embedding models can use this to improve clustering/retrieval)

Implementation notes:
- Add an embedding provider abstraction:
  - `Embedder` interface: `embed(texts: list[str]) -> list[list[float]]`
  - `OllamaEmbedder` implementation calling the Ollama embeddings endpoint
- Cache embeddings by `sha256(text)` to avoid recompute.

### Model choice: Qwen3 Embedding

If you plan to use the Qwen3 embedding family locally:

- Keep the provider abstraction unchanged; you only swap `--ollama-model` (or implement a second provider if you serve embeddings via something other than Ollama).
- Decide an `--embed-dim` up front, because vector DB collections generally require a consistent dimension.
  - Practical defaults: `1024` or `1536` for speed/storage.
  - Only use very high dims (e.g. `4096`) if you have a clear accuracy need and can afford disk/RAM growth.
- If the model supports an embedding “instruction”, treat it as part of the embedding cache key (changing it invalidates cached vectors).

### Storage: Chroma

Persist embeddings in local Chroma:
- collection: `junction_phrases`
- id: `sha256(phrase)`
- metadata: `{ "phrase": "...", "freq_total": 12, "freq_docs": 5 }`

Chroma note:
- Use one collection per embedding configuration (model + dimension + instruction), or encode those settings into the collection name to prevent mixing incompatible vectors.

---

## Stage 4: Clustering

### Approach

Cluster phrase embeddings into “semantic roles”.

MVP clustering:
- compute pairwise similarity (cosine)
- build clusters by threshold / union-find (deterministic ordering)

Later upgrade:
- HDBSCAN or agglomerative clustering (still deterministic when seeded)

### Outputs (`clusters.json`)

Each cluster:
- `cluster_id`
- `representative_phrase`
- `variants[]`
- `centroid` (optional)
- aggregated stats (sum frequencies, doc coverage)

---

## Stage 5: Graph overlay (“ghost nodes”)

### Inputs

- `DependencyGraph` of concepts (concept-only).
- For each cluster:
  - co-occurring known concepts
  - (optional) direct extracted “edges” from patterns like “X depends on Y”

### Ghost edges

Heuristic: a cluster “connects to” any known concept that:
- appears in the same paragraph/turn more than K times, or
- is frequently co-mentioned in definitional sentences about the cluster

### Scoring

Produce multiple scores (report can show all):
- **cross-layer reach**: number of distinct layers among ghost-edge neighbors
- **degree pressure**: sum of in-degrees of neighbor concepts (routing into hubs)
- **betweenness proxy**: compute approximate betweenness impact on a **local subgraph** (neighbors + neighbors-of-neighbors)
  - This is not “ranking for optimization”; it’s detecting junction pressure.
  - Directional signal matters more than numeric accuracy.

### Output (`overlay.json`)

Per cluster:
- `ghost_edges`: `[{ "to": "constraint-load", "weight": 0.42 }, …]`
- scores: `cross_layer_reach`, `betweenness`, `repair_pressure` (later)

---

## Stage 6: Report generation

Formats:
- Markdown (default): ready for a “candidate concept” review meeting
- JSON: machine-readable for further automation

Report sections per cluster:
- frequency stats
- representative phrase + variants
- ghost edges (sorted)
- scores (with short interpretation)
- top contexts (snippets)
- “human gate” checklist:
  - necessity test
  - substitution test
  - proliferation test

---

## Phase plan (implementation order)

### Phase 1 (ship first): Concept audit report (no conversations)

- Add a report generator that:
  - loads the concept-only graph
  - lists top in-degree concepts and hub-class concepts (if configured)
  - emits a per-concept audit checklist (role purity, dependency fidelity, boundary clarity)
- Keep it read-only and evidence-first (links to the source notes).

Deliverable: a `concept_audit.md` that surfaces “hidden gems” and definition issues from inside the existing framework.

### Phase 2 (ship MVP): Conversation ingestion + raw candidate phrases

- Add `irrev junctions ingest`
- Add `irrev junctions extract` (regex + definitional heuristics)
- Add `irrev junctions report` (no embeddings/clustering yet; just ranked phrases)

Deliverable: a stable “unknown phrase frequency + context” report that already reduces manual scanning.

### Phase 3 (Ollama + Chroma)

- Add embedding provider abstraction + Ollama implementation
- Add Chroma persistence + caching
- Add `irrev junctions cluster` (threshold clustering)

Deliverable: paraphrase clusters instead of raw phrases.

### Phase 4 (graph overlay)

- Add `overlay` scoring pass
- Add `betweenness` or proxy scoring
- Include cross-layer reach + hub proximity

Deliverable: ranked junction candidates with “ghost edges” into the existing concept graph.

### Phase 5 (refinement)

- “repair pressure” detection (clarification markers: “i mean”, “by that i mean”, “call this”, “not X but Y”, repeated redefinitions)
- Optional: vault-internal `role: conversation` ingestion
- Optional: `promote` command that generates a stub concept note (never auto-writes unless confirmed)

---

## Dependencies (optional extra)

Prefer optional extras so core `irrev` stays lightweight:

```toml
[project.optional-dependencies]
junctions = [
  "chromadb",
  "httpx",
]
```

If/when NLP improves:

```toml
junctions-nlp = [
  "spacy",
  "scikit-learn",
]
```

---

## Safety / privacy

- Default is local-only embeddings (Ollama on localhost).
- Do not send content off-machine unless the user explicitly opts into a remote provider.
- Support a `--redact` mode (later): strip code blocks, secrets, and paths before embedding.

---

## Open design questions

1. `.irrev/` location: default to vault root (`<vault>/.irrev`), with an optional override for unusual setups.
2. Conversation parsing: treat everything as plain Markdown text at first; add adapters only if you can justify the structure gain without false precision.
3. Betweenness scoring: approximate on a local subgraph (neighbors + neighbors-of-neighbors) is correct here; document that this is junction detection, not numeric optimization.

---

## Keep this invariant (tool mirrors framework)

Append-only corpus + stable doc IDs + hash-based cache invalidation + re-runnability are not just engineering neatness. They enforce an irreversibility-accounting discipline inside the tool itself.

Do not loosen this later.

---

## Optional: local LLM assist (Ministral / other 14B)

If you also want a locally hosted instruct model (e.g. a ~14B model with a large context window) in the loop, keep it *optional* and *non-authoritative*:

Good uses (assistive, low risk):
- Cluster labeling: propose a human-readable “semantic role” name for each cluster based on its variants + top contexts.
- “Repair pressure” extraction: identify clarification/definition passages and return spans for citation in the report.
- Stub drafting (human-gated): generate a candidate concept note skeleton from a cluster’s evidence.

Avoid using the LLM for:
- deciding promotion (that’s the human gate)
- inventing dependencies (only suggest; always show evidence + co-occurrence stats)

Implementation sketch:
- Add `LLMClient` interface (separate from embeddings).
- Default off; run only when `--llm-provider` is set.
- Hard-require structured output (`json`) and keep temperature low for stability.
