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
        "request_id": "PHASE8_CACHED_COMPOSITE_PREFLIGHT_ONCE_R1_2026-10-11",
        "requested": True,
        "requested_scope": "metadata-only cached composite preflight",
        "source": {
            "run_id": 38131641336, "commit": "5e769cd4b19887311213baf16eb81b97416322d7",
            "artifact_id": 11698879857, "name": "nifty-1m-derived-repaired-r2-38126168547",
            "canonical_csv_sha256": "cbd3c51bcaecef0572b1f0727b82ccc4f8f624469a256a6a440327c83b03204",
            "rows": 8999865, "columns": 47, "encrypted_parts": 61,
        },
        "forecast": {
            "run_id": 37957677656, "commit": "b50be8cfa1ebe008a800e65a53f9c0fb2581aecb",
            "artifact_id": 11638738288, "name": "phase7-ensemble-reference",
            "archive_sha256": "3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9",
            "manifest_sha256": "f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091",
            "aggregate_sha256": "96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39",
            "panels": 10, "rows": 50555,
        },
        "empirical_option_pnl_authorized": False,
        "holdout_access_authorized": False,
        "new_market_source_requests_authorized": False,
        "strategy_promotion_authorized": False,
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



def test_request_flags_and_immutable_input_identities_fail_closed():
    request, decision, pins = _fixtures()
    request["new_market_source_requests_authorized"] = True
    try:
        auth.evaluate_authorization(request, decision, pins)
    except ValueError as exc:
        assert "new_market_source_requests_authorized=false" in str(exc)
    else:
        raise AssertionError("source request flag must not be enabled")
    request, decision, pins = _fixtures()
    request["forecast"]["artifact_id"] = 1
    try:
        auth.evaluate_authorization(request, decision, pins)
    except ValueError as exc:
        assert "immutable source/forecast identity changed" in str(exc)
    else:
        raise AssertionError("changed forecast artifact identity must not be accepted")


def test_one_use_marker_precedes_decryption_and_is_not_a_trigger():
    workflow_path = ROOT / ".github/workflows/phase8-cached-composite-preflight.yml"
    text = workflow_path.read_text(encoding="utf-8")
    marker = text.index("Commit durable one-use marker before any plaintext decryption or CSV scan")
    decrypt = text.index("Decrypt and merge in runner temporary storage only")
    assert marker < decrypt
    marker_section = text[marker:decrypt]
    assert "git cat-file -e" in marker_section and "PREFLIGHT_REQUEST_ALREADY_CONSUMED" in marker_section
    assert "git push origin HEAD:phase-08-developer" in marker_section
    assert "CONSUMED_BEFORE_DATASET_OPEN" in marker_section
    assert "dataset_plaintext_opened_at_marker_creation" in marker_section
    assert 'research/phase8/PHASE8_CACHED_COMPOSITE_PREFLIGHT_CONSUMED_R1.json' not in text[:text.index("workflow_dispatch")]
    job_start = text.index("  cached-composite-preflight:")
    top = text[:text.index("jobs:")]
    job = text[job_start:]
    assert "contents: read" in top and "contents: write" not in top
    assert "contents: write" in job


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
    test_request_flags_and_immutable_input_identities_fail_closed()
    test_one_use_marker_precedes_decryption_and_is_not_a_trigger()
    test_workflow_and_request_are_default_closed_and_metadata_only()
    print("Phase 8 preflight authorization tests PASS")
