# Independent Tester Re-review — Official Reference Cross-Check Plan

**Decision: PASS WITH SCOPED RESTRICTIONS — revised plan/documentation gate only. No public-source network request is authorized by this report.**

**Reviewed revised proposal commit:** d62c5d55bfb43f62e31a720bf1fd19e9a8e51f13  
**Revised proposal blob:** a9715169626e48f619c096b0dbffee6b10c79bfe  
**File:** research/phase7/DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN.md

## Re-review of prior REQUEST CHANGES

The previous report correctly identified that compact-master SEM_SEGMENT must not be compared directly to the API enum IDX_I. The revised plan removes the invalid direct-equality acceptance criterion and now treats the two value systems separately. It requires that the candidate row be supported by the actual security ID and available official master fields, and explicitly fails closed if the public CSV cannot uniquely substantiate an index mapping. It does not permit switching to a different endpoint, raising caps in place, using credentials, or accepting data by string resemblance alone.

Official documentation grounding:
- Dhan's Instrument List page provides the official compact/detailed CSV endpoints and labels compact SEM_SEGMENT separately from SEM_INSTRUMENT_NAME; the page lists compact segment codes C/D/E/M: https://dhanhq.co/docs/v2/instruments/
- Dhan's Annexure separately defines API IDX_I as Index / Index Value and INDEX as an instrument type: https://dhanhq.co/docs/v2/annexure/

## Scope and gate order retained

The proposal still authorizes no request. It only specifies a future, separately gated cross-check bounded to:
1. one official NSE Indices historical NIFTY 50 OHLC request for 2024-01-02; and
2. one public Dhan compact instrument-master download, without any access token/cookie/client identity.

Each host has an exact URL/method allowlist, a strict time and byte ceiling, redirects/retries prohibited, and source-specific content parsing. A successful acceptance requires exact same-date OHLC match plus a unique and defensible official mapping. Raw sources are only bundled when complete comparison succeeds; mismatch/absence must not overwrite the existing cached Dhan row. Volume semantics remain explicitly unverified; this one-row check does not by itself authorize model-data acceptance, more history, feature engineering, model runs, strategy tests, or holdout access.

## Decision

**PASS WITH SCOPED RESTRICTIONS — plan only.** The revised proposal has resolved the specific SEM_SEGMENT / IDX_I namespace issue. Implementation needs its own independent code/workflow gate; the first real artifact then needs a separate tester audit. No public-source requests are authorized by this proposal pass.

**Tester → Developer:** The revised plan may be used as the specification for an offline adapter and mocked tests. Independent review of the exact implementation snapshot is still mandatory, and the new two-source request manifest/workflow must independently pass before either external request. Do not reuse the SPENT Dhan sample manifest.
