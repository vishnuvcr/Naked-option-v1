# Research Status


## Current checkpoint — 2026-10-10, one-use Dhan sample acquired; official primary-source cross-check is next

| Workstream | Current state | Evidence / next gate |
|---|---|---|
| Existing daily global/peer prediction extension (Run #44) | COMPLETED — NO CANDIDATE PROMOTED | [Run #44](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915); all five horizon-family tests non-significant; holdout sealed |
| Dhan historical-data recovery plan | PASS WITH SCOPED RESTRICTIONS — plan gate only | [Developer plan](phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md); [independent planning report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_DHAN_HISTORICAL_DATA_RECOVERY_PLAN_TESTER.md) |
| Dhan historical pipeline implementation | PASS WITH SCOPED RESTRICTIONS — offline code only | [Independent code PASS](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_DHAN_HISTORICAL_DATA_RECOVERY_CODE_FINAL_TESTER.md); exact reviewed hashes remain recorded in the handoff |
| One-use Dhan sample acquisition | COMPLETED — exactly one request, approval SPENT | [Guarded run 38055202149](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38055202149); HTTP 200, JSON, 121 response bytes, one request, no retries/redirects; [offline suite 38055202163](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38055202163) passed |
| Sample cache/artifact review | PASS WITH SCOPED RESTRICTIONS — artifact valid; data-model acceptance withheld | [Independent tester artifact report](gates/PHASE7_DHAN_DAILY_SAMPLE_ARTIFACT_TESTER.md), tester blob `be71edaffc364495f2165a12d0fd165462995043`; cache and safe status are committed |
| Official-reference cross-check code | OFFLINE TESTS PASS — strengthened snapshot submitted for tester review | [Run 38058028914](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38058028914): 9 instrument-master, 17 adapter and 9 runner tests; protocol check 38058029128 passed |
| Official NSE / Dhan master source requests | NOT AUTHORIZED — no new manifest/approval exists | The two-source runner has not been connected to a live workflow; the Dhan one-use sample manifest remains SPENT |
| Returned row | Corroborated by independent secondary table; official primary cross-check still pending | NIFTY 50, 2024-01-02: O 21751.35, H 21755.60, L 21555.65, C 21665.80, volume 263711568; timestamp corresponds to 2024-01-02 00:00 Asia/Kolkata |
| Broader historical acquisition / feature engineering / prediction rerun | BLOCKED pending direct official NIFTY OHLC cross-check, instrument mapping validation, new exact-snapshot tester PASS and next acquisition gate | No model or predictor result changed; this one row is not accepted for training/validation |
| Option P&L/strategy optimization (Phase 8) | BLOCKED / OUT OF CURRENT SCOPE | Current user request is prediction research, not option-strategy optimization |
| Final untouched holdout | UNOPENED | Keep sealed until final independent forward-validation gate |

### Dhan sample facts and cache provenance

- Request scope: one POST to `https://api.dhan.co/v2/charts/historical`; `securityId=13`, `exchangeSegment=IDX_I`, `instrument=INDEX`, `fromDate=2024-01-02`, `toDate=2024-01-03` (exclusive), `oi=false`.
- One request / HTTP 200 / `application/json` / 121 bytes / zero retries / zero redirects. Raw response SHA-256: `efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70`.
- Cache bundle: `data/cache/dhan_daily_sample/478f0942f8654bd763b8343a05370f8065ef5041483cb59cc3f7dd6b57ef78ba-efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70/`; raw response blob `215c3b38889b2a143613766ce33f88d954a1ea9a`; manifest blob `601f956e4e31e5a1288a3381fbf59217e37dee10`.
- Safe report: `data/reports/dhan_daily_sample_status.json`, blob `d9729dc4ec07476f9095402ef72d9b331c99bd4e`. Approval `research/gates/DHAN_DAILY_SAMPLE_APPROVAL.json` is `SPENT`; do not reuse it.
- EquityPandit's published table matches all five data fields exactly and reports -0.35% vs prior close; [row at lines 746](https://www.equitypandit.com/share-price/today/nifty-50-historical-data). This is a secondary-source corroboration, not the required official primary-source check.
- Official historical report interface: https://www.niftyindices.com/reports. The official row and exact Dhan instrument-master mapping have not yet been retrieved, therefore the row is not admitted into the research dataset, feature matrix, prediction evaluation or holdout.

### Next gate

The official-reference code/workflow gate has passed with scoped restrictions: [final tester PASS](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_DHAN_SAMPLE_OFFICIAL_REFERENCE_CODE_FINAL_TESTER.md). Current tested suite [Run 38058028914](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38058028914) passed 9 instrument-master, 17 adapter and 9 runner tests; protocol [Run 38058181267](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38058181267) passed. The offline workflow is identical on main and phase-07-developer (blob b450da4b9ffed8d8e38c8f7383084e1ba987b303). Next gate: prepare a fresh exact-hash two-source manifest/approval and guarded workflow; the tester must PASS that separate gate before any public request. No official-source request has been made, the earlier Dhan sample approval remains SPENT, and the sample row remains quarantined from model data. Do not fit models, fetch broader history or open the holdout.

## Previous checkpoint — 2026-10-10, after Phase 7 Run #44

| Workstream | Current state | Evidence / next gate |
|---|---|---|
| Prior Phase 7 ensemble/regime Run #994 | Accepted technical artifact with scoped restrictions; no candidate promoted | [Independent empirical audit](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_RUN_37957677656_EMPIRICAL_TESTER.md) |
| Available-data extension 1 (global/peer daily prices) | **COMPLETED — NO CANDIDATE PROMOTED** | [Run #44](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915); all five horizon-family tests non-significant; [results](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/results/PHASE7_RUN44_AVAILABLE_GLOBAL_PREDICTION_RESULTS.md) |
| Run #44 independent audit | **PASS WITH SCOPED RESTRICTIONS — integrity only** | [Tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md); metrics and all five family p-values independently reproduced |
| Available-data extension 2 (sector, breadth, FII/DII, option OI/volume predictors) | **PROPOSED — TESTER SPEC REVIEW PENDING** | [Frozen proposal](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md); [developer submission](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_DEVELOPER_SUBMISSION.md) |
| Full-history acquisition / empirical fit for extension 2 | **NOT AUTHORIZED** | Wait for independent spec review; if approved, only Gate A small-sample source feasibility may proceed |
| Options strategy / Phase 8 | **BLOCKED / OUT OF CURRENT USER SCOPE** | Do not run option P&L or strategy optimization while user requests prediction research only |
| Final untouched holdout | **UNOPENED** | Keep sealed for later independent forward-validation gate |

### Current prediction-only work

- Extension 1 tested 12 registered daily methods over 5 horizons (60/60 cells), using 11 global/peer series and 1,676 NIFTY daily rows. The 91,988-row panel was independently audited.
- Raw family p-values at 1/2/3/5/10 sessions were 0.9840 / 0.8882 / 0.6786 / 0.7745 / 0.9800; all Bonferroni-adjusted p-values were 1.0. No candidate is promoted.
- The best descriptive Brier leader was G06 Asia composite at five sessions (Brier improvement +0.001623, ROC AUC 0.556), but its family p-value was 0.7745; this is not persuasive predictive evidence.
- Extension 2 is a proposal only. It adds no results and has not changed the frozen Run #44 scope. Official source leads are NSE F&O UDiFF bhavcopy, historical indices/Advances-Declines, and FII/FPI/DII CSV reports. No full history has been downloaded for this extension.
- The final untouched holdout remains unopened.

Developer → Tester: Independently review the exact Extension 2 proposal and issue PASS/REQUEST CHANGES. If the spec passes, authorize only small-sample source-feasibility work, not full history or model fitting.

Tester → Developer: Keep empirical work fail-closed until the spec and each subsequent source/code/empirical gate is independently passed.

---

| Phase | Status | Gate |
|---|---|---|
| Phase 0 Governance/bootstrap | PASSED | tester report archived |
| Phase 1 Literature/method registry | PASSED | final tester gate passed |
| Phase 2 Data engineering/PIT | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived |
| Phase 3 Labels/baselines | PASSED WITH SCOPED RESTRICTIONS | final tester gate archived; B9/B10 blocked |
| Phase 4 Single-family methods | PASSED WITH SCOPED RESTRICTIONS | Family B and Family C tester gates archived |
| Phase 5 Statistical/ML | PASSED WITH SCOPED RESTRICTIONS | Family D Run #23 independently accepted; no model promoted |
| Phase 6 Novel methods | PASSED WITH SCOPED RESTRICTIONS | Run #581 independently accepted; no method promoted |
| Phase 7 Ensemble/regime and prediction-only amendments | **PASS WITH SCOPED RESTRICTIONS; extension 2 pending tester spec gate** | Run #994 accepted; Run #44 cross-market extension audited with no significant candidate |
| Phase 8 Long-option execution | BLOCKED | Not in current prediction-only scope; future Paytm Money/cost/execution gate |
| Phase 9 Robustness/statistics | BLOCKED | CPCV/DSR/PBO gate |
| Phase 10 Fresh-forward | BLOCKED | untouched-forward gate |
| Phase 11 Manuscript/final conclusion | BLOCKED | final tester sign-off |

Last updated: 2026-10-10

## Phase 5 current state

- Frozen protocol tester review passed at `research/gates/PHASE5_PROTOCOL_TESTER.md`.
- Independent tester issued REQUEST CHANGES for the early correction lineage; those submissions are archived under `research/gates/`.
- Protocol amendment for intraday refit cadence was independently passed at `research/gates/PHASE5_PROTOCOL_AMENDMENT_TESTER.md`.
- Intraday Family D now refits once per 20 trading sessions and predicts on the frozen hourly decision grid.
- The previous Family D runs that failed regression or empirical execution are rejected evidence and are not used for selection.
- Hosted Family D run #16 (`37606785909`) is preserved as non-accepted evidence because the frozen D07 wording did not exactly match the calibrated-meta-stack implementation. Tester gate `research/gates/PHASE5_D07_POST_AMENDMENT_TESTER.md` authorized fresh execution. Hosted run #19 (`37611880308`) has passed the mandatory regression gate and is currently executing the empirical D01-D15 suite. No metric is accepted yet.
- Phase 6 remains blocked until the independent tester reviews an immutable Family D artifact and issues a gate decision.

## Research continuity rule

A failed family or model is not a terminal conclusion. The full finite pre-registered universe, option economics, transaction-cost stress, multiple-testing controls and untouched-forward validation must be completed before final synthesis.


## Live verification — 2026-10-07
- Family D hosted run #19 (37611880308): **CANCELLED — NON-EVIDENCE**.
- Active step at cancellation: empirical D01-D15 execution.
- Regression suite: **PASSED**.
- Result schema validation: **SKIPPED**.
- Immutable artifact upload: **SKIPPED**.
- Family D empirical acceptance: **NONE**.
- Phase 6: **BLOCKED** pending independent tester artifact audit.

## Run #20 tester gate
- Run #20 (`37626101730`): workflow success; artifact `phase5-family-d-results` created.
- Independent tester found intraday D13-D15 had n=0 for every registered horizon because 20-observation session-local windows were built on the hourly decision matrix.
- Run #20 is non-evidence. Tester gate `research/gates/PHASE5_RUN20_INTRADAY_SEQUENCE_TESTER.md` requests changes.
- Developer correction maps causal 20-observation representations from the full 1-minute path to the frozen hourly decision rows.
- Tester approved the correction in `research/gates/PHASE5_RUN20_INTRADAY_SEQUENCE_APPROVAL_TESTER.md`.
- A fresh hosted Family D run is required; Phase 6 remains blocked pending artifact audit.


## 2026-10-07 — Family D run #23 final technical gate

- Fresh hosted run #23 (`37642007846`) on developer head `75ed6ddd90ac261364bf52570999d3c308fb37b5` completed successfully.
- Immutable artifact `phase5-family-d-results` / artifact ID `11499450561` was independently downloaded and SHA-256 verified as `27ca6cbc6e1653d40e2d896a81211c97a8d5e70543cf37ad9f402597eee306d8`.
- Independent tester gate `research/gates/PHASE5_FAMILY_D_RUN23_TESTER.md` = **PASS WITH SCOPED RESTRICTIONS**.
- All 150 Family D method/horizon cells executed; numerical reconciliation passed; D07 leakage/isolation checks passed; intraday D13-D15 coverage is restored and non-zero at every registered horizon.
- No Family D model is promoted. Multiple-testing, option economics, transaction costs, robustness and fresh-forward validation remain mandatory.
- Phase 6 remains pending only for independent tester review of the developer's proposed scope.


## 2026-10-07 — Phase 6 implementation gate
- Frozen Phase 6 method specification was approved by the tester.
- Developer implemented E01-E10/I01-I10, added causal/numerical regression tests, and created a gated workflow.
- The empirical workflow job is blocked unless the tester approval file is present on the developer branch.
- No Phase 6 empirical metric has been generated or accepted.


## 2026-10-07 — Phase 6 code gate passed
- Tester code gate `research/gates/PHASE6_CODE_APPROVAL_TESTER.md` archived on developer branch.
- E06 implementation, cutoff-invariance test, E07 exact composite amendment and schema gate passed independent review.
- No empirical result is accepted yet. The next hosted run must pass regression, then the gated empirical job can execute.


## 2026-10-07 — Phase 6 workflow correction checkpoint
- Tester-approved code gate remains scientifically valid, but the first hosted workflow attempt failed before execution because of an invalid GitHub Actions context expression.
- Failed run `37668494609` is non-evidence; no artifact exists.
- Developer replaced the empirical gate with `workflow_call.inputs.empirical_authorized` and caller-side tester-file detection.
- The corrected reusable workflow was also synced to `main` so its manual-dispatch interface is registered on the default branch.
- A fresh tester workflow gate is mandatory before another hosted attempt.


## 2026-10-07 — Phase 6 workflow correction gate passed
- Tester gate `research/gates/PHASE6_WORKFLOW_APPROVAL_TESTER.md` = **PASS — WORKFLOW CORRECTION GATE**.
- Corrected reusable workflow uses typed `workflow_call.inputs.empirical_authorized`; automatic caller derives authorization from archived tester approval.
- The default `main` branch also contains the corrected reusable workflow for manual-dispatch registration.
- A fresh Phase 6 hosted run is now authorized. No metric or artifact is accepted until post-run tester audit.

## 2026-10-08 — Phase 6 run 575 residual-defect checkpoint — tester correction approved
- Fresh hosted Research Protocol Check run `37678088131` / #575 started from developer commit `9b9b7914f82993505ec4f2f0c3aac0b3d6732521` and passed protocol detection, repository contract checks, source acquisition and the Phase 6 regression suite.
- Tester independently inspected the complete Phase 6 implementation before accepting any empirical metric and found a residual invalid `decision_times.iloc[...]` access in the later global-I03 cutoff block.
- Run #575 is therefore treated as **NON-EVIDENCE** regardless of its eventual workflow outcome; no Phase 6 metric/artifact from that run can be accepted.
- Tester gate `research/gates/PHASE6_RUN25_RESIDUAL_CUTOFF_TESTER.md` = **REQUEST CHANGES**.
- Tester approval `research/gates/PHASE6_RUN25_RESIDUAL_CUTOFF_APPROVAL_TESTER.md` = **PASS — correction approved for fresh empirical execution**.
- Corrected detached commit `e27b6358901dc60bc90bad295f46c9493ab63d1e` passed independent cutoff/code review; the developer ref can now advance only to the approved commit that archives this gate.
- Phase 6 remains **BLOCKED for scientific promotion** pending the fresh immutable 200-cell artifact and separate empirical tester gate.

## 2026-10-08 — Phase 6 run 578 regression failure
- Fresh hosted run #578 (`37680279189`) used the tester-approved cutoff correction, passed protocol/source acquisition, but failed the mandatory Phase 6 regression suite before empirical execution.
- Failure: `global_i03_cutoff` fixture expected 11:00 instead of the mathematically correct 11:15.
- Tester gate `research/gates/PHASE6_RUN26_REGRESSION_TESTER.md` = **REQUEST CHANGES**.
- Run #578 is **NON-EVIDENCE**; empirical execution was skipped and no artifact/metric was accepted.
- Phase 6 remains **BLOCKED** until the regression arithmetic is corrected and independently approved.

## 2026-10-08 — Phase 6 run 578 regression correction approved
- Tester gate `research/gates/PHASE6_RUN26_REGRESSION_APPROVAL_TESTER.md` = **PASS — correction approved for fresh empirical execution**.
- Detached correction `1a956f930b11850fb238ea3352565b36a7337395` changes only the expected timestamp in the global-I03 regression fixture from 11:00 to the mathematically correct 11:15.
- Run #578 remains **NON-EVIDENCE**; its empirical job was skipped and no artifact/metric was accepted.
- The developer branch may now advance to the archived approval commit and trigger a fresh gated Phase 6 execution.
- Phase 6 scientific promotion remains blocked until the fresh 200-cell artifact receives a separate independent empirical tester gate.
## 2026-10-08 — Phase 6 Run #581 empirical tester gate
- Fresh hosted run #581 (`37680832842`) completed successfully.
- Immutable artifact `phase6-novel-results`, ID `11513410209`, SHA-256 `2065f7d8025b87f67de1a9f04908ec2fc015a6bda98c5a8162ddad3b01961c24`.
- Complete registered grid: 200 cells = 140 EXECUTED + 60 BLOCKED_DATA; no missing or unexpected cells.
- Independent tester gate `research/gates/PHASE6_RUN581_TESTER.md` = **PASS WITH SCOPED RESTRICTIONS**.
- Technical validity is accepted; no Phase 6 method is promoted to a trading strategy.
- Phase 7 ensemble/regime research is now authorized, subject to a fresh tester gate. Phase 8 option execution, costs, robustness and fresh-forward validation remain mandatory.

## 2026-10-08 — Phase 7 specification gate
- Phase 7 developer specification `research/phase7/PHASE7_METHOD_SPEC.md` is frozen at commit `ae22d242631eb1cf2478ff818d285e458f5e33e6`.
- Tester gate `research/gates/PHASE7_SPEC_APPROVAL_TESTER.md` = **PASS — FROZEN SPECIFICATION**.
- P01-P10 definitions, blocked-predictor handling, exhaustive four-state regime partition, trend formula, trimmed mean, and 20-session expanding walk-forward schedule are now fixed.
- Phase 7 implementation is authorized; empirical execution remains blocked until a separate code gate and hosted regression gate pass.

## 2026-10-08 — Phase 7 regime amendment
- Tester found and resolved an internal P08 cutpoint inconsistency before implementation.
- Commit `5cdb61d38d83bfe16484f181380a60d612fbb9c2` freezes binary low/high volatility and low/high trend states using training-period medians.
- Tester gate `research/gates/PHASE7_SPEC_AMENDMENT_APPROVAL_TESTER.md` = **PASS**.
- Phase 7 implementation remains gated by the separate code review.

## 2026-10-08 — Phase 7 implementation authorization
- Tester-approved Phase 7 frozen specification is archived.
- Tester gate `research/gates/PHASE7_REGIME_CALIBRATION_APPROVAL_TESTER.md` = **PASS** for the causal regime calibration amendment.
- Developer implementation P01-P10 is prepared with the exact frozen rules, including P08/P09 = 0.5*base + 0.5*training regime rate.
- Separate Phase 7 code gate is now required before empirical authorization.

## 2026-10-08 — Phase 7 code correction cycle
- Tester requested changes to the first implementation because family-level data-snooping inference, regime diagnostics, chronological block diagnostics and numerical regression coverage were incomplete.
- Developer added the frozen 500-replication moving-block Brier-loss family bootstrap, four-state regime diagnostics/fallback counts, per-block performance records and deterministic synthetic tests.
- The family inference amendment was independently approved before implementation.
- A fresh Phase 7 code gate is required before empirical execution.

## 2026-10-08 — Phase 7 capture-order correction
- Tester review identified a latent prediction-to-method mapping defect in the first Phase 7 implementation.
- Because six Phase 6 methods are BLOCKED_DATA and therefore skip metric calls, the capture hook could not index against all 20 method names.
- Developer corrected this with explicit CAPTURE_ORDER and added regression coverage.
- No Phase 7 empirical execution occurred with the defective mapping.

## 2026-10-08 — Phase 7 code gate passed
- Tester gate `research/gates/PHASE7_CODE_APPROVAL_TESTER.md` = **PASS WITH SCOPED RESTRICTIONS**.
- Corrected implementation commit `3a883899d4ac32043e6771d677624f1c244ef86c` includes explicit Phase 6 capture ordering, P01-P10, family bootstrap inference, regime diagnostics, chronological block diagnostics and schema validation.
- Before empirical execution, the Phase 7 workflow must be registered on the default branch and the Research Protocol caller must contain the Phase 7 authorization gate.

## 2026-10-08 — Phase 7 workflow gate
- Tester gate `research/gates/PHASE7_WORKFLOW_APPROVAL_TESTER.md` = **PASS — WORKFLOW GATE**.
- Phase 7 reusable workflow and Research Protocol caller were independently reviewed.
- Default-branch registration is the remaining infrastructure action before the manual Run workflow control can be confirmed.
- Empirical execution remains blocked until regression passes after registration.

## 2026-10-08 — Phase 7 Run #600 workflow failure
- Hosted run #600 (`37716619573`) reached the Phase 7 regression job but failed before tests because `requirements.txt` does not exist.
- Run #600 is **NON-EVIDENCE**; empirical execution was skipped.
- Tester gate `research/gates/PHASE7_RUN600_WORKFLOW_FAILURE_TESTER.md` = **REQUEST CHANGES**.
- Developer corrected the workflow to use explicit dependencies and canonical Phase 6 data acquisition/cache steps; tester approval is required before another hosted run.

## 2026-10-08 — Phase 7 Run #600 workflow correction approved
- Tester correction gate PHASE7_RUN600_WORKFLOW_CORRECTION_APPROVAL_TESTER.md = PASS.
- Corrected workflow uses explicit dependencies and canonical cached data acquisition.
- Fresh hosted execution is authorized; Run #600 remains non-evidence.

## 2026-10-08 — Phase 7 Run #628 horizon correction approved
- Tester gate `research/gates/PHASE7_RUN628_HORIZON_APPROVAL_TESTER.md` = **PASS**.
- Production capture now binds each metrics call to the current horizon; deterministic multi-horizon regression coverage was added.
- Fresh hosted regression is authorized. Run #628 remains non-evidence.

## 2026-10-08 — Phase 7 Run #635 detector sequencing issue
- Run #635 (`37719802712`) is **NON-EVIDENCE** because the phase7 detector saw no qualifying Phase 7 file in the immediate push diff and skipped the gated workflow.
- Tester gate `research/gates/PHASE7_RUN635_DETECTOR_TESTER.md` = REQUEST CHANGES.
- Developer will use a harmless test-file trigger only; no scientific logic changes.

## 2026-10-08 — Phase 7 Run #637 repeated horizon-capture defect
- Run #637 (`37719955436`) passed regression but failed empirically at daily horizon 2 with `KeyError: ('2','E01')`.
- Cause: current developer branch still contained `H=horizons[0]`; the previously approved correction had not been preserved in the branch lineage.
- Run #637 is **NON-EVIDENCE**.
- The exact tester-approved horizon correction is being reapplied to the current branch. No scientific definitions change.

## 2026-10-08 — Phase 7 Run #637 horizon reapplication approved
- Tester gate `research/gates/PHASE7_RUN637_HORIZON_REAPPROVAL_TESTER.md` = **PASS**.
- Current developer lineage now contains the exact approved `H=H` horizon binding and direct multi-horizon capture regression.
- Fresh Phase 7 gated execution is authorized; Run #637 remains non-evidence.

## 2026-10-08 — Phase 7 Run #645 correction on current lineage
- The current branch lineage still contained `H=H`; the exact tester-requested closure fix has been rebuilt directly from the current branch head.
- No scientific definitions changed.

## 2026-10-08 — Phase 7 Run #645 closure fix approved
- Tester gate `research/gates/PHASE7_RUN645_CLOSURE_APPROVAL_TESTER.md` = **PASS**.
- Current-lineage `current_h=H` closure fix is approved; direct multi-horizon regression is present.
- Fresh gated regression is authorized; Run #645 remains non-evidence.

## 2026-10-08 — Phase 7 Run #650 tester gate
- Run #650 (`37723308187`), artifact `11532515562`, completed all 100 candidate cells.
- Independent tester gate `PHASE7_RUN650_EMPIRICAL_TESTER.md` = REQUEST CHANGES for bootstrap and regime-diagnostic implementation mismatches.
- Frozen correction amendment `PHASE7_RUN650_AMENDMENT_APPROVAL_TESTER.md` = PASS.
- Corrected implementation is in preparation; no candidate is promoted.


## 2026-10-08 — Phase 7 Run #654 independent empirical gate
- Fresh hosted Run #654 (`37763242007`) from developer head `4f1d695f291ed32996c07f01710afcecc6f2a540` completed protocol, regression, empirical execution, validation and artifact upload successfully.
- Immutable artifact `phase7-ensemble-results`, ID `11551679532`, SHA-256 `c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`.
- Independent tester gate [PHASE7_RUN654_EMPIRICAL_TESTER.md](research/gates/PHASE7_RUN654_EMPIRICAL_TESTER.md) = **PASS WITH SCOPED RESTRICTIONS**.
- Complete frozen grid: 2 layers × 5 horizons × 10 candidates = 100 executed cells. Confusion counts, metric ranges, regime-diagnostic reconciliation, and artifact digest passed independent checks.
- Corrected moving-block bootstrap construction is present and verified; the Run #650 bootstrap mismatch is closed.
- No Phase 7 candidate is promoted. All ten family-level p-values are > 0.05; the strongest raw Brier improvement is daily +10 P08 (0.00315275) with family p=0.464.
- Scoped restrictions are carried into Phase 8: abstention chronological diagnostics are not trade-only, and the intraday regime observation scale (1-minute causal path sampled at hourly decision rows) must remain fixed and explicitly documented.
- Phase 7 technical evidence is now accepted; Phase 8 remains **BLOCKED** until its independent execution/cost gate is satisfied.
- This is a status update only; no method definitions were changed after observing Run #654 results.


## 2026-10-08 — Phase 7 Run #654 final independent gate closure
- Tester report `research/gates/PHASE7_RUN654_FINAL_TESTER_GATE.md` = **PASS WITH SCOPED RESTRICTIONS**.
- Independent audit reconciled all 100 candidate cells, confusion-matrix arithmetic, metric ranges, chronological/regime diagnostic counts, and family-bootstrap p-values.
- No Phase 7 family-level test is significant at alpha=0.05; therefore no P01-P10 candidate is promoted.
- Phase 7 is closed. Phase 8 is authorized to begin only as the pre-planned long-option execution/cost translation, with final holdout still sealed.


## 2026-10-09 — Phase 7 row-level reference artifact implementation checkpoint
- Tester proposal gate `research/gates/PHASE8_RUN822_FOLLOWUP_PROPOSAL_TESTER.md` on Phase 8 tester branch authorized artifact-output infrastructure only. Tester code review `research/gates/PHASE7_REFERENCE_ARTIFACT_CODE_TESTER.md` passed with scoped restrictions; report is archived on this developer branch.
- Developer added same-run Parquet panels containing P01-P10 forecasts, labels, future returns, timestamps and block IDs, plus hashes and runtime/source manifest. Existing metric calls and scientific method definitions are unchanged.
- Hosted Run #831 (`37912024282`) passed the existing Phase 7 regression suite but started before the new tester code gate and must be treated as NON-EVIDENCE for accepting the new reference artifact. Run #835 (`37912125332`), #837 (`37912165684`) and #838 (`37912206197`) exposed a defect in the new manifest regression fixture: its aggregate JSON temporary path was outside repository ROOT, causing `Path.relative_to(ROOT)` to raise `ValueError`.
- Corrected the fixture to create temporary files under `data/reports`; commit `14d20380632e365b2a0b6b63afe58f2775375950`. Run #846 (`37912507182`) skipped the Phase 7 gate because the changed paths did not include a science trigger; a fresh hosted regression gate is still required.
- Next: trigger one fresh Phase 7 hosted gate from the reviewed source path, verify both original and new reference-artifact regression suites, then independently audit the uploaded artifact. No new Phase 7 metrics or Phase 8 option execution is accepted yet.

## 2026-10-09 — Phase 7 reference artifact regression gate PASS
- Fresh hosted Run #852 (`37912587739`, head `ac6b30090e5146d527bb0af6dd9352a9b6a7fc93`) passed the original Phase 7 regression suite, the new reference-artifact regression, and the reference-artifact tester authorization gate.
- Tester report `research/gates/PHASE7_REFERENCE_ARTIFACT_REGRESSION_TESTER.md` = PASS for regression only. The Phase 7 empirical job is in progress; no new reference artifact or metrics are accepted until post-run audit.
- Run #831 remains non-evidence because it started before the new code gate. Runs #835/#837/#838 remain non-evidence because the new regression fixture failed in those runs. Run #852 is the first correctly gated run for the new output contract.
- Phase 8 manifest amendment and the 4,800-cell option grid remain blocked pending a complete, hash-verified artifact and independent audit.

## 2026-10-09 — Phase 7 immutable reference artifact checkpoint

- Reconciled GitHub Actions runs #852 (37912587739), #924 (37914896724), and #925 (37914905848). At this checkpoint all three still report `in_progress`; their empirical jobs are executing `scripts/run_phase7_ensemble.py`, and none has published an artifact.
- Run #852 remains unusually stale: its run metadata last updated at 09:39:25 UTC despite the empirical job still being marked active. Live log retrieval for #852 and #925 returned GitHub `BlobNotFound`; this is treated as an observability limitation, not evidence of success or failure.
- Regression and tester-authorization jobs passed in the later runs, but the real-data artifact audit has not occurred. No Phase 7 metrics are newly accepted, and Phase 8 remains blocked.
- The moving-block bootstrap allocation optimization has passed equivalence regression and received tester approval with scoped restrictions; this does not waive empirical completion or artifact provenance review.
- Operational correction: avoid launching additional competing empirical jobs while these runs are active. Reconcile the first completed run and audit its artifact before deciding whether remaining attempts are duplicates or require further action.


## 2026-10-09 — repeated live poll
- No state transition: runs #852, #924 and #925 are still marked `in_progress`, each active at the Phase 7 ensemble script; no artifacts are listed.
- Added the prolonged-execution/observability issue to `research/ERROR_LOG.md`. The root cause remains unknown; stale run metadata and missing live logs are not interpreted as scientific outcomes.
- Next gate remains unchanged: first completed artifact → independent source/provenance/statistical audit → tester decision. Phase 8 stays blocked.


## 2026-10-09 — Phase 7 Run #925 independent empirical audit — REQUEST CHANGES

- Runs #852, #924 and #925 completed and uploaded artifacts. The tester selected Run #925 (ID `37914905848`) on immutable source commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1`.
- Independent tester workflow Run #943 (`37935031119`) reconciled artifact/source/code hashes, ten panel identities, timestamps, labels and future returns, then found 2,775 passing checks and 323 failing checks clustered into four implementation defects.
- Defects: P10's frozen [0.45, 0.55] abstention is absent; rows with missing volatility/trend enter low/low regime counts; P05/P06 block diagnostics do not use abstention masks; non-evaluable rows are incorrectly treated as zero in family-bootstrap differential arrays.
- Independent tester report: [PHASE7_RUN925_EMPIRICAL_TESTER.md](gates/PHASE7_RUN925_EMPIRICAL_TESTER.md) = **REQUEST CHANGES**.
- Run #925 is **NON-ACCEPTED EVIDENCE**. Older Run #654 remains an archived technical artifact but does not override this newer protocol-compliance finding.
- Phase 7/8 progression is blocked. Developer must correct these defects on `phase-07-developer`, add regression tests, and submit the exact correction commit for independent tester review before fresh empirical execution. The Phase 8 4,800-cell grid must not start until the fresh Phase 7 artifact passes.


## 2026-10-09 — Phase 7 correction submission reviewed; fresh-run gate remains blocked

- Developer correction submitted at `research/gates/PHASE7_RUN925_CORRECTION_CODE_SUBMISSION.md`.
- The targeted source fixes were independently verified and hosted Run #964 (`37936076338`) passed protocol/regression/reference-panel regression checks; empirical execution was skipped.
- Tester report `research/gates/PHASE7_RUN925_CORRECTION_REVIEW_TESTER.md` = **REQUEST CHANGES** because the correction-specific PASS is not bound to the exact reviewed snapshot. Any later source/workflow/protocol change could reuse stale approval text.
- Next developer action: bind approval to exact reviewed commit and hashes of protected source/test/validator/spec/workflow files; add positive and negative authorization tests for both manual and automatic paths.
- Runs `37935752265` and `37935794939` began empirical execution before the guard was corrected. They remain **NON-EVIDENCE**, regardless of artifact availability.
- No Phase 7 metric or strategy is promoted. Phase 8 remains blocked.


## 2026-10-09 — Phase 7 approval snapshot binding implemented

- Developer commit `b9fc7c9e7c77efb5149d35e31509251f701122ce` adds a fail-closed approval validator and positive/negative regression tests, and wires it into both the automatic caller and reusable/manual execution workflow.
- Protected source, tests, input/acquisition logic, method specifications and workflow files must match SHA-256 values in a tester-branch approval manifest. The reviewed commit must exist and be an ancestor; tester report and manifest must match byte-for-byte across branches and the report hash must match the manifest.
- Hosted [Run #981](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37938077088) passed protocol, Phase 7 regression, correction-approval validator regression and reference-artifact regression. Authorization and empirical jobs were skipped, as expected, because independent approval/manifest are not yet present.
- State: **AWAITING INDEPENDENT TESTER REVIEW**. No empirical run authorized, no metric accepted, Phase 8 blocked.


## 2026-10-09 — Phase 7 correction-approval test fixture repair

- Latest hosted check [#989](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37953177951) failed after protocol and the standard Phase 7 tests passed; the correction-approval regression asserted a bare filename against full-path registry entries.
- Developer corrected the assertion to the canonical full path. The production protected-file registry already covered that report; no scientific logic or model metrics changed.
- State: **ENGINEERING RE-RUN AND INDEPENDENT TESTER REVIEW REQUIRED**. Run #989 is non-evidence; no new Phase 7 artifact/metric is accepted. Phase 8 remains blocked until Phase 7 correction approval and a fresh post-run artifact audit pass.


## 2026-10-09 — Phase 7 snapshot approval retry

- Run #990: protocol, Phase 7 regression, correction-approval regression and reference-artifact regression passed on the corrected test snapshot.
- Tester issued a correction-specific code-gate approval with 25 protected-file hashes. The first mirrored attempt, Run #992, was correctly refused by the fail-closed validator due to a report-format/digest mismatch and one protected hash transcription error.
- Tester corrected the report and manifest on the isolated `phase-07-tester` branch. Developer mirrors the exact tester blob versions and records the Run #992 refusal.
- State: **AWAITING FRESH HOSTED SNAPSHOT VALIDATION**. Run #992 is non-evidence; no empirical metrics are accepted. Phase 8 remains blocked.


## 2026-10-09 — Phase 7 fresh empirical run authorized and started

- Snapshot-bound correction code gate: **PASS WITH SCOPED RESTRICTIONS** for one fresh empirical execution only.
- Hosted [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656) passed protocol, regression, approval-validator, reference-artifact regression and snapshot authorization. All 25 protected-file hashes and the exact tester report/manifest copies validated.
- The empirical job is currently **IN PROGRESS**. No output is accepted yet; its artifact must undergo separate independent post-run audit, including all ten method panels, P10 abstention, finite regime eligibility, P05/P06 masks, family inference, hashes and metric reconciliation.
- Run #925 remains rejected (including the re-audit in tester Run #993). Run #992 remains a logged authorization-refusal attempt. Phase 8 stays blocked until the fresh empirical gate passes.


## 2026-10-09 — Run #994 active empirical execution: runtime guardrail

- Run #994's snapshot authorization and regression gates passed; its empirical script started at 16:15:48 UTC and remains active. Validator/upload steps are pending.
- Live logs are unavailable while active (`BlobNotFound`); no failure is inferred.
- Run #925's corresponding script took 1h 53m 20s. Current run remains within the last observed runtime window.
- State: **EMPIRICAL SCRIPT ACTIVE — WAIT FOR TERMINAL STATE**. Do not start another empirical run while this one remains active. Phase 8 remains blocked.


 
## 2026-10-09 — Phase 8 costs: preliminary official-source review only

- Captured current official Paytm Money and NSE source links for the future option-execution cost model.
- Paytm public information is account-plan-sensitive: its F&O FAQ reports ₹10 per unique executed order, while its older plan notice documents ₹10/₹15 grandfathered and ₹20 newer-account plans. Use ₹10/₹15/₹20 sensitivity until the account-specific tariff/contract note is verified.
- NSE 2026 option transaction charges: ₹3,553/crore premium turnover per side from 1-Mar-2026; STT 0.15% on option sale premium and 0.15% on intrinsic value on exercise from 1-Apr-2026. Other statutory levies/GST, spread, slippage, latency and premium decay still require explicit handling.
- This is preparation only. Phase 8 has not advanced; its opening gate remains the fresh Phase 7 Run #994 artifact and independent empirical approval.


## 2026-10-09 — Additional free-source leads recorded (pre-gate only)

- Identified candidates on Hugging Face, Kaggle (reported via a community issue), Zenodo and GitHub that are not all covered by the current Phase 8 source-probe list. Candidate source URLs and limitations are recorded in the research log.
- The candidates are not accepted datasets: licensing/provenance, row coverage, expiry/strike omissions, OHLC-vs-bid/ask fields and official NSE cross-validation still require an audit.
- State is unchanged: Phase 7 Run #994 remains the active empirical target; Phase 8 is blocked and no P&L grid or source-composite amendment is authorized.


## 2026-10-09 — Free-source preview quality caveat

The current Hugging Face dataset viewer for rissin/nse-options-intraday shows legacy daily option rows dated 2005-06-10 with open/high/low/close, volume, open interest and settlement values all equal to zero for sample contracts. These may be placeholders for contracts with no eligible trade/quote, not valid executable observations. Do not silently forward-fill, impute or assign positive execution value to these rows. Validate zero/missing values by source and contract, retain explicit status/reason fields, and exclude invalid/non-positive premium rows from executable P&L while keeping them in coverage diagnostics. The dataset's license field is “other”, its provenance/redistribution terms need review, and it does not describe bid/ask data. Source: https://huggingface.co/datasets/rissin/nse-options-intraday

This confirms the source remains a candidate only. No source was imported and no Phase 8 gate was opened.



## 2026-10-09 — Hugging Face schema-range red flags found during pre-gate source search

A public preview of `artist-23/nifty-options-data` reports 33.96 million rows and shows suspicious extrema: `volume` minimum -4,288,892,671 and maximum 1.44 billion, while `iv` reaches 4,540. Those reported ranges require direct file inspection and source reconciliation; they are not evidence that every row is corrupt, but they make this candidate unsuitable for blind use. The preview includes normal-looking rows, which can coexist with bad/misparsed/extreme rows. Dataset viewer/source: https://huggingface.co/datasets/artist-23/nifty-options-data (viewer summary and schema).

The public dataset `codepyx23/india-index-options-1m` explicitly states it is a **duplicate** of `thetrademarkk/india-index-options-1m`, and both carry `CC-BY-NC-4.0`; do not count those as independent data sources or use them to claim independent cross-validation. Source: https://huggingface.co/datasets/codepyx23/india-index-options-1m/blob/main/README.md

The dataset `thetrademarkk/india-index-options-1m` describes partial option coverage, missing OI/settlement on intraday rows and no bid/ask stream. It is Q1 OHLC proxy data, not Q2 quote-executable evidence. Source: https://huggingface.co/datasets/thetrademarkk/india-index-options-1m

Required pre-acceptance checks for any of these candidates: check `high >= max(open, close, low)`, `low <= min(open, close, high)`, positive premium for executable rows, non-negative volume/OI when fields are present, IV unit/range sanity, timestamps/IST alignment, duplicated contract-minute keys, strike/expiry completeness, and overlap with official NSE contract rows. Keep raw input hash and row-level invalid reason codes. Never clamp, impute or drop bad rows silently. This is source QA preparation only: no dataset imported, composite built, or Phase 8 P&L executed.



## 2026-10-09 — Additional free minute-level spot source lead (not options)

The Hugging Face dataset `Hitjob-Done/indian-stock-market-minute-data` reports approximately 720 million rows/10.5 GB, an MIT license, and minute/day stock/index OHLCV data including symbols such as `NIFTY_50`. It is a candidate for independent underlying-index spot cross-checks, not a substitute for contract-level option records. Its card describes timestamps in UTC (convert to IST explicitly) and OI = 0 where not applicable; validate the actual NIFTY_50 shards, date coverage, timestamp conversion, license/provenance and overlap with NSE before use. Its displayed loading snippets point to dataset `xxparthparekhxx/indian-stock-market-minute-data`; the current page appears to be a source/reupload mirror, so investigate data identity/provenance and do not count mirrors as independent sources. Sources: https://huggingface.co/datasets/Hitjob-Done/indian-stock-market-minute-data and https://huggingface.co/datasets/xxparthparekhxx/indian-stock-market-minute-data.

This source can only help with spot-layer corroboration. It does not provide a contract quote, option bid/ask, or independently validated option premium path. No download or merge occurred; it remains a candidate for the free-source audit.



## 2026-10-09 — NSE official data-use / public-repository governance checkpoint

The main repository is publicly readable. The official [NSE Data Sharing & Usage Policy](https://www.nseindia.com/static/market-data/nse-data-policy) states that market data ownership remains with NSE/NSE Data and redistribution is not permitted except as agreed in the relevant agreement. The official [NSE copyright page](https://www.nseindia.com/static/nse-copyright) says website content generally may not be reproduced or stored on another website/electronic retrieval system, while its stated permission for download is scoped to personal, non-commercial or educational use and conditions. Specific instrument/data terms should be checked for the actual use case; this note is not legal advice.

**Implementation consequence for this public repo:** do not commit raw NSE bhavcopy archives, raw option rows, or public row-level datasets obtained from sources whose terms restrict redistribution unless documented permission/license explicitly allows it. Do not assume that publicly downloadable equals redistributable. Keep raw downloads transient or in access-controlled storage only where applicable terms and GitHub access controls permit; where cache reuse is appropriate, cache only under an access model compliant with the source license. Publicly store source IDs/URLs, data dates, schemas, per-file hashes, license status, reconciliation reports, aggregate research results and code. Check GitHub Actions cache/artifact visibility before relying on it for licensed raw market data. The repository’s goal of keeping reproducible evidence should not override data-licensing restrictions.

Free-source code candidates for later independent methodology review:
- https://github.com/SatvikBajpai/nifty-options-greeks — states it ships MIT-licensed code, not market data; locally downloads official NSE EOD bhavcopies, normalises legacy/UDiFF schemas, caches raw files, computes option forward/IV/Greeks, and has explicit liquidity/solver validation. Important limitation: end-of-day only, not historical bid/ask or intraday execution data; its spot source defaults to Yahoo. Suitable for a code/methodology cross-check after code-license and dependency review, not an independent data source.
- https://github.com/shayakbanerjee99/nifty-options-elt — ETL code for transforming official NSE daily F&O bhavcopy into queryable DuckDB option chains; a pipeline, not a separate price vendor.
- https://github.com/Aniruddha1980/Bhavcopy — open-source NSE report-fetching utility (README claims MIT); inspect current site compatibility/cache and provenance before use.
- https://github.com/NikhilSuthar/indian-market-data/blob/main/docs/datasets.md — catalog of NSE report types and file patterns; a useful free-source inventory, not a data license or hosted dataset.
- https://github.com/darshkale/nse-options-data-pipeline — option EOD enrichment/execution-modeling code; treat outputs as derived from the same NSE source family until lineage proves otherwise.

These do not provide historically executable bid/ask quotes. They must not be counted as independent price evidence when their output derives from the same official bhavcopy source. This is a governance/methodology preflight only: no files imported, no Phase 8 specification/workflow changed, and no option-P&L run authorized.



## 2026-10-09 16:53 UTC — Run #994 active-state recheck

- Same immutable workflow: [Run #994](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656), source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- Empirical job `113912548214` still reports `in_progress` at `scripts/run_phase7_ensemble.py` (started 16:15:48 UTC); validation and artifact upload remain pending. No Run #994 artifacts are listed.
- GitHub run-level `updated_at` remains stale and active live logs are unavailable in earlier polls; that is an observability constraint, not a terminal failure.
- At this poll elapsed runtime is about 37 minutes, less than the previous completed Run #925's 1h 53m 20s model-step duration.
- No duplicate was dispatched, no data/result was accepted, and Phase 8 remains blocked.



## 2026-10-09 — Additional GitHub/Rust/EOD option research candidates (pre-gate)

Read-only repository search identified four further leads:
- **NSE-FNO-Data-bank** — https://github.com/SantoshSrinivas79/NSE-FNO-Data-bank claims a validated daily NSE F&O bhavcopy archive with 1,579 files, 13-Apr-2020 to 31-Aug-2026 (approximately 1.2 GB compressed), plus a downloader/validator. This may help cross-check calendar/availability counts and archive integrity, but it is EOD data only. Publicly committed raw NSE data is not proof of a redistribution licence; do not mirror its archive into this repository absent documented permission.
- **jugaad-rs** — https://github.com/Am1n1602/jugaad-rs provides a Rust NSE data library/CLI including derivative history, daily reports, option-chain snapshots and related market reports. It is code for retrieving NSE data, not an independent vendor. Useful to test source redundancy/API fallbacks after licence and schema review; intraday historical quote availability must be confirmed per method.
- **Nifty IV Surface & Event-Vol Tracker** — https://github.com/kfinance/nifty-iv-event-vol-tracker documents an overnight straddle research path using NSE F&O bhavcopy (claimed 2024-01-01 to 2026-09-18), including IV/event-vol studies and a claimed backtest. Treat as a hypothesis/code-review lead only; independently verify no synthetic data contamination, reconstruct results from allowed inputs, use a chronological out-of-sample design and reconcile all costs/slippage before any strategy inference. Do not import its reported return as evidence or add it post-hoc to the frozen current Phase 7 run.
- **NSE historical archive bank / API tools** — https://github.com/Aniruddha1980/Bhavcopy and https://github.com/Teja-Ram-Pooniya/nser-r-programming-option-data-nse include methods for historical F&O bhavcopy and selected NSE reports, but are overlapping retrieval wrappers over the same official data source, not independent price observations.

No candidate raw data was downloaded or copied. These leads are listed for the next permitted data/method gate only. Current Run #994 remains the active empirical target; Phase 8 remains blocked until its independent artifact gate.


## 2026-10-09 — Automatic independent audit orchestration added

- Added main-branch workflow [.github/workflows/phase7-approved-artifact-audit.yml](https://github.com/vishnuvcr/Naked-option-v1/blob/main/.github/workflows/phase7-approved-artifact-audit.yml).
- Automatic path: after a successful completed Research Protocol Check on phase-07-developer, preflight retrieves the exact run metadata and proceeds only when the run is successful and has one non-expired, non-empty phase7-ensemble-results artifact and one phase7-ensemble-reference artifact. Non-eligible automatic events are skipped.
- Manual path: the same workflow exposes workflow_dispatch with a required run_id; the same source branch/status/artifact checks apply, and invalid manual inputs fail closed.
- Independence: the audit uses the generic tester script from pinned tester commit 50334eb728a85ae8ca88f9ded5246b867c9cb56f, checks out the exact developer source SHA, downloads only artifacts for the requested run, and writes its JSON/Markdown report and phase status/log entries to phase-07-tester. The final workflow gate fails unless the report identity is exact and all checks pass.
- The legacy Run #925 audit on phase-07-tester is now manual-only and also requires an explicit boolean opt-in; normal tester-branch pushes no longer repeat the rejected historical audit.
- **Run #994 has not yet completed** at this checkpoint (its empirical step remains in progress and no artifacts are published). No audit was run on it yet, no metrics were accepted, and Phase 8 remains blocked.


## 2026-10-09 — Approved-audit workflow smoke test (preflight only)

- A completed developer protocol run [#1033](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37965583008) had no Phase 7 result artifacts because it was documentation-only.
- The newly installed automatic audit workflow [run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37965605363) inspected that exact run, found zero phase7-ensemble-results artifacts, and correctly skipped the independent audit. No tester code was executed and no metric was inferred.
- The main workflow was subsequently tightened to require the upstream workflow name to be exactly Research Protocol Check in addition to branch, completion, successful conclusion, source SHA and both non-empty artifact checks. Future auto events will recheck these constraints. Manual dispatch requires a run ID and rejects incomplete/missing-artifact runs.
- This is preflight evidence only, not empirical evidence. Run #994 remains in progress with no artifacts; Phase 8 remains blocked.


 
## 2026-10-09 — Automatic audit preflight identity check confirmed

- Automatic Phase 7 approved-audit workflow run #2 (Actions run 37966008847) processed completed developer protocol run 37965987043.
- It accepted the exact source as a successful Research Protocol Check on phase-07-developer, then correctly stopped before audit because there were 0 required aggregate result artifacts. The independent tester job was skipped.
- This confirms the name/branch/state guard plus fail-closed artifact preflight path. It is not a scientific or tester empirical decision.
- Run #994 remains active at the ensemble script with no result artifacts. Phase 8 remains blocked.


## 2026-10-09 — Exact implementation comparison: Run #925 vs Run #994

- Compared the frozen Phase 7 source at Run #925 commit `682eadf2a9eb4de250bc3db27d02e57f88687fa1` with Run #994 source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- The method specification file `research/phase7/PHASE7_METHOD_SPEC.md` is byte-identical at both commits (Git blob SHA `964b323f5ed86b12f743dea1c9b842aba166996a`). Thus the frozen protocol text was not amended between runs.
- The implementation and tests differ materially in fixes that target the prior independent audit defects:
  1. `P10` is included in the registered abstention mask `[0.45, 0.55]`, including both endpoints.
  2. P08/P09 regime-state counts now require finite volatility **and** trend; missing features are no longer silently classified as low/low.
  3. Family-bootstrap Brier differentials now leave rows non-evaluable when label, forecast or causal baseline is unavailable; only eligible abstentions receive zero differential, preventing missing data from diluting family means.
  4. Chronological-block diagnostics can receive the method-specific eligibility mask, so P05/P06/P10 diagnostics use the same registered row eligibility as the reported metrics.
  5. Regression tests now include explicit cases for these abstention, missing-regime-feature, family-missingness and candidate-mask conditions. Result validation permits P10's candidate-eligible block count to differ from the underlying regime diagnostic count, while P08/P09 retain their equality invariant.
- These are implementation corrections toward the frozen protocol, not changes to the protocol file. They do not guarantee that the new run passes; only the independent exact-run artifact audit can establish that. Run #994 remains active, has no artifacts at the latest poll, and Phase 8 remains blocked.


## 2026-10-09 — OPEN TESTER CHECK: P10 regime-diagnostic block-count invariant

- Frozen protocol `research/phase7/PHASE7_METHOD_SPEC.md` currently says the P08/P09/P10 regime-diagnostic block count must equal the candidate chronological-block count.
- The current `scripts/validate_phase7_results.py` explicitly enforces that equality only for P08/P09 because P10's registered abstention mask can remove every eligible metric observation from a chronological block.
- The production `scripts/run_phase7_ensemble.py` currently attaches the shared regime diagnostics to P08/P09/P10, while its P10 `chronological_blocks` uses the candidate-specific abstention mask. The independent auditor reconciles the shared regime diagnostics and P10 block metrics separately but does not explicitly enforce the frozen spec's stated count equality for P10.
- This is a **possible protocol/diagnostic-definition inconsistency**, not yet a finding that Run #994's eventual artifact fails. Do not silently amend the spec or disable the check. The tester must determine, from the literal frozen text and fresh artifact, whether (a) the implementation must retain matching P10 diagnostic blocks while preserving P10 abstention semantics, or (b) a formal pre-registered specification amendment is required. Any amendment needs its own tester approval and cannot be applied post hoc to justify results already examined.
- Run #994 is already executing immutable source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`; no code/spec change has been made to that run. The tester report must document this point and keep scientific promotion/Phase 8 blocked if unresolved.


## 2026-10-09 23:20 IST — Resume checkpoint

- The authorized empirical target Run #994 remains `in_progress` on immutable source commit `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`; ensemble step started 2026-10-09 16:15:48 UTC and has not advanced to validation. The GitHub job log endpoint currently returns BlobNotFound and no artifacts are published. No metrics accepted.
- Developer correction commit `39e964d4ae99bb02b113fa4eabecd91c9af46c16` adds P10 candidate-specific regime-diagnostic filtering, P08/P09/P10 equality validation, and a fully abstained-block regression fixture. Developer workflow run #1068 passed its regression job; empirical/tester-gated jobs were skipped, so this is not independent approval or an empirical run.
- Correction has been submitted to the isolated tester branch in `research/gates/PHASE7_P10_DIAGNOSTIC_INVARIANT_TESTER.md` for independent review. No change was made to Run #994's source or protocol.
- Gate state: tester review pending; Run #994 artifact audit pending; Phase 8 blocked.


## 2026-10-10 — Exact-snapshot gate remains closed

Tester static review accepted the P10 diagnostic correction in commit 39e964d for a future empirical run only. However, the correction approval manifest was restored to the last verified snapshot because the attempted new report digest and protected hashes did not pass a second verification. Current developer HEAD is not authorized for a fresh empirical execution. Do not set empirical_authorized or proceed until the exact tester report/manifest are byte-identical across branches and all protected SHA-256 values are independently verified. Run #994 remains immutable and non-significant; no strategy selected.


## 2026-10-10 — Uploaded research-paper literature supplement

- User supplied 15 unique research PDFs; duplicate re-uploads were counted once. The structured review and registry entries L037-L051 are on phase-01-developer: [paper-by-paper review](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-01-developer/research/literature/UPLOADED_PDF_REVIEW_2026-10-10.md).
- No research plan, frozen Phase 7 method scope or horizon was changed. The papers contribute replication hypotheses, not new project metrics.
- Newly relevant prediction leads include the 2026 Cureus multi-window regression paper with a Naive Persistence comparator; deep sequence-model comparisons; dated sentiment + FII/DII + India VIX + PCR; and lagged USD/INR and global-market inputs. All require separate point-in-time and chronological checks.
- Registry audit found a pre-existing semantic column shift in literature row L003; the row was corrected on phase-01-developer and the defect recorded in its error log. Independent tester validation must verify the row and the 15 added records.
- **Current empirical hold unchanged:** the available-data/global-feature extension remains regression-passed and tester-review-pending. No prediction result has been generated by this extension. Do not start empirical execution until the exact protected snapshot receives independent tester approval.
- Options-strategy material in the PDFs is contextual only. This continuation remains prediction-only; Phase 8 stays blocked.


## 2026-10-10 — Phase 7 available-data extension corrected after tester REQUEST CHANGES

- Tester report is on the isolated tester branch: [PHASE7_AVAILABLE_GLOBAL_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_TESTER.md). It rejected the reviewed snapshot for a G13 specification mismatch, incorrect conditional Bonferroni family size, insufficient paired-baseline reporting, incomplete output validation, and a numbering typo.
- Developer corrections are now present in the predictor, regression tests, result validator, validator tests, workflow protection set, and method specification.
- G13 now follows the pre-registered equal-weight mean of raw causal 1- and 5-session log returns, with a missing contributor making that row unavailable rather than changing the constituent set.
- The inference function now multiplies by the fixed registered family size of five horizons even if fewer horizon-level tests execute; executed test count is reported separately.
- Candidate output now carries paired baseline metrics on the exact candidate prediction rows. The top-level baseline remains feature-mask independent and is explicitly labeled as a broader diagnostic.
- Added a testable complete-grid/result validator checking method and baseline cells, paired row counts, metric arithmetic, blocked reasons, horizon family p-values, fixed Bonferroni factor, source/provenance hashes, and unopened holdout.
- **Gate remains closed.** The REQUEST CHANGES tester report is not an approval; no Phase 7 approval JSON has been issued, and no empirical prediction result has been generated from this extension. Wait for a new independent review of the exact updated code/spec snapshot and the associated hosted regression run before authorizing one empirical batch.


## 2026-10-10 — Row-level forecast panel added before empirical gate

- A further independent auditability check found that aggregate metrics alone would make it harder to reproduce the candidate metrics and common-row moving-block inference.
- Predictor now writes data/reports/available_global_prediction_panels.csv alongside the summary JSON, including actual direction/realized return, each candidate probability or abstention, baseline probability, source/feature IDs and cell status. JSON provenance records its path and SHA-256.
- The standalone validator now checks panel provenance and key uniqueness, labels versus realized-return sign, metric recomputation for each model and baseline, paired baseline metrics, common-row family Brier improvements and deterministic moving-block bootstrap p-values.
- Panel export and its validator tests are included in the protected workflow snapshot and artifact upload. Exact blobs are listed in the latest developer submission addendum.
- **Empirical gate remains closed.** No row-level empirical panel or prediction result has been generated yet. Hosted regression outcome is not verified by the available status tools. The tester must independently review the added panel logic and verify hosted regression before any empirical approval.


## 2026-10-10 — Final panel audit-contract update

- Added all-row candidate/baseline-probability reconciliation and independent recomputation of mean realized log return on forecasts classified UP.
- Added explicit rejection of unknown method/row-type combinations and malformed prediction-availability flags; an empty panel cannot be paired with an executed family result. The saved CSV is serialized to 17 significant digits for round-trip float reproducibility.
- Added regression fixtures for a mismatched candidate baseline probability and a mutated family p-value, in addition to complete synthetic-panel reconciliation and probability-mutation tests.
- Current blob identifiers are pinned in the final section of the developer submission. The workflow is intended to run automatically on protected-file commits, but the latest commit-status queries still expose no checks/run result; CI therefore remains unverified.
- **No model output exists from this extension; empirical execution stays blocked** until a fresh tester report verifies the latest exact files and an actual hosted regression pass is observable.


## 2026-10-10 — Tester resubmission report and execution hold

- Independent tester resubmission: [PHASE7_AVAILABLE_GLOBAL_RESUBMISSION_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RESUBMISSION_TESTER.md). Verdict: **PASS WITH SCOPED RESTRICTIONS for static source review only; empirical execution NOT AUTHORIZED**.
- The reviewer verified that the source-level corrections are present, including raw-return G13, fixed five-horizon Bonferroni, paired baseline calculations, row-level output/provenance, metric reconstruction and family bootstrap checks. This is not a runtime test pass.
- Workflow/status lookups returned empty check/run lists, so the actual hosted regression outcome remains unverified. The approval manifest remains absent.
- Next authorized transition is only: surface an observable green automatic/manual workflow run and its exact run artifact/hashes, then request a separate execution-gate tester decision. No empirical output exists and Phase 8 remains blocked.


## 2026-10-10 — Protected NIFTY acquisition-code gap fixed

- Workflow audit found that the empirical job runs scripts/acquire_nifty_daily_history.py, but this input-acquisition code was absent from the protected exact-snapshot hashes and push triggers.
- Added the script to the push path filter, approval allowlist and SHA-256 report list in the workflow.
- Workflow blob is now updated after the previous tester resubmission; therefore the prior static report does not cover the current workflow blob.
- **Execution remains NOT AUTHORIZED.** Need an independent tester review of the latest workflow and a verifiable hosted regression run. No prediction output exists.


## 2026-10-10 — Phase 7 available-data gate after Run #43

- Acquisition/cache and timezone fixes are in the developer snapshot. [Hosted Run #43](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992695619) passed all regression suites: 8 acquisition/cache, 11 predictor and 11 result-validator checks.
- [Independent tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_TESTER.md) is **PASS WITH SCOPED RESTRICTIONS**, authorizing one exact-snapshot prediction batch only. The identical report is mirrored at [developer branch handoff](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_TESTER.md).
- **The prediction batch has not run.** The exact-snapshot approval manifest write was blocked by platform safety checks; the approval JSON remains absent. The automatic workflow therefore has no authority to enter empirical execution.
- Run #41 and #42 failed only on test fixtures, were corrected, and are logged as non-evidence. Run #43 is regression evidence, not model performance evidence.
- Phase 7 remains at the empirical-execution authorization boundary. Phase 8 and any strategy promotion remain blocked.


## 2026-10-10 — Phase 7 Run #44 completed; no model promoted

- [Run #44](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915) completed successfully: regression job, exact-snapshot approval job, empirical prediction job, result validation and artifact upload all succeeded.
- Immutable artifact ID: `11657636547`, `phase7-available-global-results`; artifact SHA-256: `63b607db7227cdd91f3a62a0a8ca5f0b010d12c3bad1848ebbd9f59961804891`.
- Independent tester audit passed artifact integrity and metric/inference reconciliation. Panel: 91,988 rows; 12 registered methods across five horizons; all 60 cells executed. Source/panel hashes match the results JSON.
- **Statistical result: no candidate promoted.** Raw family p-values by horizon 1/2/3/5/10 = 0.9840 / 0.8882 / 0.6786 / 0.7745 / 0.9800. Every Bonferroni-adjusted p-value = 1.0.
- Descriptive leaders: G13 global-equity composite at 1 and 2 sessions; G06 Asia composite at 3 and 5 sessions; G02 Bank Nifty at 10 sessions. Largest observed Brier improvement is G06 at 5 sessions (+0.001623), but its family p=0.7745 and ROC AUC=0.556; this is not persuasive evidence of predictive skill.
- Global-source cache entries all report `cache_hit: false` in this run; the previous cached schema was not accepted and the series were reacquired. The post-cache action completed; a future separately authorized run should verify cache reuse.
- [Full result summary](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/results/PHASE7_RUN44_AVAILABLE_GLOBAL_PREDICTION_RESULTS.md); [independent tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md).
- **Phase 8 remains BLOCKED.** The final untouched holdout remains unopened; no strategy has been tested or promoted. Further prediction work requires a new preregistered family and independent tester gate.


## 2026-10-10 — Extension 2 spec correction resubmitted

- Initial tester report [PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SPEC_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SPEC_TESTER.md) returned REQUEST CHANGES before data access.
- Corrected spec blob: `7f6cc6e86556db3da9f87c23c0e183bcb3282310`. It now defines legacy-to-UDiFF mapping, FII/DII imbalance denominator, exact F04/F05 formulas, canonical sector index identities, and global-bootstrap treatment of missing forecasts.
- Updated handoff: `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_DEVELOPER_SUBMISSION.md`.
- **Current gate: corrected spec re-review pending.** No source feasibility data were downloaded and no model was fit. If the tester passes, only small deterministic Gate A samples are authorized.


## 2026-10-10 — Extension 2 Gate A Run #1: partial pass, source review changes required

- [Run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019391488) passed all six offline source-schema tests and uploaded artifact ID `11657980203`, JSON SHA-256 `b39b7edce155a1ce0851186fff3f84d781474d89b5d3630831bcbf4f6df473b9`.
- Official legacy F&O archive for 2024-07-05 and official UDiFF archive for 2024-07-08 both fetched and passed date/schema checks (33,930/34,390 rows; 1,634 NIFTY option rows each).
- Official FII/DII API returned current schema but only two records for 2026-10-09. A free GitHub mirror has 164 unique records from 2026-01-14 through 2026-09-30, insufficient for the 500-date confirmatory family test.
- Sector API URL returned generic HTML; official index CSV pattern `ind_close_all_DDMMYYYY.csv` identified as a better source but not yet sampled. Advances/Declines page did not expose historical rows in this sample.
- Tester report `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_FEASIBILITY_RUN1_TESTER.md` = REQUEST CHANGES. Next bounded iteration must sample official daily index and equity bhavcopy CSVs and search more free historical FII/DII sources.
- No full-history download, feature table, labels or model fitting occurred. Gate A remains open.


## 2026-10-10 — Gate A sampler v2 regression failed before source requests

- [Run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019728293) failed in the offline test step due to an over-escaped ISO date regex; no live source request or artifact upload occurred.
- Developer corrected the regex and changed the workflow push trigger to require a tester-approved Gate A approval file.
- Corrected sampler blob `fb83fe5e880a26134a765a0426f7aa85380272fb`; tests blob `d818613dc2f9188224562a953fd979a6c274d292`; workflow blob `d303d8bd05978ef4837e1935ed40f8c2cdec851c`.
- **Status:** independent re-review pending. No source feasibility v2 download, full history, or model fitting is authorized yet.


## 2026-10-10 — Extension 2 Gate A sampler v2 exact-snapshot review pending

- Current v2 sampler blob is `fb83fe5e880a26134a765a0426f7aa85380272fb`; current test blob is `d818613dc2f9188224562a953fd979a6c274d292`; workflow blob is `c535610e69c2e90934ab4e59d754b584e29ff6ec`.
- The prior v2 tester PASS applies to sampler blob `4c69b20e3eb4a6a0f99c6f0137de06806a13ff1f`, not the current code. Exact review request: [source sampler v2 review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_REVIEW_REQUEST.md).
- Workflow now runs offline tests first, then validates an exact tester report/manifest and hashes before any source request; manual source sampling defaults to off.
- [Run #1 / 38019728293](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019728293) failed on an over-escaped ISO-date regex before live acquisition; source fetching and artifact upload were skipped.
- **Current gate:** exact-snapshot tester review and current hosted offline test evidence pending. Approval JSON remains absent. No live source requests, full history, feature table, labels or model fits are authorized at this checkpoint.


## 2026-10-10 — Gate A approval guard strengthened; exact review snapshot refreshed

- Current guarded workflow blob: `fdc0a6bef97796b38424048304b704d86f80c450`. The previous workflow blob `c535610e69c2e90934ab4e59d754b584e29ff6ec` is superseded.
- The guard now requires a specific current tester-decision line, explicit denial of full-history/model fitting, matching report SHA-256, protected file SHA-256 values, protected Git blob IDs quoted in the report, and reviewed-commit ancestry. Manual source sampling remains off by default and fails closed without the exact manifest.
- Current review request: [sampler v2 exact-snapshot review](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_REVIEW_REQUEST.md).
- No current approval manifest exists. No live source requests or artifact generation are authorized pending a new tester PASS and green hosted offline tests.


## 2026-10-10 — Gate A workflow now includes F&O transition samples

- Static audit found that the earlier v2 workflow omitted the legacy/UDiFF F&O archive sampler. That would have left the options schema transition unverified even though cash-equity schema samples were present.
- Corrected workflow blob: `1d8991255ff284c6b9cb20c4071ab56555d18dc6`. It runs both the bounded F&O sample/page sampler and the index/equity/FII-DII sampler, uploading both JSON reports.
- Updated exact-snapshot review request: [sampler v2 review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_REVIEW_REQUEST.md).
- **Gate remains closed** pending tester review of the current workflow blob and the current sampler/test/spec blobs. No approval manifest and no current source-sample artifact exist.


- Repository-level [Research Protocol Check](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38020253978) succeeded on the latest documentation commit. It validates repository contract/literature registry only; it is **not** a run of the Gate A v1/v2 source-schema regression suites. The Gate A sampler workflow remains untriggered because the exact tester approval manifest is absent.


## 2026-10-10 — Extension 2 sampler v2 exact-snapshot PASS; one bounded run authorized

- Independent tester passed the corrected exact six-file snapshot at reviewed commit `6050908b98c53d75c10175140e84e87f48934896`; report mirrored byte-identically on tester/developer branches.
- Offline hosted suite [Run 38026024826](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026024826): **22/22 unique tests passed** (7 v1 + 15 v2). Offline-only legacy-workflow safety check [Run 38026080844](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026080844) also passed.
- Current PASS scope is one bounded Gate A source sample and upload of two JSON reports only. **Full-history acquisition and model fitting are NOT AUTHORIZED.**
- A prior unapproved legacy run [38025793938](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38025793938) fetched two single-day F&O archives and small public-page/API samples. Artifact `11659904438` is **NON-ACCEPTED EVIDENCE** due to missing authorization. No features, labels or models were produced. The unguarded legacy workflow has been replaced with offline-only tests.
- The v2 live-source workflow still requires the exact mirrored tester report digest, protected byte hashes/Git blob IDs, reviewed-commit ancestry, and successful offline tests before any source request.
- **Next gate:** create the exact hash-bound manifest for the tester-approved snapshot; once the single guarded run completes, submit both reports for separate independent artifact review.


## 2026-10-10 — Gate A artifact REQUEST CHANGES; approval revoked; corrections submitted

- Post-run independent audit rejected artifact `11660395594` from Run `38026272245`. The F&O archive and cash-equity sample schemas passed, but official sector-index CSVs failed because the parser did not recognize numeric `DD-MM-YYYY` dates, and the dated NSE FII/DII API returned current 2026 rows outside the requested July 2024 window.
- The prior Gate A approval manifest was explicitly revoked; [revocation run 38026433233](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026433233) passed the offline suite, failed the authorization check on purpose, and skipped source sampling.
- Developer corrections: v2 parser now supports `DD-MM-YYYY`; every row in a dated API response is checked against the requested date window, and out-of-window/missing dates are rejected.
- Current hosted offline tests [Run 38026502365](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026502365) passed **24 checks** (7 v1 + 17 v2).
- Current protected sampler snapshot is **NOT YET APPROVED**. A new tester code review and renewed bounded sample gate are required. No full-history acquisition or model fitting is permitted.
- FII/DII historical availability remains unresolved; continue the free-source search rather than declaring unavailable.


## 2026-10-10 — Corrected sampler code gate PASS; new Gate A run still needs manifest

- Independent tester passed the corrected eight-file sampler/workflow snapshot at reviewed commit `784474de59a050ba6229ee5cb9a708c0f74ca2dc`. Report includes the exact eight protected Git blob IDs and explicit Gate A-only scope.
- Offline run [38026629021](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026629021) passed 25 checks (7 v1 + 18 v2). The fail-closed smoke test [38026802711](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026802711) showed tests pass, revoked authorization is rejected, and source sampling is skipped.
- Prior source artifact `11660395594` remains REQUEST CHANGES; the source approval is revoked. The new code-gate PASS does not change that artifact decision.
- New free-source inventory: [Extension 2 FII/DII source discovery](sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md). Several free sources claim broader date coverage, but the date range, record count, definitions and source-vintage must be validated in separately bounded source samples.
- **Next:** create a renewed exact eight-file hash-bound manifest for one corrected source sample only. Then independently audit the new two-report artifact. No full history, features/labels or fitting.


## 2026-10-10 — Corrected Gate A sample artifact audited; overall Gate A remains OPEN

- Corrected sample run [38026993369](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026993369) passed offline regressions, exact approval and bounded source sampling. Artifact ID `11661065266`, ZIP SHA-256 `10a3fba40359c230bafa0f47c2d01be8f057e39b5eed0b70335710b59c57558a`.
- Independent tester found no remaining schema/date parsing bug in the sampled official sources. Both sector-index CSVs now pass for 2024-07-05 and 2024-07-08, all ten sector identities plus NIFTY 50 present; both cash equity dates and both legacy/UDiFF F&O samples passed.
- The dated NSE FII/DII request was correctly rejected because it returned two current 2026-10-09 rows for the requested July 2024 window. The rolling GitHub flow file had 164 unique dates (2026-01-14 to 2026-09-30), fewer than the 500-session minimum; sampled dashboard HTML did not establish the missing coverage.
- Tester report [PHASE7_EXTENSION2_GATE_A_RUN2_ARTIFACT_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_GATE_A_RUN2_ARTIFACT_TESTER.md) = REQUEST CHANGES for complete Gate A because G14/G15 source coverage is insufficient, while accepting the schema checks as bounded evidence.
- One-run source manifest has been marked spent. **No further network sampling, full-history acquisition or fitting is authorized until a new bounded free-source discovery proposal receives independent approval.**
- Free sources reviewed are inventoried at [EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md](sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md).


## 2026-10-10 — New free-source discovery proposal needed; no source access currently authorized

- Updated the source inventory with CDSL's dated FPI XLS links, the Hugging Face FII/DII CSV lead (503 lines claimed in a commit diff), SEBI FPI monthly transaction archives, and a provenance finding about the MrChartist seed script.
- A governance incident was logged: the full public MrChartist `data/history.json` (143,498 bytes) was inadvertently returned during repository source review. It is not imported or accepted. Its `seed_history.js` describes generating daily rows from monthly/yearly aggregates, so seeded values must be excluded from empirical datasets.
- **The prior Gate A manifest is spent. No further network/source probes, full history, feature/label construction or model fitting are authorized.**
- Next action: prepare a new frozen, bounded source-discovery proposal that uses byte-range requests with strict caps, official CDSL FPI samples, one HF CSV sample, and an explicit synthetic-provenance rejection rule. Independent tester must approve the spec/code before any data probe.
- Inventory: [EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md](sources/EXTENSION2_FII_DII_FREE_SOURCE_DISCOVERY_2026-10-10.md).


## 2026-10-10 — Free Flow Source Discovery 3 SPEC PASS

- Independent tester passed the frozen proposal `research/phase7/EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_SPEC.md`, Git blob `52b030e09213cb30c4de6a1633da38e6b2558b1f`.
- Report is mirrored at `research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md` on tester/developer branches.
- Decision authorizes **implementation and offline regression tests only**. No live source requests, history acquisition or modeling are authorized.
- The plan has 15 initial probes plus at most three one-hop HF redirects, 2 MiB aggregate body cap, 16 KiB max CSV-range data, strict HTTP 206/Content-Range validation, pinned commit and explicit provenance rules.
- GitHub history metadata uses directory-only `/contents/data` calls to avoid file payloads; raw `data/history.json` endpoints are prohibited.
- During proposal verification, two CDSL XLS links were opened with a web reader but the reader returned unsupported-content-type errors and provided no parsed values. Logged as non-accepted activity in ERROR_LOG and tester report.
- Next: implementation on developer branch, hosted offline tests, exact-snapshot code review. The spent prior Gate A manifest must not be reused.


## 2026-10-10 — Extension 2 Free Flow Source Discovery 3 code gate pending

- Specification gate: PASS WITH SCOPED RESTRICTIONS for implementation/offline tests only. Current spec Git blob `4e30415632545c04a2875d627afa0191afe3f383`.
- Sampler implemented: `scripts/extension2_free_flow_source_discovery_3.py`; offline tests: `scripts/test_extension2_free_flow_source_discovery_3.py`.
- Latest hosted test: [Run 38028738968](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38028738968), 27/27 offline checks passed on developer snapshot `b3a6c3dcde845923a0dba55a0f350d5e67361a76`.
- Exact code/workflow review request: [PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md).
- Separate workflows: offline tests only; guarded live probe requires an exact tester report, all six byte hashes/Git blobs, and reviewed commit ancestry. Before the one source probe it marks the manifest SPENT, preventing replay.
- No live source requests occurred. Current one-run manifest absent. Full-history acquisition, features/labels, model fitting, predictive metrics/p-values and final holdout remain blocked pending a fresh code-gate review followed by separate one-run authorization.


## 2026-10-10 — Discovery 3 updated snapshot; 29/29 offline tests passed

- Latest protected-code snapshot: `918821ba9e74342bb282fe3a86138e8aa8e29ea7`.
- Latest hosted offline test: [Run 38029034365](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029034365), **29/29 checks passed**.
- Added CDSL candidate value extraction by matching buy/sell/net labels to same-column values on the sampled equity row, while retaining status `CANDIDATE_NUMERIC_VALUES_EXTRACTED_NOT_ACCEPTED_FOR_FEATURE_BUILD` until the grouped headers are reconciled.
- Added recursive source-JSON credential redaction and signed-query redaction for non-HF URLs, plus regression tests.
- Current exact handoff: [PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md). It pins the six protected Git blobs and file-byte SHA-256 values.
- **Current gate:** isolated tester code/workflow review pending. No live source requests, new manifest or sample artifact exist. Previous Gate A manifest is spent. Full history, features/labels and modeling remain blocked.


## 2026-10-10 — Discovery 3 corrections submitted for fresh code gate

- Corrected all six tester findings from the prior REQUEST CHANGES report.
- Latest protected-code snapshot: `1706a17d268e2b139fc9dba4504f498acc4f5de0`.
- Latest offline run: [38029615734](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029615734), **32/32 tests passed**. No source network fetch occurs in this workflow.
- Exact current handoff and six protected Git/blob-byte hashes: [code review request](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md).
- Corrections include spec provenance pin, strict consistency across all date fields, explicit non-finite CSV rejection, camelCase-aware nested signature redaction, sanitized dated links, and per-path protected-blob checks at the exact reviewed commit.
- **Current gate:** new independent code review pending. No source-probe manifest exists. No live requests, history downloads, feature/label tables, model fit or result statistics have been produced.


## 2026-10-10 — Corrected Gate A resample audited; free-source discovery remains gated

- Corrected resample [Run 38026993369](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026993369) succeeded; artifact ID `11661065266`, ZIP SHA-256 `10a3fba40359c230bafa0f47c2d01be8f057e39b5eed0b70335710b59c57558a`. Independent review confirms official index CSVs now pass both dates; F&O and equity samples pass.
- NSE date-filtered FII/DII response is correctly rejected as out-of-window (2026-10-09 rows for a July 2024 request). Public mirror has only 164 dates from 2026-01-14 to 2026-09-30; no 500+ aligned-session history is established.
- The Gate A manifest is SPENT. No additional requests are authorized by it.
- Next source phase: Discovery 3 free-source feasibility only. Current code review request: [PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_CODE_REVIEW_REQUEST.md). Latest offline test run [38029615734](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029615734) passed 32/32 checks, but isolated tester review is still pending.
- **No live Discovery 3 requests, full-history downloads, feature/label generation, model fitting, metrics/p-values or final-holdout access are authorized.**


## 2026-10-10 — Free Flow Source Discovery 3 code gate

- Current protected snapshot: spec blob `4e30415632545c04a2875d627afa0191afe3f383`, sampler `34b9dcb47288d103c236a8fd34603daf66135bc4`, tests `9c2e89ff810d2820d6dacdec36fbaf0a18cf4eec`, pinned requirements `921812b1d6da657ee1de2a4b35e7ff8b43cc8ce6`, offline workflow `634f87014f334d3c4a903269a073c4e5e2786d46`, live workflow `e29f66b67bd47f488b00a708988fca708b391732`.
- Hosted offline run [38029797600](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38029797600) passed all 32 fixture regressions.
- Independent tester's fresh code-gate report: [PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3_TESTER.md). Decision: PASS WITH SCOPED RESTRICTIONS for code/workflow only; it does not authorize live requests.
- Attempt to mirror the tester report to the developer branch was blocked by platform safety checks. The source manifest has NOT been created. Do not bypass the exact-report mirror requirement.
- Before any live request: run tests on the exact reviewed snapshot, calculate byte-level SHA-256 for all six protected files, mirror the report through an allowed path, then create and validate a separate single-use manifest.
- **Full-history acquisition, features/labels, model fitting, metrics/p-values and final-holdout access remain NOT AUTHORIZED.**


## 2026-10-10 — DhanHQ data-recovery proposal submitted for independent spec review

- User reported adding GitHub Actions secret `DHAN_ACCESS_TOKEN` and requested resolution of data gaps and rerunning analyses.
- Official DhanHQ documentation reviewed: [daily/intraday historical data](https://dhanhq.co/docs/v2/historical-data/) and [authentication](https://dhanhq.co/docs/v2/authentication/). Daily historical candles can potentially improve NIFTY/index OHLCV and derivative coverage; token/data API entitlement may be time-limited or require an active Data API plan.
- Critical limitation: Dhan historical candles are instrument OHLCV/OI, not documented aggregate FII/FPI/DII cash-market flow data. The FII/DII bottleneck is not considered resolved by adding this token.
- New finite spec: `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md`; tester handoff: `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_REVIEW_REQUEST.md`.
- No Dhan request was made and the token value was not read, printed or persisted. The previous FII/DII one-run manifest is spent and cannot be reused.
- **Current gate: waiting for independent specification decision.** No live request, full-history acquisition, features/labels, model fitting, metrics or holdout access authorized.


## 2026-10-10 — Dhan adapter and guarded workflow code gate PASS

- DhanHQ recovery spec received an independent spec-only PASS; the exact 4 MiB aggregate response budget was reconciled to 64 KiB profile + 1 MiB index metadata + four 752 KiB candle responses.
- Adapter and offline suite added: `scripts/dhan_market_data_recovery.py`, `scripts/test_dhan_market_data_recovery.py`.
- Offline-only workflow: `.github/workflows/phase-07-dhan-market-data-tests.yml`.
- Guarded single-sample workflow and exact manifest validator: `.github/workflows/phase-07-dhan-market-data-live.yml`, `scripts/validate_dhan_sample_approval.py`.
- Independent tester decision: PASS WITH SCOPED RESTRICTIONS for the guarded workflow code only; it authorizes creation of one exact-hash sample manifest, not full history or modeling. Report: `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md`.
- Hosted offline run [38043020539](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043020539) passed **27/27 regressions**. Earlier fixture/assertion failures were corrected and retained in Actions/error log.
- Dhan secret has not been read or logged. No Dhan API request has yet been made. Next: create one exact manifest, let the guarded workflow validate and spend it before the single bounded sample, then independently audit the artifact.
- Dhan historical candles may fill price/index data; they do not replace the unresolved combined FII/FPI/DII aggregate flow series. No full-history acquisition, features/labels, model fitting, metrics or holdout access is authorized.


## 2026-10-10 — Dhan bounded sample artifact: REQUEST CHANGES

- Guarded run [38043148580](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043148580) passed offline tests, exact manifest validation, and marked the one-run manifest SPENT before source access.
- Artifact `11666064550` (`dhan-market-data-bounded-sample`, ZIP SHA-256 `45f2b23a0835cb6b1af52ac12913bf86062f9c82a0d3edcef4c810a3f30f38d9`) reports `BLOCKED_INSTRUMENT_METADATA` after two requests. No candle request succeeded and no price history or analysis was produced.
- Tester artifact audit: REQUEST CHANGES at `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_SAMPLE_AUDIT.md`.
- Defect: the report omitted the numeric HTTP status from the failed `/v2/instrument/IDX_I` request. Corrected adapter now records safe numeric status and request/byte counts without provider body or token.
- New regression added; hosted test run is pending. The previous manifest remains SPENT; a new exact-snapshot code review and new one-run manifest are required before any retry.


## 2026-10-10 — Dhan diagnostic correction passed; retry requires fresh manifest

- First sample Run [38043148580](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043148580) stopped after two requests at instrument metadata. Its artifact was rejected because it omitted HTTP status.
- Adapter now records numeric metadata HTTP status and safe content-type; tests verify provider body/cookies/token are not exposed.
- Offline Run [38043456200](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043456200) passed 29/29 tests.
- Tester reviewed-tree/manifest validation was tightened to compare protected blobs at both reviewed commit and current HEAD (the current code-tester report is separately digest-pinned).
- Independent tester PASS for one bounded diagnostic retry only: [code tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md).
- Previous manifest remains SPENT. Next step is recompute exact byte hashes and Git blobs and create a new one-run manifest. If metadata remains non-200, stop with its numeric status; no candle history/full history/model fitting is authorized.


## 2026-10-10 — Dhan diagnostic retry 2: HTTP 302, redirect-host proposal pending

- Run [38043667443](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043667443) passed the manifest/hash gate and spent the one-run manifest before source access.
- Profile request returned HTTP 200, token valid and Data API plan active. `GET /v2/instrument/IDX_I` returned HTTP 302; no redirect was followed, no candle request occurred.
- Artifact ID `11667455094`, ZIP SHA-256 `f388a9844db92836ec6551e2e442e207dc8d504bc9ae198df860117a2aabc68e`. Independent audit: `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_SAMPLE_AUDIT_2.md`, REQUEST CHANGES.
- New finite proposal: `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md`, review request `research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_REVIEW_REQUEST.md`. It proposes one request that reports only scheme/hostname, without following the redirect or storing Location path/query.
- No price candles, options data or FII/FPI/DII flows were obtained. No prediction analyses were rerun. Both prior Dhan manifests are spent.


## 2026-10-10 — Dhan redirect-target diagnostic code gate PASS

- Official Dhan profile confirmed token valid and Data API plan active, but `GET /v2/instrument/IDX_I` returns HTTP 302. The workflow correctly does not follow it.
- New spec `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md` and tester report `research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_TESTER.md`.
- Adapter now extracts only redirect scheme/hostname, rejects malformed hosts and marks non-HTTPS targets unverified; no raw Location path/query is persisted.
- Dedicated one-request workflow: `.github/workflows/phase-07-dhan-redirect-probe-live.yml`; validator: `scripts/validate_dhan_redirect_probe_approval.py`.
- Hosted [Run 38044225274](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044225274) passed 38/38 offline regressions.
- Independent tester PASS authorizes one exact-hash redirect-target-only request after a new single-use manifest. It does not authorize following the redirect or requesting candles/history. Existing manifests are spent.


## 2026-10-10 — Current resume checkpoint: redirect probe re-review

- Research remains prediction-only in Phase 7. Existing model-family/horizon results are unchanged; no candidate has met the registered significance gate, and no option strategy test is authorized.
- Dhan profile check returned HTTP 200 (token valid, Data API plan active); the index instrument metadata endpoint returned HTTP 302. The redirect has never been followed; neither of the guarded samples obtained candle data. The combined FII/FPI/DII aggregate-flow series is still unresolved.
- The redirect-host-only diagnostic specification was approved. Developer code now parses HTTPS-only host metadata, rejects malformed/control-character URLs and credential-bearing redirects, only parses Location on 3xx, enforces a one-request/1 KiB budget, and avoids raw Location/body/token output.
- Dedicated workflow manual dispatch requires `confirm_probe=true`; its default is false. Exact-snapshot review must include that workflow, the manifest validator, source and tests.
- Hosted offline suite [Run 38044495634](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044495634) passed. A guarded attempt [Run 38044387209](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044387209) passed all 38 offline regressions but stopped at the validator because the new single-use manifest is intentionally absent; secret injection and source request were skipped.
- **Current gate: waiting for independent tester review of the exact corrected snapshot. No READY manifest exists.** Only after tester PASS and a matching hash-pinned manifest may the one redirect-host-only diagnostic run; no redirect follow, instrument-master download, candle/history calls, model fit, or holdout access is authorized.


## 2026-10-10 — Retry after redirect-workflow failures

- Resolved prior parser/test issues and added regression checks ensuring manifest pushes cannot trigger live source access.
- Removed the automatic `push` trigger from `.github/workflows/phase-07-dhan-redirect-probe-live.yml`; the diagnostic now requires manual workflow dispatch with `confirm_probe=true` (default false). This closes the last identified automatic-trigger bypass.
- Latest offline suite [Run 38044701520](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044701520) passed on developer commit `9bfd1d61c05f8658d5b6165759a735e317740328`.
- Independent tester PASS is recorded in [the exact-snapshot report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_TESTER.md). It is limited to code/workflow only; live request authorized: NONE.
- No redirect manifest exists. Earlier manifests remain SPENT. The current connector does not expose a workflow-dispatch action, so I have not fabricated a successful live run or followed the HTTP 302. No candle history, option history, FII/FPI/DII flow, model rerun or strategy evaluation occurred.
- Next bounded step: generate a new exact-hash one-use manifest, then explicitly dispatch the manual-only workflow with confirmation through an authorized GitHub Actions dispatch capability. Until that happens, no source request is authorized.


## 2026-10-10 — One-use redirect manifest prepared; manual dispatch pending

- Created `research/gates/DHAN_REDIRECT_TARGET_APPROVAL.json` after pinning SHA-256 and Git blob IDs for the ten required files, reviewed commit, and tester report. The permitted scope is one request to record redirect scheme/hostname only, capped at 1 KiB; no redirect follow, candles/history, full-history access, or model fitting.
- The dedicated workflow has no push trigger. Manifest creation did not make a source request; manual `workflow_dispatch` with `confirm_probe=true` is required, and the manifest must validate and be spent before token injection.
- **Current state: READY manifest prepared, but runtime validation and live diagnostic have not run.** The available GitHub connector exposes inspection and rerun actions but no workflow-dispatch action. No request has been attempted and no market data has been downloaded. Do not infer validation from the manifest READY field alone.


## 2026-10-10 — Hosted log diagnosis and exact manifest-pin verification

- Retrieved job logs for failed guarded run [38044387209](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044387209). All 38 offline regressions passed; manifest validation failed with `FileNotFoundError` because the run's older push-triggered checkout did not contain `research/gates/DHAN_REDIRECT_TARGET_APPROVAL.json`.
- The confirmation step was skipped on that push event. Manifest spend and the live source step were skipped too. This run made no Dhan request and is non-evidence.
- Checked the current developer branch's ten protected file Git blob IDs against the READY manifest; all ten matched the manifest's pinned blob IDs. This is a repository-content cross-check, **not** a runtime execution of the validator and does not prove the SHA-256/ancestry checks pass on the hosted runner.
- Current manifest remains one-use and scoped to one request recording redirect scheme/hostname only (maximum 1 KiB), with no redirect follow, candles/history, or model fitting. The workflow is manual-dispatch-only.
- Current GitHub connector has no workflow-dispatch action. No unsafe trigger was added, no historical run was rerun, and no live request was made. Continue only through a supported explicit manual dispatch; do not infer source feasibility or alter prediction conclusions.


## 2026-10-10 — Resume audit: redirect-probe authorization remains blocked

- Re-read the developer branch status, research log, chat log, error log, guarded workflow, manifest validator, redirect-probe specification and the isolated tester's exact-snapshot report before proceeding.
- Independent tester report `PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_TESTER.md` remains **PASS WITH SCOPED RESTRICTIONS — code/workflow only; live request authorized: NONE**. It is bound to developer commit `9bfd1d61c05f8658d5b6165759a735e317740328`.
- Cross-checked the current `phase-07-developer` Git blob IDs for all ten protected files in `DHAN_REDIRECT_TARGET_APPROVAL.json`; all ten matched the manifest. This is a repository-content cross-check only, not execution of the workflow's SHA-256/ancestry validator.
- Manifest still reads `READY`; the hosted validator has not run, and the one-request diagnostic has not run. No source request or market data acquisition occurred.
- Current GitHub connection exposes workflow run inspection and rerun operations but no `workflow_dispatch` operation. The live workflow is intentionally manual-only and requires `confirm_probe=true`; no trigger was weakened and no old push-event run was misrepresented as a fresh diagnostic.
- **Disposition:** remain in Phase 7 prediction research only. No new data, predictions, statistical results or strategy conclusions are accepted. Do not follow the HTTP 302 or request candles/history under this manifest. A supported authorized manual dispatch and independent audit of the resulting artifact are required before any next data step.

**Developer → Tester:** Independently verify that this checkpoint preserves the role boundary and does not treat the manifest pin check as runtime authorization. If a manually dispatched run later exists, inspect its exact run/commit, manifest-spend step, HTTP status, request/byte counters and artifact redaction before issuing a separate artifact decision.


## 2026-10-10 — Dhan redirect-target probe run #9

- Run: [#9 / 38047946667](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38047946667), manually dispatched on `phase-07-developer`, commit `c9fb50e09563bb4c35870f73d17ac73fcfd3abc1`; workflow conclusion: success.
- Offline regression suite: 38/38 passed. Exact one-request manifest validation passed; the one-use manifest was committed as SPENT before the source request.
- Diagnostic report artifact: [dhan-redirect-target-probe](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38047946667/artifacts/11668017741), 340-byte ZIP, SHA-256 `c7a04f1b33f31840780cdf2a3ca74ff512f1ce7ee9d7ff97378d0c900f04cc12`.
- Artifact fields: `http_status=302`, `redirect_scheme=https`, `redirect_host=s3.ap-south-1.amazonaws.com`, `request_count=1`, `bytes_read=0`, `status=REDIRECT_TARGET_RECORDED`. No redirect was followed and no price-history payload was acquired.
- Automatic artifact preflight passed in audit run [#473 / 38047812286](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38047812286); the pinned independent tester job was skipped because this report type is not yet an approved empirical data artifact. Thus independent tester sign-off remains pending.
- **Gate decision:** diagnostic succeeded within its narrow scope, but it only identifies the HTTPS redirect host. Do not follow the redirect or request market data under this authorization. A separately reviewed next-step plan/gate is required before any source request.


## 2026-10-10 — Run #9 independently reviewed; Extension 3 proposed

- Independent tester report [PHASE7_EXTENSION2_DHAN_REDIRECT_PROBE_RUN9_TESTER.md](gates/PHASE7_EXTENSION2_DHAN_REDIRECT_PROBE_RUN9_TESTER.md) was committed to isolated `phase-07-tester` at `76f73b8003367261b4a27577a0f7244bdcbcbfb2`: **PASS WITH SCOPED RESTRICTIONS — diagnostic artifact only**.
- The tester independently inspected run #9 logs and the 340-byte artifact: HTTP 302, HTTPS hostname `s3.ap-south-1.amazonaws.com`, one request, zero body bytes, no redirect-follow, no price data. Offline tests 38/38 passed and the manifest was spent before the request.
- Official Dhan documentation review found directly documented instrument-master CSV URLs: compact `https://images.dhan.co/api-data/api-scrip-master.csv` and detailed `https://images.dhan.co/api-data/api-scrip-master-detailed.csv` ([official instrument docs](https://dhanhq.co/docs/v2/instruments/)). This was public documentation research only; no request/download occurred.
- Developer proposal [Extension 3 — Official Dhan Instrument-Source Validation Plan](phase7/EXTENSION3_DHAN_OFFICIAL_INSTRUMENT_SOURCE_PLAN.md) committed at `21c70a054c4272d2280da5872858e0d52934103d`. It is PROPOSED only and authorizes no network request.
- **Next gate:** independent tester review of the Extension 3 proposal. No live request, CSV download, price history, modeling, or holdout access is authorized. The prior redirect manifest remains SPENT and must not be reused.


## 2026-10-10 — Extension 3 proposal passed; offline implementation submitted

- Independent tester proposal review [PHASE7_EXTENSION3_DHAN_INSTRUMENT_SOURCE_PLAN_TESTER.md](gates/PHASE7_EXTENSION3_DHAN_INSTRUMENT_SOURCE_PLAN_TESTER.md) on `phase-07-tester` commit `5f653466523bc92f8c9a7e59f79a9a2ff04f1040`: **PASS WITH SCOPED RESTRICTIONS — proposal/documentation gate only**.
- Developer added `scripts/dhan_instrument_master.py`, `scripts/test_dhan_instrument_master.py`, and `.github/workflows/phase-07-dhan-instrument-master-tests.yml`. The adapter has no HTTP client; it only validates supplied bytes and atomically caches validated CSVs. The CLI explicitly reports `OFFLINE_VALIDATION_ONLY`.
- Offline test workflow [38048191811](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38048191811) and protocol check [38048191923](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38048191923) were queued and then observed in progress at checkpoint time; outcomes not yet accepted.
- No CSV request, download, secret use, cache population, price history, model fitting or holdout access occurred.
- **Next gate:** wait for hosted offline tests; fix any failures; then submit the exact implementation snapshot to independent tester code/workflow review. Only after that report may a new one-use manifest be considered. The Extension 2 manifest remains SPENT.


## 2026-10-10 — Extension 3 offline code gate passed

- Hosted offline workflow [38048191811](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38048191811) succeeded: **9 instrument-master offline tests passed**; CLI reported `network_enabled=false`.
- Research Protocol Check [38048191923](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38048191923) passed repository contract and literature-registry checks.
- Independent tester report [PHASE7_EXTENSION3_DHAN_INSTRUMENT_SOURCE_CODE_TESTER.md](gates/PHASE7_EXTENSION3_DHAN_INSTRUMENT_SOURCE_CODE_TESTER.md), tester commit `a7a77f790bd407f1ac72056e5fab7cd7c784e2b6`: **PASS WITH SCOPED RESTRICTIONS — offline validator/cache foundation only**.
- New adapter performs offline CSV validation and atomic cache writes only. No live CSV was fetched and no cache was populated. The 8 MiB cap is provisional; actual source size remains unknown.
- **Next gate:** developer may prepare a separate exact-URL fetch adapter with redirects disabled, no credentials, strict timeout/content-type/byte checks and fail-closed behavior, plus mocked offline tests. It must be submitted for independent code/workflow review. No live request or new manifest yet.
