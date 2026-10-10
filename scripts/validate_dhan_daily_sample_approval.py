#!/usr/bin/env python3
"""Validate the one-use Dhan daily sample manifest and spend its approval.

This validator never contacts Dhan. check/review-check are read-only. spend
atomically changes the separate approval gate to SPENT before a workflow may
pass the access token to the isolated one-request runner.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/gates/DHAN_DAILY_SAMPLE_REQUEST.json"
APPROVAL_PATH = ROOT / "research/gates/DHAN_DAILY_SAMPLE_APPROVAL.json"
TESTER_REPORT_PATH = ROOT / "research/gates/PHASE7_DHAN_DAILY_SAMPLE_MANIFEST_TESTER.md"
DAILY_URL = "https://api.dhan.co/v2/charts/historical"
SCOPE_ID = "dhan-nifty50-daily-2024-01-02-one-request"
REQUEST_BODY = {
    "securityId": "13",
    "exchangeSegment": "IDX_I",
    "instrument": "INDEX",
    "fromDate": "2024-01-02",
    "toDate": "2024-01-03",
    "oi": False,
}
REQUIRED_PROTECTED_FILES = {
    "scripts/dhan_history_pipeline.py",
    "scripts/test_dhan_history_pipeline.py",
    "scripts/run_dhan_daily_sample.py",
    "scripts/test_run_dhan_daily_sample.py",
    "scripts/validate_dhan_daily_sample_approval.py",
    "scripts/test_validate_dhan_daily_sample_approval.py",
    ".github/workflows/phase-07-dhan-daily-sample-tests.yml",
    ".github/workflows/phase-07-dhan-daily-sample-live.yml",
    "research/phase7/DHAN_HISTORICAL_DATA_RECOVERY_PLAN.md",
    "research/gates/PHASE7_DHAN_HISTORICAL_DATA_RECOVERY_CODE_FINAL_TESTER.md",
    "research/gates/PHASE7_DHAN_HISTORICAL_DATA_RECOVERY_CODE_SUBMISSION.md",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(raw)


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError("git_validation_failed")
    return result.stdout.strip()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: pathlib.Path, error_code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(error_code) from None
    if not isinstance(value, dict):
        raise ValueError(error_code)
    return value


def validate_manifest_structure(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != 1:
        raise ValueError("manifest_schema_version_invalid")
    if manifest.get("status") != "PROPOSED":
        raise ValueError("request_manifest_status_invalid")
    if manifest.get("decision") != "AWAITING_INDEPENDENT_MANIFEST_REVIEW":
        raise ValueError("request_manifest_decision_invalid")
    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict):
        raise ValueError("authorization_block_missing")
    if authorization.get("scope_id") != SCOPE_ID:
        raise ValueError("scope_id_mismatch")
    if authorization.get("authorized_scope") != "one tiny daily NIFTY 50 index-history request only":
        raise ValueError("authorized_scope_mismatch")
    if authorization.get("source_url") != DAILY_URL or authorization.get("method") != "POST":
        raise ValueError("source_endpoint_mismatch")
    if authorization.get("request_body") != REQUEST_BODY:
        raise ValueError("request_body_mismatch")
    if (type(authorization.get("requests_max")) is not int or authorization.get("requests_max") != 1
            or type(authorization.get("response_bytes_max")) is not int
            or authorization.get("response_bytes_max") != 2 * 1024 * 1024
            or type(authorization.get("timeout_seconds")) is not int
            or authorization.get("timeout_seconds") != 20):
        raise ValueError("request_budget_mismatch")
    if authorization.get("credential_host") != "api.dhan.co" or authorization.get("credential_header") != "access-token":
        raise ValueError("credential_boundary_mismatch")
    if (authorization.get("redirect_follow_allowed") is not False
            or authorization.get("retry_allowed") is not False
            or authorization.get("full_history_authorized") is not False
            or authorization.get("intraday_authorized") is not False
            or authorization.get("rolling_options_authorized") is not False
            or authorization.get("feature_engineering_authorized") is not False
            or authorization.get("model_fitting_authorized") is not False
            or authorization.get("strategy_testing_authorized") is not False
            or authorization.get("holdout_access_authorized") is not False):
        raise ValueError("forbidden_scope_flag")
    reviewed_commit = authorization.get("reviewed_developer_commit")
    if not isinstance(reviewed_commit, str) or not HEX40.fullmatch(reviewed_commit):
        raise ValueError("reviewed_code_commit_invalid")
    protected = authorization.get("protected_files")
    if not isinstance(protected, dict) or set(protected) != REQUIRED_PROTECTED_FILES:
        raise ValueError("protected_file_set_mismatch")
    for path in sorted(REQUIRED_PROTECTED_FILES):
        entry = protected[path]
        if not isinstance(entry, dict):
            raise ValueError("protected_file_entry_invalid")
        if not isinstance(entry.get("git_blob"), str) or not HEX40.fullmatch(entry["git_blob"]):
            raise ValueError("protected_file_blob_invalid")
        if not isinstance(entry.get("sha256"), str) or not HEX64.fullmatch(entry["sha256"]):
            raise ValueError("protected_file_sha256_invalid")
    expected_authorization_sha = canonical_sha256(authorization)
    if manifest.get("authorization_sha256") != expected_authorization_sha:
        raise ValueError("authorization_digest_mismatch")


def _validate_protected_files(manifest: dict[str, Any]) -> None:
    authorization = manifest["authorization"]
    reviewed_commit = authorization["reviewed_developer_commit"]
    # The reviewed code/config commit must remain in the current branch ancestry.
    git("merge-base", "--is-ancestor", reviewed_commit, "HEAD")
    for relative_path in sorted(REQUIRED_PROTECTED_FILES):
        item = authorization["protected_files"][relative_path]
        path = ROOT / relative_path
        if not path.is_file():
            raise ValueError("protected_file_missing")
        if sha256_file(path) != item["sha256"]:
            raise ValueError("protected_file_sha256_mismatch:" + relative_path)
        if git("rev-parse", "HEAD:" + relative_path) != item["git_blob"]:
            raise ValueError("protected_file_git_blob_mismatch:" + relative_path)
        if git("rev-parse", reviewed_commit + ":" + relative_path) != item["git_blob"]:
            raise ValueError("reviewed_tree_blob_mismatch:" + relative_path)


def validate_approval_structure(
    approval: dict[str, Any],
    *,
    manifest_sha256: str,
    manifest_git_blob: str,
    tester_report_bytes: bytes | None = None,
    tester_report_git_blob: str | None = None,
) -> None:
    if approval.get("scope_id") != SCOPE_ID:
        raise ValueError("approval_scope_id_mismatch")
    if approval.get("request_manifest_sha256") != manifest_sha256:
        raise ValueError("approval_manifest_sha256_mismatch")
    if approval.get("request_manifest_git_blob") != manifest_git_blob:
        raise ValueError("approval_manifest_blob_mismatch")
    if approval.get("decision") != "APPROVED_ONE_RUN":
        raise ValueError("approval_decision_invalid")
    if approval.get("status") not in ("READY", "SPENT"):
        raise ValueError("approval_not_ready")
    report_sha = approval.get("tester_report_sha256")
    report_blob = approval.get("tester_report_git_blob")
    if not isinstance(report_sha, str) or not HEX64.fullmatch(report_sha):
        raise ValueError("tester_report_sha256_invalid")
    if not isinstance(report_blob, str) or not HEX40.fullmatch(report_blob):
        raise ValueError("tester_report_blob_invalid")
    if tester_report_bytes is None or tester_report_git_blob is None:
        raise ValueError("tester_report_missing")
    if sha256_bytes(tester_report_bytes) != report_sha or tester_report_git_blob != report_blob:
        raise ValueError("tester_report_digest_mismatch")
    text = tester_report_bytes.decode("utf-8", errors="strict")
    for marker in (
        "PASS WITH SCOPED RESTRICTIONS",
        SCOPE_ID,
        "No live request is authorized",
        "No bulk",
    ):
        if marker not in text:
            raise ValueError("tester_report_scope_marker_missing")
    if approval.get("approved_authorization_sha256") is None:
        raise ValueError("approved_authorization_digest_missing")


def validate_gate_metadata(
    approval: dict[str, Any],
    *,
    manifest_git_blob: str,
    manifest_review_commit: str | None,
) -> None:
    if approval.get("request_manifest_path") != str(MANIFEST_PATH.relative_to(ROOT)):
        raise ValueError("approval_manifest_path_mismatch")
    if approval.get("tester_report_path") != str(TESTER_REPORT_PATH.relative_to(ROOT)):
        raise ValueError("approval_tester_report_path_mismatch")
    if manifest_review_commit is not None:
        if not isinstance(manifest_review_commit, str) or not HEX40.fullmatch(manifest_review_commit):
            raise ValueError("reviewed_manifest_commit_invalid")
        if approval.get("reviewed_manifest_developer_commit") != manifest_review_commit:
            raise ValueError("reviewed_manifest_commit_mismatch")
    if approval.get("request_manifest_git_blob") != manifest_git_blob:
        raise ValueError("approval_manifest_blob_mismatch")


def validate_pending_review_gate(
    approval: dict[str, Any],
    *,
    manifest_sha256: str,
    manifest_git_blob: str,
    authorization_sha256: str,
) -> None:
    """Require the PENDING gate to pin this exact manifest before review."""
    if approval.get("status") != "PENDING_REVIEW":
        raise ValueError("approval_gate_not_pending")
    if approval.get("decision") != "AWAITING_INDEPENDENT_MANIFEST_REVIEW":
        raise ValueError("approval_gate_decision_invalid")
    if approval.get("scope_id") != SCOPE_ID:
        raise ValueError("approval_gate_scope_mismatch")
    validate_gate_metadata(
        approval, manifest_git_blob=manifest_git_blob, manifest_review_commit=None
    )
    if approval.get("request_manifest_sha256") != manifest_sha256:
        raise ValueError("approval_manifest_sha256_mismatch")
    if approval.get("approved_authorization_sha256") != authorization_sha256:
        raise ValueError("approved_authorization_digest_mismatch")


def review_check() -> None:
    manifest = read_json(MANIFEST_PATH, "request_manifest_unreadable")
    validate_manifest_structure(manifest)
    _validate_protected_files(manifest)
    approval = read_json(APPROVAL_PATH, "approval_gate_unreadable")
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest_sha = sha256_bytes(manifest_bytes)
    manifest_blob = git("rev-parse", "HEAD:" + str(MANIFEST_PATH.relative_to(ROOT)))
    validate_pending_review_gate(
        approval,
        manifest_sha256=manifest_sha,
        manifest_git_blob=manifest_blob,
        authorization_sha256=manifest["authorization_sha256"],
    )
    print(json.dumps({
        "status": "PASS_MANIFEST_REVIEW_PREFLIGHT",
        "scope_id": SCOPE_ID,
        "request_manifest_sha256": manifest_sha,
        "request_manifest_git_blob": manifest_blob,
        "authorization_sha256": manifest["authorization_sha256"],
        "reviewed_developer_commit": manifest["authorization"]["reviewed_developer_commit"],
        "live_request_authorized": False,
    }, sort_keys=True))


def check() -> None:
    manifest = read_json(MANIFEST_PATH, "request_manifest_unreadable")
    validate_manifest_structure(manifest)
    _validate_protected_files(manifest)
    approval = read_json(APPROVAL_PATH, "approval_gate_unreadable")
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest_rel = str(MANIFEST_PATH.relative_to(ROOT))
    manifest_blob = git("rev-parse", "HEAD:" + manifest_rel)
    reviewed_manifest_commit = approval.get("reviewed_manifest_developer_commit")
    validate_gate_metadata(
        approval,
        manifest_git_blob=manifest_blob,
        manifest_review_commit=reviewed_manifest_commit,
    )
    if (not isinstance(reviewed_manifest_commit, str) or not HEX40.fullmatch(reviewed_manifest_commit)):
        raise ValueError("reviewed_manifest_commit_invalid")
    git("merge-base", "--is-ancestor", reviewed_manifest_commit, "HEAD")
    if git("rev-parse", reviewed_manifest_commit + ":" + manifest_rel) != manifest_blob:
        raise ValueError("reviewed_manifest_blob_mismatch")
    report_bytes = TESTER_REPORT_PATH.read_bytes() if TESTER_REPORT_PATH.is_file() else None
    report_blob = git("rev-parse", "HEAD:" + str(TESTER_REPORT_PATH.relative_to(ROOT))) if report_bytes is not None else None
    validate_approval_structure(
        approval,
        manifest_sha256=sha256_bytes(manifest_bytes),
        manifest_git_blob=manifest_blob,
        tester_report_bytes=report_bytes,
        tester_report_git_blob=report_blob,
    )
    if approval.get("approved_authorization_sha256") != manifest["authorization_sha256"]:
        raise ValueError("approved_authorization_digest_mismatch")
    if approval.get("status") != "READY":
        raise ValueError("approval_not_ready")
    print("PASS: exact manifest, protected files, tester report, single-use scope and status validated")


def spend() -> None:
    check()
    approval = read_json(APPROVAL_PATH, "approval_gate_unreadable")
    if approval.get("status") != "READY":
        raise ValueError("approval_already_spent_or_not_ready")
    approval["status"] = "SPENT"
    approval["decision"] = "SPENT_BEFORE_SOURCE_REQUEST"
    approval["spent_from_commit"] = git("rev-parse", "HEAD")
    _write_json_atomic(APPROVAL_PATH, approval)
    print("PASS: one-use sample approval marked SPENT before source request")


def _write_json_atomic(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("review-check", "check", "spend"):
        raise SystemExit("usage: validate_dhan_daily_sample_approval.py review-check|check|spend")
    try:
        if sys.argv[1] == "review-check":
            review_check()
        elif sys.argv[1] == "check":
            check()
        else:
            spend()
    except Exception as exc:
        code = str(exc)
        if not re.fullmatch(r"[a-zA-Z0-9_:-]{1,120}", code):
            code = f"approval_validation_error_{type(exc).__name__}"
        print(json.dumps({"status": "BLOCKED", "failure_code": code}, sort_keys=True))
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
