#!/usr/bin/env python3
"""Offline regressions for the official-source one-use approval validator."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "validate_official_reference_crosscheck_approval",
    SCRIPTS / "validate_official_reference_crosscheck_approval.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

REPORT_TEXT = (
    "# Independent Tester PASS\n\n"
    "PASS WITH SCOPED RESTRICTIONS\n"
    + mod.SCOPE_ID + "\n"
    "No public-source request is authorized. No bulk history, no model fitting.\n"
)
REPORT_BYTES = REPORT_TEXT.encode("utf-8")


def valid_manifest() -> dict:
    protected = {
        path: {
            "git_blob": hashlib.sha1(path.encode("utf-8")).hexdigest(),
            "sha256": hashlib.sha256(path.encode("utf-8")).hexdigest(),
        }
        for path in mod.REQUIRED_PROTECTED_FILES
    }
    auth = {
        "scope_id": mod.SCOPE_ID,
        "authorized_scope": "one same-day official NIFTY OHLC lookup plus one public Dhan instrument mapping lookup",
        "expected_date": mod.adapter.EXPECTED_DATE,
        "expected_dhan_row": mod.adapter.EXPECTED_DHAN_ROW,
        "expected_mapping": mod.adapter.EXPECTED_MAPPING,
        "dhan_sample_response_sha256": mod.adapter.EXPECTED_DHAN_SAMPLE_RESPONSE_SHA256,
        "source_specs": mod.EXPECTED_SOURCE_SPECS,
        "total_requests_max": 2,
        "retries_allowed": False,
        "redirect_follow_allowed": False,
        "credential_forwarding_allowed": False,
        "bulk_history_authorized": False,
        "intraday_authorized": False,
        "rolling_options_authorized": False,
        "feature_engineering_authorized": False,
        "model_fitting_authorized": False,
        "strategy_testing_authorized": False,
        "holdout_access_authorized": False,
        "data_acceptance_authorized": False,
        "reviewed_developer_commit": "a" * 40,
        "protected_files": protected,
    }
    return {
        "schema_version": 1,
        "status": "PROPOSED",
        "decision": "AWAITING_INDEPENDENT_MANIFEST_REVIEW",
        "authorization": auth,
        "authorization_sha256": mod.canonical_sha256(auth),
    }


def valid_approval(manifest: dict, manifest_raw: bytes, *, report_bytes: bytes = REPORT_BYTES) -> dict:
    return {
        "status": "READY",
        "decision": "APPROVED_ONE_RUN",
        "scope_id": mod.SCOPE_ID,
        "request_manifest_path": str(mod.MANIFEST_PATH.relative_to(mod.ROOT)),
        "request_manifest_git_blob": "b" * 40,
        "request_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "approved_authorization_sha256": manifest["authorization_sha256"],
        "tester_report_path": str(mod.TESTER_REPORT_PATH.relative_to(mod.ROOT)),
        "tester_report_git_blob": "c" * 40,
        "tester_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
    }


def must_raise(fn, code: str) -> None:
    try:
        fn()
    except ValueError as exc:
        assert str(exc) == code, (str(exc), code)
    else:
        raise AssertionError(f"expected ValueError({code!r})")


def test_import_and_constants_do_not_contact_network() -> None:
    assert mod.SCOPE_ID == "dhan-sample-official-crosscheck-2024-01-02-two-hosts"
    assert len(mod.REQUIRED_PROTECTED_FILES) >= 15
    assert mod.EXPECTED_SOURCE_SPECS[0]["url"] == mod.adapter.NIFTY_INDICES_URL
    assert mod.EXPECTED_SOURCE_SPECS[1]["url"] == mod.adapter.DHAN_COMPACT_MASTER_URL


def test_valid_manifest_structure_passes() -> None:
    mod.validate_manifest_structure(valid_manifest())


def test_manifest_rejects_wrong_scope_date_data_row_and_symbol_mapping() -> None:
    cases = [
        ({"scope_id": "other"}, "scope_id_mismatch"),
        ({"expected_date": "2024-01-03"}, "expected_date_mismatch"),
        ({"expected_dhan_row": {**mod.adapter.EXPECTED_DHAN_ROW, "close": "1.00"}}, "expected_dhan_row_mismatch"),
        ({"expected_mapping": {**mod.adapter.EXPECTED_MAPPING, "symbol": "NIFTY100"}}, "expected_mapping_mismatch"),
        ({"dhan_sample_response_sha256": "0" * 64}, "dhan_sample_hash_mismatch"),
        ({"source_specs": mod.EXPECTED_SOURCE_SPECS[:1]}, "source_scope_mismatch"),
    ]
    for changes, expected in cases:
        m = valid_manifest()
        m["authorization"].update(changes)
        m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
        must_raise(lambda m=m: mod.validate_manifest_structure(m), expected)


def test_manifest_rejects_widened_budgets_credentials_retries_and_research_scope() -> None:
    invalids = [
        ({"total_requests_max": 3}, "total_request_budget_invalid"),
        ({"retries_allowed": True}, "forbidden_scope_flag"),
        ({"redirect_follow_allowed": True}, "forbidden_scope_flag"),
        ({"credential_forwarding_allowed": True}, "forbidden_scope_flag"),
        ({"bulk_history_authorized": True}, "forbidden_scope_flag"),
        ({"feature_engineering_authorized": True}, "forbidden_scope_flag"),
        ({"model_fitting_authorized": True}, "forbidden_scope_flag"),
        ({"strategy_testing_authorized": True}, "forbidden_scope_flag"),
        ({"holdout_access_authorized": True}, "forbidden_scope_flag"),
        ({"data_acceptance_authorized": True}, "forbidden_scope_flag"),
    ]
    for changes, expected in invalids:
        m = valid_manifest()
        m["authorization"].update(changes)
        m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
        must_raise(lambda m=m: mod.validate_manifest_structure(m), expected)


def test_manifest_requires_exact_protected_file_set_and_valid_hashes() -> None:
    m = valid_manifest()
    m["authorization"]["protected_files"].pop(next(iter(m["authorization"]["protected_files"])))
    m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
    must_raise(lambda: mod.validate_manifest_structure(m), "protected_file_set_mismatch")

    m = valid_manifest()
    first = next(iter(m["authorization"]["protected_files"]))
    m["authorization"]["protected_files"][first]["sha256"] = "invalid"
    m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
    must_raise(lambda: mod.validate_manifest_structure(m), "protected_file_sha256_invalid")


def test_manifest_requires_canonical_authorization_digest_and_proposed_state() -> None:
    m = valid_manifest()
    m["authorization_sha256"] = "0" * 64
    must_raise(lambda: mod.validate_manifest_structure(m), "authorization_digest_mismatch")
    m = valid_manifest()
    m["status"] = "READY"
    must_raise(lambda: mod.validate_manifest_structure(m), "manifest_status_invalid")
    m = valid_manifest()
    m["authorization"]["reviewed_developer_commit"] = "bad"
    m["authorization_sha256"] = mod.canonical_sha256(m["authorization"])
    must_raise(lambda: mod.validate_manifest_structure(m), "reviewed_developer_commit_invalid")


def test_tester_report_and_approval_pins_must_match_exact_bytes_and_paths() -> None:
    m = valid_manifest()
    manifest_raw = (json.dumps(m, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    approval = valid_approval(m, manifest_raw)
    mod.validate_tester_report(
        approval,
        manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        manifest_blob="b" * 40,
        authorization_sha256=m["authorization_sha256"],
        report_bytes=REPORT_BYTES,
        report_blob="c" * 40,
    )
    must_raise(lambda: mod.validate_tester_report(
        approval,
        manifest_sha256="0" * 64,
        manifest_blob="b" * 40,
        authorization_sha256=m["authorization_sha256"],
        report_bytes=REPORT_BYTES,
        report_blob="c" * 40,
    ), "approval_manifest_sha256_mismatch")
    must_raise(lambda: mod.validate_tester_report(
        approval,
        manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        manifest_blob="0" * 40,
        authorization_sha256=m["authorization_sha256"],
        report_bytes=REPORT_BYTES,
        report_blob="c" * 40,
    ), "approval_manifest_blob_mismatch")
    must_raise(lambda: mod.validate_tester_report(
        approval,
        manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        manifest_blob="b" * 40,
        authorization_sha256="0" * 64,
        report_bytes=REPORT_BYTES,
        report_blob="c" * 40,
    ), "approved_authorization_digest_mismatch")


def test_tester_report_requires_all_literal_scope_markers() -> None:
    m = valid_manifest()
    raw = (json.dumps(m, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    for report, expected in [
        (b"PASS WITH SCOPED RESTRICTIONS but missing everything else", "tester_report_scope_marker_missing"),
        ((("PASS WITH SCOPED RESTRICTIONS\n" + mod.SCOPE_ID + "\nNo bulk").encode()), "tester_report_scope_marker_missing"),
    ]:
        approval = valid_approval(m, raw, report_bytes=report)
        must_raise(lambda approval=approval, report=report: mod.validate_tester_report(
            approval,
            manifest_sha256=hashlib.sha256(raw).hexdigest(),
            manifest_blob="b" * 40,
            authorization_sha256=m["authorization_sha256"],
            report_bytes=report,
            report_blob="c" * 40,
        ), expected)


def test_spend_transition_is_single_use_and_populates_runner_scope() -> None:
    m = valid_manifest()
    raw = (json.dumps(m, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    approval = valid_approval(m, raw)
    spent = mod.prepare_spent(approval, spent_from_commit="d" * 40)
    assert spent["status"] == "SPENT"
    assert spent["decision"] == "SPENT_BEFORE_SOURCE_REQUEST"
    assert spent["authorized_scope_id"] == mod.SCOPE_ID
    assert spent["spent_from_commit"] == "d" * 40
    assert approval["status"] == "READY"
    must_raise(lambda: mod.prepare_spent(spent, spent_from_commit="e" * 40), "approval_already_spent_or_not_ready")
    must_raise(lambda: mod.prepare_spent(approval, spent_from_commit="not-a-commit"), "spent_from_commit_invalid")


def test_live_workflow_is_strictly_gated_and_spends_before_first_request() -> None:
    workflow_path = ROOT / ".github/workflows/phase-07-official-crosscheck-live.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    gate_check = workflow.index("Verify exact READY manifest, protected files and independent tester report")
    spend = workflow.index("Spend one-use approval before first public-source request")
    fetch = workflow.index("Request the one-date official OHLC and Dhan public mapping")
    cache = workflow.index("Commit matched raw-source cache bundle")
    assert gate_check < spend < fetch < cache
    assert "contents: write" in workflow
    assert "confirm_official_crosscheck:" in workflow
    assert "default: false" in workflow
    assert "inputs.confirm_official_crosscheck == true" in workflow
    assert "READY Official crosscheck approval" in workflow
    spend_block = workflow[spend:fetch]
    assert "python scripts/validate_official_reference_crosscheck_approval.py spend" in spend_block
    assert "git push origin HEAD:phase-07-developer" in spend_block
    request_block = workflow[fetch:cache]
    assert 'OFFICIAL_CROSSCHECK_AUTHORIZED: "1"' in request_block
    assert "continue-on-error: true" in request_block
    assert "secrets." not in workflow
    assert "DHAN_ACCESS_TOKEN" not in workflow
    assert "access-token" not in workflow.lower()
    assert "retry" in workflow.lower() and "redirect" in workflow.lower()
    assert "official-nifty-sample-crosscheck" in workflow
    assert "if: steps.fetch_crosscheck.outcome != 'success'" in workflow


def test_offline_workflow_has_read_only_permissions_and_no_source_request_step() -> None:
    offline = (ROOT / ".github/workflows/phase-07-official-crosscheck-tests.yml").read_text(encoding="utf-8")
    assert "permissions:" in offline and "contents: read" in offline
    assert "OFFICIAL_CROSSCHECK_AUTHORIZED" not in offline
    assert "DHAN_ACCESS_TOKEN" not in offline
    assert "secrets." not in offline
    assert "Run existing and new mocked cross-check test suites" in offline
    assert "CANDIDATE_PROTECTED_FINGERPRINTS=" in offline
    assert "No public-source calls are performed" in offline


def test_default_and_developer_live_workflow_contents_match() -> None:
    import subprocess
    working = (ROOT / ".github/workflows/phase-07-official-crosscheck-live.yml").read_bytes()
    try:
        main_content = subprocess.check_output(
            ["git", "show", "origin/main:.github/workflows/phase-07-official-crosscheck-live.yml"],
            cwd=ROOT,
        )
    except subprocess.CalledProcessError:
        raise AssertionError("default branch live workflow must exist") from None
    assert working == main_content


TESTS = [value for name, value in globals().copy().items() if name.startswith("test_") and callable(value)]
for test in TESTS:
    test()
print(f"PASS {len(TESTS)} official cross-check approval validator offline tests")
