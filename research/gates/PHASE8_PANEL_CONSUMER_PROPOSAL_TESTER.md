## Independent Tester Report — Phase 8 panel-consumer proposal

**Decision: PASS WITH SCOPED RESTRICTIONS — proposal only**
**Reviewed:** `research/gates/PHASE8_PANEL_CONSUMER_PROPOSAL.md`

### Findings
- The proposal addresses the central weakness of exact replay: refitting models on a later runner is not equivalent to preserving the forecasts that generated the original aggregate result.
- It correctly keeps Run #654 immutable and requires a separate, explicit Phase 8 manifest amendment rather than silently replacing the frozen artifact.
- It preserves the frozen 1e-9 tolerance, blocks fallback refitting, and requires independent checks of panel completeness, hashes, row keys, labels, timestamps, chronological blocks, and aggregate metrics.
- The Phase 7 panel output change remains subject to a separate code review and post-run artifact audit. Its current in-flight workflow attempts are not accepted as evidence until their relevant gate sequence and outputs are independently reviewed.

### Restrictions
1. This is not authorization to update `PHASE8_FROZEN_INPUT_MANIFEST.json` yet.
2. The new Phase 7 artifact must pass a separate independent audit, including recomputation of every registered metric/family statistic from the saved panel and comparison with the paired aggregate JSON within 1e-9.
3. Verify that family-bootstrap results are reproducible from saved arrays and the frozen block schedule; do not skip or replace family-level multiple-testing inference.
4. Run #654 remains unchanged and the 4,800-cell empirical option grid remains blocked.
5. The implementation must fail closed if the new artifact is incomplete, mismatched, or lacks the required provenance.

### Required next step
Developer may implement the panel consumer and validation tests, then submit a separate tester code review. After that, the new artifact must be built and audited before the manifest amendment can be proposed.