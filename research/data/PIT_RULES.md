# Point-in-Time Rules

1. **Availability dominates observation date.** A value is usable only when `available_at <= decision_time`.
2. **Historical revisions are prohibited.** If a source later revises a figure, the earlier simulation retains the originally available observation where recoverable.
3. **Contract existence is PIT.** The option contract must have been listed/active by decision time.
4. **Lot size is effective-dated.** Historical lot size comes from the contract regime in force at the trade date.
5. **Expiry information is not assumed to be today's knowledge unless the relevant contract/calendar existed then.**
6. **Global markets use actual local close times converted to IST.** Overnight lead-lag features must use only markets that had already closed before the NIFTY decision time.
7. **FII/DII reports use publication availability, not just report date.**
8. **India VIX uses the published index observation timestamp.**
9. **News uses article publication/availability time.**
10. **Corporate actions use announcement/effective dates separately.**
11. **No forward filling across unavailable periods.**
12. **No interpolation across missing option prices for trading signals.**
13. **Implied volatility/Greeks are derived only from inputs available at the same decision time; model conventions are versioned.**
14. **Composite-source rows retain all contributing source IDs.**
15. **Duplicate keys are a hard failure until reconciled.**
16. **Time zones are normalized explicitly; IST/UTC conversion must preserve DST rules for global data.**
17. **All transformations produce a manifest with input hashes and output hashes.**

## Hard leakage tests

- future timestamp referenced by a feature;
- observation available_at after feature timestamp;
- training normalization fit on future rows;
- contract/lot-size regime from a future interval;
- revised data replacing an as-of value;
- global close later than the NIFTY decision time;
- news item published after the simulated trade;
- option strike/expiry rows created from future contract inventory.
