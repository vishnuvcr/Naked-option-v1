# Independent Tester Report — Extension 2 Gate A Corrected Sample Artifact

**Decision: REQUEST CHANGES — corrected sample schema checks pass, but FII/DII source coverage is not sufficient to close Gate A.**  
**Run:** [GitHub Actions 38026993369](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38026993369)  
**Artifact:** ID 11661065266, name phase7-extension2-gate-a-source-feasibility-v2  
**ZIP SHA-256:** 10a3fba40359c230bafa0f47c2d01be8f057e39b5eed0b70335710b59c57558a  
**Scope:** post-run source-artifact audit only. No features, labels, model fitting, metrics or p-values were produced.

## 1. Artifact and report integrity

Artifact ZIP contains two JSON reports:
- F&O archive/page/API feasibility report: SHA-256 `6b2e08cea42181c77f9dcd5c4ba492876c8f4001d97e629b54a9d8da9077e178`
- Index/equity/FII-DII feasibility report: SHA-256 `8ad1dc5161d9100c3dd73a2ba8b50fac0906ca619310015dbddfa8fc2f1a2371`

Local SHA-256 of the downloaded ZIP matches the workflow upload log. Both reports reconcile to the exact bounded requests registered in the approved sampler snapshot.

## 2. Bounded schema checks that pass

### Official NSE F&O archive transition
- Legacy F&O archive 2024-07-05: 33,930 rows; required columns present; one trade date; 1,634 NIFTY index-option rows. Source archive SHA-256: `a6ba5c9f48555b4adb21c199bb2f9cd100eb2ebf05fc25b1a91feea71020474b`. Extracted CSV SHA-256: `52de7788d4ea40008612e02d41b6ce0ef561285e990e6e79396c68a9cd332d63`.
- UDiFF F&O archive 2024-07-08: 34,390 rows; required columns present; one trade date; 1,634 NIFTY index-option rows. Source archive SHA-256: `af47c5b8b6e0ac02da4d5a4d22d46d73527d81552a93aba99ae91590b8549d76`. Extracted CSV SHA-256: `bdf7b5c8dbe0a9cb48c429899f753cf87d036b0b25a6595157723ca598374064`.
- Both use official NSE archive URLs. These single-day checks show both archive schemas are retrievable and can be parsed; they do not establish full historical contract continuity or exact field equivalence over all years.

### Official NSE daily index CSVs
- 2024-07-05 and 2024-07-08 both have 118 rows; every row matches the requested source date.
- Both contain all ten frozen sector identities and NIFTY 50 with the expected Closing Index Value field. Missing expected identities: zero.
- Raw file SHA-256 values: 2024-07-05 `bfa78697340752f6b7138c524f96fb6df703154acef52829efa7cb91aec66288`; 2024-07-08 `5176db1d59b2dc25297096674329e46651448d708028b4dc16dd9ec23bb7156f`.
- Numeric DD-MM-YYYY normalization works on these official files; both now correctly report PASS. Example values: NIFTY 50 close 24,323.85 on 2024-07-05 and 24,320.55 on 2024-07-08.

### Official NSE cash-market equity bhavcopy
- Legacy cash-equity archive 2024-07-05: 2,775 rows, all rows on the requested date, 1,699 records meet SERIES=EQ, INE ISIN, positive close and positive volume.
- UDiFF cash-equity archive 2024-07-08: 2,815 rows, all rows on the requested date, 1,701 records meet the corresponding UDiFF EQ/INE/positive-close/positive-volume filter.
- The rows can support the intended derived-breadth feasibility checks, but only one adjacent daily sample pair has been inspected; no longitudinal breadth table exists.

## 3. FII/DII API response-window behavior now correctly rejected

- NSE current endpoint returned two records dated 2026-10-09 (source payload SHA-256 `295b6c4e37225f9dea0f662d82c45efc76ea00818e38d9c57acb918f7ddd042b`).
- The request for 2024-07-01 through 2024-07-10 returned the **same** two current records and same SHA-256. Both rows fall outside the requested window and the sampler now correctly marks the dated response `REJECTED_ROWS_OUTSIDE_REQUESTED_WINDOW`; they are not accepted as historical records.
- This indicates that this dated API request path does not provide the requested historical window. Do not reuse its response as history, and do not expand the query range to work around the result.

## 4. Historical flow sources: schema OK, coverage insufficient

The bounded GitHub mirror file `MrChartist/fii-dii-data/data/history.json` returned 164 rows, all with parseable dates and finite required flow values:
- Unique dates: 164; duplicate dates: zero.
- Range: 2026-01-14 through 2026-09-30.
- Missing required-field rows: zero; invalid-date rows: zero; nonnumeric/nonfinite-flow rows: zero.
- Raw file SHA-256: `f65e79ed5bc16bce0ecabf0dc7be39ea2b59af6212ab65e2ffa990e733ce7be7`.
- It contains three source labels: fetch-pipeline, historical-seed and live-fetch. These labels do not by themselves prove official row-level lineage or point-in-time vintages.

Other sampled pages remain unverified as long-range datasets:
- ChartDrift page parser exposed 16 recent HTML table rows.
- Fundata page exposed three HTML rows.
- TradersCockpit page exposed 33 HTML rows, but these were not validated as 33 unique dated history records.
- NSE page/API sampling exposes current/general data but did not demonstrate historical range retrieval.

The registered confirmatory family requires at least **500 aligned historical sessions**. The verified rolling source has 164, and these page excerpts do not establish 500 dated rows. No claim of historical FII/DII data unavailability is justified yet; several additional free sources need bounded inspection.

## 5. Decision

**REQUEST CHANGES for Gate A completion.** The corrected artifact has no remaining date/schema validation bug in the sampled index, cash-equity or F&O files, and the NSE API's out-of-window response is correctly rejected. However, source availability is not sufficiently established for the full seven-method family because G14/G15 still lack a demonstrated 500-session flow history.

This is not a model result and not a predictor failure. No full history, normalized feature table, labels, predictions, metrics, p-values or final-holdout data were created. The source authorization manifest was marked spent after this single approved batch.

## 6. Required next phase

Submit a separately scoped free-source discovery proposal before making any additional requests. At minimum consider:
- one-date static JSON samples from chirag127;
- fixed-range/page/API probes for Stockezee, RG Tools, ChartDrift and other discovered dashboards;
- a bounded and explicit plan to reconcile the MrChartist file's observed 164-row coverage with its README/API claim of 800 records, without importing the whole file;
- any free Kaggle/Hugging Face data candidates after their actual file/date/schema metadata has been verified.

Freeze endpoint URLs, date windows, response caps and row limits; test that an old or full-history URL cannot be requested. Then obtain a fresh code gate and a separate source-artifact authorization. Do not start full-history acquisition or model fitting until the free-source search has been exhausted and a later independent gate authorizes it.

**Tester → Developer:** Keep this artifact accepted only as bounded schema evidence; Gate A for the full predictor family remains open due flow-coverage insufficiency. Prepare a new bounded free-source discovery spec and exact tests before further network requests.

**Developer → Tester:** Independently review the next discovery sampler and bounds. Do not authorize full-history download or model fitting on the basis of this artifact.
