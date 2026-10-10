from __future__ import annotations

import datetime as dt
from unittest.mock import patch

import extension2_free_flow_source_discovery_3 as mod


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"", headers: dict[str, str] | None = None):
        self.status = status
        self.code = status
        self.headers = headers or {}
        self.body = body
        self.read_calls: list[int] = []
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        self.read_calls.append(size)
        if size is None or size < 0:
            raise AssertionError("unbounded read is forbidden")
        return self.body[:size]

    def close(self) -> None:
        self.closed = True


class FakeOpener:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout: int = 0):
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("unexpected extra HTTP exchange")
        return self.responses.pop(0)


def test_parse_date_formats() -> None:
    assert mod.parse_date("2026-10-01") == "2026-10-01"
    assert mod.parse_date("01-10-2026") == "2026-10-01"
    assert mod.parse_date("01/10/2026") == "2026-10-01"
    assert mod.parse_date("01-Oct-2026") == "2026-10-01"
    assert mod.parse_date("not-a-date") == ""


def test_exact_content_range_is_required() -> None:
    body = b"x" * 8
    ok, reason = mod.validate_content_range_response(
        {"status": "FETCHED", "http_status": 206, "content_range": "bytes 0-7/20", "body": body},
        0, 7, 20,
    )
    assert ok and reason == "PASS"
    cases = [
        ({"status": "FETCHED", "http_status": 200, "content_range": "bytes 0-7/20", "body": body}, "HTTP 206"),
        ({"status": "FETCHED", "http_status": 206, "content_range": "bytes 1-8/20", "body": body}, "Content-Range"),
        ({"status": "FETCHED", "http_status": 206, "content_range": "bytes 0-7/21", "body": body}, "Content-Range"),
        ({"status": "FETCHED", "http_status": 206, "content_range": "missing", "body": body}, "Content-Range"),
        ({"status": "FETCHED", "http_status": 206, "content_range": "bytes 0-7/20", "body": b"short"}, "body byte count"),
    ]
    for response, expected in cases:
        passed, message = mod.validate_content_range_response(response, 0, 7, 20)
        assert not passed and expected in message, (response, message)


def test_unregistered_url_is_rejected_before_network() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([FakeResponse(200, b"should-not-be-read")])
    client.opener = fake
    result = client.request(
        "GH-META-1A",
        "https://api.github.com/repos/MrChartist/fii-dii-data/contents/data/history.json",
        max_body_bytes=1024,
    )
    assert result["status"] == "REJECTED_SCOPE"
    assert not fake.requests
    assert client.budget.initial_requests == 0


def test_no_auto_redirect_for_cdsl() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([FakeResponse(302, b"", {"Location": "https://www.cdslindia.com/elsewhere"})])
    client.opener = fake
    result = client.request("CDSL-1", mod.FIXED_URLS["CDSL-1"], max_body_bytes=2048)
    assert result["status"] == "REJECTED_REDIRECT"
    assert len(fake.requests) == 1
    assert client.budget.exchanges == 1


def test_allowed_hf_redirect_preserves_range_but_not_credentials() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([
        FakeResponse(302, b"", {"Location": "https://cdn-lfs.huggingface.co/blob/file"}),
        FakeResponse(206, b"abcd", {"Content-Range": "bytes 0-3/10", "Content-Length": "4"}),
    ])
    client.opener = fake
    result = client.request(
        "HF-2-HEAD-RANGE", mod.HF_RESOLVE_URL, headers={
            "Range": "bytes=0-3", "Authorization": "Bearer must-not-forward",
            "Cookie": "must-not-forward",
        }, max_body_bytes=8, hf_redirects=True,
    )
    assert result["http_status"] == 206 and result["status"] == "FETCHED", result
    assert len(fake.requests) == 2
    assert fake.requests[1].get_header("Range") == "bytes=0-3"
    assert fake.requests[1].get_header("Authorization") is None
    assert fake.requests[1].get_header("Cookie") is None
    assert result["content_range"] == "bytes 0-3/10"
    assert client.budget.redirects == 1


def test_hf_redirect_to_unregistered_host_is_rejected() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([FakeResponse(302, b"", {"Location": "https://evil.example/data.csv"})])
    client.opener = fake
    result = client.request("HF-2-HEAD-RANGE", mod.HF_RESOLVE_URL, headers={"Range": "bytes=0-3"}, max_body_bytes=8, hf_redirects=True)
    assert result["status"] == "REJECTED_REDIRECT_HOST"
    assert len(fake.requests) == 1


def test_hf_second_redirect_is_rejected() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([
        FakeResponse(302, b"", {"Location": "https://cdn-lfs.huggingface.co/blob/file"}),
        FakeResponse(302, b"", {"Location": "https://cas-bridge.xethub.hf.co/blob/file"}),
    ])
    client.opener = fake
    result = client.request("HF-2-HEAD-RANGE", mod.HF_RESOLVE_URL, headers={"Range": "bytes=0-3"}, max_body_bytes=8, hf_redirects=True)
    assert result["status"] == "REJECTED_REDIRECT"
    assert len(fake.requests) == 2
    assert client.budget.redirects == 1


def test_request_body_reads_cap_plus_one_and_rejects_overflow() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([FakeResponse(200, b"x" * 10000, {"Content-Length": "10000"})])
    client.opener = fake
    result = client.request("CDSL-1", mod.FIXED_URLS["CDSL-1"], max_body_bytes=8192)
    assert result["status"] == "REJECTED_TOO_LARGE"
    assert fake.requests[0] is not None
    assert client.budget.bytes_read == 8193
    assert fake.responses == []


def test_budget_stops_at_total_bytes_and_counts_every_exchange() -> None:
    budget = mod.Budget()
    budget.bytes_read = mod.MAX_TOTAL_BYTES - 2
    try:
        budget.record_bytes(3)
    except mod.BudgetExceeded:
        pass
    else:
        raise AssertionError("global byte budget should reject overrun")
    assert budget.exhausted

    b2 = mod.Budget()
    for i in range(mod.MAX_INITIAL_REQUESTS):
        b2.start_initial(f"probe-{i}", f"https://example.invalid/{i}")
    try:
        b2.start_initial("overflow", "https://example.invalid/overflow")
    except mod.BudgetExceeded:
        pass
    else:
        raise AssertionError("initial request limit should be enforced")
    assert b2.initial_requests == mod.MAX_INITIAL_REQUESTS


def test_cdsl_xls_parser_uses_expected_date_and_equity_row() -> None:
    class FakeSheet:
        nrows = 3
        ncols = 4
        cells = [
            ["CDSL Daily FPI Report", "30-Sep-2024", "", ""],
            ["Equity", "Stock Exchange", "Gross Purchases", "Net Investment"],
            ["Debt", "Stock Exchange", "Gross Purchases", "Net Investment"],
        ]
        def cell_value(self, row, col):
            return self.cells[row][col]

    class FakeBook:
        def sheets(self):
            return [FakeSheet()]
        def release_resources(self):
            pass

    with patch.object(mod.xlrd, "open_workbook", return_value=FakeBook()):
        ok = mod.parse_cdsl_xls(b"fixture", "2024-09-30", mod.FIXED_URLS["CDSL-2"])
    assert ok["status"] == "SCHEMA_SAMPLE_PASS", ok
    assert ok["source_semantics"] == "FPI_ONLY"
    assert ok["equity_stock_exchange_rows_found"] == 1

    with patch.object(mod.xlrd, "open_workbook", return_value=FakeBook()):
        bad = mod.parse_cdsl_xls(b"fixture", "2024-10-01", mod.FIXED_URLS["CDSL-2"])
    assert bad["status"] == "NOT_VERIFIED"
    assert bad["date_check"] == "FAIL_OR_NOT_FOUND"


def test_chirag_record_date_and_provenance_are_required() -> None:
    good = {"date": "2026-10-01", "source": "nse", "fii_buy": 100, "fii_sell": 90, "dii_buy": 60, "dii_sell": 55}
    assert mod.validate_chirag_record(good)["status"] == "SCHEMA_SAMPLE_PASS"
    assert mod.validate_chirag_record({**good, "date": "2026-10-02"})["status"] == "REJECTED_SCHEMA"
    assert mod.validate_chirag_record({**good, "source": "placeholder"})["status"] == "REJECTED_PROVENANCE"
    assert mod.validate_chirag_record({**good, "provenance": "historical-seed"})["status"] == "REJECTED_SYNTHETIC"


def test_hf_tail_parser_uses_head_header_and_skips_partial_line() -> None:
    header = ["date", "fii_buy", "fii_sell", "dii_buy", "dii_sell"]
    tail = b"partial,truncated\n2024-09-30,10,9,5,4\n2024-10-01,11,10,6,5\n"
    result = mod.parse_csv_edge(tail, "tail", header_override=header)
    assert result["header"] == header
    assert result["parsed_rows"] == 2, result
    assert result["date_values"] == ["2024-09-30", "2024-10-01"]


def test_fixed_probe_list_is_finite_and_fits_budget() -> None:
    initial = len(mod.FIXED_URLS) + 1 + 3  # Chirag single record; HF HEAD + two Range requests.
    assert initial == mod.MAX_INITIAL_REQUESTS == 15
    total_caps = sum(mod.PROBE_CAPS.values()) + 2 * mod.MAX_RANGE_BYTES + mod.PROBE_CAPS["CHIRAG-COMMIT"]
    assert total_caps < mod.MAX_TOTAL_BYTES


def main() -> None:
    tests = [
        test_parse_date_formats,
        test_exact_content_range_is_required,
        test_unregistered_url_is_rejected_before_network,
        test_no_auto_redirect_for_cdsl,
        test_allowed_hf_redirect_preserves_range_but_not_credentials,
        test_hf_redirect_to_unregistered_host_is_rejected,
        test_hf_second_redirect_is_rejected,
        test_request_body_reads_cap_plus_one_and_rejects_overflow,
        test_budget_stops_at_total_bytes_and_counts_every_exchange,
        test_cdsl_xls_parser_uses_expected_date_and_equity_row,
        test_chirag_record_date_and_provenance_are_required,
        test_hf_tail_parser_uses_head_header_and_skips_partial_line,
        test_fixed_probe_list_is_finite_and_fits_budget,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} Extension 2 source-discovery 3 offline regressions")


if __name__ == "__main__":
    main()
