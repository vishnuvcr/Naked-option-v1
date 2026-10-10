# Developer → Tester Review Request — Gate A Sampler v2, Corrected Source Validation

**Status: REQUESTED — no source-sampling approval exists.** The previous Gate A approval was revoked after an independently audited artifact failed source validation.  
**Requested scope:** one bounded Gate A source-feasibility rerun only, after exact-snapshot approval. No full history or modeling.

## Exact reviewed snapshot

Reviewed developer commit candidate: `784474de59a050ba6229ee5cb9a708c0f74ca2dc`.

| Protected file | Git blob ID | SHA-256 of file bytes |
|---|---|---|
| `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` | `a5e65b56f9aa23c8292b718403c3db4448dad2e3` | `df57634e69a8696e47184f066713d9dc06d47487a5111b534f7b754ed9b7ff26` |
| `scripts/phase7_extension2_source_feasibility.py` | `532c1212fad29dbd771d609b1e0ddb85d46d9e50` | `feedd15bcb33530dbecb22293ec00cccc1bcb8748ec4a9444fbcf8c14357dc11` |
| `scripts/test_phase7_extension2_source_feasibility.py` | `4b470468a4aef23ba59d5efef8755be33ce23fe0` | `149d6237ac5ee78866089912b840cfd4e42e42c3f2efd96023352755905060db` |
| `scripts/phase7_extension2_source_feasibility_v2.py` | `1f5013a43c5394ea92bdd300a67e299c1bdb079f` | `6b182e135cf047ebdd212d7585b9f9fe72af65787f92ccd8d23a114f3ba3fcbf` |
| `scripts/test_phase7_extension2_source_feasibility_v2.py` | `9b90eb50eae7974ce583fc5201fedcd53b35ae19` | `e95d1098ab0439aa1e353a516c36ae01f993e9557f65598911946a7a6f177d30` |
| `.github/workflows/phase-07-extension2-source-feasibility-v2.yml` | `a699eaf8af92978da2ae6961cb3c5dabb44a47a4` | `26cfd955a61c56686287ee2a83a4a80ec47067fac46e72f32761edb56395c765` |
| `.github/workflows/phase-07-extension2-source-feasibility.yml` (legacy, offline-only) | `f23bb9fe8a5b1343a2a94d308c77b4e26de1d0f3` | `1a27ee4896bb6a6a16bb044c9036e0bb076a3a220fcb76fa12fd72dd43496241` |
| `.github/workflows/phase-07-extension2-source-feasibility-tests.yml` (offline-only) | `593da783fa81788a1041d17d82945e24d76caf4d` | `dac5ea2495ffb6e3010d504a823aca9f435c75bcb67ada305293723bea12ef7d` |

The commit hash above is not a Git blob ID. The v2 guard now includes all eight files in its protected allowlist: both samplers, both test files, the frozen spec, the guarded live workflow, and both offline-only workflows. This prevents the disabled legacy workflow or the local offline test workflow from being altered independently of the reviewed live-source gate.

## Corrections after the source-artifact REQUEST CHANGES

The previously accepted code gate did **not** guarantee source feasibility: the post-run tester found two defects in artifact `11660395594` from Run `38026272245`:

1. The official NSE index CSV had `Index Date` formatted `DD-MM-YYYY` (for example, `05-07-2024`); the parser did not recognize that valid official format.
2. The date-filtered NSE FII/DII API for 2024-07-01 to 2024-07-10 returned records dated 2026-10-09, but the sampler recorded them as `JSON_PARSED` without checking the response rows against the requested interval.

The current corrected code:
- parses numeric `DD-MM-YYYY` dates deterministically;
- validates **every** row of a date-parameter FII/DII API response against the requested window;
- marks any out-of-window row as `REJECTED_ROWS_OUTSIDE_REQUESTED_WINDOW`, and any missing/unparseable row date as `UNVERIFIED_RESPONSE_DATE`;
- reports only offending row/date examples for rejected payloads, not the full response as a valid sample;
- retains the 10-day date-range guard, 512 KB response limit, and maximum 50-row limit;
- adds direct payload and source-integration fixtures for out-of-window rows, missing dates and the exact index date format.

## Hosted offline regression evidence

[Offline tests Run `38026629021`](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026629021) succeeded on commit `b6bcce64a208f7af18d8daecc50e20cf9e381ed3` with **25 checks passing** (7 legacy-format checks + 18 v2 checks). The most relevant assertions passed:
- official index `DD-MM-YYYY` date normalization;
- end-to-end date-filtered API rejection for 2026 records returned for the July 2024 request;
- rejection when response rows have no parseable date;
- rejection of the former 2020–2025 URL before fetch;
- 512 KB response and 50-row bounds;
- legacy/UDiFF contract schema and all-row trade-date checks.

The code commit is an ancestor of the reviewed snapshot. The guarded v2 workflow runs these offline suites before authorization and source acquisition.

## Governance control and previous sample

- Prior artifact gate status is REQUEST CHANGES; its approval manifest has been revoked.
- The next workflow run must prove that the old manifest is rejected and no source fetch happens unless a renewed manifest validates the exact current snapshot.
- The earlier legacy workflow incident is preserved as non-evidence at Run `38025793938`; its workflow is now offline-only. No feature/label generation or model fitting occurred.
- The new bounded source artifact must be independently audited after the next authorized run. The previous artifact cannot be reused as passing evidence.

## Free-source FII/DII discovery leads to retain for follow-up

A metadata/README-only public-source review (no bulk-history file was downloaded) identified these additional free leads:
- [chirag127/fii-dii-activity-api](https://github.com/chirag127/fii-dii-activity-api): per-date JSON files, but repository tree presently lists 63 daily files spanning 2026-06-22 through 2026-10-01, insufficient alone for the planned 500+ sessions.
- [MrChartist/fii-dii-data](https://github.com/MrChartist/fii-dii-data): repository includes `data/history.json` and documents an API with 800 historical records; needs a separately authorized bounded schema/date sample and source-vintage review.
- [marketcalls/fii-dii-data](https://github.com/marketcalls/fii-dii-data): history file and multi-timeframe aggregates, but README advertises recent daily and aggregate histories; daily raw date coverage has not yet been verified.
- [r7sh7/fii-dii-data](https://github.com/r7sh7/fii-dii-data): README claims 14 years of history; its tracked `data/history.json` file is small (about 1.5 KB), so the claim must be checked against actual dated records without assuming coverage.
- Public dashboards [Stockezee](https://www.stockezee.com/fii-dii-historical-data), [StrikeVue](https://strikevue.com/in/fii-dii-data), [RG Tools](https://tools.ruchirgupta.in/tools/fii-dii/index), and [Ansaar](https://www.ansaar.in/equities/fii-dii-data) describe historical/range views. Their data access, provenance, coverage and revision behaviour remain unverified; they are source-discovery leads, not accepted data.
- The official [NSE FII/FPI & DII report page](https://www.nseindia.com/reports/fii-dii) notes that its displayed figures are provisional and can be revised. The current date-parameter API sample ignored the requested historic window, so it cannot be treated as a historical endpoint without a corrected or alternate official source.

The above is only a search inventory; no full history has been retrieved. After the corrected bounded artifact passes, the next free-source search phase should sample these repositories/pages within a newly reviewed sample scope. Do not jump to a paid feed or declare historical data unavailable until the remaining free sources have been evaluated.

## Exact decision requested

Review this snapshot and explicitly pass or request changes. If passing, authorization must remain strictly:
- one bounded Gate A sample run only;
- **Full-history acquisition: NOT AUTHORIZED**;
- **Model fitting: NOT AUTHORIZED**;
- no feature/label tables, predictions, metrics/p-values or final-holdout access;
- a separate independent post-run artifact review is mandatory before the next step.

**Developer → Tester:** Independently verify the eight protected blobs, both source corrections, the 25-test hosted evidence and the workflow’s exact-manifest/fail-closed chain. Return a fresh exact-snapshot decision; do not authorize full-history acquisition or fitting.

**Tester → Developer:** Do not create a renewed approval manifest or fetch any source unless this exact snapshot passes. When the bounded artifact arrives, audit its hashes, source dates and all-row schema checks separately before permitting further source discovery.
