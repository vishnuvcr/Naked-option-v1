# Tester Review — Modeling Readiness Implementation R5

**Date:** 2026-10-11  
**Role:** Tester branch review  
**Developer snapshot:** `phase-07-developer` at `cd01d1d9be96c12c8748364cb14a4d5247a9cdd2`  
**Reviewed blobs:**
- `scripts/modeling_readiness_preflight.py`: `f973ad103a6313f8eb010be29f02162b97472043`
- `tests/test_modeling_readiness_preflight.py`: `32fa066070d4d9ba24e2d9cc541295a760c1957f`
- `research/gates/MODELING_READINESS_REPORT_SCHEMA_R5_2026-10-11.json`: `119d5ac524a2833cbb484a62855e80818a8214e6`
- `.github/workflows/phase-07-modeling-readiness-synthetic.yml`: `bbe5fff39b7bf6e496338d81516581dcb24d36fb`

## Verdict

**REQUEST_CHANGES — synthetic implementation only.** GitHub Actions run [38149491353](https://github.com/vishnuvcr/Naked-option-v1/actions/runs/38149491353) succeeded: all nine unittest methods, deterministic self-test, and synthetic-only boundary check passed. This is not approval to inspect real data, fit/score/tune models, read holdout observations, request new data, or evaluate strategy P&L.

## Findings requiring correction

1. **Report schema is not a strong nested allowlist.** The top-level object rejects extra keys, but `target_statuses` and `feature_family_statuses` accept arbitrary nested JSON. This could permit row-level values or other prohibited data to be embedded under allowed top-level names. `sanitize_report` checks only top-level keys and does not enforce required keys/types/schema constraints. Before any real-data report is generated, define constrained nested schemas (fixed key/value types and no nested arbitrary payloads), validate the report against the schema, and test rejection of nested price/row-level values and malformed/missing required fields.

2. **Horizon iterable contract is inconsistent.** `map_session_horizons` accepts any `Iterable[int]` but iterates it once per session. A one-shot generator is consumed on the first session, so later sessions silently receive empty horizon maps. Materialize and validate the horizon list once, or narrow the accepted type and enforce it. Add a generator regression test and assert each session has the same requested horizon keys.

3. **Negative metadata counts can be misclassified as valid.** `validate_session_metadata` treats negative `unresolved_session_flags` and `spot_duplicate_keys` as falsy and may return PASS; negative count inputs must fail closed. Likewise reject negative train/validation counts explicitly in `validate_split`, with dedicated tests.

4. **Input tolerance validation is absent.** `direction_label` does not reject negative or non-finite tolerance values. A negative tolerance labels even identical prices as directional FLAT failure; reject invalid tolerance explicitly and add tests.

## Checks passed

- Workflow ran with read-only `contents: read` permissions and manual `workflow_dispatch`.
- The module exposes only `--self-test`; the workflow checks for no obvious data fetch, `read_csv`, or fit interface.
- Price labels use signed simple returns; OHLC inequalities and session-order checks are implemented.
- Holdout proof is fail-closed when the manifest is unverified.
- No empirical or trading result is claimed.

## Required resubmission

Developer must fix all findings on `phase-07-developer`, add regression tests, keep the schema report-only and synthetic-only, rerun the workflow, then submit exact current blob hashes for another tester review. No real-file feasibility audit is authorized by this decision.

**Tester → Developer:** Correct findings 1–4, rerun synthetic CI, and resubmit exact hashes.  
**Developer → Tester:** Keep all empirical gates closed; independently re-review the corrected snapshot before any further authorization.
