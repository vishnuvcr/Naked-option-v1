# Independent Tester Report — Dhan Sample Diagnostic Correction

**Decision: REQUEST CHANGES — partial correction; fresh live retry NOT AUTHORIZED.**  
**Reviewed developer head:** `7fb5b856f936ba5a95c4d249ca316651f66615e3`.  
**Protected source snapshot reviewed by blob:** adapter `e47e500f0d15e117e0078a9c98badd96bf62499f`; offline tests `22a366342432908aaa231a7e04ddd25825e39ce0`; sample validator `3c99140a5488cd58ee3bed9c21cd659183adbdf2`; offline workflow `b43ce4dadca4e5867173136531e71c63bb74e9a3`; guarded workflow `aa37cec66d46f3c181a7bda213226991c045b189`.  
**Live Dhan requests authorized by this report: NONE.** The preceding one-run manifest is SPENT.

## 1. Evidence reviewed

- First bounded sample: [workflow run 38043148580](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043148580), artifact `11666064550`, ZIP SHA-256 `45f2b23a0835cb6b1af52ac12913bf86062f9c82a0d3edcef4c810a3f30f38d9`.
- The first artifact contains `status=BLOCKED_INSTRUMENT_METADATA` and `request_count=2`; it contains no candle data. The independent artifact audit is [PHASE7_EXTENSION2_DHAN_MARKET_DATA_SAMPLE_AUDIT.md](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_SAMPLE_AUDIT.md).
- Offline run [38043259438](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043259438) passed the current diagnostic regression suite. This validates the local test path, not an actual HTTP-error header path or data availability.
- The developer error log records the sample failure and diagnostic omission. No model was fit and no prediction was rerun.

## 2. Blocking finding — safe content type is not preserved through the real error path

The prior artifact audit required the failed metadata response to include the numeric HTTP status and a safe content type, while continuing to discard provider bodies and raw headers.

The latest helper `blocked_metadata_result` can filter a provided `content-type`, but its caller does not pass one:
- `request_bytes` handles `urllib.error.HTTPError` by returning `(status, b"", {})`, discarding all headers;
- `live_sample` unpacks the metadata response headers into `_` and then calls `blocked_metadata_result(status, {}, budget, profile)`;
- the added test calls `blocked_metadata_result` directly with fabricated headers. It does not exercise the actual `HTTPError → request_bytes → live_sample` path.

Therefore the safe content-type field will remain empty for the failed HTTP status path just encountered. The correction is incomplete relative to the previous tester's required change.

## 3. Required correction before reconsideration

1. On `HTTPError`, return only the numeric status and an explicit whitelist of safe headers (at minimum `content-type`), without reading or retaining the provider error body, cookies, authorization headers or other raw headers.
2. Pass those safe headers to `blocked_metadata_result` in the actual live path.
3. Add an offline integration-style regression with an `HTTPError` fixture containing a safe content type, a `Set-Cookie` value and a sensitive body sentinel. Assert that the status and content type survive while the body and sensitive headers do not appear in the output.
4. Re-run the offline suite and update the developer's exact-snapshot review request with the reviewed commit, blob IDs and byte hashes for every protected file.
5. Obtain a fresh independent code/workflow gate and create a new single-use manifest only after that gate passes. **Do not reuse the spent manifest.**

## 4. Scope and interpretation

- No candle request succeeded; no NIFTY/India VIX price history or options history was obtained.
- This sample did not resolve the separate FII/FPI/DII aggregate-flow data gap.
- No full-history pull, feature/label construction, model fitting, predictive metrics, strategy testing or final-holdout access is authorized.
- The numeric HTTP status from this failed call was not present in the first artifact. This report does not infer that value.

**Tester → Developer:** Correct the actual HTTP-error header propagation path, add the regression described above, and submit the exact updated snapshot for a new independent gate. Keep source requests disabled.

**Developer → Tester:** Re-review the corrected exact blobs and hosted offline run. If any diagnostic field can expose credentials or if the actual HTTP-error path still drops safe metadata, return REQUEST CHANGES; do not permit a retry until the gate passes.
