from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import xlrd

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data/reports/extension2_free_flow_source_discovery3.json"
SPEC_VERSION = "EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3"
HF_REVISION = "f90f7acad633ba5a803f25cf431fb5f13ce3d162"
HF_DATASET = "johnwick3690/stocks"
HF_REL_PATH = "nifty historical data/fii dii data/fii_dii_2024_to_today.csv"
HF_FILE_URL = (
    "https://huggingface.co/datasets/johnwick3690/stocks/resolve/"
    + HF_REVISION
    + "/nifty%20historical%20data/fii%20dii%20data/fii_dii_2024_to_today.csv"
)
HF_METADATA_URL = (
    "https://huggingface.co/api/datasets/johnwick3690/stocks/revision/"
    + HF_REVISION
)
CHIRAG_COMMIT_URL = "https://api.github.com/repos/chirag127/fii-dii-activity-api/commits/main"
CHIRAG_JSON_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/chirag127/fii-dii-activity-api/"
    "{commit}/data/2026-10-01.json"
)
CDSL_INDEX_URL = "https://www.cdslindia.com/Publications/ForeignPortInvestor.html"
CDSL_XLS = {
    "cdsl_2024_09_30": (
        "https://www.cdslindia.com/downloads/Publications/Latest/Latest_30092024.xls",
        "2024-09-30",
    ),
    "cdsl_2024_10_09": (
        "https://www.cdslindia.com/downloads/Publications/Latest/Latest_09102024.xls",
        "2024-10-09",
    ),
}
CDSL_TRENDS_URL = "https://www.cdslindia.com/Publications/FIITrends.aspx"
SEBI_URL = "https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html"
NSE_URL = "https://www.nseindia.com/reports/fii-dii/"
CALCSETU_URL = "https://calcsetu.com/Utility/Diifii/"
GH_HISTORY_DIR_URLS = {
    "marketcalls": "https://api.github.com/repos/marketcalls/fii-dii-data/contents/data",
    "r7sh7": "https://api.github.com/repos/r7sh7/fii-dii-data/contents/data",
}

MAX_INITIAL_REQUESTS = 15
MAX_REDIRECT_REQUESTS = 3
MAX_HTTP_EXCHANGES = 18
MAX_TOTAL_BODY_BYTES = 2 * 1024 * 1024
MAX_CDSL_HTML_BYTES = 128 * 1024
MAX_CDSL_XLS_BYTES = 384 * 1024
MAX_CDSL_TRENDS_BYTES = 64 * 1024
MAX_HF_METADATA_BYTES = 128 * 1024
MAX_HF_RANGE_BYTES = 8 * 1024
MAX_CHIRAG_TOTAL_BYTES = 32 * 1024
MAX_CHIRAG_JSON_BYTES = 8 * 1024
MAX_SEBI_HTML_BYTES = 128 * 1024
MAX_NSE_HTML_BYTES = 128 * 1024
MAX_CALCSETU_HTML_BYTES = 64 * 1024
MAX_GITHUB_DIRECTORY_BYTES = 64 * 1024
MAX_CSV_SAMPLE_ROWS = 10
MAX_VISIBLE_HTML_ROWS = 20

HF_ALLOWED_REDIRECT_HOSTS = {
    "huggingface.co",
    "www.huggingface.co",
    "hf.co",
    "cdn-lfs.huggingface.co",
    "cas-bridge.xethub.hf.co",
    "cas-server.xethub.hf.co",
    "us.aws.cdn.hf.co",
}
HF_SOURCE_HOSTS = {"huggingface.co", "www.huggingface.co"}
OTHER_HOSTS = {
    "cdsl": {"www.cdslindia.com", "cdslindia.com"},
    "sebi": {"www.sebi.gov.in", "sebi.gov.in"},
    "nse": {"www.nseindia.com", "nseindia.com"},
    "calcsetu": {"calcsetu.com", "www.calcsetu.com"},
    "github_api": {"api.github.com"},
    "github_raw": {"raw.githubusercontent.com"},
}
HEADERS = {
    "User-Agent": "NakedOption-FreeSourceDiscovery3/1.0",
    "Accept": "text/html,application/json,text/csv,application/vnd.ms-excel,application/octet-stream,*/*",
}
DATE_RE = re.compile(r"(?<!\d)(\d{1,2})[-/ ]([A-Za-z]{3,9}|\d{1,2})[-/ ](\d{4})(?!\d)")
SYNTHETIC_MARKERS = (
    "historical-seed",
    "historical_seed",
    "synthetic",
    "generated",
    "placeholder",
    "seed data",
    "seeded",
    "realistic per-day",
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass
class Budget:
    initial_requests: int = 0
    redirect_requests: int = 0
    body_bytes_read: int = 0
    max_initial_requests: int = MAX_INITIAL_REQUESTS
    max_redirect_requests: int = MAX_REDIRECT_REQUESTS
    max_http_exchanges: int = MAX_HTTP_EXCHANGES
    max_body_bytes: int = MAX_TOTAL_BODY_BYTES

    @property
    def exchanges(self) -> int:
        return self.initial_requests + self.redirect_requests

    def reserve_initial(self) -> None:
        if self.initial_requests >= self.max_initial_requests:
            raise RuntimeError("initial request budget exhausted")
        if self.exchanges >= self.max_http_exchanges:
            raise RuntimeError("HTTP exchange budget exhausted")
        if self.body_bytes_read >= self.max_body_bytes:
            raise RuntimeError("global body byte budget exhausted")
        self.initial_requests += 1

    def reserve_redirect(self) -> None:
        if self.redirect_requests >= self.max_redirect_requests:
            raise RuntimeError("redirect request budget exhausted")
        if self.exchanges >= self.max_http_exchanges:
            raise RuntimeError("HTTP exchange budget exhausted")
        if self.body_bytes_read >= self.max_body_bytes:
            raise RuntimeError("global body byte budget exhausted")
        self.redirect_requests += 1

    def record_body(self, count: int) -> None:
        if count < 0 or self.body_bytes_read + count > self.max_body_bytes:
            raise RuntimeError("global body byte budget exceeded")
        self.body_bytes_read += count

    def as_dict(self) -> dict[str, int]:
        return {
            "initial_requests": self.initial_requests,
            "redirect_requests": self.redirect_requests,
            "http_exchanges": self.exchanges,
            "body_bytes_read": self.body_bytes_read,
            "max_initial_requests": self.max_initial_requests,
            "max_redirect_requests": self.max_redirect_requests,
            "max_http_exchanges": self.max_http_exchanges,
            "max_body_bytes": self.max_body_bytes,
        }


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: str
    http_status: int | None
    headers: dict[str, str] = field(default_factory=dict)
    data: bytes = b""
    bytes_read: int = 0
    sha256: str | None = None
    error: str | None = None
    redirect_chain: list[str] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "status": self.status,
            "http_status": self.http_status,
            "content_type": self.headers.get("content-type", ""),
            "content_length_header": self.headers.get("content-length"),
            "content_range": self.headers.get("content-range"),
            "bytes_read": self.bytes_read,
            "sha256": self.sha256,
            "redirect_chain": self.redirect_chain,
            "error": self.error,
        }


class LimitedFetcher:
    """HTTP transport with shared request/byte limits and no automatic redirects."""

    def __init__(self, budget: Budget | None = None):
        self.budget = budget or Budget()
        self._opener = urllib.request.build_opener(NoRedirect())

    @staticmethod
    def _host(url: str) -> str:
        parsed = urllib.parse.urlsplit(url)
        return (parsed.hostname or "").lower()

    @staticmethod
    def _normal_headers(headers: Any) -> dict[str, str]:
        return {str(k).lower(): str(v) for k, v in headers.items()}

    def _single_exchange(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        body_cap: int,
        is_redirect: bool,
    ) -> FetchResult:
        remaining = self.budget.max_body_bytes - self.budget.body_bytes_read
        if remaining <= 0:
            return FetchResult(
                url=url, final_url=url, status="GLOBAL_BYTE_BUDGET_EXHAUSTED",
                http_status=None, error="global body byte budget exhausted before request",
            )
        try:
            if is_redirect:
                self.budget.reserve_redirect()
            else:
                self.budget.reserve_initial()
        except RuntimeError as exc:
            return FetchResult(url=url, final_url=url, status="BUDGET_REJECTED", http_status=None, error=str(exc))

        # Drop credentials case-insensitively on every initial or redirected request.
        secret_headers = {"authorization", "cookie", "proxy-authorization"}
        clean_headers = {k: v for k, v in headers.items() if k.lower() not in secret_headers}
        request = urllib.request.Request(url, headers=clean_headers, method=method)
        try:
            response = self._opener.open(request, timeout=20)
        except urllib.error.HTTPError as exc:
            status_code = int(exc.code)
            response_headers = self._normal_headers(exc.headers or {})
            location = response_headers.get("location")
            exc.close()
            return FetchResult(
                url=url, final_url=url, status="HTTP_REDIRECT" if 300 <= status_code < 400 else "HTTP_ERROR",
                http_status=status_code, headers=response_headers, bytes_read=0,
                error=("redirect requires explicit policy handling" if location else f"HTTP {status_code}"),
                redirect_chain=[location] if location else [],
            )
        except Exception as exc:
            return FetchResult(
                url=url, final_url=url, status="FETCH_FAILED", http_status=None,
                error=f"{type(exc).__name__}: {str(exc)[:300]}",
            )

        with response:
            status_code = int(getattr(response, "status", response.getcode()))
            response_headers = self._normal_headers(response.headers)
            actual_url = response.geturl()
            if status_code < 200 or status_code >= 300:
                return FetchResult(
                    url=url, final_url=actual_url, status="HTTP_ERROR",
                    http_status=status_code, headers=response_headers,
                    error=f"HTTP {status_code}",
                )
            if method == "HEAD":
                return FetchResult(
                    url=url, final_url=actual_url, status="FETCHED",
                    http_status=status_code, headers=response_headers,
                )

            content_length = response_headers.get("content-length")
            try:
                content_length_n = int(content_length) if content_length is not None else None
            except ValueError:
                content_length_n = None
            if content_length_n is not None and content_length_n > body_cap:
                return FetchResult(
                    url=url, final_url=actual_url, status="REJECTED_TOO_LARGE",
                    http_status=status_code, headers=response_headers,
                    error=f"Content-Length {content_length_n} exceeds per-request cap {body_cap}",
                )

            # Read no more than the configured cap plus one overflow byte, and
            # never exceed the shared total body-byte budget.
            read_limit = min(body_cap + 1, remaining)
            data = response.read(read_limit)
            self.budget.record_body(len(data))
            if len(data) > body_cap:
                return FetchResult(
                    url=url, final_url=actual_url, status="REJECTED_TOO_LARGE",
                    http_status=status_code, headers=response_headers, bytes_read=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                    error=f"body exceeded per-request cap {body_cap}",
                )
            return FetchResult(
                url=url, final_url=actual_url, status="FETCHED",
                http_status=status_code, headers=response_headers, data=data,
                bytes_read=len(data), sha256=hashlib.sha256(data).hexdigest(),
            )

    @staticmethod
    def _is_registered_request(
        url: str, source: str, method: str, headers: dict[str, str]
    ) -> tuple[bool, str]:
        method = method.upper()
        if source == "cdsl":
            if method == "GET" and url in {CDSL_INDEX_URL, CDSL_TRENDS_URL, *(u for u, _ in CDSL_XLS.values())}:
                return True, ""
        elif source == "hf_metadata":
            if method == "GET" and url == HF_METADATA_URL:
                return True, ""
        elif source == "hf_file":
            if url != HF_FILE_URL:
                return False, "HF file URL is not the frozen resolve URL"
            range_value = next((v for k, v in headers.items() if k.lower() == "range"), None)
            if method == "HEAD" and range_value is None:
                return True, ""
            if method == "GET" and range_value is not None:
                match = re.fullmatch(r"bytes=(\d+)-(\d+)", range_value.strip())
                if match:
                    start, end = int(match.group(1)), int(match.group(2))
                    if start == 0 and end == MAX_HF_RANGE_BYTES - 1:
                        return True, ""
                    if end - start + 1 == MAX_HF_RANGE_BYTES and end >= MAX_HF_RANGE_BYTES:
                        return True, ""
            return False, "HF file request method/range is outside the frozen plan"
        elif source == "github_api":
            allowed = {CHIRAG_COMMIT_URL, *GH_HISTORY_DIR_URLS.values()}
            if method == "GET" and url in allowed:
                return True, ""
        elif source == "github_raw":
            pattern = r"https://raw\.githubusercontent\.com/chirag127/fii-dii-activity-api/[0-9a-f]{40}/data/2026-10-01\.json"
            if method == "GET" and re.fullmatch(pattern, url):
                return True, ""
        elif source == "sebi" and method == "GET" and url == SEBI_URL:
            return True, ""
        elif source == "nse" and method == "GET" and url == NSE_URL:
            return True, ""
        elif source == "calcsetu" and method == "GET" and url == CALCSETU_URL:
            return True, ""
        return False, f"unregistered source/method/URL: {source} {method} {url}"

    def get(
        self,
        url: str,
        *,
        source: str,
        body_cap: int,
        headers: dict[str, str] | None = None,
        method: str = "GET",
        permit_hf_redirect: bool = False,
    ) -> FetchResult:
        supplied_headers = headers or {}
        registered, reason = self._is_registered_request(url, source, method, supplied_headers)
        if not registered:
            return FetchResult(
                url=url, final_url=url, status="UNREGISTERED_URL", http_status=None,
                error=reason,
            )
        request_headers = dict(HEADERS)
        if headers:
            request_headers.update(headers)
        first = self._single_exchange(
            url, method, request_headers, body_cap, is_redirect=False
        )
        if first.status != "HTTP_REDIRECT":
            return first

        location = first.redirect_chain[0] if first.redirect_chain else None
        if not location:
            first.status = "REDIRECT_REJECTED"
            first.error = "redirect response lacked a Location header"
            return first
        if not permit_hf_redirect or source != "hf_file":
            first.status = "REDIRECT_REJECTED"
            first.error = "redirects are forbidden for this source"
            return first
        if method not in {"HEAD", "GET"}:
            first.status = "REDIRECT_REJECTED"
            first.error = "unsupported redirected method"
            return first
        parsed_location = urllib.parse.urlsplit(urllib.parse.urljoin(url, location))
        host = (parsed_location.hostname or "").lower()
        if parsed_location.scheme != "https" or host not in HF_ALLOWED_REDIRECT_HOSTS:
            first.status = "REDIRECT_REJECTED"
            first.error = f"redirect host/scheme not allowlisted: {host}"
            return first
        if parsed_location.username or parsed_location.password:
            first.status = "REDIRECT_REJECTED"
            first.error = "redirect URL may not contain credentials"
            return first

        secret_headers = {"authorization", "cookie", "proxy-authorization"}
        final_headers = {k: v for k, v in request_headers.items() if k.lower() not in secret_headers}
        redirected = self._single_exchange(
            parsed_location.geturl(), method, final_headers, body_cap, is_redirect=True
        )
        redirected.redirect_chain = [parsed_location.geturl()]
        if redirected.status == "HTTP_REDIRECT":
            redirected.status = "REDIRECT_REJECTED"
            redirected.error = "multiple-hop redirects are forbidden"
            redirected.data = b""
        redirected.url = url
        return redirected


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_date(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})", raw)
    if iso:
        try:
            return dt.date.fromisoformat("-".join(iso.groups())).isoformat()
        except ValueError:
            return None
    candidates = (
        ("%d-%b-%Y", raw[:11].title()),
        ("%d %b %Y", raw[:11].title()),
        ("%d-%B-%Y", raw[:20].title()),
        ("%d %B %Y", raw[:20].title()),
        ("%d-%m-%Y", raw[:10]),
        ("%d/%m/%Y", raw[:10]),
        ("%d %m %Y", raw[:10]),
    )
    for fmt, candidate in candidates:
        try:
            return dt.datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def is_synthetic_text(value: Any) -> bool:
    low = str(value or "").strip().lower()
    return any(marker in low for marker in SYNTHETIC_MARKERS)


def json_from_result(result: FetchResult) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    if result.status != "FETCHED":
        return None, result.status
    try:
        return json.loads(result.data.decode("utf-8-sig")), None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"JSON_PARSE_FAILED: {type(exc).__name__}"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = " ".join(" ".join(self._text).split())
            self.links.append({"href": self._href, "text": text})
            self._href = None
            self._text = []


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._in_row = False
        self._in_cell = False
        self._cell: list[str] = []
        self._row: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._in_row, self._row = True, []
        elif tag in {"td", "th"} and self._in_row:
            self._in_cell, self._cell = True, []

    def handle_data(self, data: str) -> None:
        if self._in_row and self._in_cell:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._in_row and self._in_cell:
            self._row.append(" ".join(" ".join(self._cell).split()))
            self._in_cell = False
            self._cell = []
        elif tag == "tr" and self._in_row:
            if self._row:
                self.rows.append(self._row)
            self._in_row = False
            self._row = []


def html_text_sample(data: bytes, *, max_rows: int = MAX_VISIBLE_HTML_ROWS) -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace")
    links = LinkParser()
    table = TableParser()
    links.feed(text)
    table.feed(text)
    lower = text.lower()
    dates: list[str] = []
    for match in DATE_RE.finditer(text):
        normalized = parse_date(match.group(0))
        if normalized:
            dates.append(normalized)
    unique_dates = sorted(set(dates))
    return {
        "body_sha256": sha256_bytes(data),
        "visible_link_count": len(links.links),
        "link_samples": links.links[:25],
        "unique_visible_date_count": len(unique_dates),
        "earliest_visible_date": unique_dates[0] if unique_dates else None,
        "latest_visible_date": unique_dates[-1] if unique_dates else None,
        "table_row_count_parsed": len(table.rows),
        "table_rows_sample": table.rows[:max_rows],
        "contains_fii_term": "fii" in lower or "fpi" in lower,
        "contains_dii_term": "dii" in lower,
        "contains_csv_term": "csv" in lower,
    }


def excel_value_to_text(value: Any, cell_type: int, datemode: int) -> str:
    if cell_type == xlrd.XL_CELL_DATE:
        try:
            return xlrd.xldate_as_datetime(value, datemode).date().isoformat()
        except Exception:
            return str(value)
    if cell_type == xlrd.XL_CELL_NUMBER and isinstance(value, (int, float)):
        if math.isfinite(float(value)) and float(value).is_integer():
            return str(int(value))
        return str(value)
    return str(value).strip()


def scan_cdsl_xls(data: bytes, expected_date: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "expected_report_date": expected_date,
        "body_sha256": sha256_bytes(data),
        "body_bytes": len(data),
        "schema_status": "REJECTED_SCHEMA",
        "report_date_found": False,
        "equity_row_found": False,
        "recognized_fields": [],
        "numeric_equity_values": [],
        "reason": None,
    }
    try:
        book = xlrd.open_workbook(file_contents=data, on_demand=True)
    except Exception as exc:
        result["reason"] = f"XLS_PARSE_FAILED: {type(exc).__name__}"
        return result

    date_evidence: list[str] = []
    equity_candidate_rows: list[dict[str, Any]] = []
    max_cells = 0
    for sheet in book.sheets():
        max_cells += sheet.nrows * sheet.ncols
        if max_cells > 10000:
            result["reason"] = "XLS cell budget exceeded"
            result["schema_status"] = "REJECTED_SCOPE"
            book.release_resources()
            return result
        matrix: list[list[str]] = []
        for rowx in range(sheet.nrows):
            row_texts: list[str] = []
            for colx in range(sheet.ncols):
                cell = sheet.cell(rowx, colx)
                row_texts.append(excel_value_to_text(cell.value, cell.ctype, book.datemode))
            matrix.append(row_texts)

        for ridx, row in enumerate(matrix):
            for cell in row:
                normalized = parse_date(cell)
                if normalized:
                    date_evidence.append(normalized)
            joined = " | ".join(row).lower()
            if "equity" in joined and (
                "exchange" in joined or "investment" in joined or "fpi" in joined or "fii" in joined
            ):
                context = " | ".join(" | ".join(r) for r in matrix[max(0, ridx - 3):min(len(matrix), ridx + 9)]).lower()
                fields = []
                if "gross purchase" in context or "purchase" in context or "buy value" in context:
                    fields.append("buy")
                if "gross sale" in context or "gross sales" in context or "sale" in context or "sell value" in context:
                    fields.append("sell")
                if "net investment" in context or "net purchase" in context:
                    fields.append("net")
                row_nums = [
                    value for value in row
                    if value.strip() and re.fullmatch(r"-?\d+(?:\.\d+)?", value.strip())
                ]
                equity_candidate_rows.append({
                    "sheet": sheet.name,
                    "row_index_1based": ridx + 1,
                    "row_sample": row[:12],
                    "recognized_fields_in_neighborhood": fields,
                    "numeric_values_in_row": row_nums[:8],
                })

    dates = sorted(set(date_evidence))
    result["observed_dates"] = dates[:20]
    result["observed_date_count"] = len(dates)
    result["report_date_found"] = expected_date in dates
    result["equity_candidate_rows"] = equity_candidate_rows[:5]
    result["equity_row_found"] = bool(equity_candidate_rows)
    field_union = sorted({f for row in equity_candidate_rows for f in row["recognized_fields_in_neighborhood"]})
    result["recognized_fields"] = field_union
    result["numeric_equity_values"] = [
        {"sheet": row["sheet"], "row_index_1based": row["row_index_1based"], "values": row["numeric_values_in_row"]}
        for row in equity_candidate_rows[:5]
    ]
    if not result["report_date_found"]:
        result["reason"] = "expected report date not found in workbook"
    elif not result["equity_row_found"]:
        result["reason"] = "no equity stock-exchange/investment row recognized"
    elif not {"buy", "sell", "net"}.issubset(set(field_union)):
        result["reason"] = "buy/sell/net-investment fields not all recognized near equity row"
    else:
        result["schema_status"] = "SCHEMA_SAMPLE_PASS"
        result["reason"] = None
    book.release_resources()
    return result


def inspect_cdsl_source(fetcher: LimitedFetcher) -> dict[str, Any]:
    result: dict[str, Any] = {"key": "cdsl_daily_fpi_archive", "status": "NOT_VERIFIED"}
    index = fetcher.get(CDSL_INDEX_URL, source="cdsl", body_cap=MAX_CDSL_HTML_BYTES)
    result["index_request"] = index.metadata()
    if index.status == "FETCHED":
        page = html_text_sample(index.data)
        result["index_page_sample"] = page
        # Parse all links from the already capped CDSL page body to estimate its
        # visible date span; only 20 are written to the report.
        links = LinkParser()
        links.feed(index.data.decode("utf-8", errors="replace"))
        dated_links: list[dict[str, str]] = []
        for link in links.links:
            text = link.get("text", "")
            normalized = parse_date(text)
            if normalized:
                dated_links.append({"date": normalized, "href": link.get("href", ""), "text": text})
        result["dated_link_sample"] = dated_links[:20]
        if dated_links:
            result["visible_archive_range"] = {
                "earliest": min(x["date"] for x in dated_links),
                "latest": max(x["date"] for x in dated_links),
                "count_in_sample": len(dated_links),
            }
    result["xls_samples"] = []
    for key, (url, date) in CDSL_XLS.items():
        fetched = fetcher.get(url, source="cdsl", body_cap=MAX_CDSL_XLS_BYTES)
        entry: dict[str, Any] = {"key": key, **fetched.metadata()}
        if fetched.status == "FETCHED":
            entry["parsed"] = scan_cdsl_xls(fetched.data, date)
        else:
            entry["parsed"] = {
                "expected_report_date": date,
                "schema_status": "NOT_VERIFIED",
                "reason": fetched.status,
            }
        result["xls_samples"].append(entry)
    trends = fetcher.get(CDSL_TRENDS_URL, source="cdsl", body_cap=MAX_CDSL_TRENDS_BYTES)
    result["trends_request"] = trends.metadata()
    if trends.status == "FETCHED":
        result["trends_page_sample"] = html_text_sample(trends.data)
    result["status"] = (
        "SCHEMA_SAMPLE_PASS"
        if any(x.get("parsed", {}).get("schema_status") == "SCHEMA_SAMPLE_PASS" for x in result["xls_samples"])
        else "COVERAGE_LEAD_ONLY"
    )
    return result


def inspect_hf_metadata(fetcher: LimitedFetcher) -> dict[str, Any]:
    fetched = fetcher.get(HF_METADATA_URL, source="hf_metadata", body_cap=MAX_HF_METADATA_BYTES)
    result: dict[str, Any] = {"key": "huggingface_fii_dii_csv_metadata", **fetched.metadata()}
    obj, error = json_from_result(fetched)
    if error or not isinstance(obj, dict):
        result.update({"schema_status": "NOT_VERIFIED", "reason": error or "metadata is not a JSON object"})
        return result
    returned_sha = str(obj.get("sha") or obj.get("commit") or obj.get("id") or "")
    siblings = obj.get("siblings")
    if not isinstance(siblings, list):
        siblings = obj.get("files") if isinstance(obj.get("files"), list) else []
    file_match = None
    normalized_target = HF_REL_PATH.replace("\\", "/")
    for item in siblings:
        if not isinstance(item, dict):
            continue
        path = str(item.get("rfilename") or item.get("path") or "").replace("\\", "/")
        if path == normalized_target:
            file_match = item
            break
    card_data = obj.get("cardData") if isinstance(obj.get("cardData"), dict) else {}
    card_text = " ".join(str(v) for v in card_data.values())[:20000].lower()
    if any(term in card_text for term in SYNTHETIC_MARKERS):
        result.update({
            "schema_status": "REJECTED_SYNTHETIC",
            "reason": "dataset card metadata contains synthetic/seed/placeholder marker",
        })
    elif returned_sha and returned_sha != HF_REVISION:
        result.update({
            "schema_status": "REJECTED_REVISION_MISMATCH",
            "reported_revision": returned_sha,
            "reason": "metadata response revision differs from pinned commit",
        })
    elif not file_match:
        result.update({
            "schema_status": "NOT_VERIFIED",
            "reason": "pinned metadata did not identify the exact CSV path",
        })
    else:
        result.update({
            "schema_status": "COVERAGE_LEAD_ONLY",
            "reported_revision": returned_sha or HF_REVISION,
            "file_metadata": {
                "path": normalized_target,
                "size": file_match.get("size") or file_match.get("lfs", {}).get("size") if isinstance(file_match.get("lfs"), dict) else file_match.get("size"),
                "lfs_sha256": file_match.get("lfs", {}).get("oid") if isinstance(file_match.get("lfs"), dict) else None,
            },
            "dataset_card_mentions_seed_or_synthetic": False,
            "reason": "metadata is pinned; observed daily-row schema/provenance still needs bounded head/tail sample",
        })
    return result


def parse_csv_edge(data: bytes, *, edge: str) -> dict[str, Any]:
    decoded = data.decode("utf-8-sig", errors="replace")
    lines = decoded.splitlines(keepends=True)
    if edge == "tail":
        # A tail range starts within a record; discard its first partial line.
        if lines:
            lines = lines[1:]
    # For either edge, only complete line records are admitted. A truncated
    # final line is dropped instead of being interpreted as a valid record.
    complete_lines = [line for line in lines if line.endswith(("\n", "\r"))]
    reader = csv.reader(complete_lines)
    parsed = list(reader)
    parsed = [row for row in parsed if row and any(cell.strip() for cell in row)]
    if edge == "head":
        if not parsed:
            return {"headers": [], "rows": [], "error": "no complete header row"}
        headers = [x.strip() for x in parsed[0]]
        body = parsed[1:1 + MAX_CSV_SAMPLE_ROWS]
    else:
        headers = []
        body = parsed[:MAX_CSV_SAMPLE_ROWS]
    return {
        "headers": headers,
        "rows": body,
        "complete_rows_parsed": len(parsed),
        "edge": edge,
    }


def canonical_field(headers: list[str], options: tuple[str, ...]) -> str | None:
    by_key = {re.sub(r"[^a-z0-9]", "", x.lower()): x for x in headers}
    for option in options:
        key = re.sub(r"[^a-z0-9]", "", option.lower())
        if key in by_key:
            return by_key[key]
    return None


def float_value(value: Any) -> float | None:
    try:
        parsed = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def inspect_hf_csv(fetcher: LimitedFetcher) -> dict[str, Any]:
    result: dict[str, Any] = {"key": "huggingface_fii_dii_csv_sample", "schema_status": "NOT_VERIFIED"}
    # Metadata and this source's three requests are independent records. We
    # never download the entire file; only an 8 KiB head and optional 8 KiB tail.
    head_req = fetcher.get(
        HF_FILE_URL, source="hf_file", body_cap=0, method="HEAD", permit_hf_redirect=True
    )
    result["head_request"] = head_req.metadata()
    if head_req.status != "FETCHED" or head_req.http_status != 200:
        result["reason"] = "HEAD request was not a direct/allowed successful response"
        return result
    raw_length = head_req.headers.get("content-length")
    try:
        total_length = int(raw_length) if raw_length is not None else None
    except ValueError:
        total_length = None
    result["content_length"] = total_length
    if total_length is None or total_length <= MAX_HF_RANGE_BYTES:
        result["schema_status"] = "COVERAGE_LEAD_ONLY"
        result["reason"] = "missing/invalid Content-Length or file length <= head-range cap; tail request skipped"
        return result

    head = fetcher.get(
        HF_FILE_URL,
        source="hf_file",
        body_cap=MAX_HF_RANGE_BYTES,
        headers={"Range": f"bytes=0-{MAX_HF_RANGE_BYTES - 1}"},
        permit_hf_redirect=True,
    )
    result["head_range_request"] = head.metadata()
    expected_start, expected_end = 0, MAX_HF_RANGE_BYTES - 1
    validated_head = validate_range_response(head, expected_start, expected_end, total_length)
    result["head_range_validation"] = validated_head
    if not validated_head["pass"]:
        result["schema_status"] = "NOT_VERIFIED"
        result["reason"] = "head Range failed status/Content-Range/length checks"
        return result

    tail_start = total_length - MAX_HF_RANGE_BYTES
    tail_end = total_length - 1
    tail = fetcher.get(
        HF_FILE_URL,
        source="hf_file",
        body_cap=MAX_HF_RANGE_BYTES,
        headers={"Range": f"bytes={tail_start}-{tail_end}"},
        permit_hf_redirect=True,
    )
    result["tail_range_request"] = tail.metadata()
    validated_tail = validate_range_response(tail, tail_start, tail_end, total_length)
    result["tail_range_validation"] = validated_tail
    if not validated_tail["pass"]:
        result["schema_status"] = "NOT_VERIFIED"
        result["reason"] = "tail Range failed status/Content-Range/length checks"
        return result

    head_parsed = parse_csv_edge(head.data, edge="head")
    tail_parsed = parse_csv_edge(tail.data, edge="tail")
    result["head_csv_sample"] = {
        "headers": head_parsed.get("headers", []),
        "sample_row_count": len(head_parsed.get("rows", [])),
        "rows": head_parsed.get("rows", []),
    }
    result["tail_csv_sample"] = {
        "sample_row_count": len(tail_parsed.get("rows", [])),
        "rows": tail_parsed.get("rows", []),
    }
    headers = head_parsed.get("headers", [])
    date_column = canonical_field(headers, ("date", "trade_date", "tradedate", "report_date"))
    fii_buy = canonical_field(headers, ("fii_buy", "fpi_buy", "fii_gross_buy", "fpi_gross_buy"))
    fii_sell = canonical_field(headers, ("fii_sell", "fpi_sell", "fii_gross_sell", "fpi_gross_sell"))
    dii_buy = canonical_field(headers, ("dii_buy", "dii_gross_buy"))
    dii_sell = canonical_field(headers, ("dii_sell", "dii_gross_sell"))
    fields = {
        "date": date_column,
        "fii_or_fpi_buy": fii_buy,
        "fii_or_fpi_sell": fii_sell,
        "dii_buy": dii_buy,
        "dii_sell": dii_sell,
    }
    result["mapped_fields"] = fields
    all_rows = head_parsed.get("rows", []) + tail_parsed.get("rows", [])
    parsed_dates: list[str] = []
    numeric_ok = True
    missing_date_count = 0
    for row in all_rows:
        record = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
        if date_column is None:
            missing_date_count += 1
        else:
            normalized = parse_date(record.get(date_column))
            if normalized:
                parsed_dates.append(normalized)
            else:
                missing_date_count += 1
        for col in (fii_buy, fii_sell, dii_buy, dii_sell):
            if col is None or float_value(record.get(col)) is None:
                numeric_ok = False
    result["sample_date_count"] = len(parsed_dates)
    result["sample_date_min"] = min(parsed_dates) if parsed_dates else None
    result["sample_date_max"] = max(parsed_dates) if parsed_dates else None
    result["missing_sample_date_count"] = missing_date_count
    result["sample_numeric_fields_valid"] = numeric_ok
    source_fields = [h for h in headers if any(token in h.lower() for token in ("source", "origin", "provenance", "seed", "synthetic"))]
    result["provenance_columns"] = source_fields
    sample_all_text = json.dumps(all_rows, ensure_ascii=False).lower()
    if any(marker in sample_all_text for marker in SYNTHETIC_MARKERS):
        result["schema_status"] = "REJECTED_SYNTHETIC"
        result["reason"] = "head/tail sample contains explicit synthetic/seed/placeholder marker"
    elif not all(fields.values()):
        result["schema_status"] = "REJECTED_SCHEMA"
        result["reason"] = "required date, FII/FPI buy/sell and DII buy/sell columns were not all identified"
    elif missing_date_count or not numeric_ok:
        result["schema_status"] = "REJECTED_SCHEMA"
        result["reason"] = "sample rows contain missing dates or nonnumeric required fields"
    else:
        result["schema_status"] = "COVERAGE_LEAD_ONLY"
        result["reason"] = "bounded head/tail schema sample only; source provenance and complete unique-date coverage are not established"
    result["source_file_sha256_not_observed"] = True
    result["head_sample_sha256"] = head.sha256
    result["tail_sample_sha256"] = tail.sha256
    return result


def validate_range_response(
    result: FetchResult, expected_start: int, expected_end: int, total_length: int
) -> dict[str, Any]:
    if result.status != "FETCHED" or result.http_status != 206:
        return {"pass": False, "reason": "HTTP status must be 206"}
    value = result.headers.get("content-range", "")
    match = re.fullmatch(r"bytes\s+(\d+)-(\d+)/(\d+)", value.strip(), flags=re.IGNORECASE)
    if not match:
        return {"pass": False, "reason": "Content-Range missing or malformed"}
    start, end, total = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if start != expected_start or end != expected_end:
        return {"pass": False, "reason": "Content-Range start/end do not match request"}
    if total != total_length:
        return {"pass": False, "reason": "Content-Range total does not match HEAD Content-Length"}
    expected_n = expected_end - expected_start + 1
    if result.bytes_read != expected_n:
        return {"pass": False, "reason": "response byte count does not equal requested range"}
    return {"pass": True, "start": start, "end": end, "total": total, "bytes": expected_n}


def inspect_chirag(fetcher: LimitedFetcher) -> dict[str, Any]:
    result: dict[str, Any] = {"key": "chirag_per_date_json", "schema_status": "NOT_VERIFIED"}
    commit_fetch = fetcher.get(CHIRAG_COMMIT_URL, source="github_api", body_cap=24 * 1024)
    result["commit_request"] = commit_fetch.metadata()
    obj, error = json_from_result(commit_fetch)
    if error or not isinstance(obj, dict):
        result["reason"] = error or "commit response is not an object"
        return result
    commit = str(obj.get("sha") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        result["reason"] = "main branch did not resolve to a full commit SHA"
        return result
    url = CHIRAG_JSON_URL_TEMPLATE.format(commit=commit)
    result["data_url"] = url
    file_fetch = fetcher.get(url, source="github_raw", body_cap=MAX_CHIRAG_JSON_BYTES)
    result["data_request"] = file_fetch.metadata()
    record, error = json_from_result(file_fetch)
    if error:
        result["reason"] = error
        return result
    if isinstance(record, list):
        rows = record
    elif isinstance(record, dict):
        rows = record.get("data", record.get("rows", [record]))
        if not isinstance(rows, list):
            rows = []
    else:
        rows = []
    sample_rows: list[dict[str, Any]] = []
    invalid_reason: str | None = None
    for row in rows[:5]:
        if not isinstance(row, dict):
            invalid_reason = "record is not an object"
            continue
        date_field = next((k for k in ("date", "trade_date", "tradeDate") if k in row), None)
        if not date_field or parse_date(row.get(date_field)) != "2026-10-01":
            invalid_reason = "record date does not match requested date 2026-10-01"
        source = str(row.get("source") or row.get("_source") or "").strip().lower()
        if not source:
            invalid_reason = "record has no explicit source label"
        elif is_synthetic_text(source):
            invalid_reason = "record source is synthetic/placeholder/seeded"
        elif source not in {"nse", "groww", "moneycontrol"}:
            invalid_reason = f"unrecognized source label: {source}"
        numeric_fields = [
            k for k in ("fii_net", "fii_buy", "fii_sell", "dii_net", "dii_buy", "dii_sell")
            if k in row
        ]
        if not numeric_fields or any(float_value(row.get(k)) is None for k in numeric_fields):
            invalid_reason = "required numeric flow fields missing or nonfinite"
        sample_rows.append({
            "date": row.get(date_field) if date_field else None,
            "source": source or None,
            "numeric_fields": {k: row.get(k) for k in numeric_fields},
        })
    result["pinned_commit_sha"] = commit
    result["row_count_returned"] = len(rows)
    result["sample_rows"] = sample_rows
    if not rows:
        result["schema_status"] = "REJECTED_SCHEMA"
        result["reason"] = "no rows in dated JSON"
    elif invalid_reason:
        result["schema_status"] = "REJECTED_PROVENANCE" if "source" in invalid_reason or "synthetic" in invalid_reason else "REJECTED_SCHEMA"
        result["reason"] = invalid_reason
    else:
        result["schema_status"] = "SCHEMA_SAMPLE_PASS"
        result["reason"] = "single-date third-party schema sample; not enough evidence for historical coverage"
    return result


def inspect_directory_metadata(fetcher: LimitedFetcher, key: str, url: str) -> dict[str, Any]:
    fetched = fetcher.get(url, source="github_api", body_cap=MAX_GITHUB_DIRECTORY_BYTES)
    result: dict[str, Any] = {"key": key, **fetched.metadata()}
    obj, error = json_from_result(fetched)
    if error:
        result.update({"schema_status": "NOT_VERIFIED", "reason": error})
        return result
    if not isinstance(obj, list):
        result.update({"schema_status": "REJECTED_SCHEMA", "reason": "directory endpoint did not return a list"})
        return result
    if any(isinstance(entry, dict) and "content" in entry for entry in obj):
        result.update({
            "schema_status": "REJECTED_SCOPE",
            "reason": "directory response unexpectedly contains a content payload",
        })
        return result
    history = next(
        (entry for entry in obj if isinstance(entry, dict) and entry.get("name") == "history.json"),
        None,
    )
    if history is None:
        result.update({"schema_status": "NOT_VERIFIED", "reason": "no history.json metadata entry in data directory"})
        return result
    result.update({
        "schema_status": "COVERAGE_LEAD_ONLY",
        "history_file_metadata": {
            "name": history.get("name"),
            "size": history.get("size"),
            "sha": history.get("sha"),
            "type": history.get("type"),
        },
        "reason": "directory metadata only; raw history content was not requested",
    })
    return result


def inspect_public_page(fetcher: LimitedFetcher, key: str, url: str, source: str, cap: int) -> dict[str, Any]:
    fetched = fetcher.get(url, source=source, body_cap=cap)
    result: dict[str, Any] = {"key": key, **fetched.metadata()}
    if fetched.status != "FETCHED":
        result["schema_status"] = "NOT_VERIFIED"
        result["reason"] = fetched.status
        return result
    result["page_sample"] = html_text_sample(fetched.data)
    result["schema_status"] = "COVERAGE_LEAD_ONLY"
    result["reason"] = "bounded page metadata/table sample only; daily date coverage and source provenance remain unverified"
    return result


def run_sources(fetcher: LimitedFetcher) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 1,
        "specification": SPEC_VERSION,
        "scope": "Finite bounded free-source probe only; no full history, feature/label construction or model fitting.",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": {},
    }
    report["sources"]["cdsl"] = inspect_cdsl_source(fetcher)
    report["sources"]["huggingface_metadata"] = inspect_hf_metadata(fetcher)
    report["sources"]["huggingface_csv_sample"] = inspect_hf_csv(fetcher)
    report["sources"]["chirag_per_date_json"] = inspect_chirag(fetcher)
    report["sources"]["sebi_fpi_archive"] = inspect_public_page(
        fetcher, "sebi_fpi_trade_wise_metadata", SEBI_URL, "sebi", MAX_SEBI_HTML_BYTES
    )
    report["sources"]["nse_fii_dii_page"] = inspect_public_page(
        fetcher, "nse_fii_dii_page_metadata", NSE_URL, "nse", MAX_NSE_HTML_BYTES
    )
    report["sources"]["calcsetu_recent_page"] = inspect_public_page(
        fetcher, "calcsetu_recent_table_metadata", CALCSETU_URL, "calcsetu", MAX_CALCSETU_HTML_BYTES
    )
    report["sources"]["github_history_metadata"] = {
        key: inspect_directory_metadata(fetcher, key, url)
        for key, url in GH_HISTORY_DIR_URLS.items()
    }
    report["global_budget"] = fetcher.budget.as_dict()
    report["global_budget_pass"] = (
        fetcher.budget.initial_requests <= MAX_INITIAL_REQUESTS
        and fetcher.budget.redirect_requests <= MAX_REDIRECT_REQUESTS
        and fetcher.budget.exchanges <= MAX_HTTP_EXCHANGES
        and fetcher.budget.body_bytes_read <= MAX_TOTAL_BODY_BYTES
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded Source Discovery 3 probe; no full history.")
    parser.add_argument(
        "--run-approved-scope",
        action="store_true",
        help="explicit action flag; also requires the guarded workflow authorization environment",
    )
    args = parser.parse_args(argv)
    if not args.run_approved_scope:
        print("NOT RUN: pass --run-approved-scope only from the guarded, approved workflow.")
        return 2
    if os.environ.get("PHASE7_FREE_FLOW_DISCOVERY3_APPROVED") != "1":
        print("FAIL CLOSED: approved workflow authorization environment is absent.", file=sys.stderr)
        return 3

    fetcher = LimitedFetcher()
    report = run_sources(fetcher)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    report_sha = sha256_bytes(serialized)
    REPORT_PATH.write_bytes(serialized)
    summary = {
        "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "report_sha256_without_trailing_newline": report_sha,
        "global_budget": report["global_budget"],
        "global_budget_pass": report["global_budget_pass"],
        "source_statuses": {
            key: value.get("schema_status", value.get("status"))
            for key, value in report["sources"].items()
            if isinstance(value, dict)
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["global_budget_pass"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
