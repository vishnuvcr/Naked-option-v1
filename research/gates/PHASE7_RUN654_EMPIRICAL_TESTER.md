# Phase 7 Run #654 — Independent Empirical Tester Gate

**Status: PASS WITH SCOPED RESTRICTIONS**

Run #654: `37763242007`  
Developer head: `4f1d695f291ed32996c07f01710afcecc6f2a540`  
Artifact: `phase7-ensemble-results`  
Artifact ID: `11551679532`  
Artifact SHA-256: `c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`

## Independent audit completed

The tester independently inspected the immutable Run #654 artifact and the production/validation source at the developer head.

### 1. Hosted execution integrity

- protocol job: PASS;
- Phase 7 regression: PASS;
- daily/intraday/global data acquisition: PASS;
- empirical execution: PASS;
- result validation: PASS;
- artifact upload: PASS;
- no workflow failure was used as scientific evidence.

### 2. Registered coverage

The artifact contains the complete frozen Phase 7 grid:

- 2 layers;
- 5 daily/intraday horizons each;
- 10 registered candidates P01-P10;
- 100 candidate cells total;
- all 100 cells status = EXECUTED with positive sample counts.

The final untouched holdout is not referenced as opened by the Phase 7 artifact.

### 3. Result-schema and arithmetic checks

Independent checks passed:

- confusion-count identity `tn + fp + fn + tp = n` for every candidate cell;
- accuracy, balanced accuracy, Brier, log loss, ROC-AUC and PR-AUC are finite and within their valid ranges;
- stored family p-values are in [0,1];
- stored family observed statistic equals the maximum candidate mean Brier improvement;
- chronological diagnostics are present for every candidate;
- P08/P09/P10 regime diagnostic count equals chronological diagnostic count for every layer/horizon;
- regime test-count totals reconcile with the evaluated P08/P09/P10 sample sizes;
- artifact ZIP digest exactly matches the GitHub Actions artifact digest.

### 4. Frozen moving-block bootstrap correction verified

The production code at the audited developer head now implements the tester-approved construction:

- effective L = min(block length, n);
- all overlapping block starts 0 through n-L;
- ceil(n/L) blocks sampled with replacement;
- concatenation truncated to exactly n;
- shared bootstrap indices across candidates;
- seed = 42;
- 500 replications.

The regression suite explicitly checks sample length and overlapping-block behavior. This satisfies the correction required after Run #650.

### 5. Regime-diagnostic correction verified

The production code now appends a regime diagnostic only when the corresponding chronology block has at least one finite evaluated label/probability/regime observation.

The validator enforces:
`len(regime_diagnostics) == len(chronological_blocks)`

This satisfies the Run #650 diagnostic-count correction.

### 6. Statistical disposition

No Phase 7 horizon/layer family passes the pre-registered family-level Brier data-snooping test at conventional 5% significance.

Family p-values:

- daily +1: 0.742
- daily +2: 0.738
- daily +3: 0.962
- daily +5: 0.788
- daily +10: 0.464
- intraday +5m: 0.248
- intraday +15m: 0.992
- intraday +30m: 1.000
- intraday +60m: 0.994
- intraday +120m: 0.512

The largest raw candidate Brier improvement is daily +10 P08 = 0.00315275, but its family p-value is 0.464. The largest intraday raw improvement is +5m P07 = 0.00066397, with family p-value 0.248. These are descriptive results only.

Raw accuracy maxima, especially abstention candidates P05/P06, are not sufficient evidence for promotion because their trade subsets are selected by the frozen abstention rule and the family-level inference remains non-significant.

### 7. Scoped restrictions

1. **Abstention diagnostic interpretation:** P05/P06 primary metrics are correctly calculated on trade-only observations, while their stored chronological diagnostic series are generated on the full finite probability/label series. Therefore those chronological diagnostics must not be interpreted as trade-only performance diagnostics. Before any option-execution promotion, trade-only chronological P05/P06 diagnostics should be reported as an additional audit view; no candidate selection is permitted from that amendment.

2. **Intraday regime observation scale:** the frozen P08/P09/P10 implementation computes the causal 20-observation volatility/trend statistics on the full one-minute return path and samples those statistics at the frozen hourly decision rows. This is causal and unchanged by Run #654, but the frozen specification does not explicitly state the sampling interval for the word “observation.” This implementation detail must remain fixed and be explicitly documented before any later tuning; it must not be changed based on Run #654 outcomes.

These restrictions are documentation/audit-scope restrictions, not evidence of a profitable edge, and they do not invalidate the technical artifact.

## Scientific gate decision

**PASS WITH SCOPED RESTRICTIONS.**

Run #654 is the accepted Phase 7 technical empirical artifact for the declared ensemble family. No Phase 7 candidate is promoted to a trading strategy.

The next scientific gate remains Phase 8 long-option execution research. Phase 8 must use the frozen candidate family without result-driven reselection and must include Paytm Money brokerage/fees, exchange/statutory charges, spread, slippage, latency/entry realism, premium decay and explicit option liquidity rules.

**Tester → Developer:** archive this gate on `phase-07-developer`; update STATUS.md, ERROR_LOG.md/RESEARCH_LOG.md/CHAT_LOG.md and README.md with Run #654, preserve the artifact digest, keep P01-P10 unpromoted, and carry the two scoped restrictions forward into the Phase 8 execution protocol. Do not alter Phase 7 methods based on these results.
