## Phase 8 Run #994 / R2 active forecast-input addendum

**Status: ACCEPTED FOR FORECAST REPRODUCIBILITY ONLY. REAL OPTION P&L REMAINS GATED.**

## Active forecast artifact identity

| Field | Frozen value |
|---|---|
| Phase 7 source run | 37957677656 (Run #994) |
| Phase 7 source commit | b50be8cfa1ebe008a800e65a53f9c0fb2581aecb |
| Reference artifact ID | 11638738288 |
| Archive SHA-256 | 3e8a22ded608668b5674f7aed609fefa5c4befcde39ca58b7f208e59ab25959a9 |
| Embedded manifest SHA-256 | f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091 |
| Paired aggregate SHA-256 | 96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39 |
| Phase 8 validation run | 38157819076 |
| Validation artifact ID | 11709261335 |
| Validation artifact SHA-256 | 249afea08ced49517a44744053afa382ce05165f53d0d23c5aac860a0c54214c |
| Result | 10/10 cells PASS; 50,555 rows; all_cells_reproduced=true |
| Absolute metric tolerance | 1e-9 |

The active R2 input uses saved forecast panels as-is. No Phase 7 refitting or regenerated prediction array is permitted for Phase 8. The historical Run #654 aggregate-only artifact remains preserved as R1 lineage in PHASE8_FROZEN_INPUT_MANIFEST_R1_RUN654.json; it is not the current forecast input.

## Corrected frozen P10 trade-mapping rule

Run #994's exact source declares P05 [0.45, 0.55], P06 [0.40, 0.60] and P10 [0.45, 0.55] as abstention bands. A probability on either boundary is an abstention. The Phase 8 engine and regression tests implement this mapping. This corrects the older Phase 8 code/spec omission; it does not change saved forecast probabilities or tune rules based on option P&L.

## Cached composite identity and current limits

The existing repaired NIFTY 1-minute composite is reused as-is:
- source/repair run: 38131641336;
- derived artifact ID: 11698879857;
- artifact name: nifty-1m-derived-repaired-r2-38126168547;
- merged gzip SHA-256: f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5;
- canonical decoded CSV SHA-256: cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204;
- 8,999,865 rows, 47 columns, 61 encrypted monthly parts.

Known limitations remain binding: 19,021 unmatched OPTION rows across 421 timestamps; 24,847 weekend-session-review flags; invalid/missing spot OHLC and volume values are masked and must remain counted; expiry/TTE/Greek/risk-free-rate/dividend fields are not source-populated in the raw composite. Reuse the pinned artifact; do not run new market-data source requests as part of the R2 clarification. Any derived expiry or Greek/moneyness fallback must retain its method/provenance label and cannot be represented as an observed historical field.

The Phase 8 source workflow's free-source sample audit is a limited schema/overlap check, not proof of complete historical bid/ask quotes or a full contract master. OHLC/Q1 proxy outputs remain non-quote-executable.

## Scientific universe and promotion rules — unchanged

This addendum does not alter P01–P10, labels, horizons, chronological blocks, protected holdout, the 4,800 configuration grid, C0–C3 cost scenarios, Paytm Money brokerage fallback, dated statutory rates, Q1 spreads, incremental slippage, data-quality thresholds, output metrics, Phase 8→9 shortlist rule or Phase 9/10 promotion gates.

The next implementation must pass exact code review, synthetic tests and cached-composite data-quality preflight before a separate empirical authorization. This addendum does not authorize real option P&L, holdout access or strategy promotion.

**Developer → Tester:** review the exact addendum/engine/test commit, especially P10 boundary arithmetic, cost rules and preservation of data limitations.
**Tester → Developer:** approve or request changes on the exact code/hash snapshot; keep empirical authorization disabled pending runner review and data-gate evidence.


## Effective-dated lot-size rules discovered during implementation

The official circulars confirm that lot size is cycle/expiry-specific, not a single date-only constant. For NIFTY weekly contracts, the last weekly expiry on the old lot was 19-Dec-2024 and the first revised-size weekly expiry was 02-Jan-2025; for monthlies the corresponding dates were 30-Jan-2025 and 27-Feb-2025 (NSE/FAOP/64672, https://nsearchives.nseindia.com/content/circulars/FAOP64672.pdf). The effective introduction date was shifted to 21-Nov-2024 due to the 20-Nov exchange holiday (NSE/FAOP/64990, https://nsearchives.nseindia.com/content/circulars/FAOP64990.pdf). NIFTY's 75-to-65 revision uses the last old weekly expiry 23-Dec-2025 and first revised weekly expiry 06-Jan-2026; monthly values are 30-Dec-2025 and 27-Jan-2026 respectively (NSE/FAOP/70616, https://nsearchives.nseindia.com/content/circulars/FAOP70616.pdf). See data/reference/nifty_lot_size_history.json. Unlisted/transition expiry dates remain unknown; the circular schedule is not a contract-master substitute.

Statutory transaction rates may change between entry and exit. The cost engine now applies the appropriate dated exchange/IPFT rate to each side's premium turnover and uses exit-date STT for the exit side. Brokerage fallback remains ₹20 per executed order unless the effective tariff is independently verified.
