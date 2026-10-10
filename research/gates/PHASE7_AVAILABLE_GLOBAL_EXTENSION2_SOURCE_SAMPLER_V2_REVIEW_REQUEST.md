# Developer → Tester Review Request — Extension 2 Gate A Sampler v2

**Status: AWAITING INDEPENDENT CODE-GATE DECISION. No source sample has been fetched by the current v2 snapshot.**

## Exact current snapshot

All blob IDs below were fetched from `phase-07-developer` immediately before this submission:

| Protected file | Git blob |
|---|---|
| `research/phase7/AVAILABLE_DATA_PREDICTION_EXTENSION_2_SPEC.md` | `a5e65b56f9aa23c8292b718403c3db4448dad2e3` |
| `scripts/phase7_extension2_source_feasibility.py` | `f39f2a213b760c608e0deca2f1eaacc2225aca53` |
| `scripts/test_phase7_extension2_source_feasibility.py` | `2d8833719701c87e43f310396b29380220d58578` |
| `scripts/phase7_extension2_source_feasibility_v2.py` | `fb83fe5e880a26134a765a0426f7aa85380272fb` |
| `scripts/test_phase7_extension2_source_feasibility_v2.py` | `d818613dc2f9188224562a953fd979a6c274d292` |
| `.github/workflows/phase-07-extension2-source-feasibility-v2.yml` | `c535610e69c2e90934ab4e59d754b584e29ff6ec` |

The latest tester report is `research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_SAMPLER_V2_TESTER.md` on `phase-07-tester` (blob `26e58f647a692b6e7ecc486914e290120065bfd5`). It contains a scoped PASS for a prior sampler blob `4c69b20e3eb4a6a0f99c6f0137de06806a13ff1f`, not the current sampler blob `fb83fe5e880a26134a765a0426f7aa85380272fb`. The prior PASS therefore does not approve this exact code/workflow snapshot.

## Changes since the previous scoped PASS

1. The v2 sampler's FII/DII normalized-date validator was corrected after Run #1 failed because its ISO-date regex was over-escaped. The current regex is `\d{4}-\d{2}-\d{2}`; this fix changed the sampler blob.
2. The v2 workflow is now split into three jobs:
   - offline regression tests only;
   - a fail-closed authorization job that checks an explicit tester approval JSON, exact mirrored tester-report SHA-256, reviewed-commit ancestry, exact protected path set and file SHA-256 values;
   - bounded sample acquisition, conditional on successful exact-snapshot approval.
3. Manual dispatch has a `run_source_sample` boolean that defaults to false. Manual dispatch without the explicit opt-in runs tests only. Setting it true still cannot pass the gate unless the exact-snapshot approval file validates. Push-triggered source sampling listens only for the approval-manifest path.
4. The approval manifest is absent on both branches. No source request may run until the independent tester approves these exact blobs and the developer mirrors that exact report before constructing the hash-bound manifest.

## Previous run status

- [Run #1 / 38019728293](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019728293) failed in `Run offline source/schema regressions`.
- The `Fetch only registered Gate A samples` step was skipped.
- No live source requests were made and no artifact was uploaded by that run.
- The date-regex correction is not yet covered by a completed hosted v2 test run for the current exact snapshot.

## Scope of requested review

Please independently review the exact six protected blobs above, especially:

- date normalization / validation on all FII/DII rows and the negative regression cases;
- source sample dates and request bounds;
- parsing and schema checks for official sector-index CSV, legacy F&O archive, UDiFF archive, official daily equity archive and bounded FII/DII endpoints;
- no request path to full-history acquisition, feature/label construction, model fitting, metrics/p-values or final holdout;
- correct authorization/hash gate on both automatic and manual triggers;
- whether the exact approved manifest would bind the current immutable snapshot.

A PASS may authorize only one bounded Gate A sample run and upload of `extension2_gate_a_source_feasibility_v2.json`. It must not authorize full-history downloads, feature construction, labels, model fitting, metric generation or final-holdout access.

**Developer → Tester:** Return PASS or REQUEST CHANGES against the exact current blobs; do not treat the earlier scoped PASS as approval of this changed snapshot.

**Tester → Developer:** Keep the approval manifest absent unless the exact current snapshot is explicitly passed. After the bounded artifact is produced, perform a separate source-feasibility artifact audit before permitting full-history acquisition.
