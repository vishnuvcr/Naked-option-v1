# Independent Tester Report — Dhan Historical Data Recovery Plan Amendment

**Decision: PASS WITH SCOPED RESTRICTIONS — planning gate only. No code, live request, bulk download, feature engineering or model run is authorized.**

**Reviewed developer plan:** `research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md`  
**Developer plan blob SHA:** `9145f88ec99169a900d9ff2c7b77c0592781f5ae`  
**Review date:** 2026-10-10

## Independent source checks

1. Dhan's official historical-data documentation lists `POST /charts/historical` for daily OHLCV and `POST /charts/intraday` for minute bars. It describes daily availability back to an instrument's inception and intraday intervals of 1, 5, 15, 25 and 60 minutes, up to five years for active instruments, with a maximum 90-day range per intraday call: https://dhanhq.co/docs/v2/historical-data/
2. Dhan's official expired-options documentation describes `POST /charts/rollingoption`, minute-level rolling options up to five years, up to 30 days per request, and fields including OHLC, IV, volume, OI, strike and spot. It documents the ATM-relative strike limitations. The plan correctly avoids claiming that this is a complete contract-level historical chain: https://dhanhq.co/docs/v2/expired-options-data/
3. Dhan's official option-chain documentation describes current option-chain values (including OI, Greeks, IV, volume, LTP and top bid/ask) and a one-request-per-three-seconds limit. The plan correctly distinguishes it from a historical option-chain archive: https://dhanhq.co/docs/v2/option-chain/
4. Dhan's instrument-list documentation separately lists public CSV instrument masters and the segmentwise endpoint. The plan correctly treats present-day instrument metadata as a mapping aid, not evidence of historical listing state: https://dhanhq.co/docs/v2/instruments/
5. Dhan support describes Data API as a distinct access/entitlement from ordinary Trading API access. The plan properly requires entitlement to be verified by a bounded observed API response rather than inferred from the existence of a token: https://dhan.co/support/platforms/dhanhq-api/how-to-use-algo-in-dhan/

## Governance and statistical review

- The amendment preserves the current prediction-only scope and does not authorize Phase 8 option P&L/strategy optimization.
- It preserves prior Run #44 and Phase 7 Run #994 as immutable historical results and keeps the final untouched holdout sealed.
- It requires point-in-time availability, chronological validation, training-only preprocessing, frozen amended feature definitions and family-wise multiple-testing correction before interpreting new results.
- The sequence separates plan, offline implementation/tests, fresh exact-snapshot code review, one-use manifest, tiny sample, independent sample audit, bounded expansion and independent empirical audit.
- It correctly calls out that rolling ATM-relative options may not supply complete chain history or historical bid/ask. It requires response-array alignment, units and timestamps to be checked before feature use.
- It includes immutable hashes, validated cache partitions, source lineage, fail-closed errors, redaction and status/error/chat/README updates.

## Restrictions before implementation and data use

1. Do not create a live workflow or make a live API call until a separate offline implementation/code gate passes and a new single-use manifest pins the exact commit, protected Git blobs/SHA-256 values, tests and workflow.
2. First authenticated request must be the tiny daily spot-history sample described in the plan. Do not probe account/profile metadata. Do not mix a diagnostic probe with a market-data request or reuse the spent redirect manifest.
3. Any API data field, symbol mapping, date coverage, bar-size, expiry/strike semantics or response-array behavior not yet empirically established must remain **unverified**, not be assumed.
4. Full five-year intraday/rolling-option acquisition must be partitioned and separately gated; a successful sample does not authorize bulk retrieval, feature fitting or model reruns.
5. Dhan response data must be overlap-checked against independent official/reference data where available. A green API response is not sufficient data-quality evidence.
6. Keep the project's existing method registry frozen for this step. If Dhan-derived features require a new method/family definition, submit and approve that specification before model metrics are examined.

## Decision

The plan is scientifically coherent and consistent with the public endpoint documentation. Approve it to move to **offline implementation and regression tests only**. No source acquisition or prediction experiment is authorized at this gate.

**Tester → Developer:** Implement the source client without network activity at import/test time; add mocked regression tests for endpoint/method allowlists, credential isolation, redirects, timeouts, request pacing/budgets, JSON/schema/array alignment, timestamp windows, malformed/partial responses, safe logs and atomic cache failure. Submit exact blobs and test results for a separate review.

**Developer → Tester:** Independently inspect the full implementation and workflow before preparing a new one-use manifest. Do not approve live acquisition until the source/path allowlist, response validators, cache provenance and tested authorization ordering are confirmed.
