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
