#!/usr/bin/env python3
"""Collect, normalize and encrypt the five-year NIFTY one-minute composite.

The public repository must never contain plaintext subscribed market observations.
Only encrypted raw response cache objects and encrypted CSV parts may persist in
Actions cache/artifacts. The HF_TOKEN secret is used as a local key-derivation
secret; it is never sent to Dhan, logged, or persisted.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import heapq
import json
import math
import os
import pathlib
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any, Iterable
from zoneinfo import ZoneInfo

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
except ImportError as exc:
    raise SystemExit("cryptography_required_install_requirements_composite_txt") from exc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT_MANIFEST = ROOT / "research/gates/NIFTY_1M_COMPOSITE_REQUEST_MANIFEST.json"
CACHE_ROOT = ROOT / "data/cache/nifty_1m_composite/raw"
WORK_ROOT = ROOT / "data/work/nifty_1m_composite"
EXPORT_ROOT = ROOT / "data/exports/nifty_1m_composite"
PLAIN_ROOT = EXPORT_ROOT / "plain"
ENCRYPTED_ROOT = EXPORT_ROOT / "encrypted"
REPORTS_ROOT = ROOT / "data/reports/nifty_1m_composite"
IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc
MAGIC = b"N1C1"
AAD = b"Naked-option-v1:NIFTY-1m-composite:v1"
KEY_SALT = b"Naked-option-v1-HF-TOKEN-DERIVATION-v1"
USER_AGENT = "Naked-option-v1-research-composite/1.0"
TIMEOUT_SECONDS = 35
MIN_REQUEST_INTERVAL_SECONDS = 0.5

COLUMNS = [
    "timestamp_epoch", "row_type", "timestamp_utc", "timestamp_ist", "session_date",
    "underlying", "expiry_flag", "expiry_code", "requested_relative_strike",
    "returned_strike", "option_type",
    "option_open", "option_high", "option_low", "option_close",
    "option_volume", "open_interest", "implied_volatility",
    "rolling_spot",
    "nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume",
    "spot_join_status",
    "source_provider", "source_endpoint", "source_request_id",
    "request_scope_sha256", "response_sha256", "cache_status",
    "expiry_date", "expiry_mapping_source", "time_to_expiry_years", "risk_free_rate_decimal",
    "risk_free_rate_source", "dividend_yield_decimal", "dividend_yield_source", "greek_assumption", "delta", "gamma", "theta_per_day",
    "vega_per_1pct_iv", "rho_per_1pct_rate", "greek_model", "greek_status",
    "data_quality_flags",
]


class SourceRequestError(RuntimeError):
    def __init__(self, reason: str, http_status: int | None = None):
        super().__init__(reason)
        self.reason = reason
        self.http_status = http_status


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now() -> str:
    return dt.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(obj: Any) -> str:
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(encoded)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("json_top_level_object_required")
    return obj


def derive_key(secret: str) -> bytes:
    if not isinstance(secret, str) or len(secret.strip()) < 16:
        raise ValueError("HF_TOKEN_missing_or_too_short_for_encryption_key")
    return Scrypt(salt=KEY_SALT, length=32, n=2**14, r=8, p=1).derive(secret.encode("utf-8"))


def encrypt_bytes(plaintext: bytes, key: bytes, nonce: bytes | None = None) -> bytes:
    nonce = nonce or os.urandom(12)
    return MAGIC + nonce + AESGCM(key).encrypt(nonce, plaintext, AAD)


def decrypt_bytes(ciphertext: bytes, key: bytes) -> bytes:
    if len(ciphertext) < len(MAGIC) + 12 + 16 or not ciphertext.startswith(MAGIC):
        raise ValueError("encrypted_payload_header_invalid")
    nonce = ciphertext[len(MAGIC):len(MAGIC) + 12]
    payload = ciphertext[len(MAGIC) + 12:]
    try:
        return AESGCM(key).decrypt(nonce, payload, AAD)
    except Exception:
        raise ValueError("encrypted_payload_authentication_failed") from None


def atomic_write(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_requests(root: dict[str, Any]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for entry in root.get("request_manifests", []):
        path = ROOT / str(entry.get("path", ""))
        obj = load_json(path)
        rows = obj.get("requests")
        if not isinstance(rows, list) or len(rows) != entry.get("request_count"):
            raise ValueError("request_submanifest_count_mismatch")
        requests.extend(rows)
    requests.sort(key=lambda r: (
        r.get("window_start_inclusive", ""),
        r.get("source_family") != "NIFTY_SPOT_1M",
        r.get("request_id", ""),
    ))
    return requests


def request_scope(request: dict[str, Any]) -> dict[str, Any]:
    return {"endpoint": request["endpoint"], "method": request["method"], "body": request["body"]}


def request_scope_hash(request: dict[str, Any]) -> str:
    return canonical_sha256(request_scope(request))


def safe_cache_paths(request_id: str) -> tuple[pathlib.Path, pathlib.Path]:
    if not request_id or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for ch in request_id):
        raise ValueError("unsafe_request_id")
    return CACHE_ROOT / (request_id + ".json.enc"), CACHE_ROOT / (request_id + ".meta.json")


def parse_json_numbers(raw: bytes) -> dict[str, Any]:
    try:
        obj = json.loads(raw.decode("utf-8"), parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError("response_invalid_json") from None
    if not isinstance(obj, dict):
        raise ValueError("response_json_not_object")
    code = obj.get("errorCode")
    if code is not None:
        code_text = str(code)
        if code_text in {"806", "807", "808", "809", "810"}:
            raise SourceRequestError("dhan_api_auth_or_entitlement_error_" + code_text, 200)
        raise SourceRequestError("dhan_api_error_code_" + code_text, 200)
    if obj.get("status") == "error" or obj.get("error"):
        raise SourceRequestError("dhan_api_error_payload", 200)
    return obj


def _array_set(obj: dict[str, Any], fields: list[str]) -> tuple[list[int], dict[str, list[Any]]]:
    arrays: dict[str, list[Any]] = {}
    lengths = set()
    for field in fields:
        value = obj.get(field)
        if not isinstance(value, list):
            raise ValueError("response_field_not_array_" + field)
        arrays[field] = value
        lengths.add(len(value))
    if len(lengths) != 1:
        raise ValueError("response_field_array_length_mismatch")
    timestamps = arrays["timestamp"]
    if any(isinstance(ts, bool) or not isinstance(ts, int) for ts in timestamps):
        raise ValueError("response_timestamp_not_integer_epoch")
    return timestamps, arrays


def _value_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (int, float, str)) and not isinstance(value, bool):
        return str(value)
    return ""


def _nullable_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    return number


def parse_spot_response(payload: dict[str, Any], request: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    timestamps, arrays = _array_set(payload, ["timestamp", "open", "high", "low", "close", "volume"])
    if len(timestamps) > int(request.get("max_rows", 0)):
        raise ValueError("response_row_cap_exceeded")
    start_date = dt.date.fromisoformat(request["window_start_inclusive"])
    end_date = dt.date.fromisoformat(request["window_end_exclusive"])
    from_time = dt.time.fromisoformat(request["body"]["fromDate"].split(" ", 1)[1])
    to_time = dt.time.fromisoformat(request["body"]["toDate"].split(" ", 1)[1])
    rows = []
    problems = []
    seen = set()
    for i, epoch in sorted(enumerate(timestamps), key=lambda it: (it[1], it[0])):
        ist = dt.datetime.fromtimestamp(epoch, tz=UTC).astimezone(IST)
        if not (start_date <= ist.date() < end_date):
            raise ValueError("spot_timestamp_outside_requested_calendar_window")
        if ist.date() == start_date and ist.time().replace(tzinfo=None) < from_time:
            raise ValueError("spot_timestamp_before_requested_start_time")
        if ist.date() == dt.date.fromisoformat(request["window_end_exclusive"]) - dt.timedelta(days=1) and ist.time().replace(tzinfo=None) > to_time:
            raise ValueError("spot_timestamp_after_requested_end_time")
        flags = []
        if epoch in seen:
            flags.append("DUPLICATE_TIMESTAMP_IN_PROVIDER_RESPONSE")
            problems.append("duplicate_timestamp")
        seen.add(epoch)
        row = {
            "timestamp_epoch": str(epoch),
            "row_type": "SPOT",
            "timestamp_utc": dt.datetime.fromtimestamp(epoch, tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "timestamp_ist": ist.isoformat(timespec="seconds"),
            "session_date": ist.date().isoformat(),
            "underlying": "NIFTY",
            "expiry_flag": "", "expiry_code": "", "requested_relative_strike": "",
            "returned_strike": "", "option_type": "",
            "option_open": "", "option_high": "", "option_low": "", "option_close": "",
            "option_volume": "", "open_interest": "", "implied_volatility": "",
            "rolling_spot": "",
            "nifty_open": _value_string(arrays["open"][i]),
            "nifty_high": _value_string(arrays["high"][i]),
            "nifty_low": _value_string(arrays["low"][i]),
            "nifty_close": _value_string(arrays["close"][i]),
            "nifty_volume": _value_string(arrays["volume"][i]),
            "spot_join_status": "SPOT_SOURCE_ROW",
            "source_provider": "DhanHQ",
            "source_endpoint": request["endpoint"],
            "source_request_id": request["request_id"],
            "request_scope_sha256": request_scope_hash(request),
            "response_sha256": "",
            "cache_status": "",
            "expiry_date": "", "expiry_mapping_source": "", "time_to_expiry_years": "",
            "risk_free_rate_decimal": "", "risk_free_rate_source": "", "dividend_yield_decimal": "", "dividend_yield_source": "", "greek_assumption": "",
            "delta": "", "gamma": "", "theta_per_day": "",
            "vega_per_1pct_iv": "", "rho_per_1pct_rate": "",
            "greek_model": "Black-Scholes-European-v1",
            "greek_status": "NOT_APPLICABLE_SPOT_ROW",
            "data_quality_flags": "|".join(flags),
        }
        rows.append(row)
    return rows, problems


def load_greek_inputs() -> tuple[dict[tuple[str, str, int], dict[str, str]], list[tuple[dt.datetime, float, str, str]], list[str]]:
    calendar_path = ROOT / "data/reference/NIFTY_EXPIRY_CALENDAR.csv"
    rates_path = ROOT / "data/reference/INDIA_RISK_FREE_RATES.csv"
    expiry: dict[tuple[str, str, int], dict[str, str]] = {}
    rates: list[tuple[dt.datetime, float, str, str]] = []
    missing = []
    if not calendar_path.exists():
        missing.append("expiry_calendar_missing")
    else:
        with calendar_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                try:
                    key = (row["session_date"], row["expiry_flag"], int(row["expiry_code"]))
                    exp_date = dt.date.fromisoformat(row["expiry_date"]).isoformat()
                    expiry[key] = {"expiry_date": exp_date, "dividend_yield_decimal": row.get("dividend_yield_decimal", "")}
                except (KeyError, ValueError):
                    continue
    if not rates_path.exists():
        missing.append("risk_free_rate_history_missing")
    else:
        with rates_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                try:
                    available = dt.datetime.fromisoformat(row["available_at_utc"].replace("Z", "+00:00")).astimezone(UTC)
                    rate = float(row["rate_decimal"])
                    if math.isfinite(rate):
                        rates.append((available, rate, row.get("source_id", ""), row.get("source_sha256", "")))
                except (KeyError, ValueError, TypeError):
                    continue
        rates.sort(key=lambda item: item[0])
    return expiry, rates, missing



def _last_weekday(year: int, month: int, weekday: int) -> dt.date:
    if month == 12:
        next_month = dt.date(year + 1, 1, 1)
    else:
        next_month = dt.date(year, month + 1, 1)
    day = next_month - dt.timedelta(days=1)
    while day.weekday() != weekday:
        day -= dt.timedelta(days=1)
    return day


def build_rule_expiry_map(
    session_dates: set[str],
    external_expiry_map: dict[tuple[str, str, int], dict[str, str]],
    session_calendar_complete: bool,
) -> dict[tuple[str, str, int], dict[str, str]]:
    """Best-effort expiry map; explicit source/assumption labels travel with every row.

    Policy used: Thursday expiry dates through 2025-08-28, Tuesday expiry dates
    from 2025-09-02, with holiday adjustments to the previous observed Dhan spot
    session where available. This is a rule-derived research fallback, not a
    historical contract-master archive. Exact user-supplied dated mappings override it.
    """
    combined = dict(external_expiry_map)
    if not session_dates:
        return combined
    sessions = sorted(dt.date.fromisoformat(value) for value in session_dates)
    session_set = set(sessions)
    first = sessions[0]
    last = sessions[-1]
    start = first - dt.timedelta(days=45)
    end = last + dt.timedelta(days=75)
    last_thursday = dt.date(2025, 8, 28)
    first_tuesday = dt.date(2025, 9, 2)
    weekly_candidates: list[dt.date] = []
    cursor = start
    while cursor <= end:
        if cursor.weekday() == 3 and cursor <= last_thursday:
            weekly_candidates.append(cursor)
        elif cursor.weekday() == 1 and cursor >= first_tuesday:
            weekly_candidates.append(cursor)
        cursor += dt.timedelta(days=1)

    monthly_candidates: list[dt.date] = []
    month_cursor = dt.date(first.year, first.month, 1)
    if month_cursor.month == 1:
        month_cursor = dt.date(month_cursor.year - 1, 12, 1)
    else:
        month_cursor = dt.date(month_cursor.year, month_cursor.month - 1, 1)
    final_month = dt.date(end.year, end.month, 1)
    while month_cursor <= final_month:
        last_day = _last_weekday(month_cursor.year, month_cursor.month,
                                 3 if month_cursor < dt.date(2025, 9, 1) else 1)
        monthly_candidates.append(last_day)
        if month_cursor.month == 12:
            month_cursor = dt.date(month_cursor.year + 1, 1, 1)
        else:
            month_cursor = dt.date(month_cursor.year, month_cursor.month + 1, 1)

    def adjust_expiry(candidate: dt.date) -> dt.date:
        if candidate in session_set:
            return candidate
        if candidate <= last:
            previous = [session for session in sessions if session < candidate]
            if previous:
                return previous[-1]
        # We have no spot-session observations beyond the acquisition boundary.
        # Keep the calendar-rule date and tag the rule source rather than inventing
        # a future holiday adjustment.
        return candidate

    weekly = sorted(set(adjust_expiry(value) for value in weekly_candidates))
    monthly = sorted(set(adjust_expiry(value) for value in monthly_candidates))
    source = "RULE_DERIVED_NIFTY_EXPIRY_WEEKDAY_POLICY_V1"
    if not session_calendar_complete:
        source += "_PARTIAL_SPOT_SESSION_CALENDAR"
    elif end > last:
        source += "_FUTURE_HOLIDAY_ADJUSTMENT_NOT_OBSERVED"
    for session_text in session_dates:
        session = dt.date.fromisoformat(session_text)
        for flag, dates in (("WEEK", weekly), ("MONTH", monthly)):
            available = [value for value in dates if value >= session]
            for code in (0, 1, 2):
                key = (session_text, flag, code)
                if key in combined:
                    continue
                if len(available) <= code:
                    continue
                expiry = available[code]
                combined[key] = {
                    "expiry_date": expiry.isoformat(),
                    "dividend_yield_decimal": "",
                    "expiry_mapping_source": source,
                    "dividend_yield_source": "",
                }
    return combined


def get_asof_rate(timestamp_utc: dt.datetime, rates: list[tuple[dt.datetime, float, str, str]]) -> tuple[float | None, str]:
    available = [item for item in rates if item[0] <= timestamp_utc]
    if not available:
        return None, ""
    item = available[-1]
    return item[1], item[2]


def _norm_iv(value: Any) -> float | None:
    iv = _nullable_number(value)
    if iv is None or iv <= 0 or iv > 300:
        return None
    # Versioned heuristic because the Dhan docs do not state the numeric unit.
    result = iv / 100.0 if iv > 3.0 else iv
    return result if 0 < result <= 3.0 else None


def _cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_greeks(spot: float, strike: float, years: float, iv_decimal: float,
                         rate_decimal: float, dividend_yield_decimal: float,
                         option_type: str) -> dict[str, float] | None:
    if (spot <= 0 or strike <= 0 or years <= 0 or iv_decimal <= 0
            or not all(math.isfinite(x) for x in (spot, strike, years, iv_decimal, rate_decimal, dividend_yield_decimal))
            or option_type not in ("CALL", "PUT")):
        return None
    sigma_sqrt_t = iv_decimal * math.sqrt(years)
    if sigma_sqrt_t <= 0:
        return None
    d1 = (math.log(spot / strike) + (rate_decimal - dividend_yield_decimal + 0.5 * iv_decimal**2) * years) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    density = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    discount_q = math.exp(-dividend_yield_decimal * years)
    discount_r = math.exp(-rate_decimal * years)
    if option_type == "CALL":
        delta = discount_q * _cdf(d1)
        theta_year = (-spot * discount_q * density * iv_decimal / (2 * math.sqrt(years))
                      - rate_decimal * strike * discount_r * _cdf(d2)
                      + dividend_yield_decimal * spot * discount_q * _cdf(d1))
        rho_pct = strike * years * discount_r * _cdf(d2) * 0.01
    else:
        delta = discount_q * (_cdf(d1) - 1.0)
        theta_year = (-spot * discount_q * density * iv_decimal / (2 * math.sqrt(years))
                      + rate_decimal * strike * discount_r * _cdf(-d2)
                      - dividend_yield_decimal * spot * discount_q * _cdf(-d1))
        rho_pct = -strike * years * discount_r * _cdf(-d2) * 0.01
    gamma = discount_q * density / (spot * sigma_sqrt_t)
    vega_pct = spot * discount_q * density * math.sqrt(years) * 0.01
    greeks = {
        "delta": delta, "gamma": gamma, "theta_per_day": theta_year / 365.0,
        "vega_per_1pct_iv": vega_pct, "rho_per_1pct_rate": rho_pct,
    }
    if not all(math.isfinite(x) for x in greeks.values()):
        return None
    return greeks


def apply_greeks(row: dict[str, str], expiry_map: dict[tuple[str, str, int], dict[str, str]],
                 rates: list[tuple[dt.datetime, float, str, str]]) -> None:
    row["greek_model"] = "Black-Scholes-European-v1"
    if row["row_type"] != "OPTION":
        row["greek_status"] = "NOT_APPLICABLE_SPOT_ROW"
        return
    key = (row["session_date"], row["expiry_flag"], int(row["expiry_code"]))
    exp_info = expiry_map.get(key)
    if exp_info is None:
        row["greek_status"] = "EXPIRY_MAPPING_UNAVAILABLE"
        return
    expiry_date = exp_info.get("expiry_date", "")
    if not expiry_date:
        row["greek_status"] = "EXPIRY_DATE_MISSING"
        return
    row["expiry_date"] = expiry_date
    row["expiry_mapping_source"] = exp_info.get("expiry_mapping_source", "UNSPECIFIED_EXPIRY_SOURCE")
    try:
        expiry_dt = dt.datetime.combine(dt.date.fromisoformat(expiry_date), dt.time(15, 30), tzinfo=IST)
    except ValueError:
        row["greek_status"] = "EXPIRY_DATE_INVALID"
        return
    decision_dt = dt.datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00"))
    years = (expiry_dt.astimezone(UTC) - decision_dt).total_seconds() / (365.0 * 86400.0)
    row["time_to_expiry_years"] = _value_string(years)
    if years <= 0:
        row["greek_status"] = "EXPIRY_REACHED_OR_PASSED"
        return
    rate, rate_source = get_asof_rate(decision_dt, rates)
    if rate is None:
        rate = 0.0
        rate_source = "ASSUMED_ZERO_RATE_PROXY"
    dividend = _nullable_number(exp_info.get("dividend_yield_decimal", ""))
    if dividend is None:
        dividend = 0.0
        dividend_source = "ASSUMED_ZERO_DIVIDEND_PROXY"
    else:
        dividend_source = exp_info.get("dividend_yield_source", "EXPIRY_TABLE_DIVIDEND_INPUT")
    spot = _nullable_number(row.get("rolling_spot"))
    strike = _nullable_number(row.get("returned_strike"))
    iv = _norm_iv(row.get("implied_volatility"))
    if spot is None or strike is None or spot <= 0 or strike <= 0:
        row["greek_status"] = "SPOT_OR_STRIKE_UNAVAILABLE"
        return
    if iv is None:
        row["greek_status"] = "IV_MISSING_OR_UNIT_OUT_OF_RANGE"
        return
    greeks = black_scholes_greeks(spot, strike, years, iv, rate, dividend, row["option_type"])
    if greeks is None:
        row["greek_status"] = "GREEK_MODEL_INPUT_INVALID"
        return
    row["risk_free_rate_decimal"] = _value_string(rate)
    row["risk_free_rate_source"] = rate_source
    row["dividend_yield_decimal"] = _value_string(dividend)
    row["dividend_yield_source"] = dividend_source
    assumptions = []
    if rate_source == "ASSUMED_ZERO_RATE_PROXY":
        assumptions.append("r=0 proxy; no point-in-time historical India yield series was available")
    if dividend_source == "ASSUMED_ZERO_DIVIDEND_PROXY":
        assumptions.append("q=0 proxy; no point-in-time NIFTY dividend-yield input was available")
    if row["expiry_mapping_source"].startswith("RULE_DERIVED"):
        assumptions.append("expiry estimated from NIFTY expiry weekday rule and observed Dhan spot session dates; not verified against historical contract master")
    for field, value in greeks.items():
        row[field] = format(value, ".12g")
    row["greek_assumption"] = "; ".join(assumptions) if assumptions else "point-in-time sourced inputs"
    row["greek_status"] = "CALCULATED_BS_V1_PROXY_INPUTS" if assumptions else "CALCULATED_BS_V1_SOURCED_INPUTS"


def parse_option_response(payload: dict[str, Any], request: dict[str, Any],
                          spot_by_timestamp: dict[int, dict[str, Any]],
                          response_digest: str, cache_status: str,
                          expiry_map: dict[tuple[str, str, int], dict[str, str]],
                          rates: list[tuple[dt.datetime, float, str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("option_response_data_object_missing")
    side = "ce" if request["body"]["drvOptionType"] == "CALL" else "pe"
    side_obj = data.get(side)
    if side_obj is None:
        return [], ["valid_empty_side"]
    if not isinstance(side_obj, dict):
        raise ValueError("option_side_not_object")
    timestamps, arrays = _array_set(side_obj, ["timestamp", "open", "high", "low", "close", "iv", "volume", "strike", "oi", "spot"])
    if len(timestamps) > int(request.get("max_rows", 0)):
        raise ValueError("response_row_cap_exceeded")
    start_date = dt.date.fromisoformat(request["window_start_inclusive"])
    end_date = dt.date.fromisoformat(request["window_end_exclusive"])
    seen = set()
    rows = []
    problems = []
    for i, epoch in sorted(enumerate(timestamps), key=lambda it: (it[1], it[0])):
        ist = dt.datetime.fromtimestamp(epoch, tz=UTC).astimezone(IST)
        if not (start_date <= ist.date() < end_date):
            raise ValueError("option_timestamp_outside_requested_calendar_window")
        flags = []
        if epoch in seen:
            flags.append("DUPLICATE_TIMESTAMP_IN_PROVIDER_RESPONSE")
            problems.append("duplicate_timestamp")
        seen.add(epoch)
        spotrow = spot_by_timestamp.get(epoch)
        if spotrow is None:
            join_status = "NO_EXACT_TIMESTAMP_SPOT_MATCH"
            nifty_fields = {"nifty_open": "", "nifty_high": "", "nifty_low": "", "nifty_close": "", "nifty_volume": ""}
            flags.append("SPOT_JOIN_MISSING")
        else:
            join_status = "EXACT_TIMESTAMP_MATCH"
            nifty_fields = {field: spotrow.get(field, "") for field in ("nifty_open", "nifty_high", "nifty_low", "nifty_close", "nifty_volume")}
        row = {
            "timestamp_epoch": str(epoch), "row_type": "OPTION",
            "timestamp_utc": dt.datetime.fromtimestamp(epoch, tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "timestamp_ist": ist.isoformat(timespec="seconds"), "session_date": ist.date().isoformat(),
            "underlying": "NIFTY", "expiry_flag": request["body"]["expiryFlag"],
            "expiry_code": str(request["body"]["expiryCode"]),
            "requested_relative_strike": request["body"]["strike"],
            "returned_strike": _value_string(arrays["strike"][i]),
            "option_type": request["body"]["drvOptionType"],
            "option_open": _value_string(arrays["open"][i]),
            "option_high": _value_string(arrays["high"][i]),
            "option_low": _value_string(arrays["low"][i]),
            "option_close": _value_string(arrays["close"][i]),
            "option_volume": _value_string(arrays["volume"][i]),
            "open_interest": _value_string(arrays["oi"][i]),
            "implied_volatility": _value_string(arrays["iv"][i]),
            "rolling_spot": _value_string(arrays["spot"][i]),
            **nifty_fields, "spot_join_status": join_status,
            "source_provider": "DhanHQ", "source_endpoint": request["endpoint"],
            "source_request_id": request["request_id"],
            "request_scope_sha256": request_scope_hash(request),
            "response_sha256": response_digest, "cache_status": cache_status,
            "expiry_date": "", "expiry_mapping_source": "", "time_to_expiry_years": "",
            "risk_free_rate_decimal": "", "risk_free_rate_source": "", "dividend_yield_decimal": "", "dividend_yield_source": "", "greek_assumption": "",
            "delta": "", "gamma": "", "theta_per_day": "",
            "vega_per_1pct_iv": "", "rho_per_1pct_rate": "",
            "greek_model": "Black-Scholes-European-v1", "greek_status": "",
            "data_quality_flags": "|".join(flags),
        }
        apply_greeks(row, expiry_map, rates)
        rows.append(row)
    return rows, problems


def _row_key(row: dict[str, str]) -> tuple[Any, ...]:
    return (int(row["timestamp_epoch"]), row["row_type"], row["source_request_id"],
            row["expiry_flag"], row["expiry_code"], row["requested_relative_strike"], row["option_type"])


def _iter_temp_csv(path: pathlib.Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def _write_temp_rows(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _month_writer(month: str, writers: dict[str, tuple[Any, Any]], counts: Counter):
    if month in writers:
        return writers[month][1]
    PLAIN_ROOT.mkdir(parents=True, exist_ok=True)
    path = PLAIN_ROOT / f"nifty_1m_composite_{month}.csv.gz"
    handle = gzip.open(path, "wt", encoding="utf-8", newline="", compresslevel=6)
    writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writers[month] = (handle, writer)
    counts[month] += 0
    return writer


def get_cached_payload(request: dict[str, Any], key: bytes) -> tuple[bytes, dict[str, Any]] | None:
    enc_path, meta_path = safe_cache_paths(request["request_id"])
    if not enc_path.exists() or not meta_path.exists():
        return None
    try:
        meta = load_json(meta_path)
        if meta.get("request_scope_sha256") != request_scope_hash(request):
            raise ValueError("cache_request_scope_mismatch")
        encrypted = enc_path.read_bytes()
        if sha256_bytes(encrypted) != meta.get("ciphertext_sha256"):
            raise ValueError("cache_ciphertext_hash_mismatch")
        raw = decrypt_bytes(encrypted, key)
        if sha256_bytes(raw) != meta.get("response_sha256") or len(raw) != meta.get("response_bytes"):
            raise ValueError("cache_response_hash_mismatch")
        return raw, meta
    except Exception:
        return None


def store_cached_payload(request: dict[str, Any], raw: bytes, key: bytes, http_status: int,
                         row_count: int, content_type: str) -> dict[str, Any]:
    enc_path, meta_path = safe_cache_paths(request["request_id"])
    encrypted = encrypt_bytes(raw, key)
    meta = {
        "schema_version": 1, "request_id": request["request_id"],
        "source_family": request["source_family"], "endpoint": request["endpoint"],
        "request_scope_sha256": request_scope_hash(request),
        "response_sha256": sha256_bytes(raw), "response_bytes": len(raw),
        "ciphertext_sha256": sha256_bytes(encrypted), "ciphertext_bytes": len(encrypted),
        "http_status": int(http_status), "content_type": content_type,
        "row_count": int(row_count), "retrieved_at_utc": utc_now(),
        "encrypted_at_rest": True,
        "encryption": "AES-256-GCM; key= scrypt(HF_TOKEN, fixed public context salt); token value never persisted",
    }
    atomic_write(enc_path, encrypted)
    atomic_write(meta_path, (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return meta


class RequestPacer:
    def __init__(self, interval: float = MIN_REQUEST_INTERVAL_SECONDS):
        self.interval = interval
        self.last: float | None = None

    def wait(self):
        now = time.monotonic()
        if self.last is not None:
            remaining = self.interval - (now - self.last)
            if remaining > 0:
                time.sleep(remaining)
        self.last = time.monotonic()


def fetch_live(request: dict[str, Any], token: str, pacer: RequestPacer,
               wire_budget: dict[str, int], max_wire_requests: int,
               max_retry_requests: int, response_cap_override: int | None = None) -> tuple[bytes, int, str, int]:
    url = request["endpoint"]
    cap = int(request["max_response_bytes"])
    if response_cap_override is not None:
        cap = min(cap, max(0, int(response_cap_override)))
    body = json.dumps(request["body"], separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(body) > 16 * 1024:
        raise SourceRequestError("request_body_byte_cap_exceeded")
    last_exc: Exception | None = None
    for attempt in range(2):
        is_retry = attempt > 0
        if wire_budget["wire_requests"] >= max_wire_requests:
            raise SourceRequestError("wire_request_budget_exceeded")
        if is_retry and wire_budget["retry_requests"] >= max_retry_requests:
            raise SourceRequestError("retry_budget_exceeded")
        pacer.wait()
        wire_budget["wire_requests"] += 1
        if is_retry:
            wire_budget["retry_requests"] += 1
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Accept": "application/json", "Content-Type": "application/json",
                     "access-token": token, "User-Agent": USER_AGENT},
        )
        try:
            response = urllib.request.build_opener(NoRedirect()).open(req, timeout=TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            try:
                exc.close()
            except Exception:
                pass
            if 300 <= status < 400:
                raise SourceRequestError("redirect_rejected", status) from None
            if attempt == 0 and (status == 429 or status >= 500):
                time.sleep(2.0 if status == 429 else 1.0)
                continue
            raise SourceRequestError("http_status_" + str(status), status) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise SourceRequestError("transport_error_" + type(exc).__name__) from None
        try:
            status = int(getattr(response, "status", 0))
            headers = getattr(response, "headers", {})
            raw_type = str(headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
            if 300 <= status < 400:
                raise SourceRequestError("redirect_rejected", status)
            if status < 200 or status >= 300:
                raise SourceRequestError("http_status_" + str(status), status)
            if raw_type not in ("application/json", "text/json") and not raw_type.endswith("+json"):
                raise SourceRequestError("unexpected_content_type")
            declared = headers.get("Content-Length")
            if declared:
                try:
                    declared_int = int(declared)
                except ValueError:
                    raise SourceRequestError("invalid_content_length")
                if declared_int < 0 or declared_int > cap:
                    raise SourceRequestError("response_byte_cap_exceeded")
            data = response.read(cap + 1)
            if len(data) > cap:
                raise SourceRequestError("response_byte_cap_exceeded")
            if declared and int(declared) != len(data):
                raise SourceRequestError("content_length_mismatch")
            return data, status, raw_type, attempt
        finally:
            try:
                response.close()
            except Exception:
                pass
    if last_exc:
        raise SourceRequestError("transport_error_" + type(last_exc).__name__) from None
    raise SourceRequestError("retry_exhausted")


def _validate_request_payload(payload: dict[str, Any], request: dict[str, Any]) -> None:
    if request["source_family"] == "NIFTY_SPOT_1M":
        rows, _ = parse_spot_response(payload, request)
        del rows
    elif request["source_family"] == "NIFTY_ROLLING_OPTION_1M":
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("option_response_data_object_missing")
        side = "ce" if request["body"]["drvOptionType"] == "CALL" else "pe"
        side_obj = data.get(side)
        if side_obj is None:
            return
        _array_set(side_obj, ["timestamp", "open", "high", "low", "close", "iv", "volume", "strike", "oi", "spot"])
    else:
        raise ValueError("unapproved_source_family")


def _payload_row_count(payload: dict[str, Any], request: dict[str, Any]) -> int:
    if request["source_family"] == "NIFTY_SPOT_1M":
        return len(payload.get("timestamp", [])) if isinstance(payload.get("timestamp"), list) else 0
    data = payload.get("data", {})
    side = "ce" if request["body"].get("drvOptionType") == "CALL" else "pe"
    side_data = data.get(side) if isinstance(data, dict) else None
    if not isinstance(side_data, dict):
        return 0
    ts = side_data.get("timestamp", [])
    return len(ts) if isinstance(ts, list) else 0


def _error_record(request: dict[str, Any], reason: str, status: int | None) -> dict[str, Any]:
    return {
        "request_id": request.get("request_id", ""),
        "source_family": request.get("source_family", ""),
        "window_start_inclusive": request.get("window_start_inclusive", ""),
        "window_end_exclusive": request.get("window_end_exclusive", ""),
        "status": "ERROR", "reason": reason, "http_status": status,
        "request_scope_sha256": request_scope_hash(request) if request.get("body") else "",
        "endpoint": request.get("endpoint", ""),
    }


def _read_cached_raw_total(family: str) -> int:
    total = 0
    for meta_path in CACHE_ROOT.glob("*.meta.json"):
        try:
            meta = load_json(meta_path)
            if meta.get("source_family") == family:
                total += int(meta.get("response_bytes", 0))
        except Exception:
            continue
    return total


def _select_window_requests(requests: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for request in requests:
        grouped[(request["window_start_inclusive"], request["window_end_exclusive"])].append(request)
    result = []
    for (start, end), members in sorted(grouped.items()):
        members.sort(key=lambda r: (r.get("source_family") != "NIFTY_SPOT_1M", r["request_id"]))
        result.append((start, end, members))
    return result


def _validate_spot_for_map(rows: list[dict[str, Any]]) -> tuple[dict[int, dict[str, Any]], list[dict[str, Any]]]:
    out: dict[int, dict[str, Any]] = {}
    duplicates = []
    for row in rows:
        ts = int(row["timestamp_epoch"])
        if ts in out:
            duplicates.append({"timestamp_epoch": ts, "session_date": row["session_date"]})
        out[ts] = row
    return out, duplicates


def request_payload(request: dict[str, Any], token: str, key: bytes, pacer: RequestPacer,
                    wire_budget: dict[str, int], budget: dict[str, Any],
                    auth_state: dict[str, bool]) -> tuple[dict[str, Any] | None, str, str, int, int]:
    cached = get_cached_payload(request, key)
    family = request["source_family"]
    if cached:
        raw, meta = cached
        try:
            payload = parse_json_numbers(raw)
            _validate_request_payload(payload, request)
            return payload, "CACHE_HIT", meta["response_sha256"], int(meta.get("http_status", 200)), len(raw)
        except SourceRequestError as exc:
            if exc.reason.startswith("dhan_api_auth_or_entitlement"):
                auth_state["failed"] = True
            budget["errors"].append(_error_record(request, exc.reason, exc.http_status))
            return None, "CACHE_INVALID", "", exc.http_status or 0, 0
        except Exception as exc:
            budget["errors"].append(_error_record(request, "cached_payload_invalid_" + type(exc).__name__, None))
            return None, "CACHE_INVALID", "", 0, 0
    if auth_state.get("failed"):
        budget["errors"].append(_error_record(request, "Dhan source halted after authentication/entitlement failure", None))
        return None, "SKIPPED_AUTH_FAILURE", "", 0, 0
    disabled = budget.setdefault("disabled_families", {})
    if disabled.get(family):
        budget["errors"].append(_error_record(request, "family_aggregate_byte_budget_exhausted", None))
        return None, "SKIPPED_BYTE_BUDGET", "", 0, 0
    used = int(budget["family_payload_bytes"].get(family, 0))
    limit = int(budget["family_byte_limits"][family])
    remaining = limit - used
    if remaining <= 1:
        disabled[family] = True
        budget["errors"].append(_error_record(request, "family_aggregate_byte_budget_exhausted", None))
        return None, "SKIPPED_BYTE_BUDGET", "", 0, 0
    try:
        raw, status, content_type, attempt = fetch_live(
            request, token, pacer, wire_budget,
            int(budget["max_wire_requests"]), int(budget["max_retry_requests"]),
            response_cap_override=remaining - 1
        )
        budget["downloaded_bytes"] += len(raw)
        budget["request_attempts"] = wire_budget["wire_requests"]
        budget["retry_requests"] = wire_budget["retry_requests"]
        payload = parse_json_numbers(raw)
        _validate_request_payload(payload, request)
        family_bytes = int(budget["family_payload_bytes"].get(family, 0)) + len(raw)
        limit = int(budget["family_byte_limits"][family])
        if family_bytes > limit:
            budget.setdefault("disabled_families", {})[family] = True
            budget["errors"].append(_error_record(request, "family_aggregate_byte_budget_exceeded", status))
            return None, "SKIPPED_BYTE_BUDGET", sha256_bytes(raw), status, len(raw)
        budget["family_payload_bytes"][family] = family_bytes
        side_count = _payload_row_count(payload, request)
        meta = store_cached_payload(request, raw, key, status, side_count, content_type)
        return payload, "FETCHED" if attempt == 0 else "FETCHED_AFTER_ONE_RETRY", meta["response_sha256"], status, len(raw)
    except SourceRequestError as exc:
        if (exc.http_status in (401, 403) or exc.reason.startswith("dhan_api_auth_or_entitlement")):
            auth_state["failed"] = True
        budget["errors"].append(_error_record(request, exc.reason, exc.http_status))
        budget["request_attempts"] = wire_budget["wire_requests"]
        budget["retry_requests"] = wire_budget["retry_requests"]
        return None, "FAILED_REQUEST", "", exc.http_status or 0, 0
    except Exception as exc:
        budget["errors"].append(_error_record(request, "unexpected_" + type(exc).__name__, None))
        return None, "FAILED_VALIDATION", "", 0, 0


def collect_run(root: dict[str, Any], requests: list[dict[str, Any]], token: str, key: bytes) -> dict[str, Any]:
    if ENCRYPTED_ROOT.exists():
        shutil.rmtree(ENCRYPTED_ROOT)
    if PLAIN_ROOT.exists():
        shutil.rmtree(PLAIN_ROOT)
    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    pacer = RequestPacer()
    wire_budget = {"wire_requests": 0, "retry_requests": 0}
    family_limits = {
        "NIFTY_SPOT_1M": int(root["budgets"]["spot_aggregate_bytes_max"]),
        "NIFTY_ROLLING_OPTION_1M": int(root["budgets"]["options_aggregate_bytes_max"]),
    }
    budget: dict[str, Any] = {
        "max_wire_requests": int(root["budgets"]["max_wire_requests_total"]),
        "max_retry_requests": int(root["budgets"]["max_retry_requests_total"]),
        "downloaded_bytes": 0, "request_attempts": 0, "retry_requests": 0,
        "family_payload_bytes": {family: _read_cached_raw_total(family) for family in family_limits},
        "family_byte_limits": family_limits, "errors": [], "request_results": [],
        "request_count_planned": len(requests), "request_count_processed": 0,
        "rows_spot": 0, "rows_options": 0, "spot_join_matched": 0,
        "spot_join_missing": 0, "empty_valid_responses": 0, "cache_hits": 0,
        "fresh_responses": 0, "failed_responses": 0,
    }
    expiry_map_external, rates, missing_greek_inputs = load_greek_inputs()
    month_writers: dict[str, tuple[Any, Any]] = {}
    monthly_rows: Counter = Counter()
    auth_state = {"failed": False}
    windows = _select_window_requests(requests)
    spot_context: dict[tuple[str, str], dict[str, Any]] = {}
    session_dates: set[str] = set()
    session_calendar_complete = True

    # Pass 1: acquire/cache all spot shards first. This provides an observed
    # trading-session calendar for transparent rule-derived expiry dates.
    for window_start, window_end, window_requests in windows:
        spot_request = next((r for r in window_requests if r["source_family"] == "NIFTY_SPOT_1M"), None)
        context: dict[str, Any] = {"request": spot_request, "path": None, "digest": "", "cache_status": "", "rows": 0}
        if spot_request is None:
            session_calendar_complete = False
            budget["errors"].append({"window_start": window_start, "reason": "SPOT_REQUEST_MISSING"})
            spot_context[(window_start, window_end)] = context
            continue

        payload, cache_status, digest, status_code, size = request_payload(
            spot_request, token, key, pacer, wire_budget, budget, auth_state
        )
        result = {
            "request_id": spot_request["request_id"], "source_family": spot_request["source_family"],
            "window_start_inclusive": window_start, "window_end_exclusive": window_end,
            "status": cache_status, "http_status": status_code or None,
            "response_bytes": size, "response_sha256": digest,
            "request_scope_sha256": request_scope_hash(spot_request),
        }
        budget["request_results"].append(result)
        budget["request_count_processed"] += 1
        if payload is None:
            budget["failed_responses"] += 1
            session_calendar_complete = False
            spot_context[(window_start, window_end)] = context
            continue
        try:
            rows, problems = parse_spot_response(payload, spot_request)
            for row in rows:
                row["response_sha256"] = digest
                row["cache_status"] = cache_status
            tmp = WORK_ROOT / (spot_request["request_id"] + ".csv")
            _write_temp_rows(tmp, rows)
            context.update({"path": tmp, "digest": digest, "cache_status": cache_status, "rows": len(rows)})
            result["row_count"] = len(rows)
            budget["rows_spot"] += len(rows)
            budget["cache_hits"] += int(cache_status == "CACHE_HIT")
            budget["fresh_responses"] += int(cache_status.startswith("FETCHED"))
            session_dates.update(row["session_date"] for row in rows)
            if not rows:
                session_calendar_complete = False
            if problems:
                budget["errors"].append(_error_record(spot_request, "provider_duplicate_timestamps_preserved_and_flagged", status_code))
        except Exception as exc:
            result["status"] = "FAILED_SCHEMA"
            result["reason"] = "spot_parse_error_" + type(exc).__name__
            budget["failed_responses"] += 1
            session_calendar_complete = False
            budget["errors"].append(_error_record(spot_request, result["reason"], status_code))
        spot_context[(window_start, window_end)] = context
        atomic_write(REPORTS_ROOT / "progress.json", (json.dumps({
            "updated_at_utc": utc_now(), "stage": "SPOT_SESSION_CALENDAR",
            "window_start": window_start, "window_end_exclusive": window_end,
            "request_count_processed": budget["request_count_processed"],
            "request_count_planned": budget["request_count_planned"],
            "rows_spot": budget["rows_spot"], "rows_options": 0,
            "source_failures_do_not_stop_other_request_keys": True,
        }, sort_keys=True, indent=2) + "\n").encode("utf-8"))

    expiry_map = build_rule_expiry_map(session_dates, expiry_map_external, session_calendar_complete)
    if not expiry_map_external:
        missing_greek_inputs.append(
            "expiry_map_rule_derived_from_observed_Dhan_spot_sessions_and_NIFTY_expiry_weekday_transition; not historical-contract-master verified"
        )
    if not rates:
        missing_greek_inputs.append("risk_free_rate_absent; Greeks use explicitly tagged zero-rate proxy")
    missing_greek_inputs.append("dividend_yield_absent_for_rule-derived_expiries; Greeks use explicitly tagged zero-dividend proxy")

    # Pass 2: fetch option selectors with one window in memory. Each response is
    # normalized to a timestamp-sorted scratch stream, then merged into monthly CSVs.
    for window_start, window_end, window_requests in windows:
        temp_files: list[pathlib.Path] = []
        context = spot_context.get((window_start, window_end), {})
        spot_path = context.get("path")
        spot_by_timestamp: dict[int, dict[str, Any]] = {}
        if isinstance(spot_path, pathlib.Path) and spot_path.exists():
            temp_files.append(spot_path)
            for row in _iter_temp_csv(spot_path):
                spot_by_timestamp[int(row["timestamp_epoch"])] = row

        for request in window_requests:
            if request["source_family"] == "NIFTY_SPOT_1M":
                continue
            payload, cache_status, digest, status_code, size = request_payload(
                request, token, key, pacer, wire_budget, budget, auth_state
            )
            result = {
                "request_id": request["request_id"], "source_family": request["source_family"],
                "window_start_inclusive": window_start, "window_end_exclusive": window_end,
                "status": cache_status, "http_status": status_code or None,
                "response_bytes": size, "response_sha256": digest,
                "request_scope_sha256": request_scope_hash(request),
            }
            budget["request_results"].append(result)
            budget["request_count_processed"] += 1
            if payload is None:
                budget["failed_responses"] += 1
                continue
            try:
                rows, problems = parse_option_response(
                    payload, request, spot_by_timestamp, digest, cache_status, expiry_map, rates
                )
                tmp = WORK_ROOT / (request["request_id"] + ".csv")
                _write_temp_rows(tmp, rows)
                temp_files.append(tmp)
                result["row_count"] = len(rows)
                budget["rows_options"] += len(rows)
                budget["spot_join_matched"] += sum(row["spot_join_status"] == "EXACT_TIMESTAMP_MATCH" for row in rows)
                budget["spot_join_missing"] += sum(row["spot_join_status"] == "NO_EXACT_TIMESTAMP_SPOT_MATCH" for row in rows)
                budget["cache_hits"] += int(cache_status == "CACHE_HIT")
                budget["fresh_responses"] += int(cache_status.startswith("FETCHED"))
                if not rows:
                    budget["empty_valid_responses"] += 1
                if problems:
                    budget["errors"].append(_error_record(request, "provider_duplicate_timestamps_preserved_and_flagged", status_code))
            except Exception as exc:
                result["status"] = "FAILED_SCHEMA"
                result["reason"] = "option_parse_error_" + type(exc).__name__
                budget["failed_responses"] += 1
                budget["errors"].append(_error_record(request, result["reason"], status_code))

        if temp_files:
            streams = [_iter_temp_csv(path) for path in temp_files]
            merged = heapq.merge(*streams, key=_row_key)
            for row in merged:
                month = row.get("timestamp_ist", "")[:7]
                if len(month) != 7:
                    continue
                writer = _month_writer(month, month_writers, monthly_rows)
                writer.writerow(row)
                monthly_rows[month] += 1
            for handle, _writer in month_writers.values():
                handle.flush()
            for path in temp_files:
                try:
                    path.unlink()
                except OSError:
                    pass

        atomic_write(REPORTS_ROOT / "progress.json", (json.dumps({
            "updated_at_utc": utc_now(), "stage": "OPTION_SELECTORS",
            "window_start": window_start, "window_end_exclusive": window_end,
            "request_count_processed": budget["request_count_processed"],
            "request_count_planned": budget["request_count_planned"],
            "rows_spot": budget["rows_spot"], "rows_options": budget["rows_options"],
            "failed_responses": budget["failed_responses"], "cache_hits": budget["cache_hits"],
            "retry_requests": wire_budget["retry_requests"],
            "source_failures_do_not_stop_other_request_keys": True,
        }, sort_keys=True, indent=2) + "\n").encode("utf-8"))

    for handle, _writer in month_writers.values():
        try:
            handle.close()
        except Exception:
            pass

    total_processed = budget["request_count_processed"]
    total_requests = len(requests)
    ok_statuses = {"CACHE_HIT", "FETCHED", "FETCHED_AFTER_ONE_RETRY"}
    failures = [r for r in budget["request_results"] if r.get("status") not in ok_statuses]
    budget["request_status_counts"] = dict(Counter(r.get("status", "") for r in budget["request_results"]))
    status = "COMPLETE_REQUEST_GRID" if total_processed == total_requests and not failures and not auth_state["failed"] else "PARTIAL_GRID"
    if auth_state["failed"]:
        status = "DHAN_AUTH_OR_ENTITLEMENT_FAILURE"
    budget_summary = {k: v for k, v in budget.items() if k not in ("errors", "request_results", "family_byte_limits")}
    budget_summary.update({
        "wire_requests": wire_budget["wire_requests"], "retry_requests": wire_budget["retry_requests"],
        "family_payload_bytes": budget["family_payload_bytes"],
        "observed_trading_session_count": len(session_dates),
        "observed_trading_session_calendar_complete": session_calendar_complete,
        "expiry_mapping_method": "Rule-derived weekly/monthly NIFTY expiry weekdays adjusted to previous observed Dhan spot session where observable; official rule transition represented; not verified against historical contract-master rows",
    })
    return {
        "schema_version": 1, "dataset_id": "NIFTY_1M_DHAN_ROLLING_OPTIONS_COMPOSITE_2021-10-11_2026-10-10",
        "created_at_utc": utc_now(), "status": status, "source_provider": "DhanHQ Data API",
        "history_start_inclusive": root["dataset_scope"]["history_start_inclusive"],
        "history_end_exclusive": root["dataset_scope"]["history_end_exclusive"],
        "interval": "1-minute",
        "user_acceptance": "Dhan output accepted as provided; no external market-value cross-check performed or required",
        "schema_columns": COLUMNS, "rows_per_month": dict(sorted(monthly_rows.items())),
        "summary": budget_summary, "errors": budget["errors"], "request_results": budget["request_results"],
        "missing_greek_inputs": missing_greek_inputs,
        "greek_method": "Black-Scholes-European-v1; source rate/dividend inputs where available, otherwise explicit zero-rate/zero-dividend proxy; expiry date from sourced calendar when available, otherwise rule-derived and visibly tagged",
        "greek_iv_unit_convention": "Heuristic v1: provider IV > 3 interpreted as percentage points and divided by 100; >0 through 3 interpreted as fractional; null otherwise. Dhan docs do not define IV numeric units.",
        "spot_join_policy": "Exact timestamp key only; rolling option spot and joined NIFTY spot OHLCV remain separate and are not reconciled.",
        "holdout_values_opened": False, "model_fitting_authorized": False, "final_holdout_access_authorized": False,
    }


def _iter_temp_csv(path: pathlib.Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def encrypt_outputs(key: bytes, result: dict[str, Any]) -> dict[str, Any]:
    ENCRYPTED_ROOT.mkdir(parents=True, exist_ok=True)
    encrypted_parts = []
    for path in sorted(PLAIN_ROOT.glob("nifty_1m_composite_*.csv.gz")):
        raw = path.read_bytes()
        encrypted = encrypt_bytes(raw, key)
        destination = ENCRYPTED_ROOT / (path.name + ".enc")
        atomic_write(destination, encrypted)
        month = path.name.removeprefix("nifty_1m_composite_").removesuffix(".csv.gz")
        encrypted_parts.append({
            "file": destination.name, "plain_gzip_sha256": sha256_bytes(raw),
            "plain_gzip_bytes": len(raw), "encrypted_sha256": sha256_bytes(encrypted),
            "encrypted_bytes": len(encrypted), "row_count": result["rows_per_month"].get(month, 0),
            "encryption": "AES-256-GCM, per-file random nonce, key derived via scrypt from HF_TOKEN",
        })
        path.unlink()
    manifest = {
        "schema_version": 1, "dataset_id": result["dataset_id"],
        "created_at_utc": result["created_at_utc"], "status": result["status"],
        "download_bundle_contains_encrypted_data_only": True,
        "do_not_upload_plaintext_or_publish_in_public_repository": True,
        "encryption": "AES-256-GCM; key derivation requires the same HF_TOKEN value used at collection time",
        "parts": encrypted_parts, "dataset_summary": result["summary"],
        "source_row_count_spot": result["summary"].get("rows_spot", 0),
        "source_row_count_options": result["summary"].get("rows_options", 0),
        "row_count_by_month": result["rows_per_month"],
        "failed_request_or_quality_event_count": len(result["errors"]),
        "missing_greek_inputs": result["missing_greek_inputs"], "columns": COLUMNS,
        "greek_method": result["greek_method"], "greek_iv_unit_convention": result["greek_iv_unit_convention"],
        "spot_join_policy": result["spot_join_policy"],
    }
    atomic_write(EXPORT_ROOT / "dataset_manifest.json", (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    atomic_write(EXPORT_ROOT / "coverage_and_errors.json", (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    readme = """# NIFTY one-minute composite dataset bundle

This bundle contains encrypted monthly CSV parts (.csv.gz.enc) and metadata. It does not contain plaintext market prices.
To decrypt locally, use scripts/decrypt_nifty_1m_composite.py and set HF_TOKEN to the same secret value used by the collection workflow. The token value is never written to this bundle.
After decryption, each part is a gzip-compressed CSV. Parts can be read individually with pandas/pyarrow and concatenated offline.

The columns include NIFTY spot bars, Dhan rolling-option OHLC, IV, OI, volume, strike, spot, provenance and reason-coded historical Greek fields. Historical Greeks remain null unless a timestamp-aligned expiry/rate/dividend table is available. This endpoint is a rolling ATM-relative dataset, not every historical option contract/strike.

See dataset_manifest.json and coverage_and_errors.json for completeness, request IDs, checksums, response counts and source gaps. COMPLETE_REQUEST_GRID means all enumerated requests were resolved; partial/empty responses and missing Greek inputs are not hidden.
"""
    atomic_write(EXPORT_ROOT / "README.md", readme.encode("utf-8"))
    if PLAIN_ROOT.exists():
        shutil.rmtree(PLAIN_ROOT, ignore_errors=True)
    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT, ignore_errors=True)
    return manifest


def main() -> int:
    root = load_json(ROOT_MANIFEST)
    from validate_nifty_1m_composite_manifest import validate as validate_manifest
    failures = validate_manifest()
    if failures:
        for err in failures[:20]:
            print("MANIFEST_VALIDATION_ERROR " + err)
        return 2
    requests = read_requests(root)
    token = os.environ.get("DHAN_ACCESS_TOKEN", "")
    hf_token = os.environ.get("HF_TOKEN", "")
    if not token:
        print("BLOCKED: DHAN_ACCESS_TOKEN is not configured; no requests made.")
        return 3
    if not hf_token:
        print("BLOCKED: HF_TOKEN is needed to encrypt/cache downloaded market data; no requests made.")
        return 3
    key = derive_key(hf_token)
    result = collect_run(root, requests, token, key)
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    encrypt_outputs(key, result)
    for error in result.get("errors", [])[:50]:
        print("SOURCE_ERROR " + json.dumps({k: error.get(k) for k in ("request_id", "source_family", "reason", "http_status")}, sort_keys=True))
    if len(result.get("errors", [])) > 50:
        print("SOURCE_ERROR_LOG_TRUNCATED " + json.dumps({"total_error_records": len(result.get("errors", [])), "printed": 50}))
    print(json.dumps({
        "status": result["status"],
        "request_count_processed": result["summary"].get("request_count_processed"),
        "request_count_planned": result["summary"].get("request_count_planned"),
        "wire_requests": result["summary"].get("wire_requests"),
        "retry_requests": result["summary"].get("retry_requests"),
        "rows_spot": result["summary"].get("rows_spot"),
        "rows_options": result["summary"].get("rows_options"),
        "failed_responses": result["summary"].get("failed_responses"),
        "encrypted_output_dir": str(ENCRYPTED_ROOT),
        "plaintext_market_rows_uploaded": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("INTERRUPTED: current window may be incomplete; encrypted request cache is resumable.")
        raise SystemExit(130)
