# Tester Review — Prospective Holdout Boundary Implementation R1

**Date:** 2026-10-11  
**Verdict:** PASS_WITH_SCOPED_RESTRICTIONS — synthetic-only implementation  
**Reviewed developer commit:** `8a69c5004bfa6f45efb69adb596ea1db122398f1`

## Exact reviewed blobs

- Scanner: `364ae6e5a95e1d62bc1ae0640f29d954337c8237`
- Tests: `32430369f67ac6fd7a3409139fe087bf964f066e`
- Manifest schema: `79519f214042bc13a569974b9e173b57b6580bab`
- Workflow: `c27cc77e910d7e3bd3b13ec9f4c1a179664481bc`

## Verification

- Hosted synthetic workflow [run 38153402133](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38153402133) passed all 5 tests and the CLI guard.
- The CLI exposes only `--self-test`; it has no dataset-path or manifest-path arguments.
- The scanner uses only row type, timestamp, session date, offsets, and row counts in its application logic. It streams the whole-file digest and hashes the final byte range without decoding that suffix a second time.
- It validates row widths, timestamp/session ordering, computes deterministic 70/15/15 session boundaries, records byte offsets, and computes per-horizon metadata-only purge counts. The synthetic report contains no sentinel price, quote, feature, or label values.
- The 20-session fixture correctly reports `NOT_ESTIMABLE` against the preregistered 252/250 thresholds; it does not relax thresholds to make the fixture pass.

## Restrictions

1. This pass authorizes **synthetic tests only**. The scanner function can be invoked programmatically, but no workflow or CLI is permitted to point it at the repository composite. Any real-file execution requires a separate exact-hash execution decision.
2. The output's origin counts are metadata-only session-index counts. They do not prove target-label availability, official-close linkage, model readiness, or predictive accuracy.
3. The session dates come from the composite's metadata. A later data-readiness gate must compare them with the pinned official NSE calendar and verify source/close-linkage provenance.
4. The 70/15/15 boundary is prospective only after a separate authorization to scan the cached file. Do not generate a manifest by calling the function on the actual composite under this decision.

## Decision

**Allowed:** maintain code and run synthetic-only CI; submit future changes for exact-hash review.

**Not allowed:** scanning the cached composite, opening market/holdout values, model fitting/scoring, new source requests, strategy/P&L, or trading.

**Tester → Developer:** Synthetic implementation passes. Update status/README, and request a separate exact-hash execution decision before any real-file scan.  
**Developer → Tester:** Keep the empirical gate closed until that separate decision and required provenance are available.
