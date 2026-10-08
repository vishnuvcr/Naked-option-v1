# Phase 8 Specification — Independent Tester Review

**Developer submission reviewed:** `phase-08-developer`  
**Reviewed specification lineage:** current developer Phase 8 spec/data plan/literature files through the pre-empirical submission  
**Status: REQUEST CHANGES**  
**Empirical execution: NOT AUTHORIZED**

## What passed

1. The scientific scope is finite and clearly bounded.
2. The frozen Phase 7 P01-P10 predictions are correctly treated as fixed inputs rather than candidates to be reselected after Phase 8 results.
3. CE/PE mapping, delta targets, DTE buckets and exit-policy universe are explicit.
4. One-lot/no-pyramiding treatment is explicit.
5. Quote-backed execution is correctly distinguished from OHLC/proxy execution.
6. Current 2026 Paytm/NSE cost rates cited in the specification are directionally consistent with the official sources reviewed.
7. Historical NIFTY lot-size handling is correctly date-aware in principle.
8. The row-level Phase 7 forecast reconstruction gate is an important and necessary reproducibility control.
9. The literature correctly supports the importance of transaction costs and data-snooping controls.

## Required corrections before the specification can be frozen

### 1. Liquidity tie-break is not operationally defined

The contract-selection rule says “higher contemporaneous liquidity,” but no exact liquidity observable or lookback is specified. Using entry-bar/future volume would violate causality.

**Required:** freeze the exact point-in-time liquidity statistic used for tie-breaking. It must be computed strictly from observations available before the decision/selection timestamp.

### 2. Entry/exit tolerances are not numerically frozen

The specification refers to a “registered entry tolerance” and stale-observation tolerance without giving exact values.

**Required:** freeze exact tolerances separately for intraday and daily observations, including the maximum allowed quote/bar age and the maximum search window for a fill.

### 3. Missing-data acceptance thresholds are not operational

The phrase “material unresolved data gaps” permits post-result judgment.

**Required:** freeze numerical data-quality thresholds, including:
- maximum missing critical fields;
- maximum no-fill rate;
- maximum stale-bar rate;
- maximum timestamp-gap rate;
- treatment when a cell fails a quality threshold.

### 4. Historical Paytm brokerage fallback is not numerically frozen

The specification says that when a historical Paytm tariff cannot be verified, an “explicit conservative brokerage stress” is used, but does not define that stress.

**Required:** freeze the fallback rate and clearly distinguish verified historical tariff cells from conservative fallback cells.

### 5. Contract-selection delta fallback is not fully reproducible

The fallback hierarchy is good, but the Black–Scholes inputs are not completely frozen. In particular, the risk-free rate and IV source/solver treatment need deterministic definitions.

**Required:** freeze:
- risk-free-rate source and point-in-time lookup;
- IV source;
- root-finding/solver convention if IV must be recovered;
- treatment when IV cannot be obtained.

### 6. Phase 7 reconstruction tolerance is unspecified

The reconstruction gate requires aggregate metrics to reproduce but does not define a numerical tolerance.

**Required:** freeze exact tolerances: integer counts exact; continuous metrics within a fixed absolute tolerance.

### 7. Phase 8 universe cardinality must be explicit

The current design implies up to 100 forecast cells × 3 deltas × 4 DTE buckets × 4 exits = **4,800** configuration cells, but this cardinality is not stated as a mandatory registered grid.

**Required:** explicitly register the complete 4,800-cell universe. Configurations that are impossible because no valid contract exists must be reported as `INELIGIBLE` with a deterministic reason, not silently removed.

### 8. “One or a few anomalous fills” rule is not auditable

The shortlist rule says a winner must not depend on “one or a few anomalous fills,” but no mathematical threshold exists.

**Required:** replace this with deterministic rules, for example:
- leave-one-out net expectancy remains positive after removing the largest 1% of completed trades in the base case; and
- no single expiry-month contributes more than a fixed fraction of total base-case net P&L.

The exact thresholds must be frozen before empirical execution.

### 9. Chronological block definition for option P&L is missing

Phase 8 reports chronological blocks but does not state their exact duration/partition.

**Required:** freeze the block unit. Recommended: trading-session blocks, with daily cells using 20-session blocks and intraday cells using 20-session blocks so the dependence structure remains comparable across option configurations.

### 10. Position-overlap rule needs an explicit reset policy

“One open trade at a time” is clear, but the behavior when a signal occurs while a trade is open must be explicit.

**Required:** state that overlapping signals are ignored and logged as `OVERLAP_SKIPPED`; they are not queued or retrospectively evaluated.

## Scientific gate

No empirical Phase 8 run is authorized from the current submission.

The specification can pass once the ten reproducibility/auditability gaps above are corrected without changing the substantive research universe after seeing empirical outcomes.

**Tester → Developer:** implement only the listed reproducibility corrections, update the Phase 8 specification/data plan and error/research logs, then resubmit the corrected specification for a fresh tester gate. Do not acquire strategy results or tune any economic threshold before re-approval.
