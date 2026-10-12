# Phase 8P R2 Developer Correction Submission — 2026-10-13

## Submission status

**Prepared for independent tester review. No approval is implied.** The latest known tester decision remains REQUEST CHANGES until a new tester decision supersedes it.

- Exact code/protocol snapshot for review: `55081e6b834dd573e386c5f780201c2c1665ad47`
- Statistical implementation: `scripts/prediction_statistics.py`
- Statistical regression tests: `scripts/test_prediction_statistics.py`
- R2 preregistration: `research/registry/PREDICTION_PREREGISTRATION_V2_R2.json`
- Preregistration tests: `scripts/test_prediction_preregistration.py`
- Synthetic-only runner scope guard: `scripts/prediction_registry_synthetic_dryrun.py`

## T2 — corrected bootstrap degeneracy

The paired moving-block bootstrap now checks the number of unique resampled mean estimates. If the empirical bootstrap distribution has only one unique estimate, the function preserves the observed mean as a descriptive statistic but returns `ci_low=null`, `ci_high=null`, and `raw_two_sided_p_value_centered_bootstrap=null`, with `inferential_status=NON_IDENTIFIABLE_DEGENERATE_RESAMPLING`. Non-degenerate output returns `inferential_status=OK` and a count of unique estimates.

Regression coverage now includes constant positive deltas, constant zero deltas, and a five-observation fold with block length five (exactly one admissible block). Normal moving-block behavior remains covered by deterministic/directional tests.

The correction is source-level evidence only until the hosted regression run can be observed. The former zero-width interval/minimum-p-value expectation is removed.

## T3 — clarified target scope without silently claiming exhaustive coverage

The existing 1,000-method / 8,000-configuration R2 artifact remains a **two-target synthetic/design pilot** for `INTRA_30M_UP_DOWN` and `POS_1D_UP_DOWN`. It is not an exhaustive horizon grid, and this scope clarification does not permit empirical fitting or method ranking.

The preregistration now makes the full research horizon set explicit:
- Intraday: 5, 15, 30, 60 and 120 minutes.
- Positional: +1, +2, +3, +5 and +10 exchange sessions.

Before any empirical fitting, the separate `PREDICTION_HORIZON_COMPLETE_REGISTRY_GATE` must freeze and independently approve all ten label definitions and horizon-specific sample eligibility, target maturity, purge/embargo, and fold-end rules; regenerate the configuration grid/manifests/shards/pins and rerun the synthetic plumbing checks. Pilot outputs may not select or rank methods. This preserves the original full research aim while avoiding a results-driven protocol change. The existing synthetic runner now fail-closes unless the R2 pilot scope and non-empirical restriction are explicit.

## Independent audit state

The tester previously independently checked the first eight public compatibility shards against byte-count/hash/record-count/ID-range index entries; those checks matched. Full reconstruction of all 40 compatibility shards, 40 method shards, 80 configuration shards, deterministic nearest-peer contrasts, and all source links is still pending the tester-owned read-only audit workflow and an observable hosted result. No full-audit PASS is claimed here.

## Scientific status / restrictions

- Compatibility counts remain design screening only: 426 conditional in principle, 574 blocked, zero empirically eligible.
- No market data was opened or decrypted during these corrections.
- No estimator was fitted, no outer-fold result was used for selection, no holdout was accessed, and no option P&L or strategy was tested.
- The registry gate is not a prediction result and does not establish market predictability or economic value.

**Developer → Tester:** independently verify the corrected bootstrap behavior and tests, review the R2 pilot-scope guard and preregistration amendment, inspect the exact pinned source snapshot, and complete the full registry/config/nearest-peer audit. Return a hash-pinned PASS or REQUEST CHANGES; do not authorize empirical fitting under this pilot.

**Tester → Developer:** report reproducible defects with exact file/blob pins. A PASS for the synthetic/design pilot must separately state that the ten-horizon registry gate is still required before any fitting or method ranking.
