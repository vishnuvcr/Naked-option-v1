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


## 2026-10-10 — Gate A sampler REQUEST CHANGES

- Independent review found both legacy and UDiFF sample validators checked the expected trade date only on the first row. A mixed-date archive could be accepted.
- Correction: validate all non-empty rows, report distinct date count, and add one mixed-date fixture per format.
- No live data acquisition, full-history download or model fit occurred.
- Tester report: `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_TESTER.md`.


## 2026-10-10 — Gate A sampler v2 REQUEST CHANGES

- Independent review found `NSE_FII_URLS` included `fromDate=01-01-2020&toDate=31-12-2025`, a multi-year history request disallowed in Gate A. Correct the date bounds and impose an API-specific response byte cap and row cap with regressions.
- Review request mislabeled workflow commit `1d899125...` as its Git blob. Actual workflow blob at the reviewed commit is `20470b88d29b1d97e8060936e5ed7a40fe28a80d`.
- No live data requests were made in the tester review. No approval manifest was created.


## 2026-10-10 — Legacy Gate A live-fetch workflow incident and containment

- Run `38025793938` executed the legacy one-day sampler without the required exact-snapshot tester approval because the old workflow had an automatic source-fetch trigger. It fetched only two single-day F&O archives and a small set of pages/API probes; no full history, feature/label dataset or model fitting occurred.
- Because tester authorization was missing, its artifact ID `11659904438` is **NON-ACCEPTED EVIDENCE** and cannot pass Gate A.
- The legacy workflow was replaced with offline-only tests (blob `f23bb9fe8a5b1343a2a94d308c77b4e26de1d0f3`). Safety-correction Run `38026080844` passed the v1 regression suite and contains no source-fetch step.
- Current protected sampler/workflow snapshot then received an exact-snapshot PASS with 22 hosted offline tests passing. Approval is limited to one bounded Gate A run only. Full-history acquisition and model fitting remain prohibited.


## 2026-10-10 — Gate A artifact REQUEST CHANGES / authorization revoked

- Artifact ID `11660395594` (Run `38026272245`) is not accepted as a passed Gate A report.
- Bug 1: both official index CSVs contained dates like `05-07-2024`; the current parser returned `date_check_all_rows=false` because numeric `DD-MM-YYYY` was unsupported.
- Bug 2: NSE FII/DII date endpoint requested 2024-07-01 through 2024-07-10 but returned two rows dated 2026-10-09; response SHA-256 was identical to the unfiltered endpoint. Date-window matching was not checked after retrieval.
- Historical FII/DII coverage remains unproven: current-only official API and a limited recent GitHub mirror/page are insufficient to establish 500+ sessions. Continue free-source discovery before declaring unavailable.
- Current source approval is revoked. No full history/features/labels/model fits occurred. The developer must correct date parsing and response-window validation and seek a fresh exact-snapshot gate.


## 2026-10-10 — Gate A Run 2 audit decision: flow-source coverage insufficient

- Independent tester accepted corrected parser/schema results for official sector index CSVs, cash-equity archive samples and legacy/UDiFF F&O samples.
- Historical-flow sources remain insufficient: 164 valid dated rows from a free mirror (2026-01-14 through 2026-09-30), the official dated API ignored the July 2024 range but is now safely rejected, and HTML snippets from secondary pages do not establish full daily range coverage.
- The complete Gate A decision is REQUEST CHANGES. The one-run manifest is marked SPENT after Run `38026993369`; no more requests may be made on it.
- Separate bounded free-source discovery is required before full history, features/labels or model fitting.
- Details: `research/gates/PHASE7_EXTENSION2_GATE_A_RUN2_ARTIFACT_TESTER.md`.


## 2026-10-10 — Source Discovery 3 spec review web-reader limitation (non-evidence)

During specification validation, the web reader was directed to the two fixed CDSL historical XLS URLs to verify the visible archive links. It returned an unsupported-content-type/internal-error response and did not provide any parsed XLS values. The resulting attempts are **not accepted data samples**, do not establish field schema or date coverage, and must not be used to pass the future artifact gate. The attempts and limitations are disclosed in `research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md`. No repository dataset or model was changed. All further source retrieval still requires the new code gate and one-run approval.


## 2026-10-10 — Discovery 3 code gate REQUEST CHANGES (six blockers)

Tester rejected the implementation snapshot `918821ba9e74342bb282fe3a86138e8aa8e29ea7` despite 29 passing offline fixtures. Findings: (1) output report still carries stale spec Git blob `52b030...` instead of `4e30415632545c04a2875d627afa0191afe3f383`; (2) one matching JSON date lets conflicting other date fields pass; (3) numeric flow parsing accepts NaN/Infinity; (4) nested signature/sig values are not redacted; (5) dated page hrefs go into reports unsanitized; (6) live-workflow manifest reviewer commit is not proven to be the exact reviewed tree with all approved blobs at that commit. Must fix all six, add tests, pass offline suite, then request fresh exact-snapshot code gate. No source request/manifest allowed.


## 2026-10-10 — Discovery 3 code gate returned REQUEST CHANGES

The independent tester reviewed snapshot `918821ba9e74342bb282fe3a86138e8aa8e29ea7` and found six blockers despite 29 passing offline checks: outdated spec provenance in output, conflicting dates accepted in one JSON record, non-finite CSV values treated as numeric, incomplete redaction of signature-like fields, unsanitized dated links, and insufficient workflow binding between the reviewed commit and protected file tree. Full details are in `research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md`.

No live source request or approval manifest is authorized. Correct these issues, add offline fixtures, and request a new code gate.

## 2026-10-11 — Composite acquisition tester review (PASS WITH SCOPED RESTRICTIONS)

- **Issue observed:** the 2023 year request JSON exceeded the connected repository reader's exposed content size, preventing a transparent line-by-line independent review even though the Git blob existed.
- **Root cause:** one yearly request manifest contained 1,833 request objects and was larger than the content-reader's practical limit.
- **Correction:** recreated the exact 2023 request grid as two deterministic files (987 and 846 requests) and converted the former path to a small index. The root manifest references both new parts. The offline manifest validator and pipeline workflow passed after each split/root/index change.
- **Independent test result:** the tester reconstructed all 61 30-day windows and checked all 8,601 unique request keys, 61 spot calls, 8,540 option calls, 140 option selectors per window, required endpoint/interval/caps, and every flag/code/relative-strike/call-put cell. No missing or duplicate cells were found.
- **Decision:** [tester report](research/gates/PHASE7_PPR4_USER_DIRECTED_COMPOSITE_ACQUISITION_TESTER_REVIEW.md), PASS WITH SCOPED RESTRICTIONS for the exact manifest and acquisition workflow only. The Dhan external value cross-check remains waived. No source request occurred as part of the tester review or offline CI.
- **Prevention:** every active request submanifest is reader-sized, explicitly pinned by Git blob SHA, and loaded via the root manifest; the one-use live approval rechecks the pins before making the first request.
