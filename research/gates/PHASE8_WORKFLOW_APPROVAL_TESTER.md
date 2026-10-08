# Phase 8 Workflow — Independent Tester Gate

## Status
**PASS WITH SCOPED RESTRICTIONS — workflow verification authorized**

Reviewed current phase-08-developer `.github/workflows/phase-08-long-option.yml` and the corresponding `research-protocol.yml` phase-8 detector/caller.

Checks passed:
- reusable workflow supports automatic caller execution and manual `workflow_dispatch`;
- protocol, regression, artifact, source audit and reconstruction are prerequisites to the empirical job;
- Run #654 artifact ID and SHA-256 are frozen and checked before reconstruction;
- cached artifact restoration is used before download, with digest verification after download;
- free-source audit runs before any empirical option P&L;
- reconstruction is required before empirical execution;
- empirical authorization is fail-closed and requires an explicit `STATUS: AUTHORIZED` file;
- no empirical authorization file is currently present, so the current workflow cannot start the 4,800-cell grid accidentally;
- manual run with `empirical_authorized=false` remains suitable for engineering verification;
- the 4,800-cell runner is explicitly absent/fail-closed until separately authorized.

## Scoped restriction
The default `main` branch must register both the Phase 8 reusable workflow and the Phase 8 Research Protocol caller block before relying on the manual workflow control from the repository default branch.

**Tester → Developer:** archive this workflow gate, register the Phase 8 workflow/caller on `main`, then trigger an engineering-only Phase 8 run with empirical authorization false. Submit the hosted regression/source/reconstruction evidence for the next tester gate. Do not create empirical authorization or run option P&L.
