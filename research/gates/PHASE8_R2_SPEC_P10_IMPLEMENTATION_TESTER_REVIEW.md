# Tester Review — Phase 8 R2 specification and P10 implementation

**Decision: PASS WITH SCOPED RESTRICTIONS — spec/source consistency and execution-engine regression only**
Date: 2026-10-11
Exact developer commit: e8f8f5df8d70db401c8a604405c9fe6f611a2c04
Hosted workflow run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38158813453

## Evidence reviewed

1. The hosted run completed successfully on the exact reviewed developer commit. Protocol, specification contract, Phase 8 regression, free-source option sample audit, immutable Run #994 artifact integrity and saved-panel reconstruction all passed. The empirical authorization and 4,800-cell empirical jobs were skipped.
2. The active R2 manifest still pins Run #994 source commit b50be8cfa1ebe008a800e65a53f9c0fb2581aecb, reference artifact 11638738288 and the previously accepted artifact/manifest/aggregate hashes. The historical Run #654 manifest remains as R1 lineage.
3. The active method/data specification now documents Run #994 saved panel consumption without refitting. The versioned addendum records the accepted 10-panel, 50,555-row validation with tolerance 1e-9 and explicitly keeps option P&L blocked.
4. The execution-engine direction rule now handles P10’s exact Run #994 abstention interval [0.45, 0.55] like P05; the regression checks values outside, inside, and at both boundaries. P06 remains [0.40, 0.60].
5. The existing transaction cost schedule, 4,800-cell configuration universe, entry/exit rules, costs, holdout and promotion criteria were not intentionally changed by this patch.

## Restrictions and remaining blockers

- This decision does not approve or test a Phase 8 runner; scripts/run_phase8_long_option.py is still absent as of this reviewed snapshot.
- No real option P&L, 4,800-cell grid, holdout access or strategy promotion is authorized.
- The cached composite is available and must be reused. Its exact identity is source run 38131641336 / artifact 11698879857; gzip SHA-256 f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5; canonical CSV SHA-256 cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204; 8,999,865 rows / 47 columns / 61 encrypted monthly parts.
- Material quality gaps remain: 19,021 unmatched OPTION rows across 421 timestamps, weekend-session-review flags, masked spot/volume anomalies, and raw expiry/TTE/Greek/rate/dividend fields that are not source-populated. Do not silently impute or claim a full observed contract master.
- The official/secondary sample audit is not complete historical bid/ask evidence. Q1/OHLC fills remain non-quote-executable.
- Historical NIFTY lot size is not one constant: it changed from 25 to 75 for new contracts in November 2024, and official NSE circular FAOP/70616 in October 2025 revised new-contract lot size to 65 with contract-specific transition arrangements. A dated contract master / effective-dated official schedule must decide eligibility; do not assign lot size from a simplistic date-only rule.
- The earlier daily H=1 source-alignment mismatch did not reproduce on accepted Run #994 validation. Preserve the anomaly in logs rather than declaring its root cause known.
- Tester is a role-separated branch review in this connected session, not an external independent human/model.

## Authorized next step

Developer may implement scripts/run_phase8_long_option.py and synthetic-only tests. The runner must consume saved R2 panels without model fitting, verify the exact pinned existing composite artifact and hashes, enumerate all 4,800 configurations without dropping failures, report all statuses and four costs, keep empirical authorization false, and provide a self-test path that cannot read real data or generate empirical P&L. Submit exact code hashes and hosted tests for a separate tester code review before any real P&L.

**Tester → Developer:** archive this decision, implement and test the no-refit runner against only the pinned inputs; keep empirical authorization false.
**Developer → Tester:** review the exact runner commit for 4,800-cell completeness, P10/P05/P06 abstention boundaries, contract/lot/expiry causality, charge arithmetic, duplicated-row handling and the data-quality guard before any empirical request.
