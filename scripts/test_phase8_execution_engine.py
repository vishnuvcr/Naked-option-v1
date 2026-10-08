# Phase 8 hosted engineering-gate trigger after tester-approved import correction.
from __future__ import annotations

from datetime import date
from pathlib import Path
import math
import pandas as pd

from phase8_execution_engine import (
    DTE_BUCKETS,
    SCENARIOS,
    black_scholes_delta,
    break_even_log_return,
    classify_dte,
    compute_round_trip_costs,
    conservative_trigger_exit,
    direction_from_probability,
    fill_price,
    validate_quote_timestamp,
    validate_no_overlap,
    expiry_timestamp,
    make_planned_daily_exit,
    choose_contract,
    trading_session_dte,
)


def test_direction_boundaries():
    assert direction_from_probability(0.5001, "P01") == "CE"
    assert direction_from_probability(0.4999, "P01") == "PE"
    assert direction_from_probability(0.50, "P01") is None
    assert direction_from_probability(0.45, "P05") is None
    assert direction_from_probability(0.5501, "P05") == "CE"
    assert direction_from_probability(0.3999, "P06") == "PE"
    assert direction_from_probability(0.60, "P06") is None


def test_dte_buckets():
    assert classify_dte(0) == "D0"
    assert classify_dte(1) == "D0"
    assert classify_dte(2) == "D1"
    assert classify_dte(5) == "D1"
    assert classify_dte(6) == "D2"
    assert classify_dte(10) == "D2"
    assert classify_dte(11) == "D3"
    assert classify_dte(21) == "D3"
    assert classify_dte(22) is None


def test_black_scholes_delta_signs():
    ce = black_scholes_delta(100, 100, 30/365, 0.05, 0.20, "CE")
    pe = black_scholes_delta(100, 100, 30/365, 0.05, 0.20, "PE")
    assert 0.0 < ce < 1.0
    assert -1.0 < pe < 0.0
    assert abs(ce - pe - 1.0) < 0.10


def test_break_even():
    assert abs(break_even_log_return("CE", 100, 100, 5) - math.log(1.05)) < 1e-12
    assert abs(break_even_log_return("PE", 100, 100, 5) - math.log(0.95)) < 1e-12
    assert math.isnan(break_even_log_return("PE", 100, 100, 100))


def test_trading_session_dte_is_timezone_agnostic():
    sessions = [pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-02"), pd.Timestamp("2026-10-05")]
    assert trading_session_dte(pd.Timestamp("2026-10-01 15:30", tz="Asia/Kolkata"), pd.Timestamp("2026-10-05", tz="Asia/Kolkata"), sessions) == 2


def test_contract_selection_tie_break():
    rows = pd.DataFrame([
        {"contract_id":"B","expiry":"2026-10-30","strike":100,"option_type":"CE","spot":100,"delta":0.50,"prior_liquidity":20},
        {"contract_id":"A","expiry":"2026-10-30","strike":100,"option_type":"CE","spot":100,"delta":0.50,"prior_liquidity":20},
        {"contract_id":"C","expiry":"2026-10-30","strike":101,"option_type":"CE","spot":100,"delta":0.50,"prior_liquidity":10},
    ])
    sessions = pd.date_range("2026-10-01","2026-10-30",freq="B").tolist()
    assert trading_session_dte(pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-30"), sessions) == 21
    row, reason = choose_contract(rows, pd.Timestamp("2026-10-01 15:30"), pd.Timestamp("2026-10-02 15:15"), "CE", 0.50, "D3", sessions, 0.05)
    assert reason == "PASS"
    assert row["contract_id"] == "A"


def test_fill_prices():
    q2_buy = fill_price(100, "BUY", "2026-10-01 09:16", "Q2", "C1", 0.05, ask=101, quote_timestamp="2026-10-01 09:16", max_quote_forward_seconds=120)
    q2_sell = fill_price(100, "SELL", "2026-10-01 15:15", "Q2", "C1", 0.05, bid=99, quote_timestamp="2026-10-01 15:15", max_quote_forward_seconds=120)
    assert abs(q2_buy.price - 101.2525) < 1e-12
    assert abs(q2_sell.price - 98.7525) < 1e-12
    q1_buy = fill_price(100, "BUY", "2026-10-01 09:16", "Q1", "C1", 0.05)
    q1_sell = fill_price(100, "SELL", "2026-10-01 15:15", "Q1", "C1", 0.05)
    assert abs(q1_buy.price - 101.25) < 1e-12
    assert abs(q1_sell.price - 98.75) < 1e-12


def test_stop_first_and_trailing():
    bar = {"high": 160, "low": 60}
    px, reason, _ = conservative_trigger_exit(bar, "X2", 100, None)
    assert px == 65 and reason == "STOP_LOSS"
    px, reason, high = conservative_trigger_exit({"high":120,"low":70}, "X3", 100, 120)
    assert px == 90 and reason == "TRAILING_STOP"
    assert high == 120


def test_daily_exit_mapping():
    sessions = [pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-02"), pd.Timestamp("2026-10-05")]
    assert make_planned_daily_exit(sessions, pd.Timestamp("2026-10-01 15:30", tz="Asia/Kolkata"), 1) == pd.Timestamp("2026-10-02 15:15", tz="Asia/Kolkata")


def test_cost_arithmetic():
    costs = compute_round_trip_costs(100, 120, 75, date(2026, 10, 8), "C1", brokerage_status="VERIFIED_CURRENT")
    assert costs.brokerage == 20.0
    assert costs.stt == 13.5
    assert costs.stamp_duty == 0.225
    assert costs.total > costs.brokerage


def test_expiry_timestamp_and_d0_selection():
    ex = expiry_timestamp("2026-10-02")
    assert ex == pd.Timestamp("2026-10-02 15:30", tz="Asia/Kolkata")
    rows = pd.DataFrame([
        {"contract_id":"D0", "expiry":"2026-10-02", "strike":100, "option_type":"CE", "spot":100, "delta":0.50, "prior_liquidity":10},
    ])
    sessions = [pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-02")]
    row, reason = choose_contract(rows, pd.Timestamp("2026-10-01 15:30", tz="Asia/Kolkata"), pd.Timestamp("2026-10-02 15:15", tz="Asia/Kolkata"), "CE", 0.50, "D0", sessions, 0.05)
    assert reason == "PASS" and row["contract_id"] == "D0"


def test_moneyness_fallback_does_not_compare_to_delta_target():
    rows = pd.DataFrame([
        {"contract_id":"NEAR", "expiry":"2026-10-30", "strike":101, "option_type":"CE", "spot":100, "prior_liquidity":1},
        {"contract_id":"FAR", "expiry":"2026-10-30", "strike":108, "option_type":"CE", "spot":100, "prior_liquidity":100},
    ])
    sessions = pd.bdate_range("2026-10-01", "2026-10-30").tolist()
    assert trading_session_dte(pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-30"), sessions) == 21
    row1, reason1 = choose_contract(rows, pd.Timestamp("2026-10-01 15:30"), pd.Timestamp("2026-10-02 15:15"), "CE", 0.40, "D3", sessions, 0.05)
    row2, reason2 = choose_contract(rows, pd.Timestamp("2026-10-01 15:30"), pd.Timestamp("2026-10-02 15:15"), "CE", 0.60, "D3", sessions, 0.05)
    assert reason1 == reason2 == "PASS"
    assert row1["contract_id"] == row2["contract_id"] == "NEAR"
    assert row1["delta_method"] == row2["delta_method"] == "MONEYNESS_FALLBACK"


def test_quote_timestamp_and_overlap_ordering():
    assert validate_quote_timestamp("2026-10-01 09:17", "2026-10-01 09:16", 120) == (True, "PASS")
    assert validate_quote_timestamp("2026-10-01 09:15", "2026-10-01 09:16", 120)[0] is False
    assert validate_quote_timestamp("2026-10-01 09:20", "2026-10-01 09:16", 120)[0] is False
    assert validate_no_overlap(pd.Timestamp("2026-10-01 10:00"), pd.Timestamp("2026-10-01 09:59")) is False
    assert validate_no_overlap(pd.Timestamp("2026-10-01 10:00"), pd.Timestamp("2026-10-01 10:00")) is False
    assert validate_no_overlap(pd.Timestamp("2026-10-01 10:00"), pd.Timestamp("2026-10-01 10:00"), close_processed=True) is True
    assert validate_no_overlap(pd.Timestamp("2026-10-01 10:00"), pd.Timestamp("2026-10-01 10:01")) is True


if __name__ == "__main__":
    test_direction_boundaries()
    test_dte_buckets()
    test_black_scholes_delta_signs()
    test_break_even()
    test_trading_session_dte_is_timezone_agnostic()
    test_contract_selection_tie_break()
    test_fill_prices()
    test_stop_first_and_trailing()
    test_expiry_timestamp_and_d0_selection()
    test_moneyness_fallback_does_not_compare_to_delta_target()
    test_quote_timestamp_and_overlap_ordering()
    test_daily_exit_mapping()
    test_cost_arithmetic()
    print("Phase 8 execution engine regression PASS")
