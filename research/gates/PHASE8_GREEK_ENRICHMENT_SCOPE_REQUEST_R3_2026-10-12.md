# Phase 8 — Greek-enrichment scope request R3 (2026-10-12)

## Purpose
R3 corrects a deterministic terminal-gate failure observed in R1 and R2: the encrypted cached source manifest used by the job has per-part `row_count` values but does not expose a top-level `rows_preserved` field. The prior code compared the output sum to an absent top-level key, so the completed 8,999,865-row result was rejected with `row count changed: source=None output=8999865` after the full calculation. No enriched artifact was uploaded.

R3 keeps the same narrowly scoped HF public-source authorization. It changes only manifest row-count derivation, regression coverage, preflight ordering and versioned output names.

## Exact source and requested data
- Reuse the immutable cached encrypted source artifact from Actions run 38131641336, artifact 11698879857, ZIP SHA-256 `40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b`.
- Validate exactly 61 part entries and derive expected total as the sum of their required integer, non-negative `row_count` fields. If a top-level `rows_preserved` is present, require it to equal the sum. Reject malformed counts, fractional counts, negative counts and inconsistent totals.
- Require the per-part sum to equal 8,999,865 before any Hugging Face data request. Repeat the same count assertion after processing all chunks; record the sum method in the coverage report.
- Fetch only public Hugging Face dataset `thetrademarkk/india-index-options-1m` file `index/NIFTY.parquet` and the file listing under `options/NIFTY/YYYY-MM-DD.parquet`. Preserve the resolved HF commit SHA, attribution and CC-BY-NC-4.0 non-commercial-use restriction.
- Convert timezone-aware source timestamps to Unix epoch seconds using the timestamp object's explicit `.timestamp()` method. Join spot fields on exact timestamps only; never forward-fill or interpolate.
- Use the dated HF expiry-partition list as a proxy for available dates and the separately labelled Tuesday-rule proxy for future dates. This is not an official point-in-time contract master.
- Invert Black–Scholes IV from minute option close where valid; otherwise use the documented labelled source-IV fallback. Use explicit `r=0,q=0` proxies. Greeks are model estimates, not historical vendor observations.
- Value 1-minute close at timestamp + 60 seconds. Preserve all 8,999,865 rows and all 61 partitions; encrypted-only upload remains mandatory.

## Required tester approval
No external request, decryption or enrichment is authorized until the independent tester reviews the exact developer SHA and blob hashes, runs the developer synthetic suite, runs independent formula/finite-difference tests and separately verifies missing/matching/mismatching manifest-total cases.

## Restrictions
- No Dhan API calls in this gate.
- No option P&L, holdout access, strategy promotion or commercial-use assertion.
- No plaintext data artifact upload or source row body in logs.
- The underlying research grid remains `PARTIAL_GRID`, not all exchange-listed contracts. Point-in-time expiry master, lot/tick history and executable historical bid/ask remain unresolved.
- Hugging Face source licence CC-BY-NC-4.0 permits non-commercial research only.

**Developer → Tester:** independently verify fail-closed per-part row-count derivation and the early 8,999,865-row preflight before any external HF request, along with the existing Greek/timestamp checks.

**Tester → Developer:** authorize only this exact R3 snapshot after tests pass; do not advance to P&L, holdout or strategy testing.
