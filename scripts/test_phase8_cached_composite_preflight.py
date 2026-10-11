from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import authorize_phase8_cached_composite_preflight as auth


def _fixtures():
    pins = {path: f"{index:040x}"[-40:] for index, path in enumerate(sorted(auth.REQUIRED_REVIEWED_FILES), 1)}
    decision = {
        "schema_version": 1,
        "gate": "phase8-cached-composite-preflight-implementation-r1",
        "decision": "PASS_WITH_SCOPED_RESTRICTIONS",
        "scope": "metadata-only cached composite preflight",
        "approved_code_blob_shas": pins,
        "empirical_option_pnl_authorized": False,
        "holdout_access_authorized": False,
        "strategy_promotion_authorized": False,
        "no_new_market_source_requests": True,
    }
    request = {
        "schema_version": 1,
        "gate": "phase8-cached-composite-preflight-r1",
        "requested": True,
        "approved_code_blob_shas": dict(pins),
    }
    return request, decision, pins


def test_exact_snapshot_only():
    request, decision, pins = _fixtures()
    out = auth.evaluate_authorization(request, decision, pins)
    assert out["authorized"] is True
    assert out["pnl_authorized"] is False
    assert out["new_market_source_requests_authorized"] is False


def test_changed_code_fails_closed():
    request, decision, pins = _fixtures()
    current = dict(pins)
    current["scripts/run_phase8_long_option.py"] = "9" * 40
    try:
        auth.evaluate_authorization(request, decision, current)
    except ValueError as exc:
        assert "exact reviewed code blob mismatch" in str(exc)
    else:
        raise AssertionError("stale reviewer approval must not authorize changed code")


def test_false_request_skips_execution():
    request, decision, _ = _fixtures()
    request["requested"] = False
    out = auth.evaluate_authorization(request, decision, {})
    assert out["authorized"] is False
    assert out["reason"] == "REQUEST_NOT_ENABLED"




def test_disabled_request_skips_without_review_decision():
    original_argv = sys.argv[:]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        request_path = root / "request.json"
        output_path = root / "authorization.json"
        request_path.write_text(json.dumps({
            "schema_version": 1,
            "gate": "phase8-cached-composite-preflight-r1",
            "requested": False,
        }), encoding="utf-8")
        try:
            sys.argv = [
                "authorize_phase8_cached_composite_preflight.py",
                "--request", str(request_path),
                "--decision", str(root / "decision-does-not-exist.json"),
                "--output", str(output_path),
            ]
            assert auth.main() == 0
            result = json.loads(output_path.read_text(encoding="utf-8"))
            assert result["authorized"] is False
            assert result["reason"] == "REQUEST_NOT_ENABLED"
        finally:
            sys.argv = original_argv


def test_workflow_and_request_are_default_closed_and_metadata_only():
    workflow_path = ROOT / ".github/workflows/phase8-cached-composite-preflight.yml"
    request_path = ROOT / "research/gates/PHASE8_CACHED_COMPOSITE_PREFLIGHT_EXECUTION_REQUEST_R1.json"
    text = workflow_path.read_text(encoding="utf-8")
    request = json.loads(request_path.read_text(encoding="utf-8"))

    assert "workflow_dispatch" in text
    assert "phase-08-developer" in text
    assert "actions: read" in text and "contents: read" in text
    assert "actions/download-artifact@v4" in text
    assert "run-id: 38131641336" in text
    assert "11698879857" in text and "11638738288" in text
    assert "cbd3c51bcaecef0572b1f0727b82ccc4f8f624469a256a6a440327c83b03204" in text
    assert "scripts/run_phase8_long_option.py" in text
    assert "--mode preflight" in text
    assert "--mode empirical" not in text
    assert "if: always()" in text and "CLEANUP_FAILED" in text
    assert "Upload metadata-only evidence" in text
    assert "api.dhan.co" not in text
    assert "nseindia.com/all-reports-derivatives" not in text
    assert "huggingface.co/datasets" not in text
    assert request["requested"] is False
    assert request["empirical_option_pnl_authorized"] is False
    assert request["holdout_access_authorized"] is False
    assert request["new_market_source_requests_authorized"] is False
    assert request["strategy_promotion_authorized"] is False


if __name__ == "__main__":
    test_exact_snapshot_only()
    test_changed_code_fails_closed()
    test_false_request_skips_execution()
    test_disabled_request_skips_without_review_decision()
    test_workflow_and_request_are_default_closed_and_metadata_only()
    print("Phase 8 preflight authorization tests PASS")
