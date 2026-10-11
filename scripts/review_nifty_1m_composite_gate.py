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
    "scripts/run_nifty_1m_spot_diagnostic.py",
    "scripts/test_nifty_1m_spot_diagnostic.py",
    "scripts/audit_nifty_1m_composite_cache.py",
    "scripts/test_audit_nifty_1m_composite_cache.py",
    "scripts/account_nifty_1m_probe_attempt.py",
    "scripts/test_account_nifty_1m_probe_attempt.py",
    "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_PLAN.json",
    ".github/workflows/phase-07-nifty-1m-composite-live.yml",
    ".github/workflows/phase-07-nifty-1m-composite-tests.yml",
    ".github/workflows/phase-07-nifty-1m-composite-spot-diagnostic.yml",
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
    mandatory_spot_fields = {"timestamp", "open", "high", "low", "close"}
    if not mandatory_spot_fields.issubset(fields_found):
        add(findings, "BLOCKER", "SPOT_OHLC_FIELDS_NOT_SCHEMA_GUARDED",
            "Spot parser must strictly validate timestamp and every OHLC array.")
    elif ('volume_unusable' not in source or 'SPOT_VOLUME_MISSING_OR_MISALIGNED' not in source
          or 'spot_volume_missing_or_misaligned' not in source):
        add(findings, "BLOCKER", "SPOT_VOLUME_DEGRADATION_NOT_EXPLICIT",
            "Missing/empty/misaligned volume must remain blank and be quality-flagged rather than zero-filled.")
    else:
        add(findings, "INFO", "SPOT_OHLC_STRICT_VOLUME_DEGRADED",
            "Timestamp/OHLC arrays remain mandatory and aligned; unusable volume stays blank and is quality-flagged.")

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
         "scripts/validate_nifty_1m_composite_approval.py", "scripts/run_nifty_1m_spot_diagnostic.py",
         "scripts/test_nifty_1m_spot_diagnostic.py", "scripts/audit_nifty_1m_composite_cache.py",
         "scripts/account_nifty_1m_probe_attempt.py", "scripts/test_account_nifty_1m_probe_attempt.py",
         "scripts/test_audit_nifty_1m_composite_cache.py"],
        ["python", "-m", "unittest", "-v", "test_nifty_1m_composite_manifest"],
        ["python", "-m", "unittest", "-v", "test_nifty_1m_composite_dataset"],
        ["python", "-m", "unittest", "-v", "test_nifty_1m_spot_diagnostic"],
        ["python", "-m", "unittest", "-v", "test_account_nifty_1m_probe_attempt"],
        ["python", "-m", "unittest", "-v", "test_audit_nifty_1m_composite_cache"],
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


def request_scope_digest(request: dict[str, Any]) -> str:
    scope = {"endpoint": request.get("endpoint"), "method": request.get("method"), "body": request.get("body")}
    return sha256(json.dumps(scope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def check_diagnostic_scope(target: pathlib.Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    """Independently validate exactly one non-persisting spot diagnostic request."""
    plan_path = target / "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_PLAN.json"
    manifest_path = target / "research/gates/NIFTY_1M_COMPOSITE_REQUESTS_2026.json"
    script_path = target / "scripts/run_nifty_1m_spot_diagnostic.py"
    workflow_path = target / ".github/workflows/phase-07-nifty-1m-composite-spot-diagnostic.yml"
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        add(findings, "BLOCKER", "SPOT_DIAGNOSTIC_PLAN_OR_MANIFEST_INVALID",
            "Tester cannot parse the exact diagnostic plan and the frozen 2026 request manifest.")
        return {"status": "BLOCKED", "reason": "PLAN_OR_MANIFEST_INVALID"}
    matches = [r for r in manifest.get("requests", []) if r.get("request_id") == plan.get("request_id")]
    required_false = ("persist_raw_response", "write_response_cache", "write_csv_rows",
                      "export_market_rows", "log_market_values", "log_credentials",
                      "model_fitting_authorized", "holdout_access_authorized", "strategy_testing_authorized")
    if (plan.get("status") != "DRAFT_FOR_AUTOMATED_TESTER_REVIEW"
            or plan.get("max_wire_requests") != 1 or plan.get("max_retries") != 0
            or plan.get("source_family") != "NIFTY_SPOT_1M" or len(matches) != 1
            or matches[0].get("source_family") != "NIFTY_SPOT_1M"
            or matches[0].get("endpoint") != plan.get("endpoint")
            or plan.get("endpoint") != "https://api.dhan.co/v2/charts/intraday"
            or plan.get("request_id") != "SPOT1M-20260915-20261011"
            or any(plan.get(k) is not False for k in required_false)):
        add(findings, "BLOCKER", "SPOT_DIAGNOSTIC_SCOPE_NOT_EXACT",
            "Diagnostic must be one frozen-manifest spot request, no retry, no cache/export/logged market values or model scope.")
        return {"status": "BLOCKED", "reason": "SCOPE_INVALID"}
    if not script_path.is_file() or not workflow_path.is_file():
        add(findings, "BLOCKER", "SPOT_DIAGNOSTIC_EXECUTOR_MISSING",
            "The exact diagnostic runner or automatic workflow is missing.")
        return {"status": "BLOCKED", "reason": "EXECUTOR_MISSING"}
    script = script_path.read_text(encoding="utf-8")
    workflow = workflow_path.read_text(encoding="utf-8")
    script_markers = ("wire_requests\": 1", "retries\": 0", "raw_response_persisted\": False",
                      "cache_written\": False", "market_values_logged\": False",
                      "NoRedirect()", "response.read(cap + 1)", "parse_spot_response")
    workflow_markers = ("workflow_run:", "phase-07-tester", "diagnostic_probe_authorized",
                        "NIFTY_1M_SPOT_DIAGNOSTIC_EXECUTION.json", "DHAN_ACCESS_TOKEN",
                        "run_nifty_1m_spot_diagnostic.py")
    if any(marker not in script for marker in script_markers) or any(marker not in workflow for marker in workflow_markers):
        add(findings, "BLOCKER", "SPOT_DIAGNOSTIC_SAFEGUARD_MISSING",
            "Diagnostic runner/workflow is missing one-request, no-persistence or exact tester-decision guards.")
        return {"status": "BLOCKED", "reason": "SAFEGUARD_MISSING"}
    result = {"status": "PASS", "request_id": plan["request_id"],
              "request_scope_sha256": request_scope_digest(matches[0]),
              "max_wire_requests": 1, "max_retries": 0, "persist_raw_response": False,
              "write_response_cache": False, "export_market_rows": False}
    add(findings, "INFO", "SPOT_DIAGNOSTIC_EXACT_SCOPE_PASS",
        "The one-request diagnostic scope is pinned to the frozen request manifest and writes only sanitized metadata.")
    return result


def check_spot_recovery_scope(target: pathlib.Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    """Review the no-option-refetch guard before a separate 61-spot recovery."""
    collector_path = target / "scripts/run_nifty_1m_composite_dataset.py"
    audit_path = target / "scripts/audit_nifty_1m_composite_cache.py"
    account_path = target / "scripts/account_nifty_1m_probe_attempt.py"
    workflow_path = target / ".github/workflows/phase-07-nifty-1m-composite-spot-diagnostic.yml"
    try:
        collector = collector_path.read_text(encoding="utf-8")
        audit = audit_path.read_text(encoding="utf-8")
        accounting = account_path.read_text(encoding="utf-8")
        workflow = workflow_path.read_text(encoding="utf-8")
    except Exception:
        add(findings, "BLOCKER", "SPOT_RECOVERY_GUARD_FILES_MISSING",
            "Spot-only recovery requires the collector's cache-only option mode, an independent cache auditor and an automatic workflow.")
        return {"status": "BLOCKED", "reason": "RECOVERY_GUARD_FILES_MISSING"}
    required_collector = ("allow_live: bool = True", "allow_live=not spot_only_recovery",
                          "--spot-only-recovery", "live_option_requests_enabled",
                          "def _normalize_epoch_timestamp", "response_timestamp_not_integer_epoch")
    required_audit = ("option_cache_valid", "option_cache_missing", "source_requests_made",
                      "wire_requests_reserved_for_spot", "8540", "61",
                      "EXPECTED_PRESERVED_OPTION_ROWS", "cached_option_rows",
                      "8_490_723", "not invalid")
    required_accounting = ("AUTHORIZED_NONPERSISTING_DIAGNOSTIC", "wire_delta", "request_scope_sha256",
                           "raw_response_persisted", "ALREADY_ACCOUNTED")
    required_workflow = ("audit_nifty_1m_composite_cache.py", "NIFTY_1M_SPOT_RECOVERY_EXECUTION.json",
                         "SPOT_ONLY_CACHE_PRESERVING_RECOVERY", "run_nifty_1m_composite_dataset.py --spot-only-recovery",
                         "nifty1m-composite-", "account_nifty_1m_probe_attempt.py",
                         "createWorkflowDispatch", 'ref: "phase-07-developer"',
                         "github.ref == 'refs/heads/phase-07-developer'")
    missing_collector = [marker for marker in required_collector if marker not in collector]
    missing_audit = [marker for marker in required_audit if marker not in audit]
    missing_accounting = [marker for marker in required_accounting if marker not in accounting]
    missing_workflow = [marker for marker in required_workflow if marker not in workflow]
    if missing_collector or missing_audit or missing_accounting or missing_workflow:
        detail = (
            "missing_collector=" + ",".join(missing_collector)
            + ";missing_audit=" + ",".join(missing_audit)
            + ";missing_accounting=" + ",".join(missing_accounting)
            + ";missing_workflow=" + ",".join(missing_workflow)
        )
        add(findings, "BLOCKER", "SPOT_RECOVERY_CACHE_ONLY_GUARD_MISSING",
            "Recovery workflow must count the diagnostic wire attempt, prove all 8,540 option caches are valid and disable live option refetches before the one-use marker is spent. " + detail)
        return {"status": "BLOCKED", "reason": "CACHE_ONLY_GUARD_MISSING",
                "missing_collector": missing_collector, "missing_audit": missing_audit,
                "missing_accounting": missing_accounting, "missing_workflow": missing_workflow}
    result = {"status": "PASS", "spot_request_limit": 61, "option_cache_required": 8540,
              "live_option_requests_allowed": False, "cache_audit_required": True}
    add(findings, "INFO", "SPOT_RECOVERY_CACHE_ONLY_SCOPE_PASS",
        "The separate recovery runner requires a valid cache for every option request and forbids live option refetches.")
    return result


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

    parser_path = target / "scripts/run_nifty_1m_composite_dataset.py"
    test_path = target / "scripts/test_nifty_1m_composite_dataset.py"
    approval_path = target / "scripts/validate_nifty_1m_composite_approval.py"
    workflow_path = target / ".github/workflows/phase-07-nifty-1m-composite-live.yml"
    tests_source = test_path.read_text(encoding="utf-8") if test_path.is_file() else ""
    parser_source = parser_path.read_text(encoding="utf-8") if parser_path.is_file() else ""
    approval_source = approval_path.read_text(encoding="utf-8") if approval_path.is_file() else ""
    workflow_source = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""

    check_parser(parser_source, findings)
    diagnostic_scope = check_diagnostic_scope(target, findings)
    recovery_scope = check_spot_recovery_scope(target, findings)
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
    diagnostic_result_path = target / "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_RESULT.json"
    diagnostic_execution_path = target / "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_EXECUTION.json"
    recovery_execution_path = target / "research/gates/NIFTY_1M_SPOT_RECOVERY_EXECUTION.json"
    diagnostic_result: dict[str, Any] = {}
    diagnostic_execution: dict[str, Any] = {}
    if diagnostic_result_path.is_file():
        try:
            diagnostic_result = json.loads(diagnostic_result_path.read_text(encoding="utf-8"))
        except Exception:
            add(findings, "BLOCKER", "SPOT_DIAGNOSTIC_RESULT_INVALID", "Diagnostic result exists but is not valid JSON.")
    if diagnostic_execution_path.is_file():
        try:
            diagnostic_execution = json.loads(diagnostic_execution_path.read_text(encoding="utf-8"))
        except Exception:
            add(findings, "BLOCKER", "SPOT_DIAGNOSTIC_EXECUTION_MARKER_INVALID", "Diagnostic execution marker is invalid.")
    diagnostic_already_spent = diagnostic_execution_path.is_file()
    recovery_already_spent = recovery_execution_path.is_file()
    probe_authorized = (
        diagnostic_scope.get("status") == "PASS"
        and not diagnostic_already_spent
        and not diagnostic_result_path.is_file()
    )
    diagnostic_result_bound = (
        diagnostic_result.get("developer_reviewed_sha") == diagnostic_execution.get("reviewed_developer_commit")
        and diagnostic_result.get("request_scope_sha256") == diagnostic_scope.get("request_scope_sha256")
        and diagnostic_execution.get("request_id") == "SPOT1M-20260915-20261011"
        and diagnostic_execution.get("scope") == "ONE_NONPERSISTING_SPOT_SCHEMA_DIAGNOSTIC"
        and diagnostic_execution.get("max_wire_requests") == 1
        and diagnostic_execution.get("max_retries") == 0
    )
    lengths = diagnostic_result.get("array_lengths", {})
    expected_candle_arrays = {"timestamp", "open", "high", "low", "close", "volume"}
    aligned_candle_arrays = (
        set(lengths) == expected_candle_arrays
        and len({lengths.get(field) for field in expected_candle_arrays}) == 1
        and int(lengths.get("timestamp", 0)) > 0
    )
    timestamp_normalizer_tested = (
        "def _normalize_epoch_timestamp" in parser_source
        and "test_spot_parser_normalizes_integral_epoch_timestamp_encodings" in tests_source
    )
    diagnostic_parser_ok_or_known_timestamp_encoding_gap = (
        diagnostic_result.get("parser_status") in {"PARSED_OK", "PARSED_WITH_VOLUME_GAP"}
        and int(diagnostic_result.get("row_count", 0)) > 0
    ) or (
        diagnostic_result.get("parser_status") == "PARSER_REJECTED"
        and diagnostic_result.get("parser_reason") == "response_timestamp_not_integer_epoch"
        and aligned_candle_arrays
        and timestamp_normalizer_tested
    )
    diagnostic_ready_for_recovery = (
        diagnostic_result_bound
        and diagnostic_result.get("request_id") == "SPOT1M-20260915-20261011"
        and diagnostic_result.get("http_status") == 200
        and diagnostic_parser_ok_or_known_timestamp_encoding_gap
        and diagnostic_result.get("raw_response_persisted") is False
        and diagnostic_result.get("cache_written") is False
        and diagnostic_result.get("market_values_logged") is False
        and diagnostic_result.get("wire_requests") == 1
        and diagnostic_result.get("retries") == 0
    )
    recovery_authorized = (
        diagnostic_ready_for_recovery and recovery_scope.get("status") == "PASS"
        and not recovery_already_spent
    )
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
        "diagnostic_scope_review": diagnostic_scope,
        "spot_recovery_scope_review": recovery_scope,
        "diagnostic_probe_authorized": bool(probe_authorized and verdict != "REQUEST_CHANGES"),
        "spot_recovery_authorized": bool(recovery_authorized and verdict != "REQUEST_CHANGES"),
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
