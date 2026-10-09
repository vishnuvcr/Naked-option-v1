# Independent Tester Report — Phase 7 Run #925 Empirical Artifact

**Decision: REQUEST CHANGES — DO NOT ACCEPT EMPIRICAL RESULTS OR PROMOTE ANY CANDIDATE**

Date: 2026-10-09  
Immutable empirical run: [Research Protocol Check #925](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37914905848)  
Run ID: `37914905848`  
Artifact source commit: `682eadf2a9eb4de250bc3db27d02e57f88687fa1`  
Auditor implementation commit: `1d9f85c574d9fe49025b8cd01e7e71e82a2bf7b9`  
Latest complete independent audit: [Research Protocol Check #943](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37935031119)

## Scope and evidence

The tester downloaded the immutable row-level reference and aggregate-results artifacts produced by Run #925, reacquired the source snapshot using the pinned source acquisition programs, verified artifact/code/source hashes, independently reconstructed source labels, future returns and timestamps, and recalculated metrics and family-level inference from the saved panels.

Latest corrected audit report: 2,775 checks passed and 323 checks failed. The failures arise mainly from a small number of protocol/implementation mismatches repeated across the registered horizons, not 323 independent defects. Source hashes, code hashes, panel hashes, panel identity/count, timestamps, source-derived labels and future returns reconciled. The aggregate metrics and inferential outputs do not fully reconcile with the frozen specification.

## Material findings

### 1. P10 abstention rule is not implemented

The frozen Phase 7 specification says P10 abstains when its probability lies in the inclusive interval [0.45, 0.55]. The production candidate registry uses `P10 = P09.copy()`, but the production abstention registry contains only P05 and P06. Consequently, the published P10 sample sizes and metrics include rows that the frozen protocol says should be abstentions.

**Required correction:** keep P10's raw probabilities in the reference panel; apply the registered [0.45, 0.55] abstention mask to P10 headline metrics, abstention counts/coverage, probability-bin diagnostics and any trading-like diagnostic. Update family inference so P10 has zero loss differential on eligible abstention rows and missing values outside eligible evaluation rows. Add explicit regression tests at both interval endpoints and immediately outside them.

### 2. Regime-state training includes rows with missing regime inputs

In `regimes()`, the state masks compare `vol > cutoff` and `trend > cutoff` and convert the comparisons to integers without requiring finite volatility and trend first. Comparisons involving NaN become false, so early observations with unavailable regime features are counted in the low-volatility/low-trend state. For daily H=1, for example, the published first block records 76 labels in state 00 while an independently reconstructed finite-input count is 56. The same discrepancy recurs across all ten registered layer/horizon cells.

**Required correction:** include only rows with finite labels, volatility and trend when estimating regime-specific rates/counts. Compute the pooled training rate from the protocol-eligible training labels, use it for any state with fewer than 50 eligible labels, and preserve the frozen training-only cutoffs. Add tests that ensure NaN regime inputs cannot enter any of the four state counts.

### 3. P05/P06 chronological diagnostics ignore their abstention masks

The main P05/P06 metrics apply their abstention masks, but `block_diagnostics(y,p,blocks)` is called without the same mask. Thus the per-block diagnostics describe a different sample from the headline metrics, and the recorded block counts do not consistently match the eligible/trade observations.

**Required correction:** pass the candidate-specific mask into chronological block diagnostics and calculate per-block n/accuracy/balanced accuracy/Brier only on the same eligible observations as the headline metric. Preserve a separate all-row diagnostic only if it is explicitly named and documented as such.

### 4. Family-level bootstrap missingness is mishandled for abstaining candidates

For P05/P06, `family_bootstrap()` initializes a full-length differential vector to zeros, including rows where labels, forecasts or the causal baseline are not eligible. Frozen semantics allow zero differential for abstentions on eligible benchmark rows; they do not permit unavailable/non-evaluable rows to be treated as benchmark-equivalent zeros. This changes candidate means and maximum-statistic resampling. Combined with the missing P10 abstention mask, the stored candidate differential means and family p-values fail independent reconciliation.

**Required correction:** initialize differential vectors to NaN; on rows with finite outcome, probability and causal baseline, write zero for registered abstentions and the benchmark-minus-candidate Brier differential for trades/evaluable forecasts. Keep all candidates on the same moving-block indices. Recompute the complete registered family on a fresh run after code review.

## Quantitative reconciliation disposition

- All 10 registered row-level panels were present and their manifest/file hashes and source alignment reconciled.
- The independent audit attempted all 100 layer/horizon/method metric cells and all 10 family-level tests.
- P10 headline metrics fail reconciliation in all 10 panels because its required abstention rule is absent.
- Regime prediction arrays and training-state counts fail the finite-input rule in all 10 panels.
- P05/P06/P10 diagnostic/inference checks are also affected by abstention/missingness handling.
- The descriptive P08 values and the family p-values in this artifact are **not accepted results** and must not be used to advance to Phase 8.

## Required developer resubmission

1. Fix the four findings without modifying the frozen research specification, candidate universe, horizons, seeds, blocks, bootstrap replication count or thresholds.
2. Add focused regression tests for P10 interval boundaries, finite regime-state eligibility, abstention-consistent block metrics, and missing-versus-zero family differentials.
3. Run the full regression and result-schema validators.
4. Submit the exact proposed correction commit and test evidence for independent tester review before starting a fresh empirical run.
5. After code approval, run one fresh empirical execution, upload immutable artifacts, and resubmit the full source/hash/metric/family audit. Run #925 stays preserved as non-accepted evidence.

**Phase 8 stays BLOCKED. No metric, candidate model or trading strategy is promoted by this report.**

**Tester → Developer:** Correct the four findings on `phase-07-developer` only, add regression coverage, and return the exact commit for independent review before a fresh empirical run.

**Developer → Tester:** Review the correction diff and tests independently; verify the frozen protocol is unchanged, then issue PASS for fresh execution or REQUEST CHANGES. Do not permit Phase 8 until the fresh empirical artifact passes its separate gate.
