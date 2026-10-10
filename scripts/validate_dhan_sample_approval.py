#!/usr/bin/env python3
"""Validate and consume a one-run Dhan sample manifest before network access."""
from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/gates/DHAN_MARKET_DATA_SAMPLE_APPROVAL.json"
REPORT = ROOT / "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md"
REQUIRED_SCOPE = "one bounded Dhan profile/IDX_I metadata and daily-candle schema sample only"
REQUIRED_FILES = {
    "research/phase7/EXTENSION2_DHAN_MARKET_DATA_RECOVERY_SPEC.md",
    "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_TESTER.md",
    "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md",
    "scripts/dhan_market_data_recovery.py",
    "scripts/test_dhan_market_data_recovery.py",
    "scripts/validate_dhan_sample_approval.py",
    ".github/workflows/phase-07-dhan-market-data-tests.yml",
    ".github/workflows/phase-07-dhan-market-data-live.yml",
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
    if manifest.get("authorized_scope") != REQUIRED_SCOPE:
        raise ValueError("scope_mismatch")
    reviewed = manifest.get("reviewed_developer_commit")
    if not isinstance(reviewed, str) or len(reviewed) != 40:
        raise ValueError("reviewed_commit_missing")
    git("merge-base", "--is-ancestor", reviewed, "HEAD")
    report_digest = sha256(REPORT)
    if report_digest != manifest.get("tester_report_sha256"):
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
        # The current code-tester report is digest-pinned separately because it
        # necessarily post-dates the reviewed code commit that it names.
        if rel != "research/gates/PHASE7_EXTENSION2_DHAN_MARKET_DATA_RECOVERY_CODE_TESTER.md":
            if git("rev-parse", reviewed + ":" + rel) != entry.get("git_blob"):
                raise ValueError("reviewed_commit_tree_blob_mismatch:" + rel)
    report_text = REPORT.read_text(encoding="utf-8")
    if "PASS WITH SCOPED RESTRICTIONS" not in report_text or "Live Dhan requests: NOT AUTHORIZED" not in report_text:
        raise ValueError("tester_report_scope_marker_missing")
    if manifest.get("full_history_authorized") is not False or manifest.get("model_fitting_authorized") is not False:
        raise ValueError("forbidden_scope_flag")
    if manifest.get("requests_max") != 6 or manifest.get("response_bytes_max") != 4 * 1024 * 1024:
        raise ValueError("request_budget_mismatch")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "spend"):
        raise SystemExit("usage: validate_dhan_sample_approval.py check|spend")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate(manifest)
    if sys.argv[1] == "check":
        print("PASS: exact Dhan manifest, report digest, protected hashes/blobs, ancestry and scope validated")
        return
    manifest["status"] = "SPENT"
    manifest["decision"] = "SPENT_BEFORE_SOURCE_REQUEST"
    manifest["spent_at_commit"] = git("rev-parse", "HEAD")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: exact Dhan manifest marked SPENT before any source request")


if __name__ == "__main__":
    main()
