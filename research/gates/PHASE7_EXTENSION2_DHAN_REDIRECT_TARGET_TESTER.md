# Independent Tester Report — Dhan Redirect Probe Final Snapshot (Manual-Only Trigger)

**Decision: PASS WITH SCOPED RESTRICTIONS — code/workflow only. Live request authorized: NONE.**  
**Reviewed developer commit:** `9bfd1d61c05f8658d5b6165759a735e317740328`.

## Exact reviewed blobs

- Adapter `scripts/dhan_market_data_recovery.py`: `266a9abd5677b15e93143a7538308828b2a7f0a3`
- Offline regression suite `scripts/test_dhan_market_data_recovery.py`: `e22a48bf83e121d5b1e4b64ff17f79e4cbc398dc`
- Redirect manifest validator `scripts/validate_dhan_redirect_probe_approval.py`: `6f349bd29102daeff777c2423df63bd156ef4c64`
- Offline workflow `.github/workflows/phase-07-dhan-market-data-tests.yml`: `b43ce4dadca4e5867173136531e71c63bb74e9a3`
- Dedicated guarded workflow `.github/workflows/phase-07-dhan-redirect-probe-live.yml`: `c8700b6e7bd0160603a71477e31e5291ff58008a`
- Specification `research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md`: `7044afeb8ddc242059490686727a3fe354e87b6d`

## Checks performed

1. HTTPS-only redirect parsing; actual CR/LF/NUL rejection; credential/malformed-host rejection; scheme and normalized hostname only, never raw Location path/query.
2. Location parsing restricted to 3xx responses; provider error bodies are not read/retained; content type is bounded and control-character checked.
3. Dedicated diagnostic requires its own authorization flag and a hard one-request/1 KiB budget; no redirect following or response-body parsing.
4. Manual workflow dispatch requires `confirm_probe=true`, default false. **The automatic `push` trigger has been removed**, because creating a manifest must not silently trigger live access. This removes a gap where a manifest push could bypass the manual confirmation checkbox.
5. Offline tests run before manifest validation. Manifest is validated and marked SPENT before the final source step. Token is injected only into that final diagnostic step.
6. Validator pins the protected files, byte hashes and Git blobs, reviewed-commit ancestry/tree, tester-report digest, one-request/1 KiB budget and explicit denial of full-history/model-fitting authorization.
7. Hosted offline [Run 38044701520](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044701520) passed on this exact developer commit. It exercises the new regression assertions that manifest pushes cannot trigger the live workflow.

## Scope and limitations

This is a code/workflow PASS only; **live request authorized: NONE**. No READY manifest was found on the reviewed developer branch. Previous manifests remain SPENT. Last observed Dhan instrument metadata status is HTTP 302, not a data-availability pass. The redirect has not been followed; no candles/options history were obtained; aggregate FII/FPI/DII flow remains unresolved. No modeling, prediction rerun, strategy test or holdout access is authorized.

**Tester → Developer:** Code/workflow gate passes. If continuing, create a new single-use manifest only after computing exact hashes and Git blobs for the complete protected set and this report. Because the live workflow is now manual-only, creating/pushing the manifest will not trigger a network request; dispatch it only with explicit confirmation after the manifest validator passes.

**Developer → Tester:** Audit any eventual result artifact separately. Any redirect follow or historical-data request requires a new proposal and gate.
