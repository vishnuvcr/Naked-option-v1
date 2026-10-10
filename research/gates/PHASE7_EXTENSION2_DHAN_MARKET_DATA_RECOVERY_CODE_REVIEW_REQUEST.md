# Developer → Tester Review Request — Dhan Diagnostic Retry (Final Exact Snapshot)

**Requested decision: PASS / REQUEST CHANGES for one bounded diagnostic retry only.**  
**Reviewed developer commit:** `128c6cd4b62a2d3b7e7bb5e67483085e3628cc26`.  
**Current previous-sample disposition:** REQUEST CHANGES; old manifest is SPENT.

## Exact protected files and Git blob IDs

| File | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` | `f87e8ecaec0a26947438131fef466aae3e57d824` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md` | `9db93dfb56e309dcccf549e51da09004e5f4b276` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md` | `f2310d6f8802141c452cb8b83b15c35c25e19bc1` |
| `scripts/dhan_market_data_recovery.py` | `c88669880eb27b8d7089a1545f8f7d72e16431a6` |
| `scripts/test_dhan_market_data_recovery.py` | `135450d859ded4c46405c5773f949cbecbcaf5e9` |
| `scripts/validate_dhan_sample_approval.py` | `30a0fb07f7d1c492c712844c121116a9af3ab5ca` |
| `.github/workflows/phase-07-dhan-market-data-tests.yml` | `b43ce4dadca4e5867173136531e71c63bb74e9a3` |
| `.github/workflows/phase-07-dhan-market-data-live.yml` | `aa37cec66d46f3c181a7bda213226991c045b189` |

## Hosted evidence

[Run 38043456200](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043456200) passed **29/29 offline regressions** on the reviewed code snapshot. This includes a mocked 403 response from the instrument metadata endpoint; the test verifies only the numeric status and safe content-type survive, while the provider body, cookies, authorization values and token do not.

## Corrections included

- The first live sample stopped at the instrument metadata endpoint after two requests. The artifact omitted the HTTP status and was rejected independently.
- The adapter now includes numeric status, safe content-type, request count and bytes read on metadata failure.
- The validator now compares protected file Git blob IDs against the reviewed commit tree as well as current HEAD, excluding only the code-tester report from reviewed-tree comparison because that report must post-date the commit it reviews; its current byte SHA-256 is separately pinned.
- The single-run manifest is consumed before source access. A second workflow run sees SPENT and must fail closed.
- The prior manifest remains SPENT and cannot be reused.

## Requested independent checks

1. Verify the updated diagnostic and redaction tests.
2. Verify exact blobs and reviewed commit tree binding.
3. Confirm a new manifest can authorize only one bounded diagnostic retry, not an alternate endpoint or broad range.
4. Confirm a non-200 instrument response stops the run before historical candles; it must record the status and safe content-type.
5. Keep full-history acquisition, feature/label construction, model fitting, metrics/p-values, option strategy evaluation and final-holdout access unauthorized.

**Tester → Developer:** PASS or REQUEST CHANGES for this exact snapshot. If passing, a new one-run diagnostic manifest may be prepared after byte hashes are pinned.

**Developer → Tester:** Verify the new manifest before the retry and audit the resulting artifact separately. If the endpoint remains blocked, stop and retain the flow-data gap.
