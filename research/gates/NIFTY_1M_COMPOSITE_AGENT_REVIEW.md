# Automated Independent Tester Report — NIFTY 1-Minute Composite

- Decision: PASS_WITH_SCOPED_RESTRICTIONS
- Reviewed developer commit: 6ea695600d08c8768e3bcce2a0217111d8ef577e
- Report time (UTC): 2026-10-11T05:19:24Z
- Deterministic checks: PASS
- AI reviewer: REVIEWER_UNAVAILABLE / NO_VERDICT
- Automatic repair attempt: 1
- Live requests authorized: NO
- Model fitting authorized: NO
- Holdout access authorized: NO

## Deterministic findings

- INFO — SPOT_RESPONSE_FIELDS_REQUIRED: Spot parser requires timestamp, OHLC, and volume arrays, consistent with Dhan's documented response shape.
- INFO — SANITIZED_DIAGNOSTIC_PRESENT: Unexpected validation errors retain a bounded reason token without logging payload bodies.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: missing-volume response.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: empty-volume response.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: misaligned volume array.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: invalid timestamp types.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: separate OHLC misalignment.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: sanitized parser-reason logging.

## Offline test summary

- PASS: python -m py_compile scripts/run_nifty_1m_composite_dataset.py scripts/decrypt_nifty_1m_composite.py scripts/validate_nifty_1m_composite_manifest.py scripts/test_nifty_1m_composite_dataset.py scripts/test_nifty_1m_composite_manifest.py scripts/validate_nifty_1m_composite_approval.py (exit 0)
- PASS: python -m unittest -v test_nifty_1m_composite_manifest (exit 0)
- PASS: python -m unittest -v test_nifty_1m_composite_dataset (exit 0)

## Independent AI review

AI reviewer unavailable; no independent AI verdict was produced.

- WARNING — automation/nifty_composite_agent.py: RuntimeError: Hugging Face inference returned HTTP 402 Required: Restore HF Inference Provider access and rerun the workflow.

## Gate scope

This report applies only to the exact developer commit named above. PASS does not create or spend the separate one-use acquisition approval; the acquisition workflow, request manifest, approval file, and scope checks remain mandatory. This report cannot authorize source requests, modelling, strategy tests, or holdout access.

When AI inference is unavailable, a passing deterministic suite is a scoped offline code-gate PASS only; it is not a full AI review, acquisition approval, or scientific result. No live request, model fitting, strategy test or holdout access is authorized.

Only action summaries and findings are retained; private model reasoning is not written to the repository.
