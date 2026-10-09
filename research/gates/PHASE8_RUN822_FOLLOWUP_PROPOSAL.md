# Phase 8 Run #822 follow-up proposal — eliminate cross-runtime replay dependence

**Status: SUBMITTED FOR INDEPENDENT TESTER REVIEW**  
**Scope:** reconstruction evidence protocol only. No change to P01–P10 definitions, statistical tests, 1e-9 tolerance, costs, or empirical authorization.

## Evidence reviewed

1. Immutable Phase 7 Run #654 (run ID 37763242007; artifact ID 11551679532) was produced on Python 3.11.16 with NumPy 2.4.6, pandas 3.0.6, scikit-learn 1.9.1, SciPy 1.17.1, pyarrow 25.0.1 and threadpoolctl 3.7.0. Its runner image was Ubuntu 24.04 image release 20260927.320.1.
2. Run #807 used Python 3.11.16 and the same listed package versions, with BLAS/OpenMP thread counts pinned to one, but ran on Ubuntu 24.04 image release 20261004.327.1. It reproduced the same two P07 intraday H=60 block-Brier mismatches. The Python/thread-limit change therefore did not resolve the discrepancy.
3. Run #654's acquisition log reports Hugging Face dataset revision `0f4800e43e6f96cec0794369d78eb4d3c4211ef5` and normalized source SHA-256 `5f5c91b1c29db13ccaa6ffbb3a83a526a82bedf30092e9b9585384efcec5f6d2`. Run #807 reports the same revision and SHA-256. The Phase 3 daily/intraday loader and Phase 6 dependency source blobs also match the Run #654 commit.
4. The immutable Run #654 artifact contains only `phase7_ensemble_results.json` (aggregate metrics), not the row-level predictions that would allow exact downstream replay without refitting.
5. Run #822 is the authorized diagnostic-only attempt and remains the current active hosted attempt at proposal time. Its row-level panel/diagnostic should be retained if the job finishes; it is not empirical authorization.

## Assessment

The mismatch is repeatable and extremely small, and neither Python patch pinning nor single-thread BLAS controls fixed it. Runner-image/runtime numerical variation is a plausible explanation but is **not proven**. Because the old artifact lacks row-level predictions and an execution fingerprint sufficient to replay its numerical output, further attempts to force exact aggregate replay by adjusting tolerances or rounding would be scientifically invalid.

## Proposed corrective path

1. Let Run #822 finish; preserve its diagnostics as failure evidence. Do not promote its reconstructed panel and do not launch the 4,800-cell option grid.
2. Create a **new, explicitly versioned Phase 7 reference artifact** in a fresh Phase 7 run. Preserve the existing Run #654 artifact unchanged and retain its historical scientific disposition.
3. In that same Phase 7 execution, persist:
   - the complete canonical row-level prediction panel for all 100 layer/horizon/method cells;
   - labels, future returns, decision timestamps and chronological-block membership;
   - source-file SHA-256 hashes, data revision/manifest, source-code Git blob hashes, dependency lock/version output, Python/platform/runner and BLAS/threadpool fingerprints;
   - the existing aggregate result JSON and a manifest linking all hashes.
4. Have the Phase 7 independent tester review the new output contract, panel/metric reconciliation, completeness and schema before accepting the new artifact as a Phase 8 input.
5. Formally amend the Phase 8 frozen-input manifest through a separate tester-approved gate to point at the new artifact ID and SHA-256. Do not mutate Run #654 or silently overwrite the old manifest.
6. Change Phase 8 reconstruction to consume the immutable row-level prediction panel rather than refit P07 models on a later runner. Verify exact row keys, labels, predictions, hashes, block aggregates and all registered cells against the paired aggregate JSON. Keep the 1e-9 numerical acceptance rule for metrics calculated from the saved panel; no tolerance relaxation.
7. Require a fresh independent Phase 8 tester report on the amended manifest, panel integrity and cost-aware execution engine before any empirical option-grid authorization. Empirical authorization remains false until every required gate passes.

## Acceptance criteria

- Run #654 remains immutable and its prior statistical conclusions are unchanged.
- New reference artifact is complete and internally reconciles: 100 cells, exact row counts/keys, all source hashes and all aggregate diagnostics reconciled.
- Panel is generated and aggregate JSON in the same execution, avoiding cross-runtime refitting.
- Tester approves both the Phase 7 artifact and the Phase 8 manifest/code amendment.
- No 4,800-cell execution or option P&L until the independent tester explicitly authorizes it.

## Rollback / stop conditions

If row-level panel generation is incomplete, source hashes are absent, aggregates fail to reconcile, or tester requests changes, stop at the reconstruction gate, log the failure, and do not run the empirical grid. Do not weaken tolerance, alter old results, or label the mismatch as resolved without evidence.
