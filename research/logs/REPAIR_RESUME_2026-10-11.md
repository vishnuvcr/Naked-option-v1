# Resume Log — Derived Data Repair (2026-10-11)

## Current operation

- User instructed: “Resume”.
- Data collection remains closed. No source/API requests were made in this continuation.
- Source artifact is fixed to patch run `38126168547`, artifact `11696937921`, SHA-256 `5337b545a0b95b943fc3de4f39b00c5d857a656fc663a9387a564aaf288af80b`.
- Promoted the nested-manifest preflight repair workflow to `main` at commit `6ba67c270bc2e95480cecc2cdb45d751bca48685`, and the expanded regression tests at commit `9d0ae29fa4f8a4b4f8fe814d07702eb03d987017`.
- Repair workflow run [38130635408](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38130635408) successfully completed exact-artifact preflight, pinned dependency installation, repair regression tests, encrypted artifact download, per-part integrity checks, and authenticated decryption. The row-level repair step was still running at the time of this log; no derived output counts or final verdict are claimed yet.
- A second workflow run [38130642693](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38130642693) was queued behind the same concurrency group after the test expansion. It is also tied to the same immutable source artifact.
- The repair policy is: exact-epoch reconciliation only; mask invalid OHLC/volume as missing; keep unmatched option rows blank/unmatched; never change or delete source rows; publish only encrypted derived parts and sanitized aggregate metadata.
- Current baseline findings from the latest provenance report: 19,021 unmatched option rows across 421 distinct timestamps; 382 joined-NIFTY OHLC violation occurrences across 7 epochs; 12 standalone spot OHLC violation occurrences across 12 epochs; 309 negative spot-volume occurrences; 11 negative option-volume occurrences across 10 epochs.
- Model fitting/scoring, holdout access and strategy/P&L tests remain unauthorized. No prediction conclusion is produced by data repair.

## Next checkpoints

1. Wait for the repair workflow to complete.
2. Verify the sanitized report, derived manifest, encrypted output artifact, and plaintext cleanup.
3. Have the tester review the exact output/run and issue a scoped verdict.
4. If successful, run a separate post-repair semantic validation of the derived artifact; only then consider a distinct modeling-readiness gate.

**Developer → Tester:** Review the actual repair report, manifest lineage, row preservation, repair counts, encrypted output hashes and cleanup logs when available.

**Tester → Developer:** Do not accept repair-code tests alone as proof that the production-derived dataset is ready for prediction.


## Follow-up checkpoint — 2026-10-11
- On resume, confirmed exact source artifact 11696937921 and pinned SHA-256 remain unchanged.
- Active latest workflow: [38131641336](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336). Its source checks, regression tests, dependency installation, encrypted-part verification and decryption completed successfully; the row-level repair step remained in progress.
- An earlier successful run [38130635408](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38130635408) uploaded artifact 11698138685. Its committed report lacks the current `post_repair_validation` field, so it is not considered final evidence.
- Await exact latest run's sanitized report, derived manifest and artifact metadata; require 61 hash-verified encrypted parts, 8,999,865 preserved rows, independent post-repair validation and successful plaintext cleanup before tester review.
- No model, holdout, strategy/P&L, or additional source requests are authorized by the existing scoped decision.

**Developer → Tester:** Once the active run publishes its output, independently reconcile the output report/manifest/artifact ID and hashes, row counts, join/quality audit, and cleanup evidence. Reject stale output or any mismatch.

**Tester → Developer:** Keep model/holdout/strategy gates closed until an exact-output reviewer decision is recorded.


## Completion checkpoint — derived dataset repair (2026-10-11)
- Exact repair run [38131641336](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336) succeeded end-to-end.
- Output artifact [11698879857](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38131641336/artifacts/11698879857) contains the encrypted derived dataset and sanitized metadata. All 61 part hashes and row counts passed runner-side verification; post-repair audit passed with coverage restrictions; plaintext cleanup and report publication passed.
- Preserved 8,999,865 rows; 8,471,702 exact matches, 19,021 unmatched option rows, 0 exact-join field mismatches, 0 residual nonblank invalid OHLC/volume, 0 duplicate keys/spot epochs, and 24,847 weekend-session flags retained for review.
- Tester role recorded `PASS_WITH_SCOPED_RESTRICTIONS` for this output gate only. Exact report/decision are on `phase-07-tester`.
- No prediction models, holdout access or strategies were run. Modeling readiness remains a separate gated phase.
