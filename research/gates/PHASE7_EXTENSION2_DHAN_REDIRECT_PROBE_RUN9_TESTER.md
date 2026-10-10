# Independent Tester Report — Dhan Redirect Target Probe Run #9

**Decision: PASS WITH SCOPED RESTRICTIONS — diagnostic artifact only.**  
**Reviewed run:** [38047946667](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38047946667)  
**Run branch / commit:** `phase-07-developer` / `c9fb50e09563bb4c35870f73d17ac73fcfd3abc1`  
**Artifact:** `dhan-redirect-target-probe`, ID `11668017741`, ZIP SHA-256 `c7a04f1b33f31840780cdf2a3ca74ff512f1ce7ee9d7ff97378d0c900f04cc12`

## Independent checks

1. **Run identity:** GitHub Actions metadata confirms manual `workflow_dispatch`, the expected `phase-07-developer` ref and a successful completed job.
2. **Confirmation:** the job log shows `CONFIRM_PROBE: true`; the explicit-confirmation step passed.
3. **Offline regressions:** the job log reports 38/38 Dhan recovery regressions passed before the manifest was checked.
4. **Manifest:** `validate_dhan_redirect_probe_approval.py check` reported the exact report/files/tree/scope validated. The spend step then reported `SPENT_BEFORE_SOURCE_REQUEST`, committed the spent manifest as commit `f516841`, and pushed it before the source request step.
5. **Request budget:** the diagnostic log reports `request_count: 1`, `bytes_read: 0`, `sample_count: 0`, status `REDIRECT_TARGET_RECORDED`.
6. **Artifact contents:** independently downloaded and inspected JSON contains only `bytes_read=0`, `content_type=""`, `http_status=302`, `redirect_host="s3.ap-south-1.amazonaws.com"`, `redirect_scheme="https"`, `redirect_target_status="PARSED"`, `request_count=1`, and `status="REDIRECT_TARGET_RECORDED"`. No raw Location URL/path/query, token, response body or price data is present.
7. **Redirect behavior:** the source log and artifact show the redirect target was parsed, not followed. No candle/history request or model/holdout access occurred.
8. **Automated downstream gate:** audit run [38047812286](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38047812286) passed identity/immutable-artifact preflight; its independent-tester job was skipped because this diagnostic artifact class is not an approved empirical-data artifact. This report supplies the scoped independent review; the skipped automated job is not counted as a pass.

## Decision and restrictions

**Accepted:** the narrow redirect-target diagnostic result and its procedural compliance.

**Not accepted / not authorized:** any redirect follow, use of the S3 host as an approved data endpoint, market-data download, historical candles/options data, cache population, feature/label construction, model fitting, prediction reruns, economic/strategy testing, or holdout access.

The observed hostname alone does not prove that the target/path is an official or authorized Dhan data endpoint. A separate source-validation proposal must identify an authoritative documented endpoint, use no credential forwarding to any redirect host, state exact request/response budgets, pin code and tests, and receive a new developer implementation gate plus an independent tester gate before any further external request. The spent manifest cannot be reused.

## Mathematical / logical audit

No numerical model metrics were produced, so no predictive inference can be drawn. The request count and byte count are consistent with the stated narrow scope. The HTTP 302 is evidence of a redirect response, not evidence that the source provides usable market data or that the target is safe to follow.

**Tester → Developer:** Archive this report on the isolated tester branch. Propose the next step as a separate, no-network source-documentation and endpoint-validation review first; do not issue a follow-up live request under the spent authorization.

**Developer → Tester:** Any future request must have a fresh exact-snapshot report, pinned manifest and explicit single-use authorization; return for independent review before execution.
