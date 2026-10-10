#!/usr/bin/env python3
"""Dhan historical-market-data parsing and bounded request helpers.

Importing this module and running the CLI are offline-only. No request is made
unless a caller explicitly invokes request_json after a separately gated workflow
supplies an authorization decision and secret. Do not use this module for orders.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import pathlib
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

BASE = "https://api.dhan.co/v2"
DAILY_URL = f"{BASE}/charts/historical"
INTRADAY_URL = f"{BASE}/charts/intraday"
ROLLING_OPTION_URL = f"{BASE}/charts/rollingoption"
ALLOWED_URLS = frozenset({DAILY_URL, INTRADAY_URL, ROLLING_OPTION_URL})
MAX_REQUESTS = 1  # default sample-gate budget; bulk runs need a new reviewed budget
MAX_TOTAL_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_REQUEST_BODY_BYTES = 16 * 1024
TIMEOUT_SECONDS = 20
MIN_REQUEST_INTERVAL_SECONDS = 3.0
JSON_CONTENT_TYPES = frozenset({"application/json", "application/json; charset=utf-8"})


@dataclass
class RequestBudget:
    requests: int = 0
    bytes_read: int = 0
    request_limit: int = MAX_REQUESTS
    byte_limit: int = MAX_TOTAL_BYTES
    last_request_monotonic: float | None = None

    def reserve_request(self, *, now: float | None = None) -> None:
        if self.requests >= self.request_limit:
            raise ValueError("request_budget_exceeded")
        tick = time.monotonic() if now is None else now
        if self.last_request_monotonic is not None:
            elapsed = tick - self.last_request_monotonic
            if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
                raise ValueError("request_pacing_limit")
        self.requests += 1
        self.last_request_monotonic = tick

    def account_bytes(self, count: int) -> None:
        if count < 0 or self.bytes_read + count > self.byte_limit:
            raise ValueError("global_response_byte_budget_exceeded")
        self.bytes_read += count


def _no_redirect_opener():
    """Create an opener that rejects redirect responses without following them."""
    class RejectRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    return urllib.request.build_opener(RejectRedirect())


def _valid_api_url(url: str) -> bool:
    if url not in ALLOWED_URLS:
        return False
    try:
        parsed = urllib.parse.urlsplit(url)
        return (
            parsed.scheme == "https"
            and parsed.hostname == "api.dhan.co"
            and parsed.port in (None, 443)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
    except (ValueError, TypeError):
        return False


def request_json(
    url: str,
    body_obj: dict[str, Any],
    *,
    token: str,
    budget: RequestBudget,
    opener_factory: Callable[[], Any] = _no_redirect_opener,
    now: float | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Call exactly one allowlisted POST and return data plus redacted metadata.

    This helper never follows redirects, never logs the token, and never reads
    HTTP-error bodies. Live calls must be authorized by a separate workflow and
    single-use manifest; the CLI deliberately does not expose a live mode.
    """
    if not _valid_api_url(url):
        raise ValueError("unregistered_or_unsafe_url")
    if not isinstance(body_obj, dict):
        raise ValueError("request_body_must_be_object")
    body = json.dumps(body_obj, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(body) > MAX_REQUEST_BODY_BYTES:
        raise ValueError("request_body_byte_cap_exceeded")
    if not isinstance(token, str) or not token.strip() or any(c in token for c in "\r\n"):
        raise ValueError("missing_or_invalid_dhan_access_token")

    budget.reserve_request(now=now)
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "access-token": token,
            "User-Agent": "Naked-option-v1-research/1.0",
        },
        method="POST",
    )
    opener = opener_factory()
    try:
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        # Do not inspect/read Location or response body, and do not leak exception text.
        try:
            exc.close()
        except Exception:
            pass
        if 300 <= status < 400:
            raise ValueError("dhan_redirect_rejected") from None
        raise ValueError(f"dhan_http_status_{status}") from None
    except Exception as exc:
        # URL, headers and provider error bodies must not be copied to logs.
        raise RuntimeError(f"dhan_transport_error_{type(exc).__name__}") from None

    try:
        status = int(getattr(response, "status", 0))
        if 300 <= status < 400:
            raise ValueError("dhan_redirect_rejected")
        if status < 200 or status >= 300:
            raise ValueError(f"dhan_http_status_{status}")
        headers = getattr(response, "headers", {})
        raw_type = str(headers.get("Content-Type", "")).strip().lower()
        content_type = raw_type.split(";", 1)[0].strip()
        if content_type != "application/json" and not content_type.endswith("+json"):
            raise ValueError("dhan_unexpected_content_type")
        raw_length = headers.get("Content-Length")
        if raw_length is not None:
            try:
                declared_length = int(raw_length)
            except (ValueError, TypeError):
                raise ValueError("dhan_invalid_content_length") from None
            if declared_length < 0:
                raise ValueError("dhan_invalid_content_length")
            if declared_length > MAX_RESPONSE_BYTES:
                raise ValueError("dhan_response_byte_cap_exceeded")
        data = response.read(MAX_RESPONSE_BYTES + 1)
        budget.account_bytes(len(data))
        if len(data) > MAX_RESPONSE_BYTES:
            raise ValueError("dhan_response_byte_cap_exceeded")
        if raw_length is not None and int(raw_length) != len(data):
            raise ValueError("dhan_content_length_mismatch")
        try:
            payload = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("dhan_json_invalid") from None
        if not isinstance(payload, dict):
            raise ValueError("dhan_json_root_not_object")
        meta = {
            "http_status": status,
            "content_type": content_type,
            "response_bytes": len(data),
            "response_sha256": hashlib.sha256(data).hexdigest(),
            "request_count": budget.requests,
            "cumulative_response_bytes": budget.bytes_read,
            "network_enabled": True,
        }
        return payload, meta
    finally:
        try:
            response.close()
        except Exception:
            pass


def validate_candle_payload(
    payload: dict[str, Any],
    *,
    required_fields: tuple[str, ...] = ("open", "high", "low", "close", "volume"),
) -> dict[str, Any]:
    """Check historical/intraday parallel arrays, timestamps and OHLC constraints."""
    if not isinstance(payload, dict):
        raise ValueError("candle_payload_not_object")
    mandatory = ("timestamp",) + tuple(required_fields)
    for key in mandatory:
        if key not in payload or not isinstance(payload[key], list):
            raise ValueError(f"candle_array_missing_{key}")
    lengths = {len(payload[key]) for key in mandatory}
    if len(lengths) != 1:
        raise ValueError("candle_array_length_mismatch")
    count = lengths.pop()
    if count == 0:
        raise ValueError("candle_array_empty")

    timestamps: list[int] = []
    for raw in payload["timestamp"]:
        if isinstance(raw, bool):
            raise ValueError("candle_timestamp_invalid")
        try:
            value = int(raw)
        except (ValueError, TypeError, OverflowError):
            raise ValueError("candle_timestamp_invalid") from None
        timestamps.append(value)
    if any(a >= b for a, b in zip(timestamps, timestamps[1:])):
        raise ValueError("candle_timestamps_not_strictly_increasing")

    numeric: dict[str, list[float]] = {}
    for field in required_fields:
        converted: list[float] = []
        for value in payload[field]:
            if isinstance(value, bool):
                raise ValueError(f"candle_value_invalid_{field}")
            try:
                num = float(value)
            except (ValueError, TypeError, OverflowError):
                raise ValueError(f"candle_value_invalid_{field}") from None
            if not math.isfinite(num):
                raise ValueError(f"candle_value_nonfinite_{field}")
            if field in ("open", "high", "low", "close", "volume", "open_interest", "oi", "strike", "spot", "iv") and num < 0:
                raise ValueError(f"candle_value_negative_{field}")
            converted.append(num)
        numeric[field] = converted

    if all(f in numeric for f in ("open", "high", "low", "close")):
        for i, (opn, high, low, close) in enumerate(zip(
            numeric["open"], numeric["high"], numeric["low"], numeric["close"]
        )):
            if low > high or high < max(opn, close) or low > min(opn, close):
                raise ValueError(f"candle_ohlc_inconsistent_row_{i}")

    return {
        "row_count": count,
        "first_timestamp": timestamps[0],
        "last_timestamp": timestamps[-1],
        "timestamp_sha256": hashlib.sha256(
            json.dumps(timestamps, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
        "fields": list(required_fields),
    }


def validate_rolling_option_payload(
    payload: dict[str, Any],
    *,
    option_type: str,
    required_fields: tuple[str, ...] = (
        "open", "high", "low", "close", "iv", "volume", "oi", "strike", "spot"
    ),
) -> dict[str, Any]:
    """Validate Dhan's rolling-option envelope and all requested parallel arrays."""
    if option_type not in ("CALL", "PUT"):
        raise ValueError("rolling_option_type_invalid")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("rolling_option_data_missing")
    side = "ce" if option_type == "CALL" else "pe"
    rows = data.get(side)
    if not isinstance(rows, dict):
        raise ValueError("rolling_option_side_missing")
    required = tuple(required_fields)
    # Reuse OHLC/timestamp checks for core fields; validate the entire aligned
    # field collection separately so no IV/OI/strike/spot mismatch is possible.
    for key in ("timestamp",) + required:
        if key not in rows or not isinstance(rows[key], list):
            raise ValueError(f"rolling_option_array_missing_{key}")
    lengths = {len(rows[key]) for key in ("timestamp",) + required}
    if len(lengths) != 1:
        raise ValueError("rolling_option_array_length_mismatch")
    basic = validate_candle_payload(
        {key: rows[key] for key in ("timestamp", "open", "high", "low", "close", "volume")},
        required_fields=("open", "high", "low", "close", "volume"),
    )
    # Numeric and sign checks for non-OHLC fields.
    for field in ("iv", "oi", "strike", "spot"):
        for value in rows[field]:
            if isinstance(value, bool):
                raise ValueError(f"rolling_option_value_invalid_{field}")
            try:
                numeric = float(value)
            except (ValueError, TypeError, OverflowError):
                raise ValueError(f"rolling_option_value_invalid_{field}") from None
            if not math.isfinite(numeric) or numeric < 0:
                raise ValueError(f"rolling_option_value_invalid_{field}")
    return {
        **basic,
        "option_type": option_type,
        "side": side,
        "fields": ["timestamp", *required],
    }


def validate_request_window(url: str, body: dict[str, Any]) -> dict[str, Any]:
    """Validate API endpoint-specific request shapes and documented date caps."""
    if not _valid_api_url(url):
        raise ValueError("unregistered_or_unsafe_url")
    if url == DAILY_URL:
        start, end = body.get("fromDate"), body.get("toDate")
        if not body.get("securityId") or not body.get("exchangeSegment") or not body.get("instrument"):
            raise ValueError("daily_request_instrument_fields_missing")
        _validate_date_range(start, end, max_days=None)
        if body.get("oi", False) not in (True, False):
            raise ValueError("daily_request_oi_invalid")
        return {"source": "daily_candles", "fromDate": start, "toDate": end}
    if url == INTRADAY_URL:
        start, end = body.get("fromDate"), body.get("toDate")
        if not body.get("securityId") or not body.get("exchangeSegment") or not body.get("instrument"):
            raise ValueError("intraday_request_instrument_fields_missing")
        if str(body.get("interval")) not in {"1", "5", "15", "25", "60"}:
            raise ValueError("intraday_interval_invalid")
        _validate_datetime_range(start, end, max_days=90)
        return {"source": "intraday_candles", "fromDate": start, "toDate": end, "interval": str(body["interval"])}
    if url == ROLLING_OPTION_URL:
        start, end = body.get("fromDate"), body.get("toDate")
        if not all(body.get(k) is not None for k in (
            "exchangeSegment", "interval", "securityId", "instrument",
            "expiryFlag", "expiryCode", "strike", "drvOptionType", "requiredData"
        )):
            raise ValueError("rolling_option_request_fields_missing")
        if str(body.get("interval")) not in {"1", "5", "15", "25", "60"}:
            raise ValueError("rolling_option_interval_invalid")
        if body.get("expiryFlag") not in {"WEEK", "MONTH"}:
            raise ValueError("rolling_option_expiry_flag_invalid")
        if body.get("drvOptionType") not in {"CALL", "PUT"}:
            raise ValueError("rolling_option_type_invalid")
        _validate_date_range(start, end, max_days=30)
        if not isinstance(body.get("requiredData"), list) or not body["requiredData"]:
            raise ValueError("rolling_option_required_data_invalid")
        allowed = {"open", "high", "low", "close", "iv", "volume", "oi", "strike", "spot"}
        if not set(body["requiredData"]).issubset(allowed):
            raise ValueError("rolling_option_required_data_unrecognized")
        return {"source": "rolling_expired_options", "fromDate": start, "toDate": end, "interval": str(body["interval"])}
    raise ValueError("unregistered_or_unsafe_url")


def _validate_date_range(start: Any, end: Any, *, max_days: int | None) -> None:
    try:
        from_date = __import__("datetime").date.fromisoformat(str(start))
        to_date = __import__("datetime").date.fromisoformat(str(end))
    except (ValueError, TypeError):
        raise ValueError("date_range_invalid") from None
    if to_date <= from_date:
        raise ValueError("date_range_not_increasing")
    if max_days is not None and (to_date - from_date).days > max_days:
        raise ValueError("date_range_exceeds_documented_cap")


def _validate_datetime_range(start: Any, end: Any, *, max_days: int) -> None:
    import datetime as dt
    try:
        from_date = dt.datetime.fromisoformat(str(start).replace(" ", "T"))
        to_date = dt.datetime.fromisoformat(str(end).replace(" ", "T"))
    except (ValueError, TypeError):
        raise ValueError("datetime_range_invalid") from None
    if to_date <= from_date:
        raise ValueError("datetime_range_not_increasing")
    if (to_date.date() - from_date.date()).days > max_days:
        raise ValueError("date_range_exceeds_documented_cap")


def atomic_cache_bundle(
    payload_bytes: bytes,
    validation: dict[str, Any],
    *,
    cache_root: str | pathlib.Path,
    source_url: str,
    request_metadata: dict[str, Any],
    request_parameters: dict[str, Any],
    fetched_at_utc: str,
) -> dict[str, Any]:
    """Persist validated, content-addressed response+manifest atomically, without secrets."""
    if source_url not in ALLOWED_URLS:
        raise ValueError("cache_source_url_unregistered")
    if not isinstance(payload_bytes, bytes) or not payload_bytes:
        raise ValueError("cache_payload_empty")
    digest = hashlib.sha256(payload_bytes).hexdigest()
    root = pathlib.Path(cache_root)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / digest
    manifest = {
        "schema_version": 1,
        "source_url": source_url,
        "fetched_at_utc": fetched_at_utc,
        "response_sha256": digest,
        "response_bytes": len(payload_bytes),
        "validation": validation,
        "request_metadata": {
            key: request_metadata[key]
            for key in ("http_status", "content_type", "response_bytes", "request_count", "cumulative_response_bytes")
            if key in request_metadata
        },
        "request_parameters": request_parameters,
    }
    # Explicitly reject common credential-like fields in any persisted metadata.
    forbidden = {"access-token", "access_token", "token", "client_id", "clientid", "authorization", "cookie"}
    if any(str(k).lower().replace("-", "_") in {x.replace("-", "_") for x in forbidden} for k in manifest):
        raise ValueError("cache_manifest_contains_forbidden_key")
    encoded_manifest = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if destination.exists():
        existing = destination / "manifest.json"
        content = destination / "response.json"
        if existing.is_file() and content.is_file() and hashlib.sha256(content.read_bytes()).hexdigest() == digest:
            return {"status": "CACHE_ALREADY_PRESENT", "sha256": digest, "path": str(destination)}
        raise ValueError("cache_hash_directory_conflict")
    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix=".dhan-cache-", dir=str(root)))
    try:
        (temp_dir / "response.json").write_bytes(payload_bytes)
        (temp_dir / "manifest.json").write_bytes(encoded_manifest)
        for path in (temp_dir / "response.json", temp_dir / "manifest.json"):
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
        os.replace(temp_dir, destination)
    except Exception:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return {"status": "CACHE_CREATED", "sha256": digest, "path": str(destination), "response_bytes": len(payload_bytes)}


def main() -> int:
    """Print safe status only; intentionally cannot perform live network I/O."""
    print(json.dumps({
        "status": "OFFLINE_VALIDATION_ONLY",
        "network_enabled": False,
        "allowed_endpoints": sorted(ALLOWED_URLS),
        "sample_request_budget": MAX_REQUESTS,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "max_total_response_bytes": MAX_TOTAL_BYTES,
        "timeout_seconds": TIMEOUT_SECONDS,
        "minimum_request_interval_seconds": MIN_REQUEST_INTERVAL_SECONDS,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
