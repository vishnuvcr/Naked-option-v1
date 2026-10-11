#!/usr/bin/env python3
"""Validate that a data audit is explicitly approved for exact reviewed files."""
import argparse
import hashlib
import json
from pathlib import Path


def blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + bytes([0]) + data).hexdigest()


def evaluate(decision, request, decision_path, reviewed_paths):
    failures = []
    if decision.get("verdict") != "PASS_WITH_SCOPED_RESTRICTIONS":
        failures.append("TESTER_VERDICT_NOT_PASS")
    if decision.get("real_file_preflight_execution_authorized") is not True:
        failures.append("REAL_FILE_SCOPE_NOT_AUTHORIZED")
    if request.get("requested") is not True:
        failures.append("EXECUTION_REQUEST_NOT_TRUE")
    if request.get("tester_decision_blob_sha") != blob_sha(decision_path):
        failures.append("TESTER_DECISION_HASH_MISMATCH")
    reviewed = decision.get("reviewed_files")
    if not isinstance(reviewed, dict):
        reviewed = {}
        failures.append("REVIEWED_FILE_HASH_MAP_MISSING")
    for item in reviewed_paths:
        path = Path(item)
        if not path.is_file():
            failures.append("REQUIRED_FILE_MISSING:" + item)
        elif reviewed.get(item) != blob_sha(path):
            failures.append("REVIEWED_FILE_HASH_MISMATCH:" + item)
    return {"authorized": not failures,
            "reason": "EXACT_APPROVAL_MATCHED" if not failures else "FAIL_CLOSED",
            "failures": failures}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--reviewed-files", nargs="+", required=True)
    args = parser.parse_args()
    decision_path, request_path = Path(args.decision), Path(args.request)
    if not decision_path.is_file() or not request_path.is_file():
        print(json.dumps({"authorized": False, "reason": "DECISION_OR_REQUEST_MISSING"}))
        return 0
    try:
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"authorized": False, "reason": "INVALID_JSON"}))
        return 0
    result = evaluate(decision, request, decision_path, args.reviewed_files)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
