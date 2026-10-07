# Phase 3 Data-Execution Tester Review — REQUEST CHANGES

## Review target

Developer branch `phase-03-developer`, head commit `513f1c211055b11e56107b0b2128015682cfc425`.

This is an independent tester audit of the empirical-execution package after the protocol gate passed.

## Gate decision

**REQUEST CHANGES — Phase 3 data/empirical gate is NOT passed.**

No Phase 4 method search or strategy promotion is permitted.

## Material findings

| Area | Result | Finding |
|---|---|---|
| Protocol CI | FAIL on current developer head | `research/logs/RESEARCH_LOG.md` begins with literal `[object Object]`; the protocol validator correctly stopped the run. The error log claims this was restored, but the current branch still contains the corruption. |
| Workflow completeness | FAIL | `.github/workflows/phase-03-labels-baselines.yml` validates the protocol and acquires daily/HF discovery artifacts, but it does **not** execute `acquire_hf_intraday_sample.py`, `run_phase3_daily_baselines.py`, `run_phase3_intraday_baselines.py`, or `persist_phase3_results.py`. Therefore no B0-B11 empirical result packet can be produced by this workflow. |
| B0-B11 completeness | FAIL | Daily results currently implement only B0, B1, B2, B5, B6, B7, B8 and B11. B3, B4, B9 and B10 are absent from the result-generating code. Intraday similarly omits B1/B2/B9/B10. This does not satisfy the frozen B0-B11 baseline gate. |
| Intraday B3 | FAIL | `base_preds(..., "B3")` maps the previous session's first observation (`groupby(...).first()`) as the prior close. This is the previous session **open**, not previous session close. |
| Intraday B4 semantics | REQUEST | The frozen protocol defines momentum from the most recent 5/15/30-minute return. The implementation uses the current label horizon (5/15/30/60/120) as the momentum window, so the 60/120-minute cases no longer match the registered B4 definition. |
| Logistic B11 feature contract | FAIL | The frozen protocol specifies last return, rolling volatility, gap, PIT-safe India VIX, PIT-safe global overnight composite and breadth where available. The implementation instead uses a different expanded feature set and omits the registered global/breadth/VIX layers. This is a protocol/code mismatch, not an acceptable discretionary variant. |
| PIT validation of intraday reference | FAIL | `acquire_hf_intraday_sample.py` pins a dataset revision and validates schema, but it does not demonstrate overlap against official NSE data as required by the Phase 3 data requirements. |
| Workflow result gate | FAIL | `persist_phase3_results.py` is present but not invoked by the workflow, so the declared `PHASE3_DATA_RUN.md` evidence packet is not generated. |
| Status accuracy | FAIL | Developer README/STATUS says Phase 3 execution is underway, but the current workflow has only completed protocol/data acquisition checks; empirical baseline execution has not been run from the workflow. |

## Required developer corrections

1. Restore `research/logs/RESEARCH_LOG.md` from the last canonical non-corrupted developer log, then append the current Phase 3 correction entry. Do not remove the historical errors.
2. Update the Phase 3 workflow so the automatic push/manual run performs, in order: protocol validation; canonical daily acquisition; intraday discovery; intraday sample acquisition; B0-B11 baseline scripts; result persistence; and an explicit result-schema validator. Keep caching and manual dispatch.
3. Make B0-B11 coverage explicit. A baseline that is genuinely impossible because of a documented missing data layer must be emitted as `BLOCKED_DATA` with a source-gap artifact, not silently omitted.
4. Correct B3 to use the previous session's last observation as previous close.
5. Freeze and implement B4 exactly as registered, or amend the protocol on the developer branch before execution; do not silently change the method definition.
6. Align B11 feature construction to the frozen protocol. If breadth/global/VIX are unavailable, document the exact source gap and mark that baseline component blocked rather than replacing it with unregistered features.
7. Add an official-NSE overlap check for the selected intraday research reference and record the exact dates, tolerance, provenance and result.
8. Invoke `persist_phase3_results.py` and require its gate artifact before the workflow can be green.

## Tester instruction to developer

Resubmit the corrected Phase 3 data-execution package on `phase-03-developer`. Do not begin Phase 4. After the fresh run completes, the tester will independently reconstruct labels and B0-B11 metrics from the resulting immutable artifacts.
