from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import authorize_phase8_source_cache_bootstrap as auth


def _fixture():
    blobs = {path: f"{index:040x}" for index, path in enumerate(auth.REQUIRED_CODE_PATHS, start=1)}
    sources = {
        "daily_csv": {
            "path": "data/cache/raw/phase3/nifty50_daily.csv",
            "sha256": "5816b0e73f4bd1327e567249f366fbebb01a549bd539fd4743424fbefe70f5c1",
        },
        "intraday_parquet": {
            "path": "data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet",
            "sha256": "6f6014d58cf0aa03920832b97730bc2f4287532b3c830700351d6828adfebc17",
        },
    }
    decision = {
        "schema_version": 1,
        "gate": "phase8-source-cache-bootstrap-r1",
        "decision": "APPROVE_ONE_TIME_FREE_SOURCE_CACHE_BOOTSTRAP",
        "source_cache_bootstrap_authorized": True,
        "source_audit_authorized": False,
        "empirical_option_pnl_authorized": False,
        "holdout_access_authorized": False,
        "new_option_market_sources_authorized": False,
        "strategy_promotion_authorized": False,
        "approved_code_blob_shas": blobs.copy(),
        "frozen_source_sha256": {key: value["sha256"] for key, value in sources.items()},
        "reference_artifact": {
            "run_id": 37957677656,
            "artifact_id": 11638738288,
            "artifact_sha256": "3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9",
            "embedded_manifest_sha256": "f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091",
        },
    }
    return decision, blobs, sources


def test_exact_tester_approval_passes_without_network():
    decision, blobs, sources = _fixture()
    result = auth.evaluate_decision(decision, blobs, sources, consumed_marker_exists=False)
    assert result["status"] == "APPROVED"
    assert result["network_accessed"] is False
    assert result["source_sha256"] == decision["frozen_source_sha256"]


def test_wrong_decision_is_denied():
    decision, blobs, sources = _fixture()
    decision["decision"] = "REQUEST_CHANGES"
    try:
        auth.evaluate_decision(decision, blobs, sources, consumed_marker_exists=False)
    except auth.BootstrapAuthorizationError as exc:
        assert "does not approve" in str(exc)
    else:
        raise AssertionError("non-approval decision was accepted")


def test_code_blob_drift_is_denied():
    decision, blobs, sources = _fixture()
    path = auth.REQUIRED_CODE_PATHS[0]
    blobs[path] = "f" * 40
    try:
        auth.evaluate_decision(decision, blobs, sources, consumed_marker_exists=False)
    except auth.BootstrapAuthorizationError as exc:
        assert "blob pins differ" in str(exc)
    else:
        raise AssertionError("reviewed code blob drift was accepted")


def test_source_pin_drift_is_denied():
    decision, blobs, sources = _fixture()
    sources["daily_csv"]["sha256"] = "0" * 64
    try:
        auth.evaluate_decision(decision, blobs, sources, consumed_marker_exists=False)
    except auth.BootstrapAuthorizationError as exc:
        assert "frozen input pins differ" in str(exc)
    else:
        raise AssertionError("source pin drift was accepted")


def test_consumed_marker_blocks_repeat_bootstrap():
    decision, blobs, sources = _fixture()
    try:
        auth.evaluate_decision(decision, blobs, sources, consumed_marker_exists=True)
    except auth.BootstrapAuthorizationError as exc:
        assert "marker already exists" in str(exc)
    else:
        raise AssertionError("consumed one-time bootstrap decision was reused")


def test_any_data_or_strategy_authority_flag_denies_bootstrap():
    for flag in (
        "source_audit_authorized",
        "empirical_option_pnl_authorized",
        "holdout_access_authorized",
        "new_option_market_sources_authorized",
        "strategy_promotion_authorized",
    ):
        decision, blobs, sources = _fixture()
        decision[flag] = True
        try:
            auth.evaluate_decision(decision, blobs, sources, consumed_marker_exists=False)
        except auth.BootstrapAuthorizationError:
            pass
        else:
            raise AssertionError(f"unsafe authority flag {flag} was accepted")


def main():
    tests = [
        test_exact_tester_approval_passes_without_network,
        test_wrong_decision_is_denied,
        test_code_blob_drift_is_denied,
        test_source_pin_drift_is_denied,
        test_consumed_marker_blocks_repeat_bootstrap,
        test_any_data_or_strategy_authority_flag_denies_bootstrap,
    ]
    for test in tests:
        test()
    print(json.dumps({"status": "PASS", "tests": len(tests), "network_accessed": False}, sort_keys=True))


if __name__ == "__main__":
    main()
