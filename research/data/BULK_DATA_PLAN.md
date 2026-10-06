# Phase 2C Bulk Data Plan

## Goal

Build the canonical, point-in-time dataset needed before any directional model is allowed to run.

## Batch layout

| Batch | Years | Primary content | Exit evidence |
|---|---|---|---|
| B1 | 2019-2020 | NSE legacy NIFTY option EOD | download/coverage/hash/PIT report |
| B2 | 2021-2022 | NSE legacy NIFTY option EOD + intraday validation sources | same |
| B3 | 2023-2024 | NSE legacy + UDiFF boundary | same |
| B4 | 2025-2026 | NSE UDiFF NIFTY option EOD | same |
| B5 | full window | India VIX + global daily + rates | PIT/timestamp report |
| B6 | full window | FII/FPI/DII availability audit | publication-time report or quarantine |
| B7 | full window | intraday NIFTY + option source reconciliation | contract/date/price report |

## Official NSE daily archive rules

- Before 2024-07-08 use the legacy F&O bhavcopy archive.
- From 2024-07-08 use F&O-UDiFF Common Bhavcopy Final.
- The archive transition is independently confirmed in NSE's current derivatives report hub. citeturn933765search1

## Canonical storage

Raw files live in the GitHub Actions cache under `data/cache/raw/nse_year/<year>/`.

Compact NIFTY-only Parquet outputs live under the cache's derived layer and are referenced by immutable manifests. Full raw archives are not committed to Git unless redistribution terms clearly permit it.

## Per-batch acceptance

A year is not promoted until:
- every expected weekday is classified as acquired, exchange-holiday/non-trading, or unresolved;
- NIFTY rows parse into the canonical schema;
- duplicate contract keys are zero;
- core price/expiry/type fields are valid;
- snapshot hashes are recorded;
- unresolved dates are independently inspected;
- tester approves the batch.

## Source-priority rule

Official NSE is canonical. Derived/free datasets can fill gaps or validate independently, but never silently overwrite official values.

## No paid-source rule

A paid market-data provider is not considered until B1-B7 are either completed or documented as blocked after free-source attempts.
