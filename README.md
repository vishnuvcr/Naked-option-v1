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
- **Phase 7 Run #925 is NON-ACCEPTED EVIDENCE; the independent tester issued REQUEST CHANGES.** The tester confirmed row-level source alignment but identified four protocol mismatches: P10 abstention was omitted, missing volatility/trend rows entered the low/low regime, P05/P06 block diagnostics ignored abstention masks, and family-bootstrap non-evaluable rows were set to zero. Phase 7 and Phase 8 remain blocked. See [Run #925 tester report](research/gates/PHASE7_RUN925_EMPIRICAL_TESTER.md), [Phase status](research/STATUS.md), and [Error log](research/ERROR_LOG.md).
- Developer fixed the four reported implementation defects and added tests, but tester review [PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md](research/gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md) returned REQUEST CHANGES on the correction-specific workflow gate: the approval must be bound to the exact protected-code snapshot so later changes cannot reuse a stale PASS. No new empirical run is authorized.

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
- [Phase 7 Run #925 empirical tester report](research/gates/PHASE7_RUN925_EMPIRICAL_TESTER.md)
- [Phase 7 correction authorization review](research/gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md)
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

## Phase 7 workflow correction — 2026-10-08

- Run #600 (`37716619573`) was **NON-EVIDENCE**: the Phase 7 regression job failed before tests because `requirements.txt` does not exist.
- Tester gate [PHASE7_RUN600_WORKFLOW_FAILURE_TESTER.md](research/gates/PHASE7_RUN600_WORKFLOW_FAILURE_TESTER.md) = **REQUEST CHANGES**.
- Workflow correction now follows the established explicit dependency installation and cached canonical data acquisition used by Phase 6.

## Phase 7 workflow correction gate — 2026-10-08

- Tester correction gate PHASE7_RUN600_WORKFLOW_CORRECTION_APPROVAL_TESTER.md = **PASS**.
- Fresh Phase 7 hosted execution is authorized. Run #600 remains non-evidence.

## Phase 7 Run #628 horizon correction — 2026-10-08

- Tester gate [PHASE7_RUN628_HORIZON_APPROVAL_TESTER.md](research/gates/PHASE7_RUN628_HORIZON_APPROVAL_TESTER.md) = **PASS**.
- Fresh hosted regression is authorized; Run #628 remains non-evidence.

## Phase 7 Run #637 — 2026-10-08

- Run #637 (`37719955436`) is **NON-EVIDENCE**: regression passed, but empirical execution again hit `KeyError: ('2','E01')` because the current branch still used `H=horizons[0]`.
- The issue is branch-lineage preservation, not a new scientific method problem.
- The exact tester-approved horizon correction is being reapplied on the current branch.

## Phase 7 Run #637 horizon reapplication — 2026-10-08

- Tester gate [PHASE7_RUN637_HORIZON_REAPPROVAL_TESTER.md](research/gates/PHASE7_RUN637_HORIZON_REAPPROVAL_TESTER.md) = **PASS**.
- Current branch now preserves the horizon-capture correction and direct multi-horizon regression.
- Fresh Phase 7 execution is authorized; Run #637 remains non-evidence.

## Phase 7 Run #645 closure fix — 2026-10-08

- Tester gate [PHASE7_RUN645_CLOSURE_APPROVAL_TESTER.md](research/gates/PHASE7_RUN645_CLOSURE_APPROVAL_TESTER.md) = **PASS**.
- Current branch contains the approved explicit current-horizon closure fix and direct multi-horizon regression.
- Fresh gated regression is authorized.

## Phase 7 Run #650 correction cycle — 2026-10-08
- Run #650 artifact is non-final evidence. Tester found a bootstrap construction mismatch and regime diagnostic block-count mismatch.
- Frozen correction amendment is approved; developer is implementing before fresh execution.


## Phase 7 Run #654 checkpoint — 2026-10-08

- **Hosted run:** #654 (`37763242007`) completed successfully through protocol, regression, empirical execution, validation and artifact upload.
- **Artifact:** `phase7-ensemble-results` (ID `11551679532`).
- **Artifact SHA-256:** `c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`.
- **Tester gate:** [PHASE7_RUN654_EMPIRICAL_TESTER.md](research/gates/PHASE7_RUN654_EMPIRICAL_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS**.
- **Coverage:** 100/100 frozen P01-P10 layer/horizon cells executed.
- **Statistical result:** no family-level Brier data-snooping test is significant at 5%; no Phase 7 candidate is promoted.
- **Correction status:** Run #650 bootstrap/diagnostic defects are closed by the corrected implementation and independent artifact audit.
- **Carry-forward restrictions:** abstention chronological diagnostics are full-series rather than trade-only; intraday P08-P10 regime inputs use the fixed one-minute causal return path sampled at hourly decision rows. These must remain fixed and are to be documented in Phase 8.
- **Next phase:** Phase 8 long-option execution research, with Paytm Money brokerage/fees, exchange/statutory charges, spread, slippage, latency and premium-decay realism. Phase 9 robustness and Phase 10 fresh-forward validation remain mandatory.


## Latest Phase 7 checkpoint — 2026-10-08

- Run #654 (`37763242007`) completed protocol, regression, empirical execution, validation and artifact upload.
- Artifact `phase7-ensemble-results`, ID `11551679532`, digest `c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`.
- Independent tester gate [PHASE7_RUN654_FINAL_TESTER_GATE.md](research/gates/PHASE7_RUN654_FINAL_TESTER_GATE.md) = **PASS WITH SCOPED RESTRICTIONS**.
- All 100 P01-P10 layer/horizon cells executed and independently reconciled.
- No family-level test reached alpha=0.05; no Phase 7 candidate is promoted.
- **Next phase:** Phase 8 long-option execution translation with realistic Paytm Money brokerage/charges, exchange/statutory costs, bid/ask spread, slippage, latency and premium decay. The final untouched holdout remains sealed.


## Phase 7 reference artifact status — 2026-10-09

- A same-run reference-artifact writer now emits 10 horizon panels containing P01-P10 forecasts, labels, future returns, timestamps and chronological block IDs, plus source/code/runtime fingerprints. The scientific method and existing metric calls are unchanged.
- Tester code gate: [PHASE7_REFERENCE_ARTIFACT_CODE_TESTER.md](research/gates/PHASE7_REFERENCE_ARTIFACT_CODE_TESTER.md) = PASS WITH SCOPED RESTRICTIONS.
- Hosted regression runs #835/#837/#838 failed only in the new manifest-test fixture because a temporary JSON path was outside the repository root. The fixture correction is commit `14d20380632e365b2a0b6b63afe58f2775375950`; fresh hosted verification is still pending.
- Runs #831 and the failed fixture runs are non-evidence for the new reference artifact. No Phase 7 metric is promoted and Phase 8 empirical option execution remains blocked.
- Follow the [research status](research/STATUS.md), [error log](research/ERROR_LOG.md), [research log](research/logs/RESEARCH_LOG.md) and [chat log](research/logs/CHAT_LOG.md) for gate history.

## Phase 7 reference artifact regression — 2026-10-09

- Fresh [Run #852](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37912587739) passed both the existing Phase 7 regression suite and the new row-level reference-artifact regression. The tester authorization gate also passed.
- Tester report: [PHASE7_REFERENCE_ARTIFACT_REGRESSION_TESTER.md](research/gates/PHASE7_REFERENCE_ARTIFACT_REGRESSION_TESTER.md) = PASS for regression only.
- The empirical job is still in progress. The new artifact and metrics remain unaccepted until a separate post-run audit validates all panels, hashes and aggregate reconciliation. Run #654 remains immutable; Phase 8 manifest amendment and option-grid execution remain blocked.

### 2026-10-09 Phase 7 artifact checkpoint

Runs [#852](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37912587739), [#924](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37914896724), and [#925](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37914905848) remain reported as in progress at the latest reconciliation. Their empirical jobs have not completed and no artifact is available to audit. Run #852 metadata is stale and live logs for active jobs are temporarily unavailable; neither condition is treated as evidence of success or failure. The bootstrap sampler optimization passed its equivalence regression and scoped tester review, but the real-data reference artifact gate remains open. **Phase 8 stays blocked; no strategy is promoted.** See [live phase status](research/STATUS.md) and [error log](research/ERROR_LOG.md).


## Latest Phase 7 checkpoint — 2026-10-09

- Runs #852, #924 and #925 completed with immutable artifacts. Run #925 source commit: `682eadf2a9eb4de250bc3db27d02e57f88687fa1`.
- The independent tester's audit [Run #943](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935031119) reported 2,775 passing checks and 323 failed checks grouped into four implementation defects.
- Required fixes: implement the P10 [0.45, 0.55] abstention consistently; exclude rows lacking finite volatility/trend from regime state counts; align P05/P06 block metrics with their abstention masks; and treat non-evaluable family-bootstrap rows as missing, not zero differential.
- Gate: [PHASE7_RUN925_EMPIRICAL_TESTER.md](research/gates/PHASE7_RUN925_EMPIRICAL_TESTER.md) = **REQUEST CHANGES**.
- Run #925 is not accepted evidence; no candidate or trading strategy is selected. Phase 8 remains blocked until a corrected Phase 7 code gate and fresh empirical artifact pass independent review.


## Latest Phase 7 correction checkpoint — 2026-10-09

- Developer correction source/test/validator commits are in the Phase 7 developer branch; hosted [Run #964](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37936076338) passed protocol/regression/reference-panel regression, with empirical execution skipped.
- Tester confirmed the four Run #925 corrections but issued **REQUEST CHANGES** because the approval mechanism does not bind the PASS to a specific reviewed source/workflow/protocol snapshot.
- Required next step: add exact commit/file-hash binding and positive/negative checks for manual and automatic authorization before resubmitting to tester.
- Runs `37935752265` and `37935794939` remain **NON-EVIDENCE**; any resulting metrics must not be accepted.
- No Phase 7 candidate or trading strategy is promoted. Phase 8 is blocked.


## Phase 7 correction approval hardening — 2026-10-09

- Snapshot-bound approval validator added at `scripts/validate_phase7_correction_approval.py`; positive/negative tests at `scripts/test_phase7_correction_approval.py`.
- Both the automatic protocol caller and manual/reusable Phase 7 workflow now fail closed unless the tester branch contains a matching report and JSON manifest for the exact reviewed commit and protected-file SHA-256 set.
- Hosted [Run #981](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37938077088) passed protocol and all Phase 7 regression suites; empirical execution was skipped because independent tester approval has not yet been issued.
- Developer snapshot submitted for independent review: `b9fc7c9e7c77efb5149d35e31509251f701122ce`. Phase 7 remains blocked pending tester review; Phase 8 is not authorized.


## Latest checkpoint — 2026-10-09, Phase 7 approval-test repair

- Research Protocol Check [#989](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37953177951) failed in a correction-approval regression assertion after protocol and the standard Phase 7 regression passed. Empirical execution did not run.
- Root cause: the test compared a bare filename against a tuple containing full repository-relative paths. Developer corrected the assertion to the exact protected path; this is a test-only change, not a scientific-method change.
- [Error log](research/ERROR_LOG.md) and [detailed research log](research/logs/RESEARCH_LOG.md) preserve the incident. Run #989 remains non-evidence; no metric or strategy is promoted. Phase 7 awaits a fresh hosted regression and independent tester review; Phase 8 remains blocked.


## Latest checkpoint — 2026-10-09: snapshot approval corrected

- Research Protocol Check [#990](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37953853119) passed the regression suites after the path-assertion fix.
- The first approval mirror, [Run #992](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957038797), correctly failed closed before empirical execution because the tester report line/scope format, report digest and one protected-file hash did not all match. Run #992 is non-evidence.
- The independent tester corrected the report and JSON manifest on `phase-07-tester`; developer is mirroring those exact blobs. See [Phase 7 correction tester gate](research/gates/PHASE7_RUN925_CORRECTION_CODE_TESTER.md), [snapshot manifest](research/gates/PHASE7_RUN925_CORRECTION_APPROVAL.json), and [error log](research/ERROR_LOG.md).
- State: waiting for the fresh hosted validator to confirm the exact snapshot. No new metric is accepted, no strategy promoted, and Phase 8 stays blocked pending the fresh empirical artifact's separate audit.


## Latest checkpoint — 2026-10-09: Phase 7 fresh empirical run in progress

- The exact snapshot approval was corrected and independently archived on `phase-07-tester`; the same report/manifest blobs are now on `phase-07-developer`.
- [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656) passed protocol, all Phase 7 regression suites and the tester-authorization job. The hosted validator confirmed report/manifest byte identity, reviewed-commit ancestry and all 25 protected-file hashes.
- One fresh Phase 7 empirical job is in progress; no new metric is accepted until artifact validation and a separate independent tester audit finish.
- The tester branch’s [Run #993](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957295201) repeated the prior Run #925 rejection (2,775 pass checks / 323 fails); Run #925 remains non-evidence. Phase 8 remains blocked pending Run #994’s artifact gate. See [status](research/STATUS.md), [research log](research/logs/RESEARCH_LOG.md) and [error log](research/ERROR_LOG.md).


## Run #994 runtime checkpoint — 2026-10-09

- [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656) passed the snapshot-authorization gate and is executing the empirical Phase 7 script. No output artifact has been uploaded yet.
- GitHub's live-log endpoint returns `BlobNotFound` while active; this is recorded as an observability limitation, not a scientific result.
- The prior completed Run #925 script took about 1h 53m, so Run #994 remains inside the earlier observed duration. No duplicate execution was launched. See [status](research/STATUS.md), [research log](research/logs/RESEARCH_LOG.md), and [error log](research/ERROR_LOG.md).

## Phase 8 cost-source preflight — 2026-10-09 (preliminary only)

While Run #994 is active, an official-source check was made for the eventual option-economics gate; Phase 8 has **not** started. The current Paytm Money F&O FAQ says ₹10 per unique executed order, but Paytm also documents account-cohort-specific historical tariffs. Do not assume the research account's exact tariff: test ₹10/₹15/₹20 per executed order until verified against its tariff/contract notes. NSE's 2026 schedule lists ₹3,553 per crore of option premium per side from 1 March 2026 and STT of 0.15% on option sale premium / 0.15% of intrinsic value on exercise from 1 April 2026. The final model must still include all other applicable levies/GST, spread, slippage, latency, and premium decay.

Sources: [Paytm Money F&O FAQ](https://www.paytmmoney.com/stocks/customer/fno-faq/onboarding-and-kyc/account-segment-activation/how-to-activate-fo-from-mobile-app-web), [Paytm Money pricing](https://www.paytmmoney.com/stocks/pricing), [Paytm brokerage-plan notice](https://www.paytmmoney.com/blog/brokerage-charges-increase-from-25th-aug-23-existing-users-will-continue-on-old-brokerage-charges/), [NSE transaction-charge circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf), [NSE STT schedule](https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax), [NSE levies schedule](https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies). This is only a source preflight, not an approved cost model or backtest result.


## 2026-10-09 — Additional pre-gate free-source discovery for Phase 8 (no phase transition)

A read-only source search was run while Phase 7 Run #994 remains the sole active empirical target. These are **candidate leads, not accepted research data**, and this search does not open Phase 8 or alter its frozen method.

- **Hugging Face — rissin/nse-options-intraday:** dataset card reports about 258.9 million rows/2.5 GB, daily EOD data attributed to NSE bhavcopy (2001 onward) plus Upstox one-minute candles from Oct 2024 onward; intraday open interest is missing and no bid/ask columns are described. The dataset license is listed as “other”, so provenance/terms must be reviewed before integration: https://huggingface.co/datasets/rissin/nse-options-intraday
- **Kaggle candidate:** a public GitHub issue describes a 6.8 GB one-minute NIFTY option dataset with 77 expiries, coverage ending 24-Mar-2026, OHLC/OI/volume and computed Greeks, but only ten trading days around each expiry. The issue says CC-BY-NC-SA 4.0; this is a third-party report, not a verified Kaggle metadata record. Confirm the canonical dataset card, exact license, partition completeness and any expiry/strike selection bias before use: https://github.com/Tanishpd/Indian-options-trading-algorithm/issues/13
- **Zenodo — Nifty spot/futures/options one-minute 2017–2020:** publicly discoverable archive, about 320.9 MB, documented OHLC/volume contract files. Useful as a historical overlap candidate; the current description does not establish bid/ask or complete OI coverage: https://zenodo.org/records/10899828
- **Other GitHub leads:** i9-tradebot/NIFTY_Options_Historical_Data_Collector requires a Zerodha account/enctoken and collects data via API rather than serving a ready free archive: https://github.com/i9-tradebot/NIFTY_Options_Historical_Data_Collector. mukhilj/breeze_options_pipeline requires an ICICI Direct Breeze API account: https://github.com/mukhilj/breeze_options_pipeline. QuantDev-stack/OptionVault exposes sample files but describes full bulk access as licensed rather than an unrestricted free download: https://github.com/QuantDev-stack/OptionVault.
- **Implication:** broaden the Phase 8 free-source audit beyond its current NSE/BSE probes, two GitHub API probes and selected Hugging Face data. Verify each candidate's license/provenance, full-chain coverage, dates, expiry/strike omissions, schema, cacheable file hashes and official NSE overlaps. Treat OHLC-only sources as Q1 proxy inputs, never quote-executable Q2 data; a displayed bar close is not a bid/ask quote.
- No candidate dataset was downloaded, merged or accepted in this step. Any source addition or change to the frozen Phase 8 workflow/spec must be submitted through the separate tester branch after Phase 7's fresh artifact passes its independent gate.


## 2026-10-09 — Free-source preview quality caveat

The current Hugging Face dataset viewer for rissin/nse-options-intraday shows legacy daily option rows dated 2005-06-10 with open/high/low/close, volume, open interest and settlement values all equal to zero for sample contracts. These may be placeholders for contracts with no eligible trade/quote, not valid executable observations. Do not silently forward-fill, impute or assign positive execution value to these rows. Validate zero/missing values by source and contract, retain explicit status/reason fields, and exclude invalid/non-positive premium rows from executable P&L while keeping them in coverage diagnostics. The dataset's license field is “other”, its provenance/redistribution terms need review, and it does not describe bid/ask data. Source: https://huggingface.co/datasets/rissin/nse-options-intraday

This confirms the source remains a candidate only. No source was imported and no Phase 8 gate was opened.
