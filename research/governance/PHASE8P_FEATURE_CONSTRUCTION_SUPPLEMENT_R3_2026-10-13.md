# Phase 8P R3 — Feature-construction supplement

**Status:** FROZEN PRE-RESULT IMPLEMENTATION SUPPLEMENT  
**Amendment ID:** PHASE8P_FEATURE_CONSTRUCTION_SUPPLEMENT_R3_2026-10-13

## Purpose

The R3 method registry specifies the PM0001 representation as `raw_lag_stack` with `ordered_lagged_returns_and_levels`. The registry does not make the exact lag ordering, target price lookup or treatment of missing history fully executable. This supplement freezes those mechanics before any empirical metric is calculated. It does not change the research objective, target labels, registered horizons, outer folds, purging/embargo, support minima or statistical rules.

The machine-readable contract is [PREDICTION_FEATURE_CONSTRUCTION_CONTRACT_R3_2026-10-13.json](../registry/PREDICTION_FEATURE_CONSTRUCTION_CONTRACT_R3_2026-10-13.json).

## Feature vector

Only eligible NIFTY SPOT rows and the pinned `nifty_close` field are admitted for this initial representation. Option rows are not used as directional labels or as PM0001 predictors in this first implementation. Option-derived predictors require their own point-in-time contract and are not silently substituted.

For lookback `L` (20 or 60 bars), every feature vector has `2L` elements in this fixed order:

1. **Simple returns**, newest to oldest: \(r_j=C_{t-j}/C_{t-j-1}-1\), for \(j=0,\ldots,L-1\).
2. **Spot-close levels**, newest to oldest: \(C_t,C_{t-1},\ldots,C_{t-L+1}\).

Thus, the vector has 40 or 120 features. Current close and all lagged values are known at the decision timestamp. Scaling parameters are learned from the current training fold only. The oldest return requires an exact additional historical close; incomplete history is excluded and counted, never filled.

## Horizon-specific sample construction

- **Intraday:** decision rows are eligible minute-aligned SPOT observations. All feature history, decision price and the exact horizon endpoint must be within the same regular NSE session. The target endpoint is looked up at the exact decision timestamp plus 5, 15, 30, 60 or 120 minutes.
- **Positional:** use the SPOT observation timestamped exactly 15:30 IST for each eligible official session. Features use consecutive official-session closes. A +h target is the exact observed 15:30 close at session index \(i+h\), not a calendar-day offset.
- **Labels:** simple return greater than \(10^{-8}\) maps to UP (1); less than \(-10^{-8}\) maps to DOWN (0); absolute return at or below the tolerance is excluded and counted.
- **No synthetic data:** no interpolation, forward-fill, calendar-day substitution, or nearest-timestamp substitution. Missing target pairs and incomplete lag history are counted separately.
- **PIT:** training and calibration labels are usable only after their endpoint is observable and strictly before the relevant training cutoff. The existing horizon-specific purge/embargo and frozen outer/inner fold calendar still apply.
- **Quarantine:** out-of-session, unmapped-calendar, misaligned, invalid-price and timestamp-date mismatch rows cannot become features or endpoints. Duplicate eligible timestamps fail closed.

## Limits and gates

This supplement is a mechanical implementation contract, not method approval. PM0001 and all other methods remain unauthorized for fitting until the explicit implementation gate passes. The builder writes only model-ready sample objects and aggregate diagnostics; it does not fit or rank models, inspect an untouched holdout, or evaluate option P&L.

The diagnostics must preserve input/eligible/quarantined row counts, missing target pairs, flat exclusions, feature-history exclusions, sample counts, feature dimensions, and source/calendar/contract hashes. Any unknown schema or changed pinned source fails closed.
