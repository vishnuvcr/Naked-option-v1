# PM0051 extended diagnostic addendum — 2026-10-14

The prior independently approved PM0051 bundle remains immutable; its PASS only covered log-loss inference. Before selecting another prediction model, a fresh run must add threshold-0.5 directional accuracy and TP/FP/TN/FN against the thresholded training-fold class-prior baseline; balanced accuracy, precision, recall, specificity and F1; reliability bins, ECE/MCE; Brier/ROC-AUC/average precision; paired per-session accuracy-difference uncertainty; and descriptive regime analysis.

Secondary accuracy inference: paired per-exchange-session correctness difference; 10-session moving-block bootstrap, 10,000 replicates, seed 2026101417, 95% interval; Benjamini–Yekutieli q=.05 within each frozen label family. Primary confirmatory outcome remains session-weighted out-of-sample log loss.

Regimes: trailing 20 completed-session realized volatility and close-to-close trend, each split at training-session terciles only. Missing daily close context is excluded without imputation. Regime results are descriptive, not a model-selection criterion. Do not persist observation-level predictions or access the final holdout.