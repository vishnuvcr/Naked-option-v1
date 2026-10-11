# Automated Independent Tester Report — NIFTY 1-Minute Composite

- Decision: PASS_WITH_SCOPED_RESTRICTIONS
- Reviewed developer commit: a9f7c38657b0635f7f06599674643acd7c6c79a3
- Report time (UTC): 2026-10-11T06:29:10Z
- Deterministic checks: PASS
- AI reviewer: REVIEWER_UNAVAILABLE / NO_VERDICT
- Automatic repair attempt: 1
- Single-request diagnostic authorized: NO
- Cache-preserving spot-only recovery authorized: NO
- General live requests authorized: NO
- Model fitting authorized: NO
- Holdout access authorized: NO

## Deterministic findings

- INFO — SPOT_OHLC_STRICT_VOLUME_DEGRADED: Timestamp/OHLC arrays remain mandatory and aligned; unusable volume stays blank and is quality-flagged.
- INFO — SANITIZED_DIAGNOSTIC_PRESENT: Unexpected validation errors retain a bounded reason token without logging payload bodies.
- INFO — SPOT_DIAGNOSTIC_EXACT_SCOPE_PASS: The one-request diagnostic scope is pinned to the frozen request manifest and writes only sanitized metadata.
- INFO — SPOT_ARTIFACT_PRESERVING_GAPFILL_SCOPE_PASS: The gapfill uses the immutable encrypted acquired dataset, validates the 8,490,723 option rows, requests only 47 Dhan spot shards, joins by exact timestamp and re-encrypts outputs; no live option refetch is enabled.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: missing-volume response.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: empty-volume response.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: misaligned volume array.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: invalid timestamp types.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: separate OHLC misalignment.
- INFO — REGRESSION_CASE_PRESENT: Regression coverage exists: sanitized parser-reason logging.

## Offline test summary

- PASS: python -m py_compile scripts/run_nifty_1m_composite_dataset.py scripts/decrypt_nifty_1m_composite.py scripts/validate_nifty_1m_composite_manifest.py scripts/test_nifty_1m_composite_dataset.py scripts/test_nifty_1m_composite_manifest.py scripts/validate_nifty_1m_composite_approval.py scripts/run_nifty_1m_spot_diagnostic.py scripts/test_nifty_1m_spot_diagnostic.py scripts/audit_nifty_1m_composite_cache.py scripts/account_nifty_1m_probe_attempt.py scripts/test_account_nifty_1m_probe_attempt.py scripts/test_audit_nifty_1m_composite_cache.py scripts/run_nifty_1m_spot_gapfill.py scripts/test_nifty_1m_spot_gapfill.py (exit 0)
- PASS: python -m unittest -v test_nifty_1m_composite_manifest (exit 0)
- PASS: python -m unittest -v test_nifty_1m_composite_dataset (exit 0)
- PASS: python -m unittest -v test_nifty_1m_spot_diagnostic (exit 0)
- PASS: python -m unittest -v test_account_nifty_1m_probe_attempt (exit 0)
- PASS: python -m unittest -v test_audit_nifty_1m_composite_cache (exit 0)
- PASS: python -m unittest -v test_nifty_1m_spot_gapfill (exit 0)

## Independent AI review

AI reviewer unavailable; no independent AI verdict was produced.

- WARNING — automation/nifty_composite_agent.py: RuntimeError: Hugging Face inference returned HTTP 402 Required: Restore HF Inference Provider access and rerun the workflow.

## Gate scope

This report applies only to the exact developer commit named above. Any enabled action is bounded to the separate scope booleans in the machine-readable decision: one non-persisting spot diagnostic, or a later cache-verified spot-only recovery with zero live option refetches. The general live-request permission remains false. No modeling, strategy tests or holdout use is authorized.

When AI inference is unavailable, a passing deterministic suite is not an AI verdict. A limited action may proceed only when the tester's deterministic scope check explicitly passes the exact request plan, runner, tests, and workflow. No broader permission is inferred.

Only action summaries and findings are retained; private model reasoning is not written to the repository.
