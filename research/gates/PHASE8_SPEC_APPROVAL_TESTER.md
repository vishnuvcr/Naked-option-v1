# Phase 8 Specification — Independent Tester Approval

**Developer branch reviewed:** `phase-08-developer`  
**Status: PASS WITH SCOPED RESTRICTIONS**  
**Empirical execution:** AUTHORIZED ONLY AFTER IMPLEMENTATION/WORKFLOW GATES PASS

## Re-review result

The ten issues in the earlier REQUEST CHANGES gate were corrected in the current developer lineage.

### Verified corrections

- pre-decision liquidity tie-break is fixed to prior 15 complete one-minute bars for intraday and prior-session volume for daily data;
- entry windows and exit windows are numerically fixed;
- missing-data and execution-quality thresholds are numerically fixed;
- historical Paytm brokerage fallback is fixed at ₹20 per executed order when no dated tariff can be verified;
- present-day Paytm Money's ₹10/order figure is explicitly prohibited from being back-applied without an effective-date record;
- Black–Scholes fallback inputs and deterministic bisection solver are fixed;
- Run #654 reconstruction tolerance is fixed at exact integer counts and 1e-9 absolute tolerance for continuous metrics;
- the full 4,800-cell execution grid is explicitly registered, with deterministic non-execution statuses;
- anomaly concentration has a deterministic leave-out and expiry-month rule;
- chronological option-P&L blocks are fixed at 20 NSE trading sessions;
- overlapping signals are logged as `OVERLAP_SKIPPED` rather than queued;
- BSE is explicitly secondary and cannot replace NSE contract metadata.

## Independent mathematical/cost checks

The current specification is consistent with the reviewed official cost sources:

- Paytm Money current F&O FAQ: ₹10 per unique executed F&O order;
- NSE STT from 1 April 2026: 0.15% on sale of an option's premium, seller-paid;
- NSE circular NSE/FA/73061 effective 1 March 2026: equity-option transaction charge ₹3,552/crore of traded premium per side plus ₹0.01/crore IPFT per side;
- NSE/SEBI levies page: SEBI turnover fee 0.0001%, equity-option stamp duty 0.003% buyer, GST 18% for stock-broker services;
- NSE contract-information/product pages control historical lot size, strike/tick and expiry metadata;
- NSE settlement rules make NIFTY index options European-style and cash settled.

## Scoped restrictions

1. **Historical Paytm tariff:** the ₹10 FAQ rate is current-present information, not automatically a historical rate. The research must retain the ₹20 fallback for periods where an effective-date tariff cannot be independently verified. Any later discovery of a historical tariff requires a pre-empirical data/cost manifest update and tester re-check; it cannot be chosen because it improves strategy results.

2. **OHLC/proxy execution:** Q1 results remain explicitly non-quote-executable. Only validated bid/ask data can support a quote-executable claim.

3. **Black–Scholes fallback:** the 0% dividend-yield convention is an explicitly frozen ranking approximation, not a claim about the true NIFTY dividend yield. It may not be changed after results are observed.

4. **Phase 7 reconstruction:** no option P&L is allowed until the row-level reconstruction reproduces the immutable Run #654 aggregates within the frozen tolerance and its resulting prediction panel is hashed.

## Scientific gate decision

**PASS WITH SCOPED RESTRICTIONS.**

The Phase 8 specification is now frozen for implementation. No Phase 8 empirical job may begin until the following separate gates pass:

1. options-data source/point-in-time gate;
2. forecast-reconstruction gate;
3. execution-engine regression gate;
4. GitHub Actions workflow gate.

**Tester → Developer:** implement the frozen specification exactly, acquire only approved free-source data first, and submit the data/reconstruction/code workflow gates before generating any trading P&L. Do not alter the execution universe or costs in response to early results.
