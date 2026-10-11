#!/usr/bin/env python3
"""Independent Phase 7 composite-acquisition gate review.

This file belongs to phase-07-tester. It reads a separate developer checkout,
does not modify that checkout, and emits a concise machine-readable report.
It deliberately does not authorize source requests, modelling, or holdout access.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone
from typing import Any

FILES = [
    "scripts/run_nifty_1m_composite_dataset.py",
    "scripts/test_nifty_1m_composite_dataset.py",
    "scripts/validate_nifty_1m_composite_manifest.py",
    "scripts/validate_nifty_1m_composite_approval.py",
    ".github/workflows/phase-07-nifty-1m-composite-live.yml",
    ".github/workflows/phase-07-nifty-1m-composite-tests.yml",
]
REQUIRED_FIELDS = ["timestamp", "open", "high", "low", "close", "volume"]
REQUIRED_TEST_MARKERS = {
    "missing-volume response": r"test_spot_parser_rejects_missing_volume",
    "empty-volume response": r"test_spot_parser_rejects_empty_volume",
    "misaligned volume array": r"test_spot_parser_rejects_misaligned_volume",
    "invalid timestamp types": r"test_spot_parser_rejects_noninteger_timestamp",
    "separate OHLC misalignment": r"test_spot_parser_rejects_each_misaligned_ohlc_array",
    "sanitized parser-reason logging": r"test_safe_exception_reason_logs_only_bounded_reason_tokens",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    if proc.returncode:
        return ""
    return proc.stdout.strip()


def add(findings: list[dict[str, str]], severity: str, code: str, message: str) -> None:
    findings.append({"severity": severity, "code": code, "message": message})


def function_source(tree: ast.AST, name: str) -> ast.AST | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def check_parser(source: str, findings: list[dict[str, str]]) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        add(findings, "BLOCKER", "PYTHON_SYNTAX_ERROR", f"Parser file does not compile at line {exc.lineno}.")
        return
    parse_fn = function_source(tree, "parse_spot_response")
    if parse_fn is None:
        add(findings, "BLOCKER", "SPOT_PARSER_MISSING", "parse_spot_response was not found.")
        return
    fields_found: set[str] = set()
    for node in ast.walk(parse_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_array_set":
            if len(node.args) >= 2 and isinstance(node.args[1], ast.List):
                fields_found = {x.value for x in node.args[1].elts if isinstance(x, ast.Constant) and isinstance(x.value, str)}
                break
    if not set(REQUIRED_FIELDS).issubset(fields_found):
        add(findings, "BLOCKER", "SPOT_FIELDS_NOT_SCHEMA_GUARDED",
            "Spot parser does not validate timestamp, OHLC, and volume together. Dhan's documented intraday response includes volume; do not remove it without exact response evidence.")
    else:
        add(findings, "INFO", "SPOT_RESPONSE_FIELDS_REQUIRED",
            "Spot parser requires timestamp, OHLC, and volume arrays, consistent with Dhan's documented response shape.")

    safe_fn = function_source(tree, "_safe_exception_reason")
    if safe_fn is None:
        add(findings, "BLOCKER", "SANITIZED_DIAGNOSTIC_MISSING", "No bounded _safe_exception_reason function exists.")
    else:
        uses_safe = any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_safe_exception_reason"
            for n in ast.walk(tree)
        )
        if not uses_safe:
            add(findings, "BLOCKER", "SANITIZED_DIAGNOSTIC_UNUSED",
                "The bounded exception-reason sanitizer is defined but not used.")
        elif "unexpected_" not in source or "_safe_exception_reason(exc)" not in source:
            add(findings, "BLOCKER", "PARSER_REASON_NOT_RECORDED",
                "Unexpected parser errors are not recorded with the bounded sanitized reason.")
        else:
            add(findings, "INFO", "SANITIZED_DIAGNOSTIC_PRESENT",
                "Unexpected validation errors retain a bounded reason token without logging payload bodies.")


def run_offline_tests(root: pathlib.Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    tests = [
        ["python", "-m", "py_compile", "scripts/run_nifty_1m_composite_dataset.py",
         "scripts/decrypt_nifty_1m_composite.py", "scripts/validate_nifty_1m_composite_manifest.py",
         "scripts/test_nifty_1m_composite_dataset.py", "scripts/test_nifty_1m_composite_manifest.py",
         "scripts/validate_nifty_1m_composite_approval.py"],
        ["python", "-m", "unittest", "-v", "test_nifty_1m_composite_manifest"],
        ["python", "-m", "unittest", "-v", "test_nifty_1m_composite_dataset"],
    ]
    results = []
    for command in tests:
        cwd = root / "scripts" if "unittest" in command else root
        proc = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=300, check=False)
        output_lines = [line for line in proc.stdout.splitlines() if line.strip()]
        results.append({
            "command": " ".join(command),
            "exit_code": proc.returncode,
            "output_tail": output_lines[-15:],
        })
        if proc.returncode:
            add(findings, "BLOCKER", "OFFLINE_TEST_FAILED",
                f"Offline check {command[0]} {command[1]} failed with exit code {proc.returncode}.")
    return {"checks": results, "passed": all(r["exit_code"] == 0 for r in results)}


def review(target: pathlib.Path, reviewed_sha: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    hashes: dict[str, dict[str, str | int]] = {}
    for rel in FILES:
        path = target / rel
        if not path.is_file():
            add(findings, "BLOCKER", "REQUIRED_FILE_MISSING", f"Required gate file is missing: {rel}.")
            continue
        raw = path.read_bytes()
        hashes[rel] = {
            "git_blob": git(target, "rev-parse", f"HEAD:{rel}"),
            "sha256": sha256(raw),
            "bytes": len(raw),
        }

    parser_path = target / FILES[0]
    test_path = target / FILES[1]
    approval_path = target / FILES[3]
    workflow_path = target / FILES[4]
    tests_source = test_path.read_text(encoding="utf-8") if test_path.is_file() else ""
    parser_source = parser_path.read_text(encoding="utf-8") if parser_path.is_file() else ""
    approval_source = approval_path.read_text(encoding="utf-8") if approval_path.is_file() else ""
    workflow_source = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""

    check_parser(parser_source, findings)
    for label, marker in REQUIRED_TEST_MARKERS.items():
        if not re.search(marker, tests_source):
            add(findings, "BLOCKER", "MISSING_REGRESSION_CASE", f"Missing explicit regression coverage: {label}.")
        else:
            add(findings, "INFO", "REGRESSION_CASE_PRESENT", f"Regression coverage exists: {label}.")

    guard_requirements = {
        "tester approval validation": "validate_nifty_1m_composite_approval.py check",
        "approval spent before network access": "validate_nifty_1m_composite_approval.py spend",
        "manual live-run confirmation": "inputs.confirm_live_acquisition == true",
        "encrypted-only export": "encrypted/*.csv.gz.enc",
        "no force push": "git push origin HEAD:phase-07-developer",
    }
    for label, marker in guard_requirements.items():
        if marker not in workflow_source:
            add(findings, "BLOCKER", "LIVE_GUARD_REGRESSION", f"Live workflow safeguard missing: {label}.")
    if "force-with-lease" in workflow_source or re.search(r"git\s+push[^\n]*\s--force(?:\s|$)", workflow_source):
        add(findings, "BLOCKER", "FORCE_PUSH_PRESENT", "Live workflow must never force-push research status.")

    forbidden = [
        'model_fitting_authorized": true',
        'holdout_access_authorized": true',
        'live_requests_authorized": true',
    ]
    for marker in forbidden:
        if marker in approval_source:
            add(findings, "BLOCKER", "FORBIDDEN_SCOPE_LITERAL", f"Approval validator contains forbidden permission literal: {marker}.")

    offline = run_offline_tests(target, findings)
    blockers = [f for f in findings if f["severity"] == "BLOCKER"]
    verdict = "REQUEST_CHANGES" if blockers else "PASS_WITH_SCOPED_RESTRICTIONS"
    return {
        "schema_version": 1,
        "review_type": "INDEPENDENT_AUTOMATED_TESTER_CHECK",
        "reviewed_developer_commit": reviewed_sha,
        "observed_checkout_commit": git(target, "rev-parse", "HEAD"),
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": hashes,
        "offline_tests": offline,
        "verdict": verdict,
        "live_requests_authorized": False,
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=pathlib.Path)
    parser.add_argument("--reviewed-sha", required=True)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    report = review(args.target.resolve(), args.reviewed_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "reviewed_developer_commit": report["reviewed_developer_commit"],
        "verdict": report["verdict"],
        "blocker_count": sum(f["severity"] == "BLOCKER" for f in report["findings"]),
        "live_requests_authorized": False,
    }, sort_keys=True))
    return 0 if report["verdict"] != "REQUEST_CHANGES" else 1


if __name__ == "__main__":
    raise SystemExit(main())
