## Tester review cadence update — 2026-10-13

- Per the latest user instruction, **independent review is deferred until the full planned results bundle is acquired, frozen and indexed**. Do not conduct tester reviews for each development step or intermediate commit.
- The tester workflow is dormant until `research/gates/PREDICTION_RESULTS_ACQUIRED_REVIEW_REQUEST.json` is committed with `results_acquired: true`, a pinned developer commit, and a result-bundle manifest with artifact SHA-256 hashes. The manual run button is for that same post-acquisition event only.
- Earlier R2 `REQUEST CHANGES` artifacts remain historical evidence. T2/T3 source findings were addressed on the developer branch; they are not an instruction to perform repeated step-by-step reviews under the new policy.
- [Cadence policy](research/governance/TESTER_REVIEW_CADENCE_POLICY_2026-10-13.md) · [Tester workflow](.github/workflows/phase-08p-independent-registry-review.yml).

---

## Phase 8P R2 tester continuation — 2026-10-13

- Developer submitted T2 bootstrap and T3 target-scope corrections. Source inspection indicates the bootstrap now withholds inferential output for a single-valued resampling distribution; R2 is explicitly a non-empirical two-target pilot.
- The tester audit script has been updated to test the corrected bootstrap contract and to treat the omitted eight horizons as a scoped note only when the non-empirical hard gate is present.
- **Decision remains REQUEST CHANGES** until the hosted regression and complete shard/config/semantic audit artifact can be reviewed. No data, model, or holdout work is authorized.
- [Tester continuation report](research/gates/PREDICTION_REGISTRY_R2_INDEPENDENT_AUDIT_CONTINUATION_2026-10-13.md) · [R3 tester decision](research/gates/PREDICTION_REGISTRY_V2_R2_INDEPENDENT_TESTER_DECISION_R3_2026-10-13.json).

---

## Latest Phase 8P R2 prediction-registry tester decision — 2026-10-13

- **Decision: REQUEST CHANGES.** Empirical fitting, encrypted-data access, holdout access, option P&L and strategy promotion remain prohibited.
- Blocking finding T2: the moving-block bootstrap can report a zero-width confidence interval and minimum p-value when its resampling support has no variation.
- Scope finding T3: the R2 manifest contains only the 30-minute intraday and +1-session positional labels, not the full frozen horizon set.
- [Independent tester report](research/gates/PREDICTION_REGISTRY_V2_R2_INDEPENDENT_TESTER_REVIEW_R3_2026-10-13.md) · [Machine decision](research/gates/PREDICTION_REGISTRY_V2_R2_INDEPENDENT_TESTER_DECISION_R3_2026-10-13.json).
- [Tester-owned read-only audit script](scripts/independent_prediction_registry_audit_r2.py) · [Workflow](.github/workflows/phase-08p-independent-registry-review.yml). Full reconstruction and configuration-shard audit remain pending an observed hosted result.

---
## Latest Phase 8P checkpoint — 2026-10-12

- **Duplicate-diagnostic code gate:** PASS FOR CODE ONLY on exact developer commit `aae250d8a34989ebe0bd901e1d6b7d9aa0ec5a5f`; independent tester workflow [#38204532045](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204532045) passed 19/19 checks.
- [Tester report](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_R1_2026-10-12.md) · [Machine decision](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_DECISION_R1_2026-10-12.json) · [Developer R3 request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-developer/research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_REQUEST_R3_2026-10-12.json).
- Previous tester workflow failures [#38204120560](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204120560) and [#38204512622](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38204512622) are preserved as infrastructure non-evidence; both defects were corrected on this isolated tester branch.
- **Real artifact scan remains blocked pending a separate one-use authorization.** No actual duplicate counts/classifications were generated, no raw/decrypted data was uploaded, no records were removed, and no model, holdout, option P&L or strategy work was executed.
- Current [status](research/STATUS.md), [error log](research/ERROR_LOG.md) and [chat log](research/logs/CHAT_LOG.md).

**Tester → Developer:** preserve the tester branch role and submit a separate pinned diagnostic-only authorization request. Do not scan the real artifact or fit models before the next independent gate passes.

---

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


## Phase 8P duplicate diagnostic checkpoint — 2026-10-12

- **R4 duplicate-diagnostic code gate:** **PASS FOR CODE ONLY** for developer commit `8f8d513330d1cb064b4d3ffe9933f8e8014f2850`. Independent tester run [#38205506563](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205506563) passed 29/29 checks.
- Tester receipt artifact [11726624314](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38205506563/artifacts/11726624314), ZIP SHA-256 `464d9bffb484210a3aac1e821b78828b5016394afbf07740cd1fc0e566591bac`.
- [R4 tester report](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_R4_2026-10-12.md) · [Machine decision](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_TESTER_DECISION_R4_2026-10-12.json) · [Developer request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-prediction-developer/research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW_REQUEST_R4_2026-10-12.json).
- This approval covers code and synthetic fixtures only. **No real artifact scan/decryption occurred; no empirical duplicate report or model result exists.**
- Historical tester orchestration failures #38205280084, #38205378764 and #38205429386 are preserved as non-evidence and documented in [the error log](research/ERROR_LOG.md) and [chat log](research/logs/CHAT_LOG.md).
- **Next gate:** separate one-use execution workflow and authorization-request review. No real data scan, revised preflight, empirical model fit, holdout metric, option P&L or strategy promotion before that independent gate passes.

**Tester → Developer:** preserve the exact R4 code-only PASS and submit the pinned one-use executor workflow/request.
**Developer → Tester:** independently verify the new executor before it can retrieve or decrypt the source artifact.



## One-use duplicate diagnostic executor — workflow-only tester PASS (2026-10-12)

- **Decision:** `PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY`, tester run [#38206319754](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206319754), **31/31 checks passed**.
- [Tester report](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_TESTER_R1_2026-10-12.md) · [Machine decision](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_TESTER_DECISION_R1_2026-10-12.json).
- Receipt [11727591616](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38206319754/artifacts/11727591616), ZIP SHA-256 `3009787cfb7abf9f04ca2abf695d1ffabbd9c77e26e2fe0b9303beda48f56d11`.
- The approval covers only the exact executor workflow/request, not execution. Safe no-op runs #38205955895 and #38206043280 skipped cache restore/download; request-contract failures #38205997072/#38206009396 remain in the logs.
- **Real artifact scan/decryption remains BLOCKED.** A distinct max-use-1, time-limited execution authorization must receive separate independent tester approval before the executor consumes its nonce or fetches the pinned ZIP.
- See [current status](research/STATUS.md), [error log](research/ERROR_LOG.md) and [chat log](research/logs/CHAT_LOG.md).

**Tester → Developer:** submit the one-use execution-authorization request, retaining all false flags for deduplication, model fit, holdout, external-source requests, data upload, option P&L and strategy promotion.
**Developer → Tester:** independently review the request and only issue a one-use execution authorization if all exact pins and fail-closed safeguards are satisfied.



## Phase 8P — one-use duplicate diagnostic (2026-10-12)

- Independent code gate R4: PASS 29/29. Independent executor workflow R2: PASS 33/33.
- Final one-use tester authorization was issued for nonce `PHASE8P_DUP_DIAG_EXEC_20261012_R1_8F8D5133`, tied to the exact code/workflow/request/artifact pins. [Authorization report](research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTION_AUTHORIZATION_TESTER_R1_2026-10-12.md).
- Developer run [#38207005953](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38207005953) passed the gate, committed its nonce before source access and verified the encrypted ZIP digest. The real aggregate scan is running; no output accepted yet.
- **No records dropped; no prediction model, holdout, P&L or strategy was tested.** An independent data-result gate is mandatory after the aggregate report.

**Tester → Developer:** preserve one-use nonce and await the pinned report.
**Developer → Tester:** submit report/hash for independent data-gate review before any next experiment.



## Phase 8P real-data duplicate diagnostic — no result (2026-10-12)

- [Run #38207005953](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38207005953) passed authorization and source digest verification but ended with runner-shutdown exit code 143 during the aggregate scan.
- **No aggregate report was produced.** Duplicate counts remain unknown; this is not a market-data finding or strategy result.
- The R1 nonce is consumed. A fresh pinned executor/request and separate tester-created one-use authorization are required before a new scan. Prediction, holdout, P&L and strategy gates remain blocked.

**Tester → Developer:** preserve R1, submit a new exact-snapshot executor and nonce; await independent review.
**Developer → Tester:** do not reuse R1 and do not permit strategy testing without an accepted data gate.

