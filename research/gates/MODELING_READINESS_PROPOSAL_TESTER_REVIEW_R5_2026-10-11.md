# Tester Review — Modeling-Readiness Proposal R5

Date: 2026-10-11 UTC  
Gate: MODELING_READINESS_DESIGN  
Developer proposal SHA: f3b04eec5097dffedd0a1418de1a8673a7756bd9  
Developer scope JSON SHA: 741cd5870107a52e8f20dc83b6ba83761ac71a2e  
Contract references reviewed: PPR target contract blob 049f5d3529ff5e82b3798fdb8e27bad10c413d80; paper-replication extension blob 7ecff1be9aa2d6c2c8d5abbf89457113e382b1e3.

## Decision

**PASS WITH SCOPED RESTRICTIONS — proposal/design only.**

The design is suitable to proceed to a deterministic metadata-only implementation and synthetic offline tests on phase-07-developer. This verdict does **not** authorize running that implementation against the real dataset. The exact implementation, synthetic results, artifact-handling logic and cleanup behavior must receive a fresh exact-hash tester review before a one-use real-file readiness audit can be requested.

No model fitting/tuning/scoring, holdout observation access, new source requests, options P&L, strategy testing, or trading is authorized. This design review cannot override PPR-2, PPR-3, PPR-4, PPR-6, or the current PROPOSED_NOT_AUTHORIZED target contract.

## Independent checklist

The tester re-fetched the exact two developer blobs and checked the proposal against the currently pinned target contract and paper-replication spec.

| Check | Finding |
|---|---|
| Finite phase plan | PASS: MR-0 through MR-5; terminal states required, no endless retry loop |
| Source/data boundary | PASS: existing cache/manifest inventory only; no source request authorized |
| Target provenance | PASS: do not equate final minute-bar close with official daily close without timestamp semantics and authorized provenance |
| Target definitions | PASS WITH RESTRICTIONS: daily horizons are session-indexed 1/2/3/5/10; three-class order is DOWN/FLAT/UP and tolerance remains fixed at 1e-8; next-session open remains a separate task |
| Row identity | PASS: use standalone SPOT for index targets; do not reuse rejected R4 duplicate count |
| Missing values | PASS: no fabricated target/price values or zero-filling; missing families get reason-coded blocked/not-estimable dispositions |
| Option rows | PASS: unmatched options are ineligible for features requiring underlying joins; no nearest-time matching |
| Session handling | PASS WITH RESTRICTIONS: weekday-only logic is explicitly rejected; weekend/special sessions require evidence from an authorized calendar cache |
| Point-in-time features | PASS: publication/ingestion/capture-time requirements are explicit; unknown-vintage external features are blocked/not estimable |
| Leakage and purge | PASS: label endpoints, chronological split, horizon-specific purge, train-only preprocessing and fixed minimum sample thresholds are defined |
| Holdout safety | PASS: existing holdout exclusion must be proven from metadata only; absent proof produces BLOCKED_HOLDOUT_PROOF |
| Scope/permissions | PASS: all empirical permissions are false and no model run is allowed by the proposal |
| Current upstream status | PASS: the proposal explicitly preserves PPR-2 not started and PPR-3/PPR empirical work unauthorized |

## Required implementation cautions

1. MR-0 to MR-5 reports must contain metadata/counts/hashes only; never emit row-level prices, contract details, credentials or plaintext CSV.
2. Any candle timestamp ambiguity must fail closed. A locally constructed final-bar target must be labelled as a distinct adapted estimand; it cannot be called an official-close replication without evidence and protocol approval.
3. A weekend flag must be reconciled by unique timestamp/session and official-calendar provenance, not treated as an independent count of unique sessions.
4. Missing 19,021 option joins, 24,847 weekend-review flags, masked OHLCV values and all-blank expiry/TTE/Greek/rate/dividend fields are mandatory coverage diagnostics, not automatic dataset-wide failure and not harmless omissions.
5. Do not instantiate or inspect final holdout observations to derive the exclusion boundary. If the existing exclusion metadata is missing or ambiguous, fail with BLOCKED_HOLDOUT_PROOF.
6. The implementation must not silently drop planned feature families after inspecting any predictive outcome. Eligibility/exclusions and common origins are determined before fitting; in this readiness gate there is no fitting.
7. Add synthetic tests for all cases listed in proposal section 11 and verify cleanup on success and failure. Real-file execution requires a new tester decision that pins exact implementation/workflow/test blobs and the specific one-use request.

## Scope granted

Allowed next action: **developer implementation of the deterministic feasibility scanner, sanitized report schema, and synthetic regression tests only**, using the frozen dataset identity in the scope JSON and without live data execution or external source calls. It must remain non-mutating and may not modify the R5-reviewed runtime files.

Not yet allowed: workflow run against the real encrypted dataset; source-data acquisition; model training/tuning/scoring; final holdout access; strategy/P&L testing or any trading operation.

## Reviewer independence note

This is a tester-role review using exact blob retrieval and explicit schema/protocol checks in the same connected assistant session. It is not a separate human or external AI audit, and repository text must not imply otherwise.

**Tester → Developer:** Implement only the permitted offline feasibility checks and synthetic tests, record all results/errors, then submit exact file hashes for implementation review.

**Developer → Tester:** Do not trigger a real-file run or fit any model until a fresh exact-snapshot implementation decision authorizes a narrowly scoped feasibility audit.
