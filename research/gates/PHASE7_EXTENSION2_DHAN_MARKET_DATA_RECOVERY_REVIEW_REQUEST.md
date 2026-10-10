# Developer → Tester Review Request — DhanHQ Market-Data Recovery Specification

**Requested decision: PASS / REQUEST CHANGES for specification only.**  
**Reviewed developer commit containing spec:** `489bc83cdf655e54166af50a6b443b780e9af145`.  
**Spec Git blob:** `2f8e31333ae2026fbe5887192403b6e388c26bf5`.  
**Live requests authorized: NONE.** The previous FII/DII single-run manifest is spent and must not be reused.

## User request

The user added repository secret `DHAN_ACCESS_TOKEN` and asked that it be used to resolve data-availability issues and rerun analyses. The token value has not been accessed, printed, committed, or included in artifacts. No Dhan API request has been made.

## Scope submitted for review

Read `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` at the exact blob above. The proposal asks for a finite, fail-closed DhanHQ source path:

- one authentication/entitlement probe to `GET https://api.dhan.co/v2/profile`; discard the body and persist only redacted status/boolean fields;
- official instrument-master resolution, with exact URL/size/parser pinning to be approved before any download;
- up to four daily historical candle requests to `POST https://api.dhan.co/v2/charts/historical`, for no more than two uniquely resolved instruments and two fixed ten-calendar-day windows;
- five authenticated requests maximum, 4 MiB total response-body cap, 64 KiB transport cap on the profile body, 1 MiB per candle response, 20-second timeout, no retries or redirects;
- no trading/account/order endpoints, no token logging, no bulk history, features/labels, model fitting, metrics or holdout access.

The documented daily historical endpoint returns instrument OHLCV candles and has a non-inclusive `toDate`. The official documentation says daily history may extend to instrument inception; intraday data has a five-year limit and at most 90 days per request. Data API access may require a separate subscription. These facts do **not** establish that Dhan provides aggregate daily FII/FPI and DII cash-flow totals; the spec explicitly preserves that unresolved data gap.

## Independent review requested

Verify:
1. official Dhan endpoint/authentication semantics and whether the token can be checked without persisting account-identifying profile fields;
2. instrument-master identity must be resolved from official metadata, never guessed;
3. request, response-byte, redirect, date-window and timeout caps are internally consistent;
4. response errors and token values cannot leak through logs/artifacts;
5. no live source request can happen before a new exact-snapshot code gate and single-use manifest;
6. the proposal keeps Dhan candles separate from FII/FPI/DII aggregate flows;
7. this is a specification gate only and does not authorize bulk acquisition or analysis.

**Tester → Developer:** Return PASS or REQUEST CHANGES on the exact spec blob. Do not authorize live requests at this gate.

**Developer → Tester:** Implement only after the spec decision; submit exact script/test/workflow blobs for a new code gate. No source requests until the implementation PASS and a separate single-use manifest.
