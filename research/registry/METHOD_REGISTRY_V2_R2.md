# Prediction Method Registry V2 — R2

**Status: DRAFT — INDEPENDENT TESTER REVIEW REQUIRED; NO EMPIRICAL EXECUTION AUTHORIZED.**

- 1,000 method definitions: 20 algorithm/architecture families × 10 causal feature representations × 5 inference operators.
- 8,000 configurations: 2 label strata × 2 lookbacks (20/60 bars) × 2 model-family-specific complexity presets for each method.
- Label IDs: `INTRA_30M_UP_DOWN` and `POS_1D_UP_DOWN`; definitions and common label rules are in `PREDICTION_LABEL_MANIFEST_V2_R2.json`.
- Registry: `METHOD_REGISTRY_V2_R2.json`.
- Configuration manifest: `PREDICTION_CONFIG_MANIFEST_V2_R2.json`; 4 shards of 2,000 configs each are listed with hashes and ID ranges.
- Probability output uses native probabilities where available and otherwise training-fold-only Platt scaling fitted within inner chronological training folds. Survival methods map cause-specific hazards to directional cumulative incidence.
- Every method and config is NOT_RUN. The registry is not accepted until the tester verifies uniqueness, compatibility, label rules, hashes, full shard coverage and resource feasibility.

**Developer → Tester:** independently validate method distinctness, all 16,000 configurations, hash integrity, probability calibration compatibility, label rules and resource budget. No empirical fitting.

**Tester → Developer:** hash-pinned PASS/REQUEST CHANGES. Empirical batches remain blocked until the registry, manifest and synthetic runner gates pass.