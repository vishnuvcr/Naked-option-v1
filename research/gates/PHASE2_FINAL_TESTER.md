# Phase 2 Final Tester Gate — PASS WITH SCOPED RESTRICTIONS

## Independent review target

Developer branch `phase-02-developer`, latest hosted audit run #104, run ID `37538134897`, head SHA `aeafeaff80378071e12e4a871b6dcefbb649f63f`.

Artifact:
- `phase2-source-audit`
- Artifact ID: `11447531301`
- SHA-256 digest: `fddcea5e6710ba62270707e742fbe68719d5925d22b237f5f4f19b7c10ff2853`

## Gate evidence

| Item | Result | Tester finding |
|---|---|---|
| CI workflow completed | PASS | All Phase 2 steps completed successfully. |
| Automatic + manual workflow | PASS | Push/PR/manual dispatch remain configured. |
| Static syntax/manifest validators | PASS | All completed successfully. |
| PIT synthetic leakage test | PASS | Future observation and future-availability cases are rejected. |
| Official NSE legacy sample | PASS | 33,930 rows; SHA-256 recorded. |
| Official NSE UDiFF sample | PASS | 34,390 rows; SHA-256 recorded. |
| Legacy/UDiFF schema boundary | PASS | Both schema validators passed. |
| Raw cache | PASS | Official option archives were cache hits in the final run. |
| Global free reference | PASS | S&P 500, Nasdaq, Nikkei and Hang Seng cached with hashes and explicit exchange time zones. |
| Treasury endpoint | PASS | Corrected official TextView endpoint returned HTTP 200 in probe. |
| NSE/BSE source probes | PASS | Official endpoints returned HTTP 200 in final probe. |
| NIFTY lot-size sample | PASS | Official UDiFF `NewBrdLotQty` yielded one value: 25 for the 2024-07-08 sample/2024-07-11 expiry. |
| India VIX availability | PASS WITH RESTRICTION | Current NSE snapshot retrieved, but no publish-time field was available; it must not be used as same-day historical PIT information until an historical timestamped source is added. |
| FII/DII availability | PASS WITH RESTRICTION | Current NSE snapshot retrieved; historical publication timestamp is not demonstrated, so research uses next-session conservative availability. |
| S08 derived option corroboration | PASS WITH RESTRICTION | 96/96 validation-band key match; 97.9167% within 1% relative error; max relative error 2.8037%; strict 0.25%/tick diagnostic 95.8333%. Derived source remains non-canonical. |
| S31 derived option source | QUARANTINED | ATM parquet files did not expose contract/expiry semantics needed for a valid reconciliation; no predictive use permitted. |
| Mandatory reconciliation validator | PASS | Artifact-status gate completed successfully. |
| Paid source dependency | PASS | No paid source was required to complete Phase 2. |

## Data-quality interpretation

The **canonical research feed for Phase 3 is official NSE/BSE data plus explicitly PIT-safe auxiliary sources**.

The derived Hugging Face S08 dataset is useful as a cross-source integrity check, not as a production/execution feed. Its strict agreement metric is deliberately retained rather than hidden.

The current India VIX and FII/DII endpoint checks prove source accessibility and establish a conservative timing rule, but do not prove historical publication timestamps. Therefore the Phase 3 feature factory must either obtain timestamped historical versions or apply the declared next-session quarantine rule.

The S31 source remains quarantined.

## Gate decision

**PHASE 2 PASSED — WITH EXPLICIT SOURCE RESTRICTIONS**

Phase 3 may start.

### Conditions for Phase 3

1. No current/live endpoint snapshot may be backfilled into historical decision times.
2. FII/DII uses next-session availability unless publication timing is later demonstrated.
3. India VIX uses only timestamped/historical data or is excluded from intraday PIT features.
4. S08 is validation-only, never canonical.
5. S31 is not used unless its expiry/contract semantics are independently resolved.
6. All label/model backtests use official canonical data and retain the same PIT/cost controls.

## Tester instruction to developer

Create the Phase 3 developer branch and frozen intraday/positional label definitions. Establish naive direction baselines and cost-aware option break-even thresholds before any model fitting. Preserve all Phase 2 artifacts and restrictions unchanged.
