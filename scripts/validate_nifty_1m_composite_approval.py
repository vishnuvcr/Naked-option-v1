#!/usr/bin/env python3
"""Exact-snapshot gate for the one-run NIFTY 1-minute composite acquisition.

check: validates tester report, source/request scope and protected hashes.
spend: records the approval as spent before any source request.
finish: records COMPLETE/PARTIAL from the encrypted export's metadata report.
self-test: offline validation of the manifest and request list only.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPROVAL = ROOT / "research/gates/NIFTY_1M_COMPOSITE_APPROVAL.json"
MANIFEST = ROOT / "research/gates/NIFTY_1M_COMPOSITE_REQUEST_MANIFEST.json"
REPORT = ROOT / "research/gates/PHASE7_PPR4_USER_DIRECTED_COMPOSITE_ACQUISITION_TESTER_REVIEW.md"
COVERAGE = ROOT / "data/exports/nifty_1m_composite/coverage_and_errors.json"
APPROVED_TESTER_BRANCH = "phase-07-tester"
APPROVED_BRANCH = "phase-07-developer"


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise ValueError("git_validation_failed:" + " ".join(args))
    return result.stdout.strip()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top_level_json_object_required:" + path.name)
    return value


def validate_request_grid() -> None:
    from validate_nifty_1m_composite_manifest import validate as validate_grid
    errors = validate_grid()
    if errors:
        raise ValueError("request_grid_invalid:" + ";".join(errors[:20]))
    manifest = load(MANIFEST)
    if manifest.get("budgets", {}).get("planned_unique_requests") != 8601:
        raise ValueError("request_budget_total_mismatch")
    if manifest.get("authorization", {}).get("live_requests_authorized") is not False:
        raise ValueError("request_manifest_self_authorized_live_requests")


def protected_file_check(approval: dict[str, Any]) -> None:
    pins = approval.get("protected_files")
    if not isinstance(pins, dict) or not pins:
        raise ValueError("protected_file_pins_missing")
    for rel, pin in sorted(pins.items()):
        if not isinstance(rel, str) or rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts:
            raise ValueError("unsafe_protected_file_path")
        path = ROOT / rel
        if not path.is_file():
            raise ValueError("protected_file_missing:" + rel)
        if not isinstance(pin, dict):
            raise ValueError("protected_file_pin_invalid:" + rel)
        actual_sha256 = sha256_file(path)
        actual_blob = git("rev-parse", "HEAD:" + rel)
        if actual_sha256 != pin.get("sha256"):
            raise ValueError("protected_file_sha256_mismatch:" + rel)
        if actual_blob != pin.get("git_blob"):
            raise ValueError("protected_file_git_blob_mismatch:" + rel)


def tester_report_check(approval: dict[str, Any]) -> None:
    tester = approval.get("tester_review", {})
    if tester.get("branch") != APPROVED_TESTER_BRANCH or tester.get("path") != "research/gates/PHASE7_PPR4_USER_DIRECTED_COMPOSITE_ACQUISITION_TESTER_REVIEW.md":
        raise ValueError("tester_report_reference_mismatch")
    try:
        remote_blob = git("rev-parse", "origin/" + APPROVED_TESTER_BRANCH + ":" + tester["path"])
        text = git("show", "origin/" + APPROVED_TESTER_BRANCH + ":" + tester["path"])
    except Exception:
        raise ValueError("tester_branch_or_report_unavailable") from None
    if remote_blob != tester.get("git_blob"):
        raise ValueError("tester_report_blob_mismatch")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest != tester.get("sha256"):
        raise ValueError("tester_report_sha256_mismatch")
    required = [
        "PASS WITH SCOPED RESTRICTIONS",
        "EXACT MANIFEST AND ACQUISITION WORKFLOW ONLY",
        "No further Dhan-versus-NSE/third-party price-value cross-check is required",
        "No model fitting or holdout access is authorized",
    ]
    for marker in required:
        if marker not in text:
            raise ValueError("tester_report_scope_marker_missing:" + marker)


def check() -> None:
    validate_request_grid()
    approval = load(APPROVAL)
    if approval.get("status") != "READY" or approval.get("decision") != "APPROVED_EXACT_REQUEST_GRID_AND_WORKFLOW":
        raise ValueError("acquisition_approval_not_READY")
    if approval.get("authorized_branch") != APPROVED_BRANCH:
        raise ValueError("developer_branch_mismatch")
    if approval.get("live_requests_authorized") is not True:
        raise ValueError("approval_does_not_authorize_live_requests")
    if approval.get("model_fitting_authorized") is not False or approval.get("holdout_access_authorized") is not False:
        raise ValueError("forbidden_model_or_holdout_scope")
    if approval.get("planned_request_count") != 8601 or approval.get("max_retry_requests_total") != 100 or approval.get("max_wire_requests_total") != 8701:
        raise ValueError("approval_request_budget_mismatch")
    manifest_blob = git("rev-parse", "HEAD:research/gates/NIFTY_1M_COMPOSITE_REQUEST_MANIFEST.json")
    if manifest_blob != approval.get("request_manifest_git_blob"):
        raise ValueError("root_manifest_blob_mismatch")
    reviewed = approval.get("reviewed_developer_commit")
    if not isinstance(reviewed, str) or len(reviewed) != 40:
        raise ValueError("reviewed_developer_commit_missing")
    git("merge-base", "--is-ancestor", reviewed, "HEAD")
    protected_file_check(approval)
    tester_report_check(approval)
    print("PASS: exact source request list, tester snapshot, protected file pins, budgets and no-model scope validated.")


def spend() -> None:
    approval = load(APPROVAL)
    if approval.get("status") != "READY":
        raise ValueError("approval_must_be_READY_before_spend")
    # The full exact-snapshot validation runs immediately before this step.
    approval["status"] = "SPENT_BEFORE_SOURCE_REQUEST"
    approval["decision"] = "SPENT"
    approval["started_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    approval["github_run_id"] = os.environ.get("GITHUB_RUN_ID", "")
    approval["source_operations_started"] = True
    approval["live_requests_authorized"] = False
    APPROVAL.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("PASS: exact acquisition approval marked spent before network access.")


def finish() -> None:
    approval = load(APPROVAL)
    status = "PARTIAL"
    summary: dict[str, Any] = {}
    coverage_path = COVERAGE
    if coverage_path.is_file():
        try:
            coverage = load(coverage_path)
            result_status = str(coverage.get("status", "PARTIAL_GRID"))
            summary = {
                "dataset_status": result_status,
                "request_count_processed": coverage.get("summary", {}).get("request_count_processed"),
                "request_count_planned": coverage.get("summary", {}).get("request_count_planned"),
                "wire_requests_cumulative": coverage.get("summary", {}).get("wire_requests_cumulative"),
                "retry_requests_cumulative": coverage.get("summary", {}).get("retry_requests_cumulative"),
                "rows_spot": coverage.get("summary", {}).get("rows_spot"),
                "rows_options": coverage.get("summary", {}).get("rows_options"),
                "failed_responses": coverage.get("summary", {}).get("failed_responses"),
            }
            status = "COMPLETE" if result_status == "COMPLETE_REQUEST_GRID" else "PARTIAL"
        except Exception:
            status = "PARTIAL"
            summary = {"coverage_report_parse_error": True}
    approval["status"] = status
    approval["decision"] = "ACQUISITION_FINISHED"
    approval["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    approval["result_summary"] = summary
    approval["live_requests_authorized"] = False
    approval["source_operations_started"] = True
    APPROVAL.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"acquisition_status": status, "summary": summary}, sort_keys=True))


def self_test() -> None:
    validate_request_grid()
    print("PASS: acquisition approval helper sees an exact valid manifest and does not authorize network access.")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"check", "spend", "finish", "self-test"}:
        print("usage: validate_nifty_1m_composite_approval.py check|spend|finish|self-test")
        return 2
    try:
        {"check": check, "spend": spend, "finish": finish, "self-test": self_test}[sys.argv[1]]()
        return 0
    except Exception as exc:
        print("ACQUISITION_GATE_BLOCKED " + type(exc).__name__ + ":" + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
