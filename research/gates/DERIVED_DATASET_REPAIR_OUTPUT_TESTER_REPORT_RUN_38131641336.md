# Tester Report — Derived Dataset Repair Output (Run 38131641336)

- Review date: 2026-10-11 UTC
- Decision applies only to the derived-dataset repair output and its hosted post-repair audit.
- Developer submission: [DERIVED_DATASET_REPAIR_OUTPUT_DEVELOPER_SUBMISSION_RUN_38131641336.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/DERIVED_DATASET_REPAIR_OUTPUT_DEVELOPER_SUBMISSION_RUN_38131641336.md)
- Submission commit: `431682f26b1714f092a7c209b4ef435c22eaec5f`
- Hosted run: [38131641336](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336) — **success**, all steps passed.
- Exact run source commit on main: `5e769cd4b19887311213baf16eb81b97416322d7`
- Source artifact: run `38126168547`, artifact `11696937921`, SHA-256 `5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b`.
- Derived artifact: `11698879857`, `nifty-1m-derived-repaired-r2-38126168547`, 231,076,122 bytes, not expired at review.
- Sanitized report blob SHA: `6f40739ab7a25b1a57f39d153f016a9da6698f1a`.
- Sanitized manifest blob SHA: `66683afe7c498a6b52d7863a0da0c4f7a47734c8`.
- Implementation blob SHA: `5fe7b5fb35e7cae1c1a39258ce7e3c78adf8fb8b`.
- Post-repair validator blob SHA: `e2feada6125666b1277af288e9ad1ca5fa444b50`.
- Reviewer limitation: this is a same-connected-assistant tester-role review, not a separate human or external AI review. The connector exposes the workflow's logs, sanitized report/manifest and artifact metadata but did not allow a second direct download/re-hash of the output artifact's binary bytes. The hosted workflow did verify all encrypted part hashes/sizes before upload, then uploaded the artifact and passed cleanup/publication checks.

## Reconciliation checks

| Invariant | Verified result |
|---|---:|
| Option rows | 8,490,723 |
| Standalone spot rows | 509,142 |
| Total rows / manifest total | 8,999,865 / 8,999,865 |
| Rows deleted | 0 |
| Monthly encrypted parts | 61 |
| Part manifest row counts summed | 8,999,865 |
| Exact-epoch matched option rows | 8,471,702 |
| Unmatched option rows | 19,021 |
| Exact-join field mismatches | 0 |
| Matched rows missing source spot epoch | 0 |
| Unmatched epochs already present in spot set | 0 |
| Unmatched rows containing underlying OHLCV | 0 |

The report's source run, artifact ID and source ZIP SHA-256 agree with the pinned source artifact. The derived manifest is encrypted-only, contains 61 parts, sums to the full row count, and carries the matching parent artifact ID and SHA-256. The GitHub Actions output artifact for the exact hosted run exists under the expected name and ID.

## Semantic / schema checks

The embedded post-repair audit status is `PASS_WITH_COVERAGE_RESTRICTIONS`. The following reported counts are all zero:

- Nonblank invalid OHLC rows, partial OHLC rows, negative nonblank volumes and nonfinite nonblank volumes.
- Duplicate composite OPTION keys and duplicate SPOT epochs.
- Invalid timestamps and invalid ISO session dates.
- Unknown row types and unknown join statuses.
- Monthly row-count mismatches and manifest reconciliation findings.
- Exact-join source-epoch or field mismatches.

The hosted job log confirms the independent post-repair audit was executed inside the repair routine, encrypted output and sanitized metadata were uploaded, the plaintext cleanup step printed `PASS: all plaintext gzip files removed.`, and the sanitized report/manifest exact-parent and total-row checks passed. Every hosted job step is marked successful.

## Repair counts and residual restrictions

- 1,528 joined NIFTY fields reconciled from exact-epoch SPOT rows.
- 382 joined OPTION rows had underlying OHLC masked because the exact-epoch SPOT OHLC was invalid.
- 12 standalone SPOT rows had invalid OHLC masked; 309 standalone SPOT volume values were masked.
- 11 option-volume values were masked.
- 19,021 unmatched option rows remain unmatched/blank; none was filled by nearest time, interpolation or timestamp shifting.
- 24,847 rows were flagged `REPAIR_WEEKEND_SESSION_REVIEW_REQUIRED`. They were not silently deleted or relabelled.

The earlier report without the post-repair validation block is superseded for final review by this run's report. The current report contains the required `post_repair_validation` summary; the earlier report is not used as proof for this decision.

## Decision

**PASS WITH SCOPED RESTRICTIONS — output integrity and post-repair validation summary.**

This decision closes only the derived-repair output gate. It does not declare all source coverage complete and does not approve model fitting, holdout access, prediction claims, or strategy/P&L testing. The retained 19,021 unmatched rows and 24,847 weekend-session review flags require an explicit missingness/session-label treatment in a subsequent modeling-readiness gate. The source also has previously recorded empty Greek/time-to-expiry fields; feature availability must be checked at that gate.

No new source/API calls, model fitting/scoring, holdout access, or strategy/P&L tests occurred in this gate.

**Tester → Developer:** Update main README, research status, error log index and developer action log with this exact-run decision. Prepare a separate exact-snapshot modeling-readiness proposal addressing unmatched-row eligibility, weekend-session flags, missing Greek/time-to-expiry fields, chronological splits and leakage checks. Do not begin fitting models from this repair decision alone.

**Developer → Tester:** Review the exact-SHA modeling-readiness proposal and its deterministic preflight before any fitting or holdout access. Reject any attempt to infer readiness solely from a successful repair workflow.
