from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_REVIEWED_FILES = {
    ".github/workflows/phase8-cached-composite-preflight.yml",
    "scripts/run_phase8_long_option.py",
    "scripts/test_phase8_long_option_runner.py",
    "scripts/phase8_execution_engine.py",
    "scripts/test_phase8_execution_engine.py",
    "scripts/decrypt_nifty_1m_composite.py",
    "scripts/validate_phase8_cached_composite_bundle.py",
    "scripts/test_phase8_cached_composite_bundle.py",
    "scripts/authorize_phase8_cached_composite_preflight.py",
    "scripts/test_phase8_cached_composite_preflight.py",
    "research/data/DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json",
    "research/phase8/PHASE8_FROZEN_INPUT_MANIFEST.json",
    "research/phase8/PHASE8_METHOD_SPEC.md",
    "data/reference/phase8_cost_schedule.json",
    "requirements-composite.txt",
}


def _current_blob_sha(path: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", f"HEAD:{path}"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"AUTH_BLOCKED: required tracked file unavailable: {path}")
    return result.stdout.strip()


def evaluate_authorization(request: dict[str, Any], decision: dict[str, Any],
                           current_blob_shas: dict[str, str]) -> dict[str, Any]:
    """Authorize only a metadata-only run against exact independently reviewed blobs."""
    if request.get("schema_version") != 1 or request.get("gate") != "phase8-cached-composite-preflight-r1":
        raise ValueError("AUTH_BLOCKED: request schema/gate mismatch")
    if request.get("requested") is not True:
        return {"authorized": False, "reason": "REQUEST_NOT_ENABLED", "pnl_authorized": False}
    if decision.get("schema_version") != 1 or decision.get("gate") != "phase8-cached-composite-preflight-implementation-r1":
        raise ValueError("AUTH_BLOCKED: implementation tester decision missing or wrong gate")
    if decision.get("decision") != "PASS_WITH_SCOPED_RESTRICTIONS":
        raise ValueError("AUTH_BLOCKED: exact implementation did not pass tester gate")
    if decision.get("empirical_option_pnl_authorized") is not False:
        raise ValueError("AUTH_BLOCKED: tester decision improperly enables empirical P&L")
    if decision.get("holdout_access_authorized") is not False or decision.get("strategy_promotion_authorized") is not False:
        raise ValueError("AUTH_BLOCKED: tester decision improperly enables holdout/promotion")
    reviewed = decision.get("approved_code_blob_shas")
    requested = request.get("approved_code_blob_shas")
    if not isinstance(reviewed, dict) or set(reviewed) != REQUIRED_REVIEWED_FILES:
        raise ValueError("AUTH_BLOCKED: tester decision must pin every required code/spec/data-contract file")
    if requested != reviewed:
        raise ValueError("AUTH_BLOCKED: request does not exactly copy reviewed blob hashes")
    if set(current_blob_shas) != set(reviewed):
        raise ValueError("AUTH_BLOCKED: current code pin set differs from tester-reviewed set")
    mismatches = {
        path: {"current": current_blob_shas.get(path), "reviewed": reviewed.get(path)}
        for path in reviewed if current_blob_shas.get(path) != reviewed.get(path)
    }
    if mismatches:
        raise ValueError("AUTH_BLOCKED: exact reviewed code blob mismatch: " + json.dumps(mismatches, sort_keys=True))
    if decision.get("scope") != "metadata-only cached composite preflight":
        raise ValueError("AUTH_BLOCKED: reviewer scope is not metadata-only preflight")
    if decision.get("no_new_market_source_requests") is not True:
        raise ValueError("AUTH_BLOCKED: tester did not prohibit new market-data requests")
    return {
        "authorized": True,
        "reason": "EXACT_REVIEWED_SNAPSHOT_AND_ONE_RUN_REQUEST_MATCH",
        "pnl_authorized": False,
        "holdout_authorized": False,
        "new_market_source_requests_authorized": False,
        "strategy_promotion_authorized": False,
        "approved_code_blob_count": len(reviewed),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check exact tester gate for one metadata-only Phase 8 preflight.")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    if request.get("requested") is not True:
        # No reviewer decision is needed to keep a default-disabled request skipped.
        result = evaluate_authorization(request, {}, {})
    else:
        if not args.decision.is_file():
            raise SystemExit("AUTH_BLOCKED: implementation tester decision is absent")
        decision = json.loads(args.decision.read_text(encoding="utf-8"))
        pins = request.get("approved_code_blob_shas", {})
        if not isinstance(pins, dict) or not pins:
            raise SystemExit("AUTH_BLOCKED: enabled request has no exact code pins")
        current = {path: _current_blob_sha(path) for path in pins}
        result = evaluate_authorization(request, decision, current)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
