# Developer Submission — Paper Prediction Replication Extension

**Submitted:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Decision requested:** independent tester review of the source-derived crosswalk and proposed protocol, before any new empirical work.

## Exact submission artifacts

- Crosswalk: [PAPER_PREDICTION_METHOD_CROSSWALK.md](../literature/PAPER_PREDICTION_METHOD_CROSSWALK.md)
- Proposed protocol: [PAPER_REPLICATION_EXTENSION_SPEC.md](../phase7/PAPER_REPLICATION_EXTENSION_SPEC.md)
- Existing registered methods: [METHOD_REGISTRY.md](../METHOD_REGISTRY.md)
- Existing paper inventory / extraction ledger: [UPLOADED_PAPER_METHOD_COVERAGE_AUDIT.md](../literature/UPLOADED_PAPER_METHOD_COVERAGE_AUDIT.md)
- Current phase authorization ledger: [STATUS.md](../STATUS.md)
- Existing negative-result comparator: [Run #44 independent report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_RUN44_TESTER.md)

## What is being requested for review

1. Completeness and fidelity of the 15-PDF methods inventory, including the distinction between prediction methods and option-strategy discussion.
2. Whether paper-derived methods are mapped to the right registry families and whether any proposed new row (notably CCI-derived direction) requires a registry amendment.
3. Correct target/sign/forecast-horizon definitions and separation of regression metrics from direction metrics.
4. Leakage-safe feature availability, feature selection, scaling, tuning and cross-validation.
5. The one global multiplicity scope, dependence-aware resampling and preservation of the final untouched holdout.
6. Whether the planned sequence properly respects the existing Phase 7 data/authorization gate.

## Known boundary conditions

- This is not an empirical result and does not promote any method.
- Current Run #44 results remain unchanged: 12 methods × five horizons, none significant after familywise correction.
- The currently audited NIFTY daily sample is 2020-01-01–2026-10-09 (1,676 rows), so paper-native 5/10/20-year windows are not yet supportable from that artifact.
- The one-row Dhan sample remains quarantined; do not consume its spent approval or fit on that row.
- New source pulls, full-history data collection, model fitting and final holdout access are not authorized by this submission.

**Developer → Tester:** Independently inspect the full PDFs (not just the summaries), compare each candidate and exclusion with `METHOD_REGISTRY.md`, and return a report bound to the current crosswalk/spec commit. Record all corrections before any empirical gate.

**Tester → Developer:** Approve or request changes on the isolated tester branch. If passing, state the exact next permissible action and the exact files/hashes covered.
