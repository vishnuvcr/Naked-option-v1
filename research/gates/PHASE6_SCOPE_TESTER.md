# Phase 6 Scope — Independent Tester Review

Date: 2026-10-07
Tester branch: `phase-05-tester`
Developer submission: `4d73b8303996e2a6cea2692bee844641d5f1cdb6`
Reviewed file: `research/gates/PHASE6_SCOPE_DEVELOPER_SUBMISSION.md`

## Decision

**REQUEST CHANGES — NO EMPIRICAL EXECUTION YET**

## Checks

### Passed
- Family E (E01-E10) and Family I (I01-I10) match the existing finite method registry.
- The submission correctly preserves Phase 3 frozen labels/horizons and the tester-approved intraday hourly decision grid / 20-session refit cadence where applicable.
- The data policy correctly allows BLOCKED_DATA rather than proxy substitution when PIT-safe inputs are unavailable.
- The submission correctly prevents use of the final holdout and reserves economic/option promotion for later gates.
- The workflow deliverables include regression tests, schema validation, immutable artifact upload and tester review.

### Required changes before implementation/execution

1. **Exact method definitions are not yet frozen.**
   Registry names alone are not sufficient pre-registration for E/I methods. Before code or empirical execution, the developer must specify deterministic mathematical/algorithmic definitions for each E/I method that will be executed, including:
   - window lengths/scales;
   - estimator variants and normalization;
   - thresholds/cutpoints;
   - state-count rules;
   - transition rules;
   - random seeds where applicable;
   - missing-data behavior;
   - any aggregation/weighting formula.

2. **Causality regression tests are required for derived novelty features.**
   Every feature construction that uses rolling/entropy/MFDFA/information-flow/lead-lag or regime windows must have a future-row mutation test demonstrating that a value at time t is unchanged when rows after t are modified. No centered/symmetric window may be used.

3. **E08 switching policy must be frozen before results.**
   The switching rule cannot be chosen from observed model performance. The base-model set and regime-to-model mapping must be specified ex ante, with training-only estimates where needed.

4. **I08-I10 need explicit composition rules.**
   Entropy-weighted confidence and the composite Direction Conviction State are especially vulnerable to result-driven weighting. Exact component lists, weights/normalization, and aggregation rules must be frozen before empirical execution.

5. **I07 needs a hard data-availability rule.**
   Probability-of-move-vs-premium efficiency can execute only when PIT-safe option premium/liquidity inputs exist at the decision timestamp. Otherwise it must be BLOCKED_DATA; no retrospective proxy may be invented during the run.

6. **Information-theoretic estimators must report estimator configuration.**
   E01-E07/I08 must persist estimator family, window size, discretization/binning or k-neighbor settings, bias correction where applicable, and a deterministic seed/configuration record.

## Disposition

The Phase 6 research direction is sound, but the method layer is not sufficiently specific for scientific execution. No empirical metrics should be generated from this scope until the exact definitions and causality tests are frozen and re-submitted.

## Developer → Tester

Revise the Phase 6 scope/specification with exact method definitions, data availability rules and causal regression tests, then resubmit for an independent scope gate. Do not launch a Phase 6 workflow before approval.

## Tester → Developer

After resubmission, independently inspect the exact formulas/configuration and the planned regression tests; issue a new gate before any Phase 6 empirical run.
