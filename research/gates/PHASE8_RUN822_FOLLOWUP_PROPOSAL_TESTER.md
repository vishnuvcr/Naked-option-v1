# Independent Tester Report — Phase 8 Run #822 follow-up proposal

**Decision: PASS WITH SCOPED RESTRICTIONS — protocol amendment proposal only**  
**Reviewed proposal:** `research/gates/PHASE8_RUN822_FOLLOWUP_PROPOSAL.md`  
**Developer proposal commit:** `d316da04e301977e62c6ee2c1fcba2602e608326`

## Independent findings

1. The mismatch has persisted after Python 3.11.16 pinning and single-thread BLAS/OpenMP controls. This does not prove runner-image variation is the cause; the proposal appropriately labels that explanation unproven.
2. Run #654's published artifact is an aggregate JSON, not a row-level prediction archive. Therefore, a later environment cannot independently verify each historical P07 prediction from the immutable artifact alone.
3. The reported Hugging Face revision and normalized source SHA-256 match between Run #654 and Run #807, and the checked Phase 3/6 dependency source blobs match. This reduces (but does not eliminate every possible input-path concern) the likelihood that the known mismatch is caused by a changed intraday source file.
4. The proposal correctly preserves Run #654 as immutable and requires a new, versioned artifact plus explicit manifest amendment. It does not authorize changing the reference values, relaxing the 1e-9 tolerance, promoting a strategy, or executing the 4,800-cell grid.

## Authorized scope

The developer may implement **artifact-contract and reproducibility infrastructure only**:
- Save row-level predictions, labels, future returns, timestamps, block identity, source hashes and runtime fingerprint from the same Phase 7 execution as the aggregate JSON.
- Add tests for completeness, stable row keys, deterministic serialization, hash verification, and exact aggregation from the saved panel.
- Submit the Phase 7 output-code change for a separate tester code review before running it.
- After a new artifact passes a separate empirical-artifact audit, propose the Phase 8 frozen-manifest amendment for another independent review.

## Restrictions

- This report is not approval for Phase 7 empirical execution; a separate code gate and workflow gate are mandatory.
- This report is not approval to amend the Phase 8 frozen manifest yet.
- Run #654 remains unchanged and historically valid only under its existing scoped restrictions.
- Run #822 diagnostics, if/when uploaded, must be retained as failure evidence and reviewed separately.
- Empirical option execution remains **BLOCKED**. No strategy selection, P&L claim, or 4,800-cell grid authorization is granted.
- Do not infer that runner-image drift is the root cause unless the collected fingerprint and follow-up evidence establish it.

## Required next submission

Developer must submit the Phase 7 row-level artifact implementation and tests for a distinct tester code review. The tester must independently verify that the added panel is generated from the same arrays used to compute the aggregate results and that the new output does not alter any frozen method, label, horizon, metric, seed, or statistical procedure.
