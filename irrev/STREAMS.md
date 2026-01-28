Yep, you’re pointing at two missing “map pieces”:

1. **ledger is currently “one stream” in the story**, but your design is really a **ledger spine + typed sub-ledgers** pattern
2. **domain work (language) isn’t just a side quest**, it’s a pressure-test that can feed corrections back into the core vault

Let’s nail both.

---

## 1) Multiple ledgers: what you actually have is “one spine, many streams”

In the architecture map I described *the ledger* as a single append-only stream. That’s correct mechanically, but incomplete conceptually.

A better mental model:

### The Ledger Spine

**One canonical append-only event log** (JSONL) with envelopes + content-addressed payloads.

This is your invariant-friendly base because:

* append-only is auditable
* ordering exists
* you can rebuild indexes
* it composes with bundles and repro headers

### Streams (logical ledgers)

“Multiple ledgers” show up as **typed event streams within the spine**, not necessarily multiple files.

Examples:

* **execution stream**: plan/approval/result/bundle lifecycle
* **governance stream**: approvals, force_acks, denials
* **constraint stream**: `constraint.evaluated`, `invariant.checked`
* **diagnostic stream**: `lint_report`, `self_audit_report`
* **meaning stream**: `meaning@v1` rationale artifacts (why a change)
* **domain stream**: language-domain observations + derived concept candidates

Mechanically: same log file, different `event_type` / `artifact_type` + indexes.

This is the “generic ledger” you’re describing: extend by adding new **types**, not by creating new bespoke storage.

### Why this matters

It keeps decomposition clean:

* **Storage** stays boring (JSONL + CAS)
* **Semantics** grows via type packs and rulesets
* **Queries** become “views” (indexes, dashboards, Neo4j projections)

So yes: your architecture doc should explicitly include:

> **Ledger = spine. Streams = projections by type.**

---

## 2) Where to put this in the architecture map

Add a section under Ledger:

### Ledger as a “spine”

* `.irrev/ledger.jsonl` (or `artifact.jsonl`) is the canonical log
* content store holds payloads
* indexes are rebuildable projections

### Stream indexes (rebuildable)

* `.irrev/index/by_artifact_type/...`
* `.irrev/index/by_event_type/...`
* `.irrev/index/by_operation/...`
* `.irrev/index/by_ruleset_hash/...`

This matches your Neo4j story too:
Neo4j becomes a *projection of ledger + vault*, not a “database of truth”.

---

## 3) “Generic lint supports multiple rulesets” implies “generic constraint engine” + events

You already moved there with `core.toml`.

The missing explicit step is:

* constraint engine evaluates rulesets
* **emits events** into the constraint stream:

  * `constraint.evaluated` (rule id, selector result count, predicate evidence)
  * `invariant.checked` (invariant id, outcome, evidence)
* lint becomes a surface: a CLI wrapper over the constraint engine

That gives you the plug-in effect:
New domain = new ruleset = new constraints = same engine = same ledger.

---

## 4) Language analysis feeding back into the core vault

This is the fun part: language is a mirror that reflects the lens back at itself.

You’re right that “crystallized insights” from language need to feed into the irreversibility vault, but you want to do it without contaminating the core with premature domain-specific baggage.

### The pattern: Observation → Candidate → Promotion

#### A) Observation artifacts (domain-local)

In language domain work, you’ll generate a bunch of things that are true-ish but not yet stable.

Create a domain artifact type:

* `artifact:observation` (or `artifact:domain_observation`)
  Fields:
* domain: `language:english` / `language:spanish`
* phenomenon: “agreement”, “polysemy”, “pragmatic inference”
* claim (descriptive, non-prescriptive)
* evidence references (examples, corpora snippets, links)
* “implications for invariants” (optional)

These observations are **tracked**, queryable, and don’t pretend to be core concepts.

#### B) Candidate concept proposals (still not core)

Then you create:

* `artifact:concept_candidate`
  Fields:
* proposed name
* definition draft
* mapping to existing concepts (depends_on links)
* tests: what would falsify/strain it
* which leaks it patches (“concept leaking” description)

This is where you explicitly say:

> “I think the core vault is missing a handle for X.”

#### C) Promotion workflow (vault change)

Only after candidate survives pressure:

* you add/modify a **core concept note** in the vault (git-tracked)
* you attach a meaning/rationale artifact that links:

  * observation ids
  * candidate id
  * before/after lint reports
  * invariant rationale

So language becomes a **generator of structured pressure**, not a chaotic source of new core terms.

---

## 5) “Maybe the concepts are leaking in ways not clear now”

That’s extremely plausible, and language is one of the best leak detectors because it forces you to confront:

* **implicit constraints** (what speakers assume without saying)
* **propagation** (how meaning flows across clauses and context)
* **erasure asymmetry** (how hard it is to retract a conversational implication)
* **governance** (who gets to define meanings in a community)
* **decomposition** (type systems: nouns/verbs vs roles/facets)

A very likely “core leak” language exposes:

* you may need a sharper primitive for **context-binding** (how interpretation is anchored)
* or **ambiguity absorption** as a first-class mechanism (language constantly pays cost by offloading to shared context)

You don’t need to guess now. Your system can *measure* it:
observations accumulate → candidate emerges → promotion justified.

---

## 6) Tiny concrete next step

Update your `Architecture Map.md` with two additions:

1. **Ledger Spine + Streams**
2. **Observation→Candidate→Promotion loop** for domain work feeding core

If you want, paste your current `Architecture Map.md` draft and I’ll rewrite it with these two inserts, keeping your vocabulary consistent (vault/engine/execution/projection/ledger).
