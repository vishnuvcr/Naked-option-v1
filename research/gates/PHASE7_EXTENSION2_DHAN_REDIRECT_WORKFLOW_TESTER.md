# Independent Tester Report — Dhan Redirect Probe Workflow/Manifest Gate

**Decision: REQUEST CHANGES — no live request authorized.**  
**Reviewed developer commit:** `6cdef779c3bd1285d159f7d86dc5502c0d36b8db`.  
**Current independent role:** tester branch only; this report does not edit developer source.

## Exact snapshot reviewed

- Adapter `scripts/dhan_market_data_recovery.py`: blob `9ac22992f7e4c8fd7def03ed14c19549c3716f4f`
- Offline tests `scripts/test_dhan_market_data_recovery.py`: blob `8a2428e9ab35c0a68c259083ed7031ddee84f38c`
- Probe validator `scripts/validate_dhan_redirect_probe_approval.py`: blob `84afcb5bfb168686c2ad5fa11d833a51b42cfca1`
- Probe workflow `.github/workflows/phase-07-dhan-redirect-probe-live.yml`: blob `d74fdcde3fefc8050c6a9db7f618c1076d4b4531`
- Offline workflow `.github/workflows/phase-07-dhan-market-data-tests.yml`: blob `b43ce4dadca4e5867173136531e71c63bb74e9a3`
- Redirect-target specification: blob `7044afeb8ddc242059490686727a3fe354e87b6d`
- Specification decision: [redirect-target tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_TESTER.md)

## Blocking findings

1. **The parser accepts insecure HTTP.** `safe_redirect_target` currently accepts both `http` and `https`, but the reviewed specification explicitly requires HTTPS. An HTTP Location must return `REDIRECT_TARGET_UNPARSEABLE`. Add a dedicated offline regression.
2. **Control-character checks are incorrectly escaped.** The source checks the two-character strings `\\r`, `\\n`, and `\\x00` rather than actual CR, LF and NUL characters. Change the checks to test actual control characters and add tests for those inputs.
3. **Redirect parsing is not limited to 3xx.** The `HTTPError` branch currently attempts to parse any Location header, regardless of status. Only inspect Location when the numeric status is 300–399; an error such as 401 with a Location header must not produce redirect-target fields.
4. **The runtime budget is not enforced at the probe-specific limit.** `redirect_target_probe` constructs the general `Budget()` (six requests / 4 MiB); it passes a 1 KiB per-response cap but does not make the global request/byte budget fail closed at one request/1 KiB. Add configurable limits or a dedicated budget so any second request or >1 KiB total read is rejected.
5. **The hosted offline suite is currently red.** Run [38044013621](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38044013621) fails before running tests because `scripts/test_dhan_market_data_recovery.py` has a `SyntaxError: unexpected character after line continuation character` at line 431. Fix the malformed assertion quoting and rerun the suite.
6. Keep the dedicated workflow as the only live path: it must run offline tests, validate the exact redirect-probe manifest, spend it before source access, and inject `DHAN_ACCESS_TOKEN` only into the one-request probe step. The two prior Dhan manifests remain SPENT and cannot be reused.

## Scope and decision

The dedicated workflow/validator structure is directionally appropriate: it has a manual confirmation input, validates and spends a separate manifest, and only then runs the probe. It is **not safe to issue or prepare a READY manifest for live use** until all findings above are corrected and a new independent exact-snapshot gate passes.

No source request, redirect follow, candle request, full-history pull, model fit, predictive metric, option strategy test or holdout access is authorized by this review.

**Tester → Developer:** Correct the HTTPS/control-character parsing, status-gate Location extraction, enforce hard one-request/1 KiB limits, fix the syntax error, and submit updated exact blobs plus a successful hosted offline run for a fresh independent gate.

**Developer → Tester:** Re-review the exact corrected parser, tests, validator and workflow together. Do not permit a manifest or source call while any finding remains open.
