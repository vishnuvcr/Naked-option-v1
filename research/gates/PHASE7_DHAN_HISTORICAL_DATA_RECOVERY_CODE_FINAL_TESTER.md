# Independent Tester Final Report — Dhan Historical Pipeline Code Gate

**Decision: PASS WITH SCOPED RESTRICTIONS — offline code only; preparation of a fresh one-use manifest may proceed. No live request is authorized by this report.**

**Exact reviewed code commit:** `986d78cf4e3297f203c4960493ef86e2a8663697`  
**Current developer branch head at re-check:** `49f8e3401ed88d01665dd162d175ebfb06da4c6b`  
**Hosted offline regression:** [Run 38050266592](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050266592), success; **42/42 offline/mock tests passed**.  
**Hosted protocol check:** [Run 38050266689](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38050266689), success.

## Exact blobs verified at the reviewed commit

| File | Git blob SHA |
|---|---|
| `scripts/dhan_history_pipeline.py` | `84e30b0d45ffb2a9b6985601b934c66db435b201` |
| `scripts/test_dhan_history_pipeline.py` | `e58ffd6d4b4daf8e049c0be0c2edca44dc16a161` |
| `.github/workflows/phase-07-dhan-history-pipeline-tests.yml` | `dc0de4688bfac5ee932c32ccd25fdd586effd3c2` |
| `research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md` | `9145f88ec99169a900d9ff2c7b77c0592781f5ae` |
| Developer exact-snapshot handoff blob | `e826059ee328e6c0e1de9a4494540bfa8d6b1308` |
| Prior tester report for findings 1–5 | `e9c9d3f59f7e267ed317b250df529c03c5f9598d` |
| Prior tester report for finding 6 | `16249983e2ba71474f80070f61c60ae2675781a3` |

The current developer branch has moved forward for documentation/status logging after the reviewed code commit, but the source, test and workflow blobs listed above still match the exact reviewed commit. No source/test/workflow changes were found after the tested snapshot.

## Final resolution of independent findings

The prior REQUEST CHANGES reports are retained as historical review records. The current snapshot resolves all six findings:

1. **Exclusive-end dates:** Dhan's official historical data docs specify daily `toDate` as non-inclusive, and its expired-options docs do the same. Daily/rolling date caps use exclusive duration, and cache time-range verification rejects rows whose local date equals or exceeds `toDate`. The tests cover exact 30-/365-day windows and end-date exclusion.
2. **Hard budgets:** `RequestBudget` cannot widen the one-request and 8 MiB total budget through constructor settings or mutation without rejection before an opener is created. The request path revalidates budget state.
3. **Optional numeric fields:** Present known numeric arrays, including daily `open_interest`, are checked for list shape, alignment, numeric type, finite values and non-negativity.
4. **Rolling-option optional arrays:** Dhan's published response example shows empty arrays for unrequested optional IV/OI/strike/spot fields. The parser permits those only when not requested; requested arrays must align, and populated optional arrays are checked.
5. **Strike handling:** This initial sample-gate implementation accepts ATM only. Other strike offsets are rejected until their instrument/expiry-specific bounds are implemented and independently reviewed.
6. **Cache provenance:** The cache boundary requires an integer HTTP status of 200, JSON content type, exactly one request, cumulative bytes equal to the raw response length and under the global budget, matching raw-response SHA-256/byte count, recomputed schema validation, valid request parameters and response timestamps within the requested window. Tests cover missing/bad metadata and verify rejected writes leave the cache directory empty.

## Workflow and security checks

- The reviewed workflow has `contents: read`, no Dhan secret environment and no live-network step. It runs only the offline/mock test file and offline CLI.
- The CLI reports `network_enabled=false`.
- The request helper permits only the three documented exact HTTPS Dhan history endpoints and POST; it rejects unknown request keys, requires literal boolean `live_authorized=True`, checks the token's basic format, uses a redirect-rejecting opener, does not read provider error bodies, and applies timeout/byte/request/pacing bounds.
- No actual Dhan request, credential use, market-data cache creation, feature engineering, predictor rerun, option strategy test or holdout access occurred.

## Remaining limitations — outside this code gate

- The official source responses have not yet been observed. Token/Data API entitlement, real candle response schema, row coverage, trading-session completeness, historical continuity, quotas and data-quality overlap remain unverified.
- Dhan's expired-options docs state a 30-day cap and non-inclusive end date, while the example date span differs by 31 calendar dates. The adapter follows the conservative documented 30-day duration pending a separately authorized feasibility check.
- The intraday endpoint's end-boundary semantics remain unresolved in docs and must be checked against an observed response before claiming complete intraday coverage.
- A pass here does not validate the security-ID mapping or prove that any data improves prediction.

## Decision and allowed next step

**PASS WITH SCOPED RESTRICTIONS.** The offline implementation and current regression suite are acceptable for code-gate purposes.

The developer may now prepare a new exact-hash, single-use authorization manifest and a separate manually dispatchable guarded workflow for **one tiny daily NIFTY index-history request only**. The manifest must pin the reviewed code commit and protected source/test/workflow/proposal/review blobs, be checked independently, and be spent before the request. The prior redirect manifest remains SPENT and may not be reused.

**Not authorized:** any live request until that separate manifest/workflow gate is passed; bulk history; intraday history; rolling-option history; other Dhan endpoints; feature fitting; predictor rerun; option strategy testing; final-holdout access.

**Tester → Developer:** Prepare the fresh single-use manifest and a separately guarded workflow for only one tiny daily NIFTY index-history request. Submit that exact manifest/workflow snapshot for independent review before any API call. Keep automated workflows and logs fail-closed; do not start bulk acquisition or modeling.
