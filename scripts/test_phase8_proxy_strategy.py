from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_phase8_proxy_strategy as runner


def test_grid_is_frozen_and_unique():
    grid = runner.build_grid()
    assert len(grid) == 4800
    assert len({row["config_id"] for row in grid}) == 4800
    assert len({row["cell_id"] for row in grid}) == 100


def test_signal_thresholds_and_lot_schedule():
    assert runner.engine.direction_from_probability(0.5001, "P01") == "CE"
    assert runner.engine.direction_from_probability(0.4999, "P01") == "PE"
    assert runner.engine.direction_from_probability(0.50, "P01") is None
    assert runner.engine.direction_from_probability(0.45, "P10") is None
    assert runner.engine.direction_from_probability(0.5501, "P10") == "CE"
    assert runner.lot_size_for_expiry("2023-12-28") == 50
    assert runner.lot_size_for_expiry("2024-05-02") == 25
    assert runner.lot_size_for_expiry("2024-11-26") == 75
    assert runner.lot_size_for_expiry("2026-01-06") == 65


def test_select_contract_uses_direction_delta_and_dte_bucket():
    future_expiry = int(pd.Timestamp("2024-01-05 15:30:00", tz=runner.IST).timestamp())
    options = pd.DataFrame([
        {"timestamp_epoch": 100, "option_type": "CE", "expiry_epoch": future_expiry,
         "expiry_session_idx": 4, "option_open": 10.0, "returned_strike": 100.0,
         "rolling_spot": 100.0, "nifty_close": 100.0, "delta": 0.30,
         "greek_valuation_offset_seconds": 0.0, "time_to_expiry_years": 0.01,
         "implied_volatility": 0.2, "risk_free_rate_decimal": 0.05,
         "dividend_yield_decimal": 0.0, "expiry_key": "2024-01-05", "contract_code": 0},
        {"timestamp_epoch": 100, "option_type": "CE", "expiry_epoch": future_expiry,
         "expiry_session_idx": 4, "option_open": 11.0, "returned_strike": 101.0,
         "rolling_spot": 100.0, "nifty_close": 100.0, "delta": 0.49,
         "greek_valuation_offset_seconds": 0.0, "time_to_expiry_years": 0.01,
         "implied_volatility": 0.2, "risk_free_rate_decimal": 0.05,
         "dividend_yield_decimal": 0.0, "expiry_key": "2024-01-05", "contract_code": 1},
        {"timestamp_epoch": 100, "option_type": "PE", "expiry_epoch": future_expiry,
         "expiry_session_idx": 4, "option_open": 9.0, "returned_strike": 100.0,
         "rolling_spot": 100.0, "nifty_close": 100.0, "delta": -0.50,
         "greek_valuation_offset_seconds": 0.0, "time_to_expiry_years": 0.01,
         "implied_volatility": 0.2, "risk_free_rate_decimal": 0.05,
         "dividend_yield_decimal": 0.0, "expiry_key": "2024-01-05", "contract_code": 2},
    ])
    row = runner.select_contract(
        options, np.array([0]), np.array([3]), {100: 0}, 100, 300, "CE",
        0.50, "D1", 0, {}
    )
    assert row == 1


def test_intraday_exit_planning_respects_horizon():
    times = np.array([100, 160, 220, 280, 340], dtype=np.int64)
    assert runner.plan_exit_epoch(100, "intraday", 3, ["2024-01-01"], times) == 280


def test_daily_exit_planning_uses_next_sessions_close_window():
    decision = int(pd.Timestamp("2024-01-01 15:30:00", tz=runner.IST).timestamp())
    planned = int(pd.Timestamp("2024-01-02 15:15:00", tz=runner.IST).timestamp())
    times = np.array([decision - 60, planned, planned + 60], dtype=np.int64)
    assert runner.plan_exit_epoch(
        decision, "daily", 1, ["2024-01-01", "2024-01-02"], times
    ) == planned


def test_take_profit_stop_and_trailing_exit_paths():
    times = np.array([100, 160, 220], dtype=np.int64)
    idxs = np.array([0, 1, 2], dtype=np.int64)
    data = {
        "times": times,
        "option_open": np.array([100.0, 120.0, 140.0]),
        "option_high": np.array([120.0, 160.0, 150.0]),
        "option_low": np.array([100.0, 105.0, 140.0]),
    }
    skeleton = {"series_idx": idxs, "entry_series_pos": 0, "scheduled_series_pos": 2,
                "entry_base": 100.0}
    result = runner.simulate_exit(skeleton, "X1", pd.DataFrame(), data)
    assert result["exit_reason"] == "TAKE_PROFIT"
    assert result["exit_base"] == 150.0
    assert result["exit_epoch"] == 160

    data["option_high"] = np.array([110.0, 120.0, 130.0])
    data["option_low"] = np.array([100.0, 60.0, 90.0])
    result = runner.simulate_exit(skeleton, "X2", pd.DataFrame(), data)
    assert result["exit_reason"] == "STOP_LOSS"
    assert result["exit_base"] == 65.0
    assert result["exit_epoch"] == 160

    data["option_high"] = np.array([120.0, 125.0, 130.0])
    data["option_low"] = np.array([100.0, 80.0, 90.0])
    result = runner.simulate_exit(skeleton, "X3", pd.DataFrame(), data)
    assert result["exit_reason"] == "TRAILING_STOP"
    assert result["exit_base"] == 90.0
    assert result["exit_epoch"] == 160


def test_intraday_horizon_after_close_is_skipped():
    decision = int(pd.Timestamp("2024-01-02 15:00:00", tz=runner.IST).timestamp())
    times = np.array([decision + 60, decision + 300], dtype=np.int64)
    assert runner.plan_exit_epoch(decision, "intraday", 120, ["2024-01-02"], times) is None


def test_stop_gap_uses_worse_open_not_unfillable_stop_level():
    times = np.array([100, 160, 220], dtype=np.int64)
    idxs = np.array([0, 1, 2], dtype=np.int64)
    data = {
        "times": times,
        "option_open": np.array([100.0, 50.0, 80.0]),
        "option_high": np.array([110.0, 70.0, 90.0]),
        "option_low": np.array([90.0, 40.0, 70.0]),
    }
    skeleton = {"series_idx": idxs, "entry_series_pos": 0, "scheduled_series_pos": 2,
                "entry_base": 100.0}
    result = runner.simulate_exit(skeleton, "X2", pd.DataFrame(), data)
    assert result["exit_reason"] == "STOP_LOSS"
    assert result["exit_base"] == 50.0
    assert result["exit_epoch"] == 160


def test_vectorized_exit_falls_back_to_scheduled_price_when_no_trigger():
    idxs = np.array([0, 1, 2], dtype=np.int64)
    data = {
        "times": np.array([100, 160, 220], dtype=np.int64),
        "option_open": np.array([100.0, 108.0, 112.0]),
        "option_high": np.array([120.0, 130.0, 140.0]),
        "option_low": np.array([90.0, 85.0, 80.0]),
    }
    skeleton = {"series_idx": idxs, "entry_series_pos": 0, "scheduled_series_pos": 2,
                "entry_base": 100.0}
    result = runner.simulate_exit(skeleton, "X1", pd.DataFrame(), data)
    assert result["exit_reason"] == "TIME_EXIT"
    assert result["exit_base"] == 112.0
    assert result["exit_epoch"] == 220


def test_vectorized_trailing_exit_ignores_invalid_bar_and_uses_prior_high():
    idxs = np.array([0, 1, 2, 3], dtype=np.int64)
    data = {
        "times": np.array([100, 160, 220, 280], dtype=np.int64),
        "option_open": np.array([100.0, 100.0, 80.0, 85.0]),
        "option_high": np.array([120.0, np.nan, 115.0, 90.0]),
        "option_low": np.array([95.0, 60.0, 80.0, 84.0]),
    }
    skeleton = {"series_idx": idxs, "entry_series_pos": 0, "scheduled_series_pos": 3,
                "entry_base": 100.0}
    result = runner.simulate_exit(skeleton, "X3", pd.DataFrame(), data)
    assert result["exit_reason"] == "TRAILING_STOP"
    assert result["exit_base"] == 80.0
    assert result["exit_epoch"] == 220


def test_close_valued_greek_delta_is_not_used_before_valuation_time():
    entry_epoch = int(pd.Timestamp("2024-01-02 10:00:00", tz=runner.IST).timestamp())
    row = pd.Series({
        "timestamp_epoch": entry_epoch,
        "greek_valuation_offset_seconds": 60.0,
        "delta": 0.80,
        "rolling_spot": 100.0,
        "nifty_close": 100.0,
        "returned_strike": 100.0,
        "implied_volatility": 0.20,
        "time_to_expiry_years": 99.0,
        "expiry_key": "2024-06-27",
        "risk_free_rate_decimal": 0.0,
        "dividend_yield_decimal": 0.0,
        "option_type": "CE",
    })
    value_early, method_early = runner.resolve_delta(row, entry_epoch)
    assert method_early == "BLACK_SCHOLES_RAW_IV_AT_DECISION_PROXY"
    assert value_early < 0.80
    value_on_time, method_on_time = runner.resolve_delta(row, entry_epoch + 60)
    assert method_on_time == "OBSERVED_DELTA_ASOF"
    assert abs(value_on_time - 0.80) < 1e-12


def test_vectorized_delta_matches_pointwise_asof_rules():
    entry_epoch = int(pd.Timestamp("2024-01-02 10:00:00", tz=runner.IST).timestamp())
    rows = pd.DataFrame([
        {"timestamp_epoch": entry_epoch, "greek_valuation_offset_seconds": 0.0,
         "delta": 0.70, "rolling_spot": 100.0, "returned_strike": 100.0,
         "implied_volatility": 0.20, "expiry_epoch": int(pd.Timestamp("2024-06-27 15:30:00", tz=runner.IST).timestamp()),
         "risk_free_rate_decimal": 0.0, "dividend_yield_decimal": 0.0,
         "expiry_key": "2024-06-27", "option_type": "CE"},
        {"timestamp_epoch": entry_epoch, "greek_valuation_offset_seconds": 60.0,
         "delta": 0.80, "rolling_spot": 100.0, "returned_strike": 100.0,
         "implied_volatility": 0.20, "expiry_epoch": int(pd.Timestamp("2024-06-27 15:30:00", tz=runner.IST).timestamp()),
         "risk_free_rate_decimal": 0.0, "dividend_yield_decimal": 0.0, "option_type": "CE"},
    ])
    vector_values, vector_methods = runner.resolve_deltas_vectorized(rows, entry_epoch)
    pointwise = [runner.resolve_delta(rows.iloc[i], entry_epoch) for i in range(len(rows))]
    assert vector_methods[0] == "OBSERVED_DELTA_ASOF"
    assert abs(vector_values[0] - 0.70) < 1e-12
    assert vector_methods[1] == "BLACK_SCHOLES_RAW_IV_AT_DECISION_PROXY"
    assert abs(vector_values[1] - pointwise[1][0]) < 1e-10
    assert vector_methods.tolist() == [pointwise[0][1], pointwise[1][1]]


def test_contract_selection_does_not_use_current_bar_close_for_spot_fallback():
    options = pd.DataFrame([
        {"timestamp_epoch": 100, "option_type": "CE", "expiry_epoch": 500,
         "expiry_session_idx": 4, "option_open": 10.0, "returned_strike": 110.0,
         "rolling_spot": np.nan, "nifty_close": 100.0, "delta": 0.7,
         "greek_valuation_offset_seconds": 60.0, "implied_volatility": 0.2,
         "risk_free_rate_decimal": 0.0, "dividend_yield_decimal": 0.0,
         "expiry_key": "2024-01-05", "contract_code": 0},
        {"timestamp_epoch": 100, "option_type": "CE", "expiry_epoch": 500,
         "expiry_session_idx": 4, "option_open": 11.0, "returned_strike": 100.0,
         "rolling_spot": np.nan, "nifty_close": 100.0, "delta": 0.7,
         "greek_valuation_offset_seconds": 60.0, "implied_volatility": 0.2,
         "risk_free_rate_decimal": 0.0, "dividend_yield_decimal": 0.0,
         "expiry_key": "2024-01-05", "contract_code": 1},
    ])
    row = runner.select_contract(
        options, np.array([0]), np.array([2]), {100: 0}, 100, 300, "CE",
        0.50, "D1", 0, {}
    )
    # Without a point-in-time rolling spot, the selection must not use the
    # same minute's future NIFTY close to prefer the ATM strike (code 1).
    assert row == 0


def test_row_type_normalization_tolerates_whitespace_and_bom():
    raw = pd.Series(["OPTION", " option ", "\ufeffOPTION", "SPOT", " spot "])
    normalized = runner.normalise_row_type(raw)
    assert normalized.tolist() == ["OPTION", "OPTION", "OPTION", "SPOT", "SPOT"]


def test_proxy_cost_scenarios_get_more_conservative():
    base = 100.0
    net = []
    for scenario in runner.SCENARIOS:
        buy = runner.engine.fill_price(base, "BUY", 100, "Q1", scenario, runner.TICK_SIZE)
        sell = runner.engine.fill_price(110.0, "SELL", 160, "Q1", scenario, runner.TICK_SIZE)
        net.append(sell.price - buy.price)
    assert net[0] > net[1] > net[2] > net[3]


if __name__ == "__main__":
    tests = [
        test_grid_is_frozen_and_unique,
        test_signal_thresholds_and_lot_schedule,
        test_select_contract_uses_direction_delta_and_dte_bucket,
        test_intraday_exit_planning_respects_horizon,
        test_daily_exit_planning_uses_next_sessions_close_window,
        test_take_profit_stop_and_trailing_exit_paths,
        test_intraday_horizon_after_close_is_skipped,
        test_stop_gap_uses_worse_open_not_unfillable_stop_level,
        test_vectorized_exit_falls_back_to_scheduled_price_when_no_trigger,
        test_vectorized_trailing_exit_ignores_invalid_bar_and_uses_prior_high,
        test_close_valued_greek_delta_is_not_used_before_valuation_time,
        test_vectorized_delta_matches_pointwise_asof_rules,
        test_contract_selection_does_not_use_current_bar_close_for_spot_fallback,
        test_row_type_normalization_tolerates_whitespace_and_bom,
        test_proxy_cost_scenarios_get_more_conservative,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("PASS all 13 Phase 8 proxy-strategy synthetic tests")
