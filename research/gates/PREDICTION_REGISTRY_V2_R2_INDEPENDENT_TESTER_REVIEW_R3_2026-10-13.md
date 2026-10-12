# Independent Tester Review — Prediction Registry R2 — 2026-10-13

## Decision

**REQUEST CHANGES. No empirical model fitting, encrypted-data access, model selection, holdout access, option P&L, or strategy promotion is authorized.**

- Developer branch: `phase-08-prediction-developer`
- Review request snapshot: `503af0a4c6af98aec2c2a41b633cedc50df75d34`
- Declared tested-source commit: `32cad4b775133436f809a684a6b916cd3f6d00b4`
- Submitted request: `research/gates/PREDICTION_REGISTRY_V2_R2_REVIEW_REQUEST_R2_2026-10-12.json`
- Statistical implementation blob SHA-1: `3b36b21ed3d7c47a6b58e5f95c6b6f6861e0c776`
- Statistical test blob SHA-1: `5512c48863442c2cf835b7a3c018aabd8a5b5164`
- Label-manifest blob SHA-1: `eca01d604afa3db3fcb86e962ca3a579c85a35dc`

## Blocking finding T2 — degenerate block-bootstrap inference

In `scripts/prediction_statistics.py`, `paired_moving_block_bootstrap` permits a fold containing exactly `block_length` sessions. With `n = block_length = 5`, only one non-circular block start exists, so every replicate is identical. The routine still returns a zero-width confidence interval and the smallest plus-one p-value, which can be below 0.05 despite the resampling distribution containing no inferential variation.

The existing regression test `test_constant_positive_improvement_and_too_short_fold` explicitly enshrines the degenerate case by expecting a zero-width CI and `1/(replicates+1)` p-value for constant positive deltas. This output must not be interpreted as significant evidence. The function should fail closed with an explicit non-identifiable/degenerate status and null inferential outputs whenever the resampling support has no variation (including `n == block_length)); add tests for constant positive, constant zero, and one-admissible-block folds. Keep descriptive mean improvement separate from inference.

## Blocking scope finding T3 — prediction horizon coverage is incomplete

`PREDICTION_LABEL_MANIFEST_V2_R2.json` defines only `INTRA_30M_UP_DOWN` and `POS_1D_UP_DOWN`. The earlier frozen prediction scope names intraday horizons 5/15/30/60/120 minutes and positional horizons +1/+2/+3/+5/+10 exchange sessions. The R2 eight-thousand-configuration grid therefore is not, by itself, evidence that the full frozen horizon scope is covered. Either (a) explicitly scope R2 as a two-target registry pilot and avoid an exhaustive-coverage claim, or (b) freeze target definitions, labels and configurations for the full horizon set before fitting any model. Do not add horizons after viewing results.

## Audit progress and limits

- The first eight published compatibility shards were independently fetched and checked for exact UTF-8 byte counts, SHA-256 digests, 25 records per shard, and contiguous method-ID ranges; all eight matched their index entries.
- The full 40-shard/1,000-row reconstruction, all 80 configuration shards, the deterministic nearest-peer contrast calculation, and family/operator compatibility are **not yet independently signed off**. A tester-owned read-only audit script and workflow have been added on the tester branch to finish this check against a separate checkout of the developer branch. Until its artifact is reviewed, no claim of full independent reconstruction is made.
- The developer's CI passes establish integrity/synthetic plumbing only. They do not establish prediction skill, statistical significance, economic value, or permission to fit a model.
- No market data was opened; no estimator was fitted; no holdout was accessed.

## Required correction and re-review

1. Developer corrects the degenerate bootstrap behavior and tests, preserving the mean as descriptive output while returning no CI/p-value when inference is non-identifiable.
2. Developer resolves the target-horizon scope gap explicitly in the preregistration/manifest before any empirical run.
3. The tester-side audit artifact is reviewed against the exact developer branch snapshot and its hashes.
4. Submit a new hash-pinned tester request. The existing REQUEST CHANGES decision remains authoritative until superseded by a new tester decision.

**Tester → Developer:** fix T2, resolve T3 in the frozen protocol, preserve this report and rerun only non-empirical integrity/statistical tests; submit exact changed blob hashes.

**Developer → Tester:** independently inspect the changed source and tests, review the full audit artifact and label scope, and issue a new hash-pinned decision. Keep all empirical and holdout gates closed until PASS.
