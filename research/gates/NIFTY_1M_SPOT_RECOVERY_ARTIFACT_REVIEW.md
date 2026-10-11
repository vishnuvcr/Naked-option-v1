# Tester Artifact Audit — Phase 7 NIFTY Spot Recovery

- Audit time (UTC): 2026-10-11
- Artifact: [Run #37 artifact 11693866249](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38116772719/artifacts/11693866249)
- Downloaded archive SHA-256: `aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216`
- GitHub artifact digest: `sha256:aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216`
- Scope: encrypted bundle and safe metadata only; no plaintext market prices were decrypted or inspected.
- Role caveat: this artifact inspection was performed in the tester role within the same connected assistant session. It is not a separate human identity or separate independent AI reviewer.

## Decision

**REQUEST CHANGES for the data-completeness gate.** Metadata integrity checks passed, but the output is a partial dataset and cannot be treated as a complete five-year one-minute panel. No additional requests, fitting/scoring, strategy testing or holdout access are authorized by this report.

## Checks that passed

1. The downloaded ZIP SHA-256 exactly matches GitHub's published artifact digest.
2. The archive contains 57 encrypted monthly data parts; all 57 are present in `dataset_manifest.json`, and every part's byte size and SHA-256 matches its manifest entry. No extra encrypted part was found.
3. Encrypted monthly part row counts sum to 8,894,387, matching the manifest's monthly row-count sum and 8,490,723 option rows + 403,664 spot rows.
4. The coverage metadata marks `plain_rows_uploaded=false`, `raw_response_persisted_unencrypted=false`, `source_artifact_encrypted_hashes_verified=true`, and reports the preserved option-row count as 8,490,723.
5. The 8,648 request-result records reconcile with 8,601 original planned requests plus 47 spot-gapfill requests. The reported cumulative wire count is 8,654; the additional six attempts are consistent with five cumulative retries and one earlier diagnostic attempt.
6. The exact-timestamp join summary is internally additive at the option-row level: 7,591,172 matched + 899,551 missing = 8,490,723 option rows.

## Blocking findings

### A1 — Six gapfill windows failed the row cap

All six failures returned HTTP 200 but were recorded as `FAILED_VALIDATION` with reason `response_row_cap_exceeded`. The request manifest's per-response `max_rows` is 12,000.

| Request ID | Window start | Window end (exclusive) | Response bytes | Failure reason |
|---|---|---|---:|---|
| GAPSPOT1M-20211011-20211119 | 2021-10-11 | 2021-11-19 | 1,212,513 | response_row_cap_exceeded |
| GAPSPOT1M-20211119-20211228 | 2021-11-19 | 2021-12-28 | 1,037,908 | response_row_cap_exceeded |
| GAPSPOT1M-20211228-20220205 | 2021-12-28 | 2022-02-05 | 1,152,214 | response_row_cap_exceeded |
| GAPSPOT1M-20220205-20220316 | 2022-02-05 | 2022-03-16 | 1,019,278 | response_row_cap_exceeded |
| GAPSPOT1M-20220316-20220424 | 2022-03-16 | 2022-04-24 | 1,046,896 | response_row_cap_exceeded |
| GAPSPOT1M-20220424-20220602 | 2022-04-24 | 2022-06-02 | 1,048,378 | response_row_cap_exceeded |

The six failed windows cover the contiguous initial period 2021-10-11 through 2022-06-02. Together they contain 6,517,187 response bytes. The metadata does not preserve response hashes for these failed payloads, and exact row counts above the 12,000 cap are not recorded.

### A2 — Historical byte counter underreported failed response bodies

- Manifest `downloaded_bytes`: 21,731,367 bytes, equal to the 41 successful gapfill responses.
- Sum of `response_bytes` across all 47 gapfill request results: 28,248,554 bytes.
- Difference: 6,517,187 bytes, exactly the six failed-validation response bodies above.

This confirms the prior counter-accounting defect in the realized artifact. It does **not** prove that the 256 MiB aggregate cap was exceeded: the sum of these 47 recorded response-body lengths is 28,248,554 bytes, below the cap. The developer has since moved byte charging before payload validation and added regression tests; the updated offline pipeline run [38117905230](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38117905230) passed.

### A3 — Encrypted data values were not independently inspected

The artifact is encrypted using a key derived from the repository's HF_TOKEN. This audit verified archive/part hashes and metadata arithmetic but did not decrypt the monthly CSVs. Therefore the row-preservation claim is supported by the run's manifest and workflow validation, not by an independent value-level re-read in this audit.

## Required developer action

1. Keep the current artifact immutable; do not overwrite or reinterpret the partial run.
2. Prepare a new, offline-only spot request manifest that splits the six failed calendar windows into smaller disjoint shards that stay safely below the 12,000-row cap. Validate complete coverage, no overlap/gaps, request IDs, per-shard date bounds and total request budget.
3. Add tests proving every response body is charged before payload parsing and that row-cap failures are surfaced with bounded metadata and no raw payload.
4. Submit the new exact manifest, budget plan and code snapshot for a fresh tester gate. The already-spent one-use authorization cannot be reused; no live request may occur until a new explicit exact-snapshot authorization exists.
5. After any future authorized run, reconcile request bytes from per-request records, including failed responses, and independently verify the new encrypted artifact's hashes and row arithmetic.

## Gate restrictions

- `live_requests_authorized=false`
- `model_fitting_authorized=false`
- `holdout_access_authorized=false`
- `strategy_testing_authorized=false`
- `live_option_requests_allowed=false`

**Tester → Developer:** Fix the six oversized windows through an offline manifest/code proposal and submit it for review; do not reuse the spent authorization.

**Developer → Tester:** Review the next exact manifest for complete temporal coverage, row-cap safety, request accounting, byte-budget enforcement and the prohibition on option refetch before any new request is allowed.


## Second review — offline split-manifest design only

- Exact developer snapshot reviewed: `9da1d081de4d43b206642b5a5643a44738ea0580`.
- Proposal: [NIFTY_1M_SPOT_GAPFILL_SPLIT_PROPOSAL.json](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/NIFTY_1M_SPOT_GAPFILL_SPLIT_PROPOSAL.json).
- The 34 proposed half-open windows cover the exact contiguous interval 2021-10-11 to 2022-06-02, with no gaps/overlap; every shard is at most 7 calendar days, and the request body bounds are aligned to 09:15 start and 15:30 end on the final included day. The proposal sets max_rows=4,000, max_response_bytes=8 MiB, max_attempts=1, max wire requests=34, zero retries, and every live/model/holdout/strategy authorization flag false.
- Offline pipeline/test run [38118242124](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38118242124) passed, including the new split-proposal coverage and bounds test.
- **Design decision: PASS WITH SCOPED RESTRICTIONS for offline manifest geometry only.** This is not execution-ready: the existing production collector/workflow does not yet dispatch this partial-window proposal or enforce its `max_attempts=1` field. The developer must implement and test the one-attempt behavior and an exact-manifest authorization path before requesting any live permission.
- The previous one-use approval remains spent. No new request, option refetch, model fit, holdout access or strategy test is authorized. The encrypted data-value limitation and six failed historical windows remain unresolved.

**Tester → Developer:** Implement the manifest-specific no-retry behavior and fail-closed exact-SHA request gate; submit those code changes for a new review without making source calls.

**Developer → Tester:** Review the executable code path, retry counter, exact proposal SHA binding, and request budget before any live workflow can become eligible.


## Third review — exact-SHA validator and preservation guard

- Exact developer snapshot reviewed: `d2176806aa6c5db08e0577ddc3daf08a9652f1a6`.
- The split proposal now explicitly binds its base to partial artifact `11693866249` and requires preserving 8,490,723 option rows plus the 403,664 previously recovered spot rows; successful windows must not be refetched. Its 34 shards remain contiguous, disjoint, no longer than seven calendar days, capped at 4,000 rows / 8 MiB, and specify one attempt each.
- The collector now honors a per-request `max_attempts` field; tests verify `max_attempts=1` makes one attempt and `max_attempts=2` permits one retry. The offline validator `scripts/validate_nifty_1m_spot_gapfill_split_proposal.py` checks the exact proposal shape and denies authorization unless the tester decision pins both exact SHAs, scope, and request/retry budgets. Tests cover stale SHA and missing-authorization denial. Pipeline run [38118437757](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38118437757) passed, and exact-snapshot offline tester run [38118437808](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38118437808) passed the code gate.
- **Decision: PASS WITH SCOPED RESTRICTIONS for offline proposal and authorization-validator code only.** No live request is authorized. Two execution blockers remain: (1) the validator is not yet integrated into a request-bearing workflow that spends a new one-use marker bound to the proposal blob; (2) the production collector still expects the original zero-spot artifact and is not yet able to use partial artifact `11693866249` as its base while preserving existing spot rows. Executing the 34-shard proposal with the old base would discard the 403,664 recovered spot rows, so it must not be run as-is.
- The earlier data-completeness REQUEST_CHANGES remains in force until the six failed intervals are successfully recovered and the combined artifact is re-audited. No new source requests, model fitting/scoring, holdout access, or strategy tests are authorized.

**Tester → Developer:** Implement partial-artifact ingestion/preservation and integrate the exact-SHA authorization validator into a separate fail-closed workflow. Keep it offline-only until the resulting exact snapshot receives a fresh explicit tester authorization.

**Developer → Tester:** Review the new base-artifact preflight, option/spot row preservation, de-duplication and one-use marker path before any live request can be enabled.


## Fourth review — partial-artifact runner and request-workflow gate

- Exact developer snapshot reviewed: `be7d5cb9c3825d2b389c8796dfe7085e68973772`.
- Offline pipeline tests passed, including partial-artifact row preservation, per-request attempt ceilings, exact-SHA validator behavior and split-workflow YAML validation. The code gate [38119094646](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38119094646) returned `PASS_WITH_SCOPED_RESTRICTIONS`; the AI reviewer remained unavailable (HTTP 402).
- The exact-SHA split workflow is now installed on main, developer and tester branches. It verifies the proposal blob SHA and the base artifact ZIP digest, requires a separate spent-before-request marker, uses a distinct split ledger/result, and only exposes a request job if the tester decision explicitly sets `decision_scope=SPLIT_RECOVERY_EXECUTION`, `split_recovery_authorized=true`, `live_requests_authorized=true`, request limit 34, retry limit 0, and no option requests.
- Gate runs [38118998725](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38118998725) and [38118990427](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38118990427) denied the proposal without making requests. The first denial exposed a schema-field mismatch; the validator now accepts the exact proposal SHA under either recognized field name while still requiring equality. After the schema correction, the denial reason was only the missing execution scope/authorization flags, as intended.
- **Decision remains PASS WITH SCOPED RESTRICTIONS for offline code only.** The request job must remain skipped because AI review is unavailable and live authorization is false. The 34-shard retry has not run; the dataset remains partial. No option refetch, model fitting/scoring, holdout access or strategy testing is authorized.

**Tester → Developer:** Keep the request job disabled unless an exact-snapshot tester decision explicitly authorizes the split execution scope; AI reviewer unavailability is not approval.

**Developer → Tester:** Re-review only after the authorization decision or code changes; do not infer permission from an offline code-gate pass.
