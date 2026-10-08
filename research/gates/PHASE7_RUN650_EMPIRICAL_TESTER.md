# Phase 7 Run 650 — Independent Empirical Tester Gate

**Status: REQUEST CHANGES**

The latest complete Phase 7 artifact from Run #650 (`37723308187`) was independently inspected. Artifact ID `11532515562`, digest `sha256:47c4423d6dc1782930cac7aab4bf733b6497bdd05198fa51ef770a5c16b4aff2`.

## What passed

- Hosted protocol, dependency installation, data cache and daily/intraday/global acquisition passed.
- Phase 7 regression suite passed.
- Empirical execution, artifact validation and upload passed.
- Complete registered grid is present: 2 layers × 5 horizons × 10 candidates = **100 candidate cells**.
- All 100 candidate cells are EXECUTED with positive sample counts.
- Confusion counts reconcile to `n` across candidate cells.
- Accuracy, balanced accuracy, Brier, ROC-AUC and PR-AUC are finite and within valid ranges.
- Accuracy block-bootstrap interval ordering is valid.
- Chronological block diagnostics are present.
- Family bootstrap p-values are within [0,1].
- P08/P09/P10 contain regime diagnostics and fallback counts.

## Independent findings requiring correction

### 1. Family bootstrap is not the frozen moving-block bootstrap
The specification freezes a **moving-block bootstrap**. The production implementation instead partitions the series into non-overlapping blocks starting at indices `0, block_len, 2*block_len, ...` and resamples only those blocks.

That is a fixed non-overlapping block bootstrap, not the registered moving-block construction. The family p-values therefore cannot yet be accepted as the declared data-snooping test.

**Required correction:** construct the full set of overlapping contiguous blocks of length `block_len` (with an explicitly defined deterministic tail rule), sample those blocks with replacement to rebuild length `n`, and retain the frozen 500 replications and seed 42. Add a numerical regression test proving the candidate block-start set contains overlapping starts and the resample always has length `n`.

### 2. Regime diagnostic count mismatch
For daily horizon +10, P08/P09/P10 contain 73 regime diagnostic entries but only 72 chronological metric blocks. The extra regime diagnostic corresponds to a partial terminal block that does not contribute to the candidate's recorded chronological metrics.

This is an auditability mismatch rather than evidence of predictive edge, but the stored diagnostics should reconcile one-to-one with the evaluated chronological blocks.

**Required correction:** retain regime diagnostics only for blocks with at least one evaluated finite candidate/label observation, and add a regression/schema assertion that regime-diagnostic block count equals chronological-block count for P08-P10.

## Scientific disposition

No Phase 7 candidate is promoted. No trading strategy is accepted. Run #650 remains a **NON-FINAL EMPIRICAL EVIDENCE PACKAGE** pending the two corrections above and a fresh hosted execution.

The previous successful Run #647 artifact is also not accepted as final because it uses the same frozen implementation mismatch.

**Tester → Developer:** correct only the two identified implementation/auditability issues, log Run #650, obtain a fresh tester code approval, and rerun the complete Phase 7 empirical gate. Do not select or promote a candidate from the current artifact.