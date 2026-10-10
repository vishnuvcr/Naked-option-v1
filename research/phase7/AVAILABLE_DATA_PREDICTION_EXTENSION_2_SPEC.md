# Phase 7 Available-Data Prediction Extension 2 — Frozen Proposal Pending Tester Approval

**Status: PROPOSED — NOT AUTHORIZED FOR EMPIRICAL EXECUTION**  
**Branch roles:** developer work on `phase-07-developer`; independent review on `phase-07-tester`.  
**Purpose:** continue prediction-only testing within already registered method families that were not part of Run #44. This amendment does not alter or reopen the prior frozen Phase 7 specification, Run #44 artifact, or final untouched holdout.

## 1. Research question

Do point-in-time-safe NSE cash-market breadth, sector leadership, institutional-flow and NIFTY option open-interest/volume features improve out-of-sample NIFTY direction probability forecasts beyond a causal historical-rate baseline and the already-screened cross-market daily-price candidates?

### Aims

1. Test the registered but not included in Run #44 methods G03, G14, G15, G17, F03, F04 and F05 using free/public exchange reports where a defensible historical series can be reconstructed.
2. Measure whether the features add predictive information, not whether an options trading strategy is profitable.
3. Retain explicit source-vintage, availability, missingness and contract-universe provenance; do not synthesize missing values.
4. Control the additional method/horizon search with one global maximum-statistic family test.

### Objectives

- Build a dated source inventory and validate archive coverage before model fitting.
- Produce one canonical daily feature table with a feature-by-feature publication/availability rule.
- Use the same frozen NIFTY target, forecast horizons and causal walk-forward mechanics as the available-data extension.
- Report every registered candidate/horizon cell, including `BLOCKED_DATA` reasons, paired-baseline metrics, and abstention coverage.
- Obtain a separate independent tester code/data gate and then a separate exact-snapshot execution approval before any empirical batch.

## 2. Frozen candidate universe

Exactly seven candidate methods are registered for this extension:

| Candidate | Registry ID | Frozen definition | Intended source |
|---|---|---|---|
| Sector leadership | G03 | Equal-weight mean of prior-session sector-index 1-session and 5-session log returns minus the corresponding NIFTY returns. Use a frozen named set of NSE sector indices; all set members must be present for that row. No row-wise reweighting. | NSE historical index data |
| FII/FPI net flow | G14 | Prior-session combined FII/FPI cash-market net value, normalized by prior-session NIFTY traded value; retain raw value as diagnostic. Use the same official report series/vintage throughout. | NSE FII/FPI & DII report archive |
| DII net flow | G15 | Prior-session DII cash-market net value, normalized by prior-session NIFTY traded value; retain raw value as diagnostic. | NSE FII/FPI & DII report archive |
| Advance/decline breadth | G17 | Prior-session net breadth ((advances-declines)/(advances+declines)), plus its causal 5-session sum. If denominator is zero or archive row is absent, the candidate abstains. | NSE Advances/Declines archive |
| Put/call open-interest ratio | F03 | (log((1+sum put OI)/(1+sum call OI))) for NIFTY index options with 1–45 calendar days to expiry at that source session close. Sum across strikes and all eligible expiries; do not mix stock options or futures. | NSE F&O UDiFF common bhavcopy |
| OI-change acceleration | F04 | First difference of the prior-session log total NIFTY index-option OI within the same 1–45 DTE window, and its causal one-session change. Use the same frozen expiry eligibility and option-type universe for each day. | NSE F&O UDiFF common bhavcopy |
| Volume/OI pressure | F05 | Difference between aggregate put and call (log(1+volume/OI)) for NIFTY index options within the same 1–45 DTE window. Contracts with missing/non-positive OI are excluded and counts are recorded; if the eligible side is absent, abstain. | NSE F&O UDiFF common bhavcopy |

No other candidate, feature, source, transformation, expiry window, or threshold may be added after inspecting evaluation results. No candidate is an option trade or strategy.

### Frozen sector-index set for G03

Use only the historical series for these named broad sector indices if free archive coverage and identity can be verified: NIFTY Auto, Bank, Financial Services, FMCG, IT, Media, Metal, Pharma, Realty, and Energy/Oil & Gas. The full set is frozen; if any member cannot be acquired and validated over the required period, G03 is `BLOCKED_DATA` for the run rather than dynamically changing the set. The exact symbol-to-index mapping must be recorded before fitting.

## 3. Source discovery and data-vintage rules

Official free source leads identified before implementation:

1. NSE F&O reports: https://www.nseindia.com/all-reports-derivatives  
   The report catalogue exposes the F&O UDiFF Common Bhavcopy Final ZIP, participant-wise OI and volume reports, and FII derivatives statistics. The current amendment uses the UDiFF bhavcopy for F03–F05; participant-wise OI is a validation/source-discovery lead only and is not an additional candidate in this frozen family.
2. NSE historical capital-market reports: https://www.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives  
   The catalogue exposes historical index data and Advances/Declines archives, which are the primary G03/G17 source leads.
3. NSE FII/FPI and DII reports: https://www.nseindia.com/reports/fii-dii  
   The page exposes downloadable CSV reports for NSE-exclusive and combined NSE/BSE/MSEI cash-market activity. It states that the activity is provisional and may be revised. Choose one series before fitting; the proposed primary series is combined NSE/BSE/MSEI data. Retain the source-vintage caveat and do not silently substitute NSE-exclusive values for missing combined values.

External research pages and archive endpoints may change. A source is not considered acquired until its URL, retrieval timestamp, content hash, schema, coverage, units, and any revision/provisional status are recorded in a manifest. No paid source may be considered until the documented free-source search has been completed. No claim is made here that the archives have already been bulk-downloaded or that full coverage has been verified.

## 4. Point-in-time policy

- Decision session is NIFTY session (t); all predictor inputs must come from a source session strictly earlier than (t). Same-date EOD flow, breadth, sector or options observations are forbidden even if the file is available after the close.
- Daily source session dates must be derived from the source's exchange-local date, not a UTC date truncation.
- For F03–F05, source data must be from the prior completed NSE session. The expiry window is evaluated as-of that source session; future expiry metadata may be used only if it was already listed/known at that source session. No hindsight-selected “nearest expiry” label.
- FII/FPI and DII report values are provisional and potentially revised. Since historical point-in-time vintages may not be archived, the result must explicitly identify this as a vintage limitation; the strict one-session lag prevents same-session publication leakage but does not prove that later revisions were unavailable historically.
- No backward-fill. No interpolation across missing sessions. No feature-specific future data. No current constituent list may be used to reconstruct a historical index's constituents.
- Corporate-action adjustments and index definitions must be logged for any sector data. For options, only daily contract-level price/OI/volume are used as predictive features; no option premium P&L or fill assumptions are estimated in this phase.

## 5. Labels, walk-forward model and comparator

- Target: sign of NIFTY close-to-close future log return for (H in {1,2,3,5,10}) NIFTY sessions.
- Forecasting model: the same registered causal logistic-regression estimator and training-only scaling as the available-data extension; no tuning or candidate-specific hyperparameter search.
- Minimum training prefix: 252 eligible observations; chronological test blocks: 20 sessions; purge any training label whose outcome overlaps the test decision interval.
- Baseline: positive-label rate estimated only from the eligible purged training prefix at each walk-forward fit.
- All metrics for a candidate and its baseline must use exactly the same paired eligible rows. Report sample size, coverage/abstention, positive rate, accuracy, balanced accuracy, ROC AUC, PR AUC, Brier, log loss, confusion counts, calibration diagnostics where defined, and mean realized future log return when predicted up.
- The already screened G13/G06/G02 candidates may appear as labelled descriptive reference rows only; they are not retuned, and they are not added as new candidate hypotheses in this extension.

## 6. Statistical analysis and multiplicity control

The primary statistic is Brier improvement over the causal training-rate baseline: baseline squared loss minus candidate squared loss. Positive values favor a candidate.

Use one global maximum-statistic family test across all **35 candidate/horizon combinations** (7 methods × 5 horizons), not five separate uncorrected winner searches:

1. Align the date rows across all horizons; use the common date grid where all target labels are observed. For each method/horizon, an unavailable forecast is represented as zero improvement for family inference (equal to benchmark loss), while its individual metrics are calculated only on its paired eligible rows.
2. Compute each candidate/horizon's mean Brier improvement; the observed global statistic is the maximum across all 35 cells.
3. Recenter each cell's row-level Brier differential by its own observed mean under the no-improvement null.
4. Use a common moving-block bootstrap over the date axis: seed 42, 500 replicates, block length 20 sessions, overlapping contiguous blocks, and the same sampled date indices for all 35 cells.
5. Report one global family p-value using ((1+#{T_bge T_{obs}})/(500+1)). No separate best-candidate p-value is reported as confirmatory. The registered confirmatory threshold is (alpha=0.05).
6. Descriptive metrics may rank candidates for discussion but cannot select or promote them if the global family test fails. The final untouched holdout remains unopened.

A result validator must recompute all metrics from a row-level panel, verify source/feature/availability hashes, candidate and baseline pairing, label/return sign, missingness, the global bootstrap statistic and p-value, and the complete 35-cell grid. Every unavailable method must have a non-empty `BLOCKED_DATA` reason. No silent dropping of candidates or cells.

## 7. Source/cache engineering and regressions

- Acquisition modules must be import-safe.
- Use a deterministic local cache keyed by source identity, schema version, and coverage contract. Reuse a valid hashed cache; reacquire only when missing, stale, malformed, or hash-mismatched. Preserve raw downloaded source files plus normalized canonical tables and manifests.
- Cache manifests must include URL/source identity, retrieval timestamp, source date range, row count, timezone, revision/provisional caveat, schema version, SHA-256, and the cache decision.
- Regression fixtures must cover duplicate dates/contracts, changed contract universe, wrong units, missing calls/puts, zero OI, expired contracts, source-session timezone boundaries, same-day leakage mutation, source revisions, missing-flow days, missing breadth denominator, missing frozen sector constituent, and cache hash mismatch.
- Workflow must protect this spec, all acquisition/features/predictor/validator/tests/dependency files and the workflow itself. Regression and hash reporting precede authorization; empirical execution is fail-closed behind a fresh independent tester report/approval manifest bound to the exact source snapshot.

## 8. Gate sequence and stop conditions

1. **Gate A — source feasibility only:** acquire a small, deterministic sample of archive dates and validate schemas/coverage. No target labels, model fitting, or predictive metrics.
2. **Gate B — independent tester review:** tester independently checks the source inventory, feature formulas, time availability, contract filtering, test design and multiplicity plan. If REQUEST CHANGES, developer fixes and resubmits.
3. **Gate C — implementation and regressions:** build acquisition/normalization, feature generation, predictor, result validator and tests. Hosted regression must pass.
4. **Gate D — exact-snapshot execution approval:** independent tester reviews protected hashes and actual regression run. Only then may one empirical batch run.
5. **Gate E — immutable artifact audit:** tester independently recomputes data hashes, panel metrics and the global max-statistic bootstrap. If no significance or an integrity defect appears, record it and do not promote a model.
6. No Phase 8 strategy/P&L work, no final-holdout opening, and no trading recommendation is authorized by this proposal.

## 9. Expected limitations

- NSE historical archives may be rate-limited, reorganized or subject to revised files.
- FII/FPI and DII series are provisional/revisable; exact historical publication vintages may be unavailable.
- Historical option contract universe, expiry calendar, lot-size changes, weekly-expiry rule changes and EOD OI conventions must be normalized without lookahead.
- Daily closing price/OI/volume features do not capture intraday option spreads or executable liquidity.
- A statistically significant directional forecast would still not imply positive option P&L. Paytm Money brokerage/taxes, spread, slippage, liquidity, position sizing, drawdowns and realistic entry/exit rules are outside this prediction-only amendment.

## 10. Current decision

This is a proposal only. No source has been accepted, no new feature table or model output exists, and no empirical execution is authorized until the independent tester passes this exact specification and the source-feasibility/code gates.

**Developer → Tester:** Independently review this proposal against the registry and previous phases. Check source availability assumptions, feature formulas, point-in-time timing, fixed universe, contract/expiry filters, family multiplicity, bootstrap alignment, and stop conditions. Return PASS or REQUEST CHANGES with concrete corrections; do not authorize empirical execution from a spec-only pass.

**Tester → Developer:** Do not download full history or fit models until the spec/source-feasibility gate is approved. Any change to candidate universe, timing, expiry filters, or family test must be versioned and independently approved before results are viewed.
