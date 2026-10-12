# Independent Tester Scope Review — Repeated Economic Contract-Time Rows Amendment R3
Date: 2026-10-12
Role branch: phase-08-prediction-tester

## Decision
**PASS_SCOPE_AMENDMENT_ONLY_WITH_RESTRICTIONS.** The amendment is accepted as a narrow handling rule for repeated economic contract-time records in the in-memory feature builder. It does not approve implementation code, artifact access with new code, a preflight rerun, model fitting or any downstream evaluation.

## Exact proposal reviewed
- Developer amendment path: `research/gates/PHASE8P_DUPLICATE_CONTRACT_SCOPE_AMENDMENT_R3_2026-10-12.md`
- Proposal blob SHA-1: `6ea73c246a2cecd158e4bf8dbbd087befafcb89a`
- Parent prediction scope R3 blob SHA-1: `018500722f88f5fb100a2e24afc3d5d97394631e`
- Triggering blocked preflight runs: [#38203577299](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38203577299), [#38203641510](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38203641510).
- Exact Greek artifact: ID 11723198817, SHA-256 `e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736`.
- Exact Run #994 prediction artifact: ID 11638738288, SHA-256 `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`.

## Independent scientific/protocol checks
- The earlier source-record uniqueness key includes `source_request_id` and `requested_relative_strike`; its `duplicate_composite_keys=0` report does not disprove that the same *economic* contract may have been returned via distinct request scopes.
- The amended economic key uses underlying, exact bar-end valuation instant, normalized expiry date, returned strike and normalized CE/PE side. Moving expiry flag/code into the compared signature (not the key) avoids silently treating one expiry/strike/side as two instruments when source flags disagree.
- The amendment compares the complete listed market, expiry, spot, IV, Greek, quality, source-provider/endpoint and cache fields. Only `source_request_id`, `requested_relative_strike`, `request_scope_sha256` and `response_sha256` are permitted to vary for economically identical rows. This prevents market values, OI/volume or Greek inputs from being averaged or selected after outcome inspection.
- Exact duplicates may be collapsed only in the derived in-memory feature aggregation, with raw input rows/artifacts unchanged and duplicate counts reported. Conflicts must remain BLOCKED and produce only aggregate counts/field names/hashes, no plaintext rows or contract-specific values.
- The key includes the underlying and canonical valuation instant, and the scope bars nearest-time joins, interpolation, forward fill and new source requests. It does not change labels, horizons, model settings, inference, test family or the holdout restriction.
- The preflight failure code alone does not establish whether repeated keys are identical or conflicting. No such empirical conclusion is accepted yet.

## Required next gates
1. Developer implementation must include the fixed schema-set guard, timestamp/date/side canonicalization, exact economic-signature comparison, deterministic exact-duplicate handling, conflict fail-closed outcome, and aggregate-only diagnostics.
2. Add synthetic tests for identical repeats with differing permitted provenance, conflicting values for every economic field category, key separation, missing key/signature columns, row permutation invariance and absence of raw-value output.
3. Submit exact code/test/workflow hashes for a distinct independent code-only review. Because the accepted module changes, the previous code PASS and workflow approval do not cover the new snapshot.
4. Update/review the schema-only executor so it pins the new code decision and approved developer commit before another artifact run. Its result is still a schema/coverage report only.
5. No model fitting until a distinct tester decision accepts an exact preflight report proving target maturity, chronological row/purge rules, holdout exclusion and the coverage gates.

**Tester → Developer:** implement only the R3 amendment, add the listed synthetic tests, and submit exact hashes for a new independent code review; do not rerun the artifact preflight yet.

**Developer → Tester:** preserve the blocked preflight receipts and the immutable R1/R2 amendment lineage. Review the new code for key identity, signature completeness, conflict handling, deterministic results and no raw-data egress; do not authorize empirical fitting.
