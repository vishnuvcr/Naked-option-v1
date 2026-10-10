# Developer → Tester Review Request — Dhan Diagnostic Retry Snapshot

**Requested decision: PASS / REQUEST CHANGES for one bounded diagnostic retry only.**  
**Reviewed developer commit:** `7fb5b856f936ba5a95c4d249ca316651f66615e3`.  
**Current artifact decision:** prior sample REQUEST CHANGES; its manifest is SPENT. No new manifest exists yet.

## Exact files and Git blob IDs

| File | Git blob ID |
|---|---|
| `research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md` | `f87e8ecaec0a26947438131fef466aae3e57d824` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md` | `9db93dfb56e309dcccf549e51da09004e5f4b276` |
| `research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md` | `89d44fcf281df0478ba8f030163f1cca52855b88` |
| `scripts/dhan_market_data_recovery.py` | `e47e500f0d15e117e0078a9c98badd96bf62499f` |
| `scripts/test_dhan_market_data_recovery.py` | `22a366342432908aaa231a7e04ddd25825e39ce0` |
| `scripts/validate_dhan_sample_approval.py` | `3c99140a5488cd58ee3bed9c21cd659183adbdf2` |
| `.github/workflows/phase-07-dhan-market-data-tests.yml` | `b43ce4dadca4e5867173136531e71c63bb74e9a3` |
| `.github/workflows/phase-07-dhan-market-data-live.yml` | `aa37cec66d46f3c181a7bda213226991c045b189` |

## New evidence and correction

- Previous sample [Run 38043148580](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043148580) stopped after two requests at `/v2/instrument/IDX_I`, before candle requests.
- Artifact [sample audit](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_SAMPLE_AUDIT.md) is REQUEST CHANGES; artifact ZIP SHA-256 `45f2b23a0835cb6b1af52ac12913bf86062f9c82a0d3edcef4c810a3f30f38d9`.
- Adapter now reports only the numeric instrument-metadata HTTP status, profile boolean summary and request/byte counts when metadata returns non-200. It does not include provider error body or token.
- Offline run [38043259438](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043259438) passed **28/28 checks**.

## Requested independent review

Confirm the updated diagnostic report does not expose secrets and retains the HTTP status needed to diagnose the instrument endpoint. Verify exact blobs and existing workflow/manifest protections. If passing, permit a fresh manifest for one bounded diagnostic retry only. The retry must stop if metadata remains non-200; no alternate endpoint, wider range, retries, full-history acquisition, features/labels, modeling or holdout access.

**Tester → Developer:** Independently review the corrected snapshot. The prior manifest is spent and cannot be reused.

**Developer → Tester:** Only after PASS, create a new manifest with exact byte hashes, Git blobs, report digest and reviewed-commit ancestry. The resulting artifact requires separate audit.
