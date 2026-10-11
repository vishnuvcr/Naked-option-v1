# Tester Review — MR-0 to MR-5 Feasibility Runner R7

**Date:** 2026-10-11  
**Verdict:** PASS_WITH_SCOPED_RESTRICTIONS — implementation/synthetic scope only  
**Reviewed developer commit:** `cb924f9edcea21f1fb91355fe5d75774d6fa5ca3`

## Exact reviewed blobs

- Runner: `578f80335c23186eb97e0fd4c51df37af48558f9`
- Tests: `d9452814dcf8241c2fbe5e2683abed1a7e367477`
- Report schema: `1bcecc1b2af9cfb95fcb8d440cd59c15ea0674fe`
- Synthetic workflow: `c47fad18419fadeeb08d3d26a88789c3ba245786`

## Verification

- Hosted synthetic Actions run [38153160558](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38153160558) succeeded on the exact reviewed commit.
- The 13-test regression suite passed, including synthetic tests for missing holdout boundary, timestamp/close-linkage evidence, label-purge flags, minimum-origin claims, recomputed per-split counts, common validation origins, nested report-schema validation, and bounded prefix parsing.
- CLI self-test and workflow-boundary checks passed. The workflow has read-only repository permissions and a manual dispatch trigger.
- The scanner now computes per-horizon training/validation eligible labels using split-endpoint purging, computes the intersection of validation origins across horizons, compares these computed values to the pinned split manifest, and reports `NOT_ESTIMABLE` when computed minimum counts are not met.
- No real dataset was parsed in the hosted run. No fitting, tuning, prediction scoring, holdout observation access, source requests, strategy P&L or trading occurred.

## Restrictions that remain

1. **No real-data execution is authorized by this decision.** It approves only the synthetic implementation and its deterministic offline behavior. The manifest's close-linkage evidence record is structurally validated and bound to the pinned source manifest, but the referenced source/validation artifacts still need to be present and verified as part of a separately authorized data audit.
2. **The PPR-4 holdout audit remains blocking.** The repository's current PPR-4 record says no machine-readable holdout boundary was found. Do not infer one from prose, calendar dates, or split claims. No runner invocation against the composite is allowed until a valid byte-level boundary and provenance manifests are available and exact-hash execution authorization is separately reviewed.
3. This pass is not a model result or a prediction-accuracy claim. It says nothing about whether any forecast method works.

## Decision

**Allowed:** maintain the implementation, run synthetic CI, and continue metadata-only discovery for cached boundary/provenance artifacts without opening market/holdout rows or requesting new sources.

**Not allowed:** real-file feasibility scan, model fitting/tuning/scoring, holdout access, new source requests, strategy/P&L, or trading.

**Tester → Developer:** The implementation gate passes for synthetic/offline scope. Keep the empirical gate closed and proceed only to a bounded, metadata-only search for existing valid boundary/provenance artifacts.  
**Developer → Tester:** Review any newly found artifact by exact hash and keep real-data execution unauthorized until a separate execution decision explicitly permits it.
