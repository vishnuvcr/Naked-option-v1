# Error Log

## 2026-10-07 — Phase 6 Run 37668947725
- Category: implementation/runtime
- Component: scripts/run_phase6_novel.py intraday cutoff construction
- Symptom: AttributeError: 'DatetimeIndex' object has no attribute 'iloc'
- Location: line 616 at commit 85c1b8db633dc1fb79f3426ab0b065e068efc2aa
- Impact: empirical suite terminated before artifact creation; no metrics accepted.
- Root cause: invalid positional indexing API for pandas DatetimeIndex.
- Correction: use DatetimeIndex[...] and add explicit regression coverage.
- Prevention: tester approval required before fresh empirical execution.

## 2026-10-08 — Phase 6 fresh run 575 residual cutoff defect
- Category: implementation/runtime
- Component: scripts/run_phase6_novel.py later global-I03 cutoff path
- Symptom: residual use of `decision_times.iloc[rows[0]]` on a pandas DatetimeIndex remained after the earlier cutoff correction.
- Location: commit 9b9b7914f82993505ec4f2f0c3aac0b3d6732521, current file line 721.
- Impact: fresh hosted run 575 (37678088131) is classified as non-evidence because the same AttributeError would occur when the global-I03 path is reached; no metric may be accepted.
- Root cause: incomplete search/coverage of all DatetimeIndex positional accesses during the prior correction.
- Proposed correction: replace the residual access with DatetimeIndex[...] and add regression coverage plus a source-level assertion forbidding `decision_times.iloc`.
- Prevention: tester approval is required before the developer branch is advanced for a fresh empirical run.

## 2026-10-08 — GitHub live-log visibility error during Phase 6 run 575
- Category: infrastructure/tooling
- Component: GitHub Actions live-job log retrieval
- Symptom: fetching logs for in-progress empirical job 112986961991 returned HTTP 404 BlobNotFound.
- Impact: no scientific impact; live job-step status remained available through the workflow-jobs endpoint.
- Disposition: infrastructure-only visibility issue; no metric or result was inferred from missing logs.

## 2026-10-08 — Developer tooling edit attempt
- Category: developer/tooling
- Symptom: first detached-commit construction attempt failed due to a JavaScript template-literal escaping error while assembling the multi-file tree.
- Impact: no repository change; the intended correction was not written by that failed call.
- Disposition: corrected in the subsequent repository operation; no scientific impact.

## 2026-10-08 — Developer detached correction indentation defect
- Category: developer/code assembly
- Component: proposed detached Phase 6 correction commit `1aa8be846348f9e8341d572cd3289cd12ee89045`
- Symptom: the corrected `cutoff = decision_times[...]` line was initially emitted at the wrong indentation level because the replacement omitted the source line's existing leading whitespace.
- Impact: the proposed detached commit was rejected before tester submission; developer branch was not advanced and no workflow was triggered by this flawed object.
- Correction: rebuilt the detached commit with the cutoff line correctly nested inside the `if intraday:` block.
- Prevention: inspect the exact changed source lines in the detached commit before tester review.

## 2026-10-08 — Phase 6 run 578 regression arithmetic defect
- Category: tester/regression-fixture arithmetic
- Component: scripts/test_phase6_novel.py global-I03 cutoff regression
- Symptom: regression expected `decision_times[4] - 120 minutes` to equal 11:00, but the fixture starts at 09:15 with hourly spacing, so decision_times[4] is 13:15 and the correct result is 11:15.
- Hosted run: Research Protocol Check #578 (`37680279189`), job `112994273676`.
- Impact: mandatory regression failed; empirical job was skipped; no Phase 6 artifact or metric was generated/accepted.
- Root cause: arithmetic error in the newly added regression expectation, not in the production cutoff implementation.
- Correction: update the expected timestamp to 11:15 and preserve the production change unchanged.
- Prevention: independently recompute fixture timestamps for every explicit time-delta assertion before the next hosted run.

## 2026-10-08 — Phase 6 Run #581
- No execution error occurred. Protocol, regression, empirical suite, schema validation and artifact upload all passed.
- The independent tester nevertheless recorded a scientific caution: raw maxima across 140 executed cells are not treated as discoveries because multiple-comparison and downstream trading gates remain outstanding.


## 2026-10-09 — Phase 7 Run #925 independent empirical tester REQUEST CHANGES

- Category: protocol/metrics/inference implementation
- Component: `scripts/run_phase7_ensemble.py` and independent artifact audit
- Hosted empirical run: [Run #925](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37914905848), immutable source commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1`.
- Tester audit workflow: [Run #943](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935031119).
- Symptom: the corrected independent audit recorded 2,775 passed checks and 323 failed checks across the 10 panels. The principal repeated failures were caused by four implementation mismatches, not 323 separate root causes.
- Root causes: P10's frozen abstention range [0.45, 0.55] was omitted from the production abstention registry; NaN volatility/trend inputs were implicitly classified as low/low regime state; P05/P06 chronological diagnostics ignored the same abstention masks used by headline metrics; family-bootstrap abstentions were written as zero even when label/probability/baseline rows were not eligible.
- Impact: P10 summary metrics, regime metrics and family-level inference are not protocol-reconciled. Run #925 is **NON-ACCEPTED EVIDENCE**; no P08/P09/P10 or other Phase 7 metric is promoted, and Phase 8 remains blocked.
- Tester disposition: `research/gates/PHASE7_RUN925_EMPIRICAL_TESTER.md` = **REQUEST CHANGES**.
- Correction: pending developer implementation and focused regression coverage. Do not alter the frozen Phase 7 specification, candidate universe, horizons, random seed, block lengths, 500 bootstrap replications or thresholds.
- Prevention: add negative regression cases for each abstention boundary, non-finite regime inputs, candidate-specific block masking, and missing-versus-zero benchmark differentials; require a fresh immutable artifact plus independent source/hash/metric/family audit before progression.


## 2026-10-09 — Phase 7 correction review: stale approval could authorize changed code

- Category: workflow authorization / independent gate integrity
- Component: `.github/workflows/research-protocol.yml`, `.github/workflows/phase-07-ensemble.yml`.
- Tester report: `research/gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md` = **REQUEST CHANGES**.
- Finding: correction-specific authorization checked only for file existence and expected text. It did not bind the tester PASS to the exact source/test/validator/spec/workflow snapshot. A later change to protected code could retain the old PASS and still trigger empirical execution.
- Impact: authorization is not yet robust against stale approvals; Phase 8 stays blocked, and no empirical execution may be accepted until commit/hash binding is independently approved.
- Required correction: include an exact reviewed developer commit plus protected-file hashes (preferred) or reject any protected-path changes since the approved snapshot. Add positive/negative tests for both the automatic caller and manual reusable workflow.
- Non-evidence: unreviewed-run attempts `37935752265` and `37935794939` remain non-evidence regardless of completion or artifacts.


## 2026-10-10 — Phase 7 available-data acquisition-cache gate

- **Evidence:** hosted Phase 7 available-data workflow Run #37 (37990522933) completed successfully at developer commit 18773e828f19c0ff2e9fc1af437db6b8ef181739. Both regression suites passed (11 predictor checks and 11 result-schema/panel checks); the empirical job was skipped by the fail-closed authorization gate.
- **Finding:** independent review discovered that `scripts/acquire_nifty_daily_history.py` downloads Yahoo history and performs official-source spot checks unconditionally before writing the cached file. The workflow restores a cache, but the acquisition script does not reuse a valid cached CSV/manifest. Importing the script also performs network I/O, leaving this behavior without targeted regression coverage.
- **Impact:** no prediction output was generated; this is a reproducibility/cache-governance defect. The Phase 7 available-data extension remains blocked for empirical execution.
- **Tester report:** `research/gates/PHASE7_AVAILABLE_GLOBAL_ACQUISITION_GATE_TESTER.md` = **REQUEST CHANGES — empirical execution not authorized**.
- **Required correction:** make acquisition import-safe; validate cache schema, coverage, freshness, source and SHA-256; reuse a valid cache; reacquire only when missing/stale/invalid; add no-network test fixtures; and protect the new tests in the workflow/approval path.
- **Prevention:** hosted regression green status is necessary but not sufficient; data acquisition and cache semantics must have their own regression fixtures and be reviewed before empirical execution.


## 2026-10-10 — NIFTY acquisition timezone/cutoff/cache integrity follow-up

- **Hosted evidence:** [Phase 7 available-data Run #40](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992378927) completed with 4 new acquisition/cache checks, 11 prediction regression checks and 11 result-validator checks passing. The empirical job was skipped by the missing-approval guard; this was not a prediction run.
- **Finding:** independent tester review of `scripts/acquire_nifty_daily_history.py` blob `734c5ac1b5e4f193c5cc68ded8f717f83dff4a3d` found (1) timestamps converted to UTC calendar dates rather than Yahoo exchange-local dates, (2) a chart period-2 boundary formed at midnight UTC despite an IST end-of-day policy, (3) cache validation accepting same-day rows before the bar-complete cutoff, and (4) cached manifest overlap checks not reconciled to the CSV's same-date close values and difference arithmetic.
- **Impact:** a green synthetic test suite is insufficient to establish point-in-time-safe session dates. No empirical prediction was run; Phase 7 remains blocked.
- **Tester report:** `research/gates/PHASE7_AVAILABLE_GLOBAL_ACQUISITION_GATE_TESTER.md` — REQUEST CHANGES.
- **Required correction:** exchange-local timestamp conversion; Asia/Kolkata chart boundaries; same allowed-date rule for cache and network path; overlap CSV/manifest cross-field reconciliation; tests for date conversion, pre/post-close behavior and malformed overlap records.


## 2026-10-10 — Tester PASS; execution manifest not created

- The exact-snapshot tester report now has **PASS WITH SCOPED RESTRICTIONS**, authorizing one Phase 7 prediction batch at reviewed developer commit `f04b96bc47477981bfdc63271f1e80402f9428e8`.
- Hosted Run #43 passed 8 acquisition/cache, 11 predictor and 11 result-validator tests; the empirical job was skipped because approval was not yet mirrored.
- The developer attempted to create the hash-bound approval JSON after mirroring the tester report, but the write was blocked by platform safety checks. The file remains absent. No alternative trigger has been used and no prediction outputs exist.
- Current disposition: tester code gate passed for one exact snapshot, but operational execution remains blocked until the protected authorization step can be completed through a permitted route.


## 2026-10-10 — Independent audit of Run #44

- No arithmetic, target-sign, duplicate-key, probability-range, missing-output, metric-reconciliation or bootstrap-p-value mismatch was found in the immutable result artifact.
- The only cache note is that all 11 global-source records reported `cache_hit: false`; the old cache did not satisfy the current cache contract and the sources were reacquired. The job completed and the updated data were retained in the artifact/cache.
- No statistically significant candidate was found; all adjusted horizon-family p-values were 1.0. This is a negative result, not an infrastructure failure.
- Report: `research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md`.


## 2026-10-10 — Extension 2 specification gate REQUEST CHANGES

- Tester rejected the initial proposal before source feasibility.
- Corrections required: define legacy-to-UDiFF F&O schema transition; replace undefined "NIFTY traded value" denominator for FII/DII flows with a fixed available denominator; define F04 delta/acceleration and F05 aggregate volume/OI formula exactly; provide canonical NSE sector index names/symbols; and specify how candidate abstentions enter the common-grid max-statistic bootstrap with a synthetic fixture.
- No data acquisition or model fitting occurred. This is a pre-implementation specification rejection, not an empirical model result.
- Report: `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SPEC_TESTER.md`.
