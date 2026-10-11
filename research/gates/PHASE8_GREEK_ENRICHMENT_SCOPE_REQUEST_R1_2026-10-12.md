# Phase 8 — Greek-enrichment scope request R1 (2026-10-12)

## Objective
Produce an encrypted, row-preserving R1 derivative of the currently cached 1-minute NIFTY rolling-options composite. Reuse the existing composite and HF_TOKEN-derived encryption key; retrieve only public Hugging Face NIFTY spot-minute bars and file-list metadata for published NIFTY expiry partitions. Use them to recover missing exact-timestamp spot OHLC values and map Dhan rolling expiry codes to a sourced expiry-calendar proxy. Estimate implied volatility from option close where Black–Scholes inversion is valid, then calculate Delta, Gamma, Theta/day, Vega/1%-IV and Rho/1%-rate.

## Required independent tester decision
This request creates no live-source permission by itself. Before any provider request or decryption/enrichment run, the tester must review and approve the exact developer snapshot, including the enrichment code, synthetic tests, workflow, Greek method and this request. The hosted job must check the tester's machine-readable decision against the exact developer commit and exact code blob SHA pins.

## Sources and scope
- Existing encrypted composite: GitHub Actions run 38131641336, artifact 11698879857, expected archive SHA-256 40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b.
- Public Hugging Face dataset: thetrademarkk/india-index-options-1m; use only index/NIFTY.parquet and options/NIFTY/YYYY-MM-DD.parquet file names for timestamp-aligned spot values and the expiry calendar. Attribution: https://huggingface.co/datasets/thetrademarkk/india-index-options-1m.
- Dhan credentials are not assumed to exist. Do not make new Dhan API requests in this gate.
- Source license is CC-BY-NC-4.0, so derived research output is restricted to non-commercial use. Preserve attribution in the output manifest.

## Method
1. Verify the immutable source artifact archive hash and all source-part hashes before decryption.
2. Fill only missing/invalid NIFTY spot fields using an exact epoch-second match against the HF index parquet. Never forward-fill, interpolate or overwrite valid source values.
3. Map expiry_flag + expiry_code (0=current, 1=next, 2=far) using dates in the HF NIFTY expiry partition list. Dates beyond the source list may use the documented Tuesday-expiry rule but must be separately flagged as rule-derived, not contract-master verified. Unknown flags/codes or exhausted calendars remain unmapped.
4. Compute time to expiry from source timestamp to 15:30 IST on expiry date. Use r=0 and q=0 only as explicitly labelled proxies because historical point-in-time rates/dividend yields are not supplied by the cache.
5. Invert Black–Scholes from option close, spot, strike, expiry and CE/PE type when the premium is positive, in theoretical bounds and IV is solvable. Only when inversion is unavailable may a present provider IV be used with the source's documented >3 => percent points; otherwise fractional heuristic, flagged per row.
6. Calculate European Black–Scholes Greeks with units: Delta per one spot point; Gamma per one-point spot move; Theta per calendar day; Vega per 1 volatility percentage point; Rho per 1 percentage point annual rate move. Greek values are model estimates, not observed historical vendor Greeks.
7. Preserve every input row. Unresolved spot/expiry/IV/type/session cases keep Greeks null with a clear status. Report coverage and source/assumption counts. Encrypt every output monthly gzip part with AES-256-GCM and the same HF_TOKEN-derived key; never upload plaintext.
8. No strategy P&L, holdout access, strategy promotion or new Dhan market-data requests are included.

## Fail-closed criteria
Stop without accepting output if the source artifact/part hashes, encryption authentication, schema consistency, exact timestamp join, row counts or output encryption checks fail. Tester approval grants only the public HF metadata/spot retrieval and Greek-enrichment scope above.

**Developer → Tester:** Independently audit expiry mapping, timestamp/time-to-expiry, Black–Scholes equations/signs/units, IV bounds/fallbacks, exact joins, row preservation, encryption and source/license scope for the exact commit.

**Tester → Developer:** approve only if the exact-snapshot synthetic gate passes and the report clearly distinguishes estimated Greeks and rule-derived expiries from historical exchange/vendor observations.