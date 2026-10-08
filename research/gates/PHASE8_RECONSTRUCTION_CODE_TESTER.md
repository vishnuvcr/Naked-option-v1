# Phase 8 Reconstruction/Data Implementation — Independent Tester Gate

**Developer branch reviewed:** `phase-08-developer`  
**Status: PASS WITH SCOPED RESTRICTIONS**  
**Empirical option execution:** NOT YET AUTHORIZED

## Reviewed implementation

- `scripts/reconstruct_phase7_predictions.py`
- `scripts/test_phase8_reconstruction.py`
- `scripts/audit_phase8_option_sources.py`
- `data/reference/phase8_cost_schedule.json`
- `research/phase8/PHASE8_FROZEN_INPUT_MANIFEST.json`

## Independent checks

### Phase 7 forecast reconstruction

1. The reconstruction uses the exact frozen Run #654 Phase 7 implementation through the inherited `run_phase7_ensemble.py` module rather than reimplementing the P01-P10 formulas independently.
2. The exact accepted Run #654 developer commit is frozen as `4f1d695f291ed32996c07f01710afcecc6f2a540`.
3. The exact Git blob SHA of `scripts/run_phase7_ensemble.py` at that commit is frozen as `399ad338a409b6faf56c3ee243f2643cc89f162a`.
4. The reconstruction now verifies the current checked-out Phase 7 source against both identifiers before generating predictions.
5. It reconstructs all 100 layer/horizon/candidate aggregate cells and compares the complete nested result objects with a fixed absolute tolerance of 1e-9 for continuous values and exact equality for counts/strings/nulls.
6. P05/P06 masking, chronological diagnostics, P08-P10 regime diagnostics and the family moving-block bootstrap are reused from the accepted Phase 7 implementation.
7. The prediction panel is emitted separately for every one of the ten horizons/candidates per layer and SHA-256 hashed.
8. Future labels/returns are retained for audit but are not used by the reconstruction to choose option contracts.

### Frozen-data protections

The Phase 7 aggregate reference is explicitly bound to Run #654 artifact ID `11551679532` and SHA-256 `c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a`.

The repository manifest explicitly sets `empirical_option_execution_authorized=false`, so a successful reconstruction alone cannot authorize option P&L.

### Cost schedule

The cost schedule is directionally consistent with the registered official sources and the frozen specification:

- current Paytm Money: ₹10 per executed F&O order;
- historical Paytm tariff not independently verified: fixed ₹20/order fallback;
- STT: 0.10% through 31 March 2026 and 0.15% from 1 April 2026 in the current NSE schedule;
- NSE option transaction charge: 35.03/lakh per side from 1 October 2024 through 28 February 2026, and ₹3,552/crore per side from 1 March 2026;
- NSE IPFT: ₹50/crore per side in the 2024–February 2026 period and ₹0.01/crore per side from March 2026;
- SEBI 0.0001%, equity-option stamp duty 0.003% buyer, GST 18%.

### Source-first controls

The source audit checks official NSE, BSE, Hugging Face and the open GitHub option-data engines before any large download. It does not silently mark a failed source as accepted.

## Scoped restrictions

1. Pre-1 October 2024 NSE equity-option transaction charges were member-level/slab-based; the repository intentionally uses a conservative fixed fallback rather than a result-dependent or favorable slab reconstruction. This must remain visibly tagged `CONSERVATIVE_FALLBACK`.
2. Only validated bid/ask history may later produce a **quote-executable** result; OHLC/proxy rows stay non-quote-executable.
3. The current Paytm ₹10 figure may not be back-applied to historical dates without a verified effective-date tariff.
4. The workflow gate must independently verify the Run #654 artifact digest before reconstruction. This is a workflow requirement, not a scientific method change.

## Gate decision

**PASS WITH SCOPED RESTRICTIONS.**

The implementation is approved for the next engineering gate: data/cache acquisition, artifact-digest verification, reconstruction execution and execution-engine regression. No empirical option P&L may be generated until the workflow/data gate and the independent tester approval of that gate are recorded.

**Tester → Developer:** build the Phase 8 GitHub Actions workflow, verify the Run #654 artifact digest before reconstruction, run the free-source audit with cache restoration, and add a separate execution-engine regression suite. Submit those as the next gate. Do not run the 4,800-cell option P&L yet.
