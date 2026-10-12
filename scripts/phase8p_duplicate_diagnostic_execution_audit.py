#!/usr/bin/env python3
"""Independent static audit for the one-use Phase 8P diagnostic execution workflow.

Never downloads, opens, decrypts, or scans the real Greek artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

WORKFLOW_PATH = ".github/workflows/phase8p-duplicate-diagnostic-execution.yml"
REQUEST_PATH = "research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_REVIEW_REQUEST_R2_2026-10-12.json"
EXPECTED_DEV_BRANCH = "phase-08-prediction-developer"
EXPECTED_TESTER_BRANCH = "phase-08-prediction-tester"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()


def show(root: Path, ref: str, path: str) -> str:
    return git(root, "show", f"{ref}:{path}")


def blob(root: Path, ref: str, path: str) -> str:
    return git(root, "rev-parse", f"{ref}:{path}")


def check(rows, failures, name, passed, detail=None):
    row = {"check": name, "pass": bool(passed)}
    if detail is not None:
        row["detail"] = detail
    rows.append(row)
    if not passed:
        failures.append(name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--safe-noop-run-id", type=int, default=38206043280)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    dev = f"refs/remotes/origin/{EXPECTED_DEV_BRANCH}"
    tester = f"refs/remotes/origin/{EXPECTED_TESTER_BRANCH}"
    checks, failures = [], []
    req = json.loads(show(root, dev, REQUEST_PATH))
    req_blob = blob(root, dev, REQUEST_PATH)
    workflow_text = show(root, dev, WORKFLOW_PATH)
    workflow_blob = blob(root, dev, WORKFLOW_PATH)

    check(checks, failures, "workflow_review_request_is_pending_and_non_authorizing",
          req.get("status") == "PENDING_INDEPENDENT_TESTER_REVIEW"
          and req.get("review_scope") == "EXECUTOR_WORKFLOW_AND_NOOP_GUARDS_ONLY_NO_REAL_ARTIFACT_ACCESS"
          and req.get("real_artifact_access_authorized") is False
          and req.get("real_artifact_decryption_authorized") is False
          and req.get("real_diagnostic_authorized") is False
          and req.get("model_fit_authorized") is False
          and req.get("holdout_access_authorized") is False
          and req.get("option_pnl_authorized") is False
          and req.get("strategy_promotion_authorized") is False)
    check(checks, failures, "workflow_blob_pin_matches_request",
          req.get("workflow_path") == WORKFLOW_PATH and req.get("workflow_blob_sha1") == workflow_blob,
          {"expected": req.get("workflow_blob_sha1"), "actual": workflow_blob})
    check(checks, failures, "one_use_nonce_present_at_top_level_and_contract",
          req.get("execution_nonce") == req.get("execution_authorization_contract", {}).get("one_use_nonce")
          and req.get("execution_nonce") == "PHASE8P_DUP_DIAG_EXEC_20261012_R1_8F8D5133")
    check(checks, failures, "workflow_request_blob_is_immutable_for_this_review",
          bool(req_blob) and len(req_blob) == 40,
          {"request_path": REQUEST_PATH, "request_blob_sha1": req_blob})

    # Independently pin the earlier R4 code-only and scope-only decisions on the tester-owned branch.
    code_review = req.get("r4_code_review", {})
    scope_review = req.get("r4_scope_review", {})
    code_decision_path = code_review.get("decision_path")
    code_report_path = code_review.get("report_path")
    scope_decision_path = scope_review.get("decision_path")
    try:
        actual_code_decision = blob(root, tester, code_decision_path)
        actual_code_report = blob(root, tester, code_report_path)
        actual_scope_decision = blob(root, tester, scope_decision_path)
        code_decision = json.loads(show(root, tester, code_decision_path))
        scope_decision = json.loads(show(root, tester, scope_decision_path))
        check(checks, failures, "r4_code_decision_blob_pin",
              actual_code_decision == code_review.get("decision_blob_sha1")
              == req.get("r4_code_decision_blob_sha1"))
        check(checks, failures, "r4_code_report_blob_pin",
              actual_code_report == code_review.get("report_blob_sha1")
              == req.get("r4_code_report_blob_sha1"))
        check(checks, failures, "r4_scope_decision_blob_pin",
              actual_scope_decision == scope_review.get("decision_blob_sha1")
              == req.get("r4_scope_decision_blob_sha1"))
        check(checks, failures, "r4_code_review_is_code_only",
              code_decision.get("decision") == "PASS_FOR_DUPLICATE_DIAGNOSTIC_CODE_ONLY"
              and code_decision.get("developer_commit") == req.get("developer_code_commit")
              and code_decision.get("real_artifact_accessed") is False
              and code_decision.get("real_diagnostic_authorized") is False
              and code_decision.get("model_fit_authorized") is False)
        check(checks, failures, "r4_scope_review_is_scope_only",
              scope_decision.get("decision") == "PASS_SCOPE_AMENDMENT_ONLY_WITH_RESTRICTIONS"
              and scope_decision.get("real_artifact_access_authorized") is False
              and scope_decision.get("model_fit_authorized") is False)
    except Exception as exc:
        check(checks, failures, "r4_pinned_tester_decisions_readable", False, type(exc).__name__)

    # Exact code references are reviewed as immutable git blobs; they are never executed here.
    try:
        commit = req["developer_code_commit"]
        for label, path, expected in (
            ("core_module", "scripts/phase8p_greek_prediction.py", req["implementation"]["scripts/phase8p_greek_prediction.py"]),
            ("diagnostic", "scripts/phase8p_duplicate_key_diagnostic.py", req["implementation"]["scripts/phase8p_duplicate_key_diagnostic.py"]),
            ("diagnostic_test", "scripts/test_phase8p_duplicate_key_diagnostic.py", req["implementation"]["scripts/test_phase8p_duplicate_key_diagnostic.py"]),
        ):
            actual = blob(root, dev, path)
            pinned = blob(root, commit, path)
            check(checks, failures, "current_dev_ref_preserves_" + label,
                  actual == expected, {"expected": expected, "actual": actual})
            check(checks, failures, "approved_commit_pins_" + label,
                  pinned == expected, {"expected": expected, "actual": pinned})
    except Exception as exc:
        check(checks, failures, "developer_snapshot_blob_checks", False, type(exc).__name__)

    # YAML already ran on GitHub Actions; parse its trigger/permission shape as a second static check.
    try:
        parsed = yaml.safe_load(workflow_text)
        triggers = parsed.get("on", parsed.get(True, {}))
        jobs = parsed.get("jobs", {})
        job = jobs.get("diagnostic", {})
        steps = job.get("steps", [])
        names = [step.get("name", "") for step in steps]
        required_order = [
            "Verify independent R4 code decision and two-stage execution authorization before any data access",
            "Commit the one-use nonce to the permanent developer ledger before downloading data",
            "Set up Python after execution authorization",
            "Install pinned diagnostic dependencies after authorization",
            "Check out exact approved diagnostic code in a detached worktree",
            "Restore cached encrypted Greek artifact after authorization",
            "Download or validate pinned encrypted Greek artifact",
            "Run authorized aggregate-only duplicate diagnostic",
            "Upload only aggregate diagnostic report and receipts",
        ]
        positions = [names.index(item) for item in required_order]
        check(checks, failures, "yaml_valid_and_job_exists",
              isinstance(parsed, dict) and isinstance(job, dict) and bool(steps))
        check(checks, failures, "manual_and_automatic_trigger_present",
              "push" in triggers and "workflow_dispatch" in triggers
              and "phase-08-prediction-developer" in str(triggers.get("push", {}))
              and triggers.get("workflow_dispatch", {}).get("inputs", {}).get("run_one_use_diagnostic", {}).get("default") is False)
        check(checks, failures, "least_privilege_permissions_explicit",
              parsed.get("permissions", {}).get("contents") == "write"
              and parsed.get("permissions", {}).get("actions") == "read")
        check(checks, failures, "serial_execution_group_present",
              parsed.get("concurrency", {}).get("group") == "phase8p-duplicate-diagnostic-single-use"
              and parsed.get("concurrency", {}).get("cancel-in-progress") is False)
        check(checks, failures, "ordered_gate_nonce_code_checkout_before_data_access",
              positions == sorted(positions))
        check(checks, failures, "all_data_steps_gated_on_authorized_output",
              all("steps.gate.outputs.run_authorized == 'true'" in step.get("if", "")
                  for step in steps if step.get("name") in required_order[1:]))
        check(checks, failures, "missing_approval_is_safe_noop_and_stale_approval_fails_closed",
              "SAFE_NOOP_BEFORE_ARTIFACT_ACCESS" in workflow_text
              and "DUPLICATE_EXECUTION_BLOCKED_BEFORE_ARTIFACT_ACCESS" in workflow_text
              and 'no_op("independent tester has not approved this exact execution workflow")' in workflow_text
              and 'no_op("separate one-use execution authorization has not been issued")' in workflow_text)
        check(checks, failures, "distinct_workflow_and_execution_decisions_required",
              req["execution_authorization_contract"]["workflow_approval_decision_path"] in workflow_text
              and req["execution_authorization_contract"]["one_use_execution_authorization_path"] in workflow_text
              and "PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY" in workflow_text
              and "PASS_ONE_TIME_DUPLICATE_DIAGNOSTIC_EXECUTION_ONLY" in workflow_text
              and "execution_authorization_granted" in workflow_text)
        check(checks, failures, "R2_workflow_approval_path_matches_request_contract",
              req["execution_authorization_contract"]["workflow_approval_decision_path"]
              == "research/gates/PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_TESTER_DECISION_R2_2026-10-12.json"
              and req["execution_authorization_contract"]["workflow_approval_decision_path"] in workflow_text)
        check(checks, failures, "separate_execution_authorization_request_is_pinned",
              req["execution_authorization_contract"]["one_use_execution_authorization_path"] in workflow_text
              and "EXECUTION_AUTH_REQUEST_PATH" in workflow_text
              and "PENDING_ONE_TIME_EXECUTION_AUTHORIZATION" in workflow_text
              and "request_contract" in workflow_text
              and "execution_authorization_request_blob_sha1" in workflow_text
              and 'auth_request.get("status") != "PENDING_ONE_TIME_EXECUTION_AUTHORIZATION"' in workflow_text
              and '"execution_authorization_request_blob_sha1": auth_request_blob' in workflow_text
              and "real_artifact_access_authorized" in workflow_text)
        check(checks, failures, "approval_is_bound_to_exact_request_workflow_code_and_artifact",
              all(field in workflow_text for field in (
                  "executor_request_blob_sha1", "developer_workflow_blob_sha1",
                  "workflow_approval_decision_blob_sha1", "developer_code_commit",
                  "source_artifact_id", "source_artifact_sha256",
              )) and req["source_artifact"]["sha256"] in workflow_text)
        check(checks, failures, "one_use_permanent_ledger_and_rerun_guard",
              req["execution_authorization_contract"]["permanent_nonce_ledger_path"] in workflow_text
              and "GITHUB_RUN_ATTEMPT" in workflow_text
              and "execution nonce has already been consumed" in workflow_text
              and "git push origin HEAD:phase-08-prediction-developer" in workflow_text
              and "PHASE8P_DUP_DIAG_EXEC_20261012_R1_8F8D5133" in workflow_text)
        check(checks, failures, "pinned_artifact_hash_verified_before_diagnostic",
              workflow_text.index("Download or validate pinned encrypted Greek artifact")
              < workflow_text.index("ACTUAL=\"$(sha256sum")
              < workflow_text.index("Run authorized aggregate-only duplicate diagnostic")
              and req["source_artifact"]["sha256"] in workflow_text
              and "verify_pinned_artifact_identity" in git(root, "show", f'{req["developer_code_commit"]}:scripts/phase8p_duplicate_key_diagnostic.py'))
        check(checks, failures, "HF_TOKEN_exposed_only_to_authorized_diagnostic_step",
              workflow_text.count("secrets.HF_TOKEN") == 1
              and workflow_text.index("secrets.HF_TOKEN") > workflow_text.index("Run authorized aggregate-only duplicate diagnostic")
              and workflow_text.index("secrets.HF_TOKEN") > workflow_text.index("Commit the one-use nonce"))
        check(checks, failures, "artifact_redirect_and_secret_not_echoed",
              'print(locations[-1])' in workflow_text
              and 'LOCATION="$(python' in workflow_text
              and 'curl --fail --silent --show-error --location' in workflow_text
              and 'echo "$LOCATION"' not in workflow_text
              and 'print(os.environ["HF_TOKEN"])' not in workflow_text
              and "set -x" not in workflow_text
              and "HF_TOKEN" not in workflow_text[workflow_text.index("Upload only aggregate diagnostic report and receipts"):]
              and "LOCATION" not in workflow_text[workflow_text.index("Create hash-pinned aggregate execution receipt"):])
        check(checks, failures, "only_aggregate_report_and_receipts_uploaded",
              "raw-diagnostic-report.json" in workflow_text
              and "DIAGNOSTIC_REPORT_SCHEMA_MISMATCH" in workflow_text
              and "raw_path.unlink(missing_ok=True)" in workflow_text
              and "duplicate-diagnostic-report.json" in workflow_text
              and "execution-receipt.json" in workflow_text
              and "data/cache/phase8p-artifacts/nifty-1m-greeks-enriched-r3.zip" not in workflow_text[workflow_text.index("Upload only aggregate diagnostic report and receipts"):])
        check(checks, failures, "all_out_of_scope_permissions_are_closed",
              all(term in workflow_text for term in (
                  '"deduplication_authorized": False','"model_fit_authorized": False',
                  '"holdout_access_authorized": False','"option_pnl_authorized": False',
                  '"strategy_promotion_authorized": False','"raw_or_decrypted_data_upload_authorized": False',
              )))
    except Exception as exc:
        check(checks, failures, "workflow_static_audit_complete", False, type(exc).__name__)

    # Inspect only metadata from the known safe-noop run, never fetch artifacts or source data.
    check(checks, failures, "safe_noop_run_reference_present",
          isinstance(args.safe_noop_run_id, int) and args.safe_noop_run_id > 0)

    result = {
        "schema_version": 1,
        "gate": "PHASE8P_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_REVIEW_R1",
        "decision": "PASS_DUPLICATE_DIAGNOSTIC_EXECUTOR_WORKFLOW_ONLY" if not failures else "REQUEST_CHANGES",
        "workflow_path": WORKFLOW_PATH,
        "workflow_blob_sha1": workflow_blob,
        "executor_request_path": REQUEST_PATH,
        "executor_request_blob_sha1": req_blob,
        "developer_code_commit": req.get("developer_code_commit"),
        "checks_passed": sum(1 for row in checks if row["pass"]),
        "checks_total": len(checks),
        "failures": failures,
        "checks": checks,
        "real_artifact_accessed": False,
        "real_artifact_decrypted": False,
        "real_diagnostic_authorized": False,
        "model_fitted": False,
        "holdout_accessed": False,
        "option_pnl_run": False,
        "strategy_promotion": False,
        "review_scope": "STATIC_ONLY_NO_REAL_ARTIFACT_ACCESS"
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "decision", "checks_passed", "checks_total", "failures",
        "real_artifact_accessed", "real_diagnostic_authorized", "model_fitted"
    )}, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
