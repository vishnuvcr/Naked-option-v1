#!/usr/bin/env python3
"""Independent R4 static and synthetic code gate for Phase 8P duplicate handling."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

FORBIDDEN_IMPORTS = {
    "requests", "urllib", "httpx", "socket", "ftplib", "yfinance", "akshare",
    "huggingface_hub", "boto3",
}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def blob(root: Path, commit: str, path: str) -> str:
    return git(root, "rev-parse", commit + ":" + path)


def check(rows, failures, name, passed, detail=None):
    row = {"check": name, "pass": bool(passed)}
    if detail is not None:
        row["detail"] = detail
    rows.append(row)
    if not passed:
        failures.append(name)


def run_python(root: Path, command: list[str], timeout: int = 180):
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--developer-root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.developer_root.resolve()
    tester_root = Path.cwd().resolve()
    req = json.loads(args.request.read_text(encoding="utf-8"))
    impl = req.get("implementation", {})
    commit = str(req.get("developer_commit", ""))
    checks, failures = [], []

    current = git(root, "rev-parse", "HEAD")
    check(checks, failures, "exact_developer_commit", current == commit,
          {"expected": commit, "actual": current})

    file_specs = {
        "core_module": (impl.get("core_module_path", ""), impl.get("core_module_blob_sha1")),
        "core_test": (impl.get("core_test_path", ""), impl.get("core_test_blob_sha1")),
        "core_workflow": (impl.get("core_synthetic_workflow_path", ""), impl.get("core_synthetic_workflow_blob_sha1")),
        "diagnostic": (impl.get("diagnostic_path", ""), impl.get("diagnostic_blob_sha1")),
        "diagnostic_test": (impl.get("diagnostic_test_path", ""), impl.get("diagnostic_test_blob_sha1")),
        "diagnostic_workflow": (impl.get("diagnostic_synthetic_workflow_path", ""), impl.get("diagnostic_synthetic_workflow_blob_sha1")),
    }
    contents = {}
    for key, (path, expected) in file_specs.items():
        try:
            actual = blob(root, commit, path)
            text = (root / path).read_text(encoding="utf-8")
        except Exception as exc:
            actual, text = "", ""
            check(checks, failures, "file_read_" + key, False, type(exc).__name__)
        check(checks, failures, "exact_blob_" + key,
              bool(path) and bool(expected) and actual == expected,
              {"path": path, "expected": expected, "actual": actual})
        contents[key] = text

    flags_false = (
        req.get("real_artifact_access_authorized") is False
        and req.get("real_artifact_decryption_authorized") is False
        and req.get("real_diagnostic_authorized") is False
        and req.get("deduplication_authorized") is False
        and req.get("model_fit_authorized") is False
        and req.get("holdout_access_authorized") is False
        and req.get("external_market_source_requests_authorized") is False
    )
    check(checks, failures, "request_pending_and_authorization_flags_closed",
          req.get("status") == "PENDING_INDEPENDENT_TESTER_REVIEW" and flags_false)

    # Independently verify the pinned R4 scope decision on the tester-owned branch.
    approval = req.get("scope_approval", {})
    decision_path = approval.get("tester_decision_path", "")
    report_path = approval.get("tester_report_path", "")
    expected_decision_blob = approval.get("tester_decision_blob_sha1", "")
    expected_report_blob = approval.get("tester_report_blob_sha1", "")
    try:
        actual_decision_blob = blob(tester_root, "HEAD", decision_path)
        actual_report_blob = blob(tester_root, "HEAD", report_path)
        decision_data = json.loads(git(tester_root, "show", "HEAD:" + decision_path))
        check(checks, failures, "r4_tester_scope_decision_blob",
              actual_decision_blob == expected_decision_blob,
              {"expected": expected_decision_blob, "actual": actual_decision_blob})
        check(checks, failures, "r4_tester_scope_report_blob",
              actual_report_blob == expected_report_blob,
              {"expected": expected_report_blob, "actual": actual_report_blob})
        check(checks, failures, "r4_scope_approval_is_scope_only",
              decision_data.get("decision") == "PASS_SCOPE_AMENDMENT_ONLY_WITH_RESTRICTIONS"
              and decision_data.get("proposal_blob_sha1") == approval.get("proposal_blob_sha1")
              and decision_data.get("real_artifact_access_authorized") is False
              and decision_data.get("model_fit_authorized") is False)
    except Exception as exc:
        check(checks, failures, "r4_tester_scope_decision_read", False, type(exc).__name__)

    # Both workflows must be valid and strictly synthetic-only for this review.
    for key in ("core_workflow", "diagnostic_workflow"):
        try:
            workflow = yaml.safe_load(contents[key])
            check(checks, failures, key + "_yaml_valid",
                  isinstance(workflow, dict) and isinstance(workflow.get("jobs"), dict))
        except Exception as exc:
            check(checks, failures, key + "_yaml_valid", False, type(exc).__name__)
    core_wf = contents["core_workflow"]
    diagnostic_wf = contents["diagnostic_workflow"]
    check(checks, failures, "core_workflow_pins_r4_scope_only_decision",
          "PHASE8P_DUPLICATE_CONTRACT_SCOPE_DECISION_R2_2026-10-12.json" in core_wf
          and "ee9fb7e4cc2030a532b358e450ca1e4f0325d91b" in core_wf
          and "DUPLICATE_SCOPE_GATE_BLOCKED" in core_wf)
    check(checks, failures, "synthetic_workflows_cannot_access_real_artifacts",
          all(term not in (core_wf + diagnostic_wf) for term in (
              "HF_TOKEN", "--greek-zip", "actions/artifacts/", "download-artifact",
          )))

    diagnostic = contents["diagnostic"]
    module = contents["core_module"]
    core_test = contents["core_test"]
    diagnostic_test = contents["diagnostic_test"]

    try:
        tree = ast.parse(diagnostic)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        check(checks, failures, "no_network_or_external_market_source_imports",
              not bool(imported & FORBIDDEN_IMPORTS), sorted(imported & FORBIDDEN_IMPORTS))
        check(checks, failures, "manifest_bound_schema_checks_present",
              all(term in diagnostic for term in (
                  "read_manifest_columns", "validate_greek_manifest_columns",
                  "validate_greek_part_columns", "manifest_columns_sha256",
              )))
        check(checks, failures, "r4_economic_key_and_dynamic_signature_present",
              all(term in diagnostic for term in (
                  "_economic_contract_key", "signature_fields", "ALLOWED_CONTRACT_PROVENANCE_VARIANCE",
                  "greek_valuation_epoch_seconds", "normalized_option_type",
              )))
        check(checks, failures, "pinned_identity_precedes_manifest_and_decryption",
              diagnostic.index("verify_pinned_artifact_identity(greek_zip,")
              < diagnostic.index("read_manifest_columns(greek_zip)")
              < diagnostic.index("iter_encrypted_composite_parts(greek_zip)"))
        check(checks, failures, "no_deduplication_or_raw_rows_in_diagnostic",
              "deduplication_performed" in diagnostic and "drop_duplicates" not in diagnostic
              and "raw_keys_or_rows_emitted" in diagnostic)
        check(checks, failures, "aggregate_output_only",
              all(term in diagnostic for term in (
                  '"input_artifact_sha256"', '"option_rows_scanned"',
                  '"conflicting_signature_fields"', '"manifest_columns_sha256"',
              )))
        scan_start = diagnostic.index("def scan_frames(")
        scan_end = diagnostic.index("\\ndef run_diagnostic(", scan_start)
        scan_source = diagnostic[scan_start:scan_end]
        check(checks, failures, "r5_disk_backed_scan_and_bounded_state",
              all(term in scan_source for term in (
                  "sqlite3.connect", "tempfile.TemporaryDirectory", "CREATE TABLE entries",
                  "PRAGMA cache_size=-65536", "zlib.compress", "connection.close()",
              ))
              and "groups: dict[str, dict[str, Any]]" not in scan_source
              and "seen_contracts" not in scan_source)
        check(checks, failures, "r5_progress_is_aggregate_only_and_flushed",
              all(term in diagnostic for term in (
                  "DUP_DIAG_PROGRESS", "file=sys.stderr", "flush=True", "progress({",
                  '"parts_scanned"', '"rows_scanned"', '"option_rows_scanned"',
              ))
              and "per_part_progress_reporting" in diagnostic_test
              and "disk_backed_aggregation" in diagnostic_test)
    except Exception as exc:
        check(checks, failures, "diagnostic_static_audit", False, type(exc).__name__)

    check(checks, failures, "core_dynamic_signature_uses_manifest_columns",
          all(term in module for term in (
              "CONTRACT_REQUIRED_MANIFEST_FIELDS", "validate_greek_manifest_columns",
              "validate_greek_part_columns", "field for field in manifest_columns",
              "signature_fields",
          )) and "EXPECTED_GREEK_DATA_COLUMNS" not in module)
    check(checks, failures, "conditional_timestamps_and_unknown_columns_are_handled",
          "timestamp_fields = [field for field in CONTRACT_TIMESTAMP_FIELDS if field in signature]" in module
          and "GREEK_PART_ORDERED_COLUMNS_DO_NOT_MATCH_MANIFEST" in module
          and "CONTRACT_DUPLICATE_VALUE_TYPE_UNSUPPORTED" in module)
    check(checks, failures, "synthetic_tests_cover_manifest_and_duplicate_edge_cases",
          all(term in core_test for term in (
              "single_timestamp_columns", "synthetic_unmodeled_column",
              "GREEK_PART_ORDERED_COLUMNS_DO_NOT_MATCH_MANIFEST",
              "economic_duplicate_diagnostic", "conflicting_signature_fields",
          )) and all(term in diagnostic for term in (
              "seconds_milliseconds_timestamp_normalization", "permuted =",
              "bad_timestamp = dict(full_base, timestamp_utc=",
          )))

    # Re-run both test suites inside the exact detached developer worktree.
    commands = [
        ("core_self_test", ["python", "scripts/phase8p_greek_prediction.py", "--self-test"], 120),
        ("core_regression_suite", ["python", "scripts/test_phase8p_greek_prediction.py"], 180),
        ("diagnostic_self_test", ["python", "scripts/phase8p_duplicate_key_diagnostic.py", "--self-test"], 60),
        ("diagnostic_regression_suite", ["python", "scripts/test_phase8p_duplicate_key_diagnostic.py"], 120),
    ]
    for name, command, timeout in commands:
        try:
            result = run_python(root, command, timeout)
            detail = {
                "exit_code": result.returncode,
                "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
            }
            check(checks, failures, name, result.returncode == 0, detail)
        except Exception as exc:
            check(checks, failures, name, False, type(exc).__name__)

    source_artifact = req.get("source_artifact", {})
    check(checks, failures, "pinned_source_artifact",
          source_artifact.get("artifact_id") == 11723198817
          and source_artifact.get("sha256") == "e61c1aa845c3e58bc82506797f3ca2e8f35944d8d4cd58082a04776a25378736")

    decision = "PASS_FOR_DUPLICATE_DIAGNOSTIC_CODE_ONLY" if not failures else "REQUEST_CHANGES"
    result = {
        "schema_version": 2,
        "gate": req.get("gate", "PHASE8P_DUPLICATE_DIAGNOSTIC_CODE_REVIEW"),
        "decision": decision,
        "developer_commit": commit,
        "checks_passed": sum(bool(row["pass"]) for row in checks),
        "checks_total": len(checks),
        "failures": failures,
        "checks": checks,
        "real_artifact_accessed": False,
        "real_artifact_decrypted": False,
        "model_fitted": False,
        "holdout_accessed": False,
        "deduplication_performed": False,
        "real_diagnostic_authorized": False,
        "model_fit_authorized": False,
        "review_scope": "STATIC_AND_SYNTHETIC_ONLY",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "decision", "checks_passed", "checks_total", "failures",
        "real_artifact_accessed", "model_fitted",
    )}, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
