# Developer → Tester Review Request — DhanHQ Market-Data Recovery Specification

**Requested decision: PASS / REQUEST CHANGES for specification only.**  
**Spec commit:** `5e761ffe535877448f494dfb17216bdff7373eee`.  
**Current spec Git blob:** `a1100bd3adca6abd6115c356bfd4a447909576a4`.  
**Live requests authorized: NONE.** The prior FII/DII one-run manifest is spent and must not be reused.

## User request and secret handling

The user says repository secret `DHAN_ACCESS_TOKEN` has been added and asks to use it to resolve data gaps and rerun analyses. The token value has not been accessed, printed, committed, hashed, or included in any artifact. No Dhan endpoint has been called.

## Exact proposed scope

Review `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` at the exact spec blob above. This proposes a finite first sample only after future implementation and run gates:

- one GET `https://api.dhan.co/v2/profile`; discard the body immediately and persist only redacted HTTP/status booleans (no client ID/name/UCC, active-segment list, validity timestamp, raw JSON or token);
- one GET `https://api.dhan.co/v2/instrument/IDX_I` with a 1 MiB cap to resolve NIFTY 50 and India VIX IDs from official metadata; no guessed IDs and no all-instrument CSV download;
- at most four POSTs to `https://api.dhan.co/v2/charts/historical`, at most two instruments and two fixed ten-calendar-day windows;
- six authenticated requests maximum, 4 MiB total response-body budget, 64 KiB profile cap, 1 MiB instrument metadata cap, 1 MiB per candle response, 20-second timeout, no retry or redirect;
- no order, trading, position, fund, or account transaction endpoint; no token logging; no bulk history, feature/label generation, model fitting, metrics, or holdout access.

The official DhanHQ v2 docs describe daily instrument candles (OHLCV, with OI where applicable), with a non-inclusive `toDate`; intraday data has a five-year limit and at most 90 days per call. Data API entitlement may require a separate subscription. Dhan's documented historical-candle endpoints do **not** document combined daily FII/FPI/DII cash-flow totals; this proposal must not claim to close that specific flow gap.

Official references:
- Historical data: https://dhanhq.co/docs/v2/historical-data/
- Authentication: https://dhanhq.co/docs/v2/authentication/
- Instrument list: https://dhanhq.co/docs/v2/instruments/
- Expired options: https://dhanhq.co/docs/v2/expired-options-data/

## Independent checks requested

1. Verify endpoint and authentication semantics from official docs.
2. Verify that the profile body cannot leak identifying data and that token strings never enter logs/errors/artifacts.
3. Verify the segment-specific metadata lookup, identity ambiguity handling and hard caps.
4. Check that the request/byte/time budgets are internally consistent and that there is no automatic widening or redirect.
5. Confirm all live calls remain impossible before a new exact-snapshot code PASS and a separate single-use manifest.
6. Confirm candles are not misrepresented as FII/FPI/DII flow and the spec does not authorize full history or modeling.
7. Return PASS or REQUEST CHANGES on this exact spec blob only.

**Tester → Developer:** Do not authorize live requests at this spec gate. If passing, permit implementation/offline tests only.

**Developer → Tester:** After spec decision, submit exact adapter/test/workflow blobs for code review. A separate single-use manifest is required before one bounded authenticated sample. The resulting artifact needs its own audit.
