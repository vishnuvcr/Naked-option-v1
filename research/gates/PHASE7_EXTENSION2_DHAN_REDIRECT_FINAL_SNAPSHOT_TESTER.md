# Independent Tester Report — Dhan Redirect Probe Final Snapshot

**Decision: PASS WITH SCOPED RESTRICTIONS — code/workflow only. Live request authorized: NONE.**  
**Reviewed developer commit:** `552b46b32e558d0b61841bfa167da1a5c14d46e8`.

## Exact reviewed blobs

- Adapter `scripts/dhan_market_data_recovery.py`: `266a9abd5677b15e93143a7538308828b2a7f0a3`
- Offline regression suite `scripts/test_dhan_market_data_recovery.py`: `1319f93aa39fb9908f285aef0d428ed15c6d8a7d`
- Redirect manifest validator `scripts/validate_dhan_redirect_probe_approval.py`: `6f349bd29102daeff777c2423df63bd156ef4c64`
- Offline workflow `.github/workflows/phase-07-dhan-market-data-tests.yml`: `b43ce4dadca4e5867173136531e71c63bb74e9a3`
- Dedicated guarded workflow `.github/workflows/phase-07-dhan-redirect-probe-live.yml`: `88aba6e024e20e74727502bf6b3c1cdeaa5ec71b`
- Specification `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md`: `7044afeb8ddc242059490686727a3fe354e87b6d`

## Checks performed

1. Parser requires HTTPS; rejects actual CR, LF and NUL; rejects credential-bearing, malformed, or hostless targets; only emits normalized scheme and hostname, never raw Location path/query.
2. HTTPError Location is parsed only for 3xx. Provider error bodies are not read or retained. Content-Type is length/control-character bounded.
3. Redirect probe requires its own authorization flag and uses `Budget(request_limit=1, byte_limit=1024)`; it does not parse response content or follow the redirect.
4. Dedicated workflow requires `confirm_probe=true` for manual dispatch (default false), runs offline tests before manifest validation, spends the manifest before source access, and exposes `DHAN_ACCESS_TOKEN` only to the final one-request step.
5. Validator pins the protected file set, file SHA-256 and Git blob IDs; requires reviewed-commit ancestry and matching protected blobs in the reviewed commit tree; checks tester-report digest, one-request/1 KiB scope and explicitly forbids full-history/model-fitting authorization.
6. Added workflow regression assertions are present in the reviewed suite. Hosted offline [Run 38044643585](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044643585) passed on the exact reviewed commit: all 38 Dhan offline regressions succeeded.

## Scope and limitations

This is a code/workflow PASS only. No live request is authorized by this report. No READY manifest was found in the reviewed developer branch; the previous guarded attempt correctly failed closed and skipped source access. Existing manifests remain SPENT. The Dhan instrument endpoint's last observed status remains HTTP 302, not a data-availability pass. The redirect has not been followed; no candle/option history was acquired; aggregate FII/FPI/DII flow remains unresolved. No modeling, prediction rerun, strategy test or holdout access is authorized.

**Tester → Developer:** This exact-snapshot code/workflow gate passes. If you choose to proceed, create a separate one-use manifest only after computing current byte hashes and Git blobs for every protected file and this tester report. Run the guarded workflow only after the validator confirms all pins. Do not follow the redirect or fetch candles/history under this approval.

**Developer → Tester:** Independently audit any resulting artifact and return a new report. Any request to follow the redirect or obtain historical data requires a separate scope proposal and gate.
