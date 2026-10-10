# Independent Tester Artifact Audit — DhanHQ Sample Run

**Decision: REQUEST CHANGES — the bounded run did not obtain candle data.**  
**Run:** [38043148580](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38043148580)  
**Artifact ID:** `11666064550` (`dhan-market-data-bounded-sample`)  
**ZIP SHA-256:** `45f2b23a0835cb6b1af52ac12913bf86062f9c82a0d3edcef4c810a3f30f38d9`

## Evidence

The uploaded JSON was exactly:
```json
{
  "request_count": 2,
  "status": "BLOCKED_INSTRUMENT_METADATA"
}
```

## Audit findings

- Offline regressions passed before the source step.
- Exact manifest/hash/ancestry/scope checks passed.
- The manifest was marked SPENT before the first request.
- Two requests were made: profile/entitlement probe, then the `IDX_I` instrument metadata request. The second request returned a non-200 status; the adapter stopped before any historical candle requests.
- No candle rows, price history, option history or FII/FPI/DII flows were obtained. No prediction analysis was rerun.
- The report omitted the numeric HTTP status for the failed metadata request. That prevents distinguishing endpoint/authentication/rate-limit/provider failures. This is a reporting defect.
- No secret value or profile identity was found in the artifact. The log masking showed the secret redacted.

## Required correction

1. Add only the numeric HTTP status and a safe content-type to the blocked metadata result; continue discarding provider error bodies and raw headers.
2. Add offline tests proving the status is retained and raw response body/token are not returned.
3. Rerun the offline suite and submit a fresh exact-snapshot code/workflow review.
4. The spent manifest cannot be reused. Any retry requires a new independent approval and new one-run manifest.
5. Do not widen the endpoint, add retries, skip instrument identity resolution, fetch full history or fit models.

**Tester → Developer:** Correct the missing status diagnostic and log this artifact as REQUEST CHANGES. Keep the FII/FPI/DII flow gap open.

**Developer → Tester:** Re-review the updated exact blobs. A fresh one-run diagnostic retry may be considered only after the code gate passes. If the metadata status remains non-200, stop and return the actual numeric status in the report; no candles/full history/model fitting are authorized by this audit.
