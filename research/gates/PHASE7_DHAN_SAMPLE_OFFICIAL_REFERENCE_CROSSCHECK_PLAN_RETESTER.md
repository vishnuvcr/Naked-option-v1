# Independent Tester Re-review — Official Reference Cross-Check Plan

**Decision: REQUEST CHANGES — plan-only defect; no network request is authorized.**

**Reviewed developer proposal commit:** `8eb197afa31bf6970441e235f79b95d719819098`  
**Proposal blob:** `4da1809ccd00e8fea00356cac0754666feae1568`  
**Affected file:** `research/phase7/DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN.md`

## Finding: compact CSV segment field is not the API exchangeSegment enum

The proposal's acceptance criterion 4 requires a row with `SEM_SEGMENT=IDX_I`. Dhan's own instrument-list documentation describes `SEM_SEGMENT` as a compact segment code and lists `C` (Currency), `D` (Derivatives), `E` (Equity), and `M` (Commodity). Separately, the Dhan API Annexure maps `IDX_I` to the API-level exchange segment "Index / Index Value". Those are distinct namespaces. The proposal's current direct equality condition is unsupported and likely wrong.

Official sources:
- Instrument list field mapping and compact CSV: https://dhanhq.co/docs/v2/instruments/
- API exchangeSegment enum: https://dhanhq.co/docs/v2/annexure/

## Required correction

Revise the plan so the CSV mapping check:
1. selects the candidate row by the actual compact master Security ID column and symbol/instrument fields available in the official CSV schema;
2. checks exchange, instrument-name, symbol/display name, and any exchange instrument-type fields required to show the row is the NIFTY 50 index, if present;
3. treats `IDX_I` as a separate API enum which is verified by the official Annexure, not as the expected literal `SEM_SEGMENT` value;
4. does not infer an acceptable mapping solely from `SEM_SEGMENT` or a string resemblance;
5. fails closed if the public master has no unique index row or if the published fields cannot substantiate the mapping.

The plan should also avoid requiring `SEM_SEGMENT=IDX_I` in examples or implementation tests. Update the developer plan's commit/blob pin before implementation. No live request, token use, cache change, model fit, predictor rerun, or holdout access is allowed at this gate.

**Tester → Developer:** Correct the plan and submit the new exact proposal blob for an independent re-review. Do not start implementing the live connector until the revised plan returns PASS. Keep the already-spent Dhan one-use manifest untouched.
