#!/usr/bin/env python3
"""Run the frozen PM0001 precheck against an immutable run-specific preflight report.

The existing precheck implementation remains the source of the registered rules. This
small wrapper selects the just-produced per-run preflight, and records exact provenance.
No fitting, holdout reads, raw-data export or threshold changes are allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_pm0001_data_execution_precheck_r3 as implementation  # noqa: E402


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def run_precheck_r3a(
    merged_gzip: Path,
    preflight_path: Path,
    output_path: Path,
    *,
    source_commit: str,
    workflow_run_id: str,
) -> dict[str, Any]:
    if not preflight_path.is_file():
        raise implementation.PrecheckError(f"RUN_PREFLIGHT_REPORT_MISSING:{preflight_path}")
    try:
        preflight_relative_path = preflight_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise implementation.PrecheckError("RUN_PREFLIGHT_REPORT_OUTSIDE_REPOSITORY") from exc
    preflight_raw = preflight_path.read_bytes()
    preflight_doc = implementation.read_json(preflight_path)
    if preflight_doc.get("canonical_hash_matches") is not True:
        raise implementation.PrecheckError("RUN_PREFLIGHT_CANONICAL_HASH_NOT_VERIFIED")
    if preflight_doc.get("canonical_uncompressed_csv_sha256") != implementation.DATA_SHA256:
        raise implementation.PrecheckError("RUN_PREFLIGHT_CANONICAL_DATA_HASH_MISMATCH")
    if preflight_doc.get("holdout_accessed") is not False or preflight_doc.get("model_fitting_performed") is not False:
        raise implementation.PrecheckError("RUN_PREFLIGHT_SCOPE_FLAGS_INVALID")
    # run_precheck consults this module-level input for the 80 label/fold support cells.
    implementation.DATA_PREFLIGHT = preflight_path
    report = implementation.run_precheck(merged_gzip, output_path)
    report.update({
        "source_commit": source_commit,
        "workflow_run_id": str(workflow_run_id),
        "preflight_report_path": preflight_relative_path,
        "preflight_report_git_blob_sha1": git_blob_sha1(preflight_raw),
        "preflight_report_sha256": sha256_bytes(preflight_raw),
        "precheck_runner_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "precheck_runner_git_blob_sha1": git_blob_sha1(Path(__file__).read_bytes()),
        "model_fitting_performed": False,
        "holdout_accessed": False,
        "empirical_fit_authorized": False,
    })
    output_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merged-gzip", required=True, type=Path)
    parser.add_argument("--preflight", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", "unknown"))
    parser.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID", "unknown"))
    args = parser.parse_args()
    report = run_precheck_r3a(
        args.merged_gzip, args.preflight, args.output,
        source_commit=args.source_commit,
        workflow_run_id=args.workflow_run_id,
    )
    print(json.dumps({k: v for k, v in report.items() if k not in {"rows", "feature_batch_diagnostics"}}, sort_keys=True, indent=2))
    return 0 if report.get("status") == "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING" else 2


if __name__ == "__main__":
    raise SystemExit(main())
