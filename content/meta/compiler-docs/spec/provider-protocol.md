---
role: support
type: meta
generated: true
source_repo: irrev-compiler
source_kind: spec
source_path: docs/spec/provider-protocol.md
source_sha256: 6464e57e7c1eabaa4dac140010a632943f5bec3f8d002ed9567bed559c5bfa77
---

# Provider Protocol (Normative)

> Source: `docs/spec/provider-protocol.md`

## Summary

Version: 0.1 Status date: 2026-02-11

## Normative statements (extracted)

- Providers MUST implement the `Provider` protocol in `admit_core`:
- `ProviderDescriptor` MUST declare:
- 1. Dispatch MUST resolve provider by `scope_id` through `ProviderRegistry`.
- 2. Missing registry or missing provider MUST hard-fail evaluation.
- 3. The kernel MUST emit `Fact::PredicateEvaluated` for all predicates.
- 4. Provider findings returned from `eval_predicate` MUST be recorded as witness findings.
- - Identity-bearing fields MUST be schema-defined and deterministically encoded.
- - Metadata-only fields (for example timestamps) MUST be explicitly documented as non-identity.
- - Verification MUST check canonical encoding and hash consistency for identity-bearing fields.
- Provider failures MUST return `ProviderError` with:
- Errors MUST be serializable and stable across surfaces (CLI/LSP/RPC).

## Notes

- This file is generated; edit the compiler source doc instead.
