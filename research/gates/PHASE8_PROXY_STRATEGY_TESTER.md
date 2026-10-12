# Phase 8 OHLC Proxy Strategy — Independent Tester Gate (R2)

STATUS: PASS — OHLC PROXY BACKTEST AUTHORIZED

Developer branch: phase-08-prediction-developer
Reviewed commit: a093855b44883740ca96a47995a0e6cf09563830
Runner blob SHA: 1689a00b16813795ec5256158ee10c27a92bcc1a
Synthetic test blob SHA: a128d48d2fc41851bd54a9e9c32d4809cc6a8ba2
Workflow blob SHA: 256ae2200637dd509f9d8101cad9112c1f36ee47

## Independent review findings

- Exact runner, tests, workflow, and frozen cost schedule were reviewed on the developer branch.
- Hosted regression run 38219833960 passed on the exact runner/test blobs above: compile, synthetic suite, and runner self-test.
- The prior run 38218646184 failed before any metrics, at an empty option timestamp index; its artifact contained no result tables. No result from it may be interpreted as strategy performance.
- The correction normalizes row tags for whitespace/BOM, trims the expiry text, reports aggregate-only row-type/key/OHLC counters, and fails with a readable error if no eligible option OHLC rows exist. This is runtime handling and diagnostics, not a request for a new data-validation phase.
- Forecast inputs are saved Run #994 only; no forecast refit or new market-data acquisition. Existing composite and forecast artifacts remain pinned by archive SHA-256.
- The frozen 4,800 configurations × C0-C3 grid is retained. Costs use synthetic spread/slippage and the date-effective transaction-cost schedule including the historical Paytm Money ₹20/order fallback.
- Strategy results must be called Q1/OHLC proxy results, never executable-quote results. Expiry-based lot-size approximation, partial grid, duplicate observations, estimated Greeks, and trigger ambiguity are material caveats.
- IID tests/BH values are exploratory only; a top-ranked historical result is not automatically selected.

## Decision

PASS for one hosted backtest attempt on these exact blobs. The run must publish an aggregate report and full scenario summary if eligible rows are present. If the row parser still finds none, publish the sanitized aggregate diagnostic as a runtime blocker, not as a zero-profit or no-signal scientific result. The user has waived bid/ask and additional data-validation gates; do not reintroduce those requirements.

**Tester → Developer:** run these exact blobs using the pinned existing artifacts; publish the aggregate row-class/key/OHLC counters if there are no eligible rows. Fix any runtime/parser issue autonomously and resubmit exact blobs for review.

**Developer → Tester:** independently audit the completed run for correct source linkage, timestamp/selection logic, fees, fills, P&L signs, drawdowns, and any output coverage limitation. Record a separate result-level decision; do not demand bid/ask.
