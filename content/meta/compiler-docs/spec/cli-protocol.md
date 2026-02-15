---
role: support
type: meta
generated: true
source_repo: irrev-compiler
source_kind: spec
source_path: docs/spec/cli-protocol.md
source_sha256: 9c1f3a3cc626bb30c216fb8f9e1cb64b2e78dcfbdfe3a42e9992c751add60f29
---

# CLI Ceremony Protocol (Normative)

> Source: `docs/spec/cli-protocol.md`

## Summary

Version: 0.1 Status date: 2026-02-11

## Normative statements (extracted)

- 1. `declare-cost` MUST bind witness hash, snapshot hash, and program reference.
- 2. `check` MUST validate the declared event and artifact hashes before emitting `admissibility.checked`.
- 3. `execute` MUST require a prior checked event id and MUST re-verify referenced hashes before emitting `admissibility.executed`.
- `event_id` values MUST be derived from canonical payload bytes and re-checkable during verification.
- Execute MUST fail if the referenced checked event is missing or invalid.
- When a meta registry is present, artifact schema ids and scope ids MUST be registry-valid.
- Ledger writes SHALL be append-only and duplicate event ids MUST be rejected.
- Observation-oriented commands may emit witnesses and artifacts without passing through execute, but MUST remain verifiable and content-addressed.
- 1. Scope observation mode MUST remain read-only and emit a facts bundle artifact.
- 2. Ruleset check mode MUST route predicate dispatch through `ProviderRegistry`.
- 3. Ruleset witnesses MUST include rule and predicate evaluation trace facts.
- 1. `show --quiet` MUST print canonical payload hash as `sha256:<hash>`.
- 2. `show` and `explain` hash resolution MUST be schema-first (decode then detect).
- 3. `explain` ordering MUST be deterministic for rules, predicate trace, and findings.
- 4. `status --json` MUST emit stable top-level sections: `repo`, `ledger`, `governance`, `scopes`.
- 5. `log --source ledger` MUST support deterministic filtering for `--since`, `--scope`, and `--verdict`.

## Notes

- This file is generated; edit the compiler source doc instead.
