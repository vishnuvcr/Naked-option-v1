#!/usr/bin/env python3
"""Validate and spend a one-request Dhan redirect-target diagnostic manifest."""
from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/gates/DHAN_REDIRECT_TARGET_APPROVAL.json"
REPORT = ROOT / "research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_TESTER.md"
SCOPE = "one Dhan instrument metadata request to record redirect scheme/hostname only; no redirect follow"
REQUIRED_FILES = {
    "research/phase7/EXTENSION2_DHAN_REDIRECT_TARGET_DISCOVERY_SPEC.md",
    "research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_TESTER.md",
    "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md",
    "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md",
    "scripts/dhan_market_data_recovery.py",
    "scripts/test_dhan_market_data_recovery.py",
    "scripts/validate_dhan_redirect_probe_approval.py",
    ".github/workflows/phase-07-dhan-market-data-tests.yml",
    ".github/workflows/phase-07-dhan-redirect-probe-live.yml",
}
REPORT_PATHS = {
    "research/gates/PHASE7_EXTENSION2_DHAN_REDIRECT_TARGET_TESTER.md",
    "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md",
    "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md",
}


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError("git_validation_failed")
    return result.stdout.strip()


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate(manifest: dict) -> None:
    if manifest.get("decision") != "APPROVED_ONE_RUN" or manifest.get("status") != "READY":
        raise ValueError("manifest_not_ready")
    if manifest.get("authorized_scope") != SCOPE:
        raise ValueError("scope_mismatch")
    reviewed = manifest.get("reviewed_developer_commit")
    if not isinstance(reviewed, str) or len(reviewed) != 40:
        raise ValueError("reviewed_commit_missing")
    git("merge-base", "--is-ancestor", reviewed, "HEAD")
    if sha256(REPORT) != manifest.get("tester_report_sha256"):
        raise ValueError("tester_report_digest_mismatch")
    files = manifest.get("protected_files")
    if not isinstance(files, dict) or set(files) != REQUIRED_FILES:
        raise ValueError("protected_file_set_mismatch")
    for rel in sorted(REQUIRED_FILES):
        p = ROOT / rel
        if not p.is_file():
            raise ValueError("protected_file_missing")
        entry = files[rel]
        if not isinstance(entry, dict):
            raise ValueError("protected_file_record_invalid")
        if sha256(p) != entry.get("sha256"):
            raise ValueError("protected_file_sha256_mismatch:" + rel)
        if git("rev-parse", "HEAD:" + rel) != entry.get("git_blob"):
            raise ValueError("protected_file_git_blob_mismatch:" + rel)
        if rel not in REPORT_PATHS and git("rev-parse", reviewed + ":" + rel) != entry.get("git_blob"):
            raise ValueError("reviewed_commit_tree_blob_mismatch:" + rel)
    report_text = REPORT.read_text(encoding="utf-8")
    if "PASS WITH SCOPED RESTRICTIONS" not in report_text or "Live request authorized: NONE" not in report_text:
        raise ValueError("tester_report_scope_marker_missing")
    if manifest.get("full_history_authorized") is not False or manifest.get("model_fitting_authorized") is not False:
        raise ValueError("forbidden_scope_flag")
    if manifest.get("requests_max") != 1 or manifest.get("response_bytes_max") != 1024:
        raise ValueError("request_budget_mismatch")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "spend"):
        raise SystemExit("usage: validate_dhan_redirect_probe_approval.py check|spend")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate(manifest)
    if sys.argv[1] == "check":
        print("PASS: exact redirect-probe manifest/report/files/tree/scope validated")
        return
    manifest["status"] = "SPENT"
    manifest["decision"] = "SPENT_BEFORE_SOURCE_REQUEST"
    manifest["spent_at_commit"] = git("rev-parse", "HEAD")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: redirect-probe manifest marked SPENT before source request")


if __name__ == "__main__":
    main()
