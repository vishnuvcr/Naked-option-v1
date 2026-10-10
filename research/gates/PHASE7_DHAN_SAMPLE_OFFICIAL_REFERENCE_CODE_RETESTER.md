# Independent Tester Re-review — Official NIFTY Sample Cross-Check Code

**Decision: REQUEST CHANGES — no public-source request authorized.**

**Reviewed developer branch head:** `f2903561c021bcce5c58e3b917b3f7e09cb95aa2`  
**Hosted offline suite:** [Run 38056916677](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38056916677), success: 9 instrument-master, 16 cross-check adapter, 7 runner tests.  
**Protocol check:** [Run 38057027536](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38057027536), success.

Exact blobs reviewed:
- `scripts/official_reference_crosscheck.py`: `0a8c7944885b0b50be3eeedfed0eec6b60260638`
- `scripts/run_official_reference_crosscheck.py`: `6d617987f43d9ca41840b3e14ff36521396df4b1`
- `scripts/test_official_reference_crosscheck.py`: `148ed4f8fcbdd8fd188b928cb10cf7689fb1d0f2`
- `scripts/test_run_official_reference_crosscheck.py`: `4109f5cd0784c975d3cc6e440a19797ea09b0bfc`
- `.github/workflows/phase-07-official-crosscheck-tests.yml`: `b450da4b9ffed8d8e38c8f7383084e1ba987b303`
- revised scope plan: `research/phase7/DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN.md`, blob `a9715169626e48f619c096b0dbffee6b10c79bfe`

## Prior two findings — resolved

1. **Compact segment/API enum confusion:** Current `parse_dhan_instrument_mapping` no longer requires CSV `SEM_SEGMENT == IDX_I`. It checks the compact segment namespace separately, records the compact code, and uses instrument/symbol fields as distinct evidence. This resolves the deterministic mismatch called out in the first REQUEST CHANGES report.
2. **Missing offline gate:** The current developer branch has the dedicated adapter and runner mock tests and a single consolidated offline-only workflow. The latest hosted run passed all 32 mocked tests, and the protocol run passed. No live workflow/manifest exists and no source request has occurred.

## Finding 1 — parser ignores the expected exact trading symbol

The current constant `EXPECTED_MAPPING` includes `symbol: "NIFTY"`, but `parse_dhan_instrument_mapping` never compares the returned `SEM_TRADING_SYMBOL` exactly with that expected symbol. It only requires that at least one of trading symbol / symbol name / custom symbol contains “NIFTY” and is not excluded by “BANK” or “VIX”. If the display fields are empty, a candidate symbol such as `NIFTY100` could pass this broad substring rule.

**Required correction:** compare `SEM_TRADING_SYMBOL` against the frozen expected symbol `NIFTY` exactly (after documented normalization), and keep the optional display-name checks as additional conditions rather than substitutes for the exact symbol. Add a regression where trading symbol is `NIFTY100`, other label fields are empty and it must fail.

## Finding 2 — OHLC comparison does not consume/verify the cached Dhan response artifact

`run_crosscheck` calls `adapter.compare_ohlc(nifty_row, adapter.EXPECTED_DHAN_ROW)`. That mapping is a literal constant in Python. It does not open the previously fetched Dhan sample response or validate its raw SHA-256 and manifest. Consequently the cross-check can still pass against the hard-coded values even if the actual cached Dhan file were changed or removed. This weakens the claimed source-to-source provenance.

**Required correction:** before any public requests, open the exact previously committed Dhan sample response from the cache path, verify its SHA-256 equals `efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70`, parse the timestamp and OHLCV arrays, enforce exactly one record for local date 2024-01-02 and the expected OHLCV schema, and build the comparison row from those verified cached bytes. Include the source response hash and validated row in the new official cross-check manifest/cache provenance. If the cached sample is missing, hash-mismatched or date-invalid, fail before opening either network connection. Tests must mutate/remove the cached sample and assert both source requests are not attempted.

## Finding 3 — existing cache reuse checks raw files but not the bundle manifest

In `_atomic_bundle`, if the hash-named target directory already exists, the code compares the stored official JSON and compact CSV hashes but returns `CACHE_ALREADY_PRESENT` without verifying `manifest.json`. A stale or corrupted manifest can therefore be accepted as a complete existing cross-check bundle despite carrying the wrong scope, authorization manifest digest, row, validation comparison or source metadata.

**Required correction:** when reusing an existing bundle, parse and validate `manifest.json` against the expected scope, current manifest hash, both raw hashes/lengths, validated official row, validated mapping and exact MATCH comparison. If any field is missing or inconsistent, fail closed with cache collision/manifest invalid and do not overwrite. Add regression tests that precreate a bundle with correct raw source bytes but malformed or inconsistent manifest; those must fail rather than return CACHE_ALREADY_PRESENT.

## Checks that passed in this review

- Both URLs are exact allowlisted HTTPS paths; no source credentials are allowed by the request helper, including token/cookie/authorization headers.
- Each source request is limited to one call, 20 seconds, byte-capped, content-type checked, HTTP 200 only and redirect-rejecting. Error bodies are closed without reading, retry count stays zero.
- NIFTY parser requires exactly one row for the exact date/index and validates numeric values and OHLC consistency.
- Dhan compact CSV uses the actual security-id field; compact segment namespace is not directly compared to `IDX_I`.
- The runner writes the success bundle only after both responses parse, the mapping validates, and all OHLC values match. Partial-source errors return a safe report and do not create a cross-check cache bundle.
- The module CLIs are offline-only by default. The workflow has read-only contents permission, no secrets/network acquisition step, and pushes are restricted to `phase-07-developer` for manual tests.
- No request was sent to NSE Indices or `images.dhan.co`; no cache has been added for this cross-check; no feature/model/strategy run or holdout access occurred.

## Decision

The implementation is **not yet approved** for the official NIFTY/Dhan source request. Address findings 1–3, add the specified offline regressions, run the hosted workflow, and submit the new exact source/test/workflow blob set for independent re-review. The earlier Dhan sample approval remains SPENT and cannot be reused.

**Tester → Developer:** Fix the exact-symbol acceptance, require the real cached Dhan response to be hash/schema/date-verified before opening either source, and validate an existing cache bundle's manifest before reuse. Add offline regressions and update status/error/chat/README after green tests. Do not create or spend a live manifest.

**Developer → Tester:** Re-review the corrected exact snapshot and hosted logs independently. No public-source request is authorized unless that new code/workflow gate passes and a fresh separate two-source manifest/workflow receives its own PASS.
