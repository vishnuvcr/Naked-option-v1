# Phase 4 Family B Independent Tester Gate — PASS WITH SCOPED RESTRICTION

## Review target

Developer Family B run #9, commit `99504da6fb866fb30133b6b47007df9955639007`, artifact `phase4-classical-results` (artifact 11464047326).

## Independent checks

- Protocol CI passed before empirical execution.
- Daily horizons {1,2,3,5,10} and intraday horizons {5,15,30,60,120} are present.
- Every B01-B13 row has EXECUTED, BLOCKED_DATA or NOT_APPLICABLE status.
- Confusion-matrix totals reconcile to n.
- Probability-bin counts reconcile to n for all executed methods checked.
- Directional signal mapping is fixed at 0.55/0.45/0.50 and no method-specific threshold fitting is present.
- B01 EMA20/EMA50 crossover is point-in-time.
- B02 MACD 12/26/9 uses current information only.
- B03 RSI14 thresholds are frozen at 55/45.
- B04 stochastic uses 14/3 and a 50 midpoint rule.
- B05 ADX14 uses fixed 25 trend-strength threshold with DI direction.
- B06 ATR breakout uses prior-20 extrema plus fixed 0.5*ATR14.
- B07 Donchian uses prior-20 extrema.
- B08 Bollinger uses current band position without future information.
- B10 opening-range breakout uses the 09:15-09:30 range and only applies after 09:30.
- B11 pivot/CPR uses prior-session H/L/C, so current-session information is not used in the pivot.
- B12 swing structure uses prior-5 extrema and a fixed five-bar structure comparison.
- B13 uses fixed EMA20/50/100 trend alignment.
- No option-selling, spread or short exposure appears in the Family B implementation.

## Scoped restriction

B09 VWAP is correctly marked BLOCKED_DATA because the canonical NIFTY spot reference does not provide a point-in-time volume series. It must not be inferred from another source without a protocol/source amendment.

## Directional findings

Family B produces several apparent leads, including daily B12/B06/B07/B13 at longer horizons and intraday B10/B13 at longer horizons. These are **research leads only**. They have not passed multiple-testing, chronological robustness, CPCV/DSR/PBO, cost-aware option conversion, or fresh-forward testing.

The strongest-looking Family B deviation is not treated as a strategy.

## Gate decision

**PASS WITH SCOPED RESTRICTION.**

Family B is accepted as a completed single-family research package. Family C may begin under the same pre-registration and tester-gate rules.

## Tester instruction to developer

Archive the Family B artifact and gate report. Proceed to Family C statistical/time-series methods. Do not tune or combine Family B methods based on the observed results until the later ensemble/robustness phases.
