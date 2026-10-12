# Phase 8 OHLC Proxy Strategy — Independent Tester Gate

STATUS: PASS — OHLC PROXY BACKTEST AUTHORIZED

Developer branch reviewed: phase-08-prediction-developer
Developer commit under review: a0a9eec37ad97c44b197a92b5578a53138fa4c68
Runner blob SHA: cd9bd7eebb9df54eca92d801b122ae780a042556
Synthetic test blob SHA: 0a8aa837feedceed89392a7ec337b939a4b04318
Workflow blob SHA: 256ae2200637dd509f9d8101cad9112c1f36ee47

## Scope of this decision

The user has explicitly directed that the existing OHLC data be used without requiring bid/ask or another source-validation gate. This gate authorizes the registered Q1/OHLC proxy backtest only. It does not authorize quote-executable claims, live deployment, model refitting, or automatic promotion of the best historical result.

## Independent review

- Reviewed the exact runner, its synthetic regression suite, the GitHub Actions workflow, the frozen cost schedule, and the registered 4,800-config universe.
- Hosted regression run 38218498200 completed successfully: runner/test compilation, proxy synthetic regression, and runner self-test all passed.
- The workflow downloads only the previously collected options composite and Phase 7 Run #994 forecast archive. Both archive SHA-256 values are pinned in the workflow. No new market-data source request is part of the backtest.
- Signal direction is delegated to the frozen execution engine. The runner consumes saved probabilities and does not refit forecasts.
- Contract candidates are filtered by option direction, expiry after scheduled exit, DTE bucket and delta target. Entry uses the first observed option OHLC bar strictly after the forecast decision.
- P&L is computed from buy/sell proxy fills multiplied by the selected lot size, less both-side brokerage and the dated statutory/transaction charges. C0-C3 apply progressively more conservative synthetic spread/slippage costs.
- Time exits and X1/X2/X3 triggers are implemented; after-close intraday horizons are skipped, and a stop gap uses the lower opening price rather than assuming a stop-level fill that the OHLC bar cannot support.
- Summary includes trade count, win/loss rate, average and median net return, average winners/losers, profit factor, maximum drawdown and dates, and exploratory IID-test/BH-screening columns.

## Scoped limitations that must accompany any results

1. Execution quality is Q1/OHLC proxy only. No bid/ask was used; results must not be described as executable-quote backtests.
2. The lot-size schedule is inferred from expiry dates, not joined to a point-in-time instrument master. Transition-period contracts can therefore be mis-scaled, so INR totals are estimates rather than exact exchange-reconciled amounts.
3. The input is a partial-grid rolling-options composite and includes model-estimated Greeks/inferred contract metadata. Some registered configurations may have no eligible trades.
4. Identical option contract/timestamp observations are not de-duplicated. The current stable sorting/search behavior makes selection reproducible, but conflicting duplicates could affect which observation is selected.
5. A selected delta/spot is read from the entry-time option row; results represent entry-time contract selection, not contract selection frozen at the earlier forecast timestamp.
6. OHLC bars cannot reconstruct quote queues, depth, intrabar order, or real fills. C0-C3 are synthetic friction stress scenarios; their spread rate is applied to each side, in addition to the incremental slippage rate.
7. IID t-tests and Benjamini-Hochberg q-values are exploratory screens across dependent time series/configurations; they do not establish confirmatory statistical significance. The highest historical result must not be promoted without later holdout/robustness evidence.

## Decision

**PASS for one hosted empirical Q1/OHLC proxy run over the frozen grid**, four cost scenarios, and saved Run #994 forecasts, after the workflow's regression and exact-blob gate pass. Publish sanitized result tables, the full trade ledger as a workflow artifact, and the caveats above. The user has waived further bid/ask/data-validation gates; do not re-open them in this sub-study.

**Tester → Developer:** run the approved exact blobs only; preserve all 4,800 configurations and C0-C3 scenarios, publish results and errors, and do not claim quote-executable performance or promote a strategy from ranking alone.

**Developer → Tester:** independently audit the resulting report and trade summary for arithmetic, timestamps, signal selection, costs, drawdowns, and consistency with this scope. Record PASS/REQUEST CHANGES with run and artifact IDs; do not require bid/ask or a new data-validation phase.
