# PPR-4 Read-Only Source Availability, Cache and Point-in-Time Feasibility Audit

**Audit date:** 2026-10-10  
**Branch:** `phase-07-developer`  
**Status:** **READ-ONLY INVENTORY COMPLETED; PPR-4 EXIT BLOCKED**  
**Next permitted activity:** more metadata-only repository/branch/approval-artifact search to locate a genuine sealed-holdout boundary, and further public source documentation search if needed. No data bulk download, model-panel acceptance, model fit/tune/score, final-holdout access, or option P&L is authorized.

## 1. Research question, aim and objectives

**Research question:** Which free and official data sources have a credible documented path to the price, option, volatility, flow, macro/cross-market, news and corporate-action inputs needed by the pre-registered prediction universe, and can each source meet the point-in-time and cache/provenance requirements without opening the final holdout?

**Aim:** determine source feasibility using repository metadata, existing cache manifests and public source documentation only; preserve exact distinctions between documented coverage claims, previously observed artifacts, and data actually validated by the project.

**Objectives**
1. Inventory current repository caches/files and source manifests without reading or accepting raw modeling data.
2. Document free/official sources for NIFTY/BSE history, option-chain/contract/OI/IV data, India VIX, FII/FPI/DII, FX/rates/gold/crude, global equity, breadth, news/sentiment and corporate actions.
3. Separate daily aggregates from transaction-level data, official reports from derived mirrors, daily EOD from intraday, and observed values from synthetic/backfilled estimates.
4. Record licensing, historical coverage claims, publication/ingestion times, revisions, missing values, schema and source-vintage risks.
5. Verify that a sealed final-holdout exclusion boundary exists as metadata only; do not read holdout observations or labels.
6. Produce a finite next-step source register. Do not download or accept new modeling data at this stage.

## 2. Method and scope

- Read the Git tree for `phase-07-developer`, the existing source and global manifests, cache policy, data schema, point-in-time rules, availability alignment, prior FII/DII source-discovery notes, previous source-gate reports and the prior Run #44 tester report.
- Queried public source pages/documentation for official NSE historical index and derivatives archives, India VIX, NSE FII/FPI/DII, BSE SENSEX, SEBI and CDSL FPI records, a public Hugging Face daily/intraday options data card, Cboe VIX, US Treasury rates, EIA WTI prices, GDELT news and NSE corporate actions.
- Classified findings as public documentation, README/dataset-card claims, prior artifact claims or repository inventory. No new public data request was made; no CSV/Parquet/news/history file or pretrained-model weights was downloaded.
- Did not open any holdout data or labels. The audit searched paths and prose metadata for split/holdout artifacts only.

## 3. Results

### 3.1 Existing repository data/cache state

The current Git tree contains only the following items under `data/`:
- small cache marker and README;
- one cached Dhan sample response JSON (121 bytes) with a manifest;
- a compact Dhan sample status report.

The request manifest states this was one bounded daily NIFTY sample request for 2024-01-02, with one validated OHLCV row. Its approval is marked **SPENT**. It cannot be reused for more requests. No full NIFTY OHLCV history, options chain, historical India VIX, FII/DII, news/social, FX, gold/crude, Treasury-rate or corporate-action dataset was found as a committed raw data file in `data/`.

The source registry contains 19 source leads (`S01–S18, S31`) and the global registry contains 16 (`S19–S30, S36–S39`). They contain repeated candidate records and untested/license-unverified entries. A source manifest is a plan—not evidence that a dataset was downloaded, covered the target dates, passed its schema check or is point-in-time usable.

Run #44 is prior artifact evidence, not a committed local cache. Its tester report states that all 11 global-series records had `cache_hit:false` in that run and were re-acquired because prior cache files did not satisfy the then-current schema contract. Its reported 1,676-row NIFTY daily series ended 2026-10-09 and does not provide exact 5-, 10- or 20-year source-native replication by itself. The Run #44 prediction finding remains negative for promotion: none of its five horizon families rejected the null after multiplicity correction.

### 3.2 Promising public-source leads — none yet accepted

| Data family | Publicly documented lead | Feasibility assessment | Current disposition |
|---|---|---|---|
| NIFTY index history | [NSE historical index/report archive](https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives), [NIFTY 50 FAQ](https://www.nseindia.com/static/products-services/indices-faqs) | NSE documentation says historical NIFTY 50 data are available from 1990-07-03 and lists historical index and NIFTY-TR material. Actual date-filter behavior, downloadable schema, publication vintage and row-level completeness have not been sampled. | Best primary candidate; no new sample request in this pass. |
| Options EOD/contract data | [NSE all derivatives reports](https://www.nseindia.com/all-reports-derivatives), [NSE contract-wise price/volume page](https://www.nseindia.com/report-detail/fo_eq_security) | Daily F&O reports include legacy bhavcopy, UDiFF Common Bhavcopy Final, participant OI/volume and FII derivative statistics. Legacy format changed on 2024-07-08. The contract-wise period filter is documented as limited to 90 days, so a separate archive path is needed for deep history. | Official archive lead; source-format/parser and historical coverage still unverified. |
| Third-party NSE F&O archive mirror | [NSE-FNO-Data-bank](https://github.com/SantoshSrinivas79/NSE-FNO-Data-bank) | Repository metadata/README claims 1,579 validated daily archives from 2020-04-13 to 2026-08-31; that is not an independent row-level audit, and terms/license must be checked. | Metadata lead only; no archive downloaded. |
| Large HF daily/intraday options dataset | [rissin/nse-options-intraday](https://huggingface.co/datasets/rissin/nse-options-intraday) | Dataset card claims about 258.9M rows and 2.51 GB, with daily NIFTY option history attributed to NSE F&O bhavcopy from 2001 onward and Upstox-derived minute bars from 2024 onward. Its license metadata says `other`. Public preview has zero OHLC/volume/OI values for some early BANKNIFTY contract rows, requiring careful missing/inactive-contract semantics. | High-priority *metadata lead*, not a valid accepted data panel; license, provenance, zeros/missingness and coverage need a later source gate. |
| HF minute options dataset | [thetrademarkk/india-index-options-1m](https://huggingface.co/datasets/thetrademarkk/india-index-options-1m) | Dataset card claims roughly 377M rows/4 GB, approximately 2021–2026 coverage, and declares CC-BY-NC-4.0. It says illiquid/far strikes can be sparse or absent. | License-restricted to non-commercial terms; not downloaded and not accepted. |
| Alternative HF option data | [artist-23/nifty-options-data](https://huggingface.co/datasets/artist-23/nifty-options-data) | Existing source register mentions weekly/monthly NIFTY options, but this audit did not verify a usable license, schema or date range. | Unverified license and provenance; not accepted. |
| India VIX | [NSE India VIX page](https://www.nseindia.com/static/products-services/indices-indiavix-index) | Official page links VIX history and methodology; no exact history-range/schema sample has been reviewed. | Primary-source lead; availability timestamp/vintage still required. |
| FII/FPI/DII aggregate flows | [NSE flow page](https://www.nseindia.com/reports/fii-dii) | Official page distinguishes NSE-only from combined NSE/BSE/MSEI values and notes that values are provisional/revisable. Earlier repository discovery found the date-parameter endpoint returned current rows for an old requested period, so that route is not validated as historical. | Major unresolved feature family; no replacement series inferred. |
| FPI-only daily/transaction sources | [CDSL daily FPI archive](https://www.cdslindia.com/Publications/ForeignPortInvestor.html), [SEBI trade-wise FPI archive](https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html) | Prior search found dated CDSL FPI daily XLS links; CDSL reports are FPI-only and do not supply DII. SEBI lists monthly transaction-level FPI equity archives with different grain from daily aggregated cash flows. | Useful free leads, not interchangeable with combined FII/DII. No XLS or monthly file downloaded. |
| FII/DII community mirrors | [johnwick3690/stocks](https://huggingface.co/datasets/johnwick3690/stocks), [MrChartist/fii-dii-data](https://github.com/MrChartist/fii-dii-data), [marketcalls/fii-dii-data](https://github.com/marketcalls/fii-dii-data) | HF CSV path and 503-line public diff are discovery clues only. Prior code review found the MrChartist repo can seed synthetic daily estimates from monthly/yearly totals, labelled `historical-seed`; those must be excluded. Other mirrors' README date claims conflict with tiny or aggregate-only files. | No source accepted; source-lineage and true daily coverage are not demonstrated. Do not fetch full history to “see if it works.” |
| Global equity leads | Existing manifest's Yahoo fallback symbols for S&P 500, Nasdaq, Nikkei and Hang Seng; [Stooq](https://stooq.com/) as secondary fallback | Run #44 had prior artifact coverage, but no raw global CSVs are committed in the data cache and the run's global series reported cache misses. Stooq was previously secondary-only due intermittent/truncated CI retrieval. | Historical reference only; local cache and terms are not established. |
| Cboe VIX | [Cboe VIX historical data](https://www.cboe.com/tradable_products/vix/vix_historical_data) | Official page advertises daily VIX close values from 1990 to present; custom VIX options/futures are separate products. | Public daily-index lead, license/automated retrieval timing still needs review. |
| USD/INR | [RBI reference-rate archive](https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx) | Official archive is registered as a daily source; no row-level date/schema or exact publication-time sample in this pass. | Primary-source lead; timing/missingness unverified. |
| US rates | [US Treasury daily-rate XML feed](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) | Treasury documents an XML endpoint with year filters and pagination for all records. | Free official lead; release timing must be aligned to NIFTY decision times. |
| Crude oil | [EIA WTI daily price history](https://www.eia.gov/dnav/pet/hist/leafhandler.ashx?f=a&n=pet&s=rwtc) | EIA's public page displays daily/weekly/monthly/annual choices and history reaching back decades; it offers XLS download. | Official-source lead; release/publication lag needed. |
| Gold | [LBMA Gold Price](https://www.lbma.org.uk/prices-and-data/lbma-gold-price) | Existing registry identifies it as a gold benchmark, but LBMA pricing IP/redistribution terms may constrain use. | License gate required. Do not call it unrestricted open data; review free alternate proxies before paid data. |
| Historical news | [GDELT 2.0 archive](https://www.gdeltproject.org/), [DOC API notes](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) | GDELT 2.0 documentation describes historical data files beginning in 2015, whereas DOC API searches only a rolling three-month window. Data products may contain coded metadata rather than full article text. | Strong free archive lead; article-level source/ingestion times, language/revision coverage and terms remain unverified. No news/text fetched. |
| Corporate actions | [NSE corporate actions page](https://www.nse.in/static/investor-relations/corporate-actions), [NSE index FAQs](https://www.nseindia.com/static/products-services/indices-faqs) | Official pages show announcement and record dates. For index forecasts, use a consistent price-index versus total-return index definition; index methodology already accounts for constituent changes/corporate actions. | Optional, target-definition dependent; no action files downloaded. |
| NSE trading calendar/contract master | [NSE contracts](https://www.nseindia.com/static/products-services/equity-derivatives-contract-information) and official report archive | PPR-3 horizons require actual NSE sessions, historical expiry rules and effective-dated strike/lot-size/contract validity. No versioned exchange calendar or historical contract-master file is in current cache. | Required metadata, unverified; not a dataset accepted at this gate. |
| Kaggle | [Kaggle dataset catalogue](https://www.kaggle.com/) | This read-only search did not verify a dataset with adequate license, history, schema and provenance for the current frozen tasks. | No qualified candidate established; this is not proof none exist. Continue free-source discovery if needed. |

Public metadata supports several viable *leads*, especially official NIFTY index archives, the NSE UDiFF/legacy F&O archive, Treasury XML, Cboe VIX and EIA WTI history. It does **not** establish that any file has passed row-level validation, a source acquisition gate, legal retention review or point-in-time checks. Dataset-card row counts and README history claims are not treated as audited coverage.

### 3.3 Point-in-time (PIT), source-vintage and license findings

The repository's PIT policies are sound in principle and must remain the acceptance contract:
- values require `available_at <= decision_time`;
- no forward-filling through unavailable periods or interpolating missing option prices;
- historical option contracts and lot-size regimes must have existed at decision time;
- global closes use true local close times and conservative delay, with DST normalized to IST;
- FII/DII use actual publication time; default to next Indian session when not provable;
- news uses original publication and ingestion/availability timestamps; revisions do not rewrite past information;
- output manifests include source IDs, snapshot IDs and input/output hashes.

No live source was tested in this pass, so actual point-in-time timestamp completeness is not established for any new family. In particular, CDSL/SEBI FPI-only records are different data grains, provisional NSE aggregates can revise, mixed-provenance GitHub mirrors may contain synthetic daily estimates, and large public datasets still require license verification.

### 3.4 Sealed final-holdout boundary: not verified

The current repository's PPR-3 manifest and prior Run #44 tester report state that the final holdout remains unopened. The metadata-only tree search found **no dedicated machine-readable holdout boundary/manifest** containing a holdout dataset ID/hash, split ID, row-ID hash or timestamp boundary that can be checked without reading holdout values or labels. The current specification requires such a manifest but does not supply it.

Therefore the required metadata-only proof has **not** been achieved. PPR-4 cannot declare the eligible development panel safe, create a final fit manifest or authorize model use. It would be incorrect to invent a cutoff date from prose, assume the last 20% of the current file is the sealed holdout, or infer that “not opened” proves where the split lies.

## 4. Statistical analyses and results

No modeling data, labels, features or predictions were generated in this phase. Therefore predictive statistical analysis, model metrics, significance tests and inference are **not applicable** to PPR-4. The PPR-3 frozen candidate universe remains 1,188 possible cells but none is approved for fitting by this audit. The only results are source-readiness classifications and a cache inventory.

## 5. Discussion, strengths, limitations and conclusion

**Strengths:** the source audit keeps primary data providers distinct from community mirrors, separates FPI-only transaction-level sources from aggregate FII/DII flow inputs, recognizes the 2024 F&O format change, identifies candidate long-history options archives, documents the one-row local cache and respects the no-bulk-download rule.

**Limitations:** all source-history claims are documentation/README claims until a separate bounded source gate validates the files; no dates/rows were fetched for new sources, no license review is final, and publication/ingestion timestamps are mostly unverified. The holdout boundary has not been found as machine-readable metadata.

**Conclusion:** a finite source inventory of 32 entries is recorded in [`PPR4_SOURCE_AVAILABILITY_REGISTER.csv`](PPR4_SOURCE_AVAILABILITY_REGISTER.csv). Several viable free-source leads exist, so paid sources are not justified or pursued at this stage. However, no new data has been accepted, the local cache cannot support the paper-native coverage requirements, and PPR-4 is **blocked** by the absent machine-readable sealed-holdout boundary. No prediction strategy, performance result or profit claim follows from this audit.

## 6. Exact next steps

1. Use only read-only GitHub branch/tree/commit/approval metadata searches to locate the original holdout manifest or prior protected row-ID/hash artifact. Do not read holdout observations/labels.
2. If no genuine boundary artifact exists, record the gate as blocked and propose a separately reviewed way to create a new split/holdout before any outcomes are seen; do not invent a date boundary retroactively.
3. Continue documentation-only source searches for missing FII/DII, historical sentiment and open/licensed options data if valuable; update this register before any new acquisition proposal.
4. Only after the holdout metadata issue is resolved should a PPR-4 exact source manifest be resubmitted for tester review. Bulk dataset/model acquisition and every empirical execution remain blocked until a fresh exact-snapshot PASS.

**Developer → Tester:** Independently audit the 32-row source register and cache inventory, especially source grain, licenses, coverage claims, PIT risks and the missing holdout manifest. Decide whether read-only inventory is complete while explicitly keeping PPR-4 exit/model use blocked.

**Tester → Developer:** Do not accept any source or authorize acquisition/model execution; first locate a genuine holdout-exclusion metadata artifact without opening its values/labels, or formally maintain BLOCKED_GATE.
