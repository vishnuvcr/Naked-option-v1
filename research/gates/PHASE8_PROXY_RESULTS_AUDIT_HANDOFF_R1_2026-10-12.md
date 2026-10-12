# Phase 8 Proxy Results — Developer-to-Tester Audit Handoff R1 (2026-10-12)

## Snapshot under review

- Active hosted run: [38222296903](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38222296903)
- Run commit: `368a3d19e615f8ea09a2006b6b709fc66d8946e3`
- Runner blob: `b26f86af76cedd63d3aff1cb6cb74fb9588eb7a5`
- Synthetic-test blob: `768a9e38262af9d0e5aa657bc00414078158b89b`
- Workflow blob: `9a3c04e5b23e779de5964d9396a732f0fe262ffc`
- Pre-run tester gate: PASS for this exact snapshot. Regression and tester-gate jobs passed; proxy backtest is still running at time of this note.
- Inputs are pinned to the frozen Phase 7 forecast and existing 61-part expiry-enriched option composite. This remains Q1/OHLC proxy output and not quote-executable P&L.

## Defects / audit risks found before results are available

### R1 — Incorrect maximum drawdown percentage denominator

In `scripts/run_phase8_proxy_strategy.py`, `summarise_trades()` reports:

```python
100.0 * max_dd / max(1e-9, float(peaks.max()))
```

This divides the largest absolute drawdown by the *largest peak anywhere in the full period*, not by the high-water mark immediately preceding each candidate drawdown and not necessarily the peak associated with the maximum rupee drawdown. This can materially understate maximum percentage drawdown.

Reproducible example: trade P&L `[+10, -9, +100, -20]` gives realized cumulative P&L `[10, 1, 101, 81]`. The maximum rupee drawdown is 20. The drawdown percentages at the two troughs are 90% (10 to 1) and about 19.80% (101 to 81). The true maximum percentage drawdown is 90%; the current formula returns about 19.80%.

Effect: this defect does not change trade-level net P&L, wins/losses, or the maximum drawdown in rupees, but it makes the percentage drawdown metric unreliable. Do not accept or quote the current percentage field as a valid maximum percentage drawdown.

Required correction: calculate percentage drawdown as a per-time-step series, `100 * (high_water_mark - equity) / high_water_mark` only when the high-water mark is positive, then take its maximum independently of maximum rupee drawdown. Add an exact regression test for the synthetic series above and validate peak/trough timestamps.

### R2 — Drawdown sequence ordering at equal exit timestamps

The summary sorts trades by `exit_timestamp_ist` but computes cumulative P&L row by row. Multiple trades can exit at the same timestamp; arbitrary within-timestamp order can create an artificial intra-timestamp drawdown. Result-level review should aggregate realized P&L by exit timestamp before constructing a realized-equity curve, or clearly label the current trade-order measure as non-portfolio diagnostic.

### R3 — Concurrent signal exposure / capital constraint

The runner evaluates signals as independent one-lot trades and sums their P&L per configuration. The report does not establish that simultaneous open positions are capped or that sufficient portfolio capital is reserved for overlapping signals. Trade-level net outcomes can still be described, but aggregate P&L/drawdown must not be represented as a capital-constrained deployable account result without an overlap/exposure audit.

### R4 — Retained duplicate contract/timestamp observations

The frozen proxy plan states that duplicate contract/timestamp observations are retained, and the loader uses stable source order to break selection ties. The current report must expose duplicate counts / conflicting-row evidence if available; a tie-break is not proof that duplicate OHLC rows are identical. If result-critical conflicts cannot be ruled out, mark affected aggregate metrics provisional and request a narrowly scoped diagnostic/correction instead of silently deduplicating.

## Current disposition

- No strategy performance result has been observed in this note; the active run has not yet exposed a result artifact.
- Do not change the pinned inputs or frozen strategy grid in the running attempt.
- Once the run finishes, independently reconcile artifact hashes, registered grid/summary row counts, trade ledger, cost arithmetic, P&L signs, win/loss counts, and C0–C3 monotonicity before issuing a result-level decision.
- Correct R1 and add regression coverage before treating percentage drawdown as accepted. Any new runner/test snapshot must receive a new exact-snapshot tester review before another empirical run.
- Maintain the declared expiry-mapping and lot-size limitations; do not label these results as quote-executable.

**Developer → Tester:** independently verify each finding against the exact run snapshot; after artifacts appear, deliver a result-level PASS / REQUEST CHANGES report pinned to their hashes. Do not promote a strategy from the pre-run code gate alone.

## R1 audit correction — refined overlap findings (2026-10-12)

A deeper read of `run_proxy()` shows the runner maintains `last_exit` independently for each forecast cell × delta target × DTE bucket × exit policy and skips a signal when its decision timestamp is strictly earlier than that configuration's prior exit timestamp. Entries are also selected from a bar strictly after the decision timestamp. Therefore R3 above is too broad if interpreted as claiming that a single configuration necessarily holds overlapping positions.

Refined requirement: the independent result audit must verify that the ledger's exit timestamps are strictly ordered within each configuration and reconcile the `OVERLAP_SKIPPED` counter. A configuration should be described as sequential one-lot trades if that check passes. It still should not be described as a capital-constrained multi-configuration portfolio or actual broker-executable account result: no cross-configuration capital-allocation model is part of this experiment.

Similarly, R2 is a conditional assertion to verify rather than a proven result defect: the summary sorts per-configuration trades by exit timestamp; if the ledger confirms strictly ordered/unique exit timestamps within each config, equal-time row ordering cannot create an intra-configuration artificial drawdown. Test this invariant from the completed ledger. The independently verified R1 percentage-drawdown formula defect remains confirmed and unaffected by this clarification.

**Developer → Tester:** apply these refinements in the result report; do not report a missing within-config overlap guard unless the completed ledger contradicts the runner logic.

## R5 — OHLC structural consistency is not validated (2026-10-12)

Further code review found that `load_option_data()` filters for finite, positive `option_open`, `option_high`, and `option_low`, but does not enforce `option_high >= option_low`, `option_low <= option_open <= option_high`, or consistency with a finite `option_close`. The vectorized trigger simulator treats finite high/low values as valid. Its existing “invalid bar” regression case covers a NaN high, not structurally inconsistent positive OHLC values.

This is an **unresolved data-integrity risk**, not proof that the frozen source has invalid OHLC rows. The current run is already executing the tester-approved snapshot and must not be altered mid-run. At result review, report that the artifact does not count structural OHLC violations. Before treating X1/X2/X3 trigger-policy results as dependable, either demonstrate with a narrowly scoped aggregate-only audit over the same cached rows that violations are absent (or immaterial), or submit a corrected validator and matching synthetic tests for independent review. Do not silently remove rows or change the frozen grid after seeing P&L.

**Developer → Tester:** verify the OHLC data-integrity limitation and require a scoped evidence-based disposition; distinguish “not measured” from “zero invalid rows.”

## R6 — Prove the timing of any raw-IV-derived contract selections

The point-in-time rules prohibit using IV observed only after the decision. In `scripts/run_phase8_proxy_strategy.py`, `resolve_deltas_vectorized()` falls back to the input `implied_volatility` field when an as-of stored delta is unavailable, but that raw field has no separate valuation/availability timestamp in the runner's input schema. The Greek enrichment script explicitly documents that its *derived* `greek_implied_volatility` is inverted from the same minute's `option_close` (close valued at timestamp + 60 seconds); fortunately the Phase 8 runner does not consume that `greek_implied_volatility` field. The public source dataset card for the active HF minute-OHLC source documents OHLCV/OI and no IV field, but the enriched composite's raw-IV coverage still needs to be measured rather than assumed ([source schema](https://huggingface.co/datasets/thetrademarkk/india-index-options-1m/blob/main/README.md)).

Result-level disposition required:
- Count `delta_selection_method` values in the ledger (including `OBSERVED_DELTA_ASOF`, `BLACK_SCHOLES_RAW_IV_AT_DECISION_PROXY`, and `MONEYNESS_FALLBACK`).
- For any `BLACK_SCHOLES_RAW_IV_AT_DECISION_PROXY` rows, establish the source IV was available at the entry decision timestamp. If no separate as-of evidence exists, classify those contract selections as unverified and do not promote the affected results; use only strictly as-of fields or a declared moneyness fallback in a separately tester-reviewed correction.
- Do not confuse the close-derived `greek_implied_volatility` with a point-in-time IV input at bar open.

This is currently an **as-of provenance question**, not proof that this run used leaked values. The exact current run remains unchanged; evaluate the actual ledger before a result-level pass.

**Developer → Tester:** perform this method-count/timestamp provenance check from the completed ledger and report unknown IV availability explicitly.

## R7 — Fill/trigger prices are not snapped to the ₹0.05 tick

The runner declares `TICK_SIZE = 0.05`, but inspection of `engine.proxy_spread_component()` and `engine.fill_price()` shows the tick is used only as a *minimum spread component*. Neither function rounds the simulated buy/sell fill to a permitted price increment. X1/X2/X3 targets/stops are also calculated as multipliers of the entry/previous high and may fall between valid price ticks.

For example, a premium of ₹10.05 produces mathematical levels such as a 65% stop of ₹6.5325; a real order cannot be filled at that price on a ₹0.05 tick schedule. This is a verified execution-model precision gap; its aggregate P&L effect depends on the observed prices and exits.

Required result audit: count entry/exit/trigger fills that are not on a ₹0.05 tick and estimate the impact of conservatively rounding BUY fills upward and SELL fills downward (and trigger levels under a declared rule). Keep this as a separately reported sensitivity; do not change the current frozen run mid-execution. Before using trigger-policy rankings for promotion, correct tick rounding and tests under independent review or explicitly exclude affected trigger metrics from accepted conclusions. Q1/OHLC proxy and non-quote-executable wording do not remove the price-grid constraint.

**Developer → Tester:** test tick validity and quantify the net-P&L sensitivity; determine whether this requires REQUEST CHANGES for trigger-policy results.

## R8 — Intraday entry eligibility is wider than the frozen execution convention

The runner's `make_skeletons()` accepts an intraday entry when `entry_epoch - decision_epoch <= 300` seconds. But the accepted `research/phase8/PHASE8_EXECUTION_CONVENTIONS.md` and its tester gate define the entry search as **t+1 through t+2 minutes inclusive** (and the tester gate says the first admissible observation is one minute after the forecast timestamp). The frozen `PHASE8_PROXY_BACKTEST_PLAN.md` says first observed bar strictly after the forecast decision; it does not document a five-minute entry-window amendment. A five-minute cap silently admits t+3/t+4/t+5 minute entries that were not in the approved convention.

This is a verified implementation/specification mismatch. Do not change or cancel the active hosted attempt. Once its ledger exists, calculate the intraday decision-to-entry delay distribution and count trades with a delay greater than 120 seconds. Those trades are not eligible under the frozen specification. Before accepting the affected cells or rerunning empirical execution, change the cap to the approved window, add exact boundary tests (120 seconds admitted, 180 seconds rejected), submit the updated runner/tests/workflow through a new exact-snapshot independent tester gate, and rerun the frozen grid if any outputs are affected. Do not simply relabel the five-minute extension after seeing results.

**Developer → Tester:** report the accepted convention versus implementation mismatch and give the ledger-based count of trades outside the approved entry window; require REQUEST CHANGES for affected metrics.
