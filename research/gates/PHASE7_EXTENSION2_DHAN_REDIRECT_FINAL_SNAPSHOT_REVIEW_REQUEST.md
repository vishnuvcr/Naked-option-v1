# Independent Tester Request — Current Dhan Redirect Probe Snapshot

**Requested decision: review only; no live request is authorized by this request.**

Developer branch head at submission: `2f2d96eea8e44814593efc98c57243d1c2692935`.

Current protected code blobs:
- Adapter `scripts/dhan_market_data_recovery.py`: `266a9abd5677b15e93143a7538308828b2a7f0a3`
- Offline suite `scripts/test_dhan_market_data_recovery.py`: `5c913fbae03de3000de47a039645b6249d2d53e4`
- Redirect validator `scripts/validate_dhan_redirect_probe_approval.py`: please retrieve and record the current exact blob at this branch head.
- Dedicated workflow `.github/workflows/phase-07-dhan-redirect-probe-live.yml`: `88aba6e024e20e74727502bf6b3c1cdeaa5ec71b`
- Offline workflow `.github/workflows/phase-07-dhan-market-data-tests.yml`: unchanged from previously reviewed blob `b43ce4dadca4e5867173136531e71c63bb74e9a3`
- Redirect specification: `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md`, previously reviewed blob `7044afeb8ddc242059490686727a3fe354e87b6d`.

Hosted offline suite [Run 38044495634](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044495634) passed on the code/test snapshot before the final documentation-only updates. A guarded workflow attempt [Run 38044387209](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044387209) passed all offline checks and then failed closed at manifest validation because `research/gates/DHAN_REDIRECT_TARGET_APPROVAL.json` was absent. The source request was skipped. No READY manifest currently exists.

## Required independent checks

1. Verify the actual checked-out blobs for adapter, test suite, validator, both workflows and all pinned tester reports. Do not rely on this request's copied hashes alone.
2. Verify HTTPS-only redirect parsing, actual CR/LF/NUL rejection, 3xx-only Location handling, credential/path/query redaction, strict one-request/1 KiB budget, proper JSON newline and no body/cookie/auth leakage.
3. Verify the manual confirmation input defaults false, offline tests precede manifest check, manifest is spent before source access, and the token is available only to the final one-request probe step.
4. Run/review the hosted offline suite on the exact current code/test blobs. If any check fails, return REQUEST CHANGES with line-specific findings.
5. If and only if every code/workflow gate passes, issue a separate explicit PASS with the exact blob IDs and hosted run. Do not create a manifest or trigger source access as part of this review.

## Scientific boundary

The previously observed Dhan metadata endpoint returned HTTP 302. It has not been followed. No candles/options history were obtained; aggregate FII/FPI/DII flow remains unresolved. No modeling or predictive evaluation is authorized by this code review.

**Tester → Developer:** Independently inspect this exact snapshot and issue a line-specific PASS/REQUEST CHANGES report on the tester branch. No source request until a new manifest is separately approved.

**Developer → Tester:** Check the latest branch content directly, not only this request. Treat every earlier manifest as SPENT and fail closed if any discrepancy exists.
