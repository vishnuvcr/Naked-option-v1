# Phase 8 R2 active-spec clarification and option-runner proposal

**Status: DEVELOPER PROPOSAL — IMPLEMENTATION / REAL P&L NOT AUTHORIZED BY THIS FILE**  
Date: 2026-10-11  
Developer branch: `phase-08-developer`  
Proposal base commit: `05ce9ee8d2d673324fecba08416ac0310fde9345`

## Decision requested

Approve a versioned Phase 8 addendum that aligns the active method/data specifications with the accepted Run #994 saved forecast panels, corrects the omitted P10 abstention rule, and defines the next no-refit runner submission. Do not modify historical Phase 7/Run #654 artifacts, loosen any gate, or enable the empirical workflow.

## Current accepted forecast input

- Phase 7 run: `37957677656` (Run #994).
- Phase 7 source commit: `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- Forecast artifact ID: `11638738288`; artifact SHA-256: `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`.
- Embedded panel-manifest SHA-256: `f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091`.
- Paired aggregate SHA-256: `96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39`.
- Phase 8 reconstruction result artifact ID: `11709261335`; ZIP SHA-256: `249afea08ced49517a44744053afa382ce05165f53d0d23c5aac860a0c54214c`.
- Hosted run [38157819076](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38157819076) passed; all ten P01–P10 layer/horizon panels and 50,555 rows matched their paired aggregate at absolute tolerance `1e-9`.
- Tester report: [PHASE8_RUN994_SAVED_FORECAST_R2_TESTER_REPORT.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-08-tester/research/gates/PHASE8_RUN994_SAVED_FORECAST_R2_TESTER_REPORT.md).

Run #654 and its aggregate-only manifest must remain archived as historical R1. Run #994/R2 is the active input for Phase 8. Do not rerun/refit Phase 7 to generate Phase 8 predictions.

## Required specification alignment

After this proposal passes tester review, add a new versioned file `research/phase8/PHASE8_RUN994_R2_SPEC_ADDENDUM.md` and amend the active `PHASE8_METHOD_SPEC.md` / `PHASE8_DATA_PLAN.md` references so there is no conflict between their older Run #654 text and the active R2 manifest/workflow. Preserve the original lineage in the addendum rather than silently rewriting previous gate history.

The addendum must explicitly preserve:
- the frozen P01–P10 saved forecasts, labels, horizons, chronological blocks, source/commit hashes, and 1e-9 reconstruction tolerance;
- the untouched holdout boundary;
- the registered 4,800 configuration universe (100 forecast cells × 3 delta targets × 4 DTE buckets × 4 exit policies);
- the three delta targets, four DTE buckets, four exits, entry/exit timing and overlap policy;
- Paytm Money brokerage handling, dated statutory rates, four cost scenarios, Q1 synthetic spread and separately added slippage;
- fill/data-quality thresholds, required per-cell statuses, performance metrics, Phase 8→9 shortlist rule, and final Phase 9/10 promotion gates.

### P10 abstention correction

The exact Run #994 implementation defines `ABSTAIN` as:
- P05: [0.45, 0.55];
- P06: [0.40, 0.60];
- P10: [0.45, 0.55].

The current Phase 8 method text and `scripts/phase8_execution_engine.py::direction_from_probability` only encode P05 and P06. The R2 addendum and engine must add the frozen P10 abstention interval. P10 probabilities in [0.45, 0.55], including the boundaries, must produce no trade. This is a reconciliation to the accepted Phase 7 definition, not result-driven tuning.

## Existing cached composite — reuse only

- Derived dataset artifact ID: `11698879857`, source run `38131641336`, artifact name `nifty-1m-derived-repaired-r2-38126168547`.
- Expected merged gzip SHA-256: `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5`.
- Expected canonical decoded CSV SHA-256: `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`.
- Expected 8,999,865 data rows and 47 columns; 61 encrypted monthly parts. Reuse the existing artifact/cache and existing decryption/preflight scripts. Do not repeat source discovery or issue new market-data requests for this gate.
- Current documented limitations remain in scope: 19,021 unmatched OPTION rows across 421 timestamps; 24,847 weekend-session-review flags; 382 joined OPTION rows with invalid spot OHLC masked; 12 SPOT OHLC rows masked; 309 SPOT volume and 11 OPTION volume values masked; expiry/TTE/Greeks/risk-free-rate/dividend fields are not sourced in the raw composite. These must be handled and counted, not silently imputed.
- Existing Phase 8 source audit passed its limited official/secondary sample reconciliation, but it does not prove a full historical point-in-time bid/ask archive or complete contract master. No Q1 result may be called quote-executable. Derived expiry / Black–Scholes / moneyness fallbacks must be separately flagged and cannot overwrite sourced values.

## Runner submission scope

After the addendum proposal is accepted, implement `scripts/run_phase8_long_option.py` and focused synthetic tests. The runner must:
1. consume the accepted R2 forecast panels; never fit or refit a prediction model;
2. consume only the pinned existing composite artifact after verifying its exact identity and decoded hashes;
3. preserve the original source-row/request provenance and use point-in-time information only;
4. produce exactly 4,800 configuration records, each with a deterministic `EXECUTED`, `INELIGIBLE`, `DATA_QUALITY_FAIL`, or `NO_PREDICTION` status/reason; no winner may be silently dropped;
5. use the already-frozen `scripts/phase8_execution_engine.py` and `data/reference/phase8_cost_schedule.json`, after the P10 abstention fix;
6. record the four C0–C3 scenarios separately and report gross/net P&L, every charge, fill/no-fill/gap rates, win/loss distributions, drawdown, chronological blocks, tail loss, block stability, break-even and data-quality gates;
7. handle repeated observations of one inferred contract/timestamp deterministically. Conflicting prices must fail the affected keys closed and be reported; identical duplicate rows must retain source/request provenance;
8. keep Q1 OHLC/proxy results explicitly **non-quote-executable**, and fail strict data-quality promotion when contract listing/expiry/lot-size provenance cannot meet the frozen thresholds;
9. include a synthetic `--self-test` path that cannot read market data or produce empirical P&L;
10. leave `empirical_option_execution_authorized=false` and workflow default false. Do not run the 4,800-cell real-data grid until the exact code, cost arithmetic, contract identity, point-in-time controls and the data-gate result receive separate tester approval and the required explicit authorization.

The runner implementation is submitted to the tester as a separate code-review gate after synthetic CI; this proposal does not pre-approve its code.

## Acceptance and next gate

- First: tester reviews this specification/input proposal.
- Second: developer writes the versioned R2 addendum and P10 correction, updates regression tests and documentation, then submits the exact diff for tester code review.
- Third: developer implements the runner and synthetic tests; tester reviews the exact hashes and hosted dry-run before any empirical execution request.
- Fourth: the cached real-data preflight decides which rows/cells are strictly eligible and which are proxy-only or blocked. Preserve both successful and failed results.
- No strategy promotion from Phase 8. Only candidates meeting the frozen shortlist rule may advance to Phase 9, then Phase 10.

**Developer → Tester:** Review only the R2 source identity, P10 abstention correction, preserved frozen universe/cost rules and the proposed safe runner scope. Do not authorize real P&L from proposal review alone.  
**Tester → Developer:** Return PASS/REQUEST CHANGES on this exact proposal; require exact-hash code review and hosted tests for the later implementation, with empirical authorization false by default.
