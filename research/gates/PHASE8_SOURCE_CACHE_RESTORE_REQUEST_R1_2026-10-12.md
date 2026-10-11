# Phase 8 Request R1 — Restore frozen Run #994 spot-reference inputs (2026-10-12)

## Requested independent tester decision

**Current state: REQUESTED — NO RESTORATION AUTHORIZED YET.**

Approve or reject one strictly scoped restore attempt for the two source files pinned by the immutable Phase 7 Run #994 manifest. This request is not the consumed naked-option composite preflight request and must not alter or reuse that authorization.

## Why this request is necessary

The H=1 source-alignment code now enforces a two-ULP ceiling only for source-derived float64 `future_return`, and hosted reconstruction artifacts on older snapshots measured all observed differences within that limit. The tester correctly kept the gate open because the final snapshot lacked the exact source bytes needed to make its own full-reconstruction evidence reproducible.

Repository recovery checks:

- Phase 3 historical workflow artifact [run #37578427116 / artifact #11464120657](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37578427116) contains result/manifest summaries, not the raw daily CSV or intraday Parquet.
- Read-only cache export attempt [run #38165705217](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38165705217) refused to export a Parquet that did not match the frozen SHA. The cached daily CSV did match; the cached intraday candidate did not.
- The available Phase 3 cache's intraday bytes were SHA-256 `5f5c91b1c29db13ccaa6ffbb3a83a526a82bedf30092e9b9585384efcec5f6d2`, while the immutable Run #994 manifest requires `6f6014d58cf0aa03920832b97730bc2f4287532b3c830700351d6828adfebc17`. The mismatching cache content was rejected and will not be used as a validation input.
- The frozen reference archive, embedded manifest, and aggregate SHA pins remain unchanged.

## Frozen inputs, and only these inputs

| Name | Required repository path | Required SHA-256 | Role |
|---|---|---|---|
| Daily NIFTY history | `data/cache/raw/phase3/nifty50_daily.csv` | `5816b0e73f4bd1327e567249f366fbebb01a549bd539fd4743424fbefe70f5c1` | Spot-index reference used to validate saved daily prediction panels |
| HF intraday NIFTY reference | `data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet` | `6f6014d58cf0aa03920832b97730bc2f4287532b3c830700351d6828adfebc17` | Spot-index intraday reference used to validate saved intraday prediction panels |

Frozen Run #994 pins: source run `37957677656`, reference artifact `11638738288`, archive SHA-256 `3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9`, embedded-manifest SHA-256 `f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091`.

## Exact operations requested

1. Download the immutable Run #994 reference artifact from GitHub and verify its embedded manifest hash before reading source-file pins.
2. Reuse the existing Phase 3 cache as candidate data. Preserve files that already match the frozen source SHA; based on the inspected cache, the daily CSV is already a match.
3. If the frozen artifact-specific cache contains both expected files, verify and stop without requesting market data.
4. If a file is missing or mismatched, require the independent tester decision to match the exact current code blob hashes and both frozen SHA pins before executing anything that contacts source providers.
5. Record the R1 attempt artifact before any source request. If any prior R1 attempt marker exists, block the run and require a new versioned request/decision.
6. Recreate only the missing/mismatched pinned spot-reference file(s) using the existing acquisition scripts. This can request Yahoo daily NIFTY history or the public HF NIFTY index reference, including the existing official-NSE overlap checks in the intraday script; do not request option chains, option trades/quotes, new contract data, or unrelated symbols.
7. Verify both final files against the exact SHA-256 values above. If either differs, fail closed, upload diagnostic logs only, and do not save or use the candidates as frozen inputs.
8. Save only exact-hash-verified files under the Run #994-specific cache key and publish the hash/provenance report. Subsequent workflow runs should reuse this exact cache and perform no new data request.
9. Rerun saved Run #994 source-alignment validation on the exact developer snapshot. Require per-panel ULP diagnostics; every `future_return` mismatch must be <=2 ULP, label and timestamp checks exact, no model refit, and no artifact/tolerance mutation.

## Explicit scope exclusions

This request does **not** authorize the Phase 8 option-source audit, the 4,800-cell option P&L, contract-master acquisition, historical bid/ask acquisition, holdout access, strategy selection/promotion, or any claim of a profitable naked-option buying strategy. Paytm Money transaction-cost/slippage modelling stays a later gate, after option-contract/execution data eligibility is established. The already-consumed composite preflight R1 remains disabled and is not reusable.

## Workflow incident disclosure

The cache-export workflow commit unexpectedly triggered Phase 3 because its existing push filter was broad. Run [#38165705151](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38165705151) began and reached the daily and HF acquisition steps before the filter correction. This was a workflow-control mistake. Its refreshed Phase 3 outputs are expressly excluded from the frozen Run #994 validation unless their exact hashes match the frozen manifest; the export workflow itself independently rejected the wrong intraday cache. The push filter was narrowed in [commit f27d36f](https://github.com/vishnuvcr/Naked-option-v1/commit/f27d36f07badb4f98831d0bf199826b27454f6da). The restore workflow has a separate R1 approval check and an attempt marker.

**Developer → Tester:** inspect the exact code hashes and request scope; approve only a single hash-pinned restoration if the tester agrees that no acceptable archived copy exists. No source request may run before your exact-snapshot decision.

**Tester → Developer:** reject any mismatching restored file, any scope expansion, or any replay of the consumed naked-option preflight. Keep H1 and all empirical/P&L gates blocked until exact-snapshot evidence is accepted.
