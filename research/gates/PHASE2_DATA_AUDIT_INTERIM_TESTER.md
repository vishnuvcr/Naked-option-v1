# Phase 2 Data Audit Interim Tester Report

## Observed hosted run

Run #85 on `phase-02-developer` completed all CI steps successfully, including official NSE sample acquisition, PIT fixture, source/global endpoint probes, HF acquisition, primary derived-source reconciliation and S31 secondary-source evaluation.

## Numerical evidence inspected

### Official NSE sample snapshots

- 2024-07-05 legacy archive: 33,930 data rows; SHA-256 recorded.
- 2024-07-08 UDiFF archive: 34,390 data rows; SHA-256 recorded.
- Both archives were cache hits on the successful run.

### Primary derived corroboration — S08

- Selected file: `options/NIFTY/2024-07-11.parquet`.
- Official active target-expiry contracts: 192.
- Predeclared validation-band contracts: 96.
- Derived source validation-band contracts: 96.
- Two-way key coverage: 100%.
- Strict 0.25%/tick agreement: 95.8333%.
- Practical 1% relative agreement: 97.9167%.
- Median relative error: 0.
- Maximum relative error: about 2.8037%.
- Official `ClsPric` agreement is materially lower (31.25%) and is retained only as a diagnostic.
- Derived spot field was unavailable; no spot was fabricated or forward-filled.

This passes the developer's **secondary corroboration** rule but does not establish exact price identity.

### Secondary S31 candidate

The `artist-23/nifty-options-data` ATM files were acquired, but its selected parquet schema did not expose an expiry field and the S31 reconciliation therefore had zero comparable keys. This source is **NOT_COMPARABLE** and must not be treated as validation evidence until its contract/expiry semantics are demonstrated.

### Global endpoint evidence

- Cboe VIX, RBI, LBMA, EIA, Stooq, NSE sector and breadth endpoints returned HTTP 200 in the probe.
- US Treasury URL returned HTTP 404 and requires a corrected official endpoint before use.
- This is endpoint availability, not historical-data acquisition.

## Tester gate status

**PHASE 2 DATA AUDIT: INCOMPLETE**

The main option/PIT audit has meaningful positive evidence, but the overall Phase 2 exit criteria are not all green.

## Required Phase 2 completion work

1. Add an actual global reference acquisition (at least one free global index series) with timezone/availability fields and a SHA-256 snapshot.
2. Demonstrate historical NIFTY option lot-size mapping from an official effective-dated field/source.
3. Demonstrate an India VIX historical snapshot aligned to a decision date.
4. Demonstrate FII/FPI/DII data availability timing with conservative publication handling.
5. Correct or quarantine the US Treasury source until a working official URL is identified.
6. Keep S31 marked NOT_COMPARABLE unless its expiry semantics are independently established.
7. Add a final Phase 2 gate report only after these checks are independently reproducible.

## Tester instruction to developer

Complete Phase 2C data acquisition and provenance work, then resubmit the final data gate. Do not create Phase 3 label/model branches until the final tester PASS.
