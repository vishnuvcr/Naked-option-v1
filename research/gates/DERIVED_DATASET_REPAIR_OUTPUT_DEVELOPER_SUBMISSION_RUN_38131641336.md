# Developer Submission — Derived Dataset Repair Output

- Submission date: 2026-10-11 UTC
- Review requested: exact-output integrity, embedded post-repair audit, schema/count reconciliation, coverage restrictions, cleanup and publication
- Hosted run: [38131641336](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336)
- Run source commit (main): `5e769cd4b19887311213baf16eb81b97416322d7`
- Developer implementation blob: `scripts/repair_nifty_1m_composite_values.py` = `5fe7b5fb35e7cae1c1a39258ce7e3c78adf8fb8b`
- Independent validator blob: `scripts/validate_repaired_nifty_1m_composite.py` = `e2feada6125666b1277af288e9ad1ca5fa444b50`
- Repair workflow blob: `.github/workflows/phase-07-derived-dataset-repair.yml` = `500ca1ed277d2b2f0a4d5a18582b6d740384af62`
- Offline repair tests blob: `scripts/test_repair_nifty_1m_composite_values.py` = `79a1625f768790395e5f121423e340627c83ee98`

## Immutable source and derived output

- Source run/artifact: [run 38126168547](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38126168547) / artifact [11696937921](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38126168547/artifacts/11696937921)
- Source ZIP SHA-256: `5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b`
- Derived artifact: [11698879857](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336/artifacts/11698879857), name `nifty-1m-derived-repaired-r2-38126168547`, size 231,076,122 bytes, not expired at review.
- Sanitized repair report: [DERIVED_DATASET_REPAIR_REPORT_R2_RUN_38126168547.json](https://github.com/vishnuvcr/Naked-option-v1/blob/main/research/data/DERIVED_DATASET_REPAIR_REPORT_R2_RUN_38126168547.json), blob SHA `6f40739ab7a25b1a57f39d153f016a9da6698f1a`.
- Sanitized derived manifest: [DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json](https://github.com/vishnuvcr/Naked-option-v1/blob/main/research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json), blob SHA `66683afe7c498a6b52d7863a0da0c4f7a47734c8`.

## Result summary

- Workflow conclusion: `success`; all 18 steps succeeded.
- The workflow reported exact-source verification, pre-access regression tests, decryption, all-part output hash/size checks, upload, plaintext cleanup, report/manifest validation and commit as successful.
- Report status: `DERIVED_REPAIR_COMPLETE`.
- Embedded independent post-repair audit: `PASS_WITH_COVERAGE_RESTRICTIONS`.
- Preserved rows: 8,999,865 (8,490,723 OPTION; 509,142 SPOT); rows deleted: 0.
- Join totals: 8,471,702 matched; 19,021 unmatched. Exact-join mismatches=0; matched rows missing a source epoch=0; unmatched epochs already present in SPOT set=0; unmatched rows with underlying OHLCV populated=0.
- Quality checks: nonblank invalid OHLC=0; partial OHLC=0; negative/nonfinite nonblank volume=0; duplicate option keys=0; duplicate SPOT epochs=0; invalid timestamps/session dates=0; unknown row types/join statuses=0; monthly row-count mismatches=0; manifest reconciliation findings empty.
- Repair counts: 1,528 joined NIFTY fields reconciled; 382 joined rows masked because the exact source SPOT OHLC was invalid; 12 standalone SPOT rows had invalid OHLC masked; 309 standalone SPOT volume values masked; 11 option-volume values masked; 19,021 unmatched OPTION rows preserved without approximate fill; 24,847 weekend-session rows flagged for review.
- No new source requests, model fitting/scoring, holdout access, or strategy/P&L testing occurred.

## Acceptance restrictions

This is a quality-controlled **candidate dataset with coverage restrictions**, not a complete dataset. The 19,021 unmatched option rows remain blank/unmatched. The 24,847 weekend-session flags remain for a later data/session-label review. No row is dropped and no nearest-time join, timestamp shift, interpolation, zero-fill or invented price is used.

The run's output is protected by runner-side per-part hash/size verification and a separate post-repair audit. The connected tester tool can inspect the sanitized report, manifest, Action logs and uploaded artifact metadata, but cannot itself download the binary artifact bytes for an independent second-pass rehash; record that as a review limitation rather than implying a second download happened.

**Developer → Tester:** Review the exact output run, output artifact metadata, report/manifest blob hashes, row and join reconciliation, zero remaining nonblank value anomalies, coverage flags and successful cleanup. Return REQUEST_CHANGES for any contradiction. Do not authorize modelling from the repair decision alone.

**Tester → Developer:** Publish an exact-run verdict on `phase-07-tester`. A pass can close only the repair-output gate; keep model fitting, holdout and strategy/P&L gates closed pending a separate modeling-readiness decision.
