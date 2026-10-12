# Independent tester review — Phase 8 Greek-enrichment artifact R1

Decision: **REQUEST_CHANGES**
Developer run: 38195812828
Developer snapshot: f556c7b44088f18551453c36f78e8d5de7fe141e
Artifact: nifty-1m-greeks-enriched-r3 (ID 11723198817)
Artifact ZIP SHA-256: 
Source identity: PASS; synthetic tests: PASS; download/hash/CRC: FAIL; actual artifact audit: SKIPPED

## Findings
- Artifact download/hash/CRC: HTTPError: HTTP Error 401: Server failed to authenticate the request. Please refer to the information in the www-authenticate header.

## Independent audit result
{}

## Limits and restrictions
- This is an artifact integrity and coverage gate, not evidence of a profitable trading strategy.
- The input grid remains PARTIAL_GRID; expiry map is a file-list/rule proxy, not an official point-in-time master.
- Greeks are model estimates using r=0, q=0, IV inversion/labelled fallback, not historical vendor Greek observations.
- CC-BY-NC-4.0 means non-commercial research only. No Dhan API, option P&L, holdout, strategy promotion, commercial use or plaintext upload is authorized.

**Developer → Tester:** correct any artifact mismatch before resubmission.
**Tester → Developer:** accept delivery only if this decision is PASS_WITH_SCOPED_RESTRICTIONS; trading gates remain blocked.
