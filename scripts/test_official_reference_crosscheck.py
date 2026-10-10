#!/usr/bin/env python3
"""Offline mocked regressions for the bounded official-source cross-check adapter."""
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
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("official_reference_crosscheck", SCRIPTS / "official_reference_crosscheck.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

runner_spec = importlib.util.spec_from_file_location("run_official_reference_crosscheck", SCRIPTS / "run_official_reference_crosscheck.py")
runner = importlib.util.module_from_spec(runner_spec)
sys.modules[runner_spec.name] = runner
assert runner_spec.loader is not None
runner_spec.loader.exec_module(runner)

CSV_HEADER = (
    "SEM_SMST_SECURITY_ID,SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_INSTRUMENT_NAME,"
    "SEM_TRADING_SYMBOL,SM_SYMBOL_NAME,SEM_CUSTOM_SYMBOL,SEM_EXCH_INSTRUMENT_TYPE\n"
)
GOOD_CSV = (CSV_HEADER + "13,NSE,E,INDEX,NIFTY,NIFTY 50,NIFTY 50,IDX\n").encode()
GOOD_NIFTY_ROW = {
    "INDEX_NAME": "NIFTY 50",
    "HistoricalDate": "02 Jan 2024",
    "OPEN": "21751.35",
    "HIGH": "21755.60",
    "LOW": "21555.65",
    "CLOSE": "21665.80",
}


def nifty_bytes(row: dict | None = None) -> bytes:
    return json.dumps({"d": json.dumps([row or GOOD_NIFTY_ROW])}).encode()


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/json", content_length: str | None = None):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        if content_length is not None:
            self.headers["Content-Length"] = content_length
        else:
            self.headers["Content-Length"] = str(len(body))
        self.read_calls = 0
        self.closed = False

    def read(self, size: int) -> bytes:
        self.read_calls += 1
        return self.body[:size]

    def close(self):
        self.closed = True


class TrackedErrorBody(io.BytesIO):
    def __init__(self, data: bytes):
        super().__init__(data)
        self.read_count = 0

    def read(self, size: int = -1):
        self.read_count += 1
        return super().read(size)


class FakeOpener:
    def __init__(self, result, *, expected_url: str | None = None, expected_method: str | None = None, expected_body: bytes | None = None):
        self.result = result
        self.expected_url = expected_url
        self.expected_method = expected_method
        self.expected_body = expected_body
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.expected_url is not None:
            assert request.full_url == self.expected_url
        if self.expected_method is not None:
            assert request.get_method() == self.expected_method
        if self.expected_body is not None:
            assert request.data == self.expected_body
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def must_raise(call, expected: str) -> None:
    try:
        call()
    except ValueError as exc:
        assert str(exc) == expected, (str(exc), expected)
    else:
        raise AssertionError(f"expected {expected}")


def test_import_cli_and_scope_are_offline() -> None:
    assert mod.MAX_SOURCE_REQUESTS == 2
    assert mod.EXPECTED_DATE == "2024-01-02"
    assert mod.NIFTY_INDICES_URL == "https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString"
    assert mod.DHAN_COMPACT_MASTER_URL == "https://images.dhan.co/api-data/api-scrip-master.csv"
    assert mod.main() == 0


def test_nifty_reference_double_encoded_json_parses_exact_date_and_values() -> None:
    row = mod.parse_nifty_indices_response(nifty_bytes())
    assert row == {
        "index_name": "NIFTY 50",
        "date": "2024-01-02",
        "open": "21751.35",
        "high": "21755.60",
        "low": "21555.65",
        "close": "21665.80",
    }


def test_nifty_parser_rejects_invalid_envelope_json_rows_and_date() -> None:
    cases = [
        (b"{bad", "nifty_reference_json_invalid"),
        (b'{"wrong":[]}', "nifty_reference_envelope_invalid"),
        (b'{"d":"{bad"}', "nifty_reference_data_json_invalid"),
        (json.dumps({"d": {}}).encode(), "nifty_reference_rows_invalid"),
        (json.dumps({"d": "[]"}).encode(), "nifty_reference_row_count_not_one"),
        (json.dumps({"d": json.dumps([GOOD_NIFTY_ROW, GOOD_NIFTY_ROW])}).encode(), "nifty_reference_row_count_not_one"),
    ]
    for raw, expected in cases:
        must_raise(lambda raw=raw: mod.parse_nifty_indices_response(raw), expected)
    wrong_date = {**GOOD_NIFTY_ROW, "HistoricalDate": "03 Jan 2024"}
    must_raise(lambda: mod.parse_nifty_indices_response(nifty_bytes(wrong_date)), "nifty_reference_date_mismatch")
    wrong_index = {**GOOD_NIFTY_ROW, "INDEX_NAME": "NIFTY BANK"}
    must_raise(lambda: mod.parse_nifty_indices_response(nifty_bytes(wrong_index)), "nifty_reference_index_name_mismatch")


def test_nifty_parser_rejects_nonfinite_and_inconsistent_ohlc() -> None:
    for field, value, expected in [
        ("OPEN", "NaN", "nifty_reference_numeric_invalid_open"),
        ("HIGH", "not-a-number", "nifty_reference_numeric_invalid_high"),
        ("LOW", "21760.00", "nifty_reference_ohlc_inconsistent"),
    ]:
        row = {**GOOD_NIFTY_ROW, field: value}
        must_raise(lambda row=row: mod.parse_nifty_indices_response(nifty_bytes(row)), expected)


def test_compact_instrument_mapping_uses_compact_segment_not_api_enum() -> None:
    parsed = mod.parse_dhan_instrument_mapping(GOOD_CSV)
    assert parsed["security_id"] == "13"
    assert parsed["exchange"] == "NSE"
    assert parsed["compact_segment"] == "E"
    assert parsed["instrument_name"] == "INDEX"
    assert parsed["trading_symbol"] == "NIFTY"
    assert parsed["symbol_name"] == "NIFTY 50"
    assert "csv_sha256" in parsed and parsed["csv_sha256"] == hashlib.sha256(GOOD_CSV).hexdigest()


def test_mapping_rejects_missing_ambiguous_or_wrong_candidates() -> None:
    missing = (CSV_HEADER + "99,NSE,E,INDEX,NIFTY,NIFTY 50,NIFTY 50,IDX\n").encode()
    must_raise(lambda: mod.parse_dhan_instrument_mapping(missing), "dhan_mapping_row_count_not_one")
    duplicate = (GOOD_CSV.decode() + "13,NSE,E,INDEX,NIFTY,NIFTY 50,NIFTY 50,IDX\n").encode()
    must_raise(lambda: mod.parse_dhan_instrument_mapping(duplicate), "csv_duplicate_segment_security_id")
    for row, expected in [
        ("13,BSE,E,INDEX,NIFTY,NIFTY 50,NIFTY 50,IDX", "dhan_mapping_exchange_mismatch"),
        ("13,NSE,E,EQUITY,NIFTY,NIFTY 50,NIFTY 50,EQ", "dhan_mapping_instrument_mismatch"),
        ("13,NSE,E,INDEX,BANKNIFTY,BANK NIFTY,BANK NIFTY,IDX", "dhan_mapping_symbol_mismatch"),
        ("13,NSE,IDX_I,INDEX,NIFTY,NIFTY 50,NIFTY 50,IDX", "dhan_mapping_compact_segment_invalid"),
        ("13,NSE,E,INDEX,INDIAVIX,INDIA VIX,INDIA VIX,IDX", "dhan_mapping_symbol_mismatch"),
        ("13,NSE,E,INDEX,NIFTY,OTHER,OTHER,IDX", "dhan_mapping_symbol_name_mismatch"),
    ]:
        raw = (CSV_HEADER + row + "\n").encode()
        must_raise(lambda raw=raw: mod.parse_dhan_instrument_mapping(raw), expected)


def test_exact_ohlc_comparison_matches_and_flags_each_mismatch() -> None:
    official = mod.parse_nifty_indices_response(nifty_bytes())
    same = mod.compare_ohlc(official)
    assert same["status"] == "MATCH" and same["mismatch_count"] == 0
    wrong = mod.compare_ohlc(official, {**mod.EXPECTED_DHAN_ROW, "close": "21665.81"})
    assert wrong["status"] == "MISMATCH" and wrong["mismatch_count"] == 1
    assert wrong["mismatches"]["close"] == {"dhan": "21665.81", "official": "21665.80"}
    assert same["volume_crosschecked"] is False


def test_request_once_sends_exact_post_and_hashes_response() -> None:
    raw = nifty_bytes()
    response = FakeResponse(raw, content_type="application/json; charset=utf-8")
    body = mod.make_nifty_request_body()
    opener = FakeOpener(response, expected_url=mod.NIFTY_INDICES_URL, expected_method="POST", expected_body=body)
    got, meta = mod.request_once(
        source="nifty_indices", url=mod.NIFTY_INDICES_URL, allowed_url=mod.NIFTY_INDICES_URL,
        method="POST", body=body,
        headers={"Content-Type": "application/json; charset=UTF-8", "X-Requested-With": "XMLHttpRequest", "Referer": mod.NIFTY_INDICES_REFERER},
        allowed_content_types=mod.CONTENT_TYPE_NIFTY, byte_cap=mod.NIFTY_MAX_RESPONSE_BYTES,
        timeout_seconds=20, opener_factory=lambda: opener,
    )
    assert got == raw and len(opener.calls) == 1 and response.closed
    req, timeout = opener.calls[0]
    assert timeout == 20 and req.get_header("Referer") == mod.NIFTY_INDICES_REFERER
    assert meta["response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert meta["request_count"] == 1 and meta["retry_count"] == 0 and meta["redirect_followed"] is False


def test_request_once_sends_csv_get_without_credentials() -> None:
    response = FakeResponse(GOOD_CSV, content_type="text/csv; charset=utf-8")
    opener = FakeOpener(response, expected_url=mod.DHAN_COMPACT_MASTER_URL, expected_method="GET")
    raw, meta = mod.request_once(
        source="dhan_instrument_master", url=mod.DHAN_COMPACT_MASTER_URL, allowed_url=mod.DHAN_COMPACT_MASTER_URL,
        method="GET", body=None, headers={"Accept": "text/csv"}, allowed_content_types=mod.CONTENT_TYPE_CSV,
        byte_cap=mod.MAX_CSV_BYTES, timeout_seconds=20, opener_factory=lambda: opener,
    )
    req, _ = opener.calls[0]
    header_names = {k.lower() for k, _ in req.header_items()}
    assert not header_names.intersection({"authorization", "access-token", "cookie", "dhanclientid"})
    assert raw == GOOD_CSV and meta["request_count"] == 1 and meta["retry_count"] == 0


def test_request_once_fails_closed_on_unsafe_urls_methods_and_credentials() -> None:
    base = dict(source="nifty_indices", allowed_url=mod.NIFTY_INDICES_URL, method="POST", body=b"{}", headers={},
                allowed_content_types=mod.CONTENT_TYPE_NIFTY, byte_cap=512, timeout_seconds=20,
                opener_factory=lambda: (_ for _ in ()).throw(AssertionError("opener must not be created")))
    for url in ("http://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString",
                "https://evil.example/data", mod.NIFTY_INDICES_URL + "?x=1", mod.NIFTY_INDICES_URL + "/extra"):
        must_raise(lambda url=url: mod.request_once(url=url, **base), "source_url_not_allowlisted")
    must_raise(lambda: mod.request_once(url=mod.NIFTY_INDICES_URL, **{**base, "source":"unknown"}),
               "source_name_invalid")
    must_raise(lambda: mod.request_once(url=mod.NIFTY_INDICES_URL, **{**base,"headers":{"Authorization":"x"}}),
               "source_credentials_forbidden")
    must_raise(lambda: mod.request_once(url=mod.NIFTY_INDICES_URL, **{**base,"headers":{"access-token":"secret"}}),
               "source_credentials_forbidden")


def test_request_once_rejects_redirect_without_reading_provider_body() -> None:
    body = TrackedErrorBody(b"DO_NOT_READ_OR_SAVE")
    err = urllib.error.HTTPError(mod.NIFTY_INDICES_URL, 302, "Found", {"Location":"https://evil.example/"}, body)
    opener = FakeOpener(err)
    must_raise(lambda: mod.request_once(
        source="nifty_indices",url=mod.NIFTY_INDICES_URL,allowed_url=mod.NIFTY_INDICES_URL,method="POST",body=b"{}",
        headers={},allowed_content_types=mod.CONTENT_TYPE_NIFTY,byte_cap=512,timeout_seconds=20,
        opener_factory=lambda: opener
    ), "nifty_indices_redirect_rejected")
    assert len(opener.calls) == 1 and body.read_count == 0


def test_request_once_rejects_bad_status_type_length_and_byte_cap() -> None:
    def make(response):
        return lambda: mod.request_once(
            source="nifty_indices",url=mod.NIFTY_INDICES_URL,allowed_url=mod.NIFTY_INDICES_URL,
            method="POST",body=b"{}",headers={},allowed_content_types=mod.CONTENT_TYPE_NIFTY,
            byte_cap=8,timeout_seconds=20,opener_factory=lambda: FakeOpener(response)
        )
    must_raise(make(FakeResponse(b"{}", status=204)), "nifty_indices_http_status_invalid")
    must_raise(make(FakeResponse(b"<html/>", content_type="text/html")), "nifty_indices_content_type_invalid")
    must_raise(make(FakeResponse(b"{}", content_length="bad")), "nifty_indices_content_length_invalid")
    must_raise(make(FakeResponse(b"123456789")), "nifty_indices_byte_cap_exceeded")
    must_raise(make(FakeResponse(b"{}xx", content_length="2")), "nifty_indices_content_length_mismatch")


def test_request_once_rejects_http_errors_and_timeouts_safely() -> None:
    error_body = TrackedErrorBody(b"SECRET_ERROR_BODY")
    forbidden = urllib.error.HTTPError(mod.DHAN_COMPACT_MASTER_URL,403,"Forbidden",{"Content-Type":"text/plain"},error_body)
    must_raise(lambda: mod.request_once(
        source="dhan_instrument_master",url=mod.DHAN_COMPACT_MASTER_URL,allowed_url=mod.DHAN_COMPACT_MASTER_URL,
        method="GET",body=None,headers={},allowed_content_types=mod.CONTENT_TYPE_CSV,byte_cap=100,timeout_seconds=20,
        opener_factory=lambda: FakeOpener(forbidden)
    ),"dhan_instrument_master_http_status_403")
    assert error_body.read_count == 0
    must_raise(lambda: mod.request_once(
        source="dhan_instrument_master",url=mod.DHAN_COMPACT_MASTER_URL,allowed_url=mod.DHAN_COMPACT_MASTER_URL,
        method="GET",body=None,headers={},allowed_content_types=mod.CONTENT_TYPE_CSV,byte_cap=100,timeout_seconds=20,
        opener_factory=lambda: FakeOpener(TimeoutError("secret timeout"))
    ),"dhan_instrument_master_timeout")


def test_runner_refuses_to_run_without_outer_authorization() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = pathlib.Path(folder)
        cache_root = root / "cache"
        report_path = root / "safe-report.json"
        factory_calls = []
        def forbidden_factory():
            factory_calls.append(True)
            raise AssertionError("network opener must not be constructed")
        code = runner.run_crosscheck(
            env={},
            opener_factory=forbidden_factory,
            manifest_path=root / "missing-manifest.json",
            approval_path=root / "missing-approval.json",
            cache_root=cache_root,
            report_path=report_path,
        )
        assert code == 1
        assert factory_calls == []
        assert not cache_root.exists()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["failure_code"] == "crosscheck_live_request_not_authorized"
        assert report["request_count"] == 0
        assert report["cache_created"] is False
        assert report["data_accepted_for_prediction"] is False


def _write_test_spent_gate(root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    source_specs = [
        {
            "source": "nifty_indices",
            "url": mod.NIFTY_INDICES_URL,
            "method": "POST",
            "request_count_max": 1,
            "response_bytes_max": mod.NIFTY_MAX_RESPONSE_BYTES,
            "timeout_seconds": mod.NIFTY_TIMEOUT_SECONDS,
            "redirect_follow_allowed": False,
            "retry_allowed": False,
            "credential_allowed": False,
        },
        {
            "source": "dhan_instrument_master",
            "url": mod.DHAN_COMPACT_MASTER_URL,
            "method": "GET",
            "request_count_max": 1,
            "response_bytes_max": mod.MAX_CSV_BYTES,
            "timeout_seconds": mod.DHAN_MASTER_TIMEOUT_SECONDS,
            "redirect_follow_allowed": False,
            "retry_allowed": False,
            "credential_allowed": False,
        },
    ]
    authorization = {
        "scope_id": runner.SCOPE_ID,
        "source_specs": source_specs,
        "expected_date": mod.EXPECTED_DATE,
        "expected_dhan_row": mod.EXPECTED_DHAN_ROW,
        "expected_mapping": mod.EXPECTED_MAPPING,
    }
    canonical = json.dumps(
        authorization, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    authorization_hash = hashlib.sha256(canonical).hexdigest()
    manifest = {
        "status": "PROPOSED",
        "decision": "AWAITING_INDEPENDENT_MANIFEST_REVIEW",
        "authorization": authorization,
        "authorization_sha256": authorization_hash,
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\\n").encode("utf-8")
    manifest_path = root / "manifest.json"
    approval_path = root / "approval.json"
    manifest_path.write_bytes(manifest_bytes)
    approval = {
        "status": "SPENT",
        "decision": "SPENT_BEFORE_SOURCE_REQUEST",
        "scope_id": runner.SCOPE_ID,
        "authorized_scope_id": runner.SCOPE_ID,
        "request_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "approved_authorization_sha256": authorization_hash,
        "spent_from_commit": "a" * 40,
    }
    approval_path.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\\n", encoding="utf-8")
    return manifest_path, approval_path


class SequenceOpenerFactory:
    def __init__(self, responses):
        self.responses = list(responses)
        self.openers = []

    def __call__(self):
        assert self.responses, "unexpected extra source request"
        result = self.responses.pop(0)
        if isinstance(result, tuple):
            response, url, method, body = result
            opener = FakeOpener(response, expected_url=url, expected_method=method, expected_body=body)
        else:
            opener = FakeOpener(result)
        self.openers.append(opener)
        return opener


def _good_nifty_response() -> FakeResponse:
    return FakeResponse(nifty_bytes(), content_type="application/json; charset=utf-8")


def _good_csv_response() -> FakeResponse:
    return FakeResponse(GOOD_CSV, content_type="text/csv; charset=utf-8")


def test_runner_success_fetches_exactly_two_sources_and_caches_atomically() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = pathlib.Path(folder)
        manifest_path, approval_path = _write_test_spent_gate(root)
        factory = SequenceOpenerFactory([
            (_good_nifty_response(), mod.NIFTY_INDICES_URL, "POST", mod.make_nifty_request_body()),
            (_good_csv_response(), mod.DHAN_COMPACT_MASTER_URL, "GET", None),
        ])
        cache_root = root / "cache"
        report_path = root / "report.json"
        result = runner.run_crosscheck(
            env={"OFFICIAL_CROSSCHECK_AUTHORIZED": "1"},
            opener_factory=factory,
            manifest_path=manifest_path,
            approval_path=approval_path,
            cache_root=cache_root,
            report_path=report_path,
            fetched_at_utc="2026-10-10T00:00:00Z",
        )
        assert result == 0
        assert len(factory.openers) == 2 and factory.responses == []
        observed = [opener.calls[0][0] for opener in factory.openers]
        assert observed[0].full_url == mod.NIFTY_INDICES_URL and observed[0].get_method() == "POST"
        assert observed[0].data == mod.make_nifty_request_body()
        assert observed[1].full_url == mod.DHAN_COMPACT_MASTER_URL and observed[1].get_method() == "GET"
        for request in observed:
            headers = {key.lower() for key, _ in request.header_items()}
            assert not headers.intersection({"authorization", "access-token", "cookie", "dhanclientid"})
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["status"] == "OFFICIAL_CROSSCHECK_MATCHED"
        assert report["request_count"] == 2
        assert report["retry_count"] == 0 and report["redirect_followed"] is False
        assert report["cache_created"] is True
        assert report["volume_crosschecked"] is False
        assert report["data_accepted_for_prediction"] is False
        bundles = [p for p in cache_root.iterdir() if p.is_dir()]
        assert len(bundles) == 1
        bundle = bundles[0]
        assert (bundle / "nifty_indices_response.json").read_bytes() == nifty_bytes()
        assert (bundle / "dhan_instrument_master.csv").read_bytes() == GOOD_CSV
        bundle_manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        assert bundle_manifest["data_accepted_for_prediction"] is False
        assert bundle_manifest["model_fitting_authorized"] is False
        assert bundle_manifest["holdout_access_authorized"] is False


def test_runner_never_creates_partial_cache_if_second_source_or_comparison_fails() -> None:
    bad_row = {**GOOD_NIFTY_ROW, "CLOSE": "21665.81"}
    scenarios = [
        ([ _good_nifty_response(), FakeResponse(GOOD_CSV, content_type="text/csv") ], "official_nifty_ohlc_mismatch"),
        ([ _good_nifty_response(), urllib.error.HTTPError(mod.DHAN_COMPACT_MASTER_URL, 403, "Forbidden", {"Content-Type": "text/plain"}, TrackedErrorBody(b"DO_NOT_SAVE")) ], "dhan_instrument_master_http_status_403"),
        ([ FakeResponse(nifty_bytes(bad_row), content_type="application/json"), FakeResponse(GOOD_CSV, content_type="text/csv") ], "official_nifty_ohlc_mismatch"),
    ]
    # First scenario is a mismatch expressed via a response with a valid schema.
    scenarios[0][0][0] = FakeResponse(nifty_bytes(bad_row), content_type="application/json")
    for responses, failure in scenarios:
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            manifest_path, approval_path = _write_test_spent_gate(root)
            factory = SequenceOpenerFactory(responses)
            cache_root = root / "cache"
            report_path = root / "report.json"
            code = runner.run_crosscheck(
                env={"OFFICIAL_CROSSCHECK_AUTHORIZED": "1"},
                opener_factory=factory,
                manifest_path=manifest_path,
                approval_path=approval_path,
                cache_root=cache_root,
                report_path=report_path,
                fetched_at_utc="2026-10-10T00:00:00Z",
            )
            assert code == 1
            assert not cache_root.exists()
            report = json.loads(report_path.read_text(encoding="utf-8"))
            assert report["status"] == "OFFICIAL_CROSSCHECK_FAILED_CLOSED"
            assert report["failure_code"] == failure
            assert report["cache_created"] is False
            assert report["data_accepted_for_prediction"] is False
            assert report["raw_provider_error_saved"] is False


TESTS = [v for k, v in globals().copy().items() if k.startswith("test_") and callable(v)]
for test in TESTS:
    test()
print(f"PASS {len(TESTS)} official reference cross-check adapter offline/mock tests")
