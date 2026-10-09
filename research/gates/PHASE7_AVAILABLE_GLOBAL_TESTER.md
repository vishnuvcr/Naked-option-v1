# Independent Tester Report — Phase 7 Available-Data Prediction Extension

**Decision: REQUEST CHANGES — empirical execution NOT authorized**  
**Review date:** 2026-10-10  
**Review scope:** independent static review of the developer's available-data/global-feature prediction extension. This review does not execute the empirical model and does not accept any metrics.

## Exact developer artifacts inspected

- Method specification: research/phase7/AVAILABLE_DATA_PREDICTION_SPEC.md — blob SHA 327d576f65e66eed184eb4123aafac424cea2af6.
- Acquisition: scripts/acquire_global_history.py — blob SHA 401fdacd3aa562b4907d422eb296fec502aa8f3c.
- Predictor: scripts/run_phase7_available_global.py — blob SHA 4181eb76f2d1b92fa65bc0a3b75b3a1ed5b606f7.
- Regression tests: scripts/test_phase7_available_global.py — blob SHA fe5d425c47a9192e7673d9fbfec735ba5cb7cb78.
- Workflow: .github/workflows/phase-07-available-global.yml — blob SHA 3a45705b049cc3e0bb924f15db5d8e763a7e1573.
- Developer handoff: research/gates/PHASE7_AVAILABLE_GLOBAL_DEVELOPER_SUBMISSION.md — blob SHA ece01ef83d7f6ff3f990735aa813db06adcf0615.
- Phase 7 scope remains prediction-only. The new uploaded-paper literature supplement does not change the frozen Phase 7 spec and must not be treated as an authorization.

## Positive checks

1. The target is explicitly next-1/2/3/5/10-session NIFTY direction; exact zero returns are excluded from binary labels rather than silently labeled up or down.
2. Global/peer features are created from each source's own chronologically ordered series, then backward as-of merged with exact same-date matches disabled. This is a conservative source-local-session rule.
3. The walk-forward loop fits models in fixed 20-row blocks, applies training-only scaling, and excludes the most recent H label rows from each training prefix.
4. The historical positive-rate benchmark is calculated independently of candidate feature completeness. Existing regression coverage correctly checks that a missing candidate feature should suppress that candidate forecast without suppressing the baseline.
5. The moving-block Brier comparison uses a common eligible row set across included candidate probability vectors, recentered candidate loss differentials, a fixed seed and 500 bootstrap replicates.
6. Source acquisition failures are recorded individually, source files are SHA-256 checked against the manifest, and the workflow is fail-closed when the independent approval file/report is missing.
7. The uploaded PDFs are literature inputs only; the extension has no options strategy or option P&L path.

## Required changes before approval

### 1. G13 does not implement the frozen specification

The frozen spec defines G13 as the arithmetic mean of the latest available prior-date **raw one-session and five-session log returns** from the qualifying global equity indices. The current implementation instead uses each source's ret1_z20 and ret5_z20 fields. This is a method/specification mismatch even though those z-score fields are causal.

The current row-wise pandas mean also skips missing values, allowing the effective number of contributors to vary from row to row even though the manifest-defined constituent list is declared frozen.

**Required correction:** implement the frozen raw-return definition and make missingness semantics explicit. For a fixed constituent set, do not silently average whichever sources happen to be non-null on a row. Either require all frozen constituents to be available for that composite row (with candidate abstention recorded where not) or submit a separately pre-registered specification amendment before any result exists. Add a regression where standardized and raw-return inputs intentionally differ and a second case where one constituent is missing. Do not compare or select candidates from results produced by the mismatched definition.

### 2. Bonferroni correction uses an observed test count instead of the pre-registered family size

The frozen spec requires correction across the five registered horizons. The predictor currently sets mtests to the number of horizon-level family tests that happened to execute, then uses p multiplied by mtests. If one or more horizons are NOT_APPLICABLE, the resulting adjustment can be less conservative than the registered five-horizon correction.

**Required correction:** use the fixed registered family size (five horizons) for the Bonferroni multiplier, while reporting the number of family tests actually executed separately. Add a deterministic test where at least one horizon is unavailable and assert that every available raw p-value is adjusted by min(1, 5 × p), not by the number of successful tests.

### 3. Baseline and candidate headline metrics need explicit sample comparability

The causal baseline vector is intentionally available on held-out label rows where a candidate's features are missing. That is a useful benchmark property and should be retained. However, the published _BASELINE headline metric cell is currently calculated on the broader set of available baseline rows, whereas candidate metrics are calculated only where each candidate's features and predictions are finite. Directly comparing these cells can therefore compare different test samples.

**Required correction:** preserve the feature-mask-independent baseline vector, but explicitly report sample counts and paired baseline metrics on the corresponding candidate/common evaluation rows (or clearly label the full baseline metric as a separate all-eligible-row diagnostic that is not directly comparable to candidate metrics). Ensure the common-row paired baseline used for candidate and family Brier comparisons is unambiguous in the output schema and documentation. Add a fixture where one candidate has a missing test feature and verify both the full baseline and the paired comparison behavior.

### 4. Hosted result validation is incomplete for required statistical fields

The workflow checks the five horizons, most candidate cells, metric bounds, confusion-count reconciliation, provenance and holdout status. It does not require the per-horizon _BASELINE cell, nor does its hosted schema gate validate the family-inference record and its Bonferroni values against the five-horizon frozen rule. BLOCKED_DATA cells are skipped without verifying that a non-empty reason is retained.

**Required correction:** extend the result validator to require the full expected cell grid including _BASELINE and _FAMILY_TEST; validate the family_inference executed/not-applicable state; verify raw and five-horizon-adjusted p-values are finite and in [0,1]; verify each blocked candidate/horizon has a meaningful reason; and add regression fixtures for malformed/missing inference and missing blocked reasons. Keep these checks in a separately testable function or script rather than relying only on an inline workflow snippet.

### 5. Documentation-quality correction

The numbered data-rules section in AVAILABLE_DATA_PREDICTION_SPEC.md uses “7.” twice and omits the next ordinal. Correct the numbering without altering the frozen scientific definitions.

## Authorization decision

**REQUEST CHANGES. No empirical run is authorized by this report.** The workflow must remain fail-closed and no PHASE7_AVAILABLE_GLOBAL_APPROVAL.json granting execution should be issued against the reviewed snapshot. No protected SHA-256 approval manifest is issued because the reviewed code/spec contract is rejected.

Regression success alone cannot resolve these scientific-definition and inference issues. After correction, the developer must resubmit the exact updated snapshot for a new independent tester review. Rejected/ineligible runs remain non-evidence.

**Tester → Developer:** Correct G13 to its pre-registered raw-return definition with fixed row membership, use the five-horizon Bonferroni family size, clarify full versus paired baseline metrics, strengthen schema/inference validation, add the listed regressions, fix spec numbering, then resubmit exact files and run IDs. Do not alter the frozen spec post hoc to fit any empirical outcome.

**Developer → Tester:** Review the corrected implementation on the developer branch independently, verify every formula/mask/count and failure path, and return a new gate report. Authorize only one fresh exact-snapshot run after all findings pass; then perform a separate immutable artifact audit. Do not advance to option-strategy research.


## 2026-10-10 — Current exact-snapshot execution gate review after Run #43

**Current decision: PASS WITH SCOPED RESTRICTIONS.**  
**Empirical execution authorization: YES, for one Phase 7 available-data prediction batch only, on the exact protected snapshot listed below.**  
**Run #43 / 37992695619:** https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992695619

### Reviewed exact snapshot

- Developer commit: `f04b96bc47477981bfdc63271f1e80402f9428e8`
- Frozen spec SHA-256: `37ab05618fdc75514090c1871c6a276998fbddfc19519e28db7ddbf5cf5ecd30`
- `scripts/acquire_global_history.py`: `4a6f1b4064c312153db7109131edf3fe07b17f2bf2d78cc03c0be265ff220def`
- `scripts/acquire_nifty_daily_history.py`: `30d9900d29d40c5b93955aee6b290ac18d81a11a9f5cb8d8b5f3b93b350b6e19`
- `scripts/test_acquire_nifty_daily_history.py`: `b7269fb207d311309feebc322309adecdc9acbe64a4dc418170cfcf3502ec34e`
- `scripts/run_phase7_available_global.py`: `aa3f8ab8751bb6ac0bdb3238dbd1a440f15f3019076666c02100b23aefd2e716`
- `scripts/test_phase7_available_global.py`: `4d8b11a4dca4804ce3fa277977623e392815854833f431d80e42d3a2971d7832`
- `scripts/validate_phase7_available_global_results.py`: `1f5459f64b0cfea94bd2ec3290f0f493a8c54d06e7039f3be3548766716ff7bc`
- `scripts/test_validate_phase7_available_global_results.py`: `697a434c4b4d4b14aae474340dab41fb803b60ea681699d74a362b9640be8fd7`
- `requirements-phase7-available.txt`: `c4e77ae82f1ac8b8a81d61351d580432c07760798595d0f34d488c4b5cd57022`
- `.github/workflows/phase-07-available-global.yml`: `e137ed819e5c2e16ac07ac0ba6e6fd8628e212485649dd307486edcdda2e7df3`

### Hosted regression evidence and independent checks

Run #43 regression job passed all test families: **8/8 NIFTY acquisition/cache checks, 11/11 predictor checks, and 11/11 result-validator checks**. The run's authorization step correctly found no approval manifest, and the empirical job was skipped. Earlier failure attempts #41 and #42 were caused by test-fixture omissions/inconsistent mock overlap values; the fixtures were corrected and these attempts remain regression-only non-evidence.

The reviewed corrections now: make acquisition import-safe; reuse a valid recent cache without network calls; reacquire on stale, invalid, checksum-mismatched, or manifest-missing cache; derive NIFTY session dates in Asia/Kolkata using provider timezone metadata with an explicit India-timezone fallback; define query boundaries at India-local midnight; exclude an incomplete current-day bar before the conservative 18:30 IST cutoff; reject same-day rows before that cutoff; and reconcile official overlap close, Yahoo close, difference arithmetic and within-one-point status against the exact CSV row. Negative and boundary cases are in the protected acquisition regression suite.

The predictor and output validator corrections from the prior reviewed report remain present: strict prior-session joins, horizon-label purge, training-only scaling, fixed registered horizon family size, paired-baseline samples, row-level panel SHA, and re-computation of metrics and family bootstrap inference. The source acquisition and point-in-time data contract were reviewed against the exact source snapshot; this is not an assertion that external sources will be available during acquisition.

### Scope of authorization

This approval is limited to **one** empirical Phase 7 prediction batch on the exact hashes above. It does not approve options strategies, Phase 8, a final-holdout opening, model promotion, or a trading recommendation. Source failures must remain method-specific `BLOCKED_DATA` with reasons; no missing data may be fabricated. The run's source manifest, cached CSV hashes, summary JSON and row-level panel must be retained. After the run, the independent tester must audit the immutable run ID/artifacts, recompute result metrics and family inference, report significance/uncertainty and coverage limitations, and separately decide whether any candidate merits further work. A green regression suite alone is not predictive evidence.

**Tester → Developer:** Mirror this exact report to `research/gates/PHASE7_AVAILABLE_GLOBAL_TESTER.md` on the developer branch and create the one-run approval manifest using the exact report digest and protected SHA-256 values above. Let the automatic workflow run; do not edit protected files after approval. After the batch, submit immutable artifacts for an independent result audit before any candidate or strategy is promoted.

**Developer → Tester:** Audit the resulting workflow run and all artifacts independently. Check acquisition coverage/source hashes, timestamp joins, target labels, metric reconciliation and five-horizon family tests. Keep Phase 8 blocked until a separate tester decision authorizes progression.
