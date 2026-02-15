---
role: support
type: meta
generated: true
source_repo: irrev-compiler
source_kind: spec
source_path: docs/spec/rules.md
source_sha256: 8be4fba662650c60e79d121eb4e7786031eef5e1f143c6c9af3bf61e5d383835
---

# Rulebook (Normative)

> Source: `docs/spec/rules.md`

## Summary

Version: 0.1 Status date: 2026-02-11

## Normative statements (extracted)

- The key words `MUST`, `SHALL`, `MUST NOT`, and `SHALL NOT` are normative.
- **Rule:** Any irreversible execute/apply operation MUST require evidence of a prior admissibility check bound to the same content identity.
- **Witness obligation:** If the required binding is missing or mismatched, execution MUST fail with a hard error and MUST NOT mutate state.
- **Rule:** Artifact identity MUST be computed from canonical encoding bytes only.
- **Witness obligation:** Encoding or hash mismatch MUST produce a verification failure and prevent acceptance.
- **Rule:** Extension predicate dispatch MUST go through `ProviderRegistry` and MUST NOT use hardcoded per-provider predicate variants.
- **Witness obligation:** Missing registry or unknown scope MUST hard-fail predicate evaluation.
- **Rule:** Every provider MUST publish closure requirements (`fs`, `network`, `db`, `process`) in its descriptor.
- **Witness obligation:** Descriptor output MUST include closure flags; misdeclared behavior is a governance violation in audits.
- **Rule:** Every predicate evaluation MUST emit a predicate-evaluated witness fact, including provider predicates.
- **Witness obligation:** Witnesses MUST contain predicate evaluation facts for all evaluated predicates.
- **Rule:** Emitted admissibility witnesses and ledgered artifacts MUST carry schema identifiers.
- **Witness obligation:** Missing required schema IDs MUST fail artifact registration or verification.
- **Rule:** Evaluation order and witness fact ordering SHALL be deterministic for identical inputs.
- **Witness obligation:** Non-deterministic output MUST be treated as a test failure and release blocker.
- **Rule:** Schemas and codecs MUST define which fields are identity-bearing and which are metadata-only.
- **Witness obligation:** Identity verification MUST ignore approved metadata-only fields and reject identity-field mismatch.

## Notes

- This file is generated; edit the compiler source doc instead.
