#!/usr/bin/env python3
"""Offline unit tests for the Dhan daily sample manifest validator."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
spec = importlib.util.spec_from_file_location(
    "validate_dhan_daily_sample_approval", SCRIPTS / "validate_dhan_daily_sample_approval.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

REPORT_BYTES = (
    "# Tester approval\n\n"
    "PASS WITH SCOPED RESTRICTIONS\n"
    + mod.SCOPE_ID + "\n"
    "No live request is authorized. No bulk retrieval is allowed.\n"
).encode()


def valid_manifest() -> dict:
    protected = {
        path: {"git_blob": hashlib.sha1(path.encode()).hexdigest(),
               "sha256": hashlib.sha256(path.encode()).hexdigest()}
        for path in mod.REQUIRED_PROTECTED_FILES
    }
    authorization = {
        "scope_id": mod.SCOPE_ID,
        "authorized_scope": "one tiny daily NIFTY 50 index-history request only",
        "source_url": mod.DAILY_URL,
        "method": "POST",
        "request_body": json.loads(json.dumps(mod.REQUEST_BODY)),
        "requests_max": 1,
        "response_bytes_max": 2 * 1024 * 1024,
        "timeout_seconds": 20,
        "credential_host": "api.dhan.co",
        "credential_header": "access-token",
        "redirect_follow_allowed": False,
        "retry_allowed": False,
        "full_history_authorized": False,
        "intraday_authorized": False,
        "rolling_options_authorized": False,
        "feature_engineering_authorized": False,
        "model_fitting_authorized": False,
        "strategy_testing_authorized": False,
        "holdout_access_authorized": False,
        "reviewed_developer_commit": "a" * 40,
        "protected_files": protected,
    }
    return {
        "schema_version": 1,
        "status": "PROPOSED",
        "decision": "AWAITING_INDEPENDENT_MANIFEST_REVIEW",
        "authorization": authorization,
        "authorization_sha256": mod.canonical_sha256(authorization),
    }


def must_raise(call, expected: str) -> None:
    try:
        call()
    except ValueError as exc:
        assert str(exc) == expected, (str(exc), expected)
    else:
        raise AssertionError(f"expected {expected}")


def valid_approval(manifest_raw: bytes) -> dict:
    return {
        "status": "READY",
        "decision": "APPROVED_ONE_RUN",
        "scope_id": mod.SCOPE_ID,
        "request_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "request_manifest_git_blob": "c" * 40,
        "approved_authorization_sha256": mod.canonical_sha256(valid_manifest()["authorization"]),
        "tester_report_sha256": hashlib.sha256(REPORT_BYTES).hexdigest(),
        "tester_report_git_blob": "d" * 40,
    }


def test_live_workflow_secret_guard_precedes_spend_and_fetch() -> None:
    workflow_path = ROOT / ".github/workflows/phase-07-dhan-daily-sample-live.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    secret_guard = workflow.index("Confirm Dhan token secret is configured without exposing it")
    manifest_check = workflow.index("Validate exact approved manifest and tester report")
    spend = workflow.index("Spend one-use approval before the single market-data request")
    fetch = workflow.index("Execute one validated daily NIFTY history request")
    assert secret_guard < manifest_check < spend < fetch
    guard_slice = workflow[secret_guard:manifest_check]
    assert "DHAN_TOKEN_CONFIGURED: ${{ secrets.DHAN_ACCESS_TOKEN != '' }}" in guard_slice
    assert "Blocked before spending the one-use approval" in guard_slice
    spend_slice = workflow[spend:fetch]
    assert "python scripts/validate_dhan_daily_sample_approval.py spend" in spend_slice
    assert "git push origin HEAD:phase-07-developer" in spend_slice
    fetch_slice = workflow[fetch:workflow.index("Commit validated public sample cache")]
    assert "DHAN_ACCESS_TOKEN: ${{ secrets.DHAN_ACCESS_TOKEN }}" in fetch_slice
    assert "DHAN_DAILY_SAMPLE_AUTHORIZED: \"1\"" in fetch_slice
    assert "continue-on-error: true" in fetch_slice
    assert "retry" not in fetch_slice.lower()
    assert "contents: write" in workflow


def test_live_workflow_has_manual_confirmation_and_no_redirect_follow() -> None:
    workflow = (ROOT / ".github/workflows/phase-07-dhan-daily-sample-live.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "confirm_live_sample:" in workflow
    assert "default: false" in workflow
    assert "steps.spend_manifest.outcome == 'success'" in workflow
    assert "redirect" in workflow.lower()
    assert "retry" in workflow.lower()
    assert "DHAN_ACCESS_TOKEN" in workflow


def test_module_import_does_not_contact_network() -> None:
    assert mod.DAILY_URL == "https://api.dhan.co/v2/charts/historical"
    assert mod.REQUIRED_PROTECTED_FILES
    assert mod.REQUEST_BODY["toDate"] == "2024-01-03"


def test_valid_manifest_structure_passes() -> None:
    mod.validate_manifest_structure(valid_manifest())


def test_manifest_cannot_widen_endpoint_method_or_request_body() -> None:
    m = valid_manifest()
    m["authorization"]["source_url"] = "https://evil.example/data"
    m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
    must_raise(lambda: mod.validate_manifest_structure(m), "source_endpoint_mismatch")

    m = valid_manifest()
    m["authorization"]["request_body"]["toDate"] = "2024-02-01"
    m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
    must_raise(lambda: mod.validate_manifest_structure(m), "request_body_mismatch")


def test_manifest_cannot_widen_request_bytes_timeout_or_count() -> None:
    for field, value, expected in [
        ("requests_max", 2, "request_budget_mismatch"),
        ("response_bytes_max", 16 * 1024 * 1024, "request_budget_mismatch"),
        ("timeout_seconds", 200, "request_budget_mismatch"),
    ]:
        m = valid_manifest()
        m["authorization"][field] = value
        m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
        must_raise(lambda m=m, expected=expected: mod.validate_manifest_structure(m), expected)


def test_manifest_cannot_enable_forbidden_research_scope() -> None:
    for field in (
        "redirect_follow_allowed", "retry_allowed", "full_history_authorized",
        "intraday_authorized", "rolling_options_authorized", "feature_engineering_authorized",
        "model_fitting_authorized", "strategy_testing_authorized", "holdout_access_authorized",
    ):
        m = valid_manifest()
        m["authorization"][field] = True
        m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
        must_raise(lambda m=m: mod.validate_manifest_structure(m), "forbidden_scope_flag")


def test_manifest_requires_exact_protected_files_and_sha_formats() -> None:
    m = valid_manifest()
    m["authorization"]["protected_files"].pop(next(iter(m["authorization"]["protected_files"])))
    m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
    must_raise(lambda: mod.validate_manifest_structure(m), "protected_file_set_mismatch")

    m = valid_manifest()
    key = sorted(m["authorization"]["protected_files"])[0]
    m["authorization"]["protected_files"][key]["sha256"] = "not-a-hash"
    m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
    must_raise(lambda: mod.validate_manifest_structure(m), "protected_file_sha256_invalid")


def test_manifest_digest_and_decision_must_match() -> None:
    m = valid_manifest()
    m["authorization_sha256"] = "0" * 64
    must_raise(lambda: mod.validate_manifest_structure(m), "authorization_digest_mismatch")
    m = valid_manifest()
    m["status"] = "READY"
    must_raise(lambda: mod.validate_manifest_structure(m), "request_manifest_status_invalid")


def test_spend_transition_populates_runner_required_scope_and_is_one_use() -> None:
    ready = valid_approval(b"dummy manifest")
    ready["status"] = "READY"
    ready["decision"] = "APPROVED_ONE_RUN"
    spent = mod.prepare_spent_approval(ready, spent_from_commit="e" * 40)
    assert spent["status"] == "SPENT"
    assert spent["decision"] == "SPENT_BEFORE_SOURCE_REQUEST"
    assert spent["scope_id"] == mod.SCOPE_ID
    assert spent["authorized_scope_id"] == mod.SCOPE_ID
    assert spent["spent_from_commit"] == "e" * 40
    assert ready["status"] == "READY"  # input document is not mutated
    must_raise(lambda: mod.prepare_spent_approval(
        spent, spent_from_commit="f" * 40
    ), "approval_already_spent_or_not_ready")
    must_raise(lambda: mod.prepare_spent_approval(
        {**ready, "scope_id": "another-scope"}, spent_from_commit="f" * 40
    ), "approval_scope_id_mismatch")
    must_raise(lambda: mod.prepare_spent_approval(
        ready, spent_from_commit="not-a-commit"
    ), "spent_from_commit_invalid")


def test_valid_ready_or_spent_approval_report_passes() -> None:
    m = valid_manifest()
    raw = json.dumps(m, sort_keys=True, indent=2).encode() + b"\n"
    approval = valid_approval(raw)
    for status in ("READY", "SPENT"):
        approval["status"] = status
        mod.validate_approval_structure(
            approval, manifest_sha256=hashlib.sha256(raw).hexdigest(),
            manifest_git_blob="c" * 40, tester_report_bytes=REPORT_BYTES,
            tester_report_git_blob="d" * 40,
        )


def test_approval_rejects_pending_wrong_hash_wrong_blob_or_wrong_report() -> None:
    m = valid_manifest()
    raw = json.dumps(m, sort_keys=True, indent=2).encode() + b"\n"
    approval = valid_approval(raw)
    approval["status"] = "PENDING_REVIEW"
    must_raise(lambda: mod.validate_approval_structure(
        approval, manifest_sha256=hashlib.sha256(raw).hexdigest(),
        manifest_git_blob="c" * 40, tester_report_bytes=REPORT_BYTES,
        tester_report_git_blob="d" * 40,
    ), "approval_not_ready")

    approval = valid_approval(raw)
    must_raise(lambda: mod.validate_approval_structure(
        approval, manifest_sha256="0" * 64, manifest_git_blob="c" * 40,
        tester_report_bytes=REPORT_BYTES, tester_report_git_blob="d" * 40,
    ), "approval_manifest_sha256_mismatch")

    approval = valid_approval(raw)
    must_raise(lambda: mod.validate_approval_structure(
        approval, manifest_sha256=hashlib.sha256(raw).hexdigest(),
        manifest_git_blob="0" * 40, tester_report_bytes=REPORT_BYTES,
        tester_report_git_blob="d" * 40,
    ), "approval_manifest_blob_mismatch")

    approval = valid_approval(raw)
    must_raise(lambda: mod.validate_approval_structure(
        approval, manifest_sha256=hashlib.sha256(raw).hexdigest(),
        manifest_git_blob="c" * 40, tester_report_bytes=b"approval without scope",
        tester_report_git_blob="d" * 40,
    ), "tester_report_digest_mismatch")


def test_gate_metadata_pins_paths_manifest_blob_and_review_commit() -> None:
    approval = {
        "request_manifest_path": str(mod.MANIFEST_PATH.relative_to(mod.ROOT)),
        "tester_report_path": str(mod.TESTER_REPORT_PATH.relative_to(mod.ROOT)),
        "request_manifest_git_blob": "c" * 40,
        "reviewed_manifest_developer_commit": "e" * 40,
    }
    mod.validate_gate_metadata(
        approval, manifest_git_blob="c" * 40, manifest_review_commit="e" * 40
    )
    approval["request_manifest_path"] = "other.json"
    must_raise(lambda: mod.validate_gate_metadata(
        approval, manifest_git_blob="c" * 40, manifest_review_commit="e" * 40
    ), "approval_manifest_path_mismatch")
    approval["request_manifest_path"] = str(mod.MANIFEST_PATH.relative_to(mod.ROOT))
    approval["tester_report_path"] = "untrusted.md"
    must_raise(lambda: mod.validate_gate_metadata(
        approval, manifest_git_blob="c" * 40, manifest_review_commit="e" * 40
    ), "approval_tester_report_path_mismatch")


def test_gate_metadata_rejects_manifest_or_review_commit_mismatch() -> None:
    approval = {
        "request_manifest_path": str(mod.MANIFEST_PATH.relative_to(mod.ROOT)),
        "tester_report_path": str(mod.TESTER_REPORT_PATH.relative_to(mod.ROOT)),
        "request_manifest_git_blob": "c" * 40,
        "reviewed_manifest_developer_commit": "e" * 40,
    }
    must_raise(lambda: mod.validate_gate_metadata(
        approval, manifest_git_blob="0" * 40, manifest_review_commit="e" * 40
    ), "approval_manifest_blob_mismatch")
    must_raise(lambda: mod.validate_gate_metadata(
        approval, manifest_git_blob="c" * 40, manifest_review_commit="f" * 40
    ), "reviewed_manifest_commit_mismatch")


def test_pending_review_gate_requires_exact_manifest_pins() -> None:
    approval = {
        "status": "PENDING_REVIEW",
        "decision": "AWAITING_INDEPENDENT_MANIFEST_REVIEW",
        "scope_id": mod.SCOPE_ID,
        "request_manifest_path": str(mod.MANIFEST_PATH.relative_to(mod.ROOT)),
        "tester_report_path": str(mod.TESTER_REPORT_PATH.relative_to(mod.ROOT)),
        "request_manifest_git_blob": "a" * 40,
        "request_manifest_sha256": "b" * 64,
        "approved_authorization_sha256": "c" * 64,
    }
    mod.validate_pending_review_gate(
        approval, manifest_sha256="b" * 64, manifest_git_blob="a" * 40,
        authorization_sha256="c" * 64
    )
    cases = [
        ({**approval, "request_manifest_sha256": "0" * 64},
         "approval_manifest_sha256_mismatch"),
        ({**approval, "request_manifest_git_blob": "0" * 40},
         "approval_manifest_blob_mismatch"),
        ({**approval, "approved_authorization_sha256": "0" * 64},
         "approved_authorization_digest_mismatch"),
        ({**approval, "scope_id": "other"},
         "approval_gate_scope_mismatch"),
        ({**approval, "status": "READY"},
         "approval_gate_not_pending"),
    ]
    for invalid, expected in cases:
        must_raise(lambda invalid=invalid, expected=expected: mod.validate_pending_review_gate(
            invalid, manifest_sha256="b" * 64, manifest_git_blob="a" * 40,
            authorization_sha256="c" * 64
        ), expected)


def test_approval_requires_report_scope_markers() -> None:
    raw = json.dumps(valid_manifest(), sort_keys=True, indent=2).encode() + b"\n"
    approval = valid_approval(raw)
    report = b"PASS WITH SCOPED RESTRICTIONS, but no exact scope or no-live wording"
    approval["tester_report_sha256"] = hashlib.sha256(report).hexdigest()
    must_raise(lambda: mod.validate_approval_structure(
        approval, manifest_sha256=hashlib.sha256(raw).hexdigest(),
        manifest_git_blob="c" * 40, tester_report_bytes=report,
        tester_report_git_blob="d" * 40,
    ), "tester_report_scope_marker_missing")


TESTS = [value for name, value in globals().copy().items()
         if name.startswith("test_") and callable(value)]
for test in TESTS:
    test()
print(f"PASS {len(TESTS)} Dhan daily sample manifest validator offline tests")
