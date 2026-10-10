# Developer → Tester Review Request — DhanHQ Adapter / Offline Gate

**Requested decision: PASS / REQUEST CHANGES for adapter, offline tests and offline workflow only.**  
**Reviewed developer commit:** `46305d374a60babd6ac813715aad516717a94d1b`.  
**Live Dhan requests authorized by this submission: NONE.** No live workflow or sample manifest has been created.

## Exact reviewed files and Git blob IDs

| File | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` | `f87e8ecaec0a26947438131fef466aae3e57d824` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md` | `9db93dfb56e309dcccf549e51da09004e5f4b276` |
| `scripts/dhan_market_data_recovery.py` | `3ee3d4db194fd5b9f05816454de2e756f9a8cb46` |
| `scripts/test_dhan_market_data_recovery.py` | `d45478853661a29d1160fc371def865e2bf1c510` |
| `.github/workflows/phase-07-dhan-market-data-tests.yml` | `b43ce4dadca4e5867173136531e71c63bb74e9a3` |

The tester report is mirrored byte-for-byte on both branches. The adapter import has no network side effects; the only live entrypoint refuses to run unless `DHAN_LIVE_SAMPLE_AUTHORIZED=1`, which must only be set by a future guarded workflow after a separate manifest is validated and consumed.

## Hosted offline evidence

[Run 38042858506](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042858506) succeeded on the reviewed commit: **25/25 offline regressions passed**. The workflow installs Python and runs the fixture test script only; it does not pass `DHAN_ACCESS_TOKEN`, make HTTP calls, or call `live_sample`.

A prior fixture run failed because CSV fixture newlines were escaped literally. This was corrected; the current hosted run is green. The failure and correction must be retained in the error log.

## Main review points

1. Request allowlist and HTTPS URLs; no redirects/retries; timeout and shared request/byte budget.
2. HTTP error bodies are discarded and only the status code is retained; exception strings are redacted.
3. Profile response is reduced to token-valid/data-plan booleans; identity fields and raw JSON are not returned.
4. Official index metadata parser accepts CSV or JSON, requires unique mappings for NIFTY 50 and India VIX, and rejects ambiguity.
5. Daily candle payloads use fixed non-overlapping ten-day windows and a non-inclusive end date.
6. Candle parser checks equal array lengths, finite OHLCV, OHLC inequalities, timestamp order/uniqueness, and requested date window.
7. India Standard Time is used when deriving session dates from epoch timestamps.
8. Four candle caps of 752 KiB + one metadata cap of 1 MiB + one profile cap of 64 KiB equal the 4 MiB global body budget.
9. Offline workflow has no live-source step and no secret environment binding.
10. The documented Dhan candle API is not a combined FII/FPI/DII aggregate-flow endpoint; do not claim this resolves that gap.

## Important limitations / requested tester scrutiny

- The official `IDX_I` response schema must be confirmed from a sample only after a later run gate. The parser supports common CSV/JSON shapes, but if the actual response shape differs, the sample must stop without widening.
- Dhan daily timestamp semantics must be verified against the sample and exchange session dates. No model fit is permitted at this stage.
- The adapter has no approved live workflow yet. This review cannot authorize any network request.
- Secret `DHAN_ACCESS_TOKEN` is never read by offline tests and has not been accessed or logged.

**Tester → Developer:** Return PASS or REQUEST CHANGES on these exact blobs. If passing, authorize workflow design only; do not authorize live requests.

**Developer → Tester:** After code review, submit a separate exact workflow snapshot with its manifest validation/spend guard. Require another independent workflow review before creating a single-use live-sample manifest.
