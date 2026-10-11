# Tester Review — MR-0 to MR-5 Feasibility Runner R6

**Date:** 2026-10-11  
**Verdict:** REQUEST_CHANGES — synthetic suite passes; real-data audit remains unauthorized  
**Reviewed developer commit:** `052e8afe1cb590a3aa43145bea254ee742aade26`

## Exact reviewed blobs

- Runner: `647caf57a0d3892062039b9e33f9b67d475c0778`
- Tests: `b99efb9e7a82c78d900486f2b5786d795a864009`
- Report schema: `c7e34cdd134a741eeb1235236b492acd04ebf524`
- Synthetic workflow: `c47fad18419fadeeb08d3d26a88789c3ba245786`

## Verification

- Hosted synthetic Actions run [38152966001](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38152966001) succeeded. The 13-test regression suite, CLI self-test, and workflow boundary checks all passed.
- The run was synthetic-only. It did not read the composite dataset, fit or score a model, access holdout observations, or execute strategy/P&L logic.
- Prior CI defects were reproduced from logs and corrected: a stale feature-family fixture, date/string comparison in horizon labeling, and self-referential workflow assertions. Earlier failed runs are not retroactively treated as passes.

## Remaining blocking findings

1. **Split purge and minimum sample-size evidence is asserted, not independently verified.** `validate_input_manifests` trusts booleans such as `train_label_endpoint_purge_verified` and claimed origin counts in a JSON manifest. The scan does not independently recompute train/validation label endpoints, enforce that every training label endpoint is at or before the train boundary, enforce that every validation endpoint is at or before the validation boundary, or prove the 252/250 minimum counts from the scanned observations. A stale or inaccurate manifest could therefore pass the gate.

2. **Reported target counts are pooled across train and validation.** The current `target_horizons` counts use all pre-holdout sessions and the report sets `split_status=PASS` after manifest validation. It does not report per-split counts or demonstrate common validation-origin eligibility across all horizons. The gate needs per-split target counts and a computed validation intersection, or it must mark split/target feasibility `NOT_ESTIMABLE`.

3. **Target construction still depends on an external assertion.** The code selects the latest valid SPOT bar per session as the daily close. The manifest's `official_close_linkage_proven=true` flag is not accompanied by an independently checked evidence record tied to a pinned source or mapping. The code must require and validate the evidence structure, or retain target status as `NOT_ESTIMABLE` until that evidence is separately verified.

## What is now acceptable

- The exact-run/attempt binding and exclusive workspace marker fail closed for replay within one job and for Actions reruns.
- The report schema rejects unknown nested fields and validates nested target/family structures.
- The prefix reader verifies the byte offset is within the file and ends at a newline before parsing only that prefix.
- Blocked reports no longer claim cleanup ran; fixed family names are allowlisted.
- Workflow permissions are read-only and the workflow is synthetic-only with a manual dispatch trigger.

## Required developer resubmission

Implement the three remaining blockers, add synthetic regressions for split-boundary crossing and the 252/250 computed-origin rules, rerun the hosted synthetic workflow, and submit a fresh exact-hash snapshot. Do not run the real dataset while this decision is current. The separate PPR-4 audit still records no machine-readable holdout boundary, which is independently sufficient to keep empirical execution blocked.

**Tester → Developer:** Correct findings 1–3 and resubmit an immutable exact-hash snapshot.  
**Developer → Tester:** Keep the real-data gate closed until fresh exact-hash review passes and valid boundary/provenance manifests exist.
