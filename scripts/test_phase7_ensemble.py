# Phase 7 gated trigger after approved detector correction; no scientific logic change.
# Phase 7 fresh gated-run trigger: no scientific logic change.
# Phase 7 gated-run trigger: no scientific logic change.
from pathlib import Path
import numpy as np
SRC=(Path(__file__).resolve().parents[1]/"scripts/run_phase7_ensemble.py").read_text(encoding="utf-8")
ns={}
exec(compile(SRC,"phase7","exec"),ns)

def main():
    for token in ["family_bootstrap","500","block_len","observed_max_brier_improvement","chronological_blocks","regime_fallback_count","CAPTURE_ORDER"]:
        assert token in SRC, token
    base={m:np.array([0.4,0.5,0.6]) for m in ns["METHODS"]}
    for m in ns["BLOCKED"]: base[m]=np.full(3,np.nan)
    _,_,p3,_=ns["combine"](base)
    assert np.allclose(p3,[0.4,0.5,0.6])

    y=np.array([0,1]*250,dtype=float)
    blocks=[np.arange(0,20),np.arange(200,220),np.arange(220,240),np.arange(240,500)]
    p={m:np.full(500,0.5) for m in ns["METHODS"]}
    out=ns["stacking"](p,y,blocks)
    assert np.isnan(out[:220]).all()
    assert np.isfinite(out[220:]).any()

    vol=np.ones(500); trend=np.ones(500)
    p1=np.full(500,0.6); p4=np.full(500,0.4)
    r8,r9,diag,fb=ns["regimes"](p1,p4,y,vol,trend,blocks)
    assert len(diag)>=1
    assert np.allclose(r8[220:],0.55)
    assert np.allclose(r9[220:],0.45)

    baseline=ns["causal_baseline"](y,blocks)
    fam=ns["family_bootstrap"](y,{"P01":np.full(500,0.5)},baseline,blocks,20)
    assert "family_p_value" in fam and 0.0 <= fam["family_p_value"] <= 1.0
    print("Phase 7 regression checks PASS")

if __name__=="__main__": main()
