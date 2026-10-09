# Phase 8 Run #807 — Historical Reconstruction Tester Review

**Decision: REQUEST CHANGES — empirical authorization remains blocked**

- Workflow: [Research Protocol Check #807](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37876792124)
- Developer head: `559af131d75a6fc256afd9ba09eb2792653fea8c`
- Run conclusion: FAILURE. Protocol, regression, free-source audit, immutable Run #654 artifact verification, and execution-engine regression succeeded. Forecast reconstruction failed, so forecast-panel validation and empirical authorization were skipped.
- Hosted reconstruction environment: Python 3.11.16; NumPy 2.4.6; pandas 3.0.6; scikit-learn 1.9.1; SciPy 1.17.1; pyarrow 25.0.1; threadpoolctl 3.7.0. Thread limits were set to 1 for OPENBLAS, OMP, MKL and NUMEXPR.
- Exact failures under frozen absolute tolerance (10^{-9}):
  - Intraday H=60, P07 chronological block 33: actual Brier 0.24826251046324826; reference 0.2482625195704263; absolute difference about (9.1072\times10^{-9}).
  - Intraday H=60, P07 chronological block 55: actual Brier 0.2516896144464828; reference 0.2516896166236784; absolute difference about (2.1772\times10^{-9}).
- Therefore, pinning Python and constraining numerical thread pools did not resolve the historical mismatch. The cause remains unproven; do not assert it is definitely a solver or runtime issue.
- The immutable reference artifact, metric calculation, and (10^{-9}) tolerance must remain unchanged. No rounding, tolerance widening, metric patching, or empirical grid execution is allowed.

## Required developer response

1. Preserve this run as non-evidence and attach its logs/artifact metadata to the developer-side record.
2. Investigate whether the reference aggregates can be reproduced from the exact immutable Run #654 per-row predictions/labels and frozen aggregation code, independently of refitting the model. Identify the actual source of the two differences before proposing a scientific change.
3. Add tests that reproduce the exact historical aggregation path, not just synthetic repeated-fit determinism.
4. Submit a narrowly scoped diagnosis and proposed correction for tester review before any new hosted reconstruction attempt.
5. Keep the 4,800-cell empirical grid, P&L generation and candidate selection blocked.

**Tester → Developer:** do not rerun empirical execution. Submit a reproducible root-cause analysis and targeted test for review.

**Developer → Tester:** independently audit the source rows, aggregation formula, frozen artifact and proposed reproduction test; approve only if the mismatch is resolved without changing the scientific contract.
