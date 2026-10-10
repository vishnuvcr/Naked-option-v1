# Phase 7 Run #44 — Available-Data Prediction Results

**Run:** [GitHub Actions #44](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915)  
**Commit:** `9e9dc2de3f1ecfa591db5d6c29e6543707928cb7`  
**Generated:** 2026-10-10 02:53:43 UTC  
**Research scope:** prediction-only screening; no options strategy or trading P&L tested.

## Outcome

The registered walk-forward batch completed and the output validator passed. An independent tester downloaded the immutable artifact, checked the row-level panel and source hashes, recomputed all reported candidate metrics, and independently reproduced the moving-block family p-values.

**Scientific conclusion: no candidate is statistically promoted.** All five horizon-family tests are non-significant and all Bonferroni-adjusted p-values are 1.0. The final untouched holdout remains unopened. Phase 8 and strategy development remain blocked.

## Dataset and methods

- NIFTY daily history: 1,676 rows, 2020-01-01 through 2026-10-09.
- Global/peer source series: 11/11 active; each spans 2018 through 2026-10-09. The global equity composite had four eligible constituents.
- Registered horizons: 1, 2, 3, 5 and 10 sessions.
- Registered methods: 12 per horizon; 60/60 method-horizon cells executed.
- Out-of-sample rows per horizon: 1,421; 1,419; 1,418; 1,414; and 1,404.
- Prediction panel: 91,988 rows.
- Walk-forward settings: minimum training prefix 252 sessions, test block 20 sessions, moving-block bootstrap 500 replicates, block length 20, seed 42.
- Source availability rule: source-local session date strictly earlier than the NIFTY decision session.
- Final untouched holdout: not opened.

## Best Brier-score candidate per horizon

Brier improvement is baseline Brier minus candidate Brier; positive values favor the candidate. These are descriptive leaders, not statistically selected models.

| Horizon | Best candidate | N | Accuracy | Balanced accuracy | ROC AUC | Candidate Brier | Baseline Brier | Brier improvement | Family p-value | Bonferroni p-value |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 session | G13 global-equity composite | 1,421 | 52.85% | 50.07% | 0.516 | 0.249932 | 0.250201 | +0.000269 | 0.9840 | 1.000 |
| 2 sessions | G13 global-equity composite | 1,419 | 54.12% | 50.23% | 0.536 | 0.247930 | 0.248749 | +0.000820 | 0.8882 | 1.000 |
| 3 sessions | G06 Asia composite | 1,418 | 55.64% | 52.72% | 0.546 | 0.247769 | 0.249235 | +0.001466 | 0.6786 | 1.000 |
| 5 sessions | G06 Asia composite | 1,414 | 55.73% | 52.68% | 0.556 | 0.247593 | 0.249217 | +0.001623 | 0.7745 | 1.000 |
| 10 sessions | G02 Bank Nifty | 1,404 | 55.91% | 50.00% | 0.475 | 0.250089 | 0.251055 | +0.000966 | 0.9800 | 1.000 |

The largest observed Brier improvement is G06 at five sessions (+0.001623), with ROC AUC 0.556. Its family p-value is 0.7745, so the apparent gain is not statistically persuasive after the registered family test. At ten sessions, G02's ROC AUC is below 0.5 despite a small Brier improvement. Accuracy alone is misleading here because the out-of-sample target is skewed toward positive returns; several balanced-accuracy values are close to 0.50.

## Family-level inference

| Horizon | Maximum observed Brier improvement | Raw family p-value | Bonferroni-adjusted p-value |
|---:|---:|---:|---:|
| 1 | 0.000269 | 0.9840 | 1.000 |
| 2 | 0.000820 | 0.8882 | 1.000 |
| 3 | 0.001466 | 0.6786 | 1.000 |
| 5 | 0.001623 | 0.7745 | 1.000 |
| 10 | 0.000966 | 0.9800 | 1.000 |

The registered common-row paired moving-block bootstrap used a max statistic across 12 methods per horizon and 500 replicates. The independent tester reproduced each observed maximum and raw p-value exactly from the panel. There is no evidence to reject the family null at any horizon.

## Independent artifact checks

- Run #44 completed successfully in all three jobs: fixture regressions, exact-snapshot authorization, and empirical prediction/validation/upload.
- NIFTY CSV SHA-256: `08b8b72117b70140cfdabf9b3cf78d315aff736858a3ac51c5edf7b55df559b4`.
- Source manifest SHA-256: `0564e64cb4402ae00162927c04704cbb689b4a732be60ca61934769389a599c4`.
- Prediction panel SHA-256: `0dcae6aefcd21aaa8f66c610fa48451476cf2da6b1719b190b2047cc8cf4ce70`.
- 91,988 panel rows; zero duplicate composite row keys; zero probability-bound violations; zero missing candidate predictions, labels or future returns; zero target-sign mismatches.
- Independent recomputation of accuracy, balanced accuracy, ROC AUC, PR AUC, Brier score and log loss matched the results JSON within (10^{-10}).

## Data and interpretation limitations

The source manifest identifies Yahoo Finance's free chart endpoint as a historical research reference, not execution data. NIFTY was checked against official NSE archive values at the two dates registered in the acquisition code; this is not full exchange-certified history. All 11 global source entries reported `cache_hit: false` during this run, consistent with the prior cache being rejected under the current schema/freshness contract and reacquired. The post-cache step completed, so later runs should verify cache reuse rather than assume it.

This batch does not test options data, option-chain features, brokerage, taxes, slippage, spreads, liquidity, fills, sizing, drawdowns, or Paytm Money execution. No trading profitability claim follows from these classification/probability metrics.

## Artifact and audit references

- [Immutable Run #44 and artifact](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38018506915)
- [Independent tester report — tester branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md)
- [Mirrored tester report — developer branch](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-developer/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md)

## Decision

**Do not promote G06, G13, or any other method. Do not open the final holdout or advance to Phase 8.** The correct conclusion for this registered family is negative: observed improvements are small and statistically non-significant. Further research, if pursued, must start as a new preregistered prediction phase with new hypotheses and a separate tester gate. Strategy research must separately model option payoffs and realistic execution costs.

**Developer → Tester:** Independently check the result summary against Run #44's immutable JSON/panel and preserve the non-promotion decision.

**Tester → Developer:** No candidate is cleared for strategy work. Any new family must be preregistered and reviewed before execution; keep the final holdout untouched.
