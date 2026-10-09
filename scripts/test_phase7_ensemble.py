# Phase 7 fresh gated trigger after Run 645 closure approval; no scientific logic change.
# Phase 7 fresh gated trigger after tester-approved horizon reapplication; no scientific logic change.
# Phase 7 workflow trigger after approved detector sequencing correction; no scientific logic change.
# Phase 7 verification trigger: approved regression corrections are now live.
# Phase 7 gated trigger after approved detector correction; no scientific logic change.
# Phase 7 fresh gated-run trigger: no scientific logic change.
# Phase 7 gated-run trigger: no scientific logic change.
from pathlib import Path
import numpy as np
SRC=(Path(__file__).resolve().parents[1]/"scripts/run_phase7_ensemble.py").read_text(encoding="utf-8")
ns={"__file__": str(Path(__file__).resolve().parents[0] / "run_phase7_ensemble.py"), "__name__":"phase7_test_import"}
exec(compile(SRC,"phase7","exec"),ns)

def main():
    for token in ["family_bootstrap","moving_block_resample","500","block_len","observed_max_brier_improvement","chronological_blocks","regime_fallback_count","CAPTURE_ORDER"]:
        assert token in SRC, token
    base={m:np.array([0.4,0.5,0.6]) for m in ns["METHODS"]}
    for m in ns["BLOCKED"]: base[m]=np.full(3,np.nan)
    original_run_scope=ns["p6"].run_scope
    original_metrics=ns["p6"].metrics
    def fake_run_scope(_df,intraday=False,horizons=None):
        for _h in horizons:
            ns["p6"].metrics(np.array([0.0]),np.array([0.5]),np.array([0.0]),1)
    ns["p6"].run_scope=fake_run_scope
    try:
        captured=ns["capture_scope"](None,False,[1,2,3])
    finally:
        ns["p6"].run_scope=original_run_scope
        ns["p6"].metrics=original_metrics
    assert {("1","E01"),("2","E01"),("3","E01")}.issubset(captured.keys())
    _,_,p3,_=ns["combine"](base)
    assert np.allclose(p3,[0.4,0.5,0.6])

    y=np.array([0,1]*250,dtype=float)
    blocks=[np.arange(0,20),np.arange(200,220),np.arange(220,240),np.arange(240,500)]
    p={m:np.full(500,0.5) for m in ns["METHODS"]}
    out=ns["stacking"](p,y,blocks)
    assert np.isnan(out[:20]).all()
    assert np.isfinite(out[200:220]).all()
    assert np.isfinite(out[220:]).any()

    vol=np.ones(500); trend=np.ones(500)
    p1=np.full(500,0.6); p4=np.full(500,0.4)
    r8,r9,diag,fb=ns["regimes"](p1,p4,y,vol,trend,blocks)
    assert len(diag)>=1
    assert all(sum(d["test_counts"].values())>0 for d in diag)
    assert np.allclose(r8[220:],0.55)
    assert np.allclose(r9[220:],0.45)

    baseline=ns["causal_baseline"](y,blocks)
    # Verify the allocation-light implementation is bit-for-bit equivalent
    # to the frozen legacy sampler for fixed seeds and representative edge cases.
    def legacy_resample(n, block_len, rng):
        if n <= 0: return np.array([], dtype=int)
        L=min(int(block_len),int(n))
        starts=np.arange(0,n-L+1,dtype=int)
        pool=[np.arange(s,s+L,dtype=int) for s in starts]
        n_blocks=int(np.ceil(n/L))
        selected=rng.integers(0,len(pool),size=n_blocks)
        return np.concatenate([pool[k] for k in selected])[:n]
    for n0, L0 in [(10,4),(1000,20),(2500,60),(3,20),(1,1),(0,20)]:
        fast=ns["moving_block_resample"](n0,L0,np.random.default_rng(42))
        legacy=legacy_resample(n0,L0,np.random.default_rng(42))
        assert np.array_equal(fast,legacy), (n0,L0)
    idx=ns["moving_block_resample"](10,4,np.random.default_rng(42))
    assert len(idx)==10
    assert any(idx[i+3]-idx[i]==3 for i in range(7))
    fam=ns["family_bootstrap"](y,{"P01":np.full(500,0.5)},baseline,20)
    assert "family_p_value" in fam and 0.0 <= fam["family_p_value"] <= 1.0

    # P10 is a registered abstention candidate: both interval endpoints abstain,
    # while values immediately outside the interval remain eligible.
    assert ns["ABSTAIN"]["P10"] == (0.45, 0.55)
    p10_values=np.array([0.449999,0.45,0.50,0.55,0.550001,np.nan])
    p10_eligible=np.isfinite(p10_values)&~((p10_values>=0.45)&(p10_values<=0.55))
    assert p10_eligible.tolist() == [True,False,False,False,True,False]

    # Non-evaluable rows must remain NaN in family differentials; only eligible
    # P10 abstentions receive a zero differential.
    diff=ns["candidate_brier_differential"](
        np.array([1.0,0.0,1.0,np.nan]),
        np.array([0.6,0.5,0.4,0.7]),
        np.array([0.5,0.5,0.5,0.5]),
        "P10",
    )
    assert np.isclose(diff[0],0.09)
    assert diff[1] == 0.0
    assert np.isclose(diff[2],-0.11)
    assert np.isnan(diff[3])

    # Per-block metrics must match the candidate-specific eligibility mask.
    masked_blocks=ns["block_diagnostics"](
        np.array([0.0,1.0,0.0,1.0]),
        np.array([0.4,0.6,0.2,0.8]),
        [np.arange(4)],
        np.array([True,False,True,False]),
    )
    assert len(masked_blocks)==1 and masked_blocks[0]["n"]==2
    assert np.isclose(masked_blocks[0]["accuracy"],1.0)

    # Feature rows with missing volatility/trend cannot inflate the low/low regime.
    regime_y=np.array([0.0,1.0]*115)
    regime_vol=np.ones(230); regime_trend=np.ones(230)
    regime_vol[:20]=np.nan; regime_trend[:20]=np.nan
    regime_p1=np.full(230,0.60); regime_p4=np.full(230,0.40)
    regime_blocks=[np.arange(0,20),np.arange(200,220),np.arange(220,230)]
    _,_,regime_diag,_=ns["regimes"](
        regime_p1,regime_p4,regime_y,regime_vol,regime_trend,regime_blocks
    )
    assert len(regime_diag)==1
    state_counts=regime_diag[0]["train_counts"]
    assert sum(state_counts.values())==200, state_counts
    assert state_counts["00"]==200, state_counts
    print("Phase 7 regression checks PASS")

if __name__=="__main__": main()
