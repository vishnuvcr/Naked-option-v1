#!/usr/bin/env python3
"""Synthetic-only regression tests. No network, secret, or real market-data use."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

path = Path(__file__).with_name("phase8p_greek_prediction.py")
spec = importlib.util.spec_from_file_location("phase8p", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def main():
    result = m.synthetic_self_test()
    assert result["real_artifacts_opened"] is False
    assert result["model_fitted"] is False

    # Paired inference must not silently drop a non-finite row.
    try:
        m.paired_brier_bootstrap([0,1], [.2,np.nan], [.3,.7], 2, reps=10)
    except ValueError as exc:
        assert "non-finite" in str(exc)
    else:
        raise AssertionError("non-finite paired row was silently accepted")

    # Fixed seeds make the bootstrap reproducible.
    y = np.asarray([0,1] * 60, dtype=float)
    p0 = np.where(y == 1, .56, .44)
    p1 = np.where(y == 1, .66, .34)
    a = m.paired_brier_bootstrap(y, p0, p1, 20, reps=100, seed=42)
    b = m.paired_brier_bootstrap(y, p0, p1, 20, reps=100, seed=42)
    assert a == b and a["mean_brier_improvement"] > 0

    # Exact fail-closed authorization contract.
    bad_decisions = [
        (False, True, {"status":"PASS","model_fit_authorized":True,"holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
        (True, False, {"status":"PASS","model_fit_authorized":True,"holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
        (True, True, {"status":"PASS","model_fit_authorized":True,"holdout_access_authorized":True,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
        (True, True, {"status":"BLOCKED","model_fit_authorized":False,"holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
    ]
    for scope, code, decision in bad_decisions:
        try:
            m.enforce_fit_gate(scope, code, decision)
        except m.GateBlocked:
            pass
        else:
            raise AssertionError("invalid authorization state was accepted")
    # Exact Greek valuation timestamp means source bar epoch + stored offset equals decision UTC.
    base = pd.Timestamp("2025-01-02T04:00:00Z").timestamp()
    snap_rows = [
        {"timestamp_epoch": base-60, "greek_valuation_offset_seconds": 60, "id":"exact"},
        {"timestamp_epoch": base-120, "greek_valuation_offset_seconds": 60, "id":"stale"},
        {"timestamp_epoch": base, "greek_valuation_offset_seconds": 60, "id":"future"},
    ]
    exact = m.exact_snapshot_rows(snap_rows, pd.Timestamp(base, unit="s", tz="UTC"))
    assert [r["id"] for r in exact] == ["exact"]

    # Frozen label-end adapters match the Phase 3 source rules: daily row shift(-H)
    # and intraday exact timestamp+H-minute lookup.
    daily = m.daily_target_end_dates(["2025-01-02","2025-01-03"], 
                                     ["2025-01-02","2025-01-03","2025-01-06","2025-01-07"], 2)
    assert str(daily[0].date()) == "2025-01-06" and str(daily[1].date()) == "2025-01-07"
    intrats = pd.date_range("2025-01-02T04:00:00Z", periods=5, freq="min")
    ends = m.intraday_target_end_timestamps([intrats[0],intrats[1]], intrats, 2)
    assert ends[0] == intrats[2] and ends[1] == intrats[3]

    # Synthetic per-minute spot data; the first row of a new session must not
    # manufacture a one-minute cross-session return.
    t0 = pd.Timestamp("2025-01-02T09:15:00", tz="Asia/Kolkata").timestamp()
    t1 = pd.Timestamp("2025-01-03T09:15:00", tz="Asia/Kolkata").timestamp()
    spot_rows = []
    for session, start in (("2025-01-02", t0), ("2025-01-03", t1)):
        for k in range(130):
            spot_rows.append({"timestamp_epoch":start+k*60, "session_date":session,
                              "nifty_close":22000.0 + k + (0 if session=="2025-01-02" else 500)})
    spot = pd.DataFrame(spot_rows)
    feats = m.build_spot_features(spot, [
        pd.Timestamp(t0+60*71, unit="s", tz="UTC"),
        pd.Timestamp(t1+60, unit="s", tz="UTC")])
    assert feats.loc[0,"spot_exact_bar_missing"] == 0
    assert abs(feats.loc[0,"ret_1"] - np.log(22070.0/22069.0)) < 1e-10
    assert np.isnan(feats.loc[1,"ret_1"]), "session gap must not be used as one-minute return"

    # Exercise both fixed model arms on synthetic data only and ensure same test rows.
    rng = np.random.default_rng(42)
    n = 1200
    decisions = pd.date_range("2025-01-01T04:00:00Z", periods=n, freq="min")
    rawx = rng.normal(size=(n,3))
    labels = ((rawx[:,0] + 0.35*rawx[:,1] + rng.normal(0,0.6,n)) > 0).astype(float)
    x0 = pd.DataFrame(rawx[:,:2], columns=["ret_1","rv20"])
    x1 = pd.DataFrame(rawx, columns=["ret_1","rv20","call_delta_median"])
    target_end = decisions + pd.Timedelta(minutes=1)
    blocks = np.repeat(np.arange(30),40)
    approved = {"status":"PASS","model_fit_authorized":True,"holdout_access_authorized":False,
                "option_pnl_authorized":False,"strategy_promotion_authorized":False}
    predicted = m.walk_forward_predict(labels,target_end,decisions,blocks,x0,x1,"intraday",
                                       minimum_training_rows=100,scope_approved=True,
                                       code_approved=True,preflight=approved)
    for key,result in predicted.items():
        assert result["fit_blocks"] >= 20, (key,result["fit_blocks"])
        assert np.array_equal(np.isfinite(result["p_spot"]),np.isfinite(result["p_augmented"])), key
        mask=np.isfinite(result["p_spot"])
        assert mask.sum() >= 500, (key,int(mask.sum()))

    # Scope-approved synthetic fit does not mean real input authority.
    print("PASS: Phase 8P synthetic tests; synthetic model smoke-test only; real artifacts untouched")

if __name__ == "__main__":
    main()
