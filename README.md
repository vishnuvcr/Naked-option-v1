# NIFTY Naked-Option Direction Research

Research program for predicting NIFTY 50 direction and translating signals into long-only naked option buying strategies for intraday and positional horizons.

## Research status

- Phase 2 passed the independent tester gate with explicit source restrictions.
- Phase 3 passed the independent tester gate with scoped data restrictions.
- Phase 4 Family B passed with VWAP blocked for missing PIT-safe volume; Family C passed with C10/C11 blocked for missing PIT-safe feature layers.
- Phase 5 Family D has completed the technical empirical gate with scoped restrictions. Earlier Family D runs remain rejected/non-evidence and are preserved in the logs; fresh run #23 passed independent tester audit.
- Rejected runs are preserved as non-evidence. Run #23 is the accepted Family D technical artifact, but no D model is promoted from descriptive maxima.
- Independent tester submissions for the Family D correction cycle are archived under [Phase 5 gates](research/gates/), including the run-1 request-changes report and the protocol-amendment approval.
- The current implementation uses the tester-approved session-based 20-trading-session intraday refit cadence while predictions remain on the frozen hourly grid. Run #16 is preserved as non-accepted evidence because of a D07 protocol/implementation mismatch. Run #19 is non-evidence because it timed out before artifact creation. Run #20 is non-evidence because the earlier intraday D13-D15 sequence cache was built on the hourly matrix and yielded n=0. The developer corrected the sequence path to the full 1-minute causal representation, the tester approved that correction, and fresh run #23 completed successfully. The independent tester gate for run #23 is PASS WITH SCOPED RESTRICTIONS. No D model is promoted; option economics, multiple-testing, robustness and fresh-forward validation remain mandatory.
- Phase 6 method specification and implementation code gate have now passed independent tester review. The exact E07 global composite amendment is frozen pre-result. Empirical execution is authorized through a gated GitHub Actions workflow; no Phase 6 metric is accepted until the immutable artifact is independently audited.

### Current Phase 5 scope

Family D evaluates D01-D15 using the frozen horizons: 5/15/30/60/120 minutes intraday and +1/+2/+3/+5/+10 sessions positional.

The current implementation retains the frozen hyperparameters. D04-D06 are explicitly provider-independent HistGradientBoosting surrogates. D13 uses a 20-observation lag-window MLP; D14 uses 16 fixed causal 3-tap filters followed by a 32-unit dense learner; D15 uses a fixed 2-head causal-attention representation of width 32 followed by a 32-unit dense learner. Intraday model fitting/prediction uses the frozen hourly decision grid while exact H-minute labels remain on the 1-minute path, and session-local sequence windows are enforced.

D07 now uses chronological training-only calibration for its base-probability stack. Standardization and all fitted transforms remain training-only. Failed runs are never treated as evidence.

## Canonical documents

- [Research plan](research/RESEARCH_PLAN.md)
- [Research protocol](research/RESEARCH_PROTOCOL.md)
- [Method registry](research/METHOD_REGISTRY.md)
- [Hypothesis catalog](research/HYPOTHESIS_CATALOG.md)
- [Literature review](research/literature/LITERATURE_REVIEW.md)
- [Literature search protocol](research/literature/LITERATURE_SEARCH_PROTOCOL.md)
- [Machine-readable literature registry](research/literature/LITERATURE_REGISTRY.csv)
- [Cost model](research/COST_MODEL.md)
- [Data source registry](research/DATA_SOURCE_REGISTRY.md)
- [Phase status](research/STATUS.md)
- [Research log](research/logs/RESEARCH_LOG.md)
- [Phase 5 run-1 research addendum](research/logs/PHASE5_RUN1_RESEARCH_LOG.md)
- [Error log](research/ERROR_LOG.md)
- [Phase 5 run-1 error record](research/logs/PHASE5_RUN1_ERROR.md)
- [Phase 5 sequence precompute tester gate](research/gates/PHASE5_SEQUENCE_PRECOMPUTE_TESTER.md)
- [Phase 5 D07 amendment submission](research/gates/PHASE5_D07_PROTOCOL_AMENDMENT_SUBMISSION.md)
- [Phase 5 D07 amendment tester review](research/gates/PHASE5_D07_PROTOCOL_AMENDMENT_TESTER.md)
- [Phase 5 run #16 tester pre-check](research/gates/PHASE5_RUN16_TESTER_PRECHECK.md)
- [Phase 5 D07 post-amendment tester gate](research/gates/PHASE5_D07_POST_AMENDMENT_TESTER.md)
- [Decision/chat log](research/logs/CHAT_LOG.md)
- [Phase 5 resume chat log](research/logs/CHAT_LOG_PHASE5_20261007.md)
- [Family D run #23 tester gate](research/gates/PHASE5_FAMILY_D_RUN23_TESTER.md)
- [Gate reports](research/gates/)

## Branch governance

developer implements research code and evidence packages.
tester is an isolated independent review environment. The tester independently checks mathematics, data joins, leakage, code logic, execution-cost assumptions, and reproducibility.
Each research phase has separate phase developer/tester branches and a tester gate before progression.

## Important prior-project evidence

Earlier Project artifacts reported a failed untouched-holdout next-day directional model (AUC about 0.458) and a more promising future-volatility signal. These are historical inputs only and are not accepted current results until revalidated under this repository's protocol.

## Disclaimer

This is research and backtesting infrastructure, not a guarantee of profit or investment advice. Long options can lose 100% of the premium paid.

## Latest research checkpoint — 2026-10-07

- **Family D run #23:** completed successfully.
- **Tester disposition:** PASS WITH SCOPED RESTRICTIONS.
- **Artifact:** `phase5-family-d-results` (ID `11499450561`; SHA-256 `27ca6cbc6e1653d40e2d896a81211c97a8d5e70543cf37ad9f402597eee306d8`).
- **Next gate:** independent tester review of the Phase 6 novel-method scope. No strategy has been promoted.

## Phase 6 checkpoint — 2026-10-07

- **Method specification:** tester approved.
- **Implementation/code gate:** tester approved.
- **E07 amendment:** exact four-source global composite frozen pre-result.
- **Empirical status:** authorized but not yet independently accepted; artifact gate remains mandatory.

## Latest Phase 6 checkpoint — 2026-10-08

- Fresh hosted Phase 6 run #575 (`37678088131`) is **NON-EVIDENCE** after the independent tester found a residual invalid `DatetimeIndex.iloc[...]` access in the later global-I03 cutoff path.
- Tester gate [PHASE6_RUN25_RESIDUAL_CUTOFF_TESTER.md](research/gates/PHASE6_RUN25_RESIDUAL_CUTOFF_TESTER.md) = **REQUEST CHANGES**.
- A detached developer correction commit is prepared with valid `DatetimeIndex[...]` access, regression coverage for the later cutoff path, and an assertion forbidding `decision_times.iloc`.
- The developer branch has not advanced to the proposed correction until the independent tester approves it. No Phase 6 metric or artifact is accepted; Phase 7 remains blocked.

## Phase 6 correction gate — 2026-10-08

- Tester gate [PHASE6_RUN25_RESIDUAL_CUTOFF_APPROVAL_TESTER.md](research/gates/PHASE6_RUN25_RESIDUAL_CUTOFF_APPROVAL_TESTER.md) = **PASS — fresh empirical execution authorized**.
- Corrected commit `e27b6358901dc60bc90bad295f46c9493ab63d1e` removes the residual `DatetimeIndex.iloc` defect in both cutoff paths and adds explicit later-cutoff regression coverage.
- Run #575 remains non-evidence. A new hosted run may be triggered only from the approved archived commit; no Phase 6 metric is accepted before independent artifact review.

## Phase 6 regression checkpoint — 2026-10-08

- Fresh hosted run #578 (`37680279189`) passed protocol and data acquisition but failed the mandatory regression suite before empirical execution.
- Tester gate [PHASE6_RUN26_REGRESSION_TESTER.md](research/gates/PHASE6_RUN26_REGRESSION_TESTER.md) = **REQUEST CHANGES**.
- The defect is confined to the regression fixture expectation: 13:15 − 120 minutes = 11:15.
- Run #578 is non-evidence; no artifact or Phase 6 metric was accepted. Phase 7 remains blocked.

## Phase 6 regression correction gate — 2026-10-08

- Tester gate [PHASE6_RUN26_REGRESSION_APPROVAL_TESTER.md](research/gates/PHASE6_RUN26_REGRESSION_APPROVAL_TESTER.md) = **PASS — fresh empirical execution authorized**.
- Correction `1a956f930b11850fb238ea3352565b36a7337395` fixes only the regression fixture arithmetic (13:15 − 120 minutes = 11:15).
- Run #578 remains non-evidence; the next run must pass the full regression suite before empirical execution.

## Phase 6 Run #581 — 2026-10-08

- **Status:** completed and independently audited.
- **Artifact:** `phase6-novel-results`, ID `11513410209`.
- **Artifact SHA-256:** `2065f7d8025b87f67de1a9f04908ec2fc015a6bda98c5a8162ddad3b01961c24`.
- **Coverage:** 200 registered cells; 140 executed, 60 correctly blocked by PIT/data-availability rules.
- **Tester gate:** [PHASE6_RUN581_TESTER.md](research/gates/PHASE6_RUN581_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS**.
- The technical artifact is accepted, but **no Phase 6 model is promoted**. Raw apparent accuracy/AUC elevations are not sufficient because multiple testing, chronological stability, costs, option execution economics, robustness and fresh-forward validation remain.
- **Next phase:** Phase 7 ensemble/regime-conditioned prediction, with a new independent tester gate.

## Phase 7 checkpoint — 2026-10-08

- Isolated branches created: `phase-07-developer` and `phase-07-tester`.
- Frozen specification: [PHASE7_METHOD_SPEC.md](research/phase7/PHASE7_METHOD_SPEC.md).
- Tester specification gate: [PHASE7_SPEC_APPROVAL_TESTER.md](research/gates/PHASE7_SPEC_APPROVAL_TESTER.md) = **PASS**.
- Registered methods P01-P10 cover fixed ensemble, abstention, chronological stacking and causal regime-conditioned combinations.
- Implementation/code and empirical gates remain pending; no Phase 7 result exists yet.

## Phase 7 specification amendment — 2026-10-08

- P08 regime thresholds were corrected before implementation: both volatility and trend are binary median splits estimated only from the training block.
- Tester amendment gate [PHASE7_SPEC_AMENDMENT_APPROVAL_TESTER.md](research/gates/PHASE7_SPEC_AMENDMENT_APPROVAL_TESTER.md) = **PASS**.

## Phase 7 implementation checkpoint — 2026-10-08

- P01-P10 implementation prepared in `scripts/run_phase7_ensemble.py`.
- Regression checks in `scripts/test_phase7_ensemble.py`.
- Workflow `.github/workflows/phase-07-ensemble.yml` includes automatic and manual empirical authorization gates.
- Tester regime-calibration gate = **PASS**. Complete implementation code review is the next gate.

## Phase 7 code-gate correction — 2026-10-08

- First implementation was rejected by the tester for missing family-level data-snooping inference and insufficient diagnostics.
- Corrected implementation now includes the frozen 500-rep moving-block Brier family test, regime counts/fallbacks, chronological block diagnostics and deterministic tests.
- A fresh tester code gate is required before empirical execution.

## Phase 7 code gate — 2026-10-08

- Tester code gate [PHASE7_CODE_APPROVAL_TESTER.md](research/gates/PHASE7_CODE_APPROVAL_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS**.
- Implementation includes P01-P10, causal stacking, four-state regime calibration, family-level moving-block Brier inference, chronological diagnostics and artifact schema validation.
- Empirical execution remains blocked until workflow registration and the separate workflow gate pass.

## Phase 7 workflow gate — 2026-10-08

- Tester workflow gate [PHASE7_WORKFLOW_APPROVAL_TESTER.md](research/gates/PHASE7_WORKFLOW_APPROVAL_TESTER.md) = **PASS**.
- Automatic caller and reusable workflow are approved. Default-branch registration and regression verification remain before empirical authorization.


## Latest Phase 7 Run #654 checkpoint — 2026-10-08

- **Hosted run:** #654 (`37763242007`) completed successfully through protocol, regression, empirical execution, validation and artifact upload.
- **Artifact:** `phase7-ensemble-results`, ID `11551679532`.
- **Artifact SHA-256:** `c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`.
- **Tester gate:** [PHASE7_RUN654_EMPIRICAL_TESTER.md](research/gates/PHASE7_RUN654_EMPIRICAL_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS** on the phase developer/tester branches.
- **Coverage:** 100/100 P01-P10 cells executed across 2 layers × 5 horizons.
- **Statistical result:** all family-level Brier data-snooping p-values are >0.05; no Phase 7 candidate is promoted.
- **Correction status:** the Run #650 moving-block bootstrap and regime-diagnostic defects are closed by the corrected implementation and independent Run #654 audit.
- **Next phase:** Phase 8 long-option execution research remains gated and must include Paytm Money brokerage/fees, exchange/statutory charges, spread, slippage, latency and premium-decay realism, followed by Phase 9 robustness and Phase 10 fresh-forward validation.

## Current research checkpoint — 2026-10-09 (updated)

- **Phase 7 status:** a fresh empirical run is active: [Research Protocol Check #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656), execution commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`. Protocol, the three regression suites, and the snapshot-bound tester authorization passed. The model script is still running; validation and artifact uploads have not started.
- **Independent code gate:** [Phase 7 correction snapshot review](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_RUN925_CORRECTION_CODE_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS** for one fresh execution only. Approval is bound to 25 protected-file SHA-256 hashes and the reviewed developer snapshot; it is not an empirical-result or trading-strategy approval.
- **Prior rejected evidence stays rejected:** [Run #925 independent audit](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957295201) re-confirmed its prior REQUEST CHANGES result (2,775 checks passed; 323 failed). Runs launched with stale authorization and Run #992's initial malformed approval mirror remain non-evidence.
- **Current blocker:** Run #994 must complete, validate and upload its immutable aggregate and row-level reference artifacts. Then the independent tester must rerun the source/hash/ten-panel/metric/inference audit against that exact run and commit. Phase 8 is still blocked until that empirical tester gate passes.
- **Progress records:** [latest phase status](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/STATUS.md), [detailed research log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md), [error log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/ERROR_LOG.md), [decision/chat log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/CHAT_LOG.md).
 
## Preliminary cost-source check for later Phase 8 (2026-10-09)

Phase 8 is not open yet. The initial public-source review found account-plan variation in Paytm Money brokerage material; the future model should bracket ₹10/₹15/₹20 per executed order until verified against the actual account tariff/contract note. NSE's public 2026 pages list ₹3,553 per crore premium-turnover transaction charges per side from 1 March 2026 and STT of 0.15% on sale premium / 0.15% of intrinsic value on exercise from 1 April 2026. Other applicable levies/GST, spread, slippage, latency and premium decay remain required. See the [official source list and restrictions](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md).


## Live checkpoint — 2026-10-09

- **Phase 7 Run #994:** [hosted run](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656). At the last verified check, the empirical ensemble step was still running; regression and the independent exact-snapshot authorization gate passed. Result validation and immutable artifact uploads were pending. No metrics are accepted and no strategy is selected.
- **Rejected evidence:** Run #925 remains non-evidence following independent tester review; do not substitute it for Run #994.
- **CI repair:** [Research Protocol Check #997](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37959386545) identified missing protocol/literature validator files on `main`. The exact scripts and literature registry were copied from `phase-07-developer`; a fresh protocol check is required to confirm the repair.
- **Gate rule:** Phase 8 remains blocked until Run #994 artifacts are uploaded and independently audited by the tester branch. Include broker tariff, statutory charges, spread, slippage and premium-decay assumptions before any option strategy is judged.
- **Logs:** [status](research/STATUS.md) · [research log](research/logs/RESEARCH_LOG.md) · [error log](research/logs/ERROR_LOG.md) · [conversation/decision log](research/logs/CHAT_LOG.md) · [Phase 7 tester gates](https://github.com/vishnuvcr/Naked-option-v1/tree/phase-07-tester/research/gates).

- **CI repair verified:** Research Protocol Check #1008 passed both repository-contract validation and literature-registry validation after the missing files and terminology mismatch were fixed. [Run #1008](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37960307076).
 
A broader free-source reconnaissance has also identified candidate Hugging Face, Kaggle-reported and Zenodo archives plus GitHub collectors; they are **not accepted datasets** until licensing, data coverage, OHLC-vs-quote quality and official NSE overlap are verified. Details and source links are recorded in the [developer research log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md). This is pre-gate preparation only; no Phase 8 implementation or option P&L run has started.
## Free-data quality caution — 2026-10-09

The broader source review also found preview-level validation warnings: `artist-23/nifty-options-data` lists a negative volume minimum and extreme maximum volume / IV values, requiring a full Parquet and official-NSE overlap audit before use. `codepyx23/india-index-options-1m` explicitly duplicates `thetrademarkk/india-index-options-1m`, so these cannot be treated as independent confirmation. Their CC-BY-NC-4.0 terms also need to be considered before any commercial use. These remain candidate sources only, not accepted data. See the [detailed candidate-quality requirements](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md).
Another lead is the public Hugging Face `Hitjob-Done/indian-stock-market-minute-data` dataset (reported MIT; NIFTY_50 minute/day OHLCV), but it is spot-only and may mirror `xxparthparekhxx/indian-stock-market-minute-data`; verify provenance, coverage, UTC-to-IST conversion and official NSE overlap before use. It is not an option-contract source. Details: [source audit log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md).
## Data licensing / public-repository caution — 2026-10-09

The official [NSE Data Sharing & Usage Policy](https://www.nseindia.com/static/market-data/nse-data-policy) says ownership remains with NSE/NSE Data and redistribution is governed by the relevant agreement; the [NSE copyright policy](https://www.nseindia.com/static/nse-copyright) restricts reproducing/storing site content elsewhere except within its stated terms. Because this repo is public, raw NSE bhavcopy archives and row-level market data must not be committed or republished without clear permission. Publicly store provenance, licenses, hashes, validation/reconciliation outputs and permitted aggregates; cache raw data only where source terms and access controls permit. The [research log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md) records the policy check and free ETL/pipeline leads.
A further read-only scan logged an NSE EOD archive bank, a Rust-based NSE data CLI, and a public overnight-straddle/event-IV code repository as **research leads only**. They are not independent price sources or accepted strategy evidence; any later use must verify licensing, provenance, absence of synthetic contamination, chronological holdout and all trading costs. See the [detailed research log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md).
 
## Automatic Phase 7 tester audit workflow — 2026-10-09

[Phase 7 Approved Artifact Audit](https://github.com/vishnuvcr/Naked-option-v1/blob/main/.github/workflows/phase7-approved-artifact-audit.yml) now supports both automatic auditing after a successful completed Phase 7 developer run and manual workflow dispatch with a required run ID. It fails closed unless the chosen successful developer run has both required immutable artifacts, uses tester audit code pinned to commit 50334eb728a85ae8ca88f9ded5246b867c9cb56f, and writes its full report to the isolated tester branch. The currently active [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656) still has no artifact at the last check, so no empirical gate has passed and Phase 8 remains blocked.
 
## Tester-audit preflight verification — 2026-10-09

The automatic workflow [run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37965605363) received a completed documentation-only developer protocol run ([#1033](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37965583008)) with no Phase 7 result artifacts. It detected the missing required artifact and correctly skipped the tester calculation. The workflow has since been tightened to require the exact upstream workflow name, branch, completed success state, immutable source commit and both non-empty artifact names. This validates only the preflight skip path; Run #994 still has no artifacts or accepted metrics. The manual run button requires a run ID and fails closed for incomplete or ineligible runs.
 
## Phase 7 code-delta check — 2026-10-09

A direct source comparison found the frozen Phase 7 method specification is unchanged between Run #925 and Run #994, while Run #994's implementation adds the registered P10 abstention handling, finite volatility/trend eligibility for regime counts, missing-row protection in family-bootstrap Brier differentials, and candidate-specific chronological-block masks. Added regressions cover those cases. This is a method-compliance correction, **not a passed result**; [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656) remains active with no output artifact at the latest check. The independent tester audit is required before any result/strategy promotion or Phase 8 transition. Details: [developer research log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md).


## Open tester review item — P10 regime diagnostic block counts (2026-10-09)

The frozen Phase 7 specification says regime-diagnostic block counts must equal candidate chronological-block counts for P08/P09/P10, but the current validator enforces equality only for P08/P09 because P10's [0.45, 0.55] abstention can leave empty candidate blocks. Run #994 is still active, so no artifact has yet been adjudicated. This inconsistency has been logged for the independent tester; do not change the frozen spec or promote any result post hoc. The tester must resolve whether implementation can satisfy both rules or a pre-registered, separately approved amendment is needed. Phase 8 remains blocked. Details: https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/ERROR_LOG.md


 
## Independent tester finding — P10 diagnostic block invariant (2026-10-09)

The isolated tester branch has issued [PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md) = **REQUEST CHANGES FOR SCIENTIFIC PROMOTION** for a static consistency issue: the frozen spec includes P10 in the regime-diagnostic/chronological-block count equality, while the current validator enforces this invariant only for P08/P09 because P10 abstentions can empty a block. Run #994 may complete and be audited as the already-running immutable execution, but no metric, method or strategy may be promoted until this issue is resolved through an implementation correction or a separate pre-registered tester-approved spec amendment. Phase 8 remains blocked.


 
## Latest Phase 7 resume — 2026-10-09 23:20 IST

- **Empirical Run #994:** still in progress on immutable source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`; validation pending; no artifacts; job log retrieval currently returns BlobNotFound.
- **P10 correction:** developer commit [`39e964d`](https://github.com/vishnuvcr/Naked-option-v1/commit/39e964d4ae99bb02b113fa4eabecd91c9af46c16) passed the regression job in [developer workflow #1068](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37968150153), but empirical and tester-gated jobs were skipped.
- **Independent tester review:** pending on [the isolated tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md).
- **Decision:** no accepted metrics or promoted strategy; Phase 8 remains blocked.


## Latest independent Phase 7 audit — Run #37957677656

- Decision: **PASS WITH SCOPED RESTRICTIONS — artifact integrity, source alignment, metric reconciliation and family inference** (3098 passed / 0 failed checks).
- Source run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656
- Exact developer commit: b50be8cfa1ebe008a800e65a53f9c0fb2581aecb
- Tester report: https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_RUN_37957677656_EMPIRICAL_TESTER.md
- Full JSON: https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_RUN_37957677656_AUDIT.json
- This technical audit does not independently promote a trading strategy or open Phase 8.

## 2026-10-10 — Run #994 empirical result and independent audit

- [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656) completed successfully on immutable source commit b50be8cfa1ebe008a800e65a53f9c0fb2581aecb. Both aggregate and row-level reference artifacts are retained.
- Independent tester: **PASS WITH SCOPED RESTRICTIONS**; 3,098 checks passed, 0 failed. This covers artifact integrity, source alignment, 100 metric cells, and 10 family-level tests—not strategy promotion.
- All ten family-level moving-block bootstrap tests are non-significant: daily horizons 1/2/3/5/10 have p-values 0.784/0.690/0.938/0.764/0.506; intraday horizons 5/15/30/60/120 have p-values 0.262/0.994/1.000/0.994/0.544. No tested family demonstrates statistically significant predictive improvement.
- Best isolated headline cells are not confirmatory: daily P10/H10 Brier 0.243729, ROC-AUC 0.5786, balanced accuracy 0.4963 (family p=0.506); intraday P07/H5 Brier 0.249348, ROC-AUC 0.5297, balanced accuracy 0.5212 (family p=0.262). They are candidate-level observations within a multiple-method search, not a validated trading edge.
- **Decision: no strategy selected; no live-trading recommendation.** Net profitability after option bid/ask spreads, slippage, brokerage, STT, exchange charges, GST and other Paytm Money costs has not been demonstrated. Phase 8 remains blocked.
- Open restriction: the separate tester static report still flags the P10 diagnostic-block invariant for future runs. The immutable Run #994 audit does not itself clear that future-run protocol/code consistency issue.
- The audit workflow had a shell syntax defect in its fallback-report step despite a completed technical audit; this was logged and fixed in main commit 3c0730bbdb31c18a1b0ad9e62c998189ae243dca. The audit decision/report itself is preserved.


## Authorization note — 2026-10-10

The P10 diagnostic code correction has static tester approval for a future run only, but the exact-snapshot approval manifest remains at the last verified snapshot. A fresh empirical run is not yet authorized: updated report digest/protected hashes must be recomputed and independently verified before the hosted snapshot validator can pass. This is a governance hold, not a change to Run #994's result. No strategy is selected; Phase 8 remains blocked.


## Current research checkpoint — 2026-10-10

**Phase 7 is blocked pending exact-snapshot authorization.** Run #994 remains the latest accepted empirical evidence; all ten family-level tests were non-significant, and no strategy is selected. The latest audit workflow validated existing artifacts but skipped the pinned independent tester job, so it does not constitute a new empirical result. Phase 8 remains blocked until a fresh run is explicitly authorized, independently audited, and evaluated net of options spreads, slippage, Paytm Money brokerage and statutory charges. See [research status](research/STATUS.md).


## Research resumed — uploaded literature and Phase 7 correction gate (2026-10-10)

### Newly added research sources

- The 15 unique research PDFs supplied in the conversation have been reviewed and indexed as L037–L051. The [paper-by-paper supplement](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-01-developer/research/literature/UPLOADED_PDF_REVIEW_2026-10-10.md) records each paper's question, methods, author-reported findings, limitations and relevance to this research. The [machine-readable registry](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-01-developer/research/literature/LITERATURE_REGISTRY.csv) now has 51 source records.
- Independent literature gate: [PHASE1_UPLOADED_PDF_SUPPLEMENT_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-01-tester/research/gates/PHASE1_UPLOADED_PDF_SUPPLEMENT_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS** for literature incorporation only.
- The supplement does not turn paper-reported accuracy/returns into project results. In particular, normalized price-fit “accuracy” is not directional accuracy; small or in-sample tests are not equivalent to untouched chronological evaluation; and option-strategy papers are context only for the current prediction extension.
- Registry row L003's pre-existing semantic column displacement was corrected and recorded in the research error logs.

### Latest workflow integrity check (2026-10-10)

A further audit found that the NIFTY acquisition script used by the empirical job was not included in the protected hash allowlist. The developer workflow has now been amended to include \`scripts/acquire_nifty_daily_history.py\` in its push triggers, approval allowlist, and SHA-256 report. This changes the exact workflow snapshot after the previous static tester review. The hosted regression result is still not visible, so the latest code remains **NOT AUTHORIZED** for empirical execution pending a fresh independent review and observable green workflow run.

### Active prediction extension

- **Phase 7 available-data/global-feature prediction extension:** still **NOT AUTHORIZED for empirical execution**. The initial tester review requested changes for G13 using z-scores instead of the frozen raw-return composite definition, Bonferroni adjustment using only executed rather than all five registered horizons, unclear paired baseline comparability, and incomplete result validation.
- Developer correction includes raw-return G13 with a fixed constituent set, the five-horizon Bonferroni factor, candidate-specific paired baseline metrics, a row-level forecast-panel artifact, and a standalone validator that recomputes candidate/baseline metrics and the family bootstrap from the panel. Negative schema regressions and workflow protection changes cover these outputs.
- Exact updated handoff: [PHASE7_AVAILABLE_GLOBAL_DEVELOPER_SUBMISSION.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_DEVELOPER_SUBMISSION.md).
- The initial Phase 7 tester report remains as historical REQUEST CHANGES. The latest resubmission report on the isolated tester branch is [PHASE7_AVAILABLE_GLOBAL_RESUBMISSION_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RESUBMISSION_TESTER.md): static source review passed with restrictions, but empirical execution is **NOT AUTHORIZED** because the hosted regression outcome could not be verified. The row-level panel is a planned output of the next authorized run and has not been generated. **No prediction output has been generated by this extension**, and Phase 8 remains blocked.
- See the developer [research status](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/STATUS.md), [error log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/ERROR_LOG.md) and [decision/chat log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/CHAT_LOG.md) for detailed correction history.

**Developer → Tester:** independently verify the corrected Phase 7 exact snapshot and actual hosted regression outcome; approve at most one empirical run only if every formula, mask, protected hash and result-validation contract passes.  
**Tester → Developer:** return a decision with exact reviewed commit/hashes and explicit execution authorization status. A literature review pass or code correction is not empirical approval.
