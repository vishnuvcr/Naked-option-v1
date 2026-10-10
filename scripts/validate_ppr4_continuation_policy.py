#!/usr/bin/env python3
"""Offline validation for the user-directed PPR-4 data continuation policy.

Local-only: no network calls, market-row reads, secrets, acquisition, or fitting.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "research/phase7/PPR4_USER_DIRECTED_DATA_CONTINUATION_POLICY.json"
WAIVER_PATH = ROOT / "research/gates/DHAN_SAMPLE_USER_ACCEPTANCE_WAIVER.json"
PLAN_PATH = ROOT / "research/phase7/PPR4_DHAN_OPEN_SOURCE_ACQUISITION_PLAN.md"


def load_json(path: pathlib.Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name}: top-level JSON object required")
    return obj


def validate() -> list[str]:
    errors: list[str] = []
    try:
        policy = load_json(POLICY_PATH)
        waiver = load_json(WAIVER_PATH)
        plan = PLAN_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"file_read_or_json_error:{type(exc).__name__}:{exc}"]

    directives = policy.get("user_directives", {})
    for key, expected in {
        "accept_dhan_values_as_returned": True,
        "external_cross_source_dhan_value_reconciliation_required": False,
        "research_stops_due_only_to_missing_source": False,
        "use_free_alternatives_when_dhan_lacks_feature": True,
        "combine_sources_with_explicit_lineage": True,
        "paid_sources_allowed_before_free_options_exhausted": False,
    }.items():
        if directives.get(key) is not expected:
            errors.append(f"policy_directive_mismatch:{key}")

    continuation = policy.get("continuation_rules", {})
    if continuation.get("global_research_stop_on_source_unavailability") is not False:
        errors.append("global_research_must_not_stop_on_source_unavailability")
    if continuation.get("source_failure_scope") != "SOURCE_OR_FEATURE_FAMILY_ONLY":
        errors.append("source_failure_scope_must_be_feature_family_local")
    if "NOT_ESTIMABLE" not in continuation.get("when_all_sources_for_a_family_fail", ""):
        errors.append("all-source-failure_must_be_classified_NOT_ESTIMABLE")
    if len(continuation.get("fallback_order", [])) < 4:
        errors.append("fallback_order_incomplete")
    if policy.get("execution_gate", {}).get("live_data_requests_authorized_by_this_policy_file") is not False:
        errors.append("policy_file_must_not_self_authorize_live_requests")
    if policy.get("execution_gate", {}).get("existing_one_use_dhan_approval_reusable") is not False:
        errors.append("spent_one_use_approval_must_not_be_reused")
    if policy.get("research_boundaries", {}).get("holdout_sessions") != 252:
        errors.append("prospective_holdout_session_count_changed_without_amendment")
    if policy.get("research_boundaries", {}).get("label_maturity_tail_sessions") != 10:
        errors.append("prospective_holdout_maturity_tail_changed_without_amendment")

    budget = policy.get("acquisition_budget_contract", {})
    if budget.get("serial_requests_per_second_max") != 2:
        errors.append("serial_rate_limit_must_be_two_requests_per_second")
    if budget.get("daily_dhan_request_budget_max") != 8701:
        errors.append("daily_dhan_request_budget_mismatch")
    daily = budget.get("daily_index", {})
    if (daily.get("request_max") != 40 or daily.get("response_bytes_max") != 1048576
            or daily.get("aggregate_bytes_max") != 20971520 or daily.get("rows_per_response_max") != 400):
        errors.append("daily_index_budget_mismatch")
    intraday = budget.get("intraday_index", {})
    if (intraday.get("request_max") != 70 or intraday.get("provider_window_days_max") != 90
            or intraday.get("chunk_calendar_days") != 30
            or intraday.get("response_bytes_max") != 8388608
            or intraday.get("aggregate_bytes_max") != 268435456):
        errors.append("intraday_budget_mismatch")
    options = budget.get("rolling_options", {})
    if (options.get("request_max") != 8540 or options.get("provider_window_days_max") != 30
            or options.get("chunk_calendar_days") != 30
            or options.get("expiry_flags") != ["WEEK", "MONTH"]
            or options.get("expiry_code_values") != [0, 1, 2]
            or options.get("strike_grid_by_expiry_code", {}).get("0") is None
            or len(options.get("strike_grid_by_expiry_code", {}).get("0", [])) != 21
            or len(options.get("strike_grid_by_expiry_code", {}).get("1", [])) != 7
            or len(options.get("strike_grid_by_expiry_code", {}).get("2", [])) != 7
            or options.get("option_types") != ["CALL", "PUT"]
            or options.get("interval_minutes") != 1
            or options.get("response_bytes_max") != 2097152
            or options.get("aggregate_bytes_max") != 8589934592
            or options.get("rows_per_response_max") != 10000
            or options.get("max_retry_requests_total") != 100):
        errors.append("rolling_options_budget_or_grid_mismatch")
    if budget.get("base_planned_requests") != 8601 or budget.get("max_wire_requests_including_retries") != 8701:
        errors.append("composite_request_total_mismatch")
    if options.get("greeks_policy", "").find("otherwise") < 0:
        errors.append("historical_greeks_missing_input_policy_missing")
    cache = policy.get("cache_contract", {})
    if cache.get("verify_before_fetch") is not True:
        errors.append("persisted_cache_must_be_verified_before_fetch")
    if cache.get("fetch_only_missing_or_invalid_manifest_approved_shards") is not True:
        errors.append("workflow_must_fetch_only_missing_or_invalid_approved_shards")
    if "GitHub Actions artifacts are temporary diagnostics, not authoritative cache" not in cache.get("authoritative_cache_hierarchy", []):
        errors.append("actions_artifacts_must_not_be_authoritative_cache")

    w_directives = waiver.get("user_directives", {})
    if waiver.get("decision") != "ACCEPT_DHAN_OUTPUT_AS_PROVIDED_BY_USER_DIRECTIVE":
        errors.append("dhan_waiver_decision_mismatch")
    if w_directives.get("accept_provider_values_without_external_market_value_cross_check") is not True:
        errors.append("user_waiver_must_accept_dhan_without_external_cross_check")
    if w_directives.get("require_nse_or_third_party_price_reconciliation") is not False:
        errors.append("dhan_cross_source_reconciliation_must_be_waived")
    if waiver.get("use_scope", {}).get("accepted_for_development_research") is not True:
        errors.append("existing_dhan_sample_not_marked_accepted_for_development")
    if waiver.get("use_scope", {}).get("final_holdout_access_authorized") is not False:
        errors.append("user_sample_waiver_must_not_open_final_holdout")
    sample = waiver.get("accepted_source_sample", {})
    digest = sample.get("response_sha256", "")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        errors.append("dhan_sample_response_sha256_invalid")
    if sample.get("row_count") != 1 or sample.get("response_bytes") != 121:
        errors.append("dhan_sample_receipt_fields_mismatch")

    required_plan_parts = [
        "Initial Dhan acquisition wave",
        "Free-source fallback matrix",
        "Composite-data rules",
        "Research continuation / no-source-stop rule",
        "90 days per request",
        "30 days per request",
        "no Dhan-versus-NSE/third-party market-value cross-check",
        "Paytm Money",
        "GitHub Release assets",
        "not the authoritative long-term data cache",
        "8,540",
        "8 GiB",
        "8,701",
        "one-minute",
        "Black–Scholes",
    ]
    for required in required_plan_parts:
        if required.lower() not in plan.lower():
            errors.append(f"plan_missing_required_term:{required}")

    # The variable name is allowed; a secret value must never be stored here.
    forbidden_patterns = [
        r"(?i)DHAN_ACCESS_TOKEN\s*[:=]\s*['\"][^'\"]{12,}['\"]",
        r"(?i)(access-token|authorization)\s*[:=]\s*['\"][A-Za-z0-9._-]{20,}['\"]",
    ]
    combined = POLICY_PATH.read_text(encoding="utf-8") + "\n" + WAIVER_PATH.read_text(encoding="utf-8") + "\n" + plan
    for pattern in forbidden_patterns:
        if re.search(pattern, combined):
            errors.append("possible_secret_value_found_in_policy_artifacts")
            break

    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("FAIL: PPR-4 data continuation policy validation")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PASS: Dhan user waiver and no-source-stop policy are internally consistent.")
    print("Scope: local document validation only; no network request, raw market-data read, model fit, or holdout access.")
