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

## 2026-10-07 — Phase 2C global acquisition correction

- Hosted run exposed a free-source reliability problem: Stooq returned only two usable S&P 500 rows for the requested window.
- The project did not treat this as missing global data; it switched to Yahoo Finance's public chart endpoint as the primary free research reference, normalized the returned daily close series, and kept Stooq in the source registry as a fallback.
- The data remain a research reference only; no execution feed is assumed from this provider.

## 2026-10-07 — Phase 2C global source provenance correction

- Final audit review found that S25-S28 in the manifest still named Stooq even though the successful acquisition used Yahoo Finance.
- Corrected S25-S28 to the actual Yahoo Finance reference endpoints and retained Stooq as explicit S36-S39 fallbacks.
- Clarified Phase 2 gate semantics for India VIX/FII-DII: absence of historical publication timestamps triggers conservative quarantine rather than hidden look-ahead.
- One final hosted audit run is required after the provenance correction.

## 2026-10-07 — Phase 2 final gate passed

- Hosted run #104 completed successfully after the final global-provider provenance correction.
- Independent tester final gate: `research/gates/PHASE2_FINAL_TESTER.md` = PASS WITH SCOPED RESTRICTIONS.
- Phase 2 canonical data policy is now frozen: official NSE/BSE sources are primary; derived S08 is validation-only; S31 is quarantined; India VIX/FII-DII without historical publication timestamps are conservative next-session/exclusion inputs.
- Advanced to Phase 3: label definitions, baselines, and cost-aware directionability. No model optimization yet.

## 2026-10-07 — Phase 3 tester REQUEST_CHANGES and correction

- Tester rejected the first protocol draft because sigma units, triple-barrier construction and several baseline definitions were not fully deterministic.
- Corrected and froze: 20-observation same-frequency sigma, non-updating triple barriers, 5/20 moving averages, training-only 33/67 volatility-regime cut points, equal-weight global composite, exact breadth formula, and logistic L2/C=1/liblinear/max_iter=1000 specification.
- No baseline results have been inspected during this correction.
- Phase 3 remains gated pending independent tester re-review.

## 2026-10-07 — Phase 3 tester re-review 2 correction

- Tester identified a material horizon mismatch: a 5-minute label cannot use 20 one-hour decision-grid returns as its volatility reference.
- Corrected the protocol to use `sigma_H(t)`: the standard deviation of the preceding 20 non-overlapping H-length returns for each label horizon H.
- Triple-barrier crossing is now evaluated at the finest available post-decision observation frequency while keeping barriers fixed.
- Clarified option cost normalization so broker fees are not double-counted per lot.
- Phase 3 remains gated pending final tester re-review.

## 2026-10-07 — Phase 3 data execution workflow submitted

- Tester final protocol gate passed.
- Added official NIFTY 50 daily-history acquisition in 60-day chunks from 2020-01-01 through 2026-09-30 with hashing and PIT provenance.
- Added Hugging Face intraday research-reference discovery using HF_TOKEN; no derived intraday data is accepted until the selected files are independently validated.
- Added automatic/manual Phase 3 data workflow with cache.
- No B0-B11 performance results exist yet.

## 2026-10-07 — Phase 3 hosted-run validator failure and correction

- Hosted Phase 3 run failed before data acquisition because `validate_phase3_protocol.py` searched for lowercase `leakage` against a capitalized `Leakage rules` heading.
- This was a validator-only false failure, not a data or label defect.
- Corrected the validator to normalize the protocol text to lowercase before required-phrase checks.

## 2026-10-07 — Phase 3 regression-check false positive

- The new log-placeholder regression guard correctly caught a literal object-placeholder phrase inside the error description of its own previous correction row.
- The row was rephrased to avoid the literal token, and the validator was narrowed to detect actual whole-line corruption patterns rather than mentions of the error token in prose.

## 2026-10-07 — Phase 3 daily-data composite fallback

- Official bulk NSE daily index retrieval was not reliable in the hosted runner despite successful official option-archive access in Phase 2.
- Rather than stall the research, the daily NIFTY layer was switched to a free Yahoo Finance public chart backfill with mandatory overlap checks against official NSE archive files for 2024-07-05 and 2024-07-08.
- Yahoo is explicitly non-canonical/derived; provider provenance is retained, and official NSE remains preferred whenever directly available.
