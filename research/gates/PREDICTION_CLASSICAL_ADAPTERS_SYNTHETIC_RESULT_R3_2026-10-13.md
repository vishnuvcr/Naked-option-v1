# Classical probability adapter synthetic gate — 2026-10-13

Status: PASS_SYNTHETIC_ONLY.

Latest hosted workflow: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38421973877

The workflow passed 19 synthetic tests across logistic regression, chronological OOF calibration, probit regression, linear discriminant analysis (LDA), and quadratic discriminant analysis (QDA). It also passed compilation and source checks for forbidden market-data/holdout references.

The LDA/QDA tests cover probability output, train-only scaling, supported shrinkage/regularization settings, invalid parameters, single-class training data, and fail-closed prediction behavior. Probit includes a finite-difference check of the penalized likelihood gradient.

No market data was loaded and no holdout was accessed. These results validate adapter mechanics only; they do not establish predictive performance or authorize empirical fitting. Next families: elastic-net logistic, tree ensembles, then margin/distance models. Complex temporal/state-space families remain separately gated.
