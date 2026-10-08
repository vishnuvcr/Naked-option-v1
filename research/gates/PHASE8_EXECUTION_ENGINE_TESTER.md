# Phase 8 Execution Engine — Independent Tester Review

**Developer branch reviewed:** `phase-08-developer`  
**Status: REQUEST CHANGES**  
**Empirical option P&L:** NOT AUTHORIZED

## What passed

- Long-only CE/PE direction mapping and P05/P06 abstention boundaries are implemented consistently.
- DTE bucket boundaries D0/D1/D2/D3 are correct.
- Black–Scholes delta sign convention is correct for CE/PE.
- Break-even formulas are dimensionally correct for long CE/PE.
- Q2 quote fill direction (ask for buy, bid for sell) is correct.
- C0–C3 incremental slippage values match the frozen specification.
- Brokerage, exchange, IPFT, STT, SEBI, stamp and GST components are separated and summed explicitly.
- Stop-first behavior for ambiguous same-bar stop/target information is implemented for the tested stop policy.
- Daily H-session target mapping is chronological and deterministic.

## Required corrections

### 1. Expiry timestamp bug can incorrectly exclude D0 contracts

`choose_contract()` converts `expiry` to a timestamp at midnight and then requires:

`expiry > planned_exit`

For a NIFTY contract expiring on the same day at the exchange close, midnight is earlier than a 15:15 planned exit. This incorrectly removes potentially eligible D0 contracts.

**Required correction:** normalize date-only expiry to the deterministic contract-expiry timestamp used by the study (15:30 IST on the expiry trading session, or the exact exchange cutoff fixed in the execution specification) before applying the strict-after-exit test.

### 2. Moneyness fallback is mathematically inconsistent with delta targeting

`selection_delta()` returns absolute log-moneyness when observed delta and Black–Scholes delta are unavailable, but `choose_contract()` then compares this moneyness value directly with delta targets 0.40/0.50/0.60.

This mixes dimensionless moneyness with option delta and changes the meaning of the registered delta configurations.

**Required correction:** freeze an explicit non-Greek fallback rule. Recommended deterministic rule: when no valid delta or Black–Scholes delta is available, mark `MONEYNESS_FALLBACK` and select the contract with the smallest absolute log-moneyness among contracts otherwise eligible for the DTE/direction cell. Do not compare log-moneyness numerically with a delta target. Record that the three delta-target configurations may collapse to the same fallback contract.

### 3. Q2 quote timestamp causality is not enforced by the engine

`fill_price()` accepts an ask/bid value but does not validate the associated quote timestamp against the executable timestamp or the frozen stale-data limit.

**Required correction:** add a deterministic quote-validation function and regression tests for:
- quote timestamp >= executable timestamp;
- quote age <= frozen stale window;
- missing/stale bid or ask → no quote-backed fill;
- no silent substitution with a future quote.

### 4. Overlap reset semantics need explicit strictness

`validate_no_overlap()` currently permits a new signal at exactly the stored `open_until` timestamp.

**Required correction:** make the rule explicit and test it. For the frozen Phase 8 policy, a signal occurring while the position is still open must become `OVERLAP_SKIPPED`; a signal at the exact liquidation timestamp should only be admissible if the engine has already recorded the close before evaluating the signal. This ordering must be implemented rather than inferred.

### 5. Execution regression coverage is incomplete

The current tests do not cover the expiry bug, moneyness fallback, quote timestamp validation, or exact overlap ordering.

## Scientific gate

The execution engine is not approved.

No real options data may be passed through the 4,800-cell backtest until the five corrections are implemented and independently re-reviewed.

**Tester → Developer:** fix only these engine issues, add deterministic regression tests, update the execution convention/code log, and resubmit. Do not alter the registered delta/DTE/exit universe or cost scenarios in response to results.
