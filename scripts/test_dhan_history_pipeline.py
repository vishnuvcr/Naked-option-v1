#!/usr/bin/env python3
"""Offline/mock-only regressions for the Dhan historical data pipeline."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dhan_history_pipeline", ROOT / "scripts/dhan_history_pipeline.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

CANDLES = {
    "timestamp": [1700000000, 1700000060],
    "open": [100.0, 101.0],
    "high": [102.0, 103.0],
    "low": [99.0, 100.5],
    "close": [101.0, 102.0],
    "volume": [200, 250],
}
DAILY_REQ = {
    "securityId": "13", "exchangeSegment": "IDX_I", "instrument": "INDEX",
    "fromDate": "2023-11-15", "toDate": "2023-11-16", "oi": False,
}


def cache_meta(raw: bytes) -> dict:
    return {
        "http_status": 200,
        "content_type": "application/json",
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_bytes": len(raw),
        "request_count": 1,
        "cumulative_response_bytes": len(raw),
    }

ROLLING = {
    "data": {
        "ce": {
            "timestamp": [1700000000, 1700000060],
            "open": [20.0, 21.0], "high": [22.0, 23.0],
            "low": [19.0, 20.0], "close": [21.0, 22.0],
            "iv": [12.5, 12.7], "volume": [1000, 1200],
            "oi": [5000, 5200], "strike": [22000, 22000],
            "spot": [22010, 22015],
        },
        "pe": None,
    }
}


class ReadTrackedBody(io.BytesIO):
    def __init__(self, initial_bytes: bytes):
        super().__init__(initial_bytes)
        self.read_count = 0

    def read(self, size: int = -1) -> bytes:
        self.read_count += 1
        return super().read(size)


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, headers: dict | None = None):
        self.body = body
        self.status = status
        self.headers = headers or {"Content-Type": "application/json", "Content-Length": str(len(body))}
        self.read_calls = 0
        self.closed = False

    def read(self, n: int) -> bytes:
        self.read_calls += 1
        return self.body[:n]

    def close(self) -> None:
        self.closed = True


class FakeOpener:
    def __init__(self, response_or_error, *, expected_url: str | None = None):
        self.response_or_error = response_or_error
        self.expected_url = expected_url
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.expected_url is not None:
            assert request.full_url == self.expected_url
        if isinstance(self.response_or_error, Exception):
            raise self.response_or_error
        return self.response_or_error


def must_raise(call, expected: str) -> None:
    try:
        call()
    except (ValueError, RuntimeError) as exc:
        assert str(exc) == expected, (str(exc), expected)
    else:
        raise AssertionError(f"expected {expected}")


def test_import_and_cli_are_offline() -> None:
    assert mod.ALLOWED_URLS == {mod.DAILY_URL, mod.INTRADAY_URL, mod.ROLLING_OPTION_URL}
    out = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = out
        assert mod.main() == 0
    finally:
        sys.stdout = old
    state = json.loads(out.getvalue())
    assert state["network_enabled"] is False


def test_request_requires_explicit_live_authorization() -> None:
    budget = mod.RequestBudget()
    calls = []
    must_raise(
        lambda: mod.request_json(
            mod.DAILY_URL, {}, token="dummy", budget=budget,
            opener_factory=lambda: calls.append("opened"),
        ),
        "live_request_not_authorized",
    )
    must_raise(
        lambda: mod.request_json(
            mod.DAILY_URL, DAILY_REQ, token="dummy", budget=budget,
            opener_factory=lambda: calls.append("opened"), live_authorized="true",
        ),
        "live_request_not_authorized",
    )
    assert calls == [] and budget.requests == 0


def test_unregistered_or_unsafe_urls_block_before_request() -> None:
    budget = mod.RequestBudget()
    for url in (
        "https://evil.example/v2/charts/historical",
        "http://api.dhan.co/v2/charts/historical",
        "https://api.dhan.co/v2/profile",
        "https://user@api.dhan.co/v2/charts/historical",
        "https://api.dhan.co/v2/charts/historical?token=x",
    ):
        must_raise(
            lambda url=url: mod.request_json(
                url, {}, token="dummy", budget=budget, live_authorized=True
            ),
            "unregistered_or_unsafe_url",
        )
    assert budget.requests == 0


def test_request_requires_token_and_object_body() -> None:
    b = mod.RequestBudget()
    must_raise(lambda: mod.request_json(mod.DAILY_URL, {}, token="", budget=b, live_authorized=True),
               "missing_or_invalid_dhan_access_token")
    must_raise(lambda: mod.request_json(mod.DAILY_URL, [], token="x", budget=b, live_authorized=True),
               "request_body_must_be_object")
    must_raise(lambda: mod.request_json(mod.DAILY_URL, {}, token="bad\r\nheader", budget=b, live_authorized=True),
               "missing_or_invalid_dhan_access_token")
    assert b.requests == 0


def test_request_posts_only_to_allowlisted_dhan_host_and_redacts_token() -> None:
    payload = {"open": [100], "high": [101], "low": [99], "close": [100.5], "volume": [5], "timestamp": [1700000000]}
    raw = json.dumps(payload).encode()
    response = FakeResponse(raw)
    opener = FakeOpener(response, expected_url=mod.DAILY_URL)
    budget = mod.RequestBudget()
    result, meta, raw_response = mod.request_json(
        mod.DAILY_URL, DAILY_REQ, token="TEST_TOKEN_DO_NOT_LEAK",
        budget=budget, opener_factory=lambda: opener, live_authorized=True, now=100,
    )
    req, timeout = opener.calls[0]
    assert req.get_method() == "POST"
    assert req.get_header("Access-token") == "TEST_TOKEN_DO_NOT_LEAK"
    assert timeout == mod.TIMEOUT_SECONDS
    assert result == payload
    assert raw_response == raw
    assert meta["response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert meta["request_count"] == 1 and meta["response_bytes"] == len(raw)
    assert "TEST_TOKEN_DO_NOT_LEAK" not in json.dumps(meta)
    assert response.closed


def test_redirect_is_rejected_without_reading_error_body_or_following() -> None:
    body = ReadTrackedBody(b"private-provider-error")
    error = urllib.error.HTTPError(
        mod.DAILY_URL, 302, "Found",
        {"Location": "https://other-host.example/private/path", "Set-Cookie": "secret"},
        body,
    )
    opener = FakeOpener(error)
    budget = mod.RequestBudget()
    must_raise(
        lambda: mod.request_json(
            mod.DAILY_URL, DAILY_REQ, token="secret", budget=budget,
            opener_factory=lambda: opener, live_authorized=True, now=100,
        ),
        "dhan_redirect_rejected",
    )
    assert len(opener.calls) == 1
    assert body.read_count == 0
    assert budget.requests == 1 and budget.bytes_read == 0


def test_http_error_does_not_leak_body_or_headers() -> None:
    body = ReadTrackedBody(b"PRIVATE_ACCESS_TOKEN_OR_ACCOUNT")
    error = urllib.error.HTTPError(
        mod.DAILY_URL, 403, "Forbidden",
        {"Content-Type": "application/json", "Authorization": "secret"},
        body,
    )
    b = mod.RequestBudget()
    try:
        mod.request_json(mod.DAILY_URL, DAILY_REQ, token="secret", budget=b,
                         opener_factory=lambda: FakeOpener(error), live_authorized=True, now=100)
    except ValueError as exc:
        assert str(exc) == "dhan_http_status_403"
        assert "PRIVATE" not in str(exc) and "secret" not in str(exc)
    else:
        raise AssertionError("HTTP error accepted")
    assert body.read_count == 0


def test_non_json_content_type_rejected() -> None:
    response = FakeResponse(b"not-json", headers={"Content-Type": "text/html", "Content-Length": "8"})
    must_raise(
        lambda: mod.request_json(
            mod.DAILY_URL, DAILY_REQ, token="x", budget=mod.RequestBudget(),
            opener_factory=lambda: FakeOpener(response), live_authorized=True, now=100,
        ),
        "dhan_unexpected_content_type",
    )
    assert response.read_calls == 0


def test_invalid_content_length_and_oversized_length_rejected_before_read() -> None:
    for length, expected in [("abc", "dhan_invalid_content_length"),
                             (str(mod.MAX_RESPONSE_BYTES + 1), "dhan_response_byte_cap_exceeded")]:
        response = FakeResponse(b"{}", headers={"Content-Type": "application/json", "Content-Length": length})
        must_raise(
            lambda response=response, expected=expected: mod.request_json(
                mod.DAILY_URL, DAILY_REQ, token="x", budget=mod.RequestBudget(),
                opener_factory=lambda: FakeOpener(response), live_authorized=True, now=100,
            ),
            expected,
        )
        assert response.read_calls == 0


def test_cap_plus_one_read_and_global_byte_budget_reject() -> None:
    response = FakeResponse(b"x" * (mod.MAX_RESPONSE_BYTES + 1),
                            headers={"Content-Type": "application/json"})
    must_raise(
        lambda: mod.request_json(
            mod.DAILY_URL, DAILY_REQ, token="x", budget=mod.RequestBudget(),
            opener_factory=lambda: FakeOpener(response), live_authorized=True, now=100,
        ),
        "dhan_response_byte_cap_exceeded",
    )
    assert response.read_calls == 1


def test_bad_json_and_non_object_root_rejected() -> None:
    for raw, expected in [(b"{not-json", "dhan_json_invalid"), (b"[]", "dhan_json_root_not_object")]:
        response = FakeResponse(raw)
        must_raise(
            lambda response=response: mod.request_json(
                mod.DAILY_URL, DAILY_REQ, token="x", budget=mod.RequestBudget(),
                opener_factory=lambda: FakeOpener(response), live_authorized=True, now=100,
            ),
            expected,
        )


def test_request_budget_and_pacing_fail_closed() -> None:
    budget = mod.RequestBudget()
    budget.reserve_request(now=100)
    must_raise(lambda: budget.reserve_request(now=104), "request_budget_exceeded")

    old_max_requests = mod.MAX_REQUESTS
    try:
        mod.MAX_REQUESTS = 3
        pacing_budget = mod.RequestBudget(request_limit=3)
        pacing_budget.reserve_request(now=100)
        must_raise(lambda: pacing_budget.reserve_request(now=102), "request_pacing_limit")
        pacing_budget.reserve_request(now=103)
    finally:
        mod.MAX_REQUESTS = old_max_requests


def test_sample_request_budgets_cannot_be_widened() -> None:
    must_raise(lambda: mod.RequestBudget(request_limit=mod.MAX_REQUESTS + 1),
               "request_budget_limit_invalid")
    must_raise(lambda: mod.RequestBudget(byte_limit=mod.MAX_TOTAL_BYTES + 1),
               "request_byte_budget_limit_invalid")
    budget = mod.RequestBudget()
    budget.request_limit = mod.MAX_REQUESTS + 1
    calls = []
    must_raise(lambda: mod.request_json(
        mod.DAILY_URL, DAILY_REQ, token="not-a-real-token", budget=budget,
        opener_factory=lambda: calls.append("opened"), live_authorized=True,
    ), "request_budget_limit_invalid")
    assert calls == []


def test_candle_arrays_and_ohlc_validate() -> None:
    result = mod.validate_candle_payload(CANDLES)
    assert result["row_count"] == 2 and result["first_timestamp"] == 1700000000


def test_all_additional_response_arrays_must_align() -> None:
    must_raise(lambda: mod.validate_candle_payload({**CANDLES, "open_interest": [1]}),
               "candle_array_length_mismatch_open_interest")


def test_candle_missing_unequal_and_empty_arrays_rejected() -> None:
    for bad, expected in [
        ({k: v for k, v in CANDLES.items() if k != "close"}, "candle_array_missing_close"),
        ({**CANDLES, "close": [101]}, "candle_array_length_mismatch"),
        ({**CANDLES, "timestamp": [] , "open": [], "high": [], "low": [], "close": [], "volume": []},
         "candle_array_empty"),
    ]:
        must_raise(lambda bad=bad, expected=expected: mod.validate_candle_payload(bad), expected)


def test_candle_noninteger_or_nonpositive_timestamps_rejected() -> None:
    for stamps in ([1700000000.5, 1700000060], [1700000000, 0]):
        must_raise(lambda stamps=stamps: mod.validate_candle_payload({**CANDLES, "timestamp": stamps}),
                   "candle_timestamp_invalid")


def test_candle_duplicate_or_out_of_order_timestamps_rejected() -> None:
    for stamps in ([1700000000, 1700000000], [1700000060, 1700000000]):
        must_raise(lambda stamps=stamps: mod.validate_candle_payload({**CANDLES, "timestamp": stamps}),
                   "candle_timestamps_not_strictly_increasing")


def test_candle_nonfinite_negative_and_bad_ohlc_rejected() -> None:
    must_raise(lambda: mod.validate_candle_payload({**CANDLES, "open": [float("nan"), 101]}),
               "candle_value_nonfinite_open")
    must_raise(lambda: mod.validate_candle_payload({**CANDLES, "volume": [10, -1]}),
               "candle_value_negative_volume")
    must_raise(lambda: mod.validate_candle_payload({**CANDLES, "high": [98, 103]}),
               "candle_ohlc_inconsistent_row_0")

def test_optional_open_interest_values_are_fully_validated() -> None:
    for values, expected in [
        ([10, -1], "candle_value_negative_open_interest"),
        ([10, float("nan")], "candle_value_nonfinite_open_interest"),
        ([10, "bad"], "candle_value_invalid_open_interest"),
    ]:
        must_raise(lambda values=values, expected=expected: mod.validate_candle_payload(
            {**CANDLES, "open_interest": values}
        ), expected)
    must_raise(lambda: mod.validate_candle_payload(
        {**CANDLES, "open_interest": "not-an-array"}
    ), "candle_array_invalid_open_interest")


def test_rolling_option_arrays_and_fields_validate() -> None:
    result = mod.validate_rolling_option_payload(ROLLING, option_type="CALL")
    assert result["row_count"] == 2 and result["side"] == "ce"
    assert result["fields"][0] == "timestamp"


def test_rolling_option_missing_side_or_misaligned_fields_rejected() -> None:
    must_raise(lambda: mod.validate_rolling_option_payload(ROLLING, option_type="PUT"),
               "rolling_option_side_missing")
    wrong = json.loads(json.dumps(ROLLING))
    wrong["data"]["ce"]["iv"] = [12.5]
    must_raise(lambda: mod.validate_rolling_option_payload(wrong, option_type="CALL"),
               "rolling_option_array_length_mismatch")


def test_rolling_option_invalid_type_negative_iv_and_bad_json_shape_rejected() -> None:
    must_raise(lambda: mod.validate_rolling_option_payload(ROLLING, option_type="BOTH"),
               "rolling_option_type_invalid")
    wrong = json.loads(json.dumps(ROLLING))
    wrong["data"]["ce"]["iv"][0] = -1
    must_raise(lambda: mod.validate_rolling_option_payload(wrong, option_type="CALL"),
               "rolling_option_value_invalid_iv")
    must_raise(lambda: mod.validate_rolling_option_payload({"data": []}, option_type="CALL"),
               "rolling_option_data_missing")


def test_daily_and_intraday_request_windows_validate() -> None:
    daily = {"securityId": "13", "exchangeSegment": "IDX_I", "instrument": "INDEX",
             "fromDate": "2024-01-01", "toDate": "2024-01-11", "oi": False}
    assert mod.validate_request_window(mod.DAILY_URL, daily)["source"] == "daily_candles"
    intraday = {"securityId": "13", "exchangeSegment": "IDX_I", "instrument": "INDEX",
                "interval": "1", "fromDate": "2024-01-01 09:15:00",
                "toDate": "2024-03-30 15:30:00"}
    assert mod.validate_request_window(mod.INTRADAY_URL, intraday)["interval"] == "1"
    too_long = {**intraday, "toDate": "2024-04-02 15:30:00"}
    must_raise(lambda: mod.validate_request_window(mod.INTRADAY_URL, too_long),
               "date_range_exceeds_documented_cap")


def test_expired_option_request_window_and_allowed_fields_validate() -> None:
    body = {
        "exchangeSegment": "NSE_FNO", "interval": "1", "securityId": 13,
        "instrument": "OPTIDX", "expiryFlag": "WEEK", "expiryCode": 1,
        "strike": "ATM", "drvOptionType": "CALL",
        "requiredData": ["open", "high", "low", "close", "iv", "volume", "oi", "strike", "spot"],
        "fromDate": "2024-01-01", "toDate": "2024-01-30",
    }
    assert mod.validate_request_window(mod.ROLLING_OPTION_URL, body)["source"] == "rolling_expired_options"
    exactly_30_days = {**body, "toDate": "2024-01-31"}
    assert mod.validate_request_window(mod.ROLLING_OPTION_URL, exactly_30_days)["source"] == "rolling_expired_options"
    for end, expected in [("2024-02-01", "date_range_exceeds_documented_cap"),
                          ("2023-12-30", "date_range_not_increasing")]:
        must_raise(lambda end=end: mod.validate_request_window(
            mod.ROLLING_OPTION_URL, {**body, "toDate": end}
        ), expected)
    must_raise(lambda: mod.validate_request_window(
        mod.ROLLING_OPTION_URL, {**body, "requiredData": ["token"]}
    ), "rolling_option_required_data_unrecognized")


def test_security_id_must_be_positive_scalar() -> None:
    for value in ([13], {"id": 13}, True, 0, "0", ""):
        must_raise(lambda value=value: mod.validate_request_window(
            mod.DAILY_URL, {**DAILY_REQ, "securityId": value}
        ), "daily_request_security_id_invalid")


def test_daily_oi_flag_must_be_boolean() -> None:
    must_raise(lambda: mod.validate_request_window(mod.DAILY_URL, {**DAILY_REQ, "oi": 0}),
               "daily_request_oi_invalid")


def test_daily_window_has_conservative_365_day_exclusive_cap() -> None:
    exactly_365 = {**DAILY_REQ, "fromDate": "2023-01-01", "toDate": "2024-01-01"}
    assert mod.validate_request_window(mod.DAILY_URL, exactly_365)["source"] == "daily_candles"
    too_long = {**exactly_365, "toDate": "2024-01-02"}
    must_raise(lambda: mod.validate_request_window(mod.DAILY_URL, too_long),
               "date_range_exceeds_documented_cap")


def test_timezone_offsets_are_rejected_for_intraday_windows() -> None:
    intraday = {"securityId": "13", "exchangeSegment": "IDX_I", "instrument": "INDEX",
                "interval": "1", "fromDate": "2024-01-01T09:15:00+05:30",
                "toDate": "2024-01-02T15:30:00+05:30"}
    must_raise(lambda: mod.validate_request_window(mod.INTRADAY_URL, intraday),
               "datetime_timezone_not_allowed")


def test_rolling_option_strike_cannot_be_boolean() -> None:
    body = {
        "exchangeSegment": "NSE_FNO", "interval": "1", "securityId": 13,
        "instrument": "OPTIDX", "expiryFlag": "WEEK", "expiryCode": 1,
        "strike": True, "drvOptionType": "CALL",
        "requiredData": ["open", "high", "low", "close", "volume"],
        "fromDate": "2024-01-01", "toDate": "2024-01-30",
    }
    must_raise(lambda: mod.validate_request_window(mod.ROLLING_OPTION_URL, body),
               "rolling_option_strike_invalid")


def test_rolling_option_validator_handles_custom_required_fields() -> None:
    minimal = {
        "data": {"ce": {key: ROLLING["data"]["ce"][key]
                          for key in ("timestamp", "open", "high", "low", "close", "volume")}}
    }
    result = mod.validate_rolling_option_payload(
        minimal, option_type="CALL",
        required_fields=("open", "high", "low", "close", "volume"),
    )
    assert result["row_count"] == 2

def test_rolling_option_empty_unrequested_optional_arrays_are_allowed() -> None:
    published_shape = json.loads(json.dumps(ROLLING))
    for field in ("iv", "oi", "strike", "spot"):
        published_shape["data"]["ce"][field] = []
    result = mod.validate_rolling_option_payload(
        published_shape, option_type="CALL",
        required_fields=("open", "high", "low", "close", "volume"),
    )
    assert result["row_count"] == 2
    must_raise(lambda: mod.validate_rolling_option_payload(
        published_shape, option_type="CALL",
        required_fields=("open", "high", "low", "close", "volume", "iv"),
    ), "rolling_option_array_length_mismatch")


def test_rolling_option_offset_strike_is_blocked_in_initial_sample_scope() -> None:
    body = {
        "exchangeSegment": "NSE_FNO", "interval": "1", "securityId": 13,
        "instrument": "OPTIDX", "expiryFlag": "WEEK", "expiryCode": 1,
        "strike": "ATM+999", "drvOptionType": "CALL",
        "requiredData": ["open", "high", "low", "close", "volume"],
        "fromDate": "2024-01-01", "toDate": "2024-01-31",
    }
    must_raise(lambda: mod.validate_request_window(mod.ROLLING_OPTION_URL, body),
               "rolling_option_strike_invalid")


def test_cache_rejects_response_timestamps_outside_requested_window() -> None:
    raw = json.dumps(CANDLES, sort_keys=True).encode()
    valid = mod.validate_candle_payload(CANDLES)
    outside = {**DAILY_REQ, "fromDate": "2024-01-01", "toDate": "2024-01-03"}
    with tempfile.TemporaryDirectory() as temp:
        must_raise(lambda: mod.atomic_cache_bundle(
            raw, valid, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata=cache_meta(raw), request_parameters=outside,
            fetched_at_utc="2026-10-10T00:00:00Z"
        ), "cache_timestamp_outside_requested_window")
        assert list(pathlib.Path(temp).iterdir()) == []

def test_daily_exclusive_to_date_rejected_in_cache() -> None:
    last_stamp = 1700086400  # 2023-11-16 03:43 IST; equals excluded toDate.
    payload = {**CANDLES, "timestamp": [1700000000, last_stamp]}
    raw = json.dumps(payload, sort_keys=True).encode()
    valid = mod.validate_candle_payload(payload)
    with tempfile.TemporaryDirectory() as temp:
        must_raise(lambda: mod.atomic_cache_bundle(
            raw, valid, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata=cache_meta(raw), request_parameters=DAILY_REQ,
            fetched_at_utc="2026-10-10T00:00:00Z"
        ), "cache_timestamp_outside_requested_window")
        assert list(pathlib.Path(temp).iterdir()) == []


def test_cache_bundle_rejects_invalid_json_or_validation() -> None:
    with tempfile.TemporaryDirectory() as temp:
        must_raise(lambda: mod.atomic_cache_bundle(
            b"not-json", {}, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata={}, request_parameters={}, fetched_at_utc="2026-10-10T00:00:00Z"
        ), "cache_response_json_invalid")
        must_raise(lambda: mod.atomic_cache_bundle(
            b"{}", {}, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata={}, request_parameters={}, fetched_at_utc="2026-10-10T00:00:00Z"
        ), "cache_response_json_root_invalid")


def test_request_unknown_fields_are_rejected_before_network() -> None:
    unknown = {**DAILY_REQ, "authToken": "must-not-be-sent"}
    must_raise(lambda: mod.validate_request_window(mod.DAILY_URL, unknown),
               "request_fields_unrecognized")


def test_cache_recomputes_validation_report_before_write() -> None:
    raw = json.dumps(CANDLES, sort_keys=True).encode()
    valid = mod.validate_candle_payload(CANDLES)
    tampered_validation = {**valid, "row_count": 99}
    with tempfile.TemporaryDirectory() as temp:
        must_raise(lambda: mod.atomic_cache_bundle(
            raw, tampered_validation, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata={}, request_parameters=DAILY_REQ,
            fetched_at_utc="2026-10-10T00:00:00Z"
        ), "cache_validation_report_mismatch")
        assert list(pathlib.Path(temp).iterdir()) == []


def test_invalid_request_windows_and_intervals_rejected() -> None:
    intraday = {"securityId": "13", "exchangeSegment": "IDX_I", "instrument": "INDEX",
                "interval": "7", "fromDate": "2024-01-01 09:15:00",
                "toDate": "2024-01-02 15:30:00"}
    must_raise(lambda: mod.validate_request_window(mod.INTRADAY_URL, intraday), "intraday_interval_invalid")
    must_raise(lambda: mod.validate_request_window(mod.DAILY_URL, {"fromDate": "2024-01-01"}),
               "daily_request_instrument_fields_missing")


def test_atomic_cache_bundle_hashes_and_preserves_content() -> None:
    raw = json.dumps(CANDLES, sort_keys=True).encode()
    validation = mod.validate_candle_payload(CANDLES)
    with tempfile.TemporaryDirectory() as temp:
        report = mod.atomic_cache_bundle(
            raw, validation, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata=cache_meta(raw),
            request_parameters=DAILY_REQ,
            fetched_at_utc="2026-10-10T00:00:00Z",
        )
        assert report["status"] == "CACHE_CREATED"
        folder = pathlib.Path(report["path"])
        assert hashlib.sha256((folder / "response.json").read_bytes()).hexdigest() == report["sha256"]
        manifest = json.loads((folder / "manifest.json").read_text())
        assert "access-token" not in json.dumps(manifest).lower()
        again = mod.atomic_cache_bundle(
            raw, validation, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata=cache_meta(raw),
            request_parameters=DAILY_REQ,
            fetched_at_utc="2026-10-10T00:00:00Z",
        )
        assert again["status"] == "CACHE_ALREADY_PRESENT"


def test_cache_rejects_unapproved_host_and_credential_key() -> None:
    raw = json.dumps(CANDLES, sort_keys=True).encode()
    valid = mod.validate_candle_payload(CANDLES)
    with tempfile.TemporaryDirectory() as temp:
        must_raise(lambda: mod.atomic_cache_bundle(
            raw, valid, cache_root=temp, source_url="https://evil.example/data",
            request_metadata={}, request_parameters={}, fetched_at_utc="2026-10-10T00:00:00Z"
        ), "cache_source_url_unregistered")
        must_raise(lambda: mod.atomic_cache_bundle(
            raw, valid, cache_root=temp, source_url=mod.DAILY_URL,
            request_metadata=cache_meta(raw), request_parameters={"auth_token": "should-not-persist"},
            fetched_at_utc="2026-10-10T00:00:00Z"
        ), "cache_manifest_contains_forbidden_key")


TESTS = [value for name, value in globals().copy().items()
         if name.startswith("test_") and callable(value)]
for test in TESTS:
    test()
print(f"PASS {len(TESTS)} Dhan history pipeline offline/mock tests")
