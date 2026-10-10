# Independent Tester Artifact Audit — Dhan Diagnostic Retry 2

**Decision: REQUEST CHANGES — instrument metadata remains blocked; no candle sample obtained.**  
**Run:** [38043667443](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043667443)  
**Artifact ID:** `11667455094`  
**ZIP SHA-256:** `f388a9844db92836ec6551e2e442e207dc8d504bc9ae198df860117a2aabc68e`

## Artifact contents

```json
{
  "bytes_read": 180,
  "instrument_metadata_content_type": "",
  "instrument_metadata_http_status": 302,
  "profile_probe": {
    "data_plan_active": true,
    "http_status": 200,
    "status": "TOKEN_VALID",
    "token_valid": true
  },
  "request_count": 2,
  "status": "BLOCKED_INSTRUMENT_METADATA"
}
```

## Findings

- The secret was accepted: profile HTTP 200, token valid, Data API plan active. No identity fields or token values appear in the artifact.
- The exact manifest/hash/ancestry/scope check passed and the manifest was marked SPENT before source access.
- The `GET /v2/instrument/IDX_I` request returned HTTP **302**. The reviewed policy rejects redirects; no redirect was followed and no historical candle requests were made.
- No NIFTY 50 / India VIX candles, option history or FII/FPI/DII flows were obtained. No prediction analysis was rerun.
- The current report does not include redirect destination host. It correctly omits Location path/query and raw headers, but the host-only diagnostic is needed to determine whether the redirect target can be added to a separately reviewed allowlist.

## Disposition

This artifact does not pass data-source feasibility. The token and Data API entitlement work, but the segment metadata endpoint is not usable under the current no-redirect policy. The current one-run manifest is spent and must not be reused.

**Required next step:** create a new finite proposal to expose only redirect scheme/hostname and, if justified by the official Dhan documentation, define a single-hop allowlist that never forwards the access token to the redirect host. No redirect-following or additional source request is authorized by this artifact report.

**Tester → Developer:** Record the 302 and no-data result; keep the manifest spent. Submit a new redirect-scope proposal for review before any further call.

**Developer → Tester:** Independently review the redirect host extraction and any proposed allowlist. No candle history/full history/model fitting until the metadata sample succeeds and its artifact is separately passed.
