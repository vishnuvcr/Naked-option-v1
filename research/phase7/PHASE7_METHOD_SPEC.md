# Phase 7 — Ensemble and Regime-Conditioned Prediction Specification

## Status
**FROZEN — Phase 7 empirical execution specification**

Phase 7 uses only accepted Phase 6 probabilities. Candidate definitions P01-P10 are fixed, causal and unchanged from the approved Phase 7 registration.

### Chronology
Expanding training, minimum 200 eligible observations, 20-trading-session test blocks, refit every 20 sessions. Intraday rows inherit the same session blocks. All calibration and regime thresholds are training-only. The final untouched holdout remains unopened.

### P08/P09/P10 regime rules
Four exhaustive states are defined by median splits of training-only 20-observation volatility and the training-only median of trend strength, where trend strength is absolute 20-observation mean return divided by 20-observation return SD with 1e-12 denominator guard. Regime positive-class rate q_s is training-only; <50 regime labels uses pooled training rate. P08=0.5*P01+0.5*q_s; P09=0.5*P04+0.5*q_s; P10 abstains in [0.45,0.55].

### Frozen family-level data-snooping test
For each layer/horizon, compare candidate Brier loss with the causal historical positive-rate baseline. Recenter each candidate differential by its sample mean; family statistic is the maximum positive candidate mean improvement.

Use a moving-block bootstrap with seed 42, 500 replications, daily L=20, intraday L=60. For n observations, set effective L=min(L,n), construct every overlapping contiguous block start s=0,...,n-L, sample ceil(n/L) blocks with replacement, concatenate and truncate to exactly n, and use the same indices for every candidate. P05/P06 abstentions receive zero differential, equivalent to benchmark loss. Bootstrap is inferential only and cannot select a candidate.

### Diagnostic reconciliation
P08/P09/P10 regime diagnostics are retained only for chronological evaluation blocks containing at least one finite evaluated label/probability observation, and diagnostic block count must equal the candidate chronological-block count.

### Promotion boundary
No Phase 7 candidate is a strategy. Phase 8 long-option execution, realistic Paytm Money costs, slippage, spreads and entry/exit constraints remain mandatory, followed by Phase 9 robustness and Phase 10 fresh-forward validation.
