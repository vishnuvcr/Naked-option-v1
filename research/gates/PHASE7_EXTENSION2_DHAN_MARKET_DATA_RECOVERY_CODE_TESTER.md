# Independent Tester Report — DhanHQ Adapter / Offline Gate

**Current decision: PASS WITH SCOPED RESTRICTIONS — adapter/offline tests only.**  
**Reviewed developer commit:** `46305d374a60babd6ac813715aad516717a94d1b`.  
**Live Dhan requests: NOT AUTHORIZED.**  
**Full-history acquisition: NOT AUTHORIZED.**  
**Model fitting: NOT AUTHORIZED.**

## 1. Exact protected files independently reviewed

| File | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` | `f87e8ecaec0a26947438131fef466aae3e57d824` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md` | `9db93dfb56e309dcccf549e51da09004e5f4b276` |
| `scripts/dhan_market_data_recovery.py` | `3ee3d4db194fd5b9f05816454de2e756f9a8cb46` |
| `scripts/test_dhan_market_data_recovery.py` | `d45478853661a29d1160fc371def865e2bf1c510` |
| `.github/workflows/phase-07-dhan-market-data-tests.yml` | `b43ce4dadca4e5867173136531e71c63bb74e9a3` |

## 2. Hosted evidence

[Offline regression Run 38042858506](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042858506) succeeded on the reviewed commit and logged **25/25 checks passed**. It runs only the fixture test script and does not bind the Dhan secret or execute a live entrypoint.

An earlier run, [38042825681](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38042825681), failed because the CSV fixture encoded literal backslash-n sequences rather than newlines. The fixture was corrected and the later hosted run passed. The earlier failure must remain in the developer error log.

## 3. Independent findings

- **Secret safety:** token is not accessed by the offline workflow; the profile parser emits only status/boolean fields. HTTP error bodies are discarded and error messages are reduced to a status or exception type.
- **Fail-closed transport:** registered HTTPS endpoints only; no redirects/retries; fixed timeout; request and aggregate byte budgets; profile, metadata and candle body caps.
- **Instrument identity:** JSON/CSV metadata parsing is supported; the parser refuses missing or ambiguous NIFTY 50 / India VIX mappings rather than guessing an ID.
- **Candle schema:** required arrays must align and be non-empty; values must be finite; OHLC inequalities, timestamp order/uniqueness, IST session date and requested window are checked.
- **Scope:** no live workflow exists in this reviewed snapshot. The adapter's live function is guarded by an explicit workflow authorization environment flag. This PASS cannot authorize setting that flag or making any request.
- **Data semantics:** Dhan daily candle APIs are a potential source for instrument OHLCV/OI; they do not document the aggregate daily FII/FPI/DII flow series. That gap remains open.
- **Source-shape caveat:** actual `IDX_I` response shape and actual data-plan entitlement remain unverified because no authenticated request has been made. If the approved sample disagrees with parser assumptions, stop and return REQUEST CHANGES; do not widen scope.

## 4. Decision

**PASS WITH SCOPED RESTRICTIONS** for adapter and offline-test code only. The next allowed task is to implement and submit a separate live workflow with a hash-bound one-run manifest validator/spend guard for independent review. That workflow must have automatic and manual entry points, but neither can bypass the manifest. The Dhan token must be injected only as `DHAN_ACCESS_TOKEN: ${{ secrets.DHAN_ACCESS_TOKEN }}` inside the guarded job, never printed, and never made available to offline test jobs.

This decision does **not** authorize:
- live authenticated requests;
- full-history acquisition or cache population;
- features/labels, predictions, model fitting, metrics or p-values;
- options strategy testing or final-holdout access.

**Tester → Developer:** Mirror this report exactly to the developer branch. Submit a separate guarded live workflow and manifest validator for independent review. Keep all network requests disabled until that workflow passes and a new single-use manifest is created.

**Developer → Tester:** Review the exact workflow snapshot independently, especially manifest digest/hash/blob/ancestry checks and manifest consumption before the first HTTP request. After the one approved sample, audit the artifact separately.
