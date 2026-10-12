from __future__ import annotations

"""Phase 8 Q1/OHLC proxy backtest over the already-collected composite.

No source acquisition or bid/ask validation is performed here. The run uses the
saved Phase 7 probability panels, observed option OHLC rows, explicit synthetic
spread/slippage scenarios, and the frozen Paytm Money / statutory cost schedule.
Results are exploratory proxy results, not executable-quote results.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_1samp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import phase8_execution_engine as engine

METHODS = [f"P{i:02d}" for i in range(1, 11)]
LAYERS = {"daily": (1, 2, 3, 5, 10), "intraday": (5, 15, 30, 60, 120)}
EXPECTED_PANELS = 10
EXPECTED_GRID = 4800
SCENARIOS = ("C0", "C1", "C2", "C3")
DELTA_TARGETS = (0.40, 0.50, 0.60)
DTE_BUCKETS = {"D0": (0, 1), "D1": (2, 5), "D2": (6, 10), "D3": (11, 21)}
EXIT_POLICIES = ("X0", "X1", "X2", "X3")
TICK_SIZE = 0.05
IST = "Asia/Kolkata"
REQUIRED_OPTION_COLUMNS = [
    "row_type", "timestamp_epoch", "session_date", "returned_strike", "option_type",
    "option_open", "option_high", "option_low", "option_close", "expiry_date",
    "time_to_expiry_years", "implied_volatility", "delta", "rolling_spot",
    "nifty_close", "risk_free_rate_decimal", "dividend_yield_decimal",
    "option_volume", "open_interest",
]
NUMERIC_COLUMNS = [
    "timestamp_epoch", "returned_strike", "option_open", "option_high", "option_low",
    "option_close", "time_to_expiry_years", "implied_volatility", "delta", "rolling_spot",
    "nifty_close", "risk_free_rate_decimal", "dividend_yield_decimal", "option_volume",
    "open_interest",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def lot_size_for_expiry(expiry: str) -> int:
    """NIFTY lot size by expiry effective date; contracts are date-effective."""
    d = str(expiry)[:10]
    if not d or d == "nan":
        return 0
    if d < "2024-05-02":
        return 50
    if d < "2024-11-26":
        return 25
    if d < "2026-01-06":
        return 75
    return 65


def decision_epoch(value, layer: str) -> int:
    """Interpret saved Phase 7 decision timestamps using the frozen conventions."""
    ts = pd.Timestamp(value)
    if layer == "daily":
        # The saved daily forecast is available after that session's close.
        if ts.tzinfo is None:
            if ts.hour == 0 and ts.minute == 0 and ts.second == 0:
                ts = ts.normalize() + pd.Timedelta(hours=15, minutes=30)
            ts = ts.tz_localize(IST)
        else:
            ts = ts.tz_convert(IST)
    else:
        # Phase 7 accepted intraday panels interpret naive values as UTC.
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        ts = ts.tz_convert("UTC")
    return int(ts.timestamp())


def session_date_for_epoch(epoch: int) -> str:
    return pd.Timestamp(int(epoch), unit="s", tz="UTC").tz_convert(IST).strftime("%Y-%m-%d")


def plan_exit_epoch(decision: int, layer: str, horizon: int, sessions: list[str],
                    unique_times: np.ndarray) -> int | None:
    if layer == "intraday":
        planned = int(decision + int(horizon) * 60)
        # Intraday trades cannot silently roll into the next session because an
        # H-minute target falls after the 15:30 NSE close. Those cases are skipped.
        decision_local = pd.Timestamp(decision, unit="s", tz="UTC").tz_convert(IST)
        planned_local = pd.Timestamp(planned, unit="s", tz="UTC").tz_convert(IST)
        if planned_local.date() != decision_local.date() or planned_local.strftime("%H:%M:%S") > "15:30:00":
            return None
    else:
        d = session_date_for_epoch(decision)
        pos = int(np.searchsorted(np.asarray(sessions, dtype=object), d, side="left"))
        if pos >= len(sessions):
            return None
        if sessions[pos] != d:
            # A date without an observed source session cannot anchor a daily forecast.
            return None
        target = pos + int(horizon)
        if target >= len(sessions):
            return None
        planned_ts = pd.Timestamp(sessions[target] + " 15:15:00", tz=IST)
        planned = int(planned_ts.timestamp())
    target_pos = int(np.searchsorted(unique_times, planned, side="left"))
    if target_pos >= len(unique_times):
        return None
    return planned


def normalise_option_type(values: pd.Series) -> pd.Series:
    aliases = {"CALL": "CE", "C": "CE", "PUT": "PE", "P": "PE"}
    return values.astype(str).str.strip().str.upper().replace(aliases)


def load_option_data(parts_dir: Path) -> tuple[pd.DataFrame, list[str], dict]:
    """Load the narrow OHLC execution panel; skips unusable price rows, never refits."""
    files = sorted(parts_dir.glob("*.csv.gz"))
    if not files:
        raise FileNotFoundError(f"No decrypted monthly CSV.GZ parts in {parts_dir}")
    frames = []
    sessions_seen: set[str] = set()
    diagnostics = Counter()
    for path in files:
        for chunk in pd.read_csv(path, usecols=REQUIRED_OPTION_COLUMNS, chunksize=200_000,
                                 low_memory=False):
            if "session_date" in chunk:
                sessions_seen.update(
                    chunk["session_date"].dropna().astype(str).str.slice(0, 10).tolist()
                )
            diagnostics["source_rows_read"] += len(chunk)
            rows = chunk[chunk["row_type"].astype(str).str.upper() == "OPTION"].copy()
            diagnostics["option_rows_read"] += len(rows)
            if rows.empty:
                continue
            for col in NUMERIC_COLUMNS:
                rows[col] = pd.to_numeric(rows[col], errors="coerce")
            rows["expiry_key"] = rows["expiry_date"].fillna("").astype(str).str.slice(0, 10)
            rows["option_type"] = normalise_option_type(rows["option_type"])
            # Deterministic key ordering only. Duplicate observations are not an
            # input gate and are retained; stable source order breaks exact ties.
            rows["strike_key"] = rows["returned_strike"].round(2).map(
                lambda x: "" if not np.isfinite(x) else f"{x:.2f}"
            )
            rows["contract_key"] = (
                rows["expiry_key"] + "|" + rows["strike_key"] + "|" + rows["option_type"]
            )
            frames.append(rows)
    if not frames:
        raise ValueError("No OPTION rows were available to the proxy backtest.")
    options = pd.concat(frames, ignore_index=True)
    before = len(options)
    options = options[
        options["timestamp_epoch"].notna()
        & options["returned_strike"].notna()
        & options["expiry_key"].str.match(r"^\d{4}-\d{2}-\d{2}$")
        & options["option_type"].isin(["CE", "PE"])
    ].copy()
    diagnostics["rows_skipped_missing_key_fields"] = int(before - len(options))
    # Q1 proxy fills require usable observed OHLC. This is row eligibility for
    # calculating a trade, not a source-validation gate that stops the study.
    ohlc_ok = (
        np.isfinite(options["option_open"])
        & np.isfinite(options["option_high"])
        & np.isfinite(options["option_low"])
        & (options["option_open"] > 0)
        & (options["option_high"] > 0)
        & (options["option_low"] > 0)
    )
    diagnostics["rows_skipped_unusable_ohlc"] = int((~ohlc_ok).sum())
    options = options[ohlc_ok].copy()
    options["timestamp_epoch"] = options["timestamp_epoch"].astype(np.int64)
    options["contract_code"], contract_names = pd.factorize(options["contract_key"], sort=True)
    sessions = sorted(x for x in sessions_seen if x and x != "nan")
    if not sessions:
        sessions = sorted(
            set(pd.to_datetime(options["timestamp_epoch"], unit="s", utc=True)
                .dt.tz_convert(IST).dt.strftime("%Y-%m-%d").tolist())
        )
    session_array = np.asarray(sessions, dtype=object)
    options["expiry_session_idx"] = np.searchsorted(
        session_array, options["expiry_key"].to_numpy(dtype=object), side="left"
    ).astype(np.int32)
    expiry_epoch_cache: dict[str, int] = {}
    for exp in options["expiry_key"].dropna().astype(str).unique():
        try:
            expiry_epoch_cache[exp] = int(pd.Timestamp(exp + " 15:30:00", tz=IST).timestamp())
        except Exception:
            expiry_epoch_cache[exp] = 0
    options["expiry_epoch"] = options["expiry_key"].map(expiry_epoch_cache).fillna(0).astype(np.int64)
    options.sort_values(["timestamp_epoch", "contract_code"], kind="mergesort", inplace=True)
    options.reset_index(drop=True, inplace=True)
    times = options["timestamp_epoch"].to_numpy(dtype=np.int64)
    unique_times, starts = np.unique(times, return_index=True)
    ends = np.r_[starts[1:], len(options)].astype(np.int64)
    options.attrs["contract_names_count"] = int(len(contract_names))
    diagnostics["usable_option_rows"] = int(len(options))
    diagnostics["unique_contracts"] = int(len(contract_names))
    diagnostics["unique_option_timestamps"] = int(len(unique_times))
    diagnostics["part_files_used"] = int(len(files))
    options.attrs["diagnostics"] = dict(diagnostics)
    options.attrs["sessions"] = sessions
    options.attrs["unique_times"] = unique_times
    options.attrs["starts"] = starts.astype(np.int64)
    options.attrs["ends"] = ends
    return options, sessions, dict(diagnostics)


def resolve_delta(row: pd.Series, decision_time: int) -> tuple[float, str]:
    observed = row.get("delta")
    try:
        if np.isfinite(float(observed)) and abs(float(observed)) <= 1.0:
            return abs(float(observed)), "OBSERVED_DELTA"
    except Exception:
        pass
    spot = row.get("rolling_spot")
    try:
        if not np.isfinite(float(spot)) or float(spot) <= 0:
            spot = row.get("nifty_close")
        spot = float(spot)
        strike = float(row.get("returned_strike"))
        iv = float(row.get("implied_volatility"))
        if iv > 3:
            iv /= 100.0
        t = float(row.get("time_to_expiry_years"))
        if not np.isfinite(t) or t <= 0:
            ex = pd.Timestamp(str(row.get("expiry_key")) + " 15:30:00", tz=IST)
            t = max((ex.timestamp() - decision_time) / (365.0 * 86400.0), 1e-8)
        rf = float(row.get("risk_free_rate_decimal"))
        if not np.isfinite(rf):
            rf = 0.05
        q = float(row.get("dividend_yield_decimal"))
        if not np.isfinite(q):
            q = 0.0
        if spot > 0 and strike > 0 and 0 < iv <= 5 and t > 0:
            d1 = (math.log(spot / strike) + (rf - q + 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
            nd1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
            ot = str(row.get("option_type", "")).upper()
            signed = math.exp(-q * t) * nd1 if ot == "CE" else -math.exp(-q * t) * (1.0 - nd1)
            if np.isfinite(signed) and abs(signed) <= 1:
                return abs(signed), "BLACK_SCHOLES_DELTA"
    except Exception:
        pass
    return float("nan"), "MONEYNESS_FALLBACK"


def select_contract(options: pd.DataFrame, starts: np.ndarray, ends: np.ndarray,
                    time_position: dict[int, int], entry_epoch: int, planned_exit: int,
                    direction: str, delta_target: float, dte_bucket: str,
                    entry_session_idx: int, candidate_cache: dict) -> int | None:
    key = (int(entry_epoch), int(planned_exit), direction, float(delta_target), dte_bucket)
    if key in candidate_cache:
        return candidate_cache[key]
    pos = time_position.get(int(entry_epoch))
    if pos is None:
        candidate_cache[key] = None
        return None
    lo, hi = int(starts[pos]), int(ends[pos])
    if hi <= lo:
        candidate_cache[key] = None
        return None
    local = options.iloc[lo:hi]
    dte_lo, dte_hi = DTE_BUCKETS[dte_bucket]
    mask = (
        (local["option_type"].to_numpy() == direction)
        & (local["expiry_epoch"].to_numpy(dtype=np.int64) > int(planned_exit))
        & ((local["expiry_session_idx"].to_numpy(dtype=np.int32) - int(entry_session_idx)) >= dte_lo)
        & ((local["expiry_session_idx"].to_numpy(dtype=np.int32) - int(entry_session_idx)) <= dte_hi)
        & np.isfinite(local["option_open"].to_numpy(dtype=float))
        & (local["option_open"].to_numpy(dtype=float) > 0)
    )
    if not mask.any():
        candidate_cache[key] = None
        return None
    candidate_indices = np.arange(lo, hi, dtype=np.int64)[mask]
    candidate_rows = options.iloc[candidate_indices]
    best = None
    best_key = None
    for global_idx, (_, row) in zip(candidate_indices, candidate_rows.iterrows()):
        delta, delta_method = resolve_delta(row, int(entry_epoch))
        spot = row.get("rolling_spot")
        try:
            spot = float(spot)
        except Exception:
            spot = float("nan")
        if not np.isfinite(spot) or spot <= 0:
            try:
                spot = float(row.get("nifty_close"))
            except Exception:
                spot = float("nan")
        strike = float(row["returned_strike"])
        moneyness = abs(math.log(strike / spot)) if np.isfinite(spot) and spot > 0 and strike > 0 else float("inf")
        delta_available = delta_method != "MONEYNESS_FALLBACK" and np.isfinite(delta)
        priority = 0 if delta_available else 1
        delta_error = abs(delta - float(delta_target)) if delta_available else float("inf")
        strike_distance = abs(strike - spot) if np.isfinite(spot) else float("inf")
        contract_code = int(row["contract_code"])
        sort_key = (priority, delta_error, moneyness, strike_distance, contract_code, int(global_idx))
        if best_key is None or sort_key < best_key:
            best_key, best = sort_key, int(global_idx)
    candidate_cache[key] = best
    return best


def read_forecast_events(reference_root: Path) -> tuple[dict[str, list[dict]], dict]:
    base = reference_root / "phase7_reference"
    manifest_path = base / "phase7_reference_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Run #994 manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    events_by_cell: dict[str, list[dict]] = {}
    report = {"manifest_sha256": sha256_file(manifest_path), "panels": []}
    panels = manifest.get("prediction_panels", [])
    for record in panels:
        path = base / Path(record["path"]).name
        if not path.is_file():
            raise FileNotFoundError(f"Saved forecast panel missing: {path.name}")
        layer = str(record["layer"])
        horizon = int(record["horizon"])
        if layer not in LAYERS or horizon not in LAYERS[layer]:
            continue
        panel = pd.read_parquet(path)
        report["panels"].append({
            "layer": layer, "horizon": horizon, "rows": int(len(panel)),
            "file": path.name, "sha256": sha256_file(path),
        })
        for method in METHODS:
            cell_id = f"{layer}-H{horizon}-{method}"
            cell_events = []
            for t, p in zip(panel["decision_timestamp"].tolist(), panel[method].tolist()):
                try:
                    prob = float(p)
                except Exception:
                    continue
                if not np.isfinite(prob) or prob < 0 or prob > 1:
                    continue
                direction = engine.direction_from_probability(prob, method)
                if direction is None:
                    continue
                try:
                    ts = decision_epoch(t, layer)
                except Exception:
                    continue
                cell_events.append({
                    "cell_id": cell_id, "layer": layer, "horizon": horizon,
                    "method": method, "decision_epoch": ts, "probability": prob,
                    "direction": direction,
                })
            cell_events.sort(key=lambda x: x["decision_epoch"])
            events_by_cell[cell_id] = cell_events
    report["forecast_cell_count"] = len(events_by_cell)
    report["signal_rows_total"] = int(sum(len(v) for v in events_by_cell.values()))
    return events_by_cell, report


def make_skeletons(events: list[dict], options: pd.DataFrame, sessions: list[str],
                   candidate_cache: dict, data_info: dict, delta_target: float,
                   dte_bucket: str, diagnostics: Counter) -> list[dict]:
    unique_times = data_info["unique_times"]
    starts = data_info["starts"]
    ends = data_info["ends"]
    time_position = data_info["time_position"]
    session_pos_by_timestamp = data_info["session_pos_by_timestamp"]
    skeletons = []
    for event in events:
        decision = int(event["decision_epoch"])
        entry_pos = int(np.searchsorted(unique_times, decision, side="right"))
        if decision < int(unique_times[0]) or entry_pos >= len(unique_times):
            diagnostics["NO_OVERLAPPING_OPTION_TIME"] += 1
            continue
        entry_epoch = int(unique_times[entry_pos])
        # Intraday decisions are allowed at most five minutes of source delay.
        # Daily close-to-next-session entries are naturally overnight.
        if event["layer"] == "intraday" and entry_epoch - decision > 300:
            diagnostics["ENTRY_BAR_TOO_LATE"] += 1
            continue
        planned_exit = plan_exit_epoch(decision, event["layer"], int(event["horizon"]),
                                       sessions, unique_times)
        if planned_exit is None:
            diagnostics["NO_PLANNED_EXIT_BAR"] += 1
            continue
        entry_session_idx = session_pos_by_timestamp.get(entry_epoch)
        if entry_session_idx is None:
            diagnostics["NO_ENTRY_SESSION"] += 1
            continue
        row_idx = select_contract(
            options, starts, ends, time_position, entry_epoch, int(planned_exit),
            event["direction"], float(delta_target), dte_bucket, int(entry_session_idx),
            candidate_cache,
        )
        if row_idx is None:
            diagnostics["NO_CONTRACT_FOR_DELTA_DTE"] += 1
            continue
        row = options.iloc[int(row_idx)]
        entry_base = float(row["option_open"])
        contract_code = int(row["contract_code"])
        series_idx = data_info["contract_indices"].get(contract_code)
        if series_idx is None or len(series_idx) == 0:
            diagnostics["NO_CONTRACT_SERIES"] += 1
            continue
        series_times = data_info["times"][series_idx]
        entry_series_pos = int(np.searchsorted(series_times, entry_epoch, side="left"))
        if entry_series_pos >= len(series_idx) or int(series_times[entry_series_pos]) != entry_epoch:
            diagnostics["NO_ENTRY_CONTRACT_BAR"] += 1
            continue
        scheduled_series_pos = int(np.searchsorted(series_times, int(planned_exit), side="left"))
        if scheduled_series_pos >= len(series_idx):
            diagnostics["NO_EXIT_CONTRACT_BAR"] += 1
            continue
        lot_size = lot_size_for_expiry(str(row["expiry_key"]))
        if lot_size <= 0:
            diagnostics["NO_LOT_SIZE_SCHEDULE"] += 1
            continue
        skeletons.append({
            **event,
            "decision_epoch": decision,
            "entry_epoch": entry_epoch,
            "planned_exit_epoch": int(planned_exit),
            "entry_base": entry_base,
            "contract_code": contract_code,
            "entry_row_idx": int(row_idx),
            "entry_series_pos": entry_series_pos,
            "scheduled_series_pos": scheduled_series_pos,
            "expiry_key": str(row["expiry_key"]),
            "strike": float(row["returned_strike"]),
            "option_type": str(row["option_type"]),
            "delta_used": float(abs(row["delta"])) if pd.notna(row["delta"]) else float("nan"),
            "delta_target": float(delta_target),
            "dte_bucket": dte_bucket,
            "lot_size": lot_size,
            "series_idx": series_idx,
        })
    return skeletons


def simulate_exit(skel: dict, policy: str, options: pd.DataFrame,
                  data_info: dict) -> dict | None:
    idxs = skel["series_idx"]
    entry_pos = int(skel["entry_series_pos"])
    scheduled_pos = int(skel["scheduled_series_pos"])
    if entry_pos >= len(idxs) or scheduled_pos >= len(idxs) or scheduled_pos <= entry_pos:
        return None
    option_open = data_info["option_open"]
    option_high = data_info["option_high"]
    option_low = data_info["option_low"]
    times = data_info["times"]
    entry_base = float(skel["entry_base"])
    exit_pos = scheduled_pos
    exit_base = float(option_open[idxs[scheduled_pos]])
    exit_reason = "TIME_EXIT"
    if not np.isfinite(exit_base) or exit_base < 0:
        return None
    if policy != "X0":
        trailing_high = None
        found = False
        for series_pos in range(entry_pos, scheduled_pos + 1):
            row_idx = int(idxs[series_pos])
            high = float(option_high[row_idx])
            low = float(option_low[row_idx])
            if not np.isfinite(high) or not np.isfinite(low):
                trailing_high = max(float(trailing_high or entry_base), entry_base)
                continue
            price, reason, new_high = engine.conservative_trigger_exit(
                {"high": high, "low": low}, policy, entry_base, trailing_high
            )
            trailing_high = new_high
            if reason is not None and price is not None:
                # If a stop was crossed by a gap through its level, OHLC-only
                # data cannot justify the stop price; use the lower bar open.
                bar_open = float(option_open[row_idx])
                if reason in {"STOP_LOSS", "TRAILING_STOP"} and np.isfinite(bar_open) and bar_open > 0:
                    price = min(float(price), bar_open)
                exit_pos = series_pos
                exit_base = float(price)
                exit_reason = str(reason)
                found = True
                break
        if not found:
            exit_pos = scheduled_pos
            exit_base = float(option_open[idxs[scheduled_pos]])
            exit_reason = "TIME_EXIT"
    exit_row_idx = int(idxs[exit_pos])
    if not np.isfinite(exit_base) or exit_base < 0:
        return None
    return {
        "exit_epoch": int(times[exit_row_idx]),
        "exit_base": float(exit_base),
        "exit_reason": exit_reason,
        "exit_row_idx": exit_row_idx,
    }


def build_trade(skel: dict, policy: str, exit_result: dict, options: pd.DataFrame,
                cost_schedule: dict) -> dict:
    entry_epoch = int(skel["entry_epoch"])
    exit_epoch = int(exit_result["exit_epoch"])
    entry_base = float(skel["entry_base"])
    exit_base = float(exit_result["exit_base"])
    lot_size = int(skel["lot_size"])
    entry_date = date.fromisoformat(session_date_for_epoch(entry_epoch))
    exit_date = date.fromisoformat(session_date_for_epoch(exit_epoch))
    row = {
        "config_id": f"{skel['cell_id']}-D{skel['delta_target']:.2f}-{skel['dte_bucket']}-{policy}",
        "cell_id": skel["cell_id"], "layer": skel["layer"], "horizon": int(skel["horizon"]),
        "method": skel["method"], "delta_target": float(skel["delta_target"]),
        "dte_bucket": skel["dte_bucket"], "exit_policy": policy,
        "direction": skel["direction"], "probability": float(skel["probability"]),
        "decision_timestamp_ist": session_date_for_epoch(int(skel["decision_epoch"])) + " "
            + pd.Timestamp(int(skel["decision_epoch"]), unit="s", tz="UTC").tz_convert(IST).strftime("%H:%M:%S"),
        "entry_timestamp_ist": pd.Timestamp(entry_epoch, unit="s", tz="UTC").tz_convert(IST).isoformat(),
        "exit_timestamp_ist": pd.Timestamp(exit_epoch, unit="s", tz="UTC").tz_convert(IST).isoformat(),
        "expiry_date": skel["expiry_key"], "strike": float(skel["strike"]),
        "option_type": skel["option_type"], "lot_size": lot_size,
        "entry_ohlc_open": entry_base, "exit_proxy_base": exit_base,
        "exit_reason": exit_result["exit_reason"], "gross_pnl_rupees_before_friction": (exit_base - entry_base) * lot_size,
        "entry_premium_turnover": entry_base * lot_size,
    }
    for scenario in SCENARIOS:
        entry_fill = engine.fill_price(
            entry_base, "BUY", pd.Timestamp(entry_epoch, unit="s", tz="UTC"),
            "Q1", scenario, TICK_SIZE,
        )
        exit_fill = engine.fill_price(
            exit_base, "SELL", pd.Timestamp(exit_epoch, unit="s", tz="UTC"),
            "Q1", scenario, TICK_SIZE,
        )
        fees = engine.compute_round_trip_costs(
            entry_fill.price, exit_fill.price, lot_size, entry_date, scenario,
            brokerage_status="BROKERAGE_FALLBACK", schedule=cost_schedule,
            exit_trade_date=exit_date,
        )
        net = (exit_fill.price - entry_fill.price) * lot_size - fees.total
        basis = max(entry_base * lot_size, 1e-9)
        row[f"{scenario}_entry_fill"] = entry_fill.price
        row[f"{scenario}_exit_fill"] = exit_fill.price
        row[f"{scenario}_brokerage_taxes_fees"] = fees.total
        row[f"{scenario}_spread_slippage_rupees"] = (
            (entry_fill.price - entry_base) + (exit_base - exit_fill.price)
        ) * lot_size
        row[f"{scenario}_net_pnl_rupees"] = net
        row[f"{scenario}_net_return_pct"] = 100.0 * net / basis
    return row


def summarise_trades(trades: pd.DataFrame, grid: list[dict]) -> pd.DataFrame:
    if trades.empty:
        trade_groups = {}
    else:
        trade_groups = {str(key): group.sort_values("exit_timestamp_ist", kind="mergesort")
                        for key, group in trades.groupby("config_id", sort=False)}
    rows = []
    for config in grid:
        config_id = config["config_id"]
        group = trade_groups.get(config_id)
        for scenario in SCENARIOS:
            row = {
                **config, "scenario": scenario,
                "execution_quality": "Q1_OHLC_PROXY",
                "quote_executable": False,
            }
            if group is None or group.empty:
                row.update({
                    "status": "NO_TRADES", "trade_count": 0, "win_count": 0, "loss_count": 0,
                    "breakeven_count": 0, "win_rate_pct": float("nan"), "loss_rate_pct": float("nan"),
                    "total_net_pnl_rupees": 0.0, "average_net_pnl_rupees": float("nan"),
                    "average_return_pct": float("nan"), "median_return_pct": float("nan"),
                    "average_winner_rupees": float("nan"), "average_loser_rupees": float("nan"),
                    "profit_factor": float("nan"), "max_drawdown_rupees": float("nan"),
                    "max_drawdown_pct_of_peak_equity": float("nan"),
                    "max_drawdown_peak_timestamp": "", "max_drawdown_trough_timestamp": "",
                    "p_value_iid_screen": float("nan"),
                })
                rows.append(row)
                continue
            pnl = group[f"{scenario}_net_pnl_rupees"].to_numpy(dtype=float)
            returns = group[f"{scenario}_net_return_pct"].to_numpy(dtype=float)
            wins = pnl > 0
            losses = pnl < 0
            gross_win = float(pnl[wins].sum()) if wins.any() else 0.0
            gross_loss = float(-pnl[losses].sum()) if losses.any() else 0.0
            equity = np.cumsum(pnl)
            peaks = np.maximum.accumulate(np.r_[0.0, equity])[1:]
            dd = peaks - equity
            dd_idx = int(np.argmax(dd)) if len(dd) else 0
            max_dd = float(dd[dd_idx]) if len(dd) else 0.0
            peak_idx = int(np.argmax(np.r_[0.0, equity[:dd_idx + 1]]))
            peak_time = "" if peak_idx == 0 else str(group.iloc[min(peak_idx - 1, len(group)-1)]["exit_timestamp_ist"])
            trough_time = str(group.iloc[dd_idx]["exit_timestamp_ist"]) if len(group) else ""
            try:
                pvalue = float(ttest_1samp(returns, popmean=0.0, nan_policy="omit").pvalue) if len(returns) >= 2 else float("nan")
            except Exception:
                pvalue = float("nan")
            row.update({
                "status": "SCREENING_RESULT",
                "trade_count": int(len(pnl)),
                "win_count": int(wins.sum()), "loss_count": int(losses.sum()),
                "breakeven_count": int((pnl == 0).sum()),
                "win_rate_pct": float(wins.mean() * 100.0),
                "loss_rate_pct": float(losses.mean() * 100.0),
                "total_net_pnl_rupees": float(pnl.sum()),
                "average_net_pnl_rupees": float(np.mean(pnl)),
                "average_return_pct": float(np.mean(returns)),
                "median_return_pct": float(np.median(returns)),
                "average_winner_rupees": float(pnl[wins].mean()) if wins.any() else float("nan"),
                "average_loser_rupees": float(pnl[losses].mean()) if losses.any() else float("nan"),
                "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else (float("inf") if gross_win > 0 else float("nan")),
                "max_drawdown_rupees": max_dd,
                "max_drawdown_pct_of_peak_equity": float(100.0 * max_dd / max(1e-9, float(peaks.max()))) if len(peaks) and peaks.max() > 0 else float("nan"),
                "max_drawdown_peak_timestamp": peak_time,
                "max_drawdown_trough_timestamp": trough_time,
                "p_value_iid_screen": pvalue,
            })
            rows.append(row)
    summary = pd.DataFrame(rows)
    p = summary["p_value_iid_screen"].to_numpy(dtype=float)
    valid = np.isfinite(p)
    q = np.full(len(p), np.nan, dtype=float)
    if valid.any():
        ids = np.where(valid)[0]
        order = ids[np.argsort(p[valid])]
        ranks = np.arange(1, len(order) + 1, dtype=float)
        raw = p[order] * len(order) / ranks
        adjusted = np.minimum.accumulate(raw[::-1])[::-1]
        q[order] = np.minimum(adjusted, 1.0)
    summary["q_value_bh_screen"] = q
    summary["statistical_note"] = (
        "IID t-test and BH adjustment are screening diagnostics only; dependence across "
        "time/configurations means they are not confirmatory significance claims."
    )
    return summary


def build_grid() -> list[dict]:
    grid = []
    for layer, horizons in LAYERS.items():
        for horizon in horizons:
            for method in METHODS:
                cell_id = f"{layer}-H{horizon}-{method}"
                for delta in DELTA_TARGETS:
                    for dte_bucket in DTE_BUCKETS:
                        for policy in EXIT_POLICIES:
                            grid.append({
                                "cell_id": cell_id, "layer": layer, "horizon": horizon,
                                "method": method, "delta_target": delta,
                                "dte_bucket": dte_bucket, "exit_policy": policy,
                                "config_id": f"{cell_id}-D{delta:.2f}-{dte_bucket}-{policy}",
                            })
    if len(grid) != EXPECTED_GRID or len({x["config_id"] for x in grid}) != EXPECTED_GRID:
        raise AssertionError("frozen 4,800-cell strategy grid is incomplete or duplicated")
    return grid


def self_test() -> dict:
    assert engine.direction_from_probability(0.50, "P01") is None
    assert engine.direction_from_probability(0.5001, "P01") == "CE"
    assert engine.direction_from_probability(0.4499, "P10") == "PE"
    assert engine.direction_from_probability(0.45, "P10") is None
    assert engine.direction_from_probability(0.5501, "P10") == "CE"
    assert lot_size_for_expiry("2023-12-28") == 50
    assert lot_size_for_expiry("2024-05-02") == 25
    assert lot_size_for_expiry("2024-11-26") == 75
    assert lot_size_for_expiry("2026-01-06") == 65
    assert len(build_grid()) == 4800
    assert abs(engine.proxy_spread_component(100.0, TICK_SIZE, "C1") - 1.0) < 1e-12
    return {
        "status": "PASS", "execution_quality": "Q1_OHLC_PROXY",
        "forecast_refit": False, "bid_ask_required": False,
        "registered_configs": 4800, "scenario_count": 4,
        "summary_rows_expected": 19200,
        "manual_run_available": True,
    }


def run_proxy(reference_root: Path, parts_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    options, sessions, load_diagnostics = load_option_data(parts_dir)
    unique_times = options.attrs["unique_times"]
    starts = options.attrs["starts"]
    ends = options.attrs["ends"]
    contract_indices = {
        int(code): np.asarray(indices, dtype=np.int64)
        for code, indices in options.groupby("contract_code", sort=False).indices.items()
    }
    times = options["timestamp_epoch"].to_numpy(dtype=np.int64)
    data_info = {
        "unique_times": unique_times, "starts": starts, "ends": ends,
        "time_position": {int(t): i for i, t in enumerate(unique_times)},
        "times": times,
        "option_open": options["option_open"].to_numpy(dtype=float),
        "option_high": options["option_high"].to_numpy(dtype=float),
        "option_low": options["option_low"].to_numpy(dtype=float),
        "session_pos_by_timestamp": {},
        "contract_indices": contract_indices,
    }
    local_dates = pd.to_datetime(unique_times, unit="s", utc=True).tz_convert(IST).strftime("%Y-%m-%d")
    sessions_arr = np.asarray(sessions, dtype=object)
    session_idx = np.searchsorted(sessions_arr, np.asarray(local_dates, dtype=object), side="left")
    data_info["session_pos_by_timestamp"] = {
        int(t): int(idx) for t, idx in zip(unique_times, session_idx)
    }
    events_by_cell, forecast_report = read_forecast_events(reference_root)
    cost_schedule = engine.load_cost_schedule(ROOT / "data" / "reference" / "phase8_cost_schedule.json")
    grid = build_grid()
    diagnostics = Counter()
    candidate_cache = {}
    trades = []
    for cell_id, events in events_by_cell.items():
        for delta_target in DELTA_TARGETS:
            for dte_bucket in DTE_BUCKETS:
                skeletons = make_skeletons(
                    events, options, sessions, candidate_cache, data_info,
                    float(delta_target), dte_bucket, diagnostics,
                )
                for policy in EXIT_POLICIES:
                    last_exit = None
                    for skel in skeletons:
                        signal = int(skel["decision_epoch"])
                        if last_exit is not None and signal < int(last_exit):
                            diagnostics["OVERLAP_SKIPPED"] += 1
                            continue
                        result = simulate_exit(skel, policy, options, data_info)
                        if result is None:
                            diagnostics["NO_EXIT_PRICE"] += 1
                            continue
                        trade = build_trade(skel, policy, result, options, cost_schedule)
                        trades.append(trade)
                        last_exit = int(result["exit_epoch"])
    trade_df = pd.DataFrame(trades)
    summary = summarise_trades(trade_df, grid)
    # Preserve all configuration/scenario summaries; the ledger is a proxy-result
    # output and does not include raw source rows.
    summary_path = output_dir / "phase8_proxy_strategy_summary.csv"
    summary.to_csv(summary_path, index=False, quoting=csv.QUOTE_MINIMAL)
    ledger_path = output_dir / "phase8_proxy_trade_ledger.csv.gz"
    trade_df.to_csv(ledger_path, index=False, compression="gzip")
    c3 = summary[summary["scenario"] == "C3"].copy()
    eligible = c3[(c3["trade_count"] >= 30) & (c3["total_net_pnl_rupees"] > 0)].copy()
    eligible.sort_values(
        ["total_net_pnl_rupees", "average_return_pct", "trade_count"],
        ascending=[False, False, False], kind="mergesort", inplace=True,
    )
    top = eligible.head(50)
    top_path = output_dir / "phase8_proxy_top_50_worst_cost_scenario.csv"
    top.to_csv(top_path, index=False)
    top_ids = set(top["config_id"].astype(str).tolist())
    yearly_rows = []
    if not trade_df.empty and top_ids:
        top_trades = trade_df[trade_df["config_id"].astype(str).isin(top_ids)].copy()
        top_trades["exit_year"] = top_trades["exit_timestamp_ist"].astype(str).str.slice(0, 4)
        for (config_id, year), group in top_trades.groupby(["config_id", "exit_year"], sort=True):
            for scenario in SCENARIOS:
                pnl = group[f"{scenario}_net_pnl_rupees"].to_numpy(dtype=float)
                yearly_rows.append({
                    "config_id": config_id, "exit_year": year, "scenario": scenario,
                    "trade_count": int(len(pnl)), "net_pnl_rupees": float(pnl.sum()),
                    "win_rate_pct": float((pnl > 0).mean() * 100.0) if len(pnl) else float("nan"),
                    "average_pnl_rupees": float(pnl.mean()) if len(pnl) else float("nan"),
                })
    yearly_path = output_dir / "phase8_proxy_top_50_yearly.csv"
    pd.DataFrame(yearly_rows).to_csv(yearly_path, index=False)
    top_json = [
        {
            "config_id": str(row["config_id"]), "method": str(row["method"]),
            "layer": str(row["layer"]), "horizon": int(row["horizon"]),
            "delta_target": float(row["delta_target"]), "dte_bucket": str(row["dte_bucket"]),
            "exit_policy": str(row["exit_policy"]), "trades": int(row["trade_count"]),
            "net_pnl_c3_rupees": float(row["total_net_pnl_rupees"]),
            "win_rate_c3_pct": float(row["win_rate_pct"]),
            "mean_return_c3_pct": float(row["average_return_pct"]),
            "q_value_screen": None if not np.isfinite(row["q_value_bh_screen"]) else float(row["q_value_bh_screen"]),
        }
        for _, row in top.iterrows()
    ]
    report = {
        "schema_version": 1,
        "status": "COMPLETE_PROXY_BACKTEST" if not trade_df.empty else "NO_ELIGIBLE_TRADES",
        "execution_quality": "Q1_OHLC_PROXY",
        "bid_ask_required": False,
        "quote_executable": False,
        "forecast_refitted": False,
        "source_data_acquired_new": False,
        "user_instruction": "Proceed with available OHLC data; no bid/ask prerequisite.",
        "frozen_forecast": {
            "phase7_run": 994,
            "artifact_id": 11638738288,
            "artifact_sha256": "3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9",
            "panel_count": forecast_report["forecast_cell_count"] // len(METHODS),
            "forecast_cell_count": forecast_report["forecast_cell_count"],
            "saved_signal_count": forecast_report["signal_rows_total"],
            "manifest_sha256": forecast_report["manifest_sha256"],
        },
        "input_coverage": {
            **load_diagnostics,
            "forecast_panels": forecast_report["panels"],
            "first_option_timestamp_ist": pd.Timestamp(int(unique_times[0]), unit="s", tz="UTC").tz_convert(IST).isoformat(),
            "last_option_timestamp_ist": pd.Timestamp(int(unique_times[-1]), unit="s", tz="UTC").tz_convert(IST).isoformat(),
        },
        "grid": {"registered_configs": len(grid), "cost_scenarios": list(SCENARIOS), "summary_rows": len(summary)},
        "costs": {
            "brokerage_model": "Paytm Money historical unverified fallback: INR 20 per executed order; INR 40 round trip",
            "fees": "Date-effective STT, exchange transaction charges, IPFT, SEBI fee, stamp duty and GST from frozen phase8_cost_schedule.json",
            "proxy_spread_by_scenario": engine.PROXY_SPREAD,
            "incremental_slippage_by_scenario": engine.INCREMENTAL_SLIPPAGE,
            "tick_size_rupees": TICK_SIZE,
            "lot_size_schedule": {
                "expiry_before_2024-05-02": 50,
                "expiry_2024-05-02_to_2024-11-25": 25,
                "expiry_2024-11-26_to_2026-01-05": 75,
                "expiry_from_2026-01-06": 65,
            },
            "lot_size_limitation": (
                "These are expiry-date-based lot-size proxies. Some contracts created before a "
                "lot-size transition can expire after it, so without a historical listed-contract "
                "master the absolute INR P&L and costs can be mis-scaled for transition-month "
                "contracts. Results remain exploratory."
            ),
        },
        "trade_count": int(len(trade_df)),
        "configurations_with_30_plus_trades_positive_c3": int(len(eligible)),
        "top_50_worst_cost_scenario": top_json,
        "diagnostic_counts": dict(diagnostics),
        "outputs": {
            "summary_csv": summary_path.name,
            "trade_ledger_gzip_csv": ledger_path.name,
            "top_50_csv": top_path.name,
            "top_50_yearly_csv": yearly_path.name,
        },
        "interpretation": (
            "These are OHLC proxy results. Entries use the first observed option bar strictly "
            "after the saved forecast decision. Exits use the frozen scheduled horizon or "
            "X1/X2/X3 trigger logic, with synthetic spread/slippage and date-effective fees. "
            "Ranking is exploratory; IID t-tests and BH values do not establish predictive or "
            "trading significance, and the highest historical result is not automatically promoted."
        ),
        "strategy_promotion_authorized": False,
    }
    report_path = output_dir / "phase8_proxy_strategy_run_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Phase 8 OHLC proxy option strategy backtest.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--forecast-root", type=Path, default=Path("data/cache/reference/phase7_run994/unpacked"))
    parser.add_argument("--parts-dir", type=Path, default=Path("data/cache/phase8/decrypted-parts"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/phase8/proxy_strategy"))
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return 0
    try:
        report = run_proxy(args.forecast_root, args.parts_dir, args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=True))
        return 0
    except Exception as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "phase8_proxy_strategy_error.log").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
