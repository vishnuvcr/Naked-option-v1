#!/usr/bin/env python3
"""Fail-closed validator for the one-window Dhan spot patch after split recovery R1."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_PROPOSAL = ROOT / "research/gates/NIFTY_1M_SPOT_FAILED_WINDOW_PATCH_PROPOSAL.json"
START = dt.date(2021, 11, 8)
END = dt.date(2021, 11, 15)
REQUEST_COUNT = 7
MAX_ROWS = 500
MAX_BYTES = 4_194_304
BASE_ARTIFACT_ID = "11697215166"
BASE_ARTIFACT_SHA256 = "07e402f194a42421a1d3df6a3a8b3031c30352250ff110b085e984816405d26a"


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top_level_object_required")
    return value


def validate_proposal(proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if proposal.get("status") != "DRAFT_OFFLINE_ONLY_NOT_EXECUTABLE":
        errors.append("proposal_status_not_offline_draft")
    if proposal.get("decision_scope") != "PATCH_ONLY_PREVIOUSLY_FAILED_WINDOW_20211108_20211115":
        errors.append("proposal_scope_invalid")
    if proposal.get("previously_failed_request_id") != "GAPSPOT1M-R1-20211108-20211115":
        errors.append("previously_failed_request_id_mismatch")
    if proposal.get("previously_failed_reason") != "response_row_cap_exceeded":
        errors.append("previous_failure_reason_mismatch")
    if proposal.get("source_window_start_inclusive") != START.isoformat():
        errors.append("source_window_start_mismatch")
    if proposal.get("source_window_end_exclusive") != END.isoformat():
        errors.append("source_window_end_mismatch")
    if proposal.get("source_window_calendar_days") != (END - START).days:
        errors.append("source_window_days_mismatch")
    base = proposal.get("base_partial_artifact", {})
    if base.get("run_id") != "38124538291":
        errors.append("base_artifact_run_mismatch")
    if base.get("artifact_id") != BASE_ARTIFACT_ID:
        errors.append("base_artifact_id_mismatch")
    if base.get("artifact_sha256") != BASE_ARTIFACT_SHA256:
        errors.append("base_artifact_hash_mismatch")
    if base.get("existing_option_rows") != 8_490_723:
        errors.append("base_option_rows_mismatch")
    if base.get("existing_spot_rows") != 506_898:
        errors.append("base_spot_rows_mismatch")
    if proposal.get("preserve_existing_option_rows") is not True:
        errors.append("must_preserve_option_rows")
    if proposal.get("preserve_existing_spot_rows") is not True:
        errors.append("must_preserve_existing_spot_rows")
    if proposal.get("refetch_successful_windows") is not False:
        errors.append("must_not_refetch_successful_windows")
    if proposal.get("requests_planned") != REQUEST_COUNT or proposal.get("max_wire_requests") != REQUEST_COUNT:
        errors.append("request_budget_mismatch")
    if proposal.get("max_retry_requests") != 0 or proposal.get("max_attempts_per_request") != 1:
        errors.append("retry_budget_invalid")
    if proposal.get("max_rows_per_response") != MAX_ROWS or proposal.get("max_response_bytes") != MAX_BYTES:
        errors.append("global_response_caps_invalid")
    for field in ("live_requests_authorized", "live_option_requests_allowed",
                  "model_fitting_authorized", "holdout_access_authorized", "strategy_testing_authorized"):
        if proposal.get(field) is not False:
            errors.append(field + "_must_remain_false_in_proposal")
    requests = proposal.get("requests")
    if not isinstance(requests, list) or len(requests) != REQUEST_COUNT:
        return errors + ["request_count_invalid"]
    current = START
    seen: set[str] = set()
    for i, req in enumerate(requests):
        try:
            start = dt.date.fromisoformat(req["window_start_inclusive"])
            end = dt.date.fromisoformat(req["window_end_exclusive"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"request_{i}_date_invalid")
            continue
        if start != current or (end - start).days != 1:
            errors.append(f"request_{i}_not_contiguous_single_day")
        current = end
        if req.get("source_family") != "NIFTY_SPOT_1M":
            errors.append(f"request_{i}_source_family_invalid")
        if req.get("endpoint") != "https://api.dhan.co/v2/charts/intraday" or req.get("method") != "POST":
            errors.append(f"request_{i}_endpoint_invalid")
        if req.get("max_rows") != MAX_ROWS or req.get("max_response_bytes") != MAX_BYTES:
            errors.append(f"request_{i}_caps_invalid")
        if req.get("max_attempts") != 1:
            errors.append(f"request_{i}_attempts_invalid")
        rid = req.get("request_id", "")
        if not isinstance(rid, str) or not rid.startswith("GAPSPOT1M-PATCH-R2-") or rid in seen:
            errors.append(f"request_{i}_id_invalid")
        seen.add(rid)
        body = req.get("body", {})
        if (body.get("securityId") != "13" or body.get("exchangeSegment") != "IDX_I"
                or body.get("instrument") != "INDEX" or body.get("interval") != "1"
                or body.get("oi") is not False
                or body.get("fromDate") != start.isoformat() + " 09:15:00"
                or body.get("toDate") != start.isoformat() + " 15:30:00"):
            errors.append(f"request_{i}_instrument_or_date_body_invalid")
    if current != END:
        errors.append("requests_do_not_cover_exact_failed_window")
    return errors


def validate_authorization(
    proposal: dict[str, Any], proposal_blob_sha: str, developer_sha: str,
    workflow_blob_sha: str, decision: dict[str, Any],
) -> list[str]:
    errors = validate_proposal(proposal)
    for name, value in (("proposal_blob_sha", proposal_blob_sha),
                        ("developer_sha", developer_sha),
                        ("workflow_blob_sha", workflow_blob_sha)):
        if not re.fullmatch(r"[0-9a-f]{40}", value or ""):
            errors.append(name + "_invalid")
    if decision.get("reviewed_developer_commit") != developer_sha:
        errors.append("tester_developer_sha_mismatch")
    if decision.get("patch_proposal_blob_sha") != proposal_blob_sha:
        errors.append("tester_proposal_sha_mismatch")
    if decision.get("reviewed_workflow_blob_sha") != workflow_blob_sha:
        errors.append("tester_workflow_sha_mismatch")
    if decision.get("decision") != "PASS_WITH_SCOPED_RESTRICTIONS":
        errors.append("tester_decision_not_pass")
    if decision.get("decision_scope") != "FAILED_WINDOW_PATCH_EXECUTION":
        errors.append("tester_decision_scope_invalid")
    if decision.get("spot_failed_window_patch_authorized") is not True:
        errors.append("patch_not_authorized")
    if decision.get("live_requests_authorized") is not True:
        errors.append("live_requests_not_authorized")
    if decision.get("patch_request_limit") != REQUEST_COUNT:
        errors.append("authorized_request_limit_mismatch")
    if decision.get("patch_retry_limit") != 0:
        errors.append("authorized_retry_limit_mismatch")
    if decision.get("live_option_requests_allowed") is not False:
        errors.append("option_requests_must_remain_false")
    for field in ("model_fitting_authorized", "holdout_access_authorized", "strategy_testing_authorized"):
        if decision.get(field) is not False:
            errors.append(field + "_must_remain_false")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=pathlib.Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--proposal-blob-sha", default="")
    parser.add_argument("--developer-sha", default="")
    parser.add_argument("--workflow-blob-sha", default="")
    parser.add_argument("--decision", type=pathlib.Path)
    args = parser.parse_args(argv)
    proposal = load_json(args.proposal)
    if args.decision is None:
        errors = validate_proposal(proposal)
        result = {"status": "PROPOSAL_VALID_NO_AUTHORIZATION" if not errors else "REQUEST_CHANGES",
                  "live_requests_authorized": False, "errors": errors}
    else:
        decision = load_json(args.decision)
        errors = validate_authorization(
            proposal, args.proposal_blob_sha, args.developer_sha,
            args.workflow_blob_sha, decision,
        )
        result = {"status": "AUTHORIZED" if not errors else "DENIED",
                  "live_requests_authorized": not bool(errors), "errors": errors}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
