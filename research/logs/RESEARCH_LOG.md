## 2026-10-07 — Phase 2B derived spot-data correction

- The revised LastPric corroboration threshold passed the practical price gate, but the workflow then stopped because the HF source did not contain usable spot values for the selected date/expiry.
- This is a secondary-source field-availability issue, not evidence that the option-price source is invalid.
- The reconciliation now reports the spot check explicitly as PASS/FAIL/unavailable and never forward-fills or fabricates a spot value.

## 2026-10-07 — Phase 2 resumed after user request

- Re-read the project status, research plan/protocol, method registry, error log, research log, README and tester status before continuing.
- Observed real hosted Phase 2 failures rather than bypassing them: fixed-offset timezone parsing, partial active-contract coverage, and option LastPric corroboration/spot-field issues were all logged and corrected or quarantined.
- Added S31 (`artist-23/nifty-options-data`) as a second independent free NIFTY option reference to reduce dependence on one derived dataset.

## 2026-10-07 — Phase 2 S31 schema correction

- The first S31 test showed that the WEEK/ATM_CE and WEEK/ATM_PE files do not expose an explicit expiry column.
- This was not treated as a data failure: the contract family is encoded by the source file path, and the specific weekly expiry is taken from the official selected-expiry fixture for the same historical date.
- The reconciliation was changed to make that inference explicit and auditable rather than pretending an absent field existed.

## 2026-10-07 — Phase 2 S31 rerun checkpoint

- S31 schema correction is committed.
- No further developer changes will be made until the resulting hosted workflow completes, so the data gate can be evaluated on a single stable commit.

## 2026-10-07 — Phase 2C source-completion package

- Added actual free global daily reference acquisition (S&P 500, Nasdaq Composite, Nikkei 225, Hang Seng) with cached CSV snapshots, hashes and conservative next-session availability semantics.
- Corrected the official U.S. Treasury historical-rate endpoint after the endpoint probe returned 404.
- Added effective-dated NIFTY lot-size validation using the official UDiFF sample.
- Added live official NSE India VIX and FII/DII snapshot acquisition with explicit availability rules.
- Phase 2 final gate remains pending tester review and hosted execution of these new source checks.

## 2026-10-07 — Phase 2C workflow wiring

- Wired global reference acquisition, effective-dated lot-size validation, India VIX snapshot acquisition and FII/DII snapshot acquisition into the automatic/manual Phase 2 audit workflow.
- Extended the static validator and Phase 2 exit criteria to cover these source-completion checks.
- Next hosted run is the formal Phase 2C execution gate.

## 2026-10-07 — Phase 2C bulk/PIT gate implementation

- Froze the positional EOD window (2019-02-11 to 2026-09-30) and intraday executable window (2021-01-01 to 2026-09-30).
- Added year-by-year official NSE acquisition, compact NIFTY-only Parquet generation, India VIX historical acquisition, free global/rates history, lot-size history checks and a final bulk-data gate workflow.
- The workflow is matrixed by year, rate-limited, cached, manually dispatchable and uploads immutable validation artifacts.
- Historical combined FII/DII is explicitly quarantined rather than fabricated; current live snapshots remain available.

## 2026-10-07 — Phase 2C run #14 failure diagnosis and correction

- The hosted Phase 2C run reached real data acquisition successfully for all year jobs that entered parsing.
- 2019, 2022 and 2023 produced no canonical option rows because legacy NSE expiry dates were not ISO-formatted, so valid option rows were discarded during expiry parsing.
- 2024, 2025 and 2026 were flagged for invalid NIFTY option rows because the validator counted non-option NIFTY instruments (such as futures) as invalid; this was a validation-logic error, not evidence that those rows were malformed options.
- India VIX acquisition succeeded but validation parsed zero observations because the validator accepted only a narrow subset of date formats.
- The developer correction is deliberately limited to parsing/validation semantics; no acceptance threshold was relaxed.
- Phase 2 remains open pending the next hosted run and independent tester review.

## 2026-10-07 — Phase 2C correction rerun trigger

- After diagnosing run #14, the corrected parser/validator commit was moved onto the developer branch and a follow-up log commit was pushed solely to trigger the automatic Phase 2C workflow on the corrected tree.
- No phase transition is permitted from this rerun until the tester independently inspects the resulting artifacts.

## 2026-10-07 — Phase 2C run #17 global-source failure diagnosis

- All eight official NSE year jobs passed their acquisition, NIFTY extraction and validation steps on the corrected parser tree.
- India VIX validation passed on the corrected tree before the contextual job reached global acquisition.
- The contextual job failed in the global-series script because a source response contained no usable date rows and the script called min() on an empty list.
- This is treated as a source-response validation defect, not as evidence that the global source itself is unavailable.
- The developer correction switches the Stooq series to the same unbounded daily CSV pattern already used successfully in the earlier single-window source acquisition, then filters rows to the frozen research window locally and fails explicitly if no usable observations are present.
- Phase 2 remains open; the corrected global source path must complete before the gate can be resubmitted to the tester.

## 2026-10-07 — Phase 2C run #18 global-source fallback decision

- Run #18 reached the contextual job and failed explicitly because Stooq S25 returned no usable observations across the frozen window.
- The failure is isolated to the free global equity source path; official NSE year validation was still progressing independently.
- To honor the free-source-first rule, the global acquisition now uses a two-source free chain: Stooq first and Yahoo Finance chart API as fallback for S&P 500, Nasdaq Composite, Nikkei 225 and Hang Seng. FRED remains the US 10Y source.
- The global manifest/result records the selected provider and any failed source attempts so source substitution is auditable.
- This is a data-source robustness correction, not a relaxation of acceptance criteria. The research gate remains open until the fallback source completes and the tester reproduces the resulting hashes/date coverage.

## 2026-10-07 — Phase 2C run #19 free-source escalation

- Run #19 confirmed that Stooq S25 returned no frozen-window observations and the proposed Yahoo chart fallback returned HTTP 404 from GitHub Actions.
- The free-source-first rule was therefore extended to FRED public series before any consideration of paid data. FRED series candidates were predeclared for S&P 500, Nasdaq Composite, Nikkei 225 and Hang Seng; Yahoo remains the last free fallback.
- The global validator now requires every selected global/rates record to report a provider and non-zero numeric observations.
- Cache-hit metadata was also corrected so it reflects whether the selected raw file was actually read from an existing cache.
- No paid source has been introduced and no scientific threshold has been relaxed. The Phase 2 gate remains open pending a successful contextual run and tester reproduction.

## 2026-10-07 — Phase 2C run #20 Hang Seng source diagnosis

- Run #20 failed only at S28 (Hang Seng) after the free chain exhausted: long-window Stooq returned no observations, FRED candidates returned 404, and Yahoo returned 404.
- The earlier Stooq probe had worked on a short historical window, so the most conservative next free-source action is to preserve Stooq but request it in 180-day chunks, then merge the chunks by date with duplicate protection.
- No paid source has been tried. The FRED/Yahoo alternatives remain available as fallbacks.

## 2026-10-07 — Phase 2C Hang Seng free-data composite fallback

- Run #21 confirmed that the remaining S28 Hang Seng gap survives the Stooq chunked approach and the tested FRED/Yahoo endpoints.
- A public GitHub dataset was found containing daily Hang Seng close data from 1986 through 2026-05-28. The repository has no license file visible at its root, so this source is explicitly tagged research-only/license-unverified; it is not promoted to a canonical redistribution source.
- The acquisition script can use this source only as a fallback, retains the exact commit URL, hashes the cached bytes, and preserves the verified sub-window instead of padding the missing 2026-05-29 to 2026-09-30 interval.
- This satisfies the free-source-first requirement while keeping the residual coverage limitation visible for the tester and final manuscript.

## 2026-10-07 — Phase 2C run #22 CI-efficiency correction

- The verified HSI GitHub snapshot is deterministic and provenance-locked, while the tested live S28 endpoints have repeatedly returned no data or 404s.
- To prevent unnecessary CI time and repeated network failures, S28 now selects the fixed-commit GitHub dataset first and retains live feeds as fallback alternatives.
- The source's shorter verified tail remains explicit; no synthetic extension is introduced.

## 2026-10-07 — Phase 2C run #23 runtime correction

- Run #23 did not reach a data-quality conclusion because the global acquisition spent extended CI time on sequential Stooq window requests.
- Because FRED global equity series are predeclared and free, they are now attempted before Stooq for S25-S27. The deterministic fixed-commit HSI snapshot remains first for S28.
- Stooq and Yahoo remain free fallbacks. No acceptance threshold is changed; this is an execution-order optimization to make the finite Phase 2 gate complete reliably.
