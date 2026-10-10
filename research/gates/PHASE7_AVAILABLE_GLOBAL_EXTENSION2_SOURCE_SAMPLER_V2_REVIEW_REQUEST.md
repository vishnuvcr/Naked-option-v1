# Developer → Tester Review Request — Extension 2 Gate A Sampler v2 (Corrected + Hosted Tests)

**Status: READY FOR EXACT-SNAPSHOT REVIEW.** No approval manifest exists and the v2 guarded sampler has not run on this snapshot.  
**Review scope:** one bounded Gate A source-feasibility run only.

## Exact snapshot and protected blobs

Reviewed developer commit candidate: `6050908b98c53d75c10175140e84e87f48934896`.

| Protected file | Git blob ID |
|---|---|
| `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` | `a5e65b56f9aa23c8292b718403c3db4448dad2e3` |
| `scripts/phase7_extension2_source_feasibility.py` | `532c1212fad29dbd771d609b1e0ddb85d46d9e50` |
| `scripts/test_phase7_extension2_source_feasibility.py` | `4b470468a4aef23ba59d5efef8755be33ce23fe0` |
| `scripts/phase7_extension2_source_feasibility_v2.py` | `aa714264481034c52b9e2b75d020a270212c8204` |
| `scripts/test_phase7_extension2_source_feasibility_v2.py` | `43bd50df257ecc6d094ca64c6770f26a50340ecf` |
| `.github/workflows/phase-07-extension2-source-feasibility-v2.yml` | `20470b88d29b1d97e8060936e5ed7a40fe28a80d` |

The actual workflow Git blob is listed above; `605090...` is the reviewed commit ID, not a file blob. All six protected paths were re-fetched from the current developer branch and match the listed blob IDs.

## Prior REQUEST CHANGES and corrections

The previous tester review rejected this work because an NSE FII/DII URL requested 2020–2025 data and the handoff mislabeled the workflow commit as a Git blob. These were corrected:

- The configured dated request is now 2024-07-01 through 2024-07-10 (10 days).
- `validate_nse_fii_api_url` rejects any configured window longer than 10 days and refuses unregistered host/path/key/date combinations before fetch.
- NSE FII/DII calls use a 512,000-byte cap; payloads above 50 rows are rejected without copying the rows to the report.
- Unexpected JSON shapes are flagged `UNRECOGNIZED_JSON_SHAPE`.
- Regression tests verify that the old 2020–2025 URL is refused before any call, the byte cap is passed to the fetcher, >50 rows are rejected, and unknown JSON shapes fail closed.
- Shared fetch helper accepts a per-request byte cap, with a regression proving oversized reads are rejected.

## Hosted regression evidence

- [Offline Source Feasibility Tests run](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026024826) succeeded on commit `b7713ff1ae90ac6ea8d3c477a01683634259dab1`: **7 v1 + 15 v2 = 22 offline regression checks passed**. This workflow calls test scripts only and has no network-fetch step.
- [Legacy workflow safety correction](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026080844) succeeded on commit `6050908b98c53d75c10175140e84e87f48934896`: the old v1 suite passed in the now offline-only legacy workflow.
- Earlier generic Research Protocol Check runs validate repository contract/literature registry only, not sampler tests.

## Governance issue discovered and contained

An older live-fetch workflow was still configured to trigger automatically on source/test changes. It ran once at [Run 38025793938](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38025793938) without the required exact-snapshot approval. The run was bounded to one legacy F&O date, one UDiFF F&O date, pages and small API probes; it did not run a model, create features/labels or retrieve full history. **Its artifact is non-accepted evidence because authorization was missing.** The issue is logged in the developer error log. The legacy workflow is now offline-only at the current snapshot and cannot fetch sources. The separate v2 live-source workflow is the only path allowed to perform the next sample and requires the exact manifest.

## Guarded execution design

- The v2 workflow runs both offline test suites first.
- The authorization job verifies the mirrored tester report digest, required decision line, explicit denials of full-history acquisition/model fitting, exact protected path set, file SHA-256 and Git blob IDs quoted in the report, and reviewed-commit ancestry.
- The source job is downstream of successful tests and exact-snapshot authorization.
- Manual source sampling defaults to false; selecting true still cannot bypass the approval file.
- Both F&O and index/equity/FII-DII bounded sampler JSON reports are uploaded. No full history, feature table, labels, model output, metrics, p-values or final-holdout reads are produced.

## Requested independent review

Review the six protected blobs above plus the current workflow path and logged containment. Specifically verify bounded dates/bytes/rows, all-row date and schema validation, source URL scope, fail-closed behavior, test coverage and the relationship between tests → approval check → source job.

A PASS must state the exact current scope:
- one bounded Gate A source-sampling run only;
- **Full-history acquisition: NOT AUTHORIZED**;
- **Model fitting: NOT AUTHORIZED**;
- no features, labels, prediction metrics/p-values or final holdout;
- the uploaded source-feasibility artifact requires a separate independent audit before any later step.

**Developer → Tester:** Review this exact source snapshot and return PASS or REQUEST CHANGES for Gate A only.

**Tester → Developer:** Do not create the authorization manifest until this snapshot receives an explicit scoped PASS. After the one bounded run, audit both uploaded reports independently before deciding on further progress.
