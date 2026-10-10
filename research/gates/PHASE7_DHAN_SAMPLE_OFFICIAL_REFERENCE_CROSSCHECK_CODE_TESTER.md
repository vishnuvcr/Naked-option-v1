# Independent Tester Report — Official NIFTY Sample Cross-Check Exact-Snapshot Review

**Decision: REQUEST CHANGES — no live-source request is authorized.**

**Review date:** 2026-10-10  
**Reviewed branch:** `phase-07-developer`  
**Review scope:** code/workflow snapshot only. No network requests were performed.

## Exact file blobs inspected

| File | Current Git blob SHA |
|---|---|
| `scripts/official_reference_crosscheck.py` | `ef5b507d9c1706b2afd16338db8bec2bd517352d` |
| `scripts/run_official_reference_crosscheck.py` | `ff593638d3f76671215cfe55a5cc1f96859096ea` |
| `scripts/test_official_reference_crosscheck.py` | `2817c41ba25882930ccb0a0fc2d7f77968da67ea` |
| `scripts/test_run_official_reference_crosscheck.py` | `8c02fdef90593f6223a6d1b8bf3248163bf64880` |
| `.github/workflows/phase-07-official-crosscheck-tests.yml` | `b450da4b9ffed8d8e38c8f7383084e1ba987b303` |

## Findings

### Positive

- Scope is bounded to one official NSE Indices NIFTY 50 OHLC lookup for 2024-01-02 and one public Dhan instrument-master CSV lookup.
- No Dhan token or other credentials are forwarded to the public-source hosts.
- The normal runner CLI is offline-only; live mode requires exactly `--live` and `OFFICIAL_CROSSCHECK_AUTHORIZED=1`.
- The implementation includes bounded response sizes/timeouts, redirect/retry prohibitions, source parsers, safe failure codes, and cache creation only after both sources and the exact OHLC comparison pass.
- OHLC is compared exactly to two decimal places. Volume is explicitly not cross-checked by this NSE source response.
- No live authorization manifest is present; the original Dhan sample authorization remains SPENT.

### Blocking evidence gap

The prior hosted 32-test PASS, run [38056916677](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38056916677), is recorded against older adapter/runner/test blobs:
- adapter `0a8c7944885b0b50be3eeedfed0eec6b60260638`
- runner `6d617987f43d9ca41840b3e14ff36521396df4b1`
- adapter tests `148ed4f8fcbdd8fd188b928cb10cf7689fb1d0f2`
- runner tests `4109f5cd0784c975d3cc6e440a19797ea09b0bfc`

All four current blobs listed above differ. Therefore the historical test receipt does not certify the exact current snapshot. This is an evidence gap, not a claim that current code necessarily fails. No current exact-snapshot hosted test receipt was available at review time.

## Required resubmission

1. Run the authoritative offline workflow on the exact current developer snapshot.
2. Record the tested commit SHA, run ID/conclusion, test counts, and protected file blob IDs.
3. Verify the live-workflow/approval validator hashes are included in the protected snapshot and the eventual one-use manifest pins the exact reviewed code, tests, workflow and approval digest.
4. Submit the post-test exact snapshot for a new independent decision. No public-source request, model fitting, prediction rerun, strategy testing, or holdout access before that PASS.

**Tester → Developer:** Fix the stale-snapshot evidence gap and submit a fresh hosted test receipt with exact file hashes.

**Developer → Tester:** Re-review the exact post-test snapshot; keep live acquisition blocked until an explicit fresh PASS.
