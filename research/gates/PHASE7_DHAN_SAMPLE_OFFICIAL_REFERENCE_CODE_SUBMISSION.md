# Developer Submission — Official NIFTY Sample Cross-Check Code Gate

**State: RESUBMITTED FOR INDEPENDENT TESTER REVIEW — offline code only. No public-source requests are authorized.**

## Exact tested snapshot

- Developer code/test commit: `fc584bb1abbb335f7924a964b387eb8d67206830`
- Offline hosted gate: [Run 38058028914](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38058028914), success.
- Protocol check: [Run 38058029128](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38058029128), success.

| File | Git blob SHA |
|---|---|
| `scripts/official_reference_crosscheck.py` | `ef5b507d9c1706b2afd16338db8bec2bd517352d` |
| `scripts/run_official_reference_crosscheck.py` | `ff593638d3f76671215cfe55a5cc1f96859096ea` |
| `scripts/test_official_reference_crosscheck.py` | `2817c41ba25882930ccb0a0fc2d7f77968da67ea` |
| `scripts/test_run_official_reference_crosscheck.py` | `8c02fdef90593f6223a6d1b8bf3248163bf64880` |
| `scripts/dhan_instrument_master.py` | `b292c10735ec43520a664ed9b8e892072eb169a2` |
| `scripts/test_dhan_instrument_master.py` | `fa485bc5be727153c52e7e6ef96a4251b5c553c3` |
| `.github/workflows/phase-07-official-crosscheck-tests.yml` | `b450da4b9ffed8d8e38c8f7383084e1ba987b303` |
| `research/phase7/DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN.md` | `a9715169626e48f619c096b0dbffee6b10c79bfe` |
| `research/gates/PHASE7_DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN_RETESTER.md` (tester branch) | `d9be4e443c329681b982e4e79b15326a72cfbefd` |
| Previous independent code REQUEST CHANGES report | `d4633136f94b6a78ae2a93d9f13418d68133248e` |

## Hosted test evidence

Run 38058028914 logs report:
- **9** Dhan instrument-master offline tests passed.
- **17** official-reference adapter offline/mock tests passed.
- **9** official-reference runner offline/mock tests passed.
- Both CLIs explicitly report `OFFLINE_VALIDATION_ONLY`, and the test artifact contains no actual official-source response.
- Protocol check 38058029128 passed repository and literature-registry checks.

## Corrections made after prior tester REQUEST CHANGES

1. **Compact segment vs API enum:** `SEM_SEGMENT` is interpreted as a compact master code (C/D/E/M), not directly compared with API enum `IDX_I`. The index mapping check separately validates exchange, instrument name, the exact frozen trading symbol `NIFTY`, and optional display/name labels.
2. **Exact mapping acceptance:** the parser now requires `SEM_TRADING_SYMBOL == NIFTY` after normalization. The regression rejects `NIFTY100` even where optional labels are blank and separately rejects contradictory bank/VIX display fields.
3. **Cached Dhan source provenance:** before making either public request, the runner reads the already committed Dhan `response.json` and its `manifest.json`. It verifies the raw response SHA-256 `efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70`, Dhan request parameters, response metadata and byte counts, one-element arrays, timestamp/local trading date, OHLCV values, and the manifest's cached validation record. The comparison uses the row actually parsed from the hashed cache; missing/modified data fails before constructing either network opener.
4. **Existing bundle integrity:** reuse of an already existing cross-check cache now validates `manifest.json` against the current cross-check manifest hash, source hashes/lengths, validated rows, mapping, exact MATCH comparison, prior Dhan sample provenance and exact source metadata. Corrupt JSON or altered source URL is rejected rather than being accepted as `CACHE_ALREADY_PRESENT`.
5. **Regression suite:** newly added tests cover changed/missing cached Dhan bytes, invalid cache manifest/request parameters, non-exact NIFTY symbol, malformed existing bundle manifest, and tampered source metadata. The offline workflow remains read-only, secret-free and has no public-source request step.

## Explicit authorization boundary

- No request has been made to `www.niftyindices.com` or `images.dhan.co` by this implementation.
- There is no official cross-check request manifest, approval record or live workflow in this current gate.
- The prior Dhan sample approval stays **SPENT** and cannot be reused.
- The original Dhan sample remains quarantined from feature engineering, model training/validation and prediction claims until the official primary-source cross-check and mapping lookup succeed.
- The 8 MiB public Dhan CSV cap and the reverse-engineered NiftyIndices request shape remain unverified against live responses; this gate only establishes offline safety and deterministic test behavior.

## Next gate

Only after the independent tester issues a PASS for this exact implementation may the developer prepare a new single-use two-source manifest and a guarded workflow. That manifest/workflow must be independently reviewed as a separate gate before either public source is contacted. On a failure or discrepancy, no raw provider error body may be saved; no partial cache bundle or model/data acceptance is allowed.

**Developer → Tester:** Independently inspect the exact blobs above and Run 38058028914. Confirm the old compact-segment issue is resolved; `NIFTY100` is rejected; the original Dhan cached response is hash/schema/date-verified before either opener is built; the runner compares against the actual cached row; and an existing bundle's full relevant manifest/source metadata is validated before reuse. Return PASS or REQUEST CHANGES. Do not authorize public-source requests directly.
