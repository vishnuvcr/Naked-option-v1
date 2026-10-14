# PM0001 NIFTY 50 Prediction Results — R3

- Bundle status: \`COMPLETE_TERMINAL_ACCOUNTING_NO_EMPIRICAL_FIT\`
- Results acquired: \`false\`
- Source data SHA-256: \`cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204\`
- Execution source commit: \`2eeb36952b9b236114a10f83286842be61767686\`
- Workflow run ID: \`38524306506\`
- Scope: 40 preregistered PM0001 configurations × 8 chronological outer folds.
- Primary metric: session-weighted out-of-sample log loss; improvement = class-prior baseline minus PM0001.
- Statistical inference: paired 10-session moving-block bootstrap (10,000 replicates), Benjamini–Yekutieli q=0.05 within each label stratum.
- The prior-sign baseline remains null because no definition is frozen in the preregistration; no comparator was invented.
- No untouched holdout was accessed. No raw market rows or per-observation predictions are published.

## Terminal accounting

| Terminal status | Count |
|---|---:|
| BLOCKED_GATE | 320 |

## All registered PM0001 configurations

Each config is shown; this is not a performance-based model selection or trading-strategy evaluation.

| Config ID | Label | Lookback | C | Executed folds | Blocked/failed folds | Mean fold log loss | Mean fold improvement | Inference status | Mean session improvement | 95% bootstrap CI | Raw p | BY-adjusted p | BY q=.05 reject |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---|
| CFG0001_INTRA_120M_UP_DOWN_20_FLEXIBLE | INTRA_120M_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_120M_UP_DOWN_20_REGULARIZED | INTRA_120M_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_120M_UP_DOWN_60_FLEXIBLE | INTRA_120M_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_120M_UP_DOWN_60_REGULARIZED | INTRA_120M_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_15M_UP_DOWN_20_FLEXIBLE | INTRA_15M_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_15M_UP_DOWN_20_REGULARIZED | INTRA_15M_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_15M_UP_DOWN_60_FLEXIBLE | INTRA_15M_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_15M_UP_DOWN_60_REGULARIZED | INTRA_15M_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_30M_UP_DOWN_20_FLEXIBLE | INTRA_30M_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_30M_UP_DOWN_20_REGULARIZED | INTRA_30M_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_30M_UP_DOWN_60_FLEXIBLE | INTRA_30M_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_30M_UP_DOWN_60_REGULARIZED | INTRA_30M_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_5M_UP_DOWN_20_FLEXIBLE | INTRA_5M_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_5M_UP_DOWN_20_REGULARIZED | INTRA_5M_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_5M_UP_DOWN_60_FLEXIBLE | INTRA_5M_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_5M_UP_DOWN_60_REGULARIZED | INTRA_5M_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_60M_UP_DOWN_20_FLEXIBLE | INTRA_60M_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_60M_UP_DOWN_20_REGULARIZED | INTRA_60M_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_60M_UP_DOWN_60_FLEXIBLE | INTRA_60M_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_INTRA_60M_UP_DOWN_60_REGULARIZED | INTRA_60M_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_10D_UP_DOWN_20_FLEXIBLE | POS_10D_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_10D_UP_DOWN_20_REGULARIZED | POS_10D_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_10D_UP_DOWN_60_FLEXIBLE | POS_10D_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_10D_UP_DOWN_60_REGULARIZED | POS_10D_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_1D_UP_DOWN_20_FLEXIBLE | POS_1D_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_1D_UP_DOWN_20_REGULARIZED | POS_1D_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_1D_UP_DOWN_60_FLEXIBLE | POS_1D_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_1D_UP_DOWN_60_REGULARIZED | POS_1D_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_2D_UP_DOWN_20_FLEXIBLE | POS_2D_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_2D_UP_DOWN_20_REGULARIZED | POS_2D_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_2D_UP_DOWN_60_FLEXIBLE | POS_2D_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_2D_UP_DOWN_60_REGULARIZED | POS_2D_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_3D_UP_DOWN_20_FLEXIBLE | POS_3D_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_3D_UP_DOWN_20_REGULARIZED | POS_3D_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_3D_UP_DOWN_60_FLEXIBLE | POS_3D_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_3D_UP_DOWN_60_REGULARIZED | POS_3D_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_5D_UP_DOWN_20_FLEXIBLE | POS_5D_UP_DOWN | 20 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_5D_UP_DOWN_20_REGULARIZED | POS_5D_UP_DOWN | 20 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_5D_UP_DOWN_60_FLEXIBLE | POS_5D_UP_DOWN | 60 | 1.0 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |
| CFG0001_POS_5D_UP_DOWN_60_REGULARIZED | POS_5D_UP_DOWN | 60 | 0.1 | 0 | 8 | NA | NA | NO_EMPIRICAL_FIT | NA | NA | NA | 1 | false |

## Interpretation boundary

A positive primary effect means lower log loss than the training-fold prevalence baseline. It does not, by itself, establish a tradable edge or an option strategy. Any model conclusions require complete fold coverage, paired uncertainty intervals, multiplicity-aware inference and independent review.
