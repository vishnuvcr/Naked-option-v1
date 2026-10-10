# PPR-4 Tester Review 1 — Read-Only Source/Cache/PIT Inventory

**Review date:** 2026-10-10  
**Branch:** `phase-07-tester`  
**Decision:** **REQUEST CHANGES / PPR-4 EXIT BLOCKED**  
**Permitted continuation:** read-only GitHub branch/tree/commit and approval-metadata search for a genuine sealed-holdout boundary, plus documentation-only source availability review. No bulk source downloads, no model-panel acceptance, no model fitting/tuning/scoring, no final-holdout access, no options P&L.

## Exact reviewed developer artifacts

| Artifact | Blob SHA |
|---|---|
| PPR-4 source-availability manifest | `92df58fb37d0eec17e60d9ee30bc028f3d42b6be` |
| 32-row source availability register | `143ffe396308719142b3c89d36444ec136c1ee0b` |
| Read-only source feasibility audit | `7540ad60cf35079d6f740dbf48006d1be239eda7` |
| Repository-wide holdout metadata audit | `6b236e60337b8ae6d1c108cfe7fbdcbe39cb1eda` |
| Five-entry repo cache inventory | `8746e68a39888da6e43b127a56c4295b591e919a` |
| Offline validator | `b93b80cf1c82474320e976f2d4b834c65011817c` |
| Offline GitHub Actions workflow | `90dadc70e63670e111545f5a92548e6c95575478` |
| Existing source manifest | `522a4dec2c28e1d43ba5be8e9acec9a49b960b6c` |
| Existing global source manifest | `e040354a18fed5496a532eeea4dfd3fdf3e0d9fa` |
| Availability/alignment policy | `e762f80f892f5f780be2fe7b1c2aa320ee988df6` |
| PIT rules | `17654d3f55138d35cc0d0c5da3217266a3c75941` |
| Cache policy | `93abdee38845361d2f4212ea1d193a9fdceabbc1` |
| Canonical data schema | `89f02f0196d1af98a3f682a471877da191983aae` |
| Prior FII/DII source discovery | `f8f0e9a7eab494b9457a0e2d969252e40818308b` |

PPR-3 predecessor remains approved with restrictions: [PPR-3 tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_PPR3_REVIEW2_TESTER_REPORT.md), blob `af006a136c90006b3b6d0bbf8f3cac7ed80aa413`.

## Exact hosted check

[Run 38075342074](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38075342074) completed successfully on trigger commit `ee5890e0cbe96b3ba934e16f1d018dd0699f6d52`. The only job, `metadata-only-audit`, passed. Its log reports:

- `PASS: PPR-4 source register, cache inventory, metadata-only holdout audit, source/license statuses and exact blob pins reconcile.`
- `IMPORTANT: PPR-4 exit remains BLOCKED because no machine-readable final-holdout boundary was found.`
- No source requests, file downloads, data-value reads, fitting, tuning, scoring or holdout access.

This is an offline inventory/provenance check. It is not source acquisition approval, not proof that the documented datasets are usable, and not a model-performance result.

## What passes within the restricted inventory task

1. **Register structure:** 32 ordered source rows (P4-001–P4-032), with required data family/source/grain/coverage/license/cache/status/action fields. Every row has `bulk_acquisition_authorized=false` and `model_panel_accepted=false`.
2. **Source distinctions preserved:** official versus community/derived source; daily aggregate versus transaction-level; EOD versus intraday; CDSL/SEBI FPI-only versus full FII/DII; global close versus India decision time; and observed versus synthetic/backfilled estimates.
3. **License uncertainty is retained:** the large HF mixed-source options dataset still has license metadata `other`; thetrademarkk remains CC-BY-NC-4.0; artist-23 license/provenance is unresolved; LBMA potential price/IP restrictions are flagged. No source is deemed cleared for data retention or modeling.
4. **Synthetic-source control:** MrChartist's mixed file remains rejected whole-file due to the documented synthetic `historical-seed` provenance. It must not be used as actual daily flow evidence.
5. **Local cache claim is bounded:** five metadata entries are inventoried under the Git `data/` tree; the only raw market-response cache is a 121-byte, one-row Dhan sample. The one-use approval is spent. No full NIFTY index/options/VIX/FII-DII/FX/rates/gold/crude/news/calendar dataset is accepted from that cache.
6. **Workflow integrity:** the validator hashes pinned files against the exact workflow checkout. It reports correct source-register/cache row counts and exact blob pins. The workflow checks out `${{ github.sha }}` and performs only local validation; no source network code is called.
7. **Boundaries hold:** no bulk download, model panel acceptance, model fit/tune/score, final-holdout access, option P&L or reuse of the one-use Dhan authorization is permitted.

## Critical unresolved blocker — sealed final-holdout boundary

The holdout metadata audit searched all 23 branch trees for likely names such as holdout/sealed/final-test/split manifest/origin-index/row-ID-hash. It also reviewed the current PPR3/run specifications, the existing Phase 7 approval/report, and *metadata only* for two prior workflow artifacts. It found prose asserting that the holdout remained unopened, but no machine-readable boundary containing the holdout dataset ID, split ID, date boundary and/or row-ID hash.

Exact relevant findings from the audit:

- `machine_readable_boundary_found=false`
- `exact_date_boundary=null`
- `split_id=null`
- `holdout_dataset_id=null`
- `holdout_row_id_hash=null`
- `holdout_manifest_path=null`
- no holdout observations or labels were opened
- workflow artifact contents were not downloaded

**The absence of a path-name match does not prove no manifest exists anywhere outside the visible repository metadata, but it means the current snapshot cannot prove the boundary.** This is a material gate defect. Neither “it remained unopened” prose nor a future arbitrary 80/20 split is a substitute for evidence about which data rows are part of the pre-existing sealed holdout.

### Mandatory next action

Continue *read-only* search for a real holdout boundary artifact in existing repository/approval/commit metadata. Search may expand to code/config references whose names do not contain “holdout”, but must not access any holdout values or labels. If the genuine boundary cannot be found, the developer must submit a separate proposal for a new holdout design that is approved before examining future outcomes. Do not silently retrofit a boundary to accommodate the models.

## Source readiness is not established

Several strong public leads exist (official NSE index archives, NSE F&O/UDiFF archive, HF options dataset cards, Cboe VIX, Treasury daily rates, EIA WTI, RBI USD/INR, GDELT archive and CDSL/SEBI FPI records). The register correctly calls these leads rather than verified datasets. Coverage statements remain mostly provider/dataset-card/README claims; schemas, source vintages, publication timing, missingness, licensing and row-level provenance still need a separately gated validation/acquisition step. Free-source discovery is not declared exhausted, and no paid feed was pursued.

The one-page/day Dhan sample also does not satisfy the PPR-3 target source coverage. No current row-level modeling dataset has been accepted by this pass.

## Gate decision

**REQUEST CHANGES / PPR-4 EXIT BLOCKED.** The read-only register/cache audit and its offline validator pass, but PPR-4 cannot exit and data/model gates cannot open until a real machine-readable final-holdout boundary is found and independently checked without reading any holdout value/label. The source register is useful inventory evidence, not permission to download or train.

**Developer → Tester:** Continue metadata-only search for an existing split/holdout boundary under non-obvious path/config names and return the exact evidence. If no artifact exists, draft a distinct pre-outcome split design for review; do not implement it or train.

**Tester → Developer:** Keep raw data acquisition, model-panel acceptance, model use and all holdout access blocked. Re-review only the exact boundary metadata or the proposed new split governance artifact, with a new gate decision before any source/model action.
