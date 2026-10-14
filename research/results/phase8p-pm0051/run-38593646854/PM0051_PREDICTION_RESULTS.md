# PM0051 NIFTY 50 Prediction Results — R3

- Bundle status: \`COMPLETE_TERMINAL_ACCOUNTING_NO_EMPIRICAL_FIT\`
- Results acquired: \`false\`
- Source data SHA-256: \`cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204\`
- Execution source commit: \`2b28bbaba3155cd450e4e8a913a83655548a2ffe\`
- Workflow run ID: \`38593646854\`
- Scope: 40 preregistered PM0051 configurations × 8 chronological outer folds.
- Primary metric: session-weighted out-of-sample log loss; improvement = class-prior baseline minus PM0051.
- Statistical inference: paired 10-session moving-block bootstrap (10,000 replicates), Benjamini–Yekutieli q=0.05 within each label stratum.
- The prior-sign baseline remains null because no definition is frozen in the preregistration; no comparator was invented.
- No untouched holdout was accessed. No raw market rows or per-observation predictions are published.

## Terminal accounting

| Terminal status | Count |
|---|---:|
| BLOCKED_GATE | 320 |

## All registered PM0051 configurations

Each config is shown; this is not a performance-based model selection or trading-strategy evaluation.

| Config ID | Label | Lookback | Prior scale | Executed folds | Blocked/failed folds | Mean fold log loss | Mean fold improvement | Inference status | Mean session improvement | 95% bootstrap CI | Raw p | BY-adjusted p | BY q=.05 reject |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---|
| CFG0051_INTRA_120M_UP_DOWN_20_FLEXIBLE | INTRA_120M_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_120M_UP_DOWN_20_REGULARIZED | INTRA_120M_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_120M_UP_DOWN_60_FLEXIBLE | INTRA_120M_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_120M_UP_DOWN_60_REGULARIZED | INTRA_120M_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_15M_UP_DOWN_20_FLEXIBLE | INTRA_15M_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_15M_UP_DOWN_20_REGULARIZED | INTRA_15M_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_15M_UP_DOWN_60_FLEXIBLE | INTRA_15M_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_15M_UP_DOWN_60_REGULARIZED | INTRA_15M_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_30M_UP_DOWN_20_FLEXIBLE | INTRA_30M_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_30M_UP_DOWN_20_REGULARIZED | INTRA_30M_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_30M_UP_DOWN_60_FLEXIBLE | INTRA_30M_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_30M_UP_DOWN_60_REGULARIZED | INTRA_30M_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_5M_UP_DOWN_20_FLEXIBLE | INTRA_5M_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_5M_UP_DOWN_20_REGULARIZED | INTRA_5M_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_5M_UP_DOWN_60_FLEXIBLE | INTRA_5M_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_5M_UP_DOWN_60_REGULARIZED | INTRA_5M_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_60M_UP_DOWN_20_FLEXIBLE | INTRA_60M_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_60M_UP_DOWN_20_REGULARIZED | INTRA_60M_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_60M_UP_DOWN_60_FLEXIBLE | INTRA_60M_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_INTRA_60M_UP_DOWN_60_REGULARIZED | INTRA_60M_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_10D_UP_DOWN_20_FLEXIBLE | POS_10D_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_10D_UP_DOWN_20_REGULARIZED | POS_10D_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_10D_UP_DOWN_60_FLEXIBLE | POS_10D_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_10D_UP_DOWN_60_REGULARIZED | POS_10D_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_1D_UP_DOWN_20_FLEXIBLE | POS_1D_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_1D_UP_DOWN_20_REGULARIZED | POS_1D_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_1D_UP_DOWN_60_FLEXIBLE | POS_1D_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_1D_UP_DOWN_60_REGULARIZED | POS_1D_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_2D_UP_DOWN_20_FLEXIBLE | POS_2D_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_2D_UP_DOWN_20_REGULARIZED | POS_2D_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_2D_UP_DOWN_60_FLEXIBLE | POS_2D_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_2D_UP_DOWN_60_REGULARIZED | POS_2D_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_3D_UP_DOWN_20_FLEXIBLE | POS_3D_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_3D_UP_DOWN_20_REGULARIZED | POS_3D_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_3D_UP_DOWN_60_FLEXIBLE | POS_3D_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_3D_UP_DOWN_60_REGULARIZED | POS_3D_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_5D_UP_DOWN_20_FLEXIBLE | POS_5D_UP_DOWN | 20 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_5D_UP_DOWN_20_REGULARIZED | POS_5D_UP_DOWN | 20 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_5D_UP_DOWN_60_FLEXIBLE | POS_5D_UP_DOWN | 60 | 2.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0051_POS_5D_UP_DOWN_60_REGULARIZED | POS_5D_UP_DOWN | 60 | 0.5 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |

## Directional accuracy, discrimination, and calibration

Threshold=0.5 and comparator=training-fold class-prior probability thresholded at 0.5. Confusion counts, accuracy and balanced accuracy pool out-of-sample rows. Brier, ROC AUC and average precision are row-weighted means of fold values; AUC/AP are not pooled across folds. Accuracy-difference intervals use paired 10-session moving-block bootstrap with 10,000 replicates, seed 2026101417 and BY q=.05 within label family. Primary confirmatory inference remains log loss.

| Config ID | N | Accuracy | Balanced accuracy | Baseline accuracy | Accuracy Δ | TP / FP / TN / FN | Brier | Fold-weighted ROC AUC | Fold-weighted AP | ECE | MCE | Session-weighted accuracy | Accuracy Δ 95% CI | Accuracy Δ BY p |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|
| CFG0051_INTRA_120M_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_120M_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_120M_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_120M_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_20_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_20_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_60_FLEXIBLE | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_60_REGULARIZED | 0 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |

### Regime-stratified validation diagnostics

Volatility and trend tercile thresholds are derived from training sessions only. The context uses prior completed sessions, and missing closes are not imputed. Subgroup results are descriptive and must not drive post-hoc candidate selection.

| Config ID | Label | Axis | Regime | N | Sessions | Up / Down support | Accuracy | Balanced accuracy | Baseline accuracy | Accuracy Δ | Brier | ROC AUC | AP |
|---|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| CFG0051_INTRA_120M_UP_DOWN_20_FLEXIBLE | INTRA_120M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_120M_UP_DOWN_20_REGULARIZED | INTRA_120M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_120M_UP_DOWN_60_FLEXIBLE | INTRA_120M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_120M_UP_DOWN_60_REGULARIZED | INTRA_120M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_20_FLEXIBLE | INTRA_15M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_20_REGULARIZED | INTRA_15M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_60_FLEXIBLE | INTRA_15M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_15M_UP_DOWN_60_REGULARIZED | INTRA_15M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_20_FLEXIBLE | INTRA_30M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_20_REGULARIZED | INTRA_30M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_60_FLEXIBLE | INTRA_30M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_30M_UP_DOWN_60_REGULARIZED | INTRA_30M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_20_FLEXIBLE | INTRA_5M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_20_REGULARIZED | INTRA_5M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_60_FLEXIBLE | INTRA_5M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_5M_UP_DOWN_60_REGULARIZED | INTRA_5M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_20_FLEXIBLE | INTRA_60M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_20_REGULARIZED | INTRA_60M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_60_FLEXIBLE | INTRA_60M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_INTRA_60M_UP_DOWN_60_REGULARIZED | INTRA_60M_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_20_FLEXIBLE | POS_10D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_20_REGULARIZED | POS_10D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_60_FLEXIBLE | POS_10D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_10D_UP_DOWN_60_REGULARIZED | POS_10D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_20_FLEXIBLE | POS_1D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_20_REGULARIZED | POS_1D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_60_FLEXIBLE | POS_1D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_1D_UP_DOWN_60_REGULARIZED | POS_1D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_20_FLEXIBLE | POS_2D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_20_REGULARIZED | POS_2D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_60_FLEXIBLE | POS_2D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_2D_UP_DOWN_60_REGULARIZED | POS_2D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_20_FLEXIBLE | POS_3D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_20_REGULARIZED | POS_3D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_60_FLEXIBLE | POS_3D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_3D_UP_DOWN_60_REGULARIZED | POS_3D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_20_FLEXIBLE | POS_5D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_20_REGULARIZED | POS_5D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_60_FLEXIBLE | POS_5D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |
| CFG0051_POS_5D_UP_DOWN_60_REGULARIZED | POS_5D_UP_DOWN | NA | NA | 0 | 0 | NA | NA | NA | NA | NA | NA | NA | NA |

## Interpretation boundary

A positive primary effect means lower log loss than the training-fold prevalence baseline. It does not, by itself, establish a tradable edge or an option strategy. Any model conclusions require complete fold coverage, paired uncertainty intervals, multiplicity-aware inference and independent review.
