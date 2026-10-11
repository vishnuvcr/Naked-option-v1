from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "phase-08-long-option.yml"

def require(text, token):
    assert token in text, f"missing workflow token: {token}"

def main():
    text = WF.read_text(encoding="utf-8")
    require(text, "workflow_call:")
    require(text, "workflow_dispatch:")
    require(text, "empirical_authorized:")
    require(text, "default: false")
    require(text, "permissions:")
    require(text, "actions: read")
    require(text, 'REFERENCE_ARTIFACT_ID: "11638738288"')
    require(text, 'REFERENCE_ARTIFACT_SHA256: "3e8a22ded608668b5674f7aed609fefa5c4befcde39ca58b7f208e59ab25959a9')
    require(text, 'REFERENCE_MANIFEST_SHA256: "f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091')
    require(text, 'REFERENCE_AGGREGATE_SHA256: "96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39')
    require(text, 'REFERENCE_COMMIT: "b50be8cfa1ebe008a800e65a53f9c0fb2581aecb')
    require(text, 'REFERENCE_RUN_ID: "37957677656')
    require(text, "actions/cache/restore@v4")
    require(text, "actions/cache/save@v4")
    require(text, "sha256sum")
    require(text, 'test "$actual" = "$REFERENCE_ARTIFACT_SHA256"')
    require(text, 'test "$manifest_actual" = "$REFERENCE_MANIFEST_SHA256"')
    require(text, 'test "$aggregate_actual" = "$REFERENCE_AGGREGATE_SHA256"')
    require(text, "scripts/validate_phase7_reference_panels.py")
    require(text, "phase8-run994-")
    reconstruct = text.split("  reconstruct:", 1)[1].split("  empirical-authorization:", 1)[0]
    assert "scripts/reconstruct_phase7_predictions.py" not in reconstruct, "production workflow must not refit Phase 7 forecasts"
    require(reconstruct, "--artifact-dir data/cache/reference/phase7_run994/unpacked")
    require(text, "scripts/validate_phase8_forecast_panel.py")
    require(text, "scripts/test_phase8_execution_engine.py")
    require(text, "research/phase8/PHASE8_EMPIRICAL_AUTHORIZATION.md")
    require(text, "STATUS: AUTHORIZED")
    assert "  push:" not in text, "direct push trigger would duplicate research-protocol caller"
    assert "Refuse placeholder empirical execution" in text, "empirical job must remain fail-closed until runner exists"
    assert "\\${{" not in text, "literal escaped GitHub expressions remain"
    print("Phase 8 workflow contract PASS")

if __name__ == "__main__":
    main()
