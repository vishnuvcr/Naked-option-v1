# Independent Tester Report — Official Primary-Source Cross-Check Plan

**Decision: PASS WITH SCOPED RESTRICTIONS — plan/documentation gate only. No network request is authorized.**

**Reviewed developer commit:** `8eb197afa31bf6970441e235f79b95d719819098`  
**Reviewed proposal blob:** to be confirmed from the developer branch before implementation; expected path `research/phase7/DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN.md`.

## Purpose and boundaries checked

The proposal correctly responds to the prior artifact review: the Dhan sample was fetched within scope and its OHLCV matches a secondary source, but model-data acceptance stays blocked until primary-source and instrument mapping checks are performed. It specifies only:
1. one same-day NIFTY 50 OHLC lookup from NSE Indices' public historical data interface; and
2. one public Dhan instrument-master CSV request to establish the minimal `13 / IDX_I / INDEX` mapping.

It explicitly forbids credential forwarding to the NSE Indices host or public Dhan CSV host, bulk history, extra endpoints, feature fitting, predictor reruns, strategy testing and holdout access. The prior one-use Dhan sample approval remains SPENT.

## Review findings

- **Scope:** acceptable. Two source requests maximum, one per allowlisted HTTPS host, with separate budgets.
- **Primary NIFTY OHLC comparison:** sensible and directly addresses the strongest unresolved source-quality issue. It compares all four OHLC fields exactly for 2 Jan 2024 and does not silently overwrite the Dhan result.
- **Endpoint qualification:** the historical-data interface is official at https://www.niftyindices.com/reports; the particular `Backpage.aspx/getHistoricaldatatabletoString` call shape is reverse-engineered rather than an official published OpenAPI contract. The proposal acknowledges this. The implementation must constrain it to one exact URL/body, reject redirects and unexpected envelopes, and preserve no raw error bodies. The live response schema remains unverified until this gate.
- **Instrument mapping:** public CSV URL is drawn from Dhan's official instrument documentation (https://dhanhq.co/docs/v2/instruments/). No token or credential is to be sent to `images.dhan.co`. The existing validator's 8 MiB cap is explicitly provisional; exceeding it is a safe failure, not authorization to follow redirects, retry or raise the cap in place.
- **Failure handling:** correct to cache the pair only after both source responses and all comparisons pass. If either response fails or the row differs, retain only safe status/hashes and leave both sources unaccepted.
- **Testing:** plan identifies the right offline failure cases, including malformed JSON envelope, wrong date/index, OHLC mismatch, nonunique/absent mapping, CSV size/schema, 3xx, 4xx/5xx, timeouts and partial-write prevention.
- **Separate gate:** appropriate. Implementation and mocked regressions need a new exact-snapshot tester review; an independent manifest/workflow PASS is needed before the two bounded public lookups.

## Restrictions

This report approves the **plan only**. It does not authorize:
- either network request;
- changing the spent Dhan sample manifest;
- raising the 8 MiB CSV cap without a new review;
- fetching more than the one date/one mapping row needed for this check;
- data-model acceptance, feature engineering, prediction reruns, options history, strategies or holdout access.

**Tester → Developer:** Implement the offline parser and separately guarded two-source fetch gate as defined in the proposal; use mocked responses and atomic no-write-on-failure tests. Pin the exact script/test/workflow blobs and submit that implementation for a second independent review. Do not issue the official-source calls yet.

**Developer → Tester:** Re-review the implementation snapshot, offline test outputs, endpoint/body allowlists, no-credential boundaries, two-source budgets and failure-atomicity before any new one-use manifest can be prepared.
