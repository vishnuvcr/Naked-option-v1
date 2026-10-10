# PPR-4 Alternative Proposal — Prospective Sealed Holdout After Freeze

**Date:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Status:** **PROPOSAL ONLY — TESTER REVIEW REQUIRED**  
**Current PPR-4 decision remains:** `BLOCKED_GATE_NO_MACHINE_READABLE_BOUNDARY_FOUND`

This proposal does not create a split, download data, accept a modelling panel, build features/labels, fit a model, or open any holdout. It is a response to the metadata finding that no historical holdout boundary can be proven.

## 1. Problem statement

Repository history includes prior Phase 7 results and prose stating that a final holdout remained unopened. The prior available-global runner uses expanding training prefixes, 20-session test blocks and a purge of horizon labels, but those rolling test blocks do not identify a separate sealed final-holdout set. The current repository also lacks a machine-readable holdout manifest with a split ID, date boundary and/or row-ID hash.

We must not retrospectively select some already evaluated historical rows and call them untouched. For this proposal, **every existing historical observation through the last complete session available when the final configuration freeze is approved is classified as development-only**, regardless of whether it appears in an earlier run, old result artifact or research cache.

## 2. Proposed solution: prospective forward-only holdout

Create a new forward-only holdout after separate tester approval. It will begin on the first official NSE session whose market decision cutoff occurs after the approved configuration/source/code freeze timestamp. The actual calendar date and the deterministic official-session row key must be computed from the frozen NSE calendar **after the freeze has been approved and before any future holdout label is accessed**.

### 2.1 Boundary identity

The future machine-readable `PPR4_PROSPECTIVE_HOLDOUT_MANIFEST.json` must include:
- a new immutable `split_id`, protocol version, freeze-commit SHA and UTC approval timestamp;
- the official NSE calendar source ID, version/hash and deterministic first eligible decision-session key;
- an explicit development cutoff and the rule defining the first post-freeze holdout decision origin;
- the exact candidate/configuration manifest SHA, source-eligibility manifest SHA, code/workflow/dependency hashes and feature schema version;
- the forecast-origin index rule, forecast ledger partition/ID, point-in-time source snapshot IDs and append-only prediction-manifest hash;
- explicit access controls stating that outcome labels/returns and final scoring outputs are unavailable to the development/fitting job until the holdout maturity/release gate passes.

Do not populate a calendar date from assumptions or a weekday calendar. If the official exchange-session calendar and exact release timestamp are not available, remain `BLOCKED_GATE`.

### 2.2 Fixed horizon and stopping rule

Use **252 consecutive eligible NSE decision-origin sessions** as the finite final holdout. This aligns with PPR-3's `minimum_valid_rows=250` requirement and spans roughly one trading year. Add a **10-session label-maturity tail** after the last forecast origin so every horizon (h in {1,2,3,5,10}) has a fully matured realized outcome. The exact first/last official session keys are generated and hashed before the first holdout-origin forecast; the stopping rule is based on session count, not a discretionary calendar end date.

If fewer than 250 valid common-origin observations remain for a registered confirmatory family because of non-market source outages, that family is `NOT_ESTIMABLE` and no candidate is promoted. No alternative date window is selected after seeing outcomes. A missing source or invalid timestamp must trigger the predeclared abstention/`BLOCKED_DATA` logic, not synthetic values.

### 2.3 One-time model freeze and prediction capture

Before the first holdout-origin forecast:
1. Freeze the exact eligible subset of PPR-3 configuration/pipeline/horizon cells based **only** on source documentation, coverage, point-in-time availability, development-period code/data validation and predeclared gates. Holdout outcomes must not determine eligibility.
2. Freeze hyperparameter choices, feature transforms, class order, probability conversion, seeds, all baselines, candidate family membership, and inference script/code hashes. No new candidate may enter the final test.
3. Fit each eligible model/configuration × approved pipeline × horizon × predeclared seed once on the purged pre-holdout development prefix, using only source rows available at the freeze cutoff. The fitted parameters are frozen for the entire holdout; feature inputs may update only from point-in-time values available at each decision timestamp.
4. At each decision cutoff, write a prediction-only record containing split ID, origin session, target/horizon, model/config ID, probability vector or point forecast, source snapshot hashes, code/config hashes, decision timestamp and output hash. Commit or otherwise immutably seal the record **before the future label endpoint matures**. The daily prediction job must not calculate or expose realized returns, labels, test metrics or candidate ranks.
5. Do not inspect running aggregate holdout metrics, tune parameters, alter source selection or promote a candidate during the 252 origins. Operations monitoring may check schema/source availability only and cannot expose outcome values or predictive scores.

### 2.4 Label release and independent audit

Only after all 252 forecast origins and the 10-session maturity tail are complete:
1. Freeze and hash the full prediction ledger, source-vintage manifest, row-origin grid and code/config artifacts.
2. Have the tester verify that prediction records were captured before their respective outcome endpoints matured and that the manifest covers the entire predeclared grid.
3. Release outcomes to a **separate scoring job** that reads the sealed ledger and outcome series only after the tester gate. Recompute labels, losses, familywise maximum-statistic bootstrap, adjusted (p)-values and simultaneous intervals from the frozen prediction ledger.
4. The tester independently reproduces all results from the immutable artifacts and determines whether any method clears the preregistered statistical and data-integrity gates. Negative or non-significant results must be retained; no candidate is promoted by accuracy alone.
5. The holdout becomes spent after this single final score release. It cannot be reused for retuning or further model selection.

No option P&L or strategy inference is part of this holdout protocol. A separate approved economic gate would still need current Paytm Money brokerage/statutory charges, bid/ask spread, slippage, lot/contract validity and fill constraints.


### 2.5 Confirmatory family completeness is fail-closed

The eligible confirmatory model/pipeline/horizon set and family membership must be fixed before the first prospective holdout origin using only source availability, license, timestamp coverage and development-period tests. A source that fails those checks is labelled `BLOCKED_DATA` before the final candidate manifest is frozen.

After the freeze, a candidate may not be silently removed because future source rows are missing or its forecast is inconvenient. If a frozen candidate cannot produce a finite registered output on a common confirmatory origin, record an explicit abstention/reason and preserve the row. Under the existing PPR target/inference contract, a missing planned candidate/horizon means the family is `INCOMPLETE_NOT_PROMOTABLE`; do not pairwise-drop the row, translate an abstention into a made-up probability, or issue a confirmatory family p-value/promotion from a smaller subset. Per-candidate descriptive coverage may be reported separately with its abstention rate, clearly marked non-confirmatory. The 250-row minimum does not waive this family-completeness rule.

The boundary selector is intentionally conservative: use the first official NSE session whose local IST trading date is strictly later than the Asia/Kolkata local date containing the freeze approval commit. Thus the commit-date session is excluded even if its close has not occurred; the exact first session is computed from the frozen official calendar after approval and before any holdout outcome is available.


### 2.6 Cumulative fit-call budget and phase order

The prospective final evaluation is **not** another hyperparameter search. Its eligible model/feature/horizon membership and parameter settings are frozen only after the development-period run and its independent artifact audit are complete. The run plan is:
1. Finish the approved PPR-3 development-period screening and independent metric/inference audit under its existing 4,344-fit upper bound (3,564 conservative outer fits plus 780 inner-fold tuning fits).
2. Decide and freeze the final candidate manifest using only development-period evidence and the predeclared gate. Record blocked candidates and all reasons. The candidate set is not expanded in the final holdout.
3. Fit the frozen final candidate model set once on the purged development prefix, using the already chosen settings; three predeclared seeds remain a conservative upper bound for each cell. No second tuning search, feature search or calibration search occurs in the final fit.
4. Under the current 1,188-cell universe, the conservative final-fit bound is another 3,564 estimator fit calls. Across development screening (4,344) plus final model fitting (3,564), the cumulative model fit budget is **7,908**, below the repository-wide 8,000 cap. This assumes no additional uncounted calibration/feature-selection estimators. Any implementation that requires extra fitted estimators must stop before execution and submit a budget amendment for tester approval.
5. The final model/configuration/source/code freeze commit and UTC timestamp are pinned before the first prospective forecast origin. The origin window starts on the first official NSE session whose IST trading date is strictly later than the IST local date containing that freeze commit. The freeze must happen after the development-period result audit, not before development outcomes have been used for method selection.

The budget is an upper bound; using fewer than all 1,188 cells reduces it. The actual eligible cells, fit count, and each estimator/preprocessing fit must be listed in the new final-run manifest before any fit. Do not reuse development-period predictions as final-holdout predictions.

### 2.7 Common-origin rule for the future score

Before the scoring job may read realized values, the tester freezes the 252 planned NSE forecast-origin keys and verifies prediction-ledger presence, source/target-row existence and endpoint maturity from metadata/status flags only. No actual return/label value may be opened to decide the row index. For one confirmatory family, a row may be declared globally unavailable only when its target endpoint value is objectively missing/corrupt for the entire family and the reason is logged before scoring; that row is excluded for all candidates in that family. Candidate-specific missing forecasts may not be used to shrink the row grid. If any frozen candidate has a missing/invalid probability/point forecast on a planned common origin, the applicable family is `INCOMPLETE_NOT_PROMOTABLE` under the current PPR inference contract, with no confirmatory (p)-value or promotion. Candidate coverage/abstentions may be reported descriptively but not substituted into the confirmatory family statistic.


## 3. How this differs from the prior design

| Issue | Legacy Phase 7 | Proposed final holdout |
|---|---|---|
| Evaluation scheme | Expanding walk-forward; 20-session test blocks; horizon-label purge | One frozen set of model parameters; 252 prospective origins |
| Boundary | Existing report says holdout is unopened, but no machine-readable final boundary has been located | First eligible official NSE session after an approved, hash-bound freeze commit; exact session IDs and hashes created before labels mature |
| Predictions | Historical predictions and metrics already exist for previous development tests | Append-only future prediction ledger sealed before every target endpoint |
| Selection | Used for development-period screening | No selection/tuning during the prospective holdout |
| Final outcome release | Not proven as a separate row/date partition in current metadata | Separate tester-approved one-time outcome release after 252 origins + 10-session maturity tail |
| Reuse | Old historical results remain development evidence | Final holdout is spent after the single scoring/audit pass |

The old test-block results are not relabelled as a final holdout. PPR-3's fixed-fit configuration universe may be used to define the prospective model set only after all intervening data/code gates have passed.

## 4. Important limitations and operational cost

- This requires a future forward-data collection period. It cannot produce a final-holdout performance result immediately from the already-exposed historical period.
- The 252-origin duration is chosen to be consistent with the existing minimum valid sample; this gives the project a finite stop rule but does not guarantee statistical power for every class or source family.
- If an approved free source cannot provide a genuine PIT stream and immutable per-decision snapshot, its dependent candidate must be blocked before the final candidate manifest is frozen.
- The Dhan one-use sample permission is spent and is not reused. No data source, including Hugging Face, is automatically authorized to be downloaded by this proposal.
- A future split manifest must contain real IDs/hashes generated by the approved process. This document contains no invented boundary date, dataset ID or row-ID hash.

## 5. Approval requested

**Requested tester decision:** `PASS WITH SCOPED RESTRICTIONS` for the *design only*, or `REQUEST CHANGES`. A design-only PASS must not authorize downloads, model-panel acceptance, model fitting, prediction recording or label release.

If approved, the next developer phase is to prepare a separate PPR-4 source acquisition/cache proposal with exact free/official sources, legal terms, fields, history ranges, PIT rules, cost/caching policy and sample limits. That proposal needs another independent exact-snapshot decision before any source-specific byte request. After data/code validation and a new final candidate freeze, the future prospective holdout manifest and forecast-only capture workflow need a separate explicit gate.

**Developer → Tester:** Review this prospective-holdout design for data snooping, session-boundary determinism, horizon-label maturity, immutability, fit/selection leakage, and one-time release control. Authorize the design only if those guarantees are precise; do not authorize any data or model operation.

**Tester → Developer:** If you approve this design, scope that PASS only to drafting the next source-acquisition/cache manifest. If rejected, identify changes. In either case, keep source downloads, model execution and holdout values/labels blocked.
