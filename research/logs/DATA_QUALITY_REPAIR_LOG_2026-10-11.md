# Data Quality Repair Log — 2026-10-11

## Scope and immutable source policy

The current source artifact is patch run [38126168547](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38126168547), artifact [11696937921](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38126168547/artifacts/11696937921), SHA-256 `5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b`. It contains 8,490,723 option rows, 509,142 spot rows, 8,471,702 exact matches and 19,021 unmatched option rows. The source artifact is immutable; all repairs must be separate, derived outputs with a complete row-level audit trail.

## Confirmed defects / current diagnostic scope

The latest value audit reports 714 semantic-error occurrences:
- 382 joined NIFTY OHLC violations on option rows;
- 12 standalone SPOT OHLC violations;
- 309 negative joined NIFTY-volume occurrences;
- 11 negative option-volume occurrences;
- 0 duplicate composite keys and 0 duplicate spot timestamps.

These are occurrence counts, not necessarily unique underlying bars. Joined values are repeated across option contracts, so the next report counts distinct epochs and source-request lineage before any correction.

## Implementation mistakes caught

1. **Unmatched timestamp JSON output:** the script wrote a literal backslash-n after its JSON payload. The hosted parser raised `JSONDecodeError: Extra data` at the end of the file. Fixed the output newline in `scripts/diagnose_nifty_1m_unmatched_spot_targets.py`. The fixed workflow must be rerun and its publication step verified.
2. **Dataset value-audit cleanup shell block:** an indented heredoc terminator was not recognized by Bash, causing `syntax error: unexpected end of file`. The developer workflow version now uses a simple `printf` fallback and explicitly checks plaintext files and the temporary SQLite file are absent. Hosted cleanup confirmation remains pending for that workflow version.
3. **Report publication gate:** the unmatched diagnostic workflow previously allowed README/status publication when the value diagnostic had not succeeded. The gate now requires the unmatched map, value anomaly report, and cleanup to succeed before publication.
4. **Correction policy:** no source rows were modified. Negative volume must not be clamped to zero, OHLC fields must not be swapped/extended, and unmatched option rows must not be joined by nearest timestamp unless a separate scientifically justified target/feature policy is tested and approved.

## Next steps

1. Complete the fixed-artifact value-anomaly provenance run; publish only aggregate counts, dates, source-request hashes and row fingerprints, never prices or volumes.
2. Distinguish repeated joined-bar anomalies from distinct spot-bar anomalies and compare each joined row with its standalone spot row at the same exact epoch.
3. Create a separate derived-dataset repair script with regression tests:
   - use the standalone SPOT row as the replacement only if the same-epoch source row is present, valid and exactly matches the join key;
   - mark irreparable OHLC values missing and exclude them from OHLC-dependent samples rather than inventing prices;
   - mark negative volume as missing unless an authoritative existing source record proves the correct value;
   - keep the 19,021 unmatched option rows explicitly unmatched until an exact-epoch source observation is available.
4. Tester must review exact code/artifact, before/after counts and repair rules before any derived dataset is used for prediction.

No new data requests, model fitting/scoring, holdout access, or strategy/P&L testing occurred in this work.

**Developer → Tester:** Review the sanitized provenance report and the proposed repair policy before approving a derived dataset.

**Tester → Developer:** Reject silent source edits, approximate joins, and arbitrary volume/OHLC fixes; require exact-snapshot evidence and before/after reconciliation.


## 2026-10-11 — Derived dataset repair output review completed

- Hosted repair workflow [38131641336](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336) completed successfully; all steps passed, including source integrity checks, regression tests, 61-part derived output verification, the integrated post-repair audit, encrypted artifact upload, plaintext cleanup and sanitized-report publication.
- Source remains pinned to run 38126168547 / artifact 11696937921, ZIP SHA-256 `5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b`.
- Derived encrypted artifact: [11698879857](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336/artifacts/11698879857), size 231,076,122 bytes. Report: [DERIVED_DATASET_REPAIR_REPORT_R2_RUN_38126168547.json](https://github.com/vishnuvcr/Naked-option-v1/blob/main/research/data/DERIVED_DATASET_REPAIR_REPORT_R2_RUN_38126168547.json). Manifest: [DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json](https://github.com/vishnuvcr/Naked-option-v1/blob/main/research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json).
- Validation: `DERIVED_REPAIR_COMPLETE`; post-repair audit `PASS_WITH_COVERAGE_RESTRICTIONS`. Preserved 8,999,865 rows (8,490,723 option + 509,142 spot), zero rows deleted, 61 encrypted parts, 8,471,702 exact matches and 19,021 unmatched option rows. Exact join mismatches, nonblank invalid OHLC/volume, duplicate keys/timestamps, invalid timestamps/session dates, unknown row/join types, and manifest/monthly count mismatches are all zero.
- Corrections/masking: 1,528 joined NIFTY fields reconciled from exact-epoch spot rows; 382 joined option rows masked for invalid source-spot OHLC; 12 standalone spot OHLC rows, 309 spot-volume values and 11 option-volume values masked. The original source is unchanged.
- Remaining restrictions: 19,021 unmatched option rows remain blank/unmatched across 421 timestamps; 24,847 rows carry weekend-session review flags. No approximate joins or invented values were used. These must be considered in a distinct modelling-readiness review.
- Tester decision: **PASS WITH SCOPED RESTRICTIONS — repair output and post-repair audit only**. See [tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/DERIVED_DATASET_REPAIR_OUTPUT_TESTER_REPORT_RUN_38131641336.md) and [machine-readable decision](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/DERIVED_DATASET_REPAIR_OUTPUT_TESTER_DECISION_RUN_38131641336.json). The tester-role report is from this connected session, not an external independent reviewer, and notes that a second direct download/re-hash of the artifact binary was unavailable through the connector.
- No market-data request, prediction fitting/scoring, holdout access or strategy/P&L test occurred. This is not a model-readiness or strategy approval.
- Next gate: an exact-snapshot modelling-readiness proposal must define eligibility for unmatched rows, investigate weekend-session flags and empty Greek/time-to-expiry fields, and pass tester review before any fitting or holdout access.

**Developer → Tester:** Review the exact-snapshot modelling-readiness proposal and preflight before authorizing any prediction-model run.

**Tester → Developer:** Keep model/holdout/strategy gates closed unless the modelling-readiness gate independently passes.
