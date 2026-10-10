# Independent Tester Report — Dhan Daily NIFTY One-Use Manifest and Workflow Gate

**Decision: PASS WITH SCOPED RESTRICTIONS — the exact manifest/workflow may be promoted to READY for one tiny daily NIFTY sample. No request is authorized while the approval remains PENDING_REVIEW.**

**Reviewed developer branch head:** `5aaef5ba44443fbf19a8f239daf8ba4341663432`  
**Protected source/workflow snapshot commit:** `2646f3c9a08a565973d85d51e83f0fe393c0664f`  
**Manifest commit:** `2bf8669827d975035935ad27a1f50aa77ce8f352`  
**Current pending-approval commit:** `5aaef5ba44443fbf19a8f239daf8ba4341663432`  
**Hosted offline gate:** [Run 38053917972](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38053917972), success: 42 history-pipeline tests, 7 sample-runner tests, 15 manifest-validator tests, exact manifest fingerprint check, and `PASS_MANIFEST_REVIEW_PREFLIGHT`.  
**Hosted protocol check:** [Run 38053918130](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38053918130), queued at the time of this review; its final conclusion must be checked before the source request is considered.

## Exact reviewed hashes

| Artifact | Git blob SHA / digest |
|---|---|
| `research/gates/DHAN_DAILY_SAMPLE_REQUEST.json` | blob `e908f5d8eea9d85d083d6309c017a17916e931a7`; raw-file SHA-256 `37473911f47ea32e855a3dad09349f60072d4b6840b6be4377b9e56e528be794` |
| Canonical authorization object | SHA-256 `ecea66dfbdd54987e76e3f6739d59057bf62b5a913a8359f8c147b5d6d71b618` |
| `scripts/dhan_history_pipeline.py` | blob `84e30b0d45ffb2a9b6985601b934c66db435b201`; SHA-256 `55b948a96c494e63d8e565a0703893c6bedca0a2fe9ecdc9d3bc8f9a9e964803` |
| `scripts/test_dhan_history_pipeline.py` | blob `e58ffd6d4b4daf8e049c0be0c2edca44dc16a161`; SHA-256 `479639847569d52dd5d79802f7b359c74a8895db09a6b542e226b1c30dc58f54` |
| `scripts/run_dhan_daily_sample.py` | blob `3a49360fb68e2e7c4e10ca8be31908be6a8ae8b2`; SHA-256 `41715f365a05308fd15327b3fd4c70da7ca7559cfecc51d813ef2431a7cae1e3` |
| `scripts/test_run_dhan_daily_sample.py` | blob `105ecef36f939cd7438264d9d271f5be1e229d4e`; SHA-256 `8082c92b1c8c90b0a0ac128db4207852c5d089ede33ead1350a7b0c5cfdfb4a8` |
| `scripts/validate_dhan_daily_sample_approval.py` | blob `16de96df329e6574b872ee660e1d6838fc317eff`; SHA-256 `7d089ed34b1dedc9beb8af16867999714ac2e3e2d9f8f8b676f715bf6aa75772` |
| `scripts/test_validate_dhan_daily_sample_approval.py` | blob `7fa2aeb9e38b66ce20aa6e136626978c4d5afabc`; SHA-256 `5d4f2a78ba7b8648a9edf6a97103ac60b90b2f992f1a4c10260c824212ae5638` |
| `.github/workflows/phase-07-dhan-daily-sample-live.yml` | blob `b695deadd0d12723115a67ffdf54afdd9f44d447`; SHA-256 `c6899551202fc56e4f3ad6a3210a40a1e77606496b387bf15a7ffbfef0df04e5` |
| `.github/workflows/phase-07-dhan-daily-sample-tests.yml` | blob `f6c50d546e2306e5200aa533dbc480d15b774d38`; SHA-256 `6c2a8a0f0ab0a90931533f9e38bfb82efcfddd397f3d2a2acdc9629b96db7707` |
| `research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md` | blob `9145f88ec99169a900d9ff2c7b77c0592781f5ae`; SHA-256 `801993a4bdf4709adcd6e811df889cdbea731c96b057ccec70fb39cb73e1036d` |
| `research/gates/PHASE7_DHAN_HISTORICAL_DATA_RECOVERY_CODE_FINAL_TESTER.md` | blob `f1218310778c95499e2d7958d47118a4065c0f94`; SHA-256 `6c35235d9cd08b2af87adfc697f199959e6ce94d9ba28fe2b27985ce8d17aec3` |
| `research/gates/PHASE7_DHAN_HISTORICAL_DATA_RECOVERY_CODE_SUBMISSION.md` | blob `2035255912651ade1dc17ac292a81de796d6bf91`; SHA-256 `01a32b3a8559bda98b178e40356f29c226f7d611b2a925c4a8f741ea7902e647` |

The hosted fingerprint step reported `protected_files_match_manifest=true` and `authorization_digest_matches_manifest=true`. The separate approval record remains `PENDING_REVIEW` and does not yet contain a tester report hash/blob.

## Official source contract

- Dhan v2 historical docs identify `POST https://api.dhan.co/v2/charts/historical`, require `securityId`, `exchangeSegment`, `instrument`, `fromDate`, and `toDate`, describe daily OHLCV and timestamp arrays, and explicitly call `toDate` non-inclusive: https://dhanhq.co/docs/v2/historical-data/
- Dhan's option-chain documentation illustrates underlying scrip `13` in segment `IDX_I` with an example index-level price around 25,642 in its response. This is consistent with the intended NIFTY index, but the instrument-master row itself has not yet been fetched: https://dhanhq.co/docs/v2/option-chain/
- The Dhan instrument list documentation separately exposes the official instrument master. This one-use request does not itself establish a point-in-time history of symbol mappings: https://dhanhq.co/docs/v2/instruments/

**Mapping qualification:** `securityId=13`, `exchangeSegment=IDX_I`, `instrument=INDEX` is supported by Dhan's documented examples for index underlying data, but the exact official instrument-master row and entitlement have not been directly verified in this project. A successful HTTP response alone must not be treated as data acceptance. The returned timestamp/date and prices must be cross-checked against an independent official NIFTY daily observation before the row can be used in prediction research.

## Scope being approved

Exactly one POST to `/v2/charts/historical` with the following body:

```json
{
  "securityId": "13",
  "exchangeSegment": "IDX_I",
  "instrument": "INDEX",
  "fromDate": "2024-01-02",
  "toDate": "2024-01-03",
  "oi": false
}
```

The range is one calendar day because `toDate` is exclusive. The request budget is one request, 20-second timeout, 2 MiB response cap, redirects disabled, no retries. Credentials go only to `api.dhan.co`, in the documented `access-token` header, and the workflow checks that the secret exists before spending approval.

## Independent checks completed

1. **Manifest integrity:** exact raw manifest SHA-256, canonical authorization SHA-256, Git blob and 11 protected file blob/SHA-256 pairs verified by hosted Python `hashlib` plus Git.
2. **Date semantics:** exact one-day range aligns with Dhan's documented non-inclusive `toDate`.
3. **Request restrictions:** endpoint/method/request-body allowlists, hard one-request/byte budgets, no redirects/retries, no profile/option-chain/order API and no bulk/history/strategy/model permissions.
4. **Approval ordering:** workflow runs offline regressions, checks token presence without printing it, validates the READY approval, marks it SPENT and pushes that commit before the only request step receives the token.
5. **Failure handling:** non-2xx, invalid content type, malformed schema, oversized/misaligned data and wrong date window fail closed; provider error bodies and access token are not persisted. The raw response is cached only if schema/window/provenance validation succeeds.
6. **Automation:** push-based execution is gated by an explicit READY approval commit message; a manual dispatch control requires `confirm_live_sample=true` (default false) and targets `phase-07-developer`. The default-branch workflow copy now has the identical live-workflow blob.
7. **State machine:** the offline-only workflow applies read-only checks for PENDING_REVIEW and READY and explicitly does not initiate/repeat acquisition when the approval is SPENT.
8. **Run evidence:** [Run 38053917972](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38053917972) passed 42 history-pipeline tests, 7 sample-runner tests and 15 manifest-validator tests; its final preflight line is `PASS_MANIFEST_REVIEW_PREFLIGHT` with `live_request_authorized=false`.

## Decision and restrictions

**PASS WITH SCOPED RESTRICTIONS.** The manifest/workflow gate is acceptable for one tiny daily NIFTY history request after the developer records this report and completes the READY transition. No live request is authorized while the approval remains `PENDING_REVIEW`; the workflow must revalidate exact report/hash pins and spend the one-use approval before the single request. If the Dhan secret is absent, the workflow must stop before spending approval.

This report does **not** authorize:
- more than one request;
- any retry or redirect follow;
- intraday or rolling-option history;
- bulk acquisition or any other Dhan endpoint;
- feature engineering, predictor fitting/reruns, strategy backtests or final-holdout access;
- treating the one-day sample as accepted market data without independent NIFTY mapping, date and price checks.

**Tester → Developer:** Copy this exact report to `phase-07-developer`, calculate its raw-file SHA-256 using Python `hashlib`, and set the approval record's `tester_report_git_blob` / `tester_report_sha256` to the exact copied file values. Then set `status=READY` and `decision=APPROVED_ONE_RUN` without changing the request manifest or protected code files, retaining the exact manifest blob/hash and authorization digest. Use a commit message containing `READY Dhan daily sample approval` so the guarded workflow runs automatically. If the preflight, secret-presence check, or runtime pin checks fail, stop before any request; do not bypass them. After the run, independently inspect the result artifact and do not authorize expansion until it has a separate artifact review.
