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


## Latest Phase 7 gate status — 2026-10-10

- Hosted [Run #43](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992695619) passed **8 NIFTY acquisition/cache**, **11 predictor**, and **11 result-validator** regression checks. It does not contain prediction metrics; earlier Run #41 and #42 fixture failures remain documented as non-evidence.
- The NIFTY downloader now reuses a valid hashed cache, converts source timestamps using `Asia/Kolkata`, sets query boundaries at exchange-local midnight, blocks incomplete same-day bars before the 18:30 IST cutoff, and reconciles manifest overlap checks with exact CSV closes.
- The independent tester's current [exact-snapshot gate report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_TESTER.md) is **PASS WITH SCOPED RESTRICTIONS**, authorizing a single Phase 7 available-data prediction batch only. Its mirrored copy is available [on the developer branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_TESTER.md).
- **No empirical prediction batch has run.** The approval JSON write was blocked by platform safety checks; the manifest remains absent and the workflow correctly remains fail-closed. Do not interpret green regression checks as predictive performance.
- See the [research status](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/STATUS.md), [error log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/ERROR_LOG.md), [research log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/RESEARCH_LOG.md), [chat log](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/logs/CHAT_LOG.md), and [Phase 7 developer handoff](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_DEVELOPER_SUBMISSION.md) for full details.

**Developer → Tester:** Audit exact hashes and regression evidence independently; when the authorized immutable prediction batch is produced, reconcile its source and row-level artifacts before any statistical or strategy promotion.

**Tester → Developer:** Keep execution fail-closed absent the one-run exact-snapshot manifest and keep Phase 8 blocked until empirical output passes independent review.


## Phase 7 Run #44 — available-data prediction result (2026-10-10)

- [Run #44](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915) completed regression, exact-snapshot authorization, prediction, result validation and artifact upload successfully.
- Immutable result artifact: ID `11657636547`, SHA-256 `63b607db7227cdd91f3a62a0a8ca5f0b010d12c3bad1848ebbd9f59961804891`.
- Independent audit reconciled the 91,988-row prediction panel, source hashes, all candidate metrics and all five family bootstrap p-values. All 60 registered method/horizon cells executed.
- Best descriptive Brier leaders: G13 global-equity composite at 1–2 sessions; G06 Asia composite at 3–5 sessions; G02 Bank Nifty at 10 sessions. G06 at five sessions had Brier improvement +0.001623 and ROC AUC 0.556, but family p=0.7745.
- Family p-values at horizons 1/2/3/5/10 were 0.9840/0.8882/0.6786/0.7745/0.9800; every Bonferroni-adjusted p-value was 1.0. **No candidate is promoted; the registered family did not demonstrate statistically persuasive predictive skill.**
- [Full result summary](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/results/PHASE7_RUN44_AVAILABLE_GLOBAL_PREDICTION_RESULTS.md), [tester audit on isolated branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md), and [mirrored tester audit](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md).
- **Phase 8 remains blocked.** The final untouched holdout remains unopened. This was prediction-only research; options, brokerage, slippage, spreads, Paytm Money execution and trading P&L were not tested.
- All 11 global source entries reported cache misses in this run because the previous cache did not meet the current contract; the newly acquired files were retained in the immutable artifact and workflow cache.


## Next prediction-only research step — Extension 2 proposal (2026-10-10)

Run #44 was independently audited and found no statistically significant candidate: family p-values for 1/2/3/5/10 sessions were 0.9840/0.8882/0.6786/0.7745/0.9800, with every Bonferroni-adjusted p-value equal to 1.0. No model was promoted, and the final untouched holdout remains unopened.

To continue the finite registered prediction universe without entering options strategy research, the developer has proposed a new family covering **G03 sector leadership, G14 FII/FPI flow, G15 DII flow, G17 advance/decline breadth, F03 put/call OI ratio, F04 OI-change acceleration, and F05 volume/OI pressure**. Source leads are the official [NSE F&O reports](https://www.nseindia.com/all-reports-derivatives), [NSE historical index and breadth archives](https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives), and [NSE FII/FPI/DII reports](https://www.nseindia.com/reports/fii-dii). The proposal freezes seven candidates and uses one global max-statistic bootstrap across 35 method/horizon cells.

- [Extension 2 specification](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md)
- [Developer submission for independent tester review](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_DEVELOPER_SUBMISSION.md)
- [Run #44 results](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/results/PHASE7_RUN44_AVAILABLE_GLOBAL_PREDICTION_RESULTS.md)
- [Run #44 independent audit](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md)

**Gate status:** Extension 2 is proposal-only. No full-history download or model fitting is authorized until the independent tester reviews the exact specification and source-feasibility plan. Phase 8 remains blocked and the final holdout remains unopened.


### Extension 2 specification gate update — 2026-10-10

The first independent spec review returned **REQUEST CHANGES** before any data access. The developer corrected the F&O legacy-to-UDiFF transition, FII/DII normalization, F04/F05 formulas, sector-index identities, and global bootstrap treatment of missing candidate forecasts. The corrected [specification](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md) and [developer resubmission](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_DEVELOPER_SUBMISSION.md) await a fresh independent tester decision. No source data have been downloaded and no model has been fit for Extension 2. If passed, the next gate permits only small-sample source feasibility—not full-history acquisition or empirical prediction.


### Extension 2 Gate A source-feasibility update — 2026-10-10

[Gate A Run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019391488) passed six offline checks. Official NSE legacy F&O (2024-07-05) and UDiFF (2024-07-08) sample archives were fetched and validated. The NSE FII/DII API sample proved only current-day access; one free GitHub mirror contains 164 dates (Jan–Sep 2026), below the planned 500-date inference minimum. The first sector API attempt returned generic HTML, and historical Advances/Declines data were not verified. The tester returned REQUEST CHANGES for source-feasibility completeness.

- [Gate A Run #1 report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/results/PHASE7_EXTENSION2_GATE_A_RUN1.md)
- [Independent tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_FEASIBILITY_RUN1_TESTER.md)

Next bounded step: sample the official NSE daily index CSV archive and equity bhavcopy, then continue free-source historical FII/DII discovery. Full-history acquisition and model fitting remain unauthorized.


### Gate A sampler v2 code gate — 2026-10-10

The first v2 workflow attempt failed an offline FII/DII date-validation regression before making any live source requests. The over-escaped ISO-date regex has been corrected, and the workflow now requires an explicit tester-approved Gate A approval manifest before its automatic push trigger can fetch sources. The corrected sampler/tests are awaiting independent re-review. No source data or model results were generated by the failed run.


### Gate A sampler v2 — exact-snapshot review required (2026-10-10)

The existing tester PASS applies to an earlier sampler v2 blob. The current sampler was changed to correct FII/DII date normalization, and the workflow was tightened to fail closed on both automatic and manual source-sampling triggers. Therefore the earlier PASS is not being reused.

- [Exact-snapshot review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_REVIEW_REQUEST.md)
- Current sampler blob: `fb83fe5e880a26134a765a0426f7aa85380272fb`
- Current offline test blob: `d818613dc2f9188224562a953fd979a6c274d292`
- Current guarded workflow blob: `c535610e69c2e90934ab4e59d754b584e29ff6ec`
- [Prior Run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019728293) failed before source acquisition; network-fetch and artifact-upload steps were skipped.

**Current gate:** independent re-review of this exact snapshot and a green hosted offline test run. The Gate A approval manifest is absent. No live source sample, full history, feature table, model fit or new metric has been produced by this checkpoint.


### Gate A exact-snapshot guard hardening — 2026-10-10

The Gate A workflow was strengthened again at blob `fdc0a6bef97796b38424048304b704d86f80c450`. A source-sampling run now requires an explicit tester report digest plus all six current protected Git blob IDs quoted in that report, matching file SHA-256 and Git blob maps, reviewed-commit ancestry, and explicit report text prohibiting full-history acquisition and model fitting. Manual sampling defaults to off. The previous sampler/workflow PASS is not treated as approval for changed blobs.

See the [current exact-snapshot review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_REVIEW_REQUEST.md). No Gate A source-sample run was triggered by this change; no approval manifest exists.


### Gate A F&O archive sampling coverage correction — 2026-10-10

Before any live sample request, a second audit found the v2 sampler workflow did not call the legacy/UDiFF F&O archive sampler. The workflow now runs both bounded source samplers and uploads both the F&O transition report and the index/equity/FII-DII report. Current workflow blob: `1d8991255ff284c6b9cb20c4071ab56555d18dc6`.

- [Updated exact-snapshot review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_REVIEW_REQUEST.md)
- This correction did not fetch any live data. The current exact-snapshot tester gate must pass before the bounded Gate A source workflow can execute.


Repository [Research Protocol Check #38020253978](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38020253978) succeeded, but it validates repository contract/literature registry only. It is not evidence that the Gate A v1/v2 source-schema test suites passed. The exact-snapshot review and the gated workflow run are still required before any live samples are fetched.


### Extension 2 Gate A sampler v2 — exact-snapshot code PASS (2026-10-10)

The independent tester has passed the current protected sampler/spec/test/workflow snapshot for **one bounded Gate A source-sampling run only**. Hosted offline regressions passed: [Run 38026024826](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026024826) completed 22 unique checks (7 v1 + 15 v2); [Run 38026080844](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026080844) confirmed the legacy workflow is now offline-only.

The bounded sampler fixes the previous multi-year FII/DII API request. Its dated request is restricted to ten days; the API responses are capped at 512 KB and 50 rows, with regression tests for requests/response handling. The exact tester report is mirrored at [PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_TESTER.md).

**Governance incident disclosed:** legacy Run 38025793938 fetched only bounded F&O dates and small page/API samples without the exact tester manifest. Its artifact `11659904438` is non-accepted evidence. The old live-fetch workflow was replaced with offline-only tests; the guarded v2 workflow remains the only live-sampling route. No full history, features/labels or model fitting occurred.

**Next:** the approved, hash-bound manifest must pass in the guarded workflow, then one bounded run may upload two JSON source-feasibility reports. Those reports need another independent tester audit. **Full-history acquisition and model fitting remain unauthorized.**


### Gate A artifact audit — REQUEST CHANGES (2026-10-10)

The first approved bounded sample run completed, but the tester rejected its artifact. The F&O archive and cash-equity samples passed their schemas; two official sector-index CSVs failed the date check because the date parser did not support `DD-MM-YYYY`. The NSE date-parameter FII/DII API returned current 2026-10-09 records outside the requested 2024 window, yet the previous parser incorrectly accepted the response as JSON.

The previous authorization manifest has been revoked. [Run 38026433233](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026433233) confirmed fail-closed behavior: offline tests passed, authorization failed, and source sampling was skipped. Developer corrected both issues; [offline tests Run 38026502365](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026502365) passed 24 checks. **These fixes still require independent code-gate approval before another bounded sample.**

The alternative FII/DII sources so far provide only recent rows (164 GitHub mirror rows and 16 ChartDrift page rows); 500+ historical sessions remain unestablished. Continue free-source research before declaring that data unavailable. No full-history download, feature table, labels or model fit has occurred.


### Corrected Gate A code gate — PASS, sample artifact still pending (2026-10-10)

The independent tester passed the corrected exact eight-file sampler/workflow snapshot for **one bounded Gate A retry only**. [Offline Run 38026629021](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026629021) passed 25 checks (7 v1 + 18 v2). [Fail-closed Run 38026802711](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026802711) confirmed the revoked authorization is rejected and source sampling is skipped.

**Important:** the previous source artifact (`11660395594`) remains rejected, and the source approval is still revoked. A new manifest must bind the current tester report hash and all eight protected files before another sample can run.

The free-source search has been broadened and documented in [Extension 2 FII/DII source discovery](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md). Leads include the official NSE/SEBI pages, several GitHub histories and public dashboards. Claims of 800 records or 14 years remain unverified; no new full-history file was fetched. Full-history acquisition and model fitting remain unauthorized.


### Corrected Gate A artifact audit — schema pass, flow coverage still open (2026-10-10)

The corrected bounded run [38026993369](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026993369) completed and uploaded artifact `11661065266` (ZIP SHA-256 `10a3fba40359c230bafa0f47c2d01be8f057e39b5eed0b70335710b59c57558a`). The independent tester verified the index date parser, expected sector identities, cash-equity schemas and legacy/UDiFF F&O sample schemas.

However, historical FII/DII coverage remains insufficient: the available rolling source sample has 164 unique dates (2026-01-14 to 2026-09-30), and NSE's dated API request returned current 2026 rows that were correctly rejected as outside the requested July 2024 window. Sampled public pages did not establish a 500+ session daily series. Therefore the tester's [Run 2 artifact report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_GATE_A_RUN2_ARTIFACT_TESTER.md) requests changes for closing Gate A, while accepting the source-schema checks as valid bounded evidence.

The one-run sample manifest is marked SPENT. New free sources—GitHub daily JSON, range-query dashboards and historical-file claims—are inventoried in [EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md). A separate bounded source-discovery proposal and tester gate are next. Full history, feature/label generation and model fitting remain unauthorized.


### Further free-source research — new leads, no new approved samples (2026-10-10)

The free-source inventory now includes [CDSL's dated FPI reports](https://www.cdslindia.com/Publications/ForeignPortInvestor.html), [SEBI's monthly trade-wise FPI equity archive](https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html), and Hugging Face dataset [johnwick3690/stocks](https://huggingface.co/datasets/johnwick3690/stocks), whose public commit diff lists a 503-line `fii_dii_2024_to_today.csv` lead. These are not accepted data yet: the HF file needs a bounded header/tail/date/coverage check, CDSL is FPI-only, and SEBI transaction-level FPI data must not be silently substituted for aggregate FII/FPI/DII flow.

**Provenance correction:** the MrChartist repo's `scripts/seed_history.js` explicitly generates "realistic per-day" values from monthly/yearly totals. Those seeded values are synthetic and must not be used as observed daily data. A full public `data/history.json` file (143,498 bytes) was inadvertently retrieved during repository review; it was not committed to the project data or used for analysis, and the incident is disclosed in [ERROR_LOG.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/ERROR_LOG.md).

The previous Gate A manifest is spent. No further data probes are authorized until a new narrowly bounded source-discovery spec, offline regressions, and isolated tester review pass. The detailed [free-source inventory](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md) lists the scope and limitations.


### Extension 2 Source Discovery 3 — specification passed (2026-10-10)

The independent tester passed the new bounded free-source proposal for **implementation and offline tests only**. No additional source requests are authorized yet. The spec pins the CDSL historical FPI samples, a single Hugging Face CSV head/tail probe at an immutable commit, a single-date static JSON sample and metadata-only page/repository checks. It has a 2 MiB global byte cap, 15 initial requests plus at most three one-hop HF redirects, strict HTTP 206/Content-Range handling, no full-file fallback, and excludes synthetic/seeded data.

See the [specification](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md) and [independent tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md). The previous Gate A manifest is spent. The next gate is offline implementation/tests followed by an exact-snapshot code review; a separate manifest will be required before any live source probe.

During specification link verification, the web reader could not parse the two CDSL XLS links and returned no data values. This is recorded as non-accepted activity, not as source-coverage evidence. Full-history acquisition and model fitting remain unauthorized.


### Extension 2 free daily-flow source discovery 3 — code gate pending (2026-10-10)

The finite source-discovery implementation is now in place, and its latest hosted offline suite [Run 38028738968](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38028738968) passed **27/27 checks**. The exact current code/workflow snapshot is submitted for isolated tester review in [PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md).

The sampler uses fixed CDSL, Hugging Face, one-date public JSON, page and directory-metadata probes only. It enforces shared request/byte caps, strict HTTP 206/Content-Range checks, URL/host/range allowlists, no credential forwarding, synthetic/provenance rejection, and safe metadata-only GitHub directory parsing. The live workflow consumes the single-use manifest before source access; the offline workflow invokes only fixtures.

**No live source probes have been made by this implementation.** The previous Gate A manifest is spent; this work requires a separate code-gate PASS and then a new one-run manifest. Even after the sample, the artifact must pass its own independent audit. Full-history acquisition, features/labels, model fitting, metrics/p-values and final-holdout access remain unauthorized.


### Discovery 3 code handoff refreshed — 2026-10-10

The source-discovery code has been tightened again and the current hosted offline suite [Run 38029034365](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029034365) passed **29/29 checks** on commit `918821ba9e74342bb282fe3a86138e8aa8e29ea7`. The CDSL probe now reports candidate same-column numeric buy/sell/net values from the bounded equity-row sample, but explicitly does not accept them as model features before grouped-header reconciliation. The public JSON probe recursively removes credential-like fields and redacts sensitive URL query values.

The [current code-gate review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md) pins the exact six protected file Git blobs and byte SHA-256 hashes. **No live source requests have been made.** The spec-only PASS is not a code gate. A fresh isolated tester code PASS and a separate one-run manifest are required; even after the sample, its artifact must receive an independent audit. Full-history acquisition and model fitting remain unauthorized.


### Discovery 3 code-gate resubmission — 2026-10-10

The tester returned REQUEST CHANGES on the prior code snapshot. The developer corrected six items: current spec provenance, conflicting/malformed dates, non-finite CSV values, nested signature redaction, dated-link URL redaction, and exact reviewed-commit/tree binding in the guarded workflow. The newest hosted offline test [Run 38029615734](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029615734) passed **32/32 checks**.

The exact corrected snapshot commit is `1706a17d268e2b139fc9dba4504f498acc4f5de0`. See the refreshed [code review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md). No live source calls or new source manifest exist. The independent tester must pass this exact code/workflow snapshot before a new single-use manifest can be prepared, and any resulting artifact must pass a separate audit. Full-history acquisition, feature/label generation and model fitting remain blocked.


### Corrected Gate A resample and FII/DII coverage status — 2026-10-10

The corrected bounded resample [Run 38026993369](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026993369) passed the official index date checks for both 2024-07-05 and 2024-07-08; F&O and cash-equity samples also passed. The NSE date-parameter FII/DII endpoint still returned 2026-10-09 rows for a July 2024 request, but the corrected parser now rejects those out-of-window rows.

The available public GitHub FII/DII mirror contains only 164 unique dates from 2026-01-14 through 2026-09-30. Current endpoint/page samples do not establish the 500+ aligned historical sessions needed for the registered confirmatory research. **Historical FII/DII availability remains unresolved; do not treat the source gate as complete.**

The previous one-run manifest is spent. The next step is a separate bounded free-source discovery gate described in [PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md). Its offline tests passed 32/32 in [Run 38029615734](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029615734), but independent tester code review is pending. No live discovery requests, full-history download or model fitting may occur until that gate and its new single-run manifest pass.


### Extension 2 Free Flow Source Discovery 3 — code gate only (2026-10-10)

The current bounded source-discovery code has passed a fresh independent code/workflow review, limited to the implementation and its offline safeguards. [Offline workflow Run 38029797600](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029797600) passed all 32 fixture regressions. The tester report is available on the [tester branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md).

**This does not authorize a live source probe.** The platform blocked mirroring the exact tester report to the developer branch, so no single-use manifest has been created. No live source requests or model fitting occurred. Next steps are to complete an allowed exact report mirror, compute byte-level SHA-256 values for the six protected files, and only then create a separate single-use manifest. Full-history acquisition, features/labels, model fitting, metrics/p-values and final-holdout access remain prohibited.
