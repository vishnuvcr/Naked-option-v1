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
