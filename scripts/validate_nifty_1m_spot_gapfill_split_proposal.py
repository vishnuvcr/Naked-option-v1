#!/usr/bin/env python3
"""Fail-closed offline validator for the proposed retry of six row-capped spot windows."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_PROPOSAL = ROOT / "research/gates/NIFTY_1M_SPOT_GAPFILL_SPLIT_PROPOSAL.json"
EXPECTED_START = dt.date(2021, 10, 11)
EXPECTED_END = dt.date(2022, 6, 2)
EXPECTED_REQUESTS = 34
EXPECTED_MAX_DAYS = 7
EXPECTED_MAX_ROWS = 4000
EXPECTED_MAX_BYTES = 8_388_608
EXPECTED_ARTIFACT_ID = "11693866249"
EXPECTED_ARTIFACT_SHA256 = "aff6e392df65e7dc5995cf1188af77815edb8ec02a84bc2d64156a9bb5c83216"


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top_level_object_required")
    return value


def validate_proposal(proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if proposal.get("status") != "DRAFT_OFFLINE_ONLY_NOT_EXECUTABLE":
        errors.append("proposal_status_not_offline_draft")
    if proposal.get("decision_scope") != "RETRY_ONLY_SIX_FAILED_SPOT_WINDOWS":
        errors.append("proposal_scope_invalid")
    if proposal.get("source_windows_start_inclusive") != EXPECTED_START.isoformat():
        errors.append("proposal_start_mismatch")
    if proposal.get("source_windows_end_exclusive") != EXPECTED_END.isoformat():
        errors.append("proposal_end_mismatch")
    if proposal.get("base_partial_artifact", {}).get("artifact_id") != EXPECTED_ARTIFACT_ID:
        errors.append("partial_base_artifact_id_mismatch")
    if proposal.get("base_partial_artifact", {}).get("artifact_sha256") != EXPECTED_ARTIFACT_SHA256:
        errors.append("partial_base_artifact_hash_mismatch")
    if proposal.get("base_partial_artifact", {}).get("existing_option_rows") != 8_490_723:
        errors.append("existing_option_row_count_mismatch")
    if proposal.get("base_partial_artifact", {}).get("existing_spot_rows") != 403_664:
        errors.append("existing_spot_row_count_mismatch")
    if proposal.get("preserve_existing_spot_rows") is not True:
        errors.append("existing_spot_rows_not_preserved")
    if proposal.get("refetch_successful_windows") is not False:
        errors.append("successful_windows_must_not_be_refetched")
    for field in ("live_requests_authorized", "live_option_requests_allowed",
                  "model_fitting_authorized", "holdout_access_authorized", "strategy_testing_authorized"):
        if proposal.get(field) is not False:
            errors.append(field + "_must_remain_false")
    requests = proposal.get("requests")
    if not isinstance(requests, list) or len(requests) != EXPECTED_REQUESTS:
        return errors + ["proposal_request_count_invalid"]
    if proposal.get("requests_planned") != EXPECTED_REQUESTS or proposal.get("max_wire_requests") != EXPECTED_REQUESTS:
        errors.append("proposal_wire_budget_mismatch")
    if proposal.get("max_retry_requests") != 0 or proposal.get("max_attempts_per_request") != 1:
        errors.append("proposal_retry_budget_invalid")
    current = EXPECTED_START
    seen_ids: set[str] = set()
    for index, request in enumerate(requests):
        try:
            start = dt.date.fromisoformat(request["window_start_inclusive"])
            end = dt.date.fromisoformat(request["window_end_exclusive"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"request_{index}_date_invalid")
            continue
        if start != current or end <= start:
            errors.append(f"request_{index}_gap_or_overlap")
        if (end - start).days > EXPECTED_MAX_DAYS:
            errors.append(f"request_{index}_window_too_long")
        if request.get("source_family") != "NIFTY_SPOT_1M":
            errors.append(f"request_{index}_source_family_invalid")
        if request.get("endpoint") != "https://api.dhan.co/v2/charts/intraday" or request.get("method") != "POST":
            errors.append(f"request_{index}_endpoint_invalid")
        if request.get("max_rows") != EXPECTED_MAX_ROWS or request.get("max_response_bytes") != EXPECTED_MAX_BYTES:
            errors.append(f"request_{index}_response_cap_invalid")
        if request.get("max_attempts") != 1:
            errors.append(f"request_{index}_must_have_one_attempt")
        request_id = request.get("request_id")
        if not isinstance(request_id, str) or request_id in seen_ids or not request_id.startswith("GAPSPOT1M-R1-"):
            errors.append(f"request_{index}_id_invalid")
        else:
            seen_ids.add(request_id)
        body = request.get("body", {})
        last_day = (end - dt.timedelta(days=1)).isoformat()
        if (body.get("securityId") != "13" or body.get("exchangeSegment") != "IDX_I"
                or body.get("instrument") != "INDEX" or body.get("interval") != "1"
                or body.get("oi") is not False
                or body.get("fromDate") != start.isoformat() + " 09:15:00"
                or body.get("toDate") != last_day + " 15:30:00"):
            errors.append(f"request_{index}_body_scope_invalid")
        current = end
    if current != EXPECTED_END:
        errors.append("proposal_does_not_cover_full_failed_interval")
    return errors


def validate_exact_authorization(
    proposal: dict[str, Any],
    proposal_blob_sha: str,
    developer_sha: str,
    decision: dict[str, Any],
) -> list[str]:
    """A missing, stale or broadly scoped decision is never treated as authorization."""
    errors = validate_proposal(proposal)
    if not re.fullmatch(r"[0-9a-f]{40}", proposal_blob_sha or ""):
        errors.append("proposal_blob_sha_invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", developer_sha or ""):
        errors.append("developer_sha_invalid")
    if decision.get("reviewed_developer_commit") != developer_sha:
        errors.append("tester_developer_sha_mismatch")
    decision_proposal_sha = decision.get("split_proposal_blob_sha", decision.get("proposal_blob_sha"))
    if decision_proposal_sha != proposal_blob_sha:
        errors.append("tester_proposal_blob_sha_mismatch")
    if decision.get("decision") != "PASS_WITH_SCOPED_RESTRICTIONS":
        errors.append("tester_decision_not_pass")
    if decision.get("decision_scope") != "SPLIT_RECOVERY_EXECUTION":
        errors.append("tester_scope_not_split_recovery_execution")
    if decision.get("split_recovery_authorized") is not True:
        errors.append("split_recovery_not_authorized")
    if decision.get("live_requests_authorized") is not True:
        errors.append("live_requests_not_authorized")
    if decision.get("split_recovery_request_limit") != EXPECTED_REQUESTS:
        errors.append("authorized_request_limit_mismatch")
    if decision.get("split_recovery_retry_limit") != 0:
        errors.append("authorized_retry_limit_mismatch")
    if decision.get("live_option_requests_allowed") is not False:
        errors.append("live_option_requests_must_remain_false")
    for field in ("model_fitting_authorized", "holdout_access_authorized", "strategy_testing_authorized"):
        if decision.get(field) is not False:
            errors.append(field + "_must_remain_false")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=pathlib.Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--proposal-blob-sha", default="")
    parser.add_argument("--developer-sha", default="")
    parser.add_argument("--decision", type=pathlib.Path)
    args = parser.parse_args(argv)
    proposal = load_json(args.proposal)
    if args.decision is None:
        errors = validate_proposal(proposal)
        result = {"status": "PROPOSAL_VALID_NO_AUTHORIZATION" if not errors else "REQUEST_CHANGES",
                  "live_requests_authorized": False, "errors": errors}
    else:
        decision = load_json(args.decision)
        errors = validate_exact_authorization(proposal, args.proposal_blob_sha, args.developer_sha, decision)
        result = {"status": "AUTHORIZED" if not errors else "DENIED",
                  "live_requests_authorized": not bool(errors), "errors": errors}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
