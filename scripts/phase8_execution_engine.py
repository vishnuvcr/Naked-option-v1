from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from datetime import date, datetime, time
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COST_PATH = ROOT / "data" / "reference" / "phase8_cost_schedule.json"

DELTA_TARGETS = (0.40, 0.50, 0.60)
DTE_BUCKETS = {
    "D0": (0, 1),
    "D1": (2, 5),
    "D2": (6, 10),
    "D3": (11, 21),
}
EXIT_POLICIES = ("X0", "X1", "X2", "X3")
SCENARIOS = ("C0", "C1", "C2", "C3")
PROXY_SPREAD = {"C0": 0.0050, "C1": 0.0100, "C2": 0.0200, "C3": 0.0400}
INCREMENTAL_SLIPPAGE = {"C0": 0.0000, "C1": 0.0025, "C2": 0.0050, "C3": 0.0100}


@dataclass(frozen=True)
class Fill:
    price: float
    quality: str
    timestamp: pd.Timestamp
    basis: str


@dataclass(frozen=True)
class TradeCosts:
    brokerage: float
    exchange_transaction: float
    ipft: float
    stt: float
    sebi: float
    stamp_duty: float
    gst: float
    other: float = 0.0

    @property
    def total(self) -> float:
        return float(
            self.brokerage + self.exchange_transaction + self.ipft +
            self.stt + self.sebi + self.stamp_duty + self.gst + self.other
        )


def load_cost_schedule(path: Path = COST_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"broker", "rates", "exchange_transaction_charge", "other"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"cost schedule missing sections: {sorted(missing)}")
    return data


def direction_from_probability(
    probability: float,
    candidate: str,
) -> str | None:
    if not np.isfinite(probability):
        return None
    p = float(probability)
    if candidate == "P05":
        return "CE" if p > 0.55 else "PE" if p < 0.45 else None
    if candidate == "P06":
        return "CE" if p > 0.60 else "PE" if p < 0.40 else None
    if p > 0.50:
        return "CE"
    if p < 0.50:
        return "PE"
    return None


def classify_dte(dte_sessions: int) -> str | None:
    d = int(dte_sessions)
    for bucket, (lo, hi) in DTE_BUCKETS.items():
        if lo <= d <= hi:
            return bucket
    return None


def trading_session_dte(
    decision_date: date | pd.Timestamp,
    expiry_date: date | pd.Timestamp,
    session_dates: Sequence[date | pd.Timestamp],
) -> int:
    d0 = pd.Timestamp(decision_date).normalize()
    ex = pd.Timestamp(expiry_date).normalize()
    sessions = [pd.Timestamp(x).normalize() for x in session_dates]
    if d0 not in sessions or ex not in sessions:
        raise ValueError("decision and expiry dates must both exist in the supplied NSE session calendar")
    d_i = sessions.index(d0)
    e_i = sessions.index(ex)
    return int(e_i - d_i)


def _finite(value) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except Exception:
        return False


def _norm_option_type(value: str) -> str:
    v = str(value).strip().upper()
    aliases = {"CALL": "CE", "PUT": "PE", "C": "CE", "P": "PE"}
    return aliases.get(v, v)


def as_ist_timestamp(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("Asia/Kolkata")
    return ts.tz_convert("Asia/Kolkata")


def expiry_timestamp(value) -> pd.Timestamp:
    ts = as_ist_timestamp(value)
    if ts.hour == 0 and ts.minute == 0 and ts.second == 0 and ts.microsecond == 0:
        ts = ts.normalize() + pd.Timedelta(hours=15, minutes=30)
    return ts


def _norm_time_to_expiry(row: Mapping, decision_time: pd.Timestamp) -> float:
    if _finite(row.get("time_to_expiry")) and float(row["time_to_expiry"]) > 0:
        return float(row["time_to_expiry"])
    expiry = expiry_timestamp(row["expiry"])
    decision_time = as_ist_timestamp(decision_time)
    seconds = (expiry - decision_time).total_seconds()
    return max(seconds / (365.0 * 24.0 * 3600.0), 1e-8)


def _norm_dividend_yield(row: Mapping) -> float:
    return float(row.get("dividend_yield", 0.0)) if _finite(row.get("dividend_yield", 0.0)) else 0.0


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(float(x) / math.sqrt(2.0)))


def black_scholes_delta(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free: float,
    volatility: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> float:
    if not all(_finite(v) for v in (spot, strike, time_to_expiry, risk_free, volatility, dividend_yield)):
        raise ValueError("non-finite Black-Scholes input")
    if spot <= 0 or strike <= 0 or time_to_expiry <= 0 or volatility <= 0:
        raise ValueError("invalid Black-Scholes input")
    d1 = (
        math.log(spot / strike)
        + (risk_free - dividend_yield + 0.5 * volatility * volatility) * time_to_expiry
    ) / (volatility * math.sqrt(time_to_expiry))
    ot = _norm_option_type(option_type)
    if ot == "CE":
        return math.exp(-dividend_yield * time_to_expiry) * norm_cdf(d1)
    if ot == "PE":
        return -math.exp(-dividend_yield * time_to_expiry) * norm_cdf(-d1)
    raise ValueError("option_type must be CE or PE")


def black_scholes_price(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free: float,
    volatility: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> float:
    if volatility <= 0 or time_to_expiry <= 0:
        return float("nan")
    d1 = (
        math.log(spot / strike)
        + (risk_free - dividend_yield + 0.5 * volatility * volatility) * time_to_expiry
    ) / (volatility * math.sqrt(time_to_expiry))
    d2 = d1 - volatility * math.sqrt(time_to_expiry)
    df_r = math.exp(-risk_free * time_to_expiry)
    df_q = math.exp(-dividend_yield * time_to_expiry)
    ot = _norm_option_type(option_type)
    if ot == "CE":
        return spot * df_q * norm_cdf(d1) - strike * df_r * norm_cdf(d2)
    if ot == "PE":
        return strike * df_r * norm_cdf(-d2) - spot * df_q * norm_cdf(-d1)
    raise ValueError("option_type must be CE or PE")


def implied_volatility(
    premium: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free: float,
    option_type: str,
    dividend_yield: float = 0.0,
) -> float:
    if not all(_finite(v) for v in (premium, spot, strike, time_to_expiry, risk_free, dividend_yield)):
        return float("nan")
    if premium <= 0 or spot <= 0 or strike <= 0 or time_to_expiry <= 0:
        return float("nan")
    df_r = math.exp(-risk_free * time_to_expiry)
    df_q = math.exp(-dividend_yield * time_to_expiry)
    ot = _norm_option_type(option_type)
    if ot == "CE":
        lower = max(0.0, spot * df_q - strike * df_r)
        upper = spot * df_q
    elif ot == "PE":
        lower = max(0.0, strike * df_r - spot * df_q)
        upper = strike * df_r
    else:
        raise ValueError("option_type must be CE or PE")
    if premium < lower - 1e-8 or premium > upper + 1e-8:
        return float("nan")

    lo, hi = 1e-6, 5.0
    flo = black_scholes_price(spot, strike, time_to_expiry, risk_free, lo, ot, dividend_yield) - premium
    fhi = black_scholes_price(spot, strike, time_to_expiry, risk_free, hi, ot, dividend_yield) - premium
    if not (np.isfinite(flo) and np.isfinite(fhi)) or flo * fhi > 0:
        return float("nan")

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = black_scholes_price(spot, strike, time_to_expiry, risk_free, mid, ot, dividend_yield) - premium
        if abs(fm) < 1e-12:
            return float(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return float(0.5 * (lo + hi))


def selection_delta(row: Mapping, decision_time: pd.Timestamp, risk_free: float) -> tuple[float, str]:
    if _finite(row.get("delta")):
        return abs(float(row["delta"])), "OBSERVED_DELTA"

    spot = row.get("spot")
    if not _finite(spot):
        spot = row.get("underlying_spot")
    strike = row.get("strike")
    iv = row.get("iv")
    if _finite(spot) and _finite(strike):
        t = _norm_time_to_expiry(row, decision_time)
        if _finite(iv) and float(iv) > 0:
            try:
                delta = black_scholes_delta(
                    float(spot), float(strike), t, float(risk_free),
                    float(iv), _norm_option_type(row["option_type"]),
                    _norm_dividend_yield(row),
                )
                return abs(delta), "BLACK_SCHOLES_DELTA"
            except ValueError:
                pass
        return float("nan"), "MONEYNESS_FALLBACK"
    return float("nan"), "UNUSABLE"


def contract_id(row: Mapping) -> str:
    if row.get("contract_id") not in (None, ""):
        return str(row["contract_id"])
    return f"{pd.Timestamp(row['expiry']).date().isoformat()}|{float(row['strike']):.8f}|{_norm_option_type(row['option_type'])}"


def choose_contract(
    contracts: pd.DataFrame,
    decision_time: pd.Timestamp,
    planned_exit: pd.Timestamp,
    direction: str,
    delta_target: float,
    dte_bucket: str,
    session_dates: Sequence[date | pd.Timestamp],
    risk_free: float,
) -> tuple[pd.Series | None, str]:
    required = {"expiry", "strike", "option_type", "spot"}
    if not required.issubset(contracts.columns):
        raise ValueError(f"contract panel missing columns: {sorted(required - set(contracts.columns))}")
    planned_exit = pd.Timestamp(planned_exit)
    work = contracts.copy()
    work["expiry"] = pd.to_datetime(work["expiry"])
    work["option_type_norm"] = work["option_type"].map(_norm_option_type)
    work = work[work["option_type_norm"] == _norm_option_type(direction)].copy()
    if work.empty:
        return None, "NO_DIRECTION_CONTRACT"

    work = work[pd.to_datetime(work["expiry"]) > planned_exit].copy()
    if work.empty:
        return None, "NO_EXPIRY_AFTER_EXIT"

    dtes = []
    for _, row in work.iterrows():
        try:
            dte = trading_session_dte(pd.Timestamp(decision_time).date(), pd.Timestamp(row["expiry"]).date(), session_dates)
        except Exception:
            dte = -999
        dtes.append(dte)
    work["dte_sessions"] = dtes
    work = work[work["dte_sessions"].map(classify_dte) == dte_bucket].copy()
    if work.empty:
        return None, "NO_DTE_BUCKET_CONTRACT"

    deltas = []
    methods = []
    for _, row in work.iterrows():
        d, method = selection_delta(row, as_ist_timestamp(decision_time), risk_free)
        deltas.append(d)
        methods.append(method)
    work["selection_delta"] = deltas
    work["delta_method"] = methods

    if "prior_liquidity" not in work:
        work["prior_liquidity"] = 0.0
    work["prior_liquidity"] = pd.to_numeric(work["prior_liquidity"], errors="coerce").fillna(0.0)
    work["abs_moneyness"] = np.log(work["strike"].astype(float) / work["spot"].astype(float)).abs()
    work["strike_distance"] = (work["strike"].astype(float) - work["spot"].astype(float)).abs()
    work["greek_available"] = work["delta_method"].isin(["OBSERVED_DELTA", "BLACK_SCHOLES_DELTA"])
    work["selection_priority"] = np.where(work["greek_available"], 0, 1)
    work["abs_delta_error"] = np.where(
        work["greek_available"],
        (work["selection_delta"] - float(delta_target)).abs(),
        np.inf,
    )
    work["fallback_moneyness"] = np.where(work["greek_available"], np.inf, work["abs_moneyness"])
    work = work[work["greek_available"] | np.isfinite(work["abs_moneyness"])].copy()
    if work.empty:
        return None, "NO_SELECTION_INPUT"

    work["contract_id_norm"] = [contract_id(r) for _, r in work.iterrows()]
    work = work.sort_values(
        ["selection_priority", "abs_delta_error", "fallback_moneyness",
         "prior_liquidity", "abs_moneyness", "strike_distance", "contract_id_norm"],
        ascending=[True, True, True, False, True, True, True],
        kind="mergesort",
    )
    return work.iloc[0], "PASS"


def proxy_spread_component(premium: float, tick_size: float, scenario: str) -> float:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown cost scenario {scenario}")
    if not _finite(premium) or premium < 0:
        raise ValueError("premium must be non-negative")
    if not _finite(tick_size) or tick_size <= 0:
        raise ValueError("tick_size must be positive")
    return max(float(tick_size), float(premium) * PROXY_SPREAD[scenario])


def validate_quote_timestamp(
    quote_timestamp,
    executable_timestamp,
    max_forward_seconds: int,
) -> tuple[bool, str]:
    q = as_ist_timestamp(quote_timestamp)
    e = as_ist_timestamp(executable_timestamp)
    delta = (q - e).total_seconds()
    if delta < 0:
        return False, "QUOTE_BEFORE_EXECUTION"
    if delta > int(max_forward_seconds):
        return False, "QUOTE_TOO_FAR_AFTER_EXECUTION"
    return True, "PASS"


def fill_price(
    base_price: float,
    side: str,
    timestamp,
    quality: str,
    scenario: str,
    tick_size: float,
    ask: float | None = None,
    bid: float | None = None,
    quote_timestamp=None,
    max_quote_forward_seconds: int | None = None,
) -> Fill:
    if not _finite(base_price) or base_price < 0:
        raise ValueError("invalid base price")
    ts = as_ist_timestamp(timestamp)
    side = side.upper()
    quality = quality.upper()
    slip = INCREMENTAL_SLIPPAGE[scenario]
    if quality == "Q2":
        if quote_timestamp is None or max_quote_forward_seconds is None:
            raise ValueError("Q2 fills require a quote timestamp and stale-data window")
        ok, reason = validate_quote_timestamp(quote_timestamp, ts, max_quote_forward_seconds)
        if not ok:
            raise ValueError(reason)
        if side == "BUY":
            if not _finite(ask):
                raise ValueError("Q2 BUY requires ask")
            px = float(ask) * (1.0 + slip)
            basis = "ASK_PLUS_SLIPPAGE"
        elif side == "SELL":
            if not _finite(bid):
                raise ValueError("Q2 SELL requires bid")
            px = max(0.0, float(bid) * (1.0 - slip))
            basis = "BID_MINUS_SLIPPAGE"
        else:
            raise ValueError("side must be BUY or SELL")
    elif quality == "Q1":
        spread = proxy_spread_component(base_price, tick_size, scenario)
        slip_amt = float(base_price) * slip
        if side == "BUY":
            px = float(base_price) + spread + slip_amt
            basis = "OHLC_OPEN_PLUS_SYNTHETIC_SPREAD"
        elif side == "SELL":
            px = max(0.0, float(base_price) - spread - slip_amt)
            basis = "OHLC_OPEN_MINUS_SYNTHETIC_SPREAD"
        else:
            raise ValueError("side must be BUY or SELL")
    else:
        raise ValueError("execution quality must be Q1 or Q2")
    return Fill(price=float(px), quality=quality, timestamp=ts, basis=basis)

def break_even_log_return(
    option_type: str,
    spot: float,
    strike: float,
    premium: float,
) -> float:
    if not all(_finite(v) for v in (spot, strike, premium)) or spot <= 0 or strike <= 0 or premium < 0:
        return float("nan")
    ot = _norm_option_type(option_type)
    if ot == "CE":
        return float(math.log((strike + premium) / spot))
    if ot == "PE":
        if strike <= premium:
            return float("nan")
        return float(math.log((strike - premium) / spot))
    raise ValueError("option_type must be CE or PE")


def _rate_band(schedule: Mapping, trade_date: date, key: str) -> Mapping:
    for row in schedule.get(key, []):
        start = pd.Timestamp(row["effective_from"]).date()
        end = pd.Timestamp(row["effective_to"]).date() if row.get("effective_to") else None
        if trade_date >= start and (end is None or trade_date <= end):
            return row
    raise ValueError(f"no dated rate found for {key} on {trade_date}")


def compute_round_trip_costs(
    entry_premium: float,
    exit_premium: float,
    lot_size: int,
    trade_date: date | pd.Timestamp,
    scenario: str,
    brokerage_per_order: float | None = None,
    brokerage_status: str = "BROKERAGE_FALLBACK",
    schedule: Mapping | None = None,
) -> TradeCosts:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown cost scenario {scenario}")
    if lot_size <= 0 or entry_premium < 0 or exit_premium < 0:
        raise ValueError("invalid premium or lot size")
    cfg = schedule or load_cost_schedule()
    td = pd.Timestamp(trade_date).date()
    ex = _rate_band(cfg, td, "exchange_transaction_charge")
    stt = _rate_band(cfg, td, "rates")
    if brokerage_per_order is None:
        brokerage_per_order = float(
            cfg["broker"]["current_fno_brokerage_rupees_per_executed_order"]
            if brokerage_status == "VERIFIED_CURRENT"
            else cfg["broker"]["historical_unverified_fallback_rupees_per_executed_order"]
        )
    brokerage = 2.0 * float(brokerage_per_order)
    entry_turnover = float(entry_premium) * int(lot_size)
    exit_turnover = float(exit_premium) * int(lot_size)
    premium_turnover = entry_turnover + exit_turnover

    exchange = premium_turnover / 1e7 * float(ex["rupees_per_crore_premium_per_side"])
    ipft = premium_turnover / 1e7 * float(ex["ipft_rupees_per_crore_per_side"])
    stt_cost = exit_turnover * float(stt["stt_option_sale_rate"])
    sebi = premium_turnover * float(cfg["other"]["sebi_turnover_fee_rate"])
    stamp = entry_turnover * float(cfg["other"]["equity_option_stamp_duty_rate_buyer"])
    gst_base = brokerage + exchange + ipft + sebi
    gst = gst_base * float(cfg["other"]["gst_rate"])
    return TradeCosts(
        brokerage=brokerage,
        exchange_transaction=exchange,
        ipft=ipft,
        stt=stt_cost,
        sebi=sebi,
        stamp_duty=stamp,
        gst=gst,
    )


def conservative_trigger_exit(
    bar: Mapping,
    policy: str,
    entry_premium: float,
    trailing_high: float | None,
) -> tuple[float | None, str | None, float]:
    high = float(bar["high"])
    low = float(bar["low"])
    if not all(_finite(x) for x in (high, low)):
        return None, None, max(float(trailing_high or entry_premium), entry_premium)

    current_high = max(float(trailing_high or entry_premium), entry_premium)

    if policy == "X1":
        target = entry_premium * 1.50
        if high >= target:
            return target, "TAKE_PROFIT", max(current_high, high)

    if policy == "X2":
        stop = entry_premium * 0.65
        if low <= stop:
            return stop, "STOP_LOSS", max(current_high, high)

    if policy == "X3":
        if trailing_high is not None and trailing_high > 0:
            stop = trailing_high * 0.75
            if low <= stop:
                return stop, "TRAILING_STOP", max(current_high, high)
    return None, None, max(current_high, high)


def validate_no_overlap(
    open_until: pd.Timestamp | None,
    signal_time: pd.Timestamp,
    close_processed: bool = False,
) -> bool:
    if open_until is None:
        return True
    signal = as_ist_timestamp(signal_time)
    close = as_ist_timestamp(open_until)
    if signal < close:
        return False
    if signal > close:
        return True
    return bool(close_processed)


def make_planned_daily_exit(session_dates, decision_time, H: int) -> pd.Timestamp:
    d = pd.Timestamp(decision_time).normalize()
    sessions = [pd.Timestamp(x).normalize() for x in session_dates]
    if d not in sessions:
        raise ValueError("decision date missing from session calendar")
    idx = sessions.index(d)
    if idx + H >= len(sessions):
        raise ValueError("insufficient future sessions for requested daily horizon")
    return sessions[idx + H] + pd.Timedelta(hours=15, minutes=15)
