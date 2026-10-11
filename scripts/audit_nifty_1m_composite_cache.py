#!/usr/bin/env python3
"""Preflight the exact encrypted option cache before spot-only recovery.

Performs no source requests and never decrypts/export market rows beyond parsing
cached response metadata in memory. Fails closed unless all approved option
responses are present, decryptable, hash-valid and schema-valid.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_nifty_1m_composite_dataset as collector


def main() -> int:
    root = collector.load_json(collector.ROOT_MANIFEST)
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        print(json.dumps({"status": "BLOCKED", "reason": "HF_TOKEN_NOT_CONFIGURED"}))
        return 2
    key = collector.derive_key(token)
    requests = collector.read_requests(root)
    options = [r for r in requests if r["source_family"] == "NIFTY_ROLLING_OPTION_1M"]
    spots = [r for r in requests if r["source_family"] == "NIFTY_SPOT_1M"]
    missing = []
    invalid = []
    for request in options:
        cached = collector.get_cached_payload(request, key)
        if cached is None:
            missing.append(request["request_id"])
            continue
        raw, _meta = cached
        try:
            payload = collector.parse_json_numbers(raw)
            collector._validate_request_payload(payload, request)
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
        len(options) == 8540 and len(spots) == 61 and not missing and not invalid
        and not blocked_spots and not family_auth_failure and remaining_wire >= len(spots)
        and int(ledger["total_retry_attempts"]) <= int(budget["max_retry_requests_total"])
    ) else "BLOCKED"
    result = {
        "schema_version": 1,
        "status": status,
        "option_requests_expected": len(options),
        "option_cache_valid": len(options) - len(missing) - len(invalid),
        "option_cache_missing": len(missing),
        "option_cache_invalid": len(invalid),
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
    print(json.dumps(result, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
