#!/usr/bin/env python3
"""Synthetic-only regression tests. No network, secret, or real market data use."""
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
    assert result["empirical_model_fitted"] is False

    # Inference fails closed rather than silently dropping invalid paired observations.
    try:
        m.paired_brier_bootstrap([0,1], [.2,np.nan], [.3,.7], 2, reps=10)
    except ValueError as exc:
        assert "non-finite" in str(exc)
    else:
        raise AssertionError("non-finite paired row was silently accepted")

    y = np.asarray([0,1] * 60, dtype=float)
    p0 = np.where(y == 1, .56, .44)
    p1 = np.where(y == 1, .66, .34)
    a = m.paired_brier_bootstrap(y, p0, p1, 20, reps=100, seed=42)
    b = m.paired_brier_bootstrap(y, p0, p1, 20, reps=100, seed=42)
    assert a == b and a["mean_brier_improvement"] > 0

    # Missing matches preserve the original panel block unit during resampling.
    positions = np.arange(0, 240, 2)
    gap = m.paired_brier_bootstrap(
        y, p0, p1, 20, reps=50, seed=42,
        population_n=240, row_positions=positions,
    )
    assert gap["population_n"] == 240 and gap["original_panel_positions_used"] is True

    # Fake booleans/dicts cannot open the fit gate.
    try:
        m.enforce_fit_gate()
    except m.GateBlocked as exc:
        assert "AUTHORIZATION_BUNDLE_PATH_REQUIRED" in str(exc)
    else:
        raise AssertionError("fit gate accepted absent tester authorization")
    try:
        m.enforce_fit_gate(True, True, {
            "status":"PASS","model_fit_authorized":True,
            "holdout_access_authorized":False,"option_pnl_authorized":False,
            "strategy_promotion_authorized":False,
        })
    except TypeError:
        pass
    else:
        raise AssertionError("caller-controlled boolean/dict authorization was accepted")

    # Exact Greek timestamp selection ignores SPOT rows lacking Greek offsets.
    base = pd.Timestamp("2025-01-02T04:00:00Z").timestamp()
    decision = pd.Timestamp(base, unit="s", tz="UTC")
    snap_rows = [
        {"row_type":"OPTION","timestamp_epoch":base-60,"greek_valuation_offset_seconds":60,"id":"exact"},
        {"row_type":"SPOT","timestamp_epoch":base-60,"greek_valuation_offset_seconds":np.nan,"id":"spot"},
        {"row_type":"OPTION","timestamp_epoch":base-120,"greek_valuation_offset_seconds":60,"id":"stale"},
        {"row_type":"OPTION","timestamp_epoch":base,"greek_valuation_offset_seconds":60,"id":"future"},
    ]
    exact = m.exact_snapshot_rows(snap_rows, decision)
    assert [r["id"] for r in exact] == ["exact"]
    try:
        m.exact_snapshot_rows([{"row_type":"OPTION","timestamp_epoch":base,
                                "greek_valuation_offset_seconds":np.nan}], decision)
    except m.GateBlocked as exc:
        assert "OPTION_GREEK_VALUATION_TIMESTAMP_FIELDS_MISSING" in str(exc)
    else:
        raise AssertionError("option row missing valuation offset was accepted")

    # One mixed composite chunk must build exact Greek features and separately retain SPOT rows.
    option_rows = []
    for i in range(5):
        option_rows.append({
            "row_type":"OPTION","timestamp_epoch":base-60,
            "greek_valuation_offset_seconds":60,"expiry_date":"2025-01-07",
            "expiry_flag":"WEEK","expiry_code":0,"returned_strike":25000+i*50,
            "option_type":"CE","greek_status":"GREEKS_ESTIMATED_FROM_INVERTED_IV",
            "delta":.60+i*.01,"gamma":.02,"theta_per_day":-1.,
            "vega_per_1pct_iv":.4,"greek_implied_volatility":.20,
            "open_interest":100,"volume":10,"greek_iv_source":"IV_INVERTED_FROM_OPTION_CLOSE",
            "expiry_mapping_source":"HF_EXPIRY_PARTITION_FILELIST_PROXY","data_quality_flags":"",
        })
        option_rows.append({
            "row_type":"OPTION","timestamp_epoch":base-60,
            "greek_valuation_offset_seconds":60,"expiry_date":"2025-01-07",
            "expiry_flag":"WEEK","expiry_code":0,"returned_strike":25000+i*50,
            "option_type":"PE","greek_status":"GREEKS_ESTIMATED_FROM_INVERTED_IV",
            "delta":-.40-i*.01,"gamma":.025,"theta_per_day":-.8,
            "vega_per_1pct_iv":.45,"greek_implied_volatility":.25,
            "open_interest":200,"volume":20,"greek_iv_source":"IV_INVERTED_FROM_OPTION_CLOSE",
            "expiry_mapping_source":"HF_EXPIRY_PARTITION_FILELIST_PROXY","data_quality_flags":"",
        })
    spot_row = {
        "row_type":"SPOT","timestamp_epoch":base-60,"greek_valuation_offset_seconds":np.nan,
        "session_date":"2025-01-02","nifty_close":25000.0,
    }
    spot_sink = []
    greek_frame = m.build_option_feature_frame(
        [pd.DataFrame(option_rows+[spot_row])], [decision], spot_sink
    )
    assert greek_frame.loc[0,"greek_exact_snapshot_missing"] == 0
    assert greek_frame.loc[0,"n_call"] == 5 and greek_frame.loc[0,"n_put"] == 5
    assert abs(greek_frame.loc[0,"delta_imbalance"]-.20) < 1e-12
    assert len(spot_sink) == 1 and len(spot_sink[0]) == 1

    # The approved daily decision convention is a date-only cash close, 15:30 IST.
    assert m.daily_close_timestamp("2025-01-02") == pd.Timestamp("2025-01-02T10:00:00Z")
    daily_ends = m.daily_target_end_dates(
        ["2025-01-02","2025-01-03","2025-01-06"],
        ["2025-01-02","2025-01-03","2025-01-06"], 1,
    )
    assert str(daily_ends[0].date()) == "2025-01-03"
    assert str(daily_ends[1].date()) == "2025-01-06"
    assert pd.isna(daily_ends[2])

    # Daily features need an exact 15:30 IST bar-end; holidays/weekends are not fabricated.
    all_spot = []
    for session, start in (
        ("2025-01-02", pd.Timestamp("2025-01-02T09:15:00",tz="Asia/Kolkata").timestamp()),
        ("2025-01-03", pd.Timestamp("2025-01-03T09:15:00",tz="Asia/Kolkata").timestamp()),
    ):
        for k in range(375):
            all_spot.append({
                "timestamp_epoch":start+k*60,"session_date":session,
                "nifty_close":22000.0+k+(0 if session=="2025-01-02" else 500),
            })
    daily_features = m.build_daily_spot_features(
        pd.DataFrame(all_spot), ["2025-01-02","2025-01-03"]
    )
    assert (daily_features["daily_decision_time_convention"] == m.DAILY_TIME_CONVENTION).all()
    assert (daily_features["spot_exact_bar_missing"] == 0).all()
    assert str(daily_features.loc[0,"decision_timestamp_utc"]) == "2025-01-02T10:00:00+00:00"

    # Exact intraday target end is source timestamp+H and only if that instant exists.
    intrats = pd.date_range("2025-01-02T04:00:00Z", periods=5, freq="min")
    ends = m.intraday_target_end_timestamps([intrats[0],intrats[1]], intrats, 2)
    assert ends[0] == intrats[2] and ends[1] == intrats[3]

    # Synthetic per-minute spot data: never manufacture cross-session minute returns.
    t0 = pd.Timestamp("2025-01-02T09:15:00", tz="Asia/Kolkata").timestamp()
    t1 = pd.Timestamp("2025-01-03T09:15:00", tz="Asia/Kolkata").timestamp()
    spot_rows = []
    for session, start in (("2025-01-02", t0), ("2025-01-03", t1)):
        for k in range(130):
            spot_rows.append({
                "timestamp_epoch":start+k*60, "session_date":session,
                "nifty_close":22000.0+k+(0 if session=="2025-01-02" else 500),
            })
    spot = pd.DataFrame(spot_rows)
    feats = m.build_spot_features(spot, [
        pd.Timestamp(t0+60*71, unit="s", tz="UTC"),
        pd.Timestamp(t1+60, unit="s", tz="UTC"),
    ])
    assert feats.loc[0,"spot_exact_bar_missing"] == 0
    assert abs(feats.loc[0,"ret_1"] - np.log(22070.0/22069.0)) < 1e-10
    assert np.isnan(feats.loc[1,"ret_1"]), "session gap must not be used as one-minute return"

    # Panel block indices must remain in chronological order and not recur.
    frame = pd.DataFrame({
        "layer":["intraday"]*4,"horizon":[5]*4,"source_row_index":range(4),
        "decision_timestamp":pd.date_range("2025-01-01T04:00:00Z",periods=4,freq="h"),
        "label_direction":[0,1,0,1],"future_return":[-.01,.02,-.03,.04],
        "block_index":[0,0,1,1],
        **{f"P{i:02d}":[.4,.6,.45,.55] for i in range(1,11)},
    })
    try:
        m.validate_panel_frame(frame.assign(block_index=[0,1,0,1]),"intraday",5)
    except m.GateBlocked as exc:
        assert "BLOCK_INDEX_NOT_MONOTONE_WITH_DECISION_TIME" in str(exc)
    else:
        raise AssertionError("decreasing/reordered block IDs were accepted")

    # Synthetic-only smoke test of both fixed model arms. Production wrapper still requires auth.
    rng = np.random.default_rng(42)
    n = 1200
    decisions = pd.date_range("2025-01-01T04:00:00Z",periods=n,freq="min")
    rawx = rng.normal(size=(n,3))
    labels = ((rawx[:,0] + 0.35*rawx[:,1] + rng.normal(0,.6,n)) > 0).astype(float)
    x0 = pd.DataFrame(rawx[:,:2],columns=["ret_1","rv20"])
    x1 = pd.DataFrame(rawx,columns=["ret_1","rv20","call_delta_median"])
    target_end = decisions + pd.Timedelta(minutes=1)
    blocks = np.repeat(np.arange(30),40)
    predicted = m._walk_forward_predict_core(
        labels,target_end,decisions,blocks,x0,x1,"intraday",minimum_training_rows=100
    )
    for key, output in predicted.items():
        assert output["fit_blocks"] >= 20, (key,output["fit_blocks"])
        assert np.array_equal(np.isfinite(output["p_spot"]),np.isfinite(output["p_augmented"])), key
        assert np.isfinite(output["p_spot"]).sum() >= 500, (key,int(np.isfinite(output["p_spot"]).sum()))
    print("PASS: Phase 8P synthetic tests; synthetic-only model smoke-test; real artifacts untouched")

if __name__ == "__main__":
    main()
