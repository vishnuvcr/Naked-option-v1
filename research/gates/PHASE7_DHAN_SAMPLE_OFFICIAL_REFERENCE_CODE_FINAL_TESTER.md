# Independent Tester Final Report — Official NIFTY Sample Cross-Check Code Gate

**Decision: PASS WITH SCOPED RESTRICTIONS — offline code/workflow only. No public-source request is authorized by this report.**

**Reviewed developer snapshot:** `40f74a1ad27f13dfd90f30e9e9b4d32e89a0609a`  
**Offline hosted test run:** [38058028914](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38058028914), success.  
**Protocol check:** [38058181267](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38058181267), success.  
**Workflow copy on `main` and `phase-07-developer`:** identical blob `b450da4b9ffed8d8e38c8f7383084e1ba987b303`.

## Exact reviewed file blobs

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
| Developer handoff `research/gates/PHASE7_DHAN_SAMPLE_OFFICIAL_REFERENCE_CODE_SUBMISSION.md` | `56b85163b5a71395e15a5e75e9ad4a1133e482d5` |
| Prior code REQUEST CHANGES report | `d4633136f94b6a78ae2a93d9f13418d68133248e` |

## Test evidence

Hosted run 38058028914 passed:
- 9 Dhan instrument-master validator tests;
- 17 official-reference parser/request/response tests;
- 9 cross-check runner tests.

Both source adapters' CLIs report `OFFLINE_VALIDATION_ONLY` and `network_enabled=false`. The workflow has `contents: read`, no secret injection, no external-source request step, and only runs deterministic tests/static pin validation. Protocol run 38058181267 passed the repository contract/literature checks.

## Re-review findings

All five distinct code issues identified during review are now resolved in this snapshot:

1. **CSV compact segment vs API enum:** compact `SEM_SEGMENT` is checked only against its own documented compact namespace (C/D/E/M), not directly against the API-level `IDX_I` enum. The latter is kept as request/API semantic information rather than treated as the CSV value.
2. **Exact instrument symbol:** `SEM_TRADING_SYMBOL` must equal frozen expected symbol `NIFTY` after normalization. A candidate such as `NIFTY100` cannot be accepted just because a display field contains “NIFTY”. Contradictory bank/VIX display fields are rejected.
3. **Actual cached Dhan source provenance:** before either new public-source opener is created, the runner reads the committed sample JSON and its cache manifest. It checks the pinned raw SHA-256 `efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70`, exact Dhan request parameters, response status/content type/count/byte metadata, required arrays, one-row shape, OHLCV values and the timestamp's 2024-01-02 Asia/Kolkata date. It then compares the official OHLC against this parsed cached row instead of relying only on a Python constant.
4. **Existing cache bundle metadata:** when a hash-named cache directory already exists, the runner validates its manifest for scope, authorization-manifest hash, raw source hashes and sizes, validated rows, mapping, match comparison, the prior Dhan sample provenance and exact source metadata. Corrupt JSON or modified source metadata causes a fail-closed error rather than an accepted cache hit.
5. **Required regression coverage:** tests now exercise the exact NIFTY symbol, missing/hash-modified cached Dhan responses, inconsistent prior cache metadata, partial second-source failure, and corrupt or internally inconsistent existing bundle manifests. All are offline/mocked cases.

The prior tester REQUEST CHANGES report remains archived as history; this final report supersedes it for the exact blobs above only.

## Authorization boundary and limitations

- **No request has been made** to `www.niftyindices.com` or `images.dhan.co` by this implementation. No cross-check cache was created.
- The previously used Dhan one-day sample approval remains **SPENT** and cannot be reused.
- No official-source request manifest, approval record, or live workflow is present in this code-gate snapshot.
- The NiftyIndices route `/Backpage.aspx/getHistoricaldatatabletoString` is a reverse-engineered web-interface call rather than a published stable API contract. Its response envelope and availability remain unverified. The first future response must be independently inspected; any unexpected content fails closed.
- The public Dhan CSV's actual size/schema and the mapping response remain unobserved here. The 8 MiB cap remains provisional and must not be silently raised if the request fails.
- Passing this code gate does not accept the Dhan sample into prediction data, establish historical coverage, validate volume semantics, qualify a model, enable options/strategy tests or open the holdout.

## Decision and next allowed step

**PASS WITH SCOPED RESTRICTIONS — offline code/workflow only.** The developer may prepare a *new* exact-hash manifest, approval record and guarded workflow that permits at most:
1. one same-day official NSE Indices NIFTY 50 OHLC request for 2024-01-02; and
2. one unauthenticated public Dhan compact instrument-master CSV request.

These two requests require a separate manifest/workflow review and PASS before either is made. The new approval must be unique, independently pinned and marked SPENT before the first request. No change to the SPENT Dhan sample approval is allowed. On mismatch, timeout, redirect, overflow or unrecognized schema, no partial bundle or data acceptance may occur.

**Tester → Developer:** Archive this final report byte-for-byte on `phase-07-developer`, update the handoff/status/error/chat/README with the current report blob and exact reviewed hashes, then prepare—but do not execute—the fresh two-source manifest and guarded workflow. Submit that exact manifest/workflow for an independent review. Do not make either public-source request until that second gate passes.
