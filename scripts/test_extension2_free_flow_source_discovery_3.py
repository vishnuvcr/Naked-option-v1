from __future__ import annotations

import datetime as dt
from pathlib import Path
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



def test_per_source_cap_is_enforced_by_http_wrapper() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([FakeResponse(200, b"body")])
    client.opener = fake
    result = client.request("CDSL-1", mod.FIXED_URLS["CDSL-1"], max_body_bytes=mod.MAX_TOTAL_BYTES)
    assert result["status"] == "REJECTED_SCOPE"
    assert not fake.requests
    assert client.budget.initial_requests == 0


def test_unregistered_headers_are_rejected_before_network() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([FakeResponse(200, b"body")])
    client.opener = fake
    result = client.request(
        "CDSL-1", mod.FIXED_URLS["CDSL-1"],
        headers={"Range": "bytes=0-8191"}, max_body_bytes=1024,
    )
    assert result["status"] == "REJECTED_SCOPE"
    assert not fake.requests


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
    body = b"abcd" + b"x" * (mod.MAX_RANGE_BYTES - 4)
    fake = FakeOpener([
        FakeResponse(302, b"", {"Location": "https://cdn-lfs.huggingface.co/blob/file?X-Amz-Signature=secretvalue&Expires=123"}),
        FakeResponse(206, body, {"Content-Range": f"bytes 0-{mod.MAX_RANGE_BYTES - 1}/20000", "Content-Length": str(mod.MAX_RANGE_BYTES)}),
    ])
    client.opener = fake
    result = client.request(
        "HF-2-HEAD-RANGE", mod.HF_RESOLVE_URL, headers={
            "Range": f"bytes=0-{mod.MAX_RANGE_BYTES - 1}",
        }, max_body_bytes=mod.MAX_RANGE_BYTES, hf_redirects=True,
    )
    assert result["http_status"] == 206 and result["status"] == "FETCHED", result
    assert len(fake.requests) == 2
    assert fake.requests[1].get_header("Range") == f"bytes=0-{mod.MAX_RANGE_BYTES - 1}"
    assert fake.requests[1].get_header("Authorization") is None
    assert fake.requests[1].get_header("Cookie") is None
    assert result["content_range"] == "bytes 0-3/10"
    assert client.budget.redirects == 1



def test_credentials_are_rejected_before_network() -> None:
    client = mod.LimitedHTTP()
    fake = FakeOpener([FakeResponse(200, b"should-not-be-requested")])
    client.opener = fake
    result = client.request(
        "HF-2-HEAD-RANGE", mod.HF_RESOLVE_URL,
        headers={"Range": "bytes=0-3", "Authorization": "Bearer must-not-send"},
        max_body_bytes=8, hf_redirects=True,
    )
    assert result["status"] == "REJECTED_SCOPE"
    assert not fake.requests


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


def test_signed_hf_redirect_query_is_redacted_in_report() -> None:
    safe = mod.safe_url_for_report(
        "https://cdn-lfs.huggingface.co/blob/file?X-Amz-Signature=secretvalue&Expires=123"
    )
    assert "secretvalue" not in safe
    assert "123" not in safe
    assert "%5BREDACTED%5D" in safe


def test_exhausted_budget_returns_status_without_network_or_crash() -> None:
    budget = mod.Budget()
    budget.exhausted = True
    client = mod.LimitedHTTP(budget)
    fake = FakeOpener([FakeResponse(200, b"should-not-be-requested")])
    client.opener = fake
    result = client.request("CDSL-1", mod.FIXED_URLS["CDSL-1"], max_body_bytes=1024)
    assert result["status"] == "BUDGET_EXCEEDED"
    assert not fake.requests


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



def test_github_directory_parser_uses_metadata_only_and_rejects_inline_content() -> None:
    good = [
        {"name": "history.json", "path": "data/history.json", "size": 1234,
         "sha": "a" * 40, "type": "file"},
        {"name": "notes.txt", "path": "data/notes.txt", "size": 12,
         "sha": "b" * 40, "type": "file"},
    ]
    report = mod.parse_gh_directory_metadata(good)
    assert report["schema_status"] == "COVERAGE_LEAD_ONLY"
    assert report["directory_file_metadata_sample"] == [good[0]]
    unsafe = [{"name": "history.json", "path": "data/history.json", "size": 12,
               "sha": "a" * 40, "type": "file", "content": "raw file bytes"}]
    rejected = mod.parse_gh_directory_metadata(unsafe)
    assert rejected["schema_status"] == "REJECTED_SCOPE"
    malformed = [{"name": "history.json", "path": "data/history.json", "size": "12",
                  "sha": "not-a-sha", "type": "file"}]
    assert mod.parse_gh_directory_metadata(malformed)["schema_status"] == "REJECTED_SCHEMA"


def test_chirag_url_must_be_pinned_commit_and_exact_date() -> None:
    valid = mod.CHIRAG_URL_TEMPLATE.format(commit="a" * 40)
    assert mod.is_registered_probe_url("CHIRAG-1", valid, "GET")
    assert not mod.is_registered_probe_url(
        "CHIRAG-1",
        "https://raw.githubusercontent.com/chirag127/fii-dii-activity-api/main/data/2026-10-01.json",
        "GET",
    )
    assert not mod.is_registered_probe_url(
        "CHIRAG-1",
        mod.CHIRAG_URL_TEMPLATE.format(commit="a" * 40).replace("2026-10-01", "2026-10-02"),
        "GET",
    )


def test_head_missing_length_skips_hf_range_requests() -> None:
    class FakeClient:
        def __init__(self):
            self.calls = []
        def request(self, probe_id, url, **kwargs):
            self.calls.append((probe_id, url, kwargs))
            return {
                "probe_id": probe_id, "url": url, "status": "FETCHED",
                "http_status": 200, "content_length_header": None,
                "content_type": "text/csv", "bytes_read": 0, "sha256": mod.sha256_bytes(b""),
                "history": [], "body": b"",
            }
    client = FakeClient()
    report = mod.hf_file_probe(client, {})
    assert report["schema_status"] == "COVERAGE_LEAD_ONLY"
    assert len(client.calls) == 1
    assert client.calls[0][0] == "HF-2-HEAD"



def test_cdsl_archive_date_link_detects_compact_filename() -> None:
    parser = mod.LinkTableParser()
    parser.feed('<a href="/downloads/Publications/Latest/Latest_30092024.xls">Daily FPI 30-09-2024</a>')
    found = mod.date_links(parser)
    assert len(found) == 1
    assert "30092024" in found[0]["href"]


def test_csv_edge_marks_seeded_rows_as_synthetic() -> None:
    blob = (
        b"date,fii_buy,fii_sell,dii_buy,dii_sell,source\n"
        b"2024-09-30,10,9,5,4,historical-seed\n"
    )
    report = mod.parse_csv_edge(blob, "head")
    assert report["provenance_status"] == "REJECTED_SYNTHETIC"
    assert report["row_sample"][0]["source"] == "historical-seed"


def test_hf_probe_uses_exact_ranges_and_stays_within_16_kib() -> None:
    class FakeClient:
        def __init__(self):
            self.calls = []
        def request(self, probe_id, url, **kwargs):
            self.calls.append((probe_id, url, kwargs))
            if probe_id == "HF-2-HEAD":
                return {
                    "probe_id": probe_id, "url": url, "status": "FETCHED",
                    "http_status": 200, "content_length_header": "20000",
                    "content_type": "text/csv", "bytes_read": 0,
                    "sha256": mod.sha256_bytes(b""), "history": [], "body": b"",
                }
            if probe_id == "HF-2-HEAD-RANGE":
                body = (
                    b"date,fii_buy,fii_sell,dii_buy,dii_sell\n"
                    b"2024-01-01,10,9,5,4\n"
                )
                body = body + b"x" * (mod.MAX_RANGE_BYTES - len(body))
                return {
                    "probe_id": probe_id, "url": url, "status": "FETCHED", "http_status": 206,
                    "content_length_header": str(len(body)), "content_range": "bytes 0-8191/20000",
                    "bytes_read": len(body), "sha256": mod.sha256_bytes(body), "history": [], "body": body,
                }
            if probe_id == "HF-2-TAIL-RANGE":
                start = 20000 - mod.MAX_RANGE_BYTES
                body = b"partial,truncated\n2024-09-30,13,12,7,6\n"
                body = body + b"z" * (mod.MAX_RANGE_BYTES - len(body))
                return {
                    "probe_id": probe_id, "url": url, "status": "FETCHED", "http_status": 206,
                    "content_length_header": str(len(body)), "content_range": f"bytes {start}-19999/20000",
                    "bytes_read": len(body), "sha256": mod.sha256_bytes(body), "history": [], "body": body,
                }
            raise AssertionError(f"unexpected probe: {probe_id}")
    client = FakeClient()
    result = mod.hf_file_probe(client, {})
    assert result["schema_status"] == "COVERAGE_LEAD_ONLY", result
    assert result["sampled_csv_bytes"] == 16 * 1024
    assert client.calls[1][2]["headers"]["Range"] == "bytes=0-8191"
    assert client.calls[2][2]["headers"]["Range"] == "bytes=11808-19999"
    assert len(client.calls) == 3



def test_hf_range_values_are_exactly_bounded_before_network() -> None:
    for probe_id, range_value in [
        ("HF-2-HEAD-RANGE", "bytes=1-8192"),
        ("HF-2-HEAD-RANGE", "bytes=0-16383"),
        ("HF-2-TAIL-RANGE", "bytes=0-8191"),
        ("HF-2-TAIL-RANGE", "bytes=100-200"),
    ]:
        client = mod.LimitedHTTP()
        fake = FakeOpener([FakeResponse(206, b"x" * 8192, {"Content-Range": "bytes 0-8191/20000"})])
        client.opener = fake
        result = client.request(
            probe_id, mod.HF_RESOLVE_URL,
            headers={"Range": range_value}, max_body_bytes=mod.MAX_RANGE_BYTES, hf_redirects=True,
        )
        assert result["status"] == "REJECTED_SCOPE", (probe_id, range_value, result)
        assert not fake.requests


def test_chirag_flow_fields_must_be_numeric_and_finite() -> None:
    good = {
        "date": "2026-10-01", "source": "nse",
        "fii_buy": 100, "fii_sell": 90, "dii_buy": "50.5", "dii_sell": "₹40 Cr",
    }
    assert mod.validate_chirag_record(good)["status"] == "SCHEMA_SAMPLE_PASS"
    bad_text = mod.validate_chirag_record({**good, "fii_buy": "not-a-number"})
    assert bad_text["status"] == "REJECTED_SCHEMA", bad_text
    bad_nan = mod.validate_chirag_record({**good, "dii_sell": float("nan")})
    assert bad_nan["status"] == "REJECTED_SCHEMA", bad_nan


def test_live_workflow_consumes_manifest_before_any_source_request() -> None:
    root = Path(__file__).resolve().parents[1]
    live = (root / ".github/workflows/phase-07-free-flow-source-discovery-3.yml").read_text(encoding="utf-8")
    offline = (root / ".github/workflows/phase-07-free-flow-source-discovery-3-tests.yml").read_text(encoding="utf-8")
    assert live.index("Consume the one-run manifest before any source request") < live.index("Run one frozen source probe")
    assert "SPENT — ONE BOUNDED SOURCE-DISCOVERY RUN CONSUMED" in live
    assert "[manifest-consumed]" in live
    assert "!contains(github.event.head_commit.message, '[manifest-consumed]')" in live
    assert "contents: write" in live
    assert ".github/workflows/phase-07-free-flow-source-discovery-3.yml" in offline
    assert "python scripts/test_extension2_free_flow_source_discovery_3.py" in offline
    assert "python scripts/extension2_free_flow_source_discovery_3.py" not in offline


def test_fixed_probe_list_is_finite_and_fits_budget() -> None:
    initial = len(mod.FIXED_URLS) + 1 + 3  # Chirag single record; HF HEAD + two Range requests.
    assert initial == mod.MAX_INITIAL_REQUESTS == 15
    total_caps = sum(mod.PROBE_CAPS.values()) + 2 * mod.MAX_RANGE_BYTES
    assert total_caps == 1584 * 1024
    assert total_caps < mod.MAX_TOTAL_BYTES


def main() -> None:
    tests = [
        test_parse_date_formats,
        test_exact_content_range_is_required,
        test_unregistered_url_is_rejected_before_network,
        test_per_source_cap_is_enforced_by_http_wrapper,
        test_unregistered_headers_are_rejected_before_network,
        test_no_auto_redirect_for_cdsl,
        test_allowed_hf_redirect_preserves_range_but_not_credentials,
        test_credentials_are_rejected_before_network,
        test_hf_redirect_to_unregistered_host_is_rejected,
        test_hf_second_redirect_is_rejected,
        test_signed_hf_redirect_query_is_redacted_in_report,
        test_exhausted_budget_returns_status_without_network_or_crash,
        test_request_body_reads_cap_plus_one_and_rejects_overflow,
        test_budget_stops_at_total_bytes_and_counts_every_exchange,
        test_cdsl_xls_parser_uses_expected_date_and_equity_row,
        test_chirag_record_date_and_provenance_are_required,
        test_hf_tail_parser_uses_head_header_and_skips_partial_line,
        test_github_directory_parser_uses_metadata_only_and_rejects_inline_content,
        test_chirag_url_must_be_pinned_commit_and_exact_date,
        test_head_missing_length_skips_hf_range_requests,
        test_cdsl_archive_date_link_detects_compact_filename,
        test_csv_edge_marks_seeded_rows_as_synthetic,
        test_hf_probe_uses_exact_ranges_and_stays_within_16_kib,
        test_hf_range_values_are_exactly_bounded_before_network,
        test_chirag_flow_fields_must_be_numeric_and_finite,
        test_live_workflow_consumes_manifest_before_any_source_request,
        test_fixed_probe_list_is_finite_and_fits_budget,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} Extension 2 source-discovery 3 offline regressions")


if __name__ == "__main__":
    main()
