# Independent Tester Re-review — Dhan Daily NIFTY One-Use Manifest and Spend Transition

**Decision: PASS WITH SCOPED RESTRICTIONS — the corrected manifest may be promoted to READY only after this report is copied and hash-pinned. While the approval file is PENDING_REVIEW, no request is authorized.**

**Exact sample scope ID:** `dhan-nifty50-daily-2024-01-02-one-request`.

**Reviewed developer code snapshot:** `c000619a1b90ada383c52058efde9d2e4a67ac88`  
**Current developer head / pending approval:** `17c078d41a05de948f14d151c82a36a70594ef29`  
**Reviewed manifest commit:** `685607d809ccfe5c1c5f82cce8a1073d8ab3edd8`  
**Manifest Git blob:** `3ebead76bf75feb864bcd3fb66a34e2d5125d74a`  
**Raw manifest SHA-256:** `41866df6f882205739ac48e9ee6e3c5dc656319bb29bbfd4c4fa7ff252e6446f`  
**Canonical authorization SHA-256:** `d6b1884207354b103a4ed32c239bbf870b45f894fb03ad50d05b1dad1266e189`

**Hosted offline gate:** [Run 38054352342](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38054352342), success.  
**Hosted protocol check:** [Run 38054352558](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38054352558), success.

## Exact files reviewed for the spend correction

| File | Git blob SHA |
|---|---|
| `scripts/validate_dhan_daily_sample_approval.py` | `5c09cf50262e9e3a59c643641410f58aa743f995` |
| `scripts/test_validate_dhan_daily_sample_approval.py` | `d40679fcd87aba21dfcf8d720df86c5ce4582e7d` |
| `scripts/run_dhan_daily_sample.py` | `3a49360fb68e2e7c4e10ca8be31908be6a8ae8b2` |
| `.github/workflows/phase-07-dhan-daily-sample-live.yml` | `b695deadd0d12723115a67ffdf54afdd9f44d447` |
| `.github/workflows/phase-07-dhan-daily-sample-tests.yml` | `f6c50d546e2306e5200aa533dbc480d15b774d38` |
| `research/gates/DHAN_DAILY_SAMPLE_REQUEST.json` | `3ebead76bf75feb864bcd3fb66a34e2d5125d74a` |

The hosted fingerprint step on Run 38054352342 reported:
- `protected_files_match_manifest=true`
- `authorization_digest_matches_manifest=true`
- `PASS_MANIFEST_REVIEW_PREFLIGHT`
- `live_request_authorized=false`

The pending approval file pins the same manifest blob/hash and authorization digest and remains `PENDING_REVIEW`.

## Finding from the prior snapshot and correction

The tester found that the earlier spend transition wrote `status=SPENT`, `decision=SPENT_BEFORE_SOURCE_REQUEST`, and `spent_from_commit`, but it omitted `authorized_scope_id`.

A subsequent READY attempt exposed the report validator's required literal markers: the copied report first omitted the exact no-live/no-bulk markers, and the next version omitted the literal scope ID above. Both attempts failed at report validation before the spend/request steps. The approval has been returned to `PENDING_REVIEW`; no Dhan request occurred. The runner requires this exact key to match its scope before making the one POST. Without it, a READY authorization would have been spent and the sample would fail closed before contacting Dhan.

The developer fixed this with a single `prepare_spent_approval()` transition that:
- only accepts `status=READY` and `decision=APPROVED_ONE_RUN`;
- requires the exact `scope_id`;
- validates the commit format;
- writes `authorized_scope_id=scope_id` along with the SPENT state;
- refuses a second spend attempt.

The offline regression now checks the produced SPENT record contains the runner-required scope, the input READY record is not mutated, wrong scopes fail, invalid commit hashes fail, and already-spent records cannot be spent again. The hosted suite reports **42 history pipeline tests, 7 sample runner tests, and 16 manifest-validator tests passed**.

## Guard, scope and data integrity checks

- The request manifest remains limited to one POST to `https://api.dhan.co/v2/charts/historical` with `securityId=13`, `exchangeSegment=IDX_I`, `instrument=INDEX`, `fromDate=2024-01-02`, `toDate=2024-01-03` (exclusive end), `oi=false`.
- Hard cap: one request, 20-second timeout and 2 MiB response cap. Redirects and retries are disabled.
- The default-branch copy of the guarded workflow has the same Git blob as the developer-branch live workflow. Manual dispatch is present with explicit `confirm_live_sample=true`, default false, and job ref fixed to `phase-07-developer`.
- The live workflow checks for a configured Dhan token secret using a boolean only, before spending approval. The token is then available only to the one request step.
- It validates exact manifest/protected code/report pins, pushes SPENT state before the request, uses the token only at `api.dhan.co`, saves only a redacted status file on failure, and caches response bytes only after schema/date/provenance validation.
- The official Dhan daily historical docs specify non-inclusive `toDate`: https://dhanhq.co/docs/v2/historical-data/
- The example mapping `securityId=13`, `IDX_I`, `INDEX` remains supported by Dhan's published examples but is not yet validated against an acquired official instrument-master row. The returned sample must be cross-checked against an independent official NIFTY daily observation before accepted as research data.
- No live Dhan request has been made by this gate; the token-secret availability has not been observed, and the manifest remains pending. The previous redirects-probe manifest remains spent and is not reused.

## Decision and restrictions

**Safety boundary:** No live request is authorized until the canonical copied report and its exact SHA-256/Git blob are pinned in the approval record and the runtime preflight passes with status READY. No bulk acquisition is authorized by this one-use gate.

**PASS WITH SCOPED RESTRICTIONS.** The new spend transition and exact manifest pin set are acceptable for a single one-day daily NIFTY data sample after the developer records this report at the validator's canonical report path and updates its hash/blob in the approval record.

This PASS does not authorize acquisition until the approval state changes from `PENDING_REVIEW` to `READY` with `decision=APPROVED_ONE_RUN`. If the secret check, exact manifest check, or protected-file validation fails, the live workflow must stop before spending approval. The request is not to be retried under the same manifest if it fails after spending.

Not authorized under this gate: additional dates, bulk history, intraday history, rolling-option history, other API endpoints, feature engineering, predictor reruns, strategy testing, or final-holdout access.

**Tester → Developer:** The previous READY preflight correctly rejected the prior report copy because it lacked the validator's two literal scope markers. This corrected report now includes both markers above. Copy this exact report to `research/gates/PHASE7_DHAN_DAILY_SAMPLE_MANIFEST_TESTER.md` on `phase-07-developer`, calculate its raw bytes SHA-256 with Python `hashlib`, and verify the copied Git blob is `2d7fcd4c258a51c01f3f71074fe708a1e81f09ee` only if the content is identical (otherwise use the actual resulting blob). Update the approval record with the report blob/SHA, keep the manifest pins above, set `status=READY` and `decision=APPROVED_ONE_RUN`, and commit with a message containing `READY Dhan daily sample approval`. Do not touch manifest-protected source/workflow files without another gate. Observe whether the secret preflight blocks before spend; if it passes, inspect the one-use run artifact independently before any expansion.
