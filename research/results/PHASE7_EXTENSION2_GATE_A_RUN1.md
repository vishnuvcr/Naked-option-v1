# Phase 7 Extension 2 — Gate A Source Feasibility Run #1

**Workflow:** [Run #1](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38019391488)  
**Artifact:** `phase7-extension2-gate-a-source-feasibility`, ID `11657980203`  
**Report JSON SHA-256:** `b39b7edce155a1ce0851186fff3f84d781474d89b5d3630831bcbf4f6df473b9`  
**Independent tester decision:** REQUEST CHANGES — source feasibility incomplete.  
**Scope:** bounded samples only; no full history, labels, features, model fitting or prediction metrics.

## F&O archive samples — both official URLs passed

| Sample | Source URL | HTTP | ZIP SHA-256 | CSV rows | Columns | Distinct dates | NIFTY option rows | Result |
|---|---|---:|---|---:|---:|---:|---:|---|
| Legacy F&O, 2024-07-05 | https://archives.nseindia.com/content/historical/DERIVATIVES/2024/JUL/fo05JUL2024bhav.csv.zip | 200 | `a6ba5c9f48555b4adb21c199bb2f9cd100eb2ebf05fc25b1a91feea71020474b` | 33,930 | 16 | 1 | 1,634 | PASS |
| UDiFF F&O, 2024-07-08 | https://archives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv.zip | 200 | `af47c5b8b6e0ac02da4d5a4d22d46d73527d81552a93aba99ae91590b8549d76` | 34,390 | 34 | 1 | 1,634 | PASS |

The official legacy archive has 16 columns and includes `INSTRUMENT/SYMBOL/EXPIRY_DT/STRIKE_PR/OPTION_TYP/CLOSE/CONTRACTS/OPEN_INT/TIMESTAMP`. UDiFF has 34 columns and includes `TradDt/Sgmt/TckrSymb/XpryDt/StrkPric/OptnTp/ClsPric/TtlTradgVol/OpnIntrst`. All rows in each sample matched the requested trade date. This confirms official archive access and a real schema boundary; full-history transition consistency is not yet proven.

## FII/DII sample

The official NSE `/api/fiidiiTradeReact` endpoint returned two current records for 2026-10-09 with keys `date`, `category`, `buyValue`, `sellValue`, and `netValue`. SHA-256 of response: `295b6c4e37225f9dea0f662d82c45efc76ea00818e38d9c57acb918f7ddd042b`. This endpoint sample verifies current schema/access, not historical coverage.

A free GitHub mirror, [MrChartist/fii-dii-data](https://github.com/MrChartist/fii-dii-data/blob/main/data/history.json), currently has 164 unique dated records from 2026-01-14 to 2026-09-30. It is not enough for the preregistered 500-common-date family inference and is not an official source. Additional free historical sources must be explored; historical data must not be declared unavailable yet.

## Sector and breadth source results

- The attempted NSE API URL `/api/historical/indicesHistory?... ` returned a generic HTML page, not historical JSON; that specific endpoint attempt is not usable.
- Official NSE pages for all reports and Advances/Declines were fetched, but the bounded sampler found only static page tables, not historical dated rows.
- A better official sector-history lead has been identified: NSE daily index archive CSV `https://archives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv`. This was not included in Run #1 and must be sampled in the next iteration.
- For breadth, the official daily equity bhavcopy is a possible free fallback from which to derive a fixed-universe daily advance/decline measure, but the feature definition must be versioned and independently approved before changing G17.

## Tester disposition and next step

The [independent tester report](https://github.com/vishnuvcr/Naked-option-v1/blob/phase-07-tester/research/gates/PHASE7_AVAILABLE_GLOBAL_EXTENSION2_SOURCE_FEASIBILITY_RUN1_TESTER.md) is **REQUEST CHANGES**. F&O archive feasibility passed; sector, breadth and historical FII/DII coverage remain unresolved.

Next bounded iteration:
1. Sample two official `ind_close_all` daily index CSVs and validate the ten frozen sector index identities plus NIFTY 50.
2. Sample two daily equity bhavcopy dates to assess a possible derived-breadth fallback.
3. Search additional free historical FII/DII sources (GitHub, Kaggle, Hugging Face, public data portals and historical reports); record date coverage, units, source lineage and overlap with official NSE values.
4. Keep all downloads bounded to individual sample dates or metadata; do not fetch full history, build a feature panel or fit a model.

**Developer → Tester:** Review the next exact sampler before its workflow runs, then independently audit the source sample artifact.

**Tester → Developer:** Full-history acquisition and model fitting remain NOT AUTHORIZED until Gate A is passed and any G17 source-definition change is independently approved.
