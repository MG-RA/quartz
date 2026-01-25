# AGENTS.md (repo instructions)

This repo contains two related parts:

- `content/`: an Obsidian-style vault consumed by Quartz (Markdown notes + frontmatter).
- `irrev/`: a Python tool that lints/compiles the vault (registry generation, hub detection, context packs).

## Vault structure conventions

- Notes are organized by **role folders** (`concepts/`, `papers/`, `diagnostics/`, `domains/`, `invariants/`, `meta/`, `projections/`).
- Canonical definitions live in `content/concepts/` (stable vocabulary).
- Avoid **duplicate note basenames** (e.g. two different `Irreversibility.md`), because `[[wikilinks]]` become ambiguous.

## Registry files (generated regions)

- The Registry note contains a generated region delimited by markers:
  - `<!-- GENERATED: ... -->`
  - `<!-- END GENERATED -->`
- Do not hand-edit the generated tables; regenerate/update them with the tool.

## Preferred linking hygiene

- Diagnostics should generally reference the Registry (and Registry sections) rather than depending on narrative papers.
- Keep concept notes "clean": concepts should not depend on papers.

## Graph axes (next step)

When the graph starts to feel large, the next move is usually not "add more"—it's to introduce axes so you can view one slice at a time.

### 1) Role axis (what kind of node is this?)

Most nodes fall into one of these roles:

- invariant
- diagnostic check
- failure mode
- projection / domain case
- operator note / usage guide
- historical instantiation

Once nodes are tagged by role, a lot of apparent complexity disappears.

### 2) Time axis (when does this matter?)

Some nodes are:

- pre-commitment (design-time)
- mid-flight (operational)
- post-failure (forensic)

You don't need all of them active at once; the graph looks huge when you view all temporal layers simultaneously.

### 3) Compression level (who is this for?)

You already implicitly have:

- kernel concepts (few, non-negotiable)
- working concepts (used in analysis)
- explanatory wrappers (for others)
- examples / probes (domain-specific)

Once you mark these explicitly, the "true core" is usually surprisingly small.

## Local commands (Windows / PowerShell)

- Lint vault: `irrev/.venv/Scripts/irrev.exe -v content lint`
- Check registry drift: `irrev/.venv/Scripts/irrev.exe -v content registry diff`
- Update registry in-place: `irrev/.venv/Scripts/irrev.exe -v content registry build --in-place`
- Run Python tests: `irrev/.venv/Scripts/python -m pytest -q`
- Generate a context pack (example): `irrev/.venv/Scripts/irrev.exe -v content pack concept irreversibility --explain`

## Encoding

- Keep files UTF-8 and prefer real Unicode punctuation (e.g. `→`, `—`, `–`) over mojibake sequences like `â†’`, `â€”`, `â€“`.
