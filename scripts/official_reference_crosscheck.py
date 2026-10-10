#!/usr/bin/env python3
"""Bounded public-source cross-check for one cached NIFTY 50 daily sample.

This module only validates request/response bytes and parses source rows.
It has no import-time network activity, does not contain credentials and
cannot authorize itself. The separate gate validator/workflow controls use.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from dhan_instrument_master import MAX_CSV_BYTES, validate_instrument_csv

NIFTY_INDICES_URL = "https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString"
NIFTY_INDICES_REFERER = "https://www.niftyindices.com/reports"
DHAN_COMPACT_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"

EXPECTED_SCOPE_ID = "dhan-sample-official-crosscheck-2024-01-02-two-hosts"
EXPECTED_DATE = "2024-01-02"
EXPECTED_DHAN_ROW = {
    "open": "21751.35",
    "high": "21755.60",
    "low": "21555.65",
    "close": "21665.80",
    "volume": "263711568",
}
EXPECTED_DHAN_SAMPLE_RESPONSE_SHA256 = "efd83cb7f0a1dd1002663fc84b6098faaabe32ad9d2e10dd4cc91770e2e4ed70"
EXPECTED_DHAN_SAMPLE_MANIFEST_BLOB = "601f956e4e31e5a1288a3381fbf59217e37dee10"
EXPECTED_DHAN_SAMPLE_PARAMS = {
    "exchangeSegment": "IDX_I",
    "fromDate": "2024-01-02",
    "instrument": "INDEX",
    "oi": False,
    "securityId": "13",
    "toDate": "2024-01-03",
}
EXPECTED_MAPPING = {
    "security_id": "13",
    "exchange": "NSE",
    "instrument_name": "INDEX",
    "symbol": "NIFTY",
}

NIFTY_INDICES_REQUEST_BODY = {
    "cinfo": "{'name':'NIFTY 50','startDate':'02 Jan 2024','endDate':'02 Jan 2024','indexName':'NIFTY 50'}"
}
NIFTY_MAX_RESPONSE_BYTES = 512 * 1024
NIFTY_TIMEOUT_SECONDS = 20
DHAN_MASTER_TIMEOUT_SECONDS = 20
MAX_SOURCE_REQUESTS = 2
CONTENT_TYPE_NIFTY = frozenset({"application/json", "text/json"})
CONTENT_TYPE_CSV = frozenset({
    "text/csv", "application/csv", "application/octet-stream", "text/plain"
})


class _RedirectRejectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def no_redirect_opener():
    """Create an opener which refuses HTTP redirects."""
    return urllib.request.build_opener(_RedirectRejectHandler())


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalized_content_type(value: str | None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("source_content_type_missing")
    return value.split(";", 1)[0].strip().lower()


def _header(headers: Any, name: str) -> str | None:
    if headers is None:
        return None
    try:
        value = headers.get(name)
        if value is None:
            value = headers.get(name.lower())
        if value is None:
            value = headers.get(name.title())
        return None if value is None else str(value)
    except Exception:
        return None


def _validate_url(url: str, allowed_url: str) -> None:
    if url != allowed_url:
        raise ValueError("source_url_not_allowlisted")
    parts = urllib.parse.urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.username or
            parts.password or parts.query or parts.fragment):
        raise ValueError("source_url_not_allowlisted")


def request_once(
    *,
    source: str,
    url: str,
    allowed_url: str,
    method: str,
    body: bytes | None,
    headers: dict[str, str],
    allowed_content_types: frozenset[str],
    byte_cap: int,
    timeout_seconds: int,
    opener_factory: Callable[[], Any] = no_redirect_opener,
) -> tuple[bytes, dict[str, Any]]:
    """Make exactly one bounded request; redirects, retries and unsafe responses fail closed."""
    if source not in {"nifty_indices", "dhan_instrument_master"}:
        raise ValueError("source_name_invalid")
    _validate_url(url, allowed_url)
    if method not in {"GET", "POST"} or (method == "GET" and body is not None) or (method == "POST" and not isinstance(body, bytes)):
        raise ValueError("source_request_method_or_body_invalid")
    if type(byte_cap) is not int or byte_cap <= 0:
        raise ValueError("source_byte_cap_invalid")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 20:
        raise ValueError("source_timeout_invalid")

    forbidden_headers = {
        "authorization", "access-token", "cookie", "set-cookie",
        "dhanclientid", "client-id", "client_id",
    }
    if any(str(key).strip().lower() in forbidden_headers for key in headers):
        raise ValueError("source_credentials_forbidden")
    req = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    opener = opener_factory()
    try:
        response = opener.open(req, timeout=timeout_seconds)
    except urllib.error.HTTPError as exc:
        code = int(exc.code)
        try:
            exc.close()
        except Exception:
            pass
        if 300 <= code < 400:
            raise ValueError(f"{source}_redirect_rejected") from None
        raise ValueError(f"{source}_http_status_{code}") from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            raise ValueError(f"{source}_timeout") from None
        raise ValueError(f"{source}_connection_failed") from None
    except TimeoutError:
        raise ValueError(f"{source}_timeout") from None
    except Exception as exc:
        if isinstance(exc, (ValueError, RuntimeError)):
            raise
        raise ValueError(f"{source}_request_failed") from None

    try:
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()
        if type(status) is not int or status != 200:
            raise ValueError(f"{source}_http_status_invalid")

        raw_type = _header(getattr(response, "headers", None), "Content-Type")
        content_type = _normalized_content_type(raw_type)
        if content_type not in allowed_content_types:
            raise ValueError(f"{source}_content_type_invalid")

        raw_length = _header(getattr(response, "headers", None), "Content-Length")
        expected_length = None
        if raw_length is not None:
            try:
                if not re.fullmatch(r"[0-9]+", raw_length.strip()):
                    raise ValueError
                expected_length = int(raw_length.strip())
            except ValueError:
                raise ValueError(f"{source}_content_length_invalid") from None
            if expected_length > byte_cap:
                raise ValueError(f"{source}_byte_cap_exceeded")

        raw = response.read(byte_cap + 1)
        if not isinstance(raw, bytes):
            raise ValueError(f"{source}_response_bytes_invalid")
        if len(raw) > byte_cap:
            raise ValueError(f"{source}_byte_cap_exceeded")
        if not raw:
            raise ValueError(f"{source}_response_empty")
        if expected_length is not None and expected_length != len(raw):
            raise ValueError(f"{source}_content_length_mismatch")
        metadata = {
            "source": source,
            "url": url,
            "method": method,
            "http_status": 200,
            "content_type": content_type,
            "response_bytes": len(raw),
            "response_sha256": _sha256(raw),
            "request_count": 1,
            "retry_count": 0,
            "redirect_followed": False,
        }
        return raw, metadata
    finally:
        try:
            response.close()
        except Exception:
            pass


def _normalize_key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def _pick(row: dict[str, Any], *names: str) -> Any:
    wanted = {_normalize_key(name) for name in names}
    matches = [value for key, value in row.items() if _normalize_key(key) in wanted]
    if len(matches) != 1:
        raise ValueError("nifty_reference_field_missing_or_ambiguous")
    return matches[0]


def _decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"nifty_reference_numeric_invalid_{field}")
    text = str(value).strip().replace(",", "")
    try:
        result = Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValueError(f"nifty_reference_numeric_invalid_{field}") from None
    if not result.is_finite():
        raise ValueError(f"nifty_reference_numeric_invalid_{field}")
    return result


def _parse_date(value: Any) -> str:
    text = str(value).strip()
    for fmt in ("%d %b %Y", "%d-%b-%Y", "%d %B %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError("nifty_reference_date_invalid")


def parse_nifty_indices_response(raw: bytes, *, expected_date: str = EXPECTED_DATE) -> dict[str, str]:
    """Parse the official historical-index JSON response and require exactly one NIFTY 50 row."""
    try:
        outer = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("nifty_reference_json_invalid") from None
    if not isinstance(outer, dict) or "d" not in outer:
        raise ValueError("nifty_reference_envelope_invalid")
    rows = outer["d"]
    if isinstance(rows, str):
        try:
            rows = json.loads(rows)
        except json.JSONDecodeError:
            raise ValueError("nifty_reference_data_json_invalid") from None
    if not isinstance(rows, list):
        raise ValueError("nifty_reference_rows_invalid")
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("nifty_reference_row_count_not_one")
    row = rows[0]
    index_name = str(_pick(row, "INDEX_NAME", "IndexName", "indexName")).strip()
    if index_name.casefold() != "nifty 50":
        raise ValueError("nifty_reference_index_name_mismatch")
    actual_date = _parse_date(_pick(row, "HistoricalDate", "Date", "date"))
    if actual_date != expected_date:
        raise ValueError("nifty_reference_date_mismatch")
    out = {
        "index_name": index_name,
        "date": actual_date,
        "open": format(_decimal(_pick(row, "OPEN", "Open", "open"), field="open"), ".2f"),
        "high": format(_decimal(_pick(row, "HIGH", "High", "high"), field="high"), ".2f"),
        "low": format(_decimal(_pick(row, "LOW", "Low", "low"), field="low"), ".2f"),
        "close": format(_decimal(_pick(row, "CLOSE", "Close", "close"), field="close"), ".2f"),
    }
    if Decimal(out["low"]) > Decimal(out["high"]):
        raise ValueError("nifty_reference_ohlc_inconsistent")
    if Decimal(out["high"]) < max(Decimal(out["open"]), Decimal(out["close"])):
        raise ValueError("nifty_reference_ohlc_inconsistent")
    if Decimal(out["low"]) > min(Decimal(out["open"]), Decimal(out["close"])):
        raise ValueError("nifty_reference_ohlc_inconsistent")
    return out


def parse_dhan_instrument_mapping(
    raw: bytes,
    *,
    expected: dict[str, str] = EXPECTED_MAPPING,
) -> dict[str, str]:
    """Validate Dhan's compact-master schema without confusing its codes with API enums."""
    validation, rows = validate_instrument_csv(raw, max_bytes=MAX_CSV_BYTES)
    matches = [row for row in rows if row.get("SEM_SMST_SECURITY_ID") == expected["security_id"]]
    if len(matches) != 1:
        raise ValueError("dhan_mapping_row_count_not_one")
    row = matches[0]
    exchange = (row.get("SEM_EXM_EXCH_ID") or "").strip().upper()
    compact_segment = (row.get("SEM_SEGMENT") or "").strip().upper()
    instrument = (row.get("SEM_INSTRUMENT_NAME") or "").strip().upper()
    trading_symbol = (row.get("SEM_TRADING_SYMBOL") or "").strip().upper()
    symbol_name = (row.get("SM_SYMBOL_NAME") or "").strip().upper()
    custom_symbol = (row.get("SEM_CUSTOM_SYMBOL") or "").strip().upper()
    instrument_type = (row.get("SEM_EXCH_INSTRUMENT_TYPE") or "").strip().upper()
    if exchange != expected["exchange"]:
        raise ValueError("dhan_mapping_exchange_mismatch")
    if trading_symbol != expected["symbol"]:
        raise ValueError("dhan_mapping_trading_symbol_mismatch")
    # Instrument List uses its own compact codes C/D/E/M. IDX_I is an API enum,
    # not a value to compare directly with SEM_SEGMENT.
    if compact_segment not in {"C", "D", "E", "M"}:
        raise ValueError("dhan_mapping_compact_segment_invalid")
    if instrument != expected["instrument_name"]:
        raise ValueError("dhan_mapping_instrument_mismatch")
    labels = [x for x in (trading_symbol, symbol_name, custom_symbol) if x]
    if not labels or not any("NIFTY" in label for label in labels):
        raise ValueError("dhan_mapping_symbol_mismatch")
    if any("BANK" in label or "INDIAVIX" in label or "VIX" in label for label in labels):
        raise ValueError("dhan_mapping_symbol_mismatch")
    if symbol_name and not ("NIFTY 50" in symbol_name or symbol_name == "NIFTY"):
        raise ValueError("dhan_mapping_symbol_name_mismatch")
    if custom_symbol and not ("NIFTY 50" in custom_symbol or custom_symbol == "NIFTY"):
        raise ValueError("dhan_mapping_display_name_mismatch")
    # If the exchange instrument-type field is populated, do not ignore a
    # contradictory equity/derivative value when asserting an index mapping.
    if instrument_type and instrument_type not in {"IDX", "INDEX", "INDEX_VALUE"}:
        raise ValueError("dhan_mapping_exchange_instrument_type_mismatch")
    return {
        "security_id": expected["security_id"],
        "exchange": exchange,
        "compact_segment": compact_segment,
        "instrument_name": instrument,
        "trading_symbol": trading_symbol,
        "symbol_name": symbol_name,
        "display_name": custom_symbol,
        "exchange_instrument_type": instrument_type,
        "csv_sha256": validation.sha256,
        "csv_row_count": str(validation.row_count),
        "csv_bytes": str(len(raw)),
    }

def compare_ohlc(
    nifty_reference: dict[str, str],
    dhan_row: dict[str, str] = EXPECTED_DHAN_ROW,
) -> dict[str, Any]:
    """Exact two-decimal comparison between official OHLC and the frozen Dhan row."""
    fields = ("open", "high", "low", "close")
    mismatches = {
        key: {"dhan": str(dhan_row.get(key)), "official": str(nifty_reference.get(key))}
        for key in fields if str(dhan_row.get(key)) != str(nifty_reference.get(key))
    }
    return {
        "status": "MATCH" if not mismatches else "MISMATCH",
        "date": EXPECTED_DATE,
        "field_count": len(fields),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "volume_crosschecked": False,
    }


def make_nifty_request_body() -> bytes:
    return json.dumps(NIFTY_INDICES_REQUEST_BODY, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def main() -> int:
    """This CLI validates the adapter configuration only; it never performs requests."""
    print(json.dumps({
        "status": "OFFLINE_VALIDATION_ONLY",
        "network_enabled": False,
        "nifty_indices_url": NIFTY_INDICES_URL,
        "dhan_master_url": DHAN_COMPACT_MASTER_URL,
        "max_source_requests": MAX_SOURCE_REQUESTS,
        "nifty_response_byte_cap": NIFTY_MAX_RESPONSE_BYTES,
        "dhan_master_response_byte_cap": MAX_CSV_BYTES,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
