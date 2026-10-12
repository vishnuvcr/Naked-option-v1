# Phase 8P Duplicate Diagnostic Runtime Amendment R5

Date: 2026-10-12  
Status: PROPOSED — developer design only; no real-data authorization

## Trigger

The first authorized real-data attempt, run [#38207005953](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38207005953), passed authorization, nonce-consumption and source-digest gates, but terminated after approximately 12 minutes with exit code 143 and a hosted-runner shutdown message. It produced no report. The cause is not proven to be OOM; do not state that as fact.

## Objective

Make the exact same aggregate-only duplicate classification feasible to execute and diagnose without relaxing schema, economic-key, signature, or privacy requirements.

## Proposed technical changes

1. Replace the all-contract Python dictionary/set accumulator with a disk-backed SQLite staging table in the ephemeral runner. Use a keyed hash of the canonical economic key as the lookup key, retain only the signature hash plus enough bounded state to identify conflicting field names, and store no raw contract keys in any uploaded output. Temporary plaintext staging must be deleted in an unconditional cleanup step.
2. Stream each part/row rather than calling `to_dict("records")` on a full part where practical. Validate every ordered part header against the exact manifest before accepting any row.
3. Emit periodic progress to the runner log only: part index/total if known, rows/option rows processed, elapsed seconds, and current temporary database size. Never emit keys, prices, raw rows, signatures, or decrypted table content.
4. Enforce a meaningful per-step timeout and record exit status, elapsed time, and safe resource telemetry where available. A timeout must create a sanitized BLOCKED receipt; it must not be mislabeled as a duplicate-data finding.
5. Preserve all R4 semantics: economic key = underlying, Greek valuation epoch, normalized actual expiry, returned strike and normalized option side; the full manifest signature excludes only the four explicitly allowed collection-provenance fields. Any non-provenance conflict blocks. No source rows are deleted or rewritten.
6. Produce a stable aggregate receipt containing source artifact ID/digest, exact code/workflow hashes, part/row counts, duplicate/identical/conflicting group counts, conflicting field names, diagnostic hash and explicit no-raw-data/no-upload flags. Do not upload the temporary database or decrypted files.
7. Keep model fitting, holdout access, feature generation, external market requests, option P&L and strategy promotion unreachable in this diagnostic workflow.

## Required gates

- Implement changes on the developer branch only and add deterministic synthetic tests for cross-part duplicates, multiple conflicts in one key, row/part permutation invariance, manifest mismatch, malformed keys, and aggregate-only output.
- Run local/synthetic CI and inspect workflow changes.
- Submit exact module/test/workflow blob hashes to the independent tester branch.
- Obtain independent code PASS, then a distinct executor-workflow/request PASS.
- Create a fresh one-use authorization request with a new nonce; the consumed R1 nonce must never be reused.
- Only after the tester issues that exact final authorization may a single real-data diagnostic run.
- Submit the resulting aggregate report to a separate tester data-result gate. Only a PASS may reopen the next schema/coverage preflight gate; no model or strategy testing before then.

## Success criteria

A complete sanitized aggregate report is produced; all input parts are accounted for; results are invariant to part/row order; every duplicate group is classified identical or conflicting; no source rows are changed; no raw/decrypted data is uploaded; and an independent tester approves the exact output.

## Non-goals

This amendment does not modify the research question, labels, method registry, model selection, validation design, holdout policy, option-entry logic or trading-cost assumptions. It does not infer anything about market predictability or profitability.

**Developer → Tester:** review this runtime amendment and its later exact implementation; keep the consumed R1 nonce invalid.
**Tester → Developer:** independently approve/reject exact R5 scope and implementation; no artifact access or model fit before fresh workflow and one-use execution gates pass.
