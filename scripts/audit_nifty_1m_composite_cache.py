#!/usr/bin/env python3
"""Preflight cached option payloads before cache-preserving spot-gap recovery.

The earlier acquisition was intentionally partial: some option selectors failed,
but the valid cached responses yielded the existing 8,490,723 option rows. This
preflight must prove those same rows can be rebuilt from hash-verified encrypted
cache without any live option request. It does not require cached payloads for
selectors that failed in the prior run.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_nifty_1m_composite_dataset as collector

EXPECTED_PRESERVED_OPTION_ROWS = 8_490_723


def audit(root: dict, hf_token: str) -> dict:
    if not hf_token:
        return {"status": "BLOCKED", "reason": "HF_TOKEN_NOT_CONFIGURED",
                "source_requests_made": 0, "market_values_logged": False}
    key = collector.derive_key(hf_token)
    requests = collector.read_requests(root)
    options = [r for r in requests if r["source_family"] == "NIFTY_ROLLING_OPTION_1M"]
    spots = [r for r in requests if r["source_family"] == "NIFTY_SPOT_1M"]
    missing = []
    invalid = []
    valid_count = 0
    cached_rows = 0
    for request in options:
        cached = collector.get_cached_payload(request, key)
        if cached is None:
            missing.append(request["request_id"])
            continue
        raw, _meta = cached
        try:
            payload = collector.parse_json_numbers(raw)
            collector._validate_request_payload(payload, request)
            row_count = collector._payload_row_count(payload, request)
            valid_count += 1
            cached_rows += int(row_count)
        except Exception:
            invalid.append(request["request_id"])
    ledger = collector.load_attempt_ledger()
    budget = root["budgets"]
    remaining_wire = int(budget["max_wire_requests_total"]) - int(ledger["total_wire_attempts"])
    blocked_spots = [
        request["request_id"] for request in spots
        if int(ledger["request_attempts_by_id"].get(request["request_id"], 0)) >= 2
        or request["request_id"] in ledger["permanent_failure_requests"]
    ]
    family_auth_failure = "NIFTY_SPOT_1M" in ledger["permanent_failure_families"]
    status = "PASS" if (
        len(options) == 8540 and len(spots) == 61
        and valid_count > 0 and not invalid
        and cached_rows == EXPECTED_PRESERVED_OPTION_ROWS
        and not blocked_spots and not family_auth_failure and remaining_wire >= len(spots)
        and int(ledger["total_retry_attempts"]) <= int(budget["max_retry_requests_total"])
    ) else "BLOCKED"
    return {
        "schema_version": 1,
        "status": status,
        "option_requests_expected": len(options),
        "option_cache_valid": valid_count,
        "option_cache_missing": len(missing),
        "option_cache_invalid": len(invalid),
        "cached_option_rows": cached_rows,
        "expected_preserved_option_rows": EXPECTED_PRESERVED_OPTION_ROWS,
        "spot_requests_expected": len(spots),
        "spot_requests_ready": len(spots) - len(blocked_spots),
        "spot_request_attempts_exhausted": len(blocked_spots),
        "spot_family_auth_failure": family_auth_failure,
        "wire_requests_used": int(ledger["total_wire_attempts"]),
        "wire_requests_remaining": remaining_wire,
        "wire_requests_reserved_for_spot": len(spots),
        "live_option_requests_permitted": False,
        "source_requests_made": 0,
        "market_values_logged": False,
    }


def main() -> int:
    root = collector.load_json(collector.ROOT_MANIFEST)
    result = audit(root, os.environ.get("HF_TOKEN", ""))
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
