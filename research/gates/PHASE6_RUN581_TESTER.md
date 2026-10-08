# Phase 6 Run #581 — Independent Empirical Tester Gate

**Status: PASS WITH SCOPED RESTRICTIONS**

## Run identity

- Workflow: Research Protocol Check
- Run: #581
- Run ID: `37680832842`
- Developer SHA: `fef0bbf4600b47a41100f6a6b6397d34d3b7a3c7`
- Artifact: `phase6-novel-results`
- Artifact ID: `11513410209`
- Artifact SHA-256: `2065f7d8025b87f67de1a9f04908ec2fc015a6bda98c5a8162ddad3b01961c24`
- Protocol: `research/phase6/PHASE6_METHOD_SPEC.md`
- Seed: 42

## Independent audit performed

The tester independently inspected the immutable artifact rather than relying on the workflow conclusion.

### 1. Coverage and status reconciliation

Registered grid:

- 2 layers: daily + intraday
- 20 methods: E01-E10 and I01-I10
- 5 horizons per layer
- Total: **200 method/horizon cells**

Observed:

- **140 EXECUTED**
- **60 BLOCKED_DATA**
- **0 missing cells**
- **0 unexpected statuses**
- Every method has exactly five cells per layer.

Blocked methods are consistent with the frozen data-availability rules:

- E07: insufficient PIT-safe global composite coverage.
- I02: insufficient PIT-safe global source history.
- I04: no PIT-safe option IV/OI history.
- I06: no PIT-safe bid/ask history.
- I07: no PIT-safe option premium/contract history for the registered break-even calculation.
- I10: correctly blocked because I02 is blocked and frozen I10 forbids reweighting blocked components.

No blocked cell was silently converted into a numerical score.

### 2. Mathematical / schema checks

For all **140 executed cells**:

- (TN+FP+FN+TP=n): passed.
- Accuracy reconstructed exactly from confusion counts: passed.
- Positive-class rate reconstructed exactly: passed.
- Accuracy bootstrap lower <= median <= upper: passed.
- Accuracy, balanced accuracy, Brier, ROC-AUC and PR-AUC were finite and within their valid ranges.
- No executed cell had a non-positive sample count.
- No missing required executed metric was detected.

The hosted schema-validation job also passed before artifact upload.

### 3. Chronology / leakage gate

The production correction previously approved by the tester is unchanged in this run. The current developer change after that approval only corrected a regression-fixture timestamp.

The fresh run passed the full Phase 6 regression suite, including the explicit DatetimeIndex cutoff checks and the later global-I03 cutoff test.

Therefore this run does **not** reopen the previously rejected cutoff implementation.

This gate does not claim that a predictive edge exists merely because chronology tests passed; chronology is a necessary condition, not evidence of profitability.

### 4. Empirical result pattern

The results show several apparent daily accuracy/AUC elevations above 0.50, but they are not yet promotion-grade evidence.

Examples:

- Daily E08, horizon 1: accuracy ≈ **54.97%**, ROC-AUC ≈ **0.555**.
- Daily E08, horizon 2: accuracy ≈ **53.13%**, ROC-AUC ≈ **0.525**.
- Daily I08, horizon 1: accuracy ≈ **53.46%**, ROC-AUC ≈ **0.536**.
- Daily I09, horizon 3: accuracy ≈ **57.00%**, but ROC-AUC ≈ **0.488**, illustrating why raw accuracy alone is insufficient.
- Intraday I08, 5-minute horizon: accuracy ≈ **52.40%**, ROC-AUC ≈ **0.530**.

The tester also observed that several cells have unadjusted bootstrap accuracy intervals whose lower bound exceeds 0.50. This is **not** treated as statistical confirmation because the Phase 6 grid contains many correlated comparisons and the bootstrap intervals are not a family-wise multiple-testing correction.

### 5. Cross-horizon stability

No candidate demonstrates the combination required for promotion:

- stable discrimination across daily and intraday horizons,
- stable chronological performance,
- multiple-testing-adjusted significance,
- cost-aware positive expectancy,
- realistic option execution economics,
- robustness under slippage/spread stress,
- and untouched fresh-forward confirmation.

For example, E08 is relatively strong among the daily results but its intraday performance is much weaker and includes sub-50% accuracy at 15 minutes. I09 shows elevated raw accuracy in several cells but weak ROC-AUC in corresponding daily horizons. These patterns are research leads, not validated strategies.

## Tester disposition

**PASS WITH SCOPED RESTRICTIONS.**

The Phase 6 empirical execution itself is technically valid and complete enough to enter the next scientific stage. The artifact is accepted as an immutable Phase 6 evidence package.

**No E01-E10 or I01-I10 method is promoted to a trading strategy by this gate.**

The accepted artifact may be used for Phase 7 ensemble/regime research, subject to the existing promotion criteria and a new tester gate. Phase 8 option execution remains mandatory before any long-option strategy can be considered.

## Required next steps

1. Archive this tester gate on `phase-06-developer`.
2. Update phase status and README with the artifact identity and scoped result.
3. Preserve all 200 cells and blocked-data reasons.
4. Begin Phase 7 only after the developer/tester handoff is recorded.
5. Do not select a method merely because it has the highest raw accuracy/AUC.
6. Maintain the final untouched holdout and fresh-forward separation.
7. Carry realistic Paytm Money transaction costs, brokerage, spread and slippage into later option execution research.

**Tester → Developer:** Archive this gate exactly, update the status ledger, and proceed to Phase 7 ensemble/regime research. Do not promote any Phase 6 model directly to a trading strategy; any Phase 7 candidate must pass a new independent tester gate.
