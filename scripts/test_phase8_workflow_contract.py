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
    require(text, 'RUN654_ARTIFACT_ID: "11551679532"')
    require(text, 'RUN654_ARTIFACT_SHA256: "c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a"')
    require(text, "actions/cache/restore@v4")
    require(text, "actions/cache/save@v4")
    require(text, "sha256sum")
    require(text, 'test "$actual" = "$RUN654_ARTIFACT_SHA256"')
    require(text, "scripts/reconstruct_phase7_predictions.py")
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
