# Phase 8 Strategy-Testing Readiness — Independent Tester Review
Date: 2026-10-12
Decision: **BLOCKED for empirical P&L; proceed with non-empirical regression only**

## Scope
Independent review of whether the accepted Phase 7 forecast artifact and currently registered option data can support a valid Phase 8 long-option backtest without changing the frozen 4,800-cell strategy universe or weakening controls.

## Evidence checked
- `research/phase8/PHASE8_FROZEN_INPUT_MANIFEST.json` pins Phase 7 Run #994, artifact 11638738288, archive SHA-256 `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`, 10 forecast panels and 50,555 forecast rows. The manifest explicitly sets `empirical_option_execution_authorized=false`.
- `research/phase8/PHASE8_DATA_PLAN.md` requires option contract identity, type, strike, expiry, lot size, timestamp, OHLC and (where available) bid/ask, volume, OI, source and snapshot provenance; it prescribes official NSE reconciliation and secondary-source validation.
- `scripts/run_phase8_long_option.py` registers 4,800 configurations, but its input gate marks every configuration INELIGIBLE with `POINT_IN_TIME_FIXED_CONTRACT_PANEL_NOT_YET_APPROVED`; empirical mode exits before reading option data and says the fixed-contract panel and reviewed executor are not authorized.
- `.github/workflows/phase-08-long-option.yml` has regression/self-test jobs and an explicit `workflow_dispatch` input defaulting to false. Its empirical job depends on empirical authorization, source, reconstruction and regression gates.
- Previous R5 duplicate-diagnostic code and executor workflow reviews were code/workflow-only; the actual encrypted artifact has not been scanned, and no real duplicate classifications exist.

## Independent checks and reasoning
1. A prediction panel does not provide the realized executable option contract path or price series needed for option P&L.
2. The available composite is described as a partial grid; historical contract expiry/master joins are not verified as point-in-time correct. A present-day contract master cannot safely be projected backward without historical effective dates.
3. OHLC or model-estimated Greeks are not executable bid/ask quotes. Any proxy-based result must be clearly segregated as a sensitivity experiment, not represented as executable trading P&L.
4. The four frozen cost scenarios and Paytm Money charges must remain applied consistently; spread/slippage sensitivity cannot cure missing contract identity or expiry ambiguity.
5. A substitute panel cannot be accepted merely because rows exist. It must pass contract identity, timestamp/expiry/lot-size point-in-time validation, provenance, duplicate classification, causality, quote/execution-price policy and frozen cost checks.

## Decision
**BLOCKED** for empirical option P&L and strategy ranking. Do not loosen the gate or fabricate metrics. **PASS to continue only the permitted synthetic regression, source feasibility audit, and aggregate-only duplicate diagnostic after its separate one-use authorization is legitimately present.**

## Required next actions
1. Run the existing Phase 8 regression/self-test path; preserve run ID, job outcomes and artifacts.
2. Resolve the one-use authorization using the repository's approved process; do not reuse consumed R1 nonce or treat the unapproved R2 nonce as authorization.
3. Run the R5 aggregate-only duplicate diagnostic on the exact pinned artifact and retain its report/hash.
4. Audit existing source cache/official samples for a historical point-in-time contract panel. Report per-field coverage and failed joins; do not silently infer expiry/lot size.
5. Submit the proposed panel manifest and data-quality report for a new independent tester gate before any empirical P&L.
6. Only after all gates pass, execute the frozen 4,800-cell grid and four cost scenarios; report net metrics, drawdowns, trade counts, uncertainty and multiple-testing controls.

## Gate boundary
This review is not a trading recommendation, does not accept an empirical result, and does not authorize empirical P&L. The branch's role remains **independent tester**.

### Developer → Tester
Developer should supply a hash-pinned panel manifest, field-coverage/official reconciliation report, duplicate-diagnostic result, and fresh regression evidence for independent re-review. Keep empirical authorization false until the tester issues a separate PASS.
