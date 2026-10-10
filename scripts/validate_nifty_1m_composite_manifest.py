#!/usr/bin/env python3
"""Offline structural validator for the explicit NIFTY one-minute acquisition manifest."""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT_MANIFEST = ROOT / "research/gates/NIFTY_1M_COMPOSITE_REQUEST_MANIFEST.json"
OPTIONS_URL = "https://api.dhan.co/v2/charts/rollingoption"
SPOT_URL = "https://api.dhan.co/v2/charts/intraday"
EXPECTED_START = dt.date(2021, 10, 11)
EXPECTED_END = dt.date(2026, 10, 11)
OPTIONS_FIELDS = {"open", "high", "low", "close", "iv", "volume", "strike", "oi", "spot"}
ALLOWED_FLAGS = {"WEEK", "MONTH"}
ALLOWED_TYPES = {"CALL", "PUT"}


def read_json(path: pathlib.Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"top_level_object_required:{path.name}")
    return value


def windows() -> list[tuple[str, str]]:
    out = []
    current = EXPECTED_START
    while current < EXPECTED_END:
        end = min(current + dt.timedelta(days=30), EXPECTED_END)
        out.append((current.isoformat(), end.isoformat()))
        current = end
    return out


def validate() -> list[str]:
    errors: list[str] = []
    try:
        root = read_json(ROOT_MANIFEST)
    except Exception as exc:
        return [f"root_manifest_read_error:{type(exc).__name__}"]

    if root.get("schema_version") != 1:
        errors.append("root_schema_version_must_be_1")
    if root.get("status") != "DRAFT_FOR_EXACT_SNAPSHOT_TESTER_REVIEW":
        errors.append("request_manifest_must_remain_draft_until_separate_approval")
    auth = root.get("authorization", {})
    for key in ("live_requests_authorized", "modeling_authorized", "holdout_access_authorized"):
        if auth.get(key) is not False:
            errors.append(f"manifest_must_keep_{key}_false")
    if auth.get("user_dhan_cross_source_value_check_waived") is not True:
        errors.append("user_dhan_cross_source_check_waiver_missing")
    if auth.get("user_requests_no_global_stop_on_missing_source") is not True:
        errors.append("no_global_stop_instruction_missing")

    expected_windows = windows()
    if root.get("chunks") != len(expected_windows) or len(expected_windows) != 61:
        errors.append("unexpected_30_day_window_count")

    request_entries = root.get("request_manifests", [])
    if {entry.get("year") for entry in request_entries} != {2021, 2022, 2023, 2024, 2025, 2026}:
        errors.append("request_manifests_must_cover_2021_through_2026")
    all_requests: list[dict] = []
    for entry in request_entries:
        rel = entry.get("path")
        if not isinstance(rel, str) or not rel.startswith("research/gates/NIFTY_1M_COMPOSITE_REQUESTS_"):
            errors.append("unsafe_or_missing_request_manifest_path")
            continue
        try:
            item = read_json(ROOT / rel)
        except Exception as exc:
            errors.append(f"request_manifest_read_error:{rel}:{type(exc).__name__}")
            continue
        requests = item.get("requests")
        if not isinstance(requests, list) or len(requests) != entry.get("request_count") or len(requests) != item.get("request_count"):
            errors.append(f"request_count_mismatch:{rel}")
            continue
        all_requests.extend(requests)

    ids = [r.get("request_id") for r in all_requests]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_request_id")
    if len(all_requests) != 8601:
        errors.append(f"total_request_count_mismatch:{len(all_requests)}")
    counts = Counter(r.get("source_family") for r in all_requests)
    if counts["NIFTY_ROLLING_OPTION_1M"] != 8540:
        errors.append("option_request_count_must_equal_8540")
    if counts["NIFTY_SPOT_1M"] != 61:
        errors.append("spot_request_count_must_equal_61")

    option_grid = Counter()
    spot_windows = set()
    observed_windows = set()
    for r in all_requests:
        fam = r.get("source_family")
        endpoint = r.get("endpoint")
        body = r.get("body", {})
        start = r.get("window_start_inclusive")
        end = r.get("window_end_exclusive")
        if (start, end) not in expected_windows:
            errors.append(f"request_window_not_in_frozen_30_day_partition:{r.get('request_id')}")
            continue
        observed_windows.add((start, end))
        max_bytes = r.get("max_response_bytes")
        max_rows = r.get("max_rows")
        if fam == "NIFTY_SPOT_1M":
            if endpoint != SPOT_URL or max_bytes != 8388608 or max_rows != 12000:
                errors.append(f"spot_endpoint_or_caps_invalid:{r.get('request_id')}")
            expected_last = (dt.date.fromisoformat(end) - dt.timedelta(days=1)).isoformat()
            if (body.get("securityId") != "13" or body.get("exchangeSegment") != "IDX_I"
                    or body.get("instrument") != "INDEX" or body.get("interval") != "1"
                    or body.get("oi") is not False
                    or body.get("fromDate") != f"{start} 09:15:00"
                    or body.get("toDate") != f"{expected_last} 15:30:00"):
                errors.append(f"spot_request_body_mismatch:{r.get('request_id')}")
            if (start, end) in spot_windows:
                errors.append(f"duplicate_spot_window:{start}:{end}")
            spot_windows.add((start, end))
        elif fam == "NIFTY_ROLLING_OPTION_1M":
            if endpoint != OPTIONS_URL or max_bytes != 2097152 or max_rows != 10000:
                errors.append(f"option_endpoint_or_caps_invalid:{r.get('request_id')}")
            code = body.get("expiryCode")
            strike = body.get("strike")
            opt_type = body.get("drvOptionType")
            flag = body.get("expiryFlag")
            if (body.get("exchangeSegment") != "NSE_FNO" or body.get("instrument") != "OPTIDX"
                    or body.get("securityId") != 13 or body.get("interval") != "1"
                    or flag not in ALLOWED_FLAGS or code not in (0, 1, 2)
                    or opt_type not in ALLOWED_TYPES or body.get("fromDate") != start
                    or body.get("toDate") != end or set(body.get("requiredData", [])) != OPTIONS_FIELDS):
                errors.append(f"option_request_body_mismatch:{r.get('request_id')}")
            allowed = set(range(-10, 11)) if code == 0 else set(range(-3, 4))
            try:
                if strike == "ATM":
                    strike_offset = 0
                elif isinstance(strike, str) and strike.startswith("ATM+"):
                    strike_offset = int(strike[4:])
                elif isinstance(strike, str) and strike.startswith("ATM-"):
                    strike_offset = -int(strike[4:])
                else:
                    strike_offset = 999
            except (TypeError, ValueError):
                strike_offset = 999
            if strike_offset not in allowed:
                errors.append(f"strike_outside_allowed_grid:{r.get('request_id')}:{strike}")
            option_grid[(start, end, flag, code, strike, opt_type)] += 1
        else:
            errors.append(f"unknown_source_family:{fam}")

    if spot_windows != set(expected_windows):
        errors.append("spot_requests_do_not_cover_all_windows")
    if observed_windows != set(expected_windows):
        errors.append("request_windows_do_not_match_full_five_year_partition")

    for start, end in expected_windows:
        if sum(1 for r in all_requests if r.get("window_start_inclusive") == start and r.get("window_end_exclusive") == end and r.get("source_family") == "NIFTY_SPOT_1M") != 1:
            errors.append(f"spot_window_count_not_one:{start}")
        opt_here = [r for r in all_requests if r.get("window_start_inclusive") == start and r.get("window_end_exclusive") == end and r.get("source_family") == "NIFTY_ROLLING_OPTION_1M"]
        if len(opt_here) != 140:
            errors.append(f"option_grid_count_not_140:{start}:{len(opt_here)}")
        for flag in ALLOWED_FLAGS:
            for code in (0, 1, 2):
                strikes = range(-10, 11) if code == 0 else range(-3, 4)
                for k in strikes:
                    strike = "ATM" if k == 0 else (f"ATM+{k}" if k > 0 else f"ATM{k}")
                    for side in ALLOWED_TYPES:
                        if option_grid[(start, end, flag, code, strike, side)] != 1:
                            errors.append(f"option_grid_cell_missing_or_duplicate:{start}:{flag}:{code}:{strike}:{side}")

    budgets = root.get("budgets", {})
    if (budgets.get("planned_unique_requests") != 8601
            or budgets.get("planned_option_requests") != 8540
            or budgets.get("planned_spot_requests") != 61
            or budgets.get("max_retry_requests_total") != 100
            or budgets.get("max_wire_requests_total") != 8701
            or budgets.get("serial_max_requests_per_second") != 2
            or budgets.get("options_aggregate_bytes_max") != 8589934592):
        errors.append("root_budget_contract_mismatch")
    output = root.get("output", {})
    if output.get("not_publishing_subscribed_market_rows_to_public_git_or_release") is not True:
        errors.append("plain_market_data_must_not_be_published_to_public_git_or_release")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("FAIL: NIFTY 1-minute composite manifest validation")
        for failure in failures[:120]:
            print("- " + failure)
        if len(failures) > 120:
            print(f"... {len(failures) - 120} additional findings")
        sys.exit(1)
    print("PASS: exact request grid, all 61 non-overlapping windows, response caps and no-live scope validate.")
    print("Scope: offline manifest checks only; no API requests or market-data values read.")
