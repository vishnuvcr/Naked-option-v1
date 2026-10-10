# Independent Tester Report — Phase 7 Available-Data Prediction Run #44

**Decision: PASS WITH SCOPED RESTRICTIONS — artifact integrity and metric reconciliation pass; no candidate is promoted.**  
**Phase 8 / strategy development: NOT AUTHORIZED by this report.**  
**Review date:** 2026-10-10  
**Role:** independent tester review of the immutable output artifact, row-level panel, source manifest, and independently recomputed metrics/inference.

## 1. Run and artifact identity

- Hosted run: [Run #44](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915)
- Run ID: `38018506915`
- Developer commit: `9e9dc2de3f1ecfa591db5d6c29e6543707928cb7`
- All three hosted jobs succeeded: regression, exact-snapshot tester approval, and empirical prediction/validation/artifact upload.
- Artifact: `phase7-available-global-results`, artifact ID `11657636547`, 2,416,937 bytes.
- Downloaded ZIP SHA-256: `63b607db7227cdd91f3a62a0a8ca5f0b010d12c3bad1848ebbd9f59961804891`.
- ZIP contains results JSON, 91,988-row prediction panel, global source manifest, 11 global/peer-market CSVs, and the NIFTY daily CSV.

Provenance SHA-256 reconciliation:
- NIFTY CSV: `08b8b72117b70140cfdabf9b3cf78d315aff736858a3ac51c5edf7b55df559b4` — matches JSON provenance.
- Global source manifest: `0564e64cb4402ae00162927c04704cbb689b4a732be60ca61934769389a599c4` — matches JSON provenance.
- Prediction panel: `0dcae6aefcd21aaa8f66c610fa48451476cf2da6b1719b190b2047cc8cf4ce70` — matches JSON provenance.

## 2. Independent structural and arithmetic checks

Independent audit of the downloaded files found:

- NIFTY history: 1,676 rows, 2020-01-01 through 2026-10-09; source rows have the expected source and `available_at` fields.
- 11/11 global/peer sources marked ACTIVE, 2,139–2,284 rows per source, each ending 2026-10-09; the frozen global-equity composite was eligible.
- Five registered forecast horizons: 1, 2, 3, 5, and 10 sessions.
- Twelve registered methods per horizon; all 60 method/horizon cells executed. No cell was silently omitted or reported as blocked.
- Prediction panel has 91,988 rows and 12 columns.
- Duplicate `(date, horizon_sessions, method, row_type)` keys: **0**.
- Missing labels, future returns, or candidate probabilities: **0**.
- Probability or baseline-probability bounds violations: **0**.
- Target-sign mismatch between `actual_direction` and the sign of `future_log_return`: **0**.
- Independently recomputed accuracy, balanced accuracy, ROC AUC, PR AUC, Brier score and log loss matched the results JSON for every method/horizon to within (10^{-10}).
- Independently reimplemented the registered common-row paired 20-session moving-block bootstrap (500 replicates, seed 42, max statistic across 12 methods). The observed maximum Brier improvements and raw p-values matched the JSON for all five horizons exactly to floating-point reporting precision.
- All five Bonferroni-adjusted horizon p-values are 1.0.

These checks establish reproducible metric calculations on this artifact. They do not establish that any model has useful out-of-sample predictive power.

## 3. Best Brier-score candidate per horizon

Positive Brier improvement means the candidate beat the causal training-rate baseline on Brier score. Values are computed on paired rows.

| Horizon | Best Brier candidate | N | Accuracy | Balanced accuracy | ROC AUC | Candidate Brier | Baseline Brier | Brier improvement | Family p | Bonferroni p |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 session | G13 global-equity composite | 1,421 | 52.85% | 50.07% | 0.516 | 0.249932 | 0.250201 | +0.000269 | 0.9840 | 1.000 |
| 2 sessions | G13 global-equity composite | 1,419 | 54.12% | 50.23% | 0.536 | 0.247930 | 0.248749 | +0.000820 | 0.8882 | 1.000 |
| 3 sessions | G06 Asia composite | 1,418 | 55.64% | 52.72% | 0.546 | 0.247769 | 0.249235 | +0.001466 | 0.6786 | 1.000 |
| 5 sessions | G06 Asia composite | 1,414 | 55.73% | 52.68% | 0.556 | 0.247593 | 0.249217 | +0.001623 | 0.7745 | 1.000 |
| 10 sessions | G02 Bank Nifty | 1,404 | 55.91% | 50.00% | 0.475 | 0.250089 | 0.251055 | +0.000966 | 0.9800 | 1.000 |

G06 at five sessions has the strongest ROC AUC among the Brier-winning horizon leaders (0.556) and the largest Brier improvement in this batch (+0.001623). This is still a small effect and the registered family test is emphatically non-significant ((p=0.7745); Bonferroni-adjusted (p=1.0)). G02 at ten sessions has ROC AUC below 0.5 despite a small Brier improvement, so it is not a credible directional classifier. Accuracy alone is not a selection criterion here: the target is imbalanced toward positive returns in these evaluation samples, and several models have balanced accuracy near 0.50.

## 4. Family-level statistical conclusion

| Horizon | Maximum observed Brier improvement | Raw family p-value | Bonferroni-adjusted p-value |
|---:|---:|---:|---:|
| 1 | 0.000269 | 0.9840 | 1.000 |
| 2 | 0.000820 | 0.8882 | 1.000 |
| 3 | 0.001466 | 0.6786 | 1.000 |
| 5 | 0.001623 | 0.7745 | 1.000 |
| 10 | 0.000966 | 0.9800 | 1.000 |

**No horizon rejects the family null.** The observed candidate ranking is consistent with noise after accounting for the registered method family and horizon family. No model is statistically promoted. The final untouched holdout remains unopened, as registered.

## 5. Data and scope caveats

1. All 11 global-source manifest records show `cache_hit: false` in this run. The workflow restored its cache, but the global acquisition script rejected the prior files as not meeting its current cache-validity contract and reacquired them. The output files now have the current schema and hashes; the workflow's post-cache step completed. This appears to be a legacy-cache/schema migration, not proof that every future run must download again. The next authorized run should verify cache reuse, but this one-run approval does not authorize another empirical batch.
2. Yahoo Finance is explicitly a free historical research reference, not execution data. NIFTY source rows were spot-checked against official NSE archive data at the two dates registered in the acquisition code; this does not turn the full series into an exchange-certified tick-by-tick dataset.
3. The experiment is prediction-only. It does not test options payoffs, option-chain information, fills, slippage, brokerage, taxes, liquidity, or Paytm Money execution costs. No trading profitability inference may be drawn from these directional probability metrics.
4. This is one registered batch over the selected available-data method family. The final untouched holdout was not opened; no claim of final out-of-sample confirmation is permitted.

## 6. Decision and next gate

**Tester decision:** PASS WITH SCOPED RESTRICTIONS for data/result integrity only. The registered experiment ran, output artifacts are internally consistent, and metrics/statistical tests were independently reproduced. The scientific result is negative for promotion: no statistically significant candidate was found. This does not mean all possible prediction methods have been exhausted; it means this pre-registered family did not produce a candidate worth promoting.

- Do not advance to Phase 8.
- Do not create an options strategy from these results.
- Preserve Run #44 and its artifact as immutable evidence.
- Any further prediction-family research requires a new pre-registered developer proposal and a separate tester gate; it must not reuse the final untouched holdout for tuning.
- A later strategy study, if separately authorized, must include options data, realistic Paytm Money brokerage/taxes/transaction costs, slippage, spreads, liquidity, position sizing and drawdown analysis.

**Tester → Developer:** Record the negative family-level result and artifact hashes, keep Phase 8 blocked, and propose any next prediction family as a separately preregistered phase rather than promoting G06/G13 from this screening result.

**Developer → Tester:** Independently review any proposed new family before execution, with a frozen hypothesis, exact features/labels, multiplicity control, cache/source contract and immutable result-validation plan.
