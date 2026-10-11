# Phase 8 — Greek-enrichment scope request R2 (2026-10-12)

## Purpose
R2 supersedes R1 for implementation execution. It retains the same narrowly scoped HF public source access and adds a regression-backed fix for Pandas 3 timestamp-resolution compatibility in exact-epoch spot matching. It does not add Dhan calls or widen historical option contract coverage.

## Exact source and requested data
- Reuse the cached encrypted source artifact from Actions run 38131641336, artifact 11698879857, ZIP SHA-256 40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b.
- Fetch only the public Hugging Face dataset thetrademarkk/india-index-options-1m file index/NIFTY.parquet and the file listing under options/NIFTY/YYYY-MM-DD.parquet. Preserve the resolved HF commit SHA, attribution and CC-BY-NC-4.0 non-commercial-use restriction.
- Convert timezone-aware source timestamps to Unix epoch seconds by using the timestamp object's explicit .timestamp() method, not integer datetime representations whose integer unit varies under Pandas 3. Exact-match spot fields only; never forward-fill or interpolate.
- Use HF expiry-partition dates as the expiry-calendar proxy for dates present in that file list. For later expiry dates, use the separately labelled Tuesday-rule proxy; this is not an official contract-master snapshot.
- Invert Black–Scholes implied volatility from option close when valid, otherwise use the existing documented provider-IV unit heuristic and label the fallback. Use r=0 and q=0 explicit proxies. Greeks are model estimates, not historical vendor observations.
- Value 1-minute close at timestamp + 60 seconds; report per-row status and preserve unresolved fields as null. Preserve exactly 8,999,865 source rows and all 61 month partitions. Output data chunks must remain encrypted with the existing HF_TOKEN-derived encryption key.

## Required tester approval
No external request, decryption, or enrichment is authorized until the exact developer SHA and exact blob hashes are reviewed and a PASS_WITH_SCOPED_RESTRICTIONS decision appears on phase-08-tester. A stale R1 decision must never authorize R2. The tester must run both the developer synthetic suite and the independent formula/time-resolution checks in a separate environment.

## Restrictions
- No Dhan API calls in this gate.
- No option P&L, holdout access, strategy promotion or commercial-use assertion.
- No plaintext data artifact upload or source row body in logs.
- The underlying research grid remains PARTIAL_GRID and is not all exchange-listed NIFTY contracts. Point-in-time expiry master, lot/tick history and executable historical bid/ask remain unresolved.
- Hugging Face source licence CC-BY-NC-4.0 permits non-commercial use only.

**Developer → Tester:** independently verify the exact-timestamp join at second-resolution timestamp dtype, row preservation, expiry/TTE handling, IV inversion/fallback and Greek formula signs/units.

**Tester → Developer:** approve only the exact R2 snapshot, and only for the specified HF spot/expiry-calendar enrichment. Keep trade execution and strategy-testing gates blocked.
