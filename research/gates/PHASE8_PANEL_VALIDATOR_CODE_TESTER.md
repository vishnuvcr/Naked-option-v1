## Independent Tester Code Review — Phase 8 saved-panel validator

**Decision: PASS WITH SCOPED RESTRICTIONS — validator implementation only**
**Reviewed developer commits:** 536d0de5db1f9e32931515a6e6fc963feb17f7d7, 535fb4cb4104b80d000ef193f1bb74f3efc65ec9, 793dca4568f376577faa75f6c08bcf087e15e95a, and regression fixture f41f1e9c9f113d9a4d794fe773aa2e5a716c24c3.

### Findings
- The validator consumes the saved panel columns and does not refit the P01–P10 model predictions.
- It checks the paired aggregate JSON hash, manifest schema/protocol/seed, expected 10 layer/horizon panels, per-panel SHA-256, row count, column schema, panel identity, unique ordered row indices, ordered unique timestamps, contiguous block assignment, and source data hashes.
- It recomputes P01–P10 metric outputs, chronological block diagnostics, and family-bootstrap inference from the saved predictions, then uses the frozen recursive numerical comparison with absolute tolerance 1e-9. The saved P08–P10 regime diagnostic metadata is excluded from recomputation but remains protected by the paired aggregate JSON hash; this limitation must remain explicit.
- The synthetic regression fixture exercises saved-panel metric reconciliation without model refitting.

### Restrictions before workflow integration
1. The regression test must pass in hosted CI before the validator is accepted for use.
2. Verify code-file hashes against the immutable source commit recorded in the artifact manifest, either in the hosted workflow or in the separate artifact audit. The manifest's code hashes must not be accepted merely because they are well-formed strings.
3. The post-run artifact audit must independently check all ten panel row counts, hashes, full metric comparisons and family-level inference. The validator cannot amend the Phase 8 frozen manifest by itself.
4. Do not change the current frozen Run #654 manifest until the new Phase 7 artifact is complete and independently accepted.
5. No empirical option-grid execution, option P&L claim or strategy promotion is authorized by this review.


## Independent Tester Follow-up — Phase 8 saved-panel validator hardening

**Decision: PASS WITH SCOPED RESTRICTIONS — validator code and synthetic tests only**

### Evidence reviewed
- Full ten-panel synthetic artifact validation: workflow run `37912985007`, SUCCESS.
- Immutable Git-commit code-hash verification: workflow run `37913188030`, SUCCESS.
- Synthetic fixture isolation from real Git-commit verification: workflow run `37913169416`, SUCCESS.
- Basic saved-panel aggregation regression: workflow run `37912665449`, SUCCESS.

### Independent review
- The validator checks source-code SHA-256 by retrieving each declared path from the artifact's recorded immutable Git commit, then comparing bytes; malformed or unavailable source paths fail closed.
- The full synthetic artifact test covers all ten registered layer/horizon cells and validates the validator's output contract. Its test-only bypass for immutable code verification is isolated to synthetic fixture construction; the separate commit-hash test exercises actual Git object retrieval and tamper rejection.
- The saved-panel metric comparison retains the frozen (10^{-9}) tolerance and recomputes method metrics, chronological-block diagnostics, and family-level inference from saved arrays rather than re-fitting forecasts.

### Restrictions
1. This is code/test approval only. No real Phase 7 reference artifact has yet been independently accepted.
2. The actual artifact audit must verify source hashes against the data available in the audited checkout, code hashes against the exact manifest commit, ten panel hashes/schema/row counts, all registered aggregate metrics and family-level statistics.
3. Confirm P08–P10 regime diagnostic metadata remains intact in the paired aggregate JSON; the current consumer does not independently regenerate that metadata.
4. Do not amend the frozen Phase 8 manifest or launch the 4,800-cell option grid until the new Phase 7 artifact is complete and a separate artifact audit passes.


## Independent Tester Follow-up — exact-commit metric implementation

**Decision: PASS WITH SCOPED RESTRICTIONS — source-version integrity correction**

- Hosted validator regression run `37913662777` completed SUCCESS.
- The Phase 7 and Phase 8 `scripts/run_phase7_ensemble.py` files were independently confirmed to differ, so importing the Phase 8 working-tree module after checking hashes for the Phase 7 commit was not acceptable.
- The correction now loads and executes the exact Phase 7 module bytes from the immutable commit named in the manifest, after checking declared source hashes. The Phase 8 reconstruction checkout fetches full history so the Git source commit is available.
- Regression verifies the exact-commit module can be loaded and the hash verifier rejects tampered hashes. Full synthetic artifact validation still passes with its code-loader bypass isolated to synthetic fixtures.

**Restrictions remain:** This is code/test approval only. The actual Phase 7 artifact must pass a distinct post-run audit for all ten panels, hashes, source files, immutable code commit, all metrics/family inference, and paired aggregate integrity. The consumer must preserve P08–P10 regime diagnostics in the aggregate JSON. No Phase 8 frozen-manifest amendment or 4,800-cell option grid is authorized by this report.


## Independent Tester Follow-up — source-data alignment validation

**Decision: PASS WITH SCOPED RESTRICTIONS — source alignment code/test**

- Hosted regression run `37914065821` completed SUCCESS.
- The validator now independently recomputes daily labels/future returns and intraday labels/future returns from the hashed source data using the exact Phase 7/6/3 implementation versions recorded in the manifest. It also checks source-derived decision timestamps and row counts.
- Regression tests exercise daily and intraday alignment and verify that a deliberately mutated label or future return is rejected. The full synthetic artifact test isolates source loading/alignment only for its synthetic fixture and still passes.
- This closes the identified label/return provenance gap for the tested code path. It does not accept any real artifact. Actual post-run audit must still validate the downloaded Phase 7 artifact, all ten panels, all hashes and aggregate/family statistics before the Phase 8 manifest can change. No option-grid execution is authorized.


## Independent Tester Follow-up — manifest and panel identity hardening

**Decision: PASS WITH SCOPED RESTRICTIONS — hosted regression run `37914278229` SUCCESS.**

- Validator now requires the exact declared daily/intraday source entries and the four expected code-file fingerprints; extra/missing entries fail closed.
- Each panel must identify the same run ID and commit as the manifest, in addition to matching layer, horizon, row count, schema and SHA-256.
- The dedicated hosted synthetic validator regression passed with these checks enabled. This remains a synthetic code-path pass, not acceptance of a real artifact.
- Actual artifact audit must still verify all ten panels, source-derived labels/returns/timestamps, code hashes, aggregate metrics and family-level inference. The Phase 8 manifest and 4,800-cell grid remain blocked until that audit passes.
