#!/usr/bin/env python3
"""Run the exact, tester-authorized one-week NIFTY spot patch; never touch option endpoints."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import run_nifty_1m_composite_dataset as collector
import run_nifty_1m_spot_gapfill as gapfill
import decrypt_nifty_1m_composite as decryptor
import validate_nifty_1m_spot_failed_window_patch as patch_validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATCH_MARKER = ROOT / "research/gates/NIFTY_1M_SPOT_FAILED_WINDOW_PATCH_EXECUTION.json"
PATCH_RESULT = ROOT / "research/gates/NIFTY_1M_SPOT_FAILED_WINDOW_PATCH_RESULT.json"
EXPECTED_OPTION_ROWS = 8_490_723
BASE_SPOT_ROWS = 506_898
BASE_WIRE_ATTEMPTS = 8_687
BASE_RETRY_ATTEMPTS = 5


def _git_blob_sha(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _json_write(path: pathlib.Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _existing_spot_epochs(parts: list[pathlib.Path]) -> set[int]:
    epochs: set[int] = set()
    row_count = 0
    for path in parts:
        for row in gapfill._iter_gzip_rows(path):
            if row.get("row_type") != "SPOT":
                continue
            row_count += 1
            epoch = int(row["timestamp_epoch"])
            if epoch in epochs:
                raise ValueError("duplicate_timestamp_in_existing_spot_rows")
            epochs.add(epoch)
    if row_count != BASE_SPOT_ROWS or len(epochs) != BASE_SPOT_ROWS:
        raise ValueError("existing_spot_rows_not_exactly_preserved")
    return epochs


def _save_failure(exc: Exception, args: argparse.Namespace) -> None:
    text = str(exc) if str(exc) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", str(exc)) else type(exc).__name__
    _json_write(PATCH_RESULT, {
        "schema_version": 1,
        "result_type": "SPOT_ONLY_FAILED_WINDOW_PATCH",
        "status": "PATCH_EXECUTION_FAILED",
        "reviewed_developer_commit": args.reviewed_sha,
        "patch_proposal_blob_sha": args.proposal_blob_sha,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "error_code": text,
        "raw_market_values_committed": False,
        "live_option_requests_allowed": False,
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
        "strategy_testing_authorized": False,
        "completed_at_utc": collector.utc_now(),
    })


def execute_patch(args: argparse.Namespace) -> int:
    token = os.environ.get("DHAN_ACCESS_TOKEN", "").strip()
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not token or not hf_token:
        raise ValueError("required_secret_not_configured")
    proposal_path = args.patch_proposal.resolve()
    proposal = patch_validator.load_json(proposal_path)
    proposal_errors = patch_validator.validate_proposal(proposal)
    if proposal_errors:
        raise ValueError("patch_proposal_invalid:" + ",".join(proposal_errors[:8]))
    if not args.proposal_blob_sha or _git_blob_sha(proposal_path) != args.proposal_blob_sha:
        raise ValueError("patch_proposal_blob_sha_mismatch")
    marker = gapfill._load_object(PATCH_MARKER)
    base = proposal["base_partial_artifact"]
    if (marker.get("status") != "SPENT_BEFORE_SOURCE_REQUEST"
            or marker.get("scope") != "PATCH_ONLY_PREVIOUSLY_FAILED_WINDOW"
            or marker.get("reviewed_developer_commit") != args.reviewed_sha
            or marker.get("patch_proposal_blob_sha") != args.proposal_blob_sha
            or marker.get("max_patch_requests") != 7
            or marker.get("max_retry_requests") != 0
            or marker.get("base_artifact_id") != patch_validator.BASE_ARTIFACT_ID
            or marker.get("base_artifact_sha256") != patch_validator.BASE_ARTIFACT_SHA256
            or marker.get("live_option_requests_allowed") is not False
            or not marker.get("tester_decision_blob")
            or not marker.get("reviewed_workflow_blob_sha")):
        raise ValueError("failed_window_patch_marker_missing_or_scope_mismatch")

    source_dir = args.source_dir.resolve()
    plain_dir = args.plain_dir.resolve()
    base_spot_rows = int(proposal["expected_existing_spot_rows"])
    if base_spot_rows != BASE_SPOT_ROWS:
        raise ValueError("proposal_expected_spot_rows_mismatch")
    preflight = gapfill.preflight(
        source_dir, plain_dir, hf_token,
        expected_spot_rows=base_spot_rows,
        expected_artifact_run_id=int(base["run_id"]),
    )
    if preflight.get("status") != "PASS":
        raise ValueError("encrypted_partial_artifact_preflight_failed")

    normalized = gapfill._normalize_artifact_layout(source_dir)
    old_coverage = gapfill._load_object(normalized / "coverage_and_errors.json")
    old_manifest = decryptor.read_manifest(normalized)
    old_summary = old_coverage.get("summary", {})
    if int(old_summary.get("rows_options", -1)) != EXPECTED_OPTION_ROWS or int(old_summary.get("rows_spot", -1)) != BASE_SPOT_ROWS:
        raise ValueError("base_coverage_summary_mismatch")
    old_current_gapfill = old_coverage.get("gapfill_request_results", [])
    old_prior_gapfill = old_coverage.get("previous_gapfill_request_results", [])
    if not isinstance(old_current_gapfill, list) or not isinstance(old_prior_gapfill, list):
        raise ValueError("base_gapfill_history_invalid")
    old_all_gapfill = list(old_prior_gapfill) + list(old_current_gapfill)
    prior_cumulative = int(old_summary.get("gapfill_request_count_cumulative_planned",
                                           old_summary.get("gapfill_request_count_planned", 0)))
    if len(old_all_gapfill) != prior_cumulative or prior_cumulative != 81:
        raise ValueError("base_gapfill_history_count_mismatch")
    if (int(old_summary.get("gapfill_request_count_cumulative_succeeded", -1)) != 74
            or int(old_summary.get("gapfill_request_count_cumulative_failed", -1)) != 7):
        raise ValueError("base_gapfill_outcome_counts_mismatch")

    key = gapfill.derive_key(hf_token)
    base_parts = [path for path in plain_dir.glob("nifty_1m_composite_*.csv.gz")]
    if not base_parts:
        raise ValueError("decrypted_base_parts_missing")
    existing_epochs = _existing_spot_epochs(base_parts)

    if gapfill.WORK_ROOT.exists():
        shutil.rmtree(gapfill.WORK_ROOT)
    gapfill.WORK_ROOT.mkdir(parents=True, exist_ok=True)
    if gapfill.ENCRYPTED_ROOT.exists():
        shutil.rmtree(gapfill.ENCRYPTED_ROOT)
    ledger_path = args.attempt_ledger.resolve()
    ledger = gapfill._read_ledger(ledger_path)
    gap_collector = gapfill.SpotGapFillCollector(
        token=token,
        key=key,
        requests=proposal["requests"],
        ledger=ledger,
        baseline_wire_attempts=BASE_WIRE_ATTEMPTS,
        baseline_retry_attempts=BASE_RETRY_ATTEMPTS,
        ledger_path=ledger_path,
    )
    gap = gap_collector.collect()
    if len(gap["spot_by_epoch"]) != int(gap["rows_spot"]):
        raise ValueError("duplicate_spot_timestamp_across_patch_shards")
    overlap = existing_epochs.intersection(gap["spot_by_epoch"].keys())
    if overlap:
        raise ValueError("new_spot_timestamp_overlaps_preserved_base")

    row_counts, joins = gapfill.merge_into_existing_dataset(
        base_parts, gapfill.WORK_ROOT, gap["spot_by_epoch"],
        preserve_existing_spot_rows=True,
    )
    rows_options = int(joins["rows_options_out"])
    rows_spot_total = int(joins["rows_spot_out"])
    if rows_options != EXPECTED_OPTION_ROWS:
        raise ValueError("merged_option_row_count_changed")
    if rows_spot_total != BASE_SPOT_ROWS + int(gap["rows_spot"]):
        raise ValueError("merged_existing_spot_row_count_changed")

    success_statuses = {"CACHE_HIT", "FETCHED", "FETCHED_AFTER_ONE_RETRY"}
    succeeded = sum(item.get("status") in success_statuses for item in gap["request_results"])
    failed = len(proposal["requests"]) - succeeded
    old_cumulative_succeeded = int(old_summary.get("gapfill_request_count_cumulative_succeeded", 0))
    old_cumulative_failed = int(old_summary.get("gapfill_request_count_cumulative_failed", 0))
    all_errors = list(old_coverage.get("errors", [])) + list(gap["errors"])
    all_request_results = list(old_coverage.get("request_results", [])) + list(gap["request_results"])

    session_dates: set[str] = set()
    for path in gapfill.PLAIN_ROOT.glob("nifty_1m_composite_*.csv.gz"):
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("row_type") == "SPOT":
                    session_dates.add(row.get("session_date", ""))

    spot_recovery_status = "SPOT_GAPFILL_COMPLETE" if (
        failed == 0 and int(joins["spot_join_missing"]) == 0
        and old_coverage.get("status") == "COMPLETE"
    ) else "SPOT_GAPFILL_PARTIAL"
    patch_status = "SPOT_PATCH_REQUESTS_VALID" if failed == 0 else "SPOT_PATCH_REQUESTS_PARTIAL"
    summary = {
        **{key: old_summary.get(key) for key in (
            "request_count_planned", "failed_responses", "empty_valid_responses",
            "missing_greek_inputs", "historical_option_request_grid_status"
        )},
        "request_count_processed": int(old_summary.get("request_count_processed", 0)) + len(proposal["requests"]),
        "gapfill_request_count_planned": len(proposal["requests"]),
        "gapfill_request_count_succeeded": succeeded,
        "gapfill_request_count_failed": failed,
        "gapfill_request_count_cumulative_planned": prior_cumulative + len(proposal["requests"]),
        "gapfill_request_count_cumulative_succeeded": old_cumulative_succeeded + succeeded,
        "gapfill_request_count_cumulative_failed": old_cumulative_failed + failed,
        "wire_requests_this_run": gap["wire_requests_this_run"],
        "wire_requests_cumulative": gap["wire_requests_cumulative"],
        "retry_requests_this_run": gap["retry_requests_this_run"],
        "retry_requests_cumulative": gap["retry_requests_cumulative"],
        "rows_options": rows_options,
        "original_rows_options": EXPECTED_OPTION_ROWS,
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "rows_spot": rows_spot_total,
        "spot_rows_existing_preserved": BASE_SPOT_ROWS,
        "spot_rows_downloaded": int(gap["rows_spot"]),
        "spot_join_matched": int(joins["spot_join_matched"]),
        "spot_join_missing": int(joins["spot_join_missing"]),
        "spot_recovery_status": spot_recovery_status,
        "spot_volume_quality_flag_count": int(old_summary.get("spot_volume_quality_flag_count", 0)) + sum(
            "SPOT_VOLUME_MISSING_OR_MISALIGNED" in row.get("data_quality_flags", "")
            for row in gap["spot_by_epoch"].values()
        ),
        "observed_trading_session_count": len(session_dates),
        "cache_hits": int(old_summary.get("cache_hits", 0)) + gap["cache_hits"],
        "fresh_responses": int(old_summary.get("fresh_responses", 0)) + gap["fresh_responses"],
        "downloaded_bytes": int(old_summary.get("downloaded_bytes", 0)) + gap["downloaded_bytes"],
        "response_bytes_this_run": gap["downloaded_bytes"],
        "previous_downloaded_bytes_reconciled_from_request_results": True,
        "source_requests_made_this_run": gap["wire_requests_this_run"],
        "live_option_requests_allowed": False,
        "raw_response_persisted_unencrypted": False,
        "patch_requests_planned": len(proposal["requests"]),
        "patch_requests_succeeded": succeeded,
        "patch_requests_failed": failed,
        "patch_requests_max_rows": 500,
        "patch_requests_max_response_bytes": 4_194_304,
    }
    result = {
        "schema_version": 1,
        "dataset_id": old_manifest.get("dataset_id", "NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10_SPOT_GAPFILL"),
        "created_at_utc": collector.utc_now(),
        "status": "PARTIAL_GRID",
        "spot_gapfill_status": spot_recovery_status,
        "spot_patch_status": patch_status,
        "source_provider": "DhanHQ Data API",
        "history_start_inclusive": "2021-10-11",
        "history_end_exclusive": "2026-10-11",
        "interval": "1-minute",
        "user_acceptance": "Patch only the previously failed 2021-11-08 to 2021-11-15 spot interval. Preserve all existing option and spot rows.",
        "schema_columns": list(old_manifest.get("columns", gapfill.COLUMNS)),
        "rows_per_month": dict(sorted(row_counts.items())),
        "summary": summary,
        "errors": all_errors,
        "request_results": all_request_results,
        "gapfill_request_results": list(gap["request_results"]),
        "previous_gapfill_request_results": old_all_gapfill,
        "original_request_failures_preserved": old_coverage.get("original_request_failures_preserved", len(all_errors)),
        "missing_greek_inputs": old_coverage.get("missing_greek_inputs", []),
        "greek_method": old_coverage.get("greek_method", old_manifest.get("greek_method", "")),
        "greek_iv_unit_convention": old_coverage.get("greek_iv_unit_convention", old_manifest.get("greek_iv_unit_convention", "")),
        "spot_join_policy": "Exact timestamp_epoch join only. Existing spot rows are retained unchanged; unmatched option targets remain blank.",
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
        "strategy_testing_authorized": False,
        "source_artifact_run_id": old_coverage.get("source_artifact_run_id", "38116772719"),
        "base_partial_artifact_run_id": str(base["run_id"]),
        "base_partial_artifact_id": str(base["artifact_id"]),
        "base_partial_artifact_sha256": base["artifact_sha256"],
        "patch_proposal_blob_sha": args.proposal_blob_sha,
        "patch_workflow_blob_sha": marker["reviewed_workflow_blob_sha"],
        "source_artifact_encrypted_hashes_verified": True,
        "source_rows_options_verified": EXPECTED_OPTION_ROWS,
        "source_rows_spot_preserved": rows_spot_total >= BASE_SPOT_ROWS,
        "plain_rows_uploaded": False,
    }
    gapfill.encrypt_outputs(key, result)
    shutil.rmtree(plain_dir, ignore_errors=True)
    shutil.rmtree(gapfill.WORK_ROOT, ignore_errors=True)
    shutil.rmtree(ROOT / "data/recovery/source-artifact", ignore_errors=True)

    safe = {
        "schema_version": 1,
        "result_type": "SPOT_ONLY_FAILED_WINDOW_PATCH",
        "status": patch_status,
        "dataset_status": "PARTIAL_GRID",
        "spot_gapfill_status": spot_recovery_status,
        "reviewed_developer_commit": args.reviewed_sha,
        "patch_proposal_blob_sha": args.proposal_blob_sha,
        "patch_workflow_blob_sha": marker["reviewed_workflow_blob_sha"],
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "base_partial_artifact_id": str(base["artifact_id"]),
        "base_partial_artifact_sha256": base["artifact_sha256"],
        "summary": summary,
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "existing_spot_rows_preserved": rows_spot_total >= BASE_SPOT_ROWS,
        "raw_market_values_committed": False,
        "live_option_requests_allowed": False,
        "model_fitting_authorized": False,
        "holdout_access_authorized": False,
        "strategy_testing_authorized": False,
        "completed_at_utc": collector.utc_now(),
    }
    gapfill.atomic_write(PATCH_RESULT, (json.dumps(safe, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({
        "status": patch_status, "dataset_status": "PARTIAL_GRID",
        "option_rows_preserved": rows_options == EXPECTED_OPTION_ROWS,
        "existing_spot_rows_preserved": rows_spot_total >= BASE_SPOT_ROWS,
        "spot_rows_new": int(gap["rows_spot"]), "spot_rows_total": rows_spot_total,
        "spot_join_matched": int(joins["spot_join_matched"]), "spot_join_missing": int(joins["spot_join_missing"]),
        "requests_planned": len(proposal["requests"]), "requests_succeeded": succeeded, "requests_failed": failed,
        "wire_requests_this_run": gap["wire_requests_this_run"], "wire_requests_cumulative": gap["wire_requests_cumulative"],
        "retry_requests_this_run": gap["retry_requests_this_run"], "market_values_logged": False,
    }, sort_keys=True))
    return 0 if failed == 0 else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True, type=pathlib.Path)
    parser.add_argument("--plain-dir", required=True, type=pathlib.Path)
    parser.add_argument("--patch-proposal", type=pathlib.Path,
                        default=ROOT / "research/gates/NIFTY_1M_SPOT_FAILED_WINDOW_PATCH_PROPOSAL.json")
    parser.add_argument("--proposal-blob-sha", required=True)
    parser.add_argument("--reviewed-sha", required=True)
    parser.add_argument("--attempt-ledger", required=True, type=pathlib.Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"status": "DRY_RUN_NOT_AUTHORIZED", "live_requests_made": False}))
        return 2
    try:
        return execute_patch(args)
    except Exception as exc:
        _save_failure(exc, args)
        safe_text = str(exc) if str(exc) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", str(exc)) else type(exc).__name__
        print(json.dumps({"status": "PATCH_EXECUTION_FAILED", "error_code": safe_text,
                          "raw_market_values_logged": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
