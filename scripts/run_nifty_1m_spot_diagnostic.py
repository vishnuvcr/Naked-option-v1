#!/usr/bin/env python3
"""One-request, non-persisting Dhan NIFTY spot schema diagnostic.

Only response metadata and sanitized parser findings are written. The response
body exists in memory for parsing, is never logged or cached, and is not exported.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import urllib.error
import urllib.request
from collections import Counter
from typing import Any

from run_nifty_1m_composite_dataset import (
    IST, ROOT, NoRedirect, _safe_exception_reason, load_json, parse_json_numbers,
    parse_spot_response, read_requests, request_scope_hash, utc_now,
)

PLAN_PATH = ROOT / "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_PLAN.json"
MANIFEST_PATH = ROOT / "research/gates/NIFTY_1M_COMPOSITE_REQUEST_MANIFEST.json"
TIMEOUT_SECONDS = 35
USER_AGENT = "Naked-option-v1-spot-diagnostic/1.0"


def find_request(request_id: str) -> dict[str, Any]:
    root = load_json(MANIFEST_PATH)
    matches = [r for r in read_requests(root) if r.get("request_id") == request_id]
    if len(matches) != 1:
        raise ValueError("diagnostic_request_id_not_unique_in_frozen_manifest")
    request = matches[0]
    if request.get("source_family") != "NIFTY_SPOT_1M":
        raise ValueError("diagnostic_request_family_mismatch")
    if request.get("endpoint") != "https://api.dhan.co/v2/charts/intraday" or request.get("method") != "POST":
        raise ValueError("diagnostic_request_endpoint_mismatch")
    return request


def _array_metadata(payload: dict[str, Any]) -> tuple[list[str], dict[str, str], dict[str, int]]:
    keys = sorted(str(k) for k in payload.keys())
    types: dict[str, str] = {}
    lengths: dict[str, int] = {}
    for key in ("timestamp", "open", "high", "low", "close", "volume"):
        if key not in payload:
            types[key] = "MISSING"
        else:
            value = payload[key]
            types[key] = type(value).__name__
            if isinstance(value, list):
                lengths[key] = len(value)
    return keys, types, lengths


def summarize_response(
    raw: bytes,
    request: dict[str, Any],
    http_status: int,
    content_type: str,
    reviewed_sha: str,
) -> dict[str, Any]:
    """Produce a result containing metadata and no candle/market values."""
    result: dict[str, Any] = {
        "schema_version": 1,
        "plan_id": "NIFTY_1M_SPOT_DIAGNOSTIC_2026-10-11_V1",
        "request_id": request["request_id"],
        "request_scope_sha256": request_scope_hash(request),
        "developer_reviewed_sha": reviewed_sha,
        "executed_at_utc": utc_now(),
        "http_status": int(http_status),
        "content_type": str(content_type).split(";", 1)[0].strip().lower()[:80],
        "response_bytes": len(raw),
        "top_level_keys": [],
        "field_types": {},
        "array_lengths": {},
        "api_error_code": None,
        "parser_status": "NOT_RUN",
        "parser_reason": "",
        "row_count": 0,
        "quality_flag_counts": {},
        "raw_response_persisted": False,
        "cache_written": False,
        "market_values_logged": False,
        "wire_requests": 1,
        "retries": 0,
    }
    if len(raw) > int(request["max_response_bytes"]):
        result["parser_status"] = "RESPONSE_TOO_LARGE"
        result["parser_reason"] = "response_byte_cap_exceeded"
        return result
    if not (200 <= http_status < 300):
        result["parser_status"] = "HTTP_ERROR"
        result["parser_reason"] = "http_status_" + str(int(http_status))
        return result
    if "json" not in result["content_type"]:
        result["parser_status"] = "CONTENT_TYPE_ERROR"
        result["parser_reason"] = "unexpected_content_type"
        return result
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        result["parser_status"] = "INVALID_JSON"
        result["parser_reason"] = "response_invalid_json"
        return result
    if not isinstance(payload, dict):
        result["parser_status"] = "INVALID_OBJECT"
        result["parser_reason"] = "response_json_not_object"
        return result
    keys, types, lengths = _array_metadata(payload)
    result["top_level_keys"] = keys
    result["field_types"] = types
    result["array_lengths"] = lengths
    code = payload.get("errorCode")
    if code is not None:
        code_text = str(code)
        result["api_error_code"] = code_text if code_text.isdigit() and len(code_text) <= 8 else "NON_NUMERIC_OR_UNEXPECTED"
        result["parser_status"] = "DHAN_API_ERROR"
        result["parser_reason"] = "dhan_api_error_code_" + result["api_error_code"]
        return result
    if payload.get("status") == "error" or payload.get("error"):
        result["parser_status"] = "DHAN_API_ERROR"
        result["parser_reason"] = "dhan_api_error_payload"
        return result
    try:
        rows, problems = parse_spot_response(payload, request)
        result["row_count"] = len(rows)
        flags = Counter(
            flag
            for row in rows
            for flag in str(row.get("data_quality_flags", "")).split("|")
            if flag
        )
        result["quality_flag_counts"] = dict(sorted(flags.items()))
        if not rows:
            result["parser_status"] = "PARSED_EMPTY"
        elif "spot_volume_missing_or_misaligned" in problems:
            result["parser_status"] = "PARSED_WITH_VOLUME_GAP"
        else:
            result["parser_status"] = "PARSED_OK"
    except Exception as exc:
        result["parser_status"] = "PARSER_REJECTED"
        result["parser_reason"] = _safe_exception_reason(exc)
    return result


def perform_one_probe(request: dict[str, Any], token: str, reviewed_sha: str) -> dict[str, Any]:
    body = json.dumps(request["body"], separators=(",", ":"), sort_keys=True).encode("utf-8")
    req = urllib.request.Request(
        request["endpoint"], data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "access-token": token, "User-Agent": USER_AGENT},
    )
    # Exactly one network attempt. No redirects and no retry by design.
    try:
        response = urllib.request.build_opener(NoRedirect()).open(req, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        try:
            exc.close()
        except OSError:
            pass
        return summarize_response(b"", request, status, "", reviewed_sha)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result = summarize_response(b"", request, 0, "", reviewed_sha)
        result["parser_status"] = "TRANSPORT_ERROR"
        result["parser_reason"] = "transport_error_" + type(exc).__name__
        result["http_status"] = None
        return result
    try:
        status = int(getattr(response, "status", 0))
        content_type = str(getattr(response, "headers", {}).get("Content-Type", ""))
        cap = int(request["max_response_bytes"])
        raw = response.read(cap + 1)
        if len(raw) > cap:
            raw = raw[:cap + 1]
        return summarize_response(raw, request, status, content_type, reviewed_sha)
    finally:
        try:
            response.close()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--reviewed-sha", required=True)
    args = parser.parse_args()
    plan = load_json(PLAN_PATH)
    if plan.get("status") != "DRAFT_FOR_AUTOMATED_TESTER_REVIEW":
        raise SystemExit("DIAGNOSTIC_PLAN_STATUS_INVALID")
    if plan.get("max_wire_requests") != 1 or plan.get("max_retries") != 0:
        raise SystemExit("DIAGNOSTIC_REQUEST_BUDGET_INVALID")
    for field in ("persist_raw_response", "write_response_cache", "write_csv_rows",
                  "export_market_rows", "log_market_values", "log_credentials"):
        if plan.get(field) is not False:
            raise SystemExit("DIAGNOSTIC_PRIVACY_CONSTRAINT_INVALID:" + field)
    token = os.environ.get("DHAN_ACCESS_TOKEN", "").strip()
    if not token:
        raise SystemExit("DHAN_ACCESS_TOKEN_NOT_CONFIGURED")
    request = find_request(str(plan["request_id"]))
    result = perform_one_probe(request, token, args.reviewed_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in (
        "request_id", "http_status", "response_bytes", "top_level_keys",
        "field_types", "array_lengths", "parser_status", "parser_reason",
        "row_count", "raw_response_persisted", "cache_written", "market_values_logged"
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
