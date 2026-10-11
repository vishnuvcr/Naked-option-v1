from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import authorize_phase8_cached_composite_preflight as auth


def _fixtures():
    pins = {
        "scripts/run_phase8_long_option.py": "1" * 40,
        "scripts/decrypt_nifty_1m_composite.py": "2" * 40,
        ".github/workflows/phase8-cached-composite-preflight.yml": "3" * 40,
    }
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


if __name__ == "__main__":
    test_exact_snapshot_only()
    test_changed_code_fails_closed()
    test_false_request_skips_execution()
    print("Phase 8 preflight authorization tests PASS")
