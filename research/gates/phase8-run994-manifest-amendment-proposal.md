# Phase 8 saved-panel reference amendment — Run #994

Date: 2026-10-11
Status: DEVELOPER PROPOSAL — NO OPTION P&L AUTHORIZED
Developer branch: `phase-08-developer`

## Decision requested

Amend the active Phase 8 input to use the newer immutable Phase 7 Run #994 artifact containing all ten row-level forecast panels and its paired aggregate output. Preserve Run #654 and the old manifest unchanged as historical lineage. Change the Phase 8 consumer to validate and consume these saved panels without refitting the Phase 7 predictors.

## Exact source identity

- Phase 7 workflow run ID: `37957677656` (run number 994).
- Developer source commit: `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- GitHub Actions artifact ID: `11638738288`; name: `phase7-ensemble-reference`.
- Downloaded archive SHA-256: `3e8a22ded608668b5674f7aed609fefa5c4befcde39ca58b7f208e59ab25959a9`.
- Embedded manifest SHA-256: `f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091`.
- Paired aggregate JSON SHA-256: `96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39`.
- Phase 7 tester report: [PHASE7_RUN_37957677656_EMPIRICAL_TESTER.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_RUN_37957677656_EMPIRICAL_TESTER.md).
- Phase 7 independent audit: 3,098 checks passed, zero failed, exact run/commit identity verified; scientific promotion was not granted by that technical audit.

The archive contains exactly ten panel files: daily horizons 1, 2, 3, 5, 10 (1,670 rows each) and intraday horizons 5, 15, 30, 60, 120 (8,441 rows each), totalling 50,555 forecast rows. Every listed Parquet digest was recomputed against the downloaded archive and matched the embedded manifest. The aggregate JSON digest also matches.

## Implementation changes proposed

1. Add an immutable versioned R2 manifest linked to all identifiers above and set the active manifest to R2. Archive the prior Run #654 manifest as R1; do not overwrite or mutate Run #654 itself.
2. Update the Phase 8 workflow to download/cache artifact `11638738288`, verify the archive SHA-256 and its Run #994 ID/commit/artifact identity, then unpack it to an R2-specific cache path.
3. Replace production forecast reconstruction/refitting with `scripts/validate_phase7_reference_panels.py --artifact-dir ...`. That validator checks panel schema/digests/rows, exact source-code commit hashes, source-file hashes, timestamps, labels and future returns, and recomputes all registered metrics and family tests from saved forecasts at the existing absolute tolerance `1e-9`.
4. Continue running `scripts/validate_phase8_forecast_panel.py` on the copied saved panels. Fail closed if any file, hash, source, metric or identity check differs. There is no fallback to refitting.
5. Keep `empirical_option_execution_authorized=false`, keep the workflow dispatch default false, and do not create/enable the 4,800-cell empirical execution authorization file in this amendment.
6. Preserve Phase 8 option-source/data checks. This change addresses only forecast artifact lineage and must not be misrepresented as proving a complete historical option panel or profitable strategy.

## Non-goals and safeguards

- No scientific definition, label, probability, abstention interval, horizon, block schedule, family inference, seed, or tolerance changes.
- No result-driven selection, final holdout access, option P&L, strategy promotion, or paid data purchase.
- No replacement or deletion of historical Run #654 or its prior failure evidence.
- The Phase 7 panel audit is a technical integrity gate, not evidence of predictive efficacy or economic edge.

## Developer → Tester

Review the exact R2 artifact/manifest/workflow diff, check all constants and hash lineage, confirm no re-fit fallback or authorization flag is enabled, and require a hosted regression/integration run before any Phase 8 empirical option grid.

## Tester → Developer

Do not run the empirical option grid or claim a trading strategy until this exact snapshot is reviewed, hosted panel validation passes, the point-in-time option-history/data-quality gate passes, and a separate empirical authorization is approved.
