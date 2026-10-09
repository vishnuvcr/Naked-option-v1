# Independent Tester Review — Phase 7 Available-Data Extension After Hosted Run #37

**Decision: REQUEST CHANGES — empirical prediction execution NOT authorized**  
**Review date:** 2026-10-10  
**Role:** independent tester branch; static review of the current developer snapshot plus independent inspection of the hosted run record.  
**No prediction results were generated or accepted in this review.**

## Exact reviewed snapshot and CI evidence

- The hosted workflow is [Run #37 / 37990522933](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37990522933).
- Run head commit: `18773e828f19c0ff2e9fc1af437db6b8ef181739`.
- Current `phase-07-developer` head at review: `14656183f9977c94a178996943e027d09d4a483d`.
- GitHub compare between those commits reports only these four post-run changes: `research/STATUS.md`, `research/gates/PHASE7_AVAILABLE_GLOBAL_DEVELOPER_SUBMISSION.md`, `research/logs/CHAT_LOG.md`, and `research/logs/RESEARCH_LOG.md`. No protected code/spec/test/requirements/workflow path changed between the run and current developer head.
- Current workflow blob: `6eb5de6bbd1e3773160a8f65be7c2cc81e0178ce`. Current NIFTY acquisition blob: `66b0041f2989f5dc508524052f157d6544596d5f`.
- Hosted regression job `independent-fixture-regression`: **SUCCESS**.
  - 11/11 Phase 7 available-global regression checks passed.
  - 11/11 result-schema/panel validator regression checks passed.
  - The job printed SHA-256 hashes for all nine protected paths, including `scripts/acquire_nifty_daily_history.py`.
- Hosted authorization job completed successfully in fail-closed mode because no tester approval manifest was mirrored: it printed “No independent tester approval is mirrored; regression-only submission run.”
- Empirical job conclusion: **SKIPPED**. Thus this run demonstrates green regression fixtures and fail-closed behavior; it is not a prediction run and provides no empirical metric.

## Checks reviewed

1. The corrected specification, predictor, result validator and their regression files match the previously reviewed blobs, and the hosted logs now verify execution of both regression suites.
2. The current workflow includes the NIFTY acquisition script in its push path filter and protected SHA-256 inventory; the run's hash step explicitly hashed that script.
3. The Phase 7 scope remains prediction-only, uses the existing fixed horizons and no final untouched holdout, and does not open Phase 8.
4. The automatic cache action restores `data/cache/raw/phase3` and `data/cache/raw/global_history`; however, the NIFTY acquisition script defeats reuse of the restored NIFTY cache, as detailed below.

## Blocking finding — the NIFTY acquisition step does not reuse its cache

In `scripts/acquire_nifty_daily_history.py`, top-level execution calls `yahoo_daily()` and then `compare_spots(rows)` before writing `data/cache/raw/phase3/nifty50_daily.csv`. It does not first inspect an existing file/manifest, validate freshness and SHA-256, and reuse a valid cache. Consequently, the workflow cache can restore the file, but this script downloads the full Yahoo history and overwrites the file on every run. This conflicts with the repository's explicit cache-and-reuse requirement, adds unnecessary network dependency, and allows provider revisions to replace historical values on each execution.

The acquisition code is also executed at import time, which makes focused no-network cache-path tests difficult; the hosted regression currently tests the predictor and result validator, not this acquisition behavior.

### Required correction before empirical authorization

- Make the acquisition module import-safe, with network/write work called from an explicit `main()`.
- Before downloading, validate an existing NIFTY CSV and its manifest: required columns, date uniqueness/order, row and coverage floor, positive close values, source identity, file SHA-256, and an explicit freshness policy. Reuse the cached history when valid.
- Reacquire only when the cache is missing, stale, malformed, or hash-mismatched. Record which branch was taken and why in the source manifest.
- Add isolated regression tests showing: valid cache causes zero network calls; stale/invalid/hash-mismatched cache reacquires; missing manifest cannot silently bless a cache; and acquired output/manifest checksums agree.
- Add the new acquisition test file to the automatic workflow, protected hash set, and exact approval path set; pin any new dependencies if needed.
- Keep the provider-vintage limitation explicit. The cache policy should not claim that a provider snapshot is exchange-exact.

## Disposition

**REQUEST CHANGES. No empirical execution is authorized by this report.** The hosted regressions pass, but the missing cache-reuse contract is a reproducibility and governance defect. No approval JSON should be created, no predictions should be run, and Phase 8 must remain blocked until the correction receives a new independent review and a fresh green hosted regression run whose hashes match the exact reviewed snapshot.

**Tester → Developer:** Fix cache reuse and acquisition testability without changing the frozen prediction specification or model universe. Add the specific regression cases, update the workflow protected paths, and submit exact blobs for a fresh tester review.

**Developer → Tester:** Resubmit the corrected acquisition, focused tests and workflow with a hosted run URL, regression summaries and SHA-256 output. Do not proceed to empirical predictions until the tester returns an explicit fresh decision.


## Follow-up audit of the cache repair — 2026-10-10

**Current disposition remains REQUEST CHANGES; no empirical prediction run is authorized.**

### Exact code/test/hosted run reviewed

- Latest developer head at the time of audit: `080ce1c5b3728e804e77b9322d082074483f8aa1`.
- Acquisition script blob: `734c5ac1b5e4f193c5cc68ded8f717f83dff4a3d`.
- New acquisition test blob: `6ce43f99c2353a9876d3950d48f6dd3c40399ac6`.
- Workflow blob: `0cb6775fb3974bba701a74b2bf71655bc61ae2a8`.
- Hosted run: [Run #40 / 37992378927](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37992378927); head SHA `080ce1c5b3728e804e77b9322d082074483f8aa1`.
- Result: workflow completed successfully in fail-closed mode. The regression job reports **4/4 new NIFTY cache checks passed**, **11/11 predictor regressions passed**, and **11/11 result-validator regressions passed**. The authorization job correctly found no tester approval; the empirical prediction job was skipped.
- SHA-256 output for the newly protected items:
  - `scripts/acquire_nifty_daily_history.py`: `b1f8ca12e0a5e154bf78164180aaaffe73bf37805396c8fcc7be08dcd00c5244`
  - `scripts/test_acquire_nifty_daily_history.py`: `ff987970e6250a47889e2733bd699ba7e3ff8531fd0a551085e0fb071111be99`
  - `.github/workflows/phase-07-available-global.yml`: `e137ed819e5c2e16ac07ac0ba6e6fd8628e212485649dd307486edcdda2e7df3`

### New blocking findings from independent source review

1. **Exchange-timezone date conversion is not correct by construction.** The downloader maps every Yahoo timestamp using `datetime.fromtimestamp(timestamp, UTC).date()`, discarding Yahoo's `meta.exchangeTimezoneName`. The existing global-series downloader instead converts the UTC instant into the source's exchange timezone before deriving the session date. NIFTY should do likewise (expecting `Asia/Kolkata` if the provider metadata omits the field). Two official-date spot checks are useful but do not replace deterministic timestamp/timezone tests.

2. **The partial-current-day cutoff is applied in UTC rather than the exchange timezone.** Before the configured 18:30 IST completion time, `exclusive_end_date()` returns today's calendar date; the code then makes the period-2 instant midnight **UTC** on that date. If Yahoo's daily timestamp represents local midnight in India, today's row timestamp is earlier than that UTC cutoff and can still be returned before the daily bar is complete. Use a timezone-aware `Asia/Kolkata` start/end boundary for the chart query and enforce the same allowed maximum session date in cache validation.

3. **A cache with a current-date row is accepted before the data-availability cutoff.** `_validate_rows()` only checks age (0 through 7 calendar days); it accepts a same-day last row when run at noon IST even though the acquisition policy says not to admit that incomplete bar. It should reject any last session after `exclusive_end_date(now) - 1 day`.

4. **The manifest's official-source comparison is not reconciled against the cached CSV.** Cache validation checks the existence of two records with `within_1_point is True`, but does not verify that the manifest's Yahoo close matches the close in the CSV for that exact date, nor that `abs_diff` equals `abs(yahoo_close - official_close)` and is within tolerance. The negative cache tests currently mock an official close of 1.0 while the fixture CSV has a close around 10,000, and the acquisition still passes. Add cross-field validation and ensure tests use internally consistent comparisons; add a mismatch mutation that must invalidate cache.

### Required correction and re-review scope

- Convert Yahoo timestamps to the instrument's local exchange timezone using `result.meta.exchangeTimezoneName` with an explicit `Asia/Kolkata` fallback.
- Build chart period boundaries in `Asia/Kolkata`, not UTC. Preserve the conservative end-of-day cut-off.
- Enforce the maximum allowed session date consistently in both acquisition and cache validation, and test before/after cutoff cases.
- Validate official overlap records against the actual CSV closes and formula, not a Boolean alone.
- Extend acquisition tests for UTC-to-IST date mapping around midnight, pre-close omission of today's row, post-close permission of a complete same-day row, and inconsistent overlap-manifest rejection.
- Keep the new tests in workflow triggers, regression invocations, and protected hash/approval-path lists; then produce a fresh hosted run and request another exact-snapshot tester review.

### Final disposition

**REQUEST CHANGES — empirical execution NOT AUTHORIZED.** Run #40 verifies that the current synthetic regression cases execute successfully, but does not close the additional timezone/cutoff/overlap-validation findings. No predictions or prediction metrics were produced; the approval JSON must remain absent.

**Tester → Developer:** Correct the local-session conversion, cutoff and overlap reconciliation without changing the registered prediction scope or model universe. Add the required tests, run the automatic workflow, and submit its exact SHA-256 output for re-review.

**Developer → Tester:** After resubmission, independently verify the time-zone/date math and negative fixtures as well as the hosted test result; do not authorize the empirical run if any point-in-time or cache consistency finding remains open.
