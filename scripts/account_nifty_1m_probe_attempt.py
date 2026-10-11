#!/usr/bin/env python3
"""Record a previously tester-authorized non-persisting diagnostic in the wire budget.

The diagnostic itself never persists raw market data. This separate, offline
step counts its one actual HTTP attempt in the cumulative wire ledger while
keeping it distinct from collection-request retry counters and per-request
collection attempts.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_nifty_1m_composite_dataset as collector

MARKER_PATH = ROOT / "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_EXECUTION.json"
RESULT_PATH = ROOT / "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_RESULT.json"
PLAN_PATH = ROOT / "research/gates/NIFTY_1M_SPOT_DIAGNOSTIC_PLAN.json"
LEDGER_PATH = collector.ATTEMPT_LEDGER_PATH
EVENT_TYPE = "AUTHORIZED_NONPERSISTING_DIAGNOSTIC"


def account_probe_attempt(marker_path: pathlib.Path = MARKER_PATH,
                          result_path: pathlib.Path = RESULT_PATH,
                          ledger_path: pathlib.Path = LEDGER_PATH,
                          expected_scope_sha256: str | None = None) -> dict[str, Any]:
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if (marker.get("status") != "SPENT_BEFORE_SOURCE_REQUEST"
            or marker.get("scope") != "ONE_NONPERSISTING_SPOT_SCHEMA_DIAGNOSTIC"
            or marker.get("max_wire_requests") != 1
            or marker.get("max_retries") != 0
            or marker.get("request_id") != plan.get("request_id")
            or result.get("request_id") != plan.get("request_id")
            or result.get("developer_reviewed_sha") != marker.get("reviewed_developer_commit")
            or result.get("wire_requests") != 1
            or result.get("retries") != 0
            or not result.get("executed_at_utc")
            or not result.get("request_scope_sha256")):
        raise ValueError("authorized_diagnostic_marker_result_mismatch")
    if expected_scope_sha256 and result.get("request_scope_sha256") != expected_scope_sha256:
        raise ValueError("diagnostic_request_scope_hash_mismatch")

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    existing_events = []
    if ledger_path.exists():
        for line_number, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                raise ValueError("attempt_ledger_corrupt_fail_closed") from None
            if not isinstance(event, dict) or event.get("schema_version") != 1:
                raise ValueError("attempt_ledger_event_schema_mismatch")
            existing_events.append(event)
    probe_id = str(marker.get("github_run_id", "")).strip()
    if not probe_id:
        raise ValueError("diagnostic_run_id_missing")
    if any(event.get("event_type") == EVENT_TYPE and str(event.get("probe_id", "")) == probe_id
           for event in existing_events):
        return {"status": "ALREADY_ACCOUNTED", "probe_id": probe_id,
                "wire_delta": 0, "request_attempt_counters_changed": False}

    event = {
        "schema_version": 1,
        "wire_delta": 1,
        "retry_delta": 0,
        "request_updates": {},
        "permanent_request_updates": {},
        "permanent_family_updates": {},
        "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "event_type": EVENT_TYPE,
        "probe_id": probe_id,
        "diagnostic_request_id": str(result["request_id"]),
        "request_scope_sha256": str(result["request_scope_sha256"]),
        "request_attempt_counters_changed": False,
        "raw_response_persisted": False,
    }
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return {"status": "ACCOUNTED", "probe_id": probe_id,
            "wire_delta": 1, "request_attempt_counters_changed": False}


def main() -> int:
    from validate_nifty_1m_composite_manifest import validate as validate_manifest
    errors = validate_manifest()
    if errors:
        raise SystemExit("DIAGNOSTIC_ACCOUNTING_MANIFEST_INVALID")
    root = collector.load_json(collector.ROOT_MANIFEST)
    request_id = json.loads(PLAN_PATH.read_text(encoding="utf-8"))["request_id"]
    requests = collector.read_requests(root)
    matches = [r for r in requests if r.get("request_id") == request_id]
    if len(matches) != 1:
        raise SystemExit("DIAGNOSTIC_ACCOUNTING_REQUEST_NOT_UNIQUE")
    expected_hash = collector.request_scope_hash(matches[0])
    result = account_probe_attempt(expected_scope_sha256=expected_hash)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
