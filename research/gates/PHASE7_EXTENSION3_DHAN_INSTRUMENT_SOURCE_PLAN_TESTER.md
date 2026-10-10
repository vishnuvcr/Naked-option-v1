# Independent Tester Report — Extension 3 Official Dhan Instrument-Source Plan

**Decision: PASS WITH SCOPED RESTRICTIONS — proposal/documentation gate only.**  
**Reviewed proposal:** `research/phase7/EXTENSION3_DHAN_OFFICIAL_INSTRUMENT_SOURCE_PLAN.md`  
**Developer proposal commit:** `21c70a054c4272d2280da5872858e0d52934103d`

## Checks

1. The plan correctly separates the instrument-master metadata source from historical OHLC/volume and options history.
2. The official Dhan instrument documentation lists the compact CSV `https://images.dhan.co/api-data/api-scrip-master.csv`, detailed CSV `https://images.dhan.co/api-data/api-scrip-master-detailed.csv`, and the segmentwise API endpoint. The plan does not assume the previous S3 redirect host is approved for use.
3. The plan explicitly denies any network request at proposal stage and requires a fresh exact-snapshot code review and one-use manifest before a later CSV request.
4. It prohibits forwarding credentials to the public CSV host and requires HTTPS/hostname/content-type/size/schema/duplicate-ID checks, atomic cache creation, provenance and content hash.
5. The plan distinguishes an instrument master from prices and does not claim that a successful CSV fetch would produce predictive evidence.
6. Rejection criteria are fail-closed for redirects, unexpected host/content, oversize or malformed data, and ambiguous security IDs.

## Required restrictions for implementation

- The exact URL must remain the documented `https://images.dhan.co/api-data/api-scrip-master.csv` or `https://images.dhan.co/api-data/api-scrip-master-detailed.csv`; no URL derivation from the prior redirect target.
- Do not send `DHAN_ACCESS_TOKEN`, client ID, cookies or other credentials to `images.dhan.co`.
- Disable redirects. Any 3xx is a rejected fetch; do not follow it and do not make a second request.
- Set a conservative explicit byte cap before implementation; reject Content-Length over cap and stop reading at cap+1. Record the over-cap condition without retaining body contents.
- Offline tests must cover redirect rejection, HTTP error, content-type mismatch, invalid UTF-8/CSV, missing headers, duplicate/blank security IDs, truncation/oversize, atomic cache failure, deterministic hash/provenance and no-network import/test behavior.
- The live request must use a new manifest with exact protected Git blobs and SHA-256 values for the workflow, adapter, tests, validator, proposal and this tester report. The old redirect manifest is SPENT and must never be reused.
- The first successful CSV cache remains instrument metadata only. It does not authorize candles/history, options chains, DII/FII, news, feature engineering, modeling or holdout access.

## Decision

The proposal is adequate to proceed to **offline-only implementation and regression tests** on the developer branch. This decision does not authorize a live CSV request. After code and workflow are implemented, submit the exact snapshot for a separate code/workflow gate; only after that approval may a fresh one-use manifest be prepared and a manual run considered.

**Tester → Developer:** Proceed with offline-only implementation and tests under the restrictions above. No network request or credential use.

**Developer → Tester:** Submit exact code blobs, tests, workflow and manifest validator for a new independent code gate before preparing any live manifest.
