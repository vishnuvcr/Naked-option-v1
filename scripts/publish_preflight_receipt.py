#!/usr/bin/env python3
"""Build a sanitized receipt for the offline preflight Actions run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_REPORT_KEYS = {
    "status", "file_name", "file_size_bytes", "sha256", "gzip_integrity",
    "expected_compressed_sha256", "compressed_sha256_matches_expected",
    "uncompressed_sha256", "expected_uncompressed_sha256", "uncompressed_sha256_matches_expected",
    "uncompressed_size_bytes", "expected_uncompressed_size_bytes", "uncompressed_size_matches_expected",
    "data_rows", "columns", "column_names", "recognized_timestamp_column",
    "timestamp_epoch_min", "timestamp_epoch_max", "timestamp_parse_errors",
    "recognized_row_type_counts", "null_or_blank_counts_by_column",
    "row_width_errors", "duplicate_key_check", "duplicate_key_fields",
    "duplicate_key_count", "incomplete_composite_key_rows",
    "key_group_row_counts", "limitations",
}
ALLOWED_LIMITATIONS = {
    "This is structural preflight only, not modelling-readiness approval.",
    "Unparseable timestamps and incomplete composite identifiers are reported but not repaired.",
    "This scan does not establish session-calendar correctness, target validity, leakage safety, exact spot joins, or OHLC semantics.",
    "No market row values are emitted in this report.",
    "Gzip container metadata may change on recompression; the exact uncompressed CSV byte hash and byte count are checked separately.",
}
ALLOWED_STATUSES = {
    "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS",
    "PREFLIGHT_REVIEW_DUPLICATE_CHECK_NOT_ESTIMABLE",
    "PREFLIGHT_FAIL_DUPLICATE_KEYS",
    "PREFLIGHT_REVIEW_TIMESTAMP_PARSE_ERRORS",
    "PREFLIGHT_REVIEW_INCOMPLETE_COMPOSITE_KEYS",
    "PREFLIGHT_FAIL_UNCOMPRESSED_SHA256",
    "PREFLIGHT_FAIL_UNCOMPRESSED_SIZE",
    "PREFLIGHT_FAIL_ROW_WIDTH",
    "PREFLIGHT_FAIL_ROW_COUNT",
}
SAFE_NAME = __import__("re").compile(r"^[A-Za-z_][A-Za-z0-9_ .:/-]{0,99}$")


def build_receipt(run_metadata: dict, report_path: Path | None) -> dict:
    receipt = {
        "schema_version": 1,
        "source_workflow_run_id": run_metadata.get("id"),
        "source_workflow_name": run_metadata.get("name"),
        "source_head_sha": run_metadata.get("head_sha"),
        "source_head_branch": run_metadata.get("head_branch"),
        "source_conclusion": run_metadata.get("conclusion"),
        "source_status": run_metadata.get("status"),
        "source_created_at": run_metadata.get("created_at"),
        "report_available": False,
        "receipt_status": "NO_SANITIZED_REPORT",
        "report": None,
    }
    if not report_path or not report_path.is_file():
        return receipt
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("REPORT_SCHEMA_NOT_OBJECT")
    unexpected = sorted(set(report) - ALLOWED_REPORT_KEYS)
    if unexpected:
        raise ValueError("REPORT_CONTAINS_UNAPPROVED_FIELDS")
    required_hash_fields = (
        "sha256", "expected_compressed_sha256",
        "uncompressed_sha256", "expected_uncompressed_sha256",
    )
    if not isinstance(report.get("status"), str) or any(not isinstance(report.get(k), str) for k in required_hash_fields):
        raise ValueError("REPORT_REQUIRED_METADATA_MISSING")
    for field in required_hash_fields:
        value = report[field]
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            raise ValueError("REPORT_SHA256_INVALID")
    for field in (
        "compressed_sha256_matches_expected",
        "uncompressed_sha256_matches_expected",
        "uncompressed_size_matches_expected",
    ):
        if not isinstance(report.get(field), bool):
            raise ValueError("REPORT_CONTENT_IDENTITY_FLAG_INVALID")
    for field in ("uncompressed_size_bytes", "expected_uncompressed_size_bytes"):
        value = report.get(field)
        if not isinstance(value, int) or value < 0:
            raise ValueError("REPORT_CONTENT_SIZE_INVALID")
    if report.get("file_name") != "nifty_repaired_composite_2021-10_to_2026-10.csv.gz":
        raise ValueError("REPORT_FILE_NAME_INVALID")
    if report.get("status") not in ALLOWED_STATUSES:
        raise ValueError("REPORT_STATUS_INVALID")
    if not isinstance(report.get("column_names"), list) or not all(isinstance(x, str) and SAFE_NAME.fullmatch(x) for x in report["column_names"]):
        raise ValueError("REPORT_COLUMN_NAMES_INVALID")
    if report.get("recognized_timestamp_column") not in report["column_names"] and report.get("recognized_timestamp_column") is not None:
        raise ValueError("REPORT_TIMESTAMP_COLUMN_INVALID")
    for field in ("data_rows", "columns", "file_size_bytes", "timestamp_parse_errors", "row_width_errors"):
        if not isinstance(report.get(field), int) or report[field] < 0:
            raise ValueError("REPORT_COUNT_FIELD_INVALID")
    for field in ("null_or_blank_counts_by_column", "recognized_row_type_counts"):
        value = report.get(field)
        if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, int) and v >= 0 for k, v in value.items()):
            raise ValueError("REPORT_COUNT_MAP_INVALID")
    if not isinstance(report.get("limitations"), list) or not all(x in ALLOWED_LIMITATIONS for x in report["limitations"]):
        raise ValueError("REPORT_LIMITATIONS_INVALID")
    if report.get("gzip_integrity") != "PASS":
        raise ValueError("REPORT_GZIP_STATUS_INVALID")
    if report.get("duplicate_key_check") not in {"PASS", "NOT_ESTIMABLE_NO_RECOGNIZED_COMPOSITE_KEY", "FAIL_DUPLICATE_KEYS_FOUND", "PARTIAL_INCOMPLETE_COMPOSITE_KEYS"}:
        raise ValueError("REPORT_DUPLICATE_CHECK_INVALID")
    for field in ("duplicate_key_count", "incomplete_composite_key_rows"):
        value = report.get(field)
        if value is not None and (not isinstance(value, int) or value < 0):
            raise ValueError("REPORT_COUNT_FIELD_INVALID")
    for field in ("timestamp_epoch_min", "timestamp_epoch_max"):
        value = report.get(field)
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            raise ValueError("REPORT_TIMESTAMP_EXTREMA_INVALID")
    if not all(isinstance(k, str) and SAFE_NAME.fullmatch(k) for k in report["recognized_row_type_counts"]):
        raise ValueError("REPORT_ROW_TYPE_NAME_INVALID")
    groups = report.get("key_group_row_counts")
    if not isinstance(groups, dict):
        raise ValueError("REPORT_KEY_GROUP_COUNTS_INVALID")
    for group in groups.values():
        if not isinstance(group, dict) or not isinstance(group.get("fields"), list) or not all(name in report["column_names"] for name in group["fields"]):
            raise ValueError("REPORT_KEY_GROUP_COUNTS_INVALID")
        if not isinstance(group.get("rows_assigned"), int) or group["rows_assigned"] < 0:
            raise ValueError("REPORT_KEY_GROUP_COUNTS_INVALID")
    if not set(report["null_or_blank_counts_by_column"]).issubset(set(report["column_names"])):
        raise ValueError("REPORT_NULL_COUNT_COLUMN_INVALID")
    if not isinstance(report.get("duplicate_key_fields"), list):
        raise ValueError("REPORT_KEY_FIELDS_INVALID")
    if not all(isinstance(group, list) and all(name in report["column_names"] for name in group) for group in report["duplicate_key_fields"]):
        raise ValueError("REPORT_KEY_FIELDS_INVALID")
    if report.get("uncompressed_sha256_matches_expected") is not True or report.get("uncompressed_size_matches_expected") is not True:
        receipt["receipt_status"] = "REPORT_PRESENT_CONTENT_IDENTITY_MISMATCH"
    elif report.get("data_rows") != 8_999_865 or report.get("columns") != 47:
        receipt["receipt_status"] = "REPORT_PRESENT_WITH_EXPECTATION_MISMATCH"
    elif report.get("status") != "PREFLIGHT_PASS_WITH_SCOPED_RESTRICTIONS":
        receipt["receipt_status"] = "REPORT_PRESENT_NONPASS"
    elif report.get("compressed_sha256_matches_expected") is False:
        receipt["receipt_status"] = "REPORT_PRESENT_PASS_CONTENT_HASH_VERIFIED"
    else:
        receipt["receipt_status"] = "REPORT_PRESENT_PASS"
    receipt["report_available"] = True
    receipt["report"] = report
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-metadata", required=True)
    parser.add_argument("--report", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_metadata = json.loads(Path(args.run_metadata).read_text(encoding="utf-8"))
    report_path = Path(args.report) if args.report else None
    receipt = build_receipt(run_metadata, report_path)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt_status": receipt["receipt_status"],
        "source_workflow_run_id": receipt["source_workflow_run_id"],
        "report_available": receipt["report_available"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
