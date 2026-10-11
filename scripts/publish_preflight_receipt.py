#!/usr/bin/env python3
"""Build a sanitized receipt for the offline preflight Actions run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_REPORT_KEYS = {
    "status", "file_name", "file_size_bytes", "sha256", "gzip_integrity",
    "data_rows", "columns", "column_names", "recognized_timestamp_column",
    "timestamp_epoch_min", "timestamp_epoch_max", "timestamp_parse_errors",
    "recognized_row_type_counts", "null_or_blank_counts_by_column",
    "row_width_errors", "duplicate_key_check", "duplicate_key_fields",
    "duplicate_key_count", "incomplete_composite_key_rows",
    "key_group_row_counts", "limitations",
}


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
    if not isinstance(report.get("status"), str) or not isinstance(report.get("sha256"), str):
        raise ValueError("REPORT_REQUIRED_METADATA_MISSING")
    if report.get("data_rows") != 8_999_865 or report.get("columns") != 47:
        # Preserve failed/partial scan metadata, but never label it as accepted.
        receipt["receipt_status"] = "REPORT_PRESENT_WITH_EXPECTATION_MISMATCH"
    else:
        receipt["receipt_status"] = "REPORT_PRESENT"
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
