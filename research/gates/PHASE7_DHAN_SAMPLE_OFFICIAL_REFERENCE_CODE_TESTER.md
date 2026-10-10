# Independent Tester Report — Official NIFTY Sample Cross-Check Implementation

**Decision: REQUEST CHANGES — no request to NSE Indices or the Dhan instrument-master host is authorized.**

**Reviewed developer branch head:** 7753d426d4c009347d66776956477921986e79a7  
**Reviewed current plan blob:** a9715169626e48f619c096b0dbffee6b10c79bfe  
**Adapter blob:** afa0ef71678a6aa73467ecca5df918af67a20aeb  
**Runner blob:** fd702f1633cada0b4f368667634a788bfaa54222

## Finding 1 — implementation still contains the mapping defect removed from the plan

The revised plan correctly says not to compare the compact CSV field SEM_SEGMENT with API enum IDX_I. However, the current implementation still sets EXPECTED_MAPPING.segment to IDX_I and the mapping parser searches for a row where:

- SEM_SMST_SECURITY_ID equals 13; and
- SEM_SEGMENT equals IDX_I.

It then requires that same equality again. This contradicts the revised plan and the official Dhan instrument-list column definition, which describes compact SEM_SEGMENT using its own codes (C/D/E/M). Dhan's Annexure separately defines IDX_I as the API exchangeSegment enum for Index Value.

Official evidence:
- Instrument list / compact CSV field mapping: https://dhanhq.co/docs/v2/instruments/
- API exchangeSegment / instrument enums: https://dhanhq.co/docs/v2/annexure/

This is at minimum a deterministic fail-closed defect: it is likely to report no mapping and prevent the check from passing even when the official row is otherwise valid. Do not try to make the source data match this assumption. Correct the implementation to query and validate the actual official CSV fields; keep IDX_I as a separate API-level semantic assertion based on Dhan's Annexure. If the public compact CSV cannot uniquely substantiate that security ID as the index, fail closed and propose an alternate reference under a new review gate.

## Finding 2 — independent offline regression tests and workflow not present in reviewed branch

The reviewed scripts directory contains scripts/official_reference_crosscheck.py and scripts/run_official_reference_crosscheck.py, but no dedicated cross-check test module. The current .github/workflows directory also has no official-reference-crosscheck test workflow or live workflow. The runner references:
- research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_REQUEST.json
- research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_APPROVAL.json

Those exact files were not present in the reviewed branch. A caller cannot safely treat the present code as a ready, independently tested one-use gate. The absence of a live workflow is not itself a safety defect; attempting public network calls before offline tests and a fresh manifest/review are present would be a serious gate violation.

Required next steps:
1. Fix the compact CSV mapping logic as described above; preserve the two exact source URL/method/body allowlists, no-credentials boundaries, timeout and byte caps, and no-retry/no-redirect behavior.
2. Add deterministic offline/mock tests covering both response parsers, exact date/index, matching and mismatching OHLC, zero/multiple rows, malformed/double-encoded JSON, CSV schema/mapping absent/nonunique, wrong field types, non-200, content-type mismatch, redirects, timeouts, oversize/cap+1 reads and atomic no-write-on-any-failure.
3. Review the runner's fail-closed path and cache atomicity. A failure after the first source request must not produce a partial success cache. Persist only safe request metadata/status on failures, not raw error bodies.
4. Add an offline-only test workflow; run it in GitHub Actions and retain exact logs/artifact hashes.
5. Only after code and workflow PASS, create a fresh exact-snapshot request manifest and separate approval record. Include current adapter, runner, tests, test workflow, the amended proposal, and relevant independent tester reports. Have the isolated tester review those exact pins and live-workflow snapshot. The official-reference gate must spend the new approval before its first request and may make no more than one request per exact host.

## Disposition

This report approves neither the implementation nor any network activity. The already-approved Dhan one-use sample remains SPENT and must not be reused. Do not attempt either official public-source request, mutate the accepted Dhan cache, fit a model, rerun prediction experiments, test options strategies, or open the final holdout until the corrected implementation and fresh two-source manifest/workflow both pass their separate tester gates.

**Tester → Developer:** Fix the compact-segment/API-enum mismatch and submit the exact new adapter + runner + offline tests + workflow blobs for independent re-review. Keep both external requests disabled and do not create a READY request approval yet.
