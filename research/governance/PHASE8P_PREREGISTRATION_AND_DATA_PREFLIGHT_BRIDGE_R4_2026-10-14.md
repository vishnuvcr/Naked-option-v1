# Phase 8P R4 — preregistration and data-preflight bridge

Date: 2026-10-14
Branch: `phase-08-prediction-prereg-freeze-developer`
Status: **synthetic/static checks only; no real artifacts opened; no model fit authorized.**

## Keep the protocols separate

- **Greek incremental study:** `research/gates/PHASE8P_GREEK_PREDICTION_SCOPE_R3_2026-10-12.md`. Twenty fixed comparisons (two estimators by ten horizons); paired Brier improvement; 500 moving-block bootstrap replicates; seed 42; Holm correction. Date-only daily predictions map to the 15:30 IST cash close under the tester-reviewed R2 amendment. No options P&L.
- **Main prediction registry R3:** `research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json`. 1,000 methods and 40,000 configurations over ten directional labels; out-of-sample log-loss; 10,000 bootstrap replicates; seed 2026101209; Benjamini–Yekutieli correction within label strata.
- **Markov transition-prior contract:** `research/registry/MARKOV_SWITCHING_TRANSITION_PRIOR_CONTRACT_V1_2026-10-14.json` applies only to `markov_switching_logit` in the main registry. The Greek incremental study does not use Markov switching.

Do not transfer metrics, bootstrap settings, multiplicity procedures or execution authorization between these protocols.

## Previous tester findings F1–F6

The current Greek runner contains remediation that needs a fresh independent review on this exact branch:

F1. End-to-end artifact preflight and separate fit path.
F2. Exact developer commit, pinned tester decision blobs and authorization-bundle SHA-256.
F3. Chronological decision/block order, no block-ID recurrence, target maturity and purge.
F4. OPTION rows are isolated for Greek calculations; SPOT rows supply spot-price features.
F5. Explicit date-only daily mapping to 15:30 IST cash close.
F6. Artifact IDs/digests, panel hashes, label-source pins, coverage counts, target maturity, holdout proof and aggregate-only receipt.

Source presence is not independent acceptance. This gate uses synthetic/static tests only and does not download, decrypt, fit or score real artifacts.

## Existing main-registry preflight remains blocked

`research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json` says `PASS_DATA_PREFLIGHT_WITH_SCOPED_BLOCKS`, but its preregistration Git blob SHA is null and it contains scoped sample-eligibility blocks. It is not a global fitting authorization; preserve it as history. The accompanying preflight attempt records no model fit and no holdout access.

## Finite next steps

1. Run synthetic regression tests, chronology tests and source/hash reconciliation on this exact branch.
2. Submit the exact green commit for independent code-only review of F1–F6 and protocol separation.
3. Only after tester PASS, run a schema/coverage-only Greek artifact preflight against pinned artifact IDs/digests. Report aggregate counts only; no fit or holdout.
4. Freeze and independently review the exact preflight report.
5. Empirical fitting is a later gate requiring the full ten-horizon protocol, data/label provenance and separate immutable authorization bundle. Do not run `--run-study` before that gate passes.

Authorization now: synthetic CI allowed; schema-only artifact preflight not yet authorized; empirical fitting, holdout access, options P&L and strategy promotion not authorized.

**Developer → Tester:** review F1–F6 and protocol separation on the exact green SHA; do not authorize artifact opening yet.
**Tester → Developer:** issue a hash-pinned code-only decision or precise fixes, then review schema-only preflight separately.
