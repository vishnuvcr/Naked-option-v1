# Phase 8 Run #746 — Tester Request Changes

## Finding
Hosted engineering run 746 (`37815192558`) passed protocol, workflow-contract regression and the complete free-source audit, but the reconstruction regression failed before execution-engine tests.

Failure: `scripts/test_phase8_reconstruction.py` executes `reconstruct_phase7_predictions.py` via `exec()` without supplying `__file__`; production module line 16 evaluates `Path(__file__)` and raises `NameError`.

## Disposition
**NON-EVIDENCE — test-harness defect only.** No option P&L was generated. Empirical authorization remained false and all empirical jobs were skipped.

## Required correction
Add a deterministic `__file__` value to the reconstruction regression execution namespace, matching the established Phase 7 test-harness pattern. Add a regression assertion that the namespace includes the expected module path. Do not change reconstruction logic, tolerance, Run #654 binding, or any execution/cost definition.

**Tester → Developer:** correct only the reconstruction test harness, record this error, obtain a fresh tester recheck, then rerun the engineering gate. Do not generate empirical option P&L.
