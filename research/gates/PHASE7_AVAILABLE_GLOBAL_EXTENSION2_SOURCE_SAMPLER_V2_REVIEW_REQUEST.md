# Developer → Tester Review Request — Extension 2 Gate A Sampler v2 (Corrected)

**Status: REQUESTED — no approval manifest exists; no live source sample has been fetched from this corrected snapshot.**  
**Review scope: exact code/workflow review for one bounded Gate A sample run only.**

## Reviewed snapshot

Reviewed developer commit candidate: `3c3dfaa77aec242b74d7c8c45f7a25ba0a30f6ae`.

| Protected file | Git blob ID |
|---|---|
| `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` | `a5e65b56f9aa23c8292b718403c3db4448dad2e3` |
| `scripts/phase7_extension2_source_feasibility.py` | `532c1212fad29dbd771d609b1e0ddb85d46d9e50` |
| `scripts/test_phase7_extension2_source_feasibility.py` | `4b470468a4aef23ba59d5efef8755be33ce23fe0` |
| `scripts/phase7_extension2_source_feasibility_v2.py` | `546ff0cf09eccfcd6ca79d3299e2cf80e5ed3799` |
| `scripts/test_phase7_extension2_source_feasibility_v2.py` | `5f648d7ee0cbd4ada2d591617fbf53195e3c3720` |
| `.github/workflows/phase-07-extension2-source-feasibility-v2.yml` | `20470b88d29b1d97e8060936e5ed7a40fe28a80d` |

The current developer tree was re-fetched from both the branch and the pinned snapshot; all six protected blob IDs above matched. The actual workflow Git blob is `20470b88d29b1d97e8060936e5ed7a40fe28a80d`; commit IDs are kept separate from Git blob IDs.

## Changes since the prior REQUEST CHANGES

Tester finding: `scripts/phase7_extension2_source_feasibility_v2.py` had requested NSE FII/DII data from 2020 to 2025, contrary to the Gate A small-sample restriction.

Correction in current snapshot:
- Replaced the multi-year URL with the fixed ten-day window `fromDate=01-07-2024&toDate=10-07-2024`.
- Added a URL validator that rejects any configured date range longer than ten days and rejects unregistered host/path/key combinations before making a request.
- Added a 512,000-byte response cap specifically for the NSE FII/DII API probes.
- Added a maximum of 50 returned rows; excess-row responses are marked `REJECTED_EXCESS_ROWS` and their payload is not copied into the report.
- Updated shared `fetch_bytes` to accept a per-request byte cap and added an offline regression for the cap.
- Added v2 regressions that reject the old 2020–2025 URL, validate the configured small window and caps, and test response payloads over/under the row limit.
- Corrected the handoff's workflow blob/commit distinction. Current report request pins the exact actual workflow Git blob.

## Bounded sources that the workflow will call

1. Legacy F&O bhavcopy for 2024-07-05 and UDiFF F&O archive for 2024-07-08, plus small page/API probes (`scripts/phase7_extension2_source_feasibility.py`).
2. Official daily index CSVs for 2024-07-05 and 2024-07-08, equity cash bhavcopies on those dates, a bounded rolling FII/DII mirror, public FII/DII pages, and the bounded NSE FII/DII endpoints (`scripts/phase7_extension2_source_feasibility_v2.py`).
3. Only two small JSON source-feasibility reports are uploaded. No normalized full-history tables, labels, feature tables, model outputs, metrics or p-values are produced.

## Guarded workflow behavior

- The first job runs both offline test suites.
- The authorization job requires the tester report mirrored on the developer branch, an exact report SHA-256, an explicit current decision line, explicit denials of full-history acquisition/model fitting, exact protected-file allowlist, SHA-256 bytes, Git blob IDs quoted in the tester report and reviewed-commit ancestry.
- The source job is downstream of successful regressions and exact-snapshot authorization. Manual source sampling defaults to false; selecting true still cannot bypass the tester manifest.
- A changed sampler/test/workflow/spec blob invalidates this review and requires a fresh tester decision.
- The earlier failed run `38019728293` stopped at the offline regression step and never fetched data. The prior protocol checks validate only repository contract/literature registry and are not Gate A test evidence.

## Requested independent review

Review the exact current blobs listed above. Verify:
- both archive samplers are bounded to the registered dates/pages;
- date parameter validation, 512 KB request cap and 50-row limit prevent a multi-year NSE FII/DII request or large result being processed as Gate A evidence;
- offline tests cover the prior full-history request and excess-row case;
- source parsing, schema checks, report paths and workflow guards are coherent;
- the source job cannot run unless the offline tests pass and the exact tester authorization validates.

A PASS may authorize only one small deterministic Gate A run. It must explicitly prohibit full-history acquisition and model fitting. After that run, the uploaded source artifact requires a separate independent artifact review before the next stage.

**Developer → Tester:** Independently review the exact six protected Git blobs and return PASS or REQUEST CHANGES for this snapshot only.

**Tester → Developer:** Do not create the approval manifest or fetch live data until the current exact snapshot is passed. Full-history acquisition and model fitting remain unauthorized.
