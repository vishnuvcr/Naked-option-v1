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
