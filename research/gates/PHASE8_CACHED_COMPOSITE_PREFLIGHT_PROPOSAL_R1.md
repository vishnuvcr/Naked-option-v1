# Phase 8 cached-composite preflight — R1

Date: 2026-10-11
Branch: `phase-08-developer`
Status: PROPOSAL ONLY — CACHED-DATA PREFLIGHT; NO P&L

## Decision requested

Authorize one hosted, read-only preflight of the existing repaired NIFTY composite and the accepted Run #994 saved forecasts. This is the next step after successful forecast reproducibility and regression gates. It must not make new market-data requests, fit prediction models, access the holdout, create option P&L, or promote any strategy.

## Exact immutable inputs

### Saved forecast panels

- Source run: `37957677656`, run #994.
- Source commit: `b50be8cfa1ebe008a800e65a53f9c0fb2581aecb`.
- Artifact ID: `11638738288`, name `phase7-ensemble-reference`.
- ZIP SHA-256: `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`.
- Embedded manifest SHA-256: `f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091`.
- Aggregate SHA-256: `96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39`.
- Accepted Phase 8 reproducibility run: [38157819076](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38157819076); 10/10 forecast cells, 50,555 rows, tolerance (10^{-9}).

### Existing repaired composite

- Source run: `38131641336`, source commit: `5e769cd4b19887311213baf16eb81b97416322d7`.
- Artifact ID: `11698879857`, name `nifty-1m-derived-repaired-r2-38126168547`.
- Exact canonical decoded CSV SHA-256: `cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204`.
- Recorded merged gzip SHA-256: `f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5` (record/provenance only; gzip metadata can vary on re-merge).
- Expected data rows: `8,999,865`; columns: `47`; types: `8,490,723 OPTION` and `509,142 SPOT`; 61 encrypted monthly parts.
- Existing reviewed repository manifest: `research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json`.

## Implementation contract

Add a dedicated developer-branch workflow with both push/path triggers and `workflow_dispatch`. The workflow will:

1. Run protocol, runner unit tests, the pure runner self-test, accepted forecast-artifact checks, and current free-source sample gate before the preflight.
2. Verify the source workflow run identity/status and exact artifact ID/name. Download only artifact `11698879857` from run `38131641336`.
3. Validate the encrypted-only marker, exact 61 manifest part records, safe filenames, declared byte sizes, SHA-256 of every encrypted part, and total expected row count before decryption.
4. Decrypt/merge using the existing pinned `scripts/decrypt_nifty_1m_composite.py` and the repository `HF_TOKEN` secret. The secret is never printed or written. Plaintext exists only under `$RUNNER_TEMP`.
5. Verify the exact canonical decoded CSV SHA-256, expected row/column/type counts, and the saved R2 forecast panel hashes. Run `scripts/run_phase8_long_option.py --mode preflight --composite-csv-gz ...`.
6. Verify the resulting JSON explicitly says: forecast preflight PASS; composite structural/hash preflight PASS; all 4,800 configurations retained; `strict_fixed_contract_execution_ready=false`; `empirical_option_execution_authorized=false`; `empirical_pnl_generated=false`; `strategy_promotion_authorized=false`.
7. Upload only JSON/CSV metadata reports as a short-retention artifact. Never upload plaintext, raw option rows, decrypted monthly parts, or the merged CSV.
8. In an unconditional cleanup step, delete downloaded encrypted shards, decrypted monthly files, merged plaintext/gzip and working directories; verify paths are absent. Fail closed if cleanup fails.
9. Record failures with exact gate/code, counts and hashes only—no market rows or secrets.

## Expected scientific disposition

The preflight is a **data-readiness result only**. Based on the pinned 47-column schema, it is expected to flag missing explicit `lot_size`/`tick_size` columns and absence of complete point-in-time contract-master/bid-ask coverage. The output may therefore mark all 4,800 cells `INELIGIBLE`. This must not be relabeled as a negative or positive trading result. It does not prevent a separately gated exploratory OHLC/proxy analysis proposal later, but that track must be labelled non-quote-executable and cannot silently substitute for strict eligibility.

Known quality limits remain in force: 19,021 unmatched option rows across 421 timestamps; 24,847 weekend-review flags; masked invalid/missing OHLC/volume rows; derived expiry/Greeks/rates/dividend assumptions; and a limited date/source overlap sample rather than complete historical quote coverage.

## Safety restrictions

- No new public/private market-data discovery or provider API calls.
- No model fitting/refitting or saved prediction regeneration.
- No holdout access.
- No empirical option trades, order simulation that emits P&L, parameter selection, or strategy promotion.
- Do not alter the 4,800-cell universe, the 4 cost scenarios, the costs, labels, forecast horizons, execution rule, or the (10^{-9}) forecast-reproducibility tolerance.
- This is one exact artifact preflight; no looping retries or indefinite dataset rebuilding.
- The workflow must have a manual run button and must trigger automatically for relevant developer-branch edits.

## Developer → Tester

Review the exact pinned identities and hashes, all 61-part verification, secret handling, temporary plaintext lifecycle, runner call, expected status invariants, upload paths, cleanup behavior, and proof that no P&L/holdout/new network-source request can run.

## Tester → Developer

Return an exact-snapshot decision. If approved, authorize only implementation plus synthetic tests and one metadata-only cached-composite preflight. Keep all empirical/strategy authorization false until a later separate gate.
