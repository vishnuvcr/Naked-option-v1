#!/usr/bin/env python3
"""Offline-only regression tests for Dhan adapter. Never calls the network."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import sys
import urllib.error
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dhan_recovery", ROOT / "scripts/dhan_market_data_recovery.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_import_does_not_request_network() -> None:
    assert mod.PROFILE_URL == "https://api.dhan.co/v2/profile"
    assert mod.MAX_REQUESTS == 6


def test_missing_secret_stops_before_request() -> None:
    with patch.dict(mod.os.environ, {"DHAN_LIVE_SAMPLE_AUTHORIZED": "1"}, clear=True):
        assert mod.live_sample() == {"status": "BLOCKED_SECRET_MISSING"}


def test_live_sample_requires_workflow_authorization() -> None:
    with patch.dict(mod.os.environ, {"DHAN_ACCESS_TOKEN": "do-not-print"}, clear=True):
        try:
            mod.live_sample()
        except RuntimeError as exc:
            assert str(exc) == "live_sample_not_authorized"
        else:
            raise AssertionError("live sample must fail closed")


def test_profile_probe_redacts_identity_fields() -> None:
    body = json.dumps({
        "dhanClientId": "private-id", "dhanClientName": "private-name",
        "dhanClientUcc": "private-ucc", "tokenValidity": "private-time",
        "activeSegment": "Equity", "dataPlan": "Active",
    }).encode()
    result = mod.parse_profile_probe(200, body)
    assert result == {"http_status": 200, "token_valid": True,
                      "data_plan_active": True, "status": "TOKEN_VALID"}
    assert all(secret not in json.dumps(result) for secret in ("private-id", "private-name", "private-ucc", "private-time", "Equity"))


def test_profile_probe_blocks_inactive_data_plan() -> None:
    result = mod.parse_profile_probe(200, b'{"dataPlan":"Inactive","dhanClientId":"hidden"}')
    assert result["data_plan_active"] is False
    assert "dhanClientId" not in result


def test_profile_probe_handles_bad_json_without_echo() -> None:
    result = mod.parse_profile_probe(200, b"private-token-like-payload")
    assert result["status"] == "PROFILE_SCHEMA_UNVERIFIED"
    assert "private-token-like-payload" not in json.dumps(result)


def test_request_url_allowlist_blocks_unregistered_host_before_budget() -> None:
    b = mod.Budget()
    try:
        mod.request_bytes("https://evil.example/profile", method="GET", token="secret", body=None, cap=10, budget=b)
    except ValueError as exc:
        assert str(exc) == "unregistered_url"
    else:
        raise AssertionError("unregistered URL accepted")
    assert b.requests == 0


def test_request_missing_token_blocks_before_budget() -> None:
    b = mod.Budget()
    try:
        mod.request_bytes(mod.PROFILE_URL, method="GET", token="", body=None, cap=10, budget=b)
    except ValueError as exc:
        assert str(exc) == "missing_dhan_access_token"
    else:
        raise AssertionError("missing token accepted")
    assert b.requests == 0


def test_request_counts_bytes_and_requests() -> None:
    class Response:
        status = 200
        headers = {"Content-Type": "application/json", "Set-Cookie": "ignore-me"}
        def read(self, n): return b'{"ok":true}'
        def close(self): pass
    class Opener:
        def open(self, req, timeout):
            assert req.full_url == mod.PROFILE_URL
            assert req.get_header("Access-token") == "do-not-print"
            assert timeout == 20
            return Response()
    b = mod.Budget()
    status, body, headers = mod.request_bytes(mod.PROFILE_URL, method="GET", token="do-not-print", body=None,
                                                cap=100, budget=b, opener_factory=Opener)
    assert status == 200 and body == b'{"ok":true}'
    assert headers == {"content-type": "application/json"}
    assert b.requests == 1 and b.bytes_read == len(body)


def test_request_rejects_over_cap_and_counts_overflow_byte() -> None:
    class Response:
        status = 200
        headers = {}
        def read(self, n): return b"123456"
        def close(self): pass
    class Opener:
        def open(self, req, timeout): return Response()
    b = mod.Budget()
    try:
        mod.request_bytes(mod.PROFILE_URL, method="GET", token="secret", body=None, cap=5, budget=b, opener_factory=Opener)
    except ValueError as exc:
        assert str(exc) == "per_response_byte_cap_exceeded"
    else:
        raise AssertionError("oversized response accepted")
    assert b.bytes_read == 6


def test_global_budget_fails_closed() -> None:
    b = mod.Budget(requests=mod.MAX_REQUESTS, bytes_read=0)
    try:
        b.reserve_request()
    except ValueError as exc:
        assert str(exc) == "request_budget_exceeded"
    else:
        raise AssertionError("request budget exceeded")
    b = mod.Budget(bytes_read=mod.MAX_TOTAL_BYTES - 2)
    try:
        b.account_bytes(3)
    except ValueError as exc:
        assert str(exc) == "global_response_byte_budget_exceeded"
    else:
        raise AssertionError("byte budget exceeded")


def test_instrument_mapping_requires_unique_exact_ids() -> None:
    rows = [
        {"SEM_TRADING_SYMBOL": "NIFTY", "SEM_CUSTOM_SYMBOL": "NIFTY 50", "SEM_SMST_SECURITY_ID": "101",
         "SEM_SEGMENT": "IDX_I", "SEM_INSTRUMENT_NAME": "INDEX"},
        {"SEM_TRADING_SYMBOL": "INDIAVIX", "SEM_CUSTOM_SYMBOL": "INDIA VIX", "SEM_SMST_SECURITY_ID": "102",
         "SEM_SEGMENT": "IDX_I", "SEM_INSTRUMENT_NAME": "INDEX"},
    ]
    got = mod.parse_index_instruments(json.dumps(rows).encode())
    assert got["NIFTY 50"]["security_id"] == "101"
    assert got["INDIA VIX"]["security_id"] == "102"


def test_instrument_mapping_accepts_official_csv_headers() -> None:
    body = (
        "SEM_TRADING_SYMBOL,SEM_CUSTOM_SYMBOL,SEM_SMST_SECURITY_ID,SEM_SEGMENT,SEM_INSTRUMENT_NAME\\n"
        "NIFTY,NIFTY 50,101,IDX_I,INDEX\\n"
        "INDIAVIX,INDIA VIX,102,IDX_I,INDEX\\n"
    ).encode()
    got = mod.parse_index_instruments(body)
    assert got["NIFTY 50"]["security_id"] == "101"
    assert got["INDIA VIX"]["security_id"] == "102"


def test_http_error_returns_status_without_provider_body() -> None:
    class Opener:
        def open(self, req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "unauthorized", {}, None)
    b = mod.Budget()
    status, body, headers = mod.request_bytes(
        mod.PROFILE_URL, method="GET", token="secret-token", body=None,
        cap=mod.MAX_PROFILE_BYTES, budget=b, opener_factory=Opener,
    )
    assert status == 401 and body == b"" and headers == {}
    assert b.requests == 1


def test_instrument_mapping_rejects_ambiguous_security_id() -> None:
    rows = [
        {"symbol": "NIFTY", "name": "NIFTY 50", "securityId": "101", "segment": "IDX_I", "instrument": "INDEX"},
        {"symbol": "NIFTY", "name": "NIFTY 50", "securityId": "999", "segment": "IDX_I", "instrument": "INDEX"},
        {"symbol": "INDIAVIX", "name": "INDIA VIX", "securityId": "102", "segment": "IDX_I", "instrument": "INDEX"},
    ]
    try:
        mod.parse_index_instruments(json.dumps(rows).encode())
    except ValueError as exc:
        assert str(exc) == "instrument_mapping_missing_or_ambiguous:nifty_50"
    else:
        raise AssertionError("ambiguous mapping accepted")


def test_windows_are_fixed_and_non_overlapping() -> None:
    assert len(mod.WINDOWS) == 2
    for start, end in mod.WINDOWS:
        mod.validate_window(start, end)
        assert (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days == 10
    assert mod.WINDOWS[0][1] <= mod.WINDOWS[1][0]


def test_payload_uses_non_inclusive_end_and_resolved_id() -> None:
    payload = json.loads(mod.build_historical_payload(
        {"security_id": "13", "exchange_segment": "IDX_I", "instrument": "INDEX"},
        "2024-07-01", "2024-07-11"))
    assert payload["securityId"] == "13"
    assert payload["fromDate"] == "2024-07-01"
    assert payload["toDate"] == "2024-07-11"
    assert payload["oi"] is True


def test_payload_rejects_wide_or_invalid_window() -> None:
    for start, end in (("2024-01-01", "2024-01-12"), ("2024-07-11", "2024-07-01"), ("bad", "2024-07-01")):
        try:
            mod.build_historical_payload({"security_id": "13", "exchange_segment": "IDX_I", "instrument": "INDEX"}, start, end)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid date window accepted")


def _candles():
    return {
        "open": [100.0, 101.0], "high": [102.0, 103.0],
        "low": [99.0, 100.0], "close": [101.0, 102.0],
        "volume": [10, 20], "timestamp": [1720000000, 1720086400],
        "open_interest": [0, 0],
    }


def test_candle_schema_accepts_aligned_finite_ohlcv() -> None:
    # UTC dates: 2024-07-03 and 2024-07-04.
    result = mod.parse_candles(200, json.dumps(_candles()).encode(), "2024-07-01", "2024-07-11")
    assert result["status"] == "SCHEMA_SAMPLE_PASS"
    assert result["row_count"] == 2
    assert result["has_open_interest"] is True


def test_candle_schema_rejects_mismatched_arrays() -> None:
    obj = _candles()
    obj["close"] = [101.0]
    result = mod.parse_candles(200, json.dumps(obj).encode(), "2024-07-01", "2024-07-11")
    assert result["status"] == "REJECTED_SCHEMA"


def test_candle_schema_rejects_out_of_window_timestamps() -> None:
    obj = _candles()
    obj["timestamp"] = [1704067200, 1704153600]
    result = mod.parse_candles(200, json.dumps(obj).encode(), "2024-07-01", "2024-07-11")
    assert result["status"] == "REJECTED_OUTSIDE_REQUESTED_WINDOW"


def test_candle_schema_rejects_duplicate_or_unsorted_timestamps() -> None:
    obj = _candles()
    obj["timestamp"] = [1720000000, 1720000000]
    result = mod.parse_candles(200, json.dumps(obj).encode(), "2024-07-01", "2024-07-11")
    assert result["status"] == "REJECTED_DUPLICATE_OR_UNSORTED_TIMESTAMP"


def test_candle_schema_rejects_invalid_ohlc() -> None:
    obj = _candles()
    obj["high"] = [98.0, 103.0]
    result = mod.parse_candles(200, json.dumps(obj).encode(), "2024-07-01", "2024-07-11")
    assert result["status"] == "REJECTED_INVALID_OHLCV"


def test_candle_schema_rejects_nan() -> None:
    obj = _candles()
    obj["close"] = [float("nan"), 102.0]
    result = mod.parse_candles(200, json.dumps(obj).encode(), "2024-07-01", "2024-07-11")
    assert result["status"] == "REJECTED_NONFINITE_CANDLE"


def test_workflow_or_test_suite_does_not_invoke_live_sample() -> None:
    # The offline workflow invokes only this fixture suite and contains no live authorization.
    adapter = (ROOT / "scripts/dhan_market_data_recovery.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__"' in adapter
    workflow = (ROOT / ".github/workflows/phase-07-dhan-market-data-tests.yml").read_text(encoding="utf-8")
    assert "test_dhan_market_data_recovery.py" in workflow
    assert "live_sample" not in workflow
    assert "DHAN_ACCESS_TOKEN" not in workflow

def main() -> None:
    tests = [
        test_import_does_not_request_network,
        test_missing_secret_stops_before_request,
        test_live_sample_requires_workflow_authorization,
        test_profile_probe_redacts_identity_fields,
        test_profile_probe_blocks_inactive_data_plan,
        test_profile_probe_handles_bad_json_without_echo,
        test_request_url_allowlist_blocks_unregistered_host_before_budget,
        test_request_missing_token_blocks_before_budget,
        test_request_counts_bytes_and_requests,
        test_request_rejects_over_cap_and_counts_overflow_byte,
        test_global_budget_fails_closed,
        test_instrument_mapping_requires_unique_exact_ids,
        test_instrument_mapping_accepts_official_csv_headers,
        test_http_error_returns_status_without_provider_body,
        test_instrument_mapping_rejects_ambiguous_security_id,
        test_windows_are_fixed_and_non_overlapping,
        test_payload_uses_non_inclusive_end_and_resolved_id,
        test_payload_rejects_wide_or_invalid_window,
        test_candle_schema_accepts_aligned_finite_ohlcv,
        test_candle_schema_rejects_mismatched_arrays,
        test_candle_schema_rejects_out_of_window_timestamps,
        test_candle_schema_rejects_duplicate_or_unsorted_timestamps,
        test_candle_schema_rejects_invalid_ohlc,
        test_candle_schema_rejects_nan,
        test_workflow_or_test_suite_does_not_invoke_live_sample,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} Dhan offline regressions")


if __name__ == "__main__":
    main()
