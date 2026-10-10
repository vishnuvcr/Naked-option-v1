#!/usr/bin/env python3
"""Fail-closed DhanHQ historical-candle sampler.

This module never makes a request on import. Live access requires an explicit
workflow-set authorization flag after an independent code gate and one-run
manifest validation. Never log or persist DHAN_ACCESS_TOKEN or profile identity.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

BASE = "https://api.dhan.co/v2"
PROFILE_URL = f"{BASE}/profile"
INDEX_INSTRUMENT_URL = f"{BASE}/instrument/IDX_I"
HISTORICAL_URL = f"{BASE}/charts/historical"
MAX_REQUESTS = 6
MAX_TOTAL_BYTES = 4 * 1024 * 1024
MAX_PROFILE_BYTES = 64 * 1024
MAX_INDEX_METADATA_BYTES = 1024 * 1024
MAX_CANDLE_BYTES = 752 * 1024
MAX_REDIRECT_DIAGNOSTIC_REQUESTS = 1
MAX_REDIRECT_DIAGNOSTIC_BYTES = 1024
TIMEOUT_SECONDS = 20
WINDOWS = (("2024-07-01", "2024-07-11"), ("2024-07-15", "2024-07-25"))
ALLOWED_INSTRUMENTS = ("NIFTY 50", "INDIA VIX")


@dataclass
class Budget:
    requests: int = 0
    bytes_read: int = 0
    request_limit: int = MAX_REQUESTS
    byte_limit: int = MAX_TOTAL_BYTES

    def reserve_request(self) -> None:
        if self.requests >= self.request_limit:
            raise ValueError("request_budget_exceeded")
        self.requests += 1

    def account_bytes(self, count: int) -> None:
        if count < 0 or self.bytes_read + count > self.byte_limit:
            raise ValueError("global_response_byte_budget_exceeded")
        self.bytes_read += count


def _no_redirect_opener():
    class RejectRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    return urllib.request.build_opener(RejectRedirect())


def safe_redirect_target(location: str) -> dict[str, str]:
    """Extract only scheme and normalized hostname; never return raw Location."""
    try:
        if not isinstance(location, str) or not location or len(location) > 2048:
            return {"redirect_target_status": "REDIRECT_TARGET_UNPARSEABLE"}
        if any(ch in location for ch in ("\r", "\n", "\x00")):
            return {"redirect_target_status": "REDIRECT_TARGET_UNPARSEABLE"}
        parsed = urllib.parse.urlsplit(location)
        if parsed.username is not None or parsed.password is not None or not parsed.hostname:
            return {"redirect_target_status": "REDIRECT_TARGET_UNPARSEABLE"}
        _ = parsed.port
        host = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
        if not host or len(host) > 253:
            return {"redirect_target_status": "REDIRECT_TARGET_UNPARSEABLE"}
        labels = host.split(".")
        if any(
            not label or len(label) > 63
            or re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label) is None
            for label in labels
        ):
            return {"redirect_target_status": "REDIRECT_TARGET_UNPARSEABLE"}
        scheme = parsed.scheme.lower()
        if scheme != "https":
            return {"redirect_target_status": "REDIRECT_TARGET_UNPARSEABLE"}
        return {"redirect_target_status": "PARSED", "redirect_scheme": scheme, "redirect_host": host}
    except (ValueError, UnicodeError):
        return {"redirect_target_status": "REDIRECT_TARGET_UNPARSEABLE"}


def request_bytes(
    url: str,
    *,
    method: str,
    token: str,
    body: bytes | None,
    cap: int,
    budget: Budget,
    opener_factory: Callable[[], Any] = _no_redirect_opener,
) -> tuple[int, bytes, dict[str, str]]:
    """Make one allowlisted HTTPS request, read cap+1 for overflow detection."""
    if url not in (PROFILE_URL, INDEX_INSTRUMENT_URL, HISTORICAL_URL):
        raise ValueError("unregistered_url")
    if not token:
        raise ValueError("missing_dhan_access_token")
    if method not in ("GET", "POST"):
        raise ValueError("unsupported_method")
    if (url == HISTORICAL_URL) != (method == "POST"):
        raise ValueError("method_url_mismatch")
    budget.reserve_request()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "access-token": token,
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    opener = opener_factory()
    try:
        response = opener.open(req, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        # Never read or retain the provider error body; keep only safe metadata.
        safe_headers: dict[str, str] = {}
        try:
            content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
            location = exc.headers.get("Location", "") if exc.headers else ""
        except Exception:
            content_type, location = "", ""
        if (
            isinstance(content_type, str)
            and bool(content_type)
            and len(content_type) <= 120
            and not any(ch in content_type for ch in ("\r", "\n"))
        ):
            safe_headers["content-type"] = content_type
        if 300 <= int(exc.code) < 400 and location:
            safe_headers.update(safe_redirect_target(location))
        return int(exc.code), b"", safe_headers
    except Exception as exc:
        # Exception text may include request details; deliberately redact it.
        raise RuntimeError(f"dhan_transport_error_{type(exc).__name__}") from None
    try:
        status = int(response.status)
        if status < 200 or status >= 300:
            raise RuntimeError(f"dhan_http_status_{status}")
        data = response.read(cap + 1)
        budget.account_bytes(len(data))
        if len(data) > cap:
            raise ValueError("per_response_byte_cap_exceeded")
        # No redirect is followed by the configured opener; reject redirect statuses.
        if status in (301, 302, 303, 307, 308):
            raise ValueError("redirect_rejected")
        safe_headers = {k.lower(): v for k, v in response.headers.items()
                        if k.lower() in ("content-type", "content-length")}
        return status, data, safe_headers
    finally:
        response.close()


def parse_profile_probe(status: int, body: bytes) -> dict[str, Any]:
    """Return only redacted status flags; never return identity or raw fields."""
    result: dict[str, Any] = {
        "http_status": status,
        "token_valid": status == 200,
        "data_plan_active": None,
        "status": "TOKEN_VALID" if status == 200 else "TOKEN_REJECTED",
    }
    if status != 200:
        return result
    try:
        obj = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result["status"] = "PROFILE_SCHEMA_UNVERIFIED"
        result["token_valid"] = None
        return result
    if not isinstance(obj, dict):
        result["status"] = "PROFILE_SCHEMA_UNVERIFIED"
        result["token_valid"] = None
        return result
    if "dataPlan" in obj:
        result["data_plan_active"] = str(obj.get("dataPlan", "")).strip().lower() == "active"
    else:
        result["status"] = "DATA_ENTITLEMENT_UNKNOWN"
    return result


def parse_index_instruments(body: bytes) -> dict[str, dict[str, str]]:
    """Accept official CSV or JSON segment metadata; require unique exact mappings."""
    rows: list[dict[str, Any]]
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("instrument_metadata_not_text") from None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        try:
            rows = list(csv.DictReader(io.StringIO(text)))
        except csv.Error:
            raise ValueError("instrument_metadata_unrecognized_shape") from None
        if not rows or not rows[0]:
            raise ValueError("instrument_metadata_unrecognized_shape")
    else:
        if isinstance(obj, list):
            rows = obj
        elif isinstance(obj, dict):
            rows = obj.get("data", obj.get("dataList", obj.get("instruments")))
            if not isinstance(rows, list):
                raise ValueError("instrument_metadata_unrecognized_shape")
        else:
            raise ValueError("instrument_metadata_unrecognized_shape")
    found: dict[str, list[dict[str, str]]] = {s: [] for s in ALLOWED_INSTRUMENTS}
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("SEM_TRADING_SYMBOL", row.get("symbol", row.get("tradingSymbol", "")))).strip().upper()
        name = str(row.get("SEM_CUSTOM_SYMBOL", row.get("displayName", row.get("name", "")))).strip().upper()
        secid = str(row.get("SEM_SMST_SECURITY_ID", row.get("SEM_SECURITY_ID", row.get("securityId", row.get("security_id", ""))))).strip()
        segment = str(row.get("SEM_SEGMENT", row.get("segment", row.get("exchangeSegment", "")))).strip().upper()
        inst = str(row.get("SEM_INSTRUMENT_NAME", row.get("instrument", row.get("instrumentType", "")))).strip().upper()
        label = "NIFTY 50" if symbol in ("NIFTY", "NIFTY 50", "NIFTY50") or name in ("NIFTY 50", "NIFTY50") else (
            "INDIA VIX" if symbol in ("INDIA VIX", "INDIAVIX") or name == "INDIA VIX" else None
        )
        if label and secid and segment in ("IDX_I", "I") and (inst in ("INDEX", "IDX", "INDEXES", "")):
            found[label].append({"security_id": secid, "exchange_segment": "IDX_I", "instrument": "INDEX"})
    result = {}
    for label, matches in found.items():
        unique = {(m["security_id"], m["exchange_segment"], m["instrument"]) for m in matches}
        if len(unique) != 1:
            raise ValueError("instrument_mapping_missing_or_ambiguous:" + label.lower().replace(" ", "_"))
        secid, segment, instrument = next(iter(unique))
        result[label] = {"security_id": secid, "exchange_segment": segment, "instrument": instrument}
    return result

def validate_window(from_date: str, to_date: str) -> None:
    start = dt.date.fromisoformat(from_date)
    end = dt.date.fromisoformat(to_date)
    if end <= start or (end - start).days > 10:
        raise ValueError("date_window_invalid_or_exceeds_10_days")


def build_historical_payload(instrument: dict[str, str], from_date: str, to_date: str) -> bytes:
    validate_window(from_date, to_date)
    payload = {
        "securityId": instrument["security_id"],
        "exchangeSegment": instrument["exchange_segment"],
        "instrument": instrument["instrument"],
        "oi": True,
        "fromDate": from_date,
        "toDate": to_date,
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def parse_candles(status: int, body: bytes, from_date: str, to_date: str) -> dict[str, Any]:
    validate_window(from_date, to_date)
    if status != 200:
        return {"status": "HTTP_REJECTED", "http_status": status}
    try:
        obj = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"status": "REJECTED_NON_JSON"}
    if not isinstance(obj, dict):
        return {"status": "REJECTED_SCHEMA"}
    required = ("open", "high", "low", "close", "volume", "timestamp")
    if any(not isinstance(obj.get(k), list) for k in required):
        return {"status": "REJECTED_SCHEMA", "reason": "required_array_missing"}
    n = len(obj["timestamp"])
    if n == 0 or any(len(obj[k]) != n for k in required):
        return {"status": "REJECTED_SCHEMA", "reason": "array_lengths_mismatch_or_empty"}
    if "open_interest" in obj and (not isinstance(obj["open_interest"], list) or len(obj["open_interest"]) != n):
        return {"status": "REJECTED_SCHEMA", "reason": "open_interest_length_mismatch"}
    dates = []
    previous = None
    for i, ts in enumerate(obj["timestamp"]):
        if isinstance(ts, bool) or not isinstance(ts, (int, float)) or not math.isfinite(float(ts)):
            return {"status": "REJECTED_TIMESTAMP", "row": i}
        day = dt.datetime.fromtimestamp(int(ts), tz=dt.timezone(dt.timedelta(hours=5, minutes=30))).date().isoformat()
        if not (from_date <= day < to_date):
            return {"status": "REJECTED_OUTSIDE_REQUESTED_WINDOW", "row": i, "date": day}
        if previous is not None and int(ts) <= previous:
            return {"status": "REJECTED_DUPLICATE_OR_UNSORTED_TIMESTAMP", "row": i}
        previous = int(ts)
        dates.append(day)
    for i, (o, h, l, close, volume) in enumerate(zip(obj["open"], obj["high"], obj["low"], obj["close"], obj["volume"])):
        vals = (o, h, l, close, volume)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in vals):
            return {"status": "REJECTED_NONFINITE_CANDLE", "row": i}
        if min(o, h, l, close) <= 0 or h < max(o, close, l) or l > min(o, close, h) or volume < 0:
            return {"status": "REJECTED_INVALID_OHLCV", "row": i}
    return {
        "status": "SCHEMA_SAMPLE_PASS",
        "row_count": n,
        "first_date": dates[0],
        "last_date": dates[-1],
        "unique_dates": len(set(dates)),
        "has_open_interest": isinstance(obj.get("open_interest"), list),
        "fields": list(required) + (["open_interest"] if isinstance(obj.get("open_interest"), list) else []),
    }


def sample_plan(instruments: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    plan = []
    for label in ALLOWED_INSTRUMENTS:
        for start, end in WINDOWS:
            plan.append({
                "label": label,
                "security_id": instruments[label]["security_id"],
                "exchange_segment": instruments[label]["exchange_segment"],
                "instrument": instruments[label]["instrument"],
                "from_date": start,
                "to_date": end,
            })
    if len(plan) > 4:
        raise ValueError("historical_request_budget_exceeded")
    return plan


def blocked_metadata_result(status: int, headers: dict[str, str], budget: Budget, profile: dict[str, Any]) -> dict[str, Any]:
    """Return only safe diagnostics for a failed instrument metadata response."""
    content_type = headers.get("content-type", "")
    if len(content_type) > 120 or any(ch in content_type for ch in ("\r", "\n")):
        content_type = ""
    result = {
        "status": "BLOCKED_INSTRUMENT_METADATA",
        "instrument_metadata_http_status": int(status),
        "instrument_metadata_content_type": content_type,
        "profile_probe": profile,
        "request_count": budget.requests,
        "bytes_read": budget.bytes_read,
    }
    for key in ("redirect_target_status", "redirect_scheme", "redirect_host"):
        value = headers.get(key)
        if value:
            result[key] = value
    return result


def redirect_target_probe() -> dict[str, Any]:
    """One-request diagnostic: report only status and redirect scheme/hostname."""
    if os.environ.get("DHAN_REDIRECT_DIAGNOSTIC_AUTHORIZED") != "1":
        raise RuntimeError("redirect_diagnostic_not_authorized")
    token = os.environ.get("DHAN_ACCESS_TOKEN", "")
    if not token:
        return {"status": "BLOCKED_SECRET_MISSING", "request_count": 0, "bytes_read": 0}
    budget = Budget(
        request_limit=MAX_REDIRECT_DIAGNOSTIC_REQUESTS,
        byte_limit=MAX_REDIRECT_DIAGNOSTIC_BYTES,
    )
    status, body, headers = request_bytes(
        INDEX_INSTRUMENT_URL, method="GET", token=token, body=None,
        cap=MAX_REDIRECT_DIAGNOSTIC_BYTES, budget=budget,
    )
    # Body is never parsed or returned. Only redirect metadata and bounded counters survive.
    result: dict[str, Any] = {
        "http_status": status,
        "request_count": budget.requests,
        "bytes_read": budget.bytes_read,
        "content_type": headers.get("content-type", ""),
    }
    for key in ("redirect_target_status", "redirect_scheme", "redirect_host"):
        if headers.get(key):
            result[key] = headers[key]
    if 300 <= status < 400:
        result["status"] = "REDIRECT_TARGET_RECORDED" if result.get("redirect_target_status") == "PARSED" and result.get("redirect_scheme") == "https" else "REDIRECT_TARGET_UNVERIFIED"
    elif status == 200:
        result["status"] = "METADATA_ENDPOINT_NO_REDIRECT"
    else:
        result["status"] = "METADATA_ENDPOINT_BLOCKED"
    return result


def live_sample() -> dict[str, Any]:
    """Called only by a future guarded workflow after consuming a one-run manifest."""
    if os.environ.get("DHAN_LIVE_SAMPLE_AUTHORIZED") != "1":
        raise RuntimeError("live_sample_not_authorized")
    token = os.environ.get("DHAN_ACCESS_TOKEN", "")
    if not token:
        return {"status": "BLOCKED_SECRET_MISSING"}
    budget = Budget()
    # Profile response body is bounded, immediately reduced to booleans, then discarded.
    status, profile_body, _ = request_bytes(
        PROFILE_URL, method="GET", token=token, body=None,
        cap=MAX_PROFILE_BYTES, budget=budget,
    )
    profile = parse_profile_probe(status, profile_body)
    del profile_body
    if profile.get("token_valid") is not True or profile.get("data_plan_active") is not True:
        return {"status": "BLOCKED_AUTH_OR_ENTITLEMENT", "profile_probe": profile,
                "request_count": budget.requests, "bytes_read": budget.bytes_read}
    status, instrument_body, metadata_headers = request_bytes(
        INDEX_INSTRUMENT_URL, method="GET", token=token, body=None,
        cap=MAX_INDEX_METADATA_BYTES, budget=budget,
    )
    if status != 200:
        return blocked_metadata_result(status, metadata_headers, budget, profile)
    instruments = parse_index_instruments(instrument_body)
    del instrument_body
    plan = sample_plan(instruments)
    reports = []
    for item in plan:
        payload = build_historical_payload(item, item["from_date"], item["to_date"])
        status, body, _ = request_bytes(
            HISTORICAL_URL, method="POST", token=token, body=payload,
            cap=MAX_CANDLE_BYTES, budget=budget,
        )
        parsed = parse_candles(status, body, item["from_date"], item["to_date"])
        reports.append({"label": item["label"], "from_date": item["from_date"],
                        "to_date_exclusive": item["to_date"], "response_sha256": __import__("hashlib").sha256(body).hexdigest(),
                        "validation": parsed})
        del body
    # Token is never included in the return object or output.
    return {"status": "SAMPLE_COMPLETED", "profile_probe": profile,
            "instrument_labels": list(instruments), "sample_reports": reports,
            "request_count": budget.requests, "bytes_read": budget.bytes_read}


if __name__ == "__main__":
    if os.environ.get("DHAN_REDIRECT_DIAGNOSTIC_AUTHORIZED") == "1":
        result = redirect_target_probe()
        out = __import__("pathlib").Path("data/reports/dhan_redirect_target_probe.json")
    else:
        if os.environ.get("DHAN_LIVE_SAMPLE_AUTHORIZED") != "1":
            raise SystemExit("Blocked: no approved Dhan sample manifest.")
        result = live_sample()
        out = __import__("pathlib").Path("data/reports/dhan_market_data_sample.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps({
        "report_path": str(out),
        "status": result.get("status"),
        "request_count": result.get("request_count"),
        "bytes_read": result.get("bytes_read"),
        "sample_count": len(result.get("sample_reports", [])),
    }, indent=2, sort_keys=True))
