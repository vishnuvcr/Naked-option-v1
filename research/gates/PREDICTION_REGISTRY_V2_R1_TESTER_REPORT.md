# Independent Tester Review — Registry V2 R1
Date: 2026-10-12
Decision: **REQUEST CHANGES**
Reviewed method-registry commit: `2195173c4cea8146034ab90c14299370dfa88889`
Reviewed configuration-manifest commit: `76908596a4dc21b1c0b0aa9ba78f88089744e6bc`
Reviewed method records: 1,000; configurations: 2,000.
No market data was opened, no model was fitted, and no untouched holdout was accessed.

## Verified checks

- Parsed the full JSON files from the developer branch.
- Method count = 1,000; method IDs = 1,000 unique; canonical method fingerprints = 1,000 unique.
- Independent SHA-256 recomputation passed for all 1,000 method identity fingerprints.
- Configuration count = 2,000; configuration IDs = 2,000 unique; configuration hashes = 2,000 unique.
- All 2,000 configurations reference an existing parent method.
- Independent SHA-256 recomputation passed for all 2,000 configuration hashes.
- Recomputed configuration-manifest SHA-256 matches declared value `71c49148b2e5666a47cad550cd12cdc9b40bc7af46fa0817f658ea0591191240`.

## Blocking findings

### R1 — Configuration grid is too shallow to substantiate exhaustive configuration testing
Each method has only two configurations, differing only in lookback (20/60 bars). The declared 1,000-method target is represented, but this does not yet constitute a defensible model-specific configuration grid: tree depth/estimators, regularization, kernel choices, latent-state counts, neural width/regularization, survival hazards, calibration options and other family-specific settings are absent.

**Required correction:** publish a frozen finite grid with explicit model-family-specific parameter presets. Include target/horizon strata in the config manifest rather than only in method identity. For every method, enumerate at least: intraday and positional strata; two lookback choices; and two justified family-specific complexity/regularization presets where applicable. Explicitly list all parameters fixed at defaults and their values. Keep configuration counts separate from method counts.

### R2 — Probability and decision-operator compatibility is not fully specified
Some algorithms (e.g., hinge-loss SVM, nearest-centroid, survival/first-passage) do not natively produce calibrated directional probabilities in the same form. The registry assigns probability-threshold, conformal and regime-gated operators without explicitly defining the probability adapter and training-only calibration path.

**Required correction:** define a single pre-registered, training-fold-only probability adapter for non-probabilistic outputs, with calibration fitted strictly within training data. Define how survival/cause-specific hazards map to direction probability and how each abstention/conformal operator is calibrated without evaluation leakage. Add compatibility tests or explicitly mark incompatible method/operator combinations NOT_ELIGIBLE and replace them before counting toward 1,000.

### R3 — Target, label and eligibility details are deferred too far
The method identity says intraday/positional, but the configuration records do not specify exact target horizons, label construction, minimum samples, maximum missingness, class support or the eligibility rule for data-dependent representations.

**Required correction:** the configuration manifest must explicitly identify the pre-registered intraday and positional label/horizon IDs, and reference a frozen label manifest. Before empirical execution, tester must approve exact per-stratum sample/missingness/class-support rules and data dependency/PIT requirements.

## Decision

**REQUEST CHANGES — registry/configuration gate.** Hash integrity and basic counts pass; scientific configuration coverage and probability-output compatibility do not. No empirical execution is authorized.

**Tester → Developer:** revise registry/config manifest, expand model-specific grids, specify probability calibration/compatibility and exact label IDs, then resubmit.
**Developer → Tester:** provide new hashes and a synthetic-only validator; no model fitting until PASS.