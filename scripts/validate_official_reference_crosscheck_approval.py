#!/usr/bin/env python3
"""Fail-closed manifest validator for the one-date official-source cross-check.

No network code is imported or called by this module. The live workflow must
validate exact hashes, confirm tester approval, then mark approval SPENT and
push that state before invoking the separate bounded runner.
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

import official_reference_crosscheck as adapter

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_REQUEST.json"
APPROVAL_PATH = ROOT / "research/gates/OFFICIAL_NIFTY_SAMPLE_CROSSCHECK_APPROVAL.json"
TESTER_REPORT_PATH = ROOT / "research/gates/PHASE7_OFFICIAL_CROSSCHECK_MANIFEST_TESTER.md"
SCOPE_ID = adapter.EXPECTED_SCOPE_ID
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")

REQUIRED_PROTECTED_FILES = {
    "scripts/dhan_instrument_master.py",
    "scripts/test_dhan_instrument_master.py",
    "scripts/official_reference_crosscheck.py",
    "scripts/test_official_reference_crosscheck.py",
    "scripts/run_official_reference_crosscheck.py",
    "scripts/test_run_official_reference_crosscheck.py",
    "scripts/validate_official_reference_crosscheck_approval.py",
    "scripts/test_validate_official_reference_crosscheck_approval.py",
    ".github/workflows/phase-07-official-crosscheck-tests.yml",
    ".github/workflows/phase-07-official-crosscheck-live.yml",
    "research/phase7/DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN.md",
    "research/gates/PHASE7_DHAN_SAMPLE_OFFICIAL_REFERENCE_CROSSCHECK_PLAN_TESTER.md",
    "research/gates/PHASE7_DHAN_SAMPLE_OFFICIAL_REFERENCE_CODE_FINAL_TESTER.md",
    "research/gates/PHASE7_DHAN_SAMPLE_OFFICIAL_REFERENCE_CODE_SUBMISSION.md",
    "research/gates/PHASE7_DHAN_SAMPLE_ARTIFACT_TESTER.md",
    "data/cache/dhan_daily_sample/478f0942f8654bd763b8343a05370f8065ef5041483cb59cc3f7dd6b57ef78ba-efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70/response.json",
    "data/cache/dhan_daily_sample/478f0942f8654bd763b8343a05370f8065ef5041483cb59cc3f7dd6b57ef78ba-efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70/manifest.json",
}

EXPECTED_SOURCE_SPECS = [
    {
        "source": "nifty_indices",
        "url": adapter.NIFTY_INDICES_URL,
        "method": "POST",
        "request_count_max": 1,
        "response_bytes_max": adapter.NIFTY_MAX_RESPONSE_BYTES,
        "timeout_seconds": adapter.NIFTY_TIMEOUT_SECONDS,
        "redirect_follow_allowed": False,
        "retry_allowed": False,
        "credential_allowed": False,
    },
    {
        "source": "dhan_instrument_master",
        "url": adapter.DHAN_COMPACT_MASTER_URL,
        "method": "GET",
        "request_count_max": 1,
        "response_bytes_max": adapter.MAX_CSV_BYTES,
        "timeout_seconds": adapter.DHAN_MASTER_TIMEOUT_SECONDS,
        "redirect_follow_allowed": False,
        "retry_allowed": False,
        "credential_allowed": False,
    },
]


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
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: pathlib.Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(code) from None
    if not isinstance(value, dict):
        raise ValueError(code)
    return value


def validate_manifest_structure(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != 1:
        raise ValueError("manifest_schema_version_invalid")
    if manifest.get("status") != "PROPOSED":
        raise ValueError("manifest_status_invalid")
    if manifest.get("decision") != "AWAITING_INDEPENDENT_MANIFEST_REVIEW":
        raise ValueError("manifest_decision_invalid")
    auth = manifest.get("authorization")
    if not isinstance(auth, dict):
        raise ValueError("manifest_authorization_missing")
    if auth.get("scope_id") != SCOPE_ID:
        raise ValueError("scope_id_mismatch")
    if auth.get("authorized_scope") != "one same-day official NIFTY OHLC lookup plus one public Dhan instrument mapping lookup":
        raise ValueError("authorized_scope_mismatch")
    if auth.get("expected_date") != adapter.EXPECTED_DATE:
        raise ValueError("expected_date_mismatch")
    if auth.get("expected_dhan_row") != adapter.EXPECTED_DHAN_ROW:
        raise ValueError("expected_dhan_row_mismatch")
    if auth.get("expected_mapping") != adapter.EXPECTED_MAPPING:
        raise ValueError("expected_mapping_mismatch")
    if auth.get("dhan_sample_response_sha256") != adapter.EXPECTED_DHAN_SAMPLE_RESPONSE_SHA256:
        raise ValueError("dhan_sample_hash_mismatch")
    if auth.get("source_specs") != EXPECTED_SOURCE_SPECS:
        raise ValueError("source_scope_mismatch")
    if auth.get("total_requests_max") != 2 or type(auth.get("total_requests_max")) is not int:
        raise ValueError("total_request_budget_invalid")
    for field in ("retries_allowed", "redirect_follow_allowed", "credential_forwarding_allowed",
                  "bulk_history_authorized", "intraday_authorized", "rolling_options_authorized",
                  "feature_engineering_authorized", "model_fitting_authorized",
                  "strategy_testing_authorized", "holdout_access_authorized", "data_acceptance_authorized"):
        if auth.get(field) is not False:
            raise ValueError("forbidden_scope_flag")
    reviewed_commit = auth.get("reviewed_developer_commit")
    if not isinstance(reviewed_commit, str) or not HEX40.fullmatch(reviewed_commit):
        raise ValueError("reviewed_developer_commit_invalid")
    protected = auth.get("protected_files")
    if not isinstance(protected, dict) or set(protected) != REQUIRED_PROTECTED_FILES:
        raise ValueError("protected_file_set_mismatch")
    for path, entry in protected.items():
        if not isinstance(entry, dict):
            raise ValueError("protected_file_entry_invalid")
        if not isinstance(entry.get("git_blob"), str) or not HEX40.fullmatch(entry["git_blob"]):
            raise ValueError("protected_file_blob_invalid")
        if not isinstance(entry.get("sha256"), str) or not HEX64.fullmatch(entry["sha256"]):
            raise ValueError("protected_file_sha256_invalid")
    if manifest.get("authorization_sha256") != canonical_sha256(auth):
        raise ValueError("authorization_digest_mismatch")


def validate_protected_files(manifest: dict[str, Any]) -> None:
    auth = manifest["authorization"]
    reviewed_commit = auth["reviewed_developer_commit"]
    git("merge-base", "--is-ancestor", reviewed_commit, "HEAD")
    for relative in sorted(REQUIRED_PROTECTED_FILES):
        item = auth["protected_files"][relative]
        path = ROOT / relative
        if not path.is_file():
            raise ValueError("protected_file_missing")
        if sha256_file(path) != item["sha256"]:
            raise ValueError("protected_file_sha256_mismatch:" + relative)
        current_blob = git("rev-parse", "HEAD:" + relative)
        reviewed_blob = git("rev-parse", reviewed_commit + ":" + relative)
        if current_blob != item["git_blob"] or reviewed_blob != item["git_blob"]:
            raise ValueError("protected_file_git_blob_mismatch:" + relative)


def validate_tester_report(
    approval: dict[str, Any],
    *,
    manifest_sha256: str,
    manifest_blob: str,
    authorization_sha256: str,
    report_bytes: bytes | None,
    report_blob: str | None,
) -> None:
    if approval.get("request_manifest_path") != str(MANIFEST_PATH.relative_to(ROOT)):
        raise ValueError("approval_manifest_path_mismatch")
    if approval.get("tester_report_path") != str(TESTER_REPORT_PATH.relative_to(ROOT)):
        raise ValueError("approval_tester_report_path_mismatch")
    if approval.get("request_manifest_sha256") != manifest_sha256:
        raise ValueError("approval_manifest_sha256_mismatch")
    if approval.get("request_manifest_git_blob") != manifest_blob:
        raise ValueError("approval_manifest_blob_mismatch")
    if approval.get("approved_authorization_sha256") != authorization_sha256:
        raise ValueError("approved_authorization_digest_mismatch")
    if not isinstance(report_bytes, bytes) or report_blob is None:
        raise ValueError("tester_report_missing")
    if sha256_bytes(report_bytes) != approval.get("tester_report_sha256"):
        raise ValueError("tester_report_sha256_mismatch")
    if report_blob != approval.get("tester_report_git_blob"):
        raise ValueError("tester_report_blob_mismatch")
    try:
        report = report_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("tester_report_encoding_invalid") from None
    for marker in (
        "PASS WITH SCOPED RESTRICTIONS",
        SCOPE_ID,
        "No public-source request is authorized",
        "No bulk",
    ):
        if marker not in report:
            raise ValueError("tester_report_scope_marker_missing")


def _write_json_atomic(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_gate() -> tuple[dict[str, Any], dict[str, Any], bytes, str, str]:
    manifest = read_json(MANIFEST_PATH, "manifest_unreadable")
    validate_manifest_structure(manifest)
    validate_protected_files(manifest)
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest_sha = sha256_bytes(manifest_bytes)
    manifest_blob = git("rev-parse", "HEAD:" + str(MANIFEST_PATH.relative_to(ROOT)))
    approval = read_json(APPROVAL_PATH, "approval_unreadable")
    report_bytes = TESTER_REPORT_PATH.read_bytes() if TESTER_REPORT_PATH.is_file() else None
    report_blob = git("rev-parse", "HEAD:" + str(TESTER_REPORT_PATH.relative_to(ROOT))) if report_bytes is not None else None
    validate_tester_report(
        approval,
        manifest_sha256=manifest_sha,
        manifest_blob=manifest_blob,
        authorization_sha256=manifest["authorization_sha256"],
        report_bytes=report_bytes,
        report_blob=report_blob,
    )
    return manifest, approval, manifest_bytes, manifest_sha, manifest_blob


def review_check() -> None:
    manifest = read_json(MANIFEST_PATH, "manifest_unreadable")
    validate_manifest_structure(manifest)
    validate_protected_files(manifest)
    approval = read_json(APPROVAL_PATH, "approval_unreadable")
    raw = MANIFEST_PATH.read_bytes()
    manifest_sha = sha256_bytes(raw)
    manifest_blob = git("rev-parse", "HEAD:" + str(MANIFEST_PATH.relative_to(ROOT)))
    if approval.get("status") != "PENDING_REVIEW":
        raise ValueError("approval_not_pending")
    if approval.get("decision") != "AWAITING_INDEPENDENT_MANIFEST_REVIEW":
        raise ValueError("approval_pending_decision_invalid")
    if approval.get("scope_id") != SCOPE_ID:
        raise ValueError("approval_scope_mismatch")
    if approval.get("request_manifest_path") != str(MANIFEST_PATH.relative_to(ROOT)):
        raise ValueError("approval_manifest_path_mismatch")
    if approval.get("request_manifest_sha256") != manifest_sha:
        raise ValueError("approval_manifest_sha256_mismatch")
    if approval.get("request_manifest_git_blob") != manifest_blob:
        raise ValueError("approval_manifest_blob_mismatch")
    if approval.get("approved_authorization_sha256") != manifest["authorization_sha256"]:
        raise ValueError("approved_authorization_digest_mismatch")
    print(json.dumps({
        "status": "PASS_MANIFEST_REVIEW_PREFLIGHT",
        "scope_id": SCOPE_ID,
        "request_manifest_sha256": manifest_sha,
        "request_manifest_git_blob": manifest_blob,
        "authorization_sha256": manifest["authorization_sha256"],
        "live_request_authorized": False,
    }, sort_keys=True))


def check() -> None:
    manifest, approval, _, _, _ = _load_gate()
    if approval.get("status") != "READY" or approval.get("decision") != "APPROVED_ONE_RUN":
        raise ValueError("approval_not_ready")
    print("PASS: exact manifest, protected files, tester report, source budgets, scope and READY status validated")


def prepare_spent(approval: dict[str, Any], *, spent_from_commit: str) -> dict[str, Any]:
    if approval.get("status") != "READY" or approval.get("decision") != "APPROVED_ONE_RUN":
        raise ValueError("approval_already_spent_or_not_ready")
    if approval.get("scope_id") != SCOPE_ID:
        raise ValueError("approval_scope_mismatch")
    if not isinstance(spent_from_commit, str) or not HEX40.fullmatch(spent_from_commit):
        raise ValueError("spent_from_commit_invalid")
    spent = dict(approval)
    spent["status"] = "SPENT"
    spent["decision"] = "SPENT_BEFORE_SOURCE_REQUEST"
    spent["authorized_scope_id"] = SCOPE_ID
    spent["spent_from_commit"] = spent_from_commit
    return spent


def spend() -> None:
    manifest, approval, _, _, _ = _load_gate()
    if approval.get("status") != "READY" or approval.get("decision") != "APPROVED_ONE_RUN":
        raise ValueError("approval_already_spent_or_not_ready")
    approval = prepare_spent(approval, spent_from_commit=git("rev-parse", "HEAD"))
    _write_json_atomic(APPROVAL_PATH, approval)
    print("PASS: one-use official cross-check approval marked SPENT before first source request")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"review-check", "check", "spend"}:
        raise SystemExit("usage: validate_official_reference_crosscheck_approval.py review-check|check|spend")
    try:
        {"review-check": review_check, "check": check, "spend": spend}[sys.argv[1]]()
    except Exception as exc:
        code = str(exc)
        if not re.fullmatch(r"[A-Za-z0-9_:-]{1,160}", code):
            code = f"gate_validation_error_{type(exc).__name__}"
        print(json.dumps({"status": "BLOCKED", "failure_code": code}, sort_keys=True))
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
