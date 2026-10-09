# Independent Tester Report — Phase 7 correction snapshot binding

**Decision: PASS WITH SCOPED RESTRICTIONS**  
**Reviewed developer commit:** `ccb063fb414db971c9a43ed0e0cd85ef9d3c4c4f`  
**Scope:** correction-specific authorization safety only; approval permits one fresh Phase 7 empirical execution against the exact protected snapshot, not strategy promotion.

## Independent findings

1. **Snapshot binding is fail-closed.** The validator checks the reviewed developer SHA format and ancestry, the approval decision/scope, the exact protected-file path set and SHA-256 values, byte-identical copies of this report and its JSON manifest on the isolated tester/developer branches, and the report digest recorded in the manifest. Errors or missing files deny authorization.
2. **Regression coverage addresses stale-approval bypass.** The tests cover a matching synthetic snapshot, protected-file mutation, a changed tester-branch copy, a non-ancestor reviewed commit, and an incomplete protected-file manifest. The workflow-contract test verifies that both the automatic protocol caller and reusable/manual execution workflow invoke the snapshot validator.
3. **Fresh hosted engineering evidence passed.** Research Protocol Check [#990](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37953853119), commit `ccb063fb414db971c9a43ed0e0cd85ef9d3c4c4f`, passed the protocol, Phase 7 regression, correction-approval regression, and reference-artifact regression. Authorization and empirical jobs were skipped because the report/manifest had not yet been installed; this is the correct fail-closed behavior.
4. **The latest fixture repair is scoped correctly.** The difference from the prior failed checkpoint changes the test expectation from a bare filename to the exact repository-relative protected path `research/gates/PHASE7_REFERENCE_ARTIFACT_CODE_TESTER.md`. It does not change forecasting logic, labels, model candidates, hyperparameters, thresholds, metrics, or the scientific protocol.
5. **Protected snapshot recorded separately.** The companion manifest contains SHA-256 hashes for all 25 exact protected paths from the reviewed developer snapshot. The production validator recomputes these hashes in the hosted checkout before setting empirical authorization true.

## Restrictions

- This is **not** an empirical-result approval and does not accept the rejected Run #925 artifact or runs launched using stale approval.
- The approval is valid only for the protected file contents recorded in the companion manifest. Any changed protected file, missing tester copy, changed report bytes, invalid ancestry, or mismatched report digest must deny authorization.
- At most one fresh Phase 7 empirical run may proceed after the manifest/report have been copied byte-for-byte to the developer branch and the hosted validator returns authorized. The resulting immutable artifacts must receive a separate independent post-run audit of all ten panels, row alignment, P10 abstention, finite regime eligibility, P05/P06 mask alignment, family-bootstrap missingness, hashes, aggregate metrics and inference.
- No Phase 7 method is promoted and Phase 8 remains blocked until the fresh empirical artifact passes the separate tester gate. Paytm Money brokerage, exchange/statutory charges, spread, slippage, latency and premium decay remain mandatory in Phase 8.

## Disposition

The correction-specific authorization code gate is **PASS WITH SCOPED RESTRICTIONS** for one fresh empirical execution on the reviewed snapshot. This report is not a statement that the snapshot is profitable, statistically significant, or tradable.

**Tester → Developer:** Copy this report and its companion JSON manifest byte-for-byte to `phase-07-developer`; do not edit protected files; confirm the hosted validator reports authorization true before a single fresh run, then submit its immutable artifact for independent audit.

**Developer → Tester:** Independently audit the next artifact, all ten panels and the complete frozen metric/inference checks. Issue a separate empirical gate; do not permit Phase 8 based solely on this code gate.
