# Independent Tester Report — DhanHQ Market-Data Recovery Specification

**Current decision: PASS WITH SCOPED RESTRICTIONS — specification only.**  
**Reviewed spec commit:** `56c8197832e1bb04a20b3b6d9b68f6468ffeaf49`.  
**Reviewed spec Git blob:** `f87e8ecaec0a26947438131fef466aae3e57d824`.  
**Live source requests: NOT AUTHORIZED.**  
**Full-history acquisition: NOT AUTHORIZED.**  
**Model fitting: NOT AUTHORIZED.**

## 1. Independent review

Reviewed:
- `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` at exact blob `7fb4a477d4c85b382656073f97881fe036cd6646`;
- `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_REVIEW_REQUEST.md`;
- official DhanHQ documentation for historical data, authentication and instrument metadata.

References:
- Historical data: https://dhanhq.co/docs/v2/historical-data/
- Authentication: https://dhanhq.co/docs/v2/authentication/
- Instrument list: https://dhanhq.co/docs/v2/instruments/
- Expired options: https://dhanhq.co/docs/v2/expired-options-data/

## 2. Findings

### Pass — data semantics are scoped correctly

DhanHQ v2 `POST /charts/historical` returns instrument candles with OHLCV and, where applicable, open interest. The daily `toDate` is non-inclusive. The docs say daily history can extend to instrument inception; intraday history is limited to five years and at most 90 days per call. Dhan's instrument-list documentation provides a segment-specific `GET /v2/instrument/{exchangeSegment}` endpoint and CSV master links.

The spec correctly says these candle endpoints are **not** documented as a daily aggregate FII/FPI/DII cash-flow source. Therefore Dhan can potentially improve index/price/derivative history, but cannot by itself close the FII/DII flow-data gap.

### Pass — authentication handling is privacy-aware

The proposal discards the `/v2/profile` response body and stores only redacted status booleans/categories. It explicitly forbids logging or persisting client identifiers, name, UCC, active-segment list, token validity timestamp, raw profile JSON, token values, and authorization headers. It also prohibits trading/order/account transaction endpoints.

### Pass — bounded sample budget is internally consistent

- At most six authenticated requests: one profile, one `IDX_I` instrument metadata request, four daily-candle requests.
- Maximum response bodies: profile 64 KiB, index metadata 1 MiB, each of four candle responses 752 KiB. Worst-case aggregate is 64 KiB + 1024 KiB + 4 × 752 KiB = 4096 KiB exactly, matching the 4 MiB global cap.
- The global budget must be enforced across all calls, including error bodies; do not rely on per-response limits alone.

### Pass — staged authorization remains appropriate

The proposal correctly separates specification, offline implementation, code review, one bounded sample and artifact review. The spent FII/DII discovery manifest cannot be reused. No authenticated request is authorized by this specification decision.

## 3. Decision and limits

**PASS WITH SCOPED RESTRICTIONS — specification only, corrected exact spec blob.**

This does not authorize:
- any Dhan network request;
- full-history acquisition or cache population;
- features/labels, prediction runs, model fitting, metrics or p-values;
- options strategy evaluation or final-holdout access.

The user-reported secret has not been read, printed, or used by the tester.

**Tester → Developer:** Fix the 4 MiB aggregate budget inconsistency, then implement the import-safe adapter and offline fixtures only. Submit exact script/test/workflow blobs for a separate code gate. Do not request or use the secret until the code gate passes and a fresh single-use manifest validates.

**Developer → Tester:** Re-review the corrected exact implementation snapshot, especially shared request/byte-budget enforcement, profile-body discard/redaction, index identity resolution, date validation and fail-closed authorization. The later sample artifact requires a separate post-run audit.
