# Legacy Strategy Component Mining Map

## Purpose

Translate prior strategy logic into **naked-long-compatible predictors** without carrying forward hidden short exposure.

| Component | Source families | Naked-long research translation | Pre-registered hypotheses/method families |
|---|---|---|---|
| 10:00–10:05 entry burst | TT-A01, TT-A03 | Direction at opening + 45–50 min confirmation | H03, H15; opening-range rules |
| 09:20–09:35 setup | TT-A02, TT-A07 | Early-session regime classification | H03, H12 |
| DTE=3 | TT-A03 | Event/expiry timing state | H11, H12 |
| Expiry-day special case | TT-A01, TT-A05, TT-A03 | Separate expiry-day long-option policy | H11, H18 |
| Monday exclusion | TT-A06 | Weekday regime effect | H11 |
| Delta bands 0.08/0.10 | TT-A02, TT-A04, TT-A07 | Candidate long-option delta zone and direction confirmation | H17, F01-F15 |
| Delta 0.20/0.30/0.40/0.50 | TT-A02, TT-A04, TT-A07 | Strike-selection surface for long calls/puts | H17, F01-F15 |
| Delta crossing >=0.60/0.65 | TT-A04, TT-A07 | Large directional move / convexity trigger | H12, H15, I01-I10 |
| Premium matching | TT-A01, TT-A06 | Cross-strike/cross-expiry premium-equilibrium deviation | H05, H13, I01-I10 |
| State/entered runtime variables | TT-A04, TT-A07 | Explicit finite-state directional policy | J01-J08 |
| IC → ratio transition | TT-A07 | Volatility/regime transition detector, not copied structure | H12, H13, H14 |
| Ratio reversal | TT-A04 | Direction-switch trigger based on option-surface dynamics | H12, H18, J01-J08 |
| 0W/1W term structure | TT-A02, TT-A06 | Near/far expiry IV/premium slope and directional response | H05, H18, F01-F15 |
| P&L loss barriers -3000/-4000/-7000 | TT-A01, TT-A05, TT-A06 | Translate into standardized % of premium-risk stop, not rupee constants | H16, H18 |
| 15:10/15:15/15:29 exits | multiple | Time barrier sensitivity | H11, H15 |
| one-trade/day | TT-A05/TT-A06 | Abstention/overtrading control | H15 |
| ATM spot | TT-A01, TT-A03, TT-A06 | Baseline strike selection | A01-A05, F01-F15 |
| nearest/far expiry | multiple | Expiry-selection test | H17-H18 |

## Important methodological rule

A component is accepted only when it is evaluated prospectively, point-in-time, with realistic option fills and costs. A legacy strategy's original profitability is **not** transferred to this project merely because its rule is reproduced.

## Expected high-value ablations

1. DTE/expiry-day conditional directional long call/put.
2. Delta-crossing triggers around 0.50, 0.60 and 0.65.
3. 0.10–0.30 delta long-option selection versus ATM.
4. 0W/1W and 0W/1W/month premium or IV slope as a directional regime input.
5. Opening-burst plus premium-equilibrium confirmation.
6. State-machine ensemble with explicit abstention.
7. Time-barrier exits versus volatility-scaled exits.
