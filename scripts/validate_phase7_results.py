# Phase 7 approved-workflow trigger: no scientific logic change.
import json
from pathlib import Path
import math

METHODS=[f"P{i:02d}" for i in range(1,11)]
HORIZONS={"daily":["1","2","3","5","10"],"intraday":["5","15","30","60","120"]}

def main():
    p=Path("data/reports/phase7_ensemble_results.json")
    d=json.loads(p.read_text(encoding="utf-8"))
    assert d["protocol"]=="research/phase7/PHASE7_METHOD_SPEC.md"
    for layer,hs in HORIZONS.items():
        for h in hs:
            cell=d[layer]["horizons"][h]
            assert "_FAMILY_TEST" in cell
            ft=cell["_FAMILY_TEST"]
            assert 0.0 <= ft["family_p_value"] <= 1.0
            for m in METHODS:
                x=cell[m]
                assert x["status"]=="EXECUTED"
                assert x["n"]>0
                assert 0.0 <= x["accuracy"] <= 1.0
                assert 0.0 <= x["balanced_accuracy"] <= 1.0
                assert 0.0 <= x["brier"] <= 1.0
                assert math.isfinite(x["log_loss"])
                assert 0.0 <= x["roc_auc"] <= 1.0
                assert "chronological_blocks" in x
                if m in ("P08","P09","P10"):
                    assert "regime_diagnostics" in x
                    assert "regime_fallback_count" in x
                    assert len(x["regime_diagnostics"]) == len(x["chronological_blocks"])
    print("Phase 7 result schema PASS")

if __name__=="__main__":
    main()
