from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
import xlrd
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/reports/extension2_free_flow_source_discovery_3.json"
MAX_EXCHANGES = 18
MAX_INITIAL_REQUESTS = 15
MAX_REDIRECTS = 3
MAX_TOTAL_BYTES = 2 * 1024 * 1024
MAX_RANGE_BYTES = 8 * 1024
MAX_HF_CSV_BYTES = 16 * 1024
MAX_CSV_SAMPLE_ROWS = 10
MAX_VISIBLE_ROWS = 20
HF_COMMIT = "f90f7acad633ba5a803f25cf431fb5f13ce3d162"
CURRENT_SPEC_GIT_BLOB = "4e30415632545c04a2875d627afa0191afe3f383"
HF_PATH = "nifty historical data/fii dii data/fii_dii_2024_to_today.csv"
HF_RESOLVE_URL = (
    "https://huggingface.co/datasets/johnwick3690/stocks/resolve/"
    + HF_COMMIT
    + "/nifty%20historical%20data/fii%20dii%20data/fii_dii_2024_to_today.csv"
)
HF_ALLOWED_HOSTS = {
    "huggingface.co", "www.huggingface.co", "hf.co", "cdn-lfs.huggingface.co",
    "cas-bridge.xethub.hf.co", "cas-server.xethub.hf.co", "us.aws.cdn.hf.co",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NakedOptionResearch/1.0)",
    "Accept": "application/json,text/csv,application/vnd.ms-excel,application/octet-stream,text/html,*/*",
}
PROBE_CAPS = {
    "CDSL-1": 128 * 1024,
    "CDSL-2": 384 * 1024,
    "CDSL-3": 384 * 1024,
    "CDSL-4": 64 * 1024,
    "HF-1": 128 * 1024,
    "CHIRAG-COMMIT": 24 * 1024,
    "CHIRAG-1": 8 * 1024,
    "SEBI-1": 128 * 1024,
    "NSE-1": 128 * 1024,
    "CALCSETU-1": 64 * 1024,
    "GH-META-1A": 64 * 1024,
    "GH-META-1B": 64 * 1024,
}

FIXED_URLS = {
    "CDSL-1": "https://www.cdslindia.com/Publications/ForeignPortInvestor.html",
    "CDSL-2": "https://www.cdslindia.com/downloads/Publications/Latest/Latest_30092024.xls",
    "CDSL-3": "https://www.cdslindia.com/downloads/Publications/Latest/Latest_09102024.xls",
    "CDSL-4": "https://www.cdslindia.com/Publications/FIITrends.aspx",
    "HF-1": f"https://huggingface.co/api/datasets/johnwick3690/stocks/revision/{HF_COMMIT}",
    "CHIRAG-COMMIT": "https://api.github.com/repos/chirag127/fii-dii-activity-api/commits/main",
    "SEBI-1": "https://www.sebi.gov.in/statistics/fpi-investment/trade-wise-equity-data-of-fpi.html",
    "NSE-1": "https://www.nseindia.com/reports/fii-dii/",
    "CALCSETU-1": "https://calcsetu.com/Utility/Diifii/",
    "GH-META-1A": "https://api.github.com/repos/marketcalls/fii-dii-data/contents/data",
    "GH-META-1B": "https://api.github.com/repos/r7sh7/fii-dii-data/contents/data",
}
CHIRAG_DATE = "2026-10-01"
CHIRAG_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/chirag127/fii-dii-activity-api/"
    "{commit}/data/2026-10-01.json"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iso_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def safe_url_for_report(url: str) -> str:
    """Record URL identity without persisting sensitive query parameter values."""
    parsed = urllib.parse.urlsplit(url)
    if not parsed.query:
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    sensitive_tokens = ("token", "sig", "signature", "credential", "auth", "api_key", "apikey", "secret", "password", "expires", "access_key", "key")
    safe_pairs = []
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        safe_pairs.append((key, "[REDACTED]" if any(token in key.lower() for token in sensitive_tokens) else value))
    safe_query = urllib.parse.urlencode(safe_pairs)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, safe_query, ""))


def redact_sensitive_json(value: Any) -> Any:
    """Recursively remove credential-like keys and sanitize URLs in source JSON."""
    sensitive_exact = {"authorization", "cookie", "token", "secret", "password", "credential", "api_key", "apikey", "access_key", "private_key", "signature", "sig", "signed_token"}
    sensitive_suffixes = ("_token", "_secret", "_password", "_credential", "_api_key", "_apikey", "_access_key", "_private_key", "_signature", "_sig")
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in sensitive_exact or any(lowered.endswith(suffix) for suffix in sensitive_suffixes):
                continue
            result[str(key)] = redact_sensitive_json(child)
        return result
    if isinstance(value, list):
        return [redact_sensitive_json(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", value)
        if value.lower().startswith(("https://", "http://")):
            try:
                return safe_url_for_report(value)
            except Exception:
                return "[REDACTED_URL]"
    return value


def is_registered_probe_url(probe_id: str, url: str, method: str) -> bool:
    """Reject URLs and HTTP methods outside the frozen discovery inventory."""
    if probe_id in FIXED_URLS:
        return url == FIXED_URLS[probe_id] and method == "GET"
    if probe_id == "HF-2-HEAD":
        return url == HF_RESOLVE_URL and method == "HEAD"
    if probe_id in {"HF-2-HEAD-RANGE", "HF-2-TAIL-RANGE"}:
        return url == HF_RESOLVE_URL and method == "GET"
    if probe_id == "CHIRAG-1" and method == "GET":
        parsed = urllib.parse.urlsplit(url)
        pattern = rf"/chirag127/fii-dii-activity-api/[0-9a-f]{{40}}/data/{re.escape(CHIRAG_DATE)}\.json"
        return parsed.scheme == "https" and parsed.hostname == "raw.githubusercontent.com" and bool(re.fullmatch(pattern, parsed.path))
    return False


def validate_content_range_response(
    response: dict[str, Any], start: int, end: int, total_length: int,
) -> tuple[bool, str]:
    if response.get("status") != "FETCHED" or response.get("http_status") != 206:
        return False, "range requires HTTP 206; HTTP 200 is always rejected"
    match = re.fullmatch(r"bytes\s+(\d+)-(\d+)/(\d+)", str(response.get("content_range") or ""), flags=re.I)
    if not match:
        return False, "missing or malformed Content-Range"
    got_start, got_end, total = map(int, match.groups())
    if (got_start, got_end, total) != (start, end, total_length):
        return False, "Content-Range does not exactly match requested inclusive range and HEAD length"
    if len(response.get("body", b"")) != end - start + 1:
        return False, "body byte count does not match the inclusive range length"
    return True, "PASS"


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    def __init__(self) -> None:
        self.initial_requests = 0
        self.redirects = 0
        self.exchanges = 0
        self.bytes_read = 0
        self.exhausted = False
        self.audit: list[dict[str, Any]] = []

    @property
    def remaining_bytes(self) -> int:
        return MAX_TOTAL_BYTES - self.bytes_read

    def start_initial(self, probe_id: str, url: str) -> None:
        if self.exhausted:
            raise BudgetExceeded("global budget already exhausted")
        if self.initial_requests >= MAX_INITIAL_REQUESTS:
            self.exhausted = True
            raise BudgetExceeded("initial request limit exceeded")
        self.initial_requests += 1
        self.audit.append({
            "probe_id": probe_id, "url": url,
            "kind": "initial", "timestamp_utc": iso_utc(),
        })

    def start_redirect(self, probe_id: str, url: str) -> None:
        if self.exhausted:
            raise BudgetExceeded("global budget already exhausted")
        if self.redirects >= MAX_REDIRECTS:
            self.exhausted = True
            raise BudgetExceeded("redirect limit exceeded")
        self.redirects += 1
        self.audit.append({
            "probe_id": probe_id, "url": url,
            "kind": "redirect", "timestamp_utc": iso_utc(),
        })

    def start_exchange(self) -> None:
        if self.exchanges >= MAX_EXCHANGES:
            self.exhausted = True
            raise BudgetExceeded("HTTP exchange limit exceeded")
        self.exchanges += 1

    def record_bytes(self, count: int) -> None:
        if count < 0 or count > self.remaining_bytes:
            self.exhausted = True
            raise BudgetExceeded("global response-body budget exceeded")
        self.bytes_read += count
        if self.bytes_read >= MAX_TOTAL_BYTES:
            self.exhausted = True


class NoAutoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LimitedHTTP:
    """Explicit no-auto-redirect HTTP client with shared request and byte budgets."""

    def __init__(self, budget: Budget | None = None) -> None:
        self.budget = budget or Budget()
        self.opener = urllib.request.build_opener(NoAutoRedirect())

    def request(
        self,
        probe_id: str,
        url: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        max_body_bytes: int,
        hf_redirects: bool = False,
    ) -> dict[str, Any]:
        if not is_registered_probe_url(probe_id, url, method):
            return {
                "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                "error": "URL or HTTP method is not registered in the frozen probe inventory",
                "history": [], "bytes_read": 0,
            }
        if probe_id in {"HF-2-HEAD-RANGE", "HF-2-TAIL-RANGE"}:
            allowed_cap = MAX_RANGE_BYTES
            allowed_headers = {"range"}
        elif probe_id == "HF-2-HEAD":
            allowed_cap = 0
            allowed_headers = set()
        else:
            allowed_cap = PROBE_CAPS.get(probe_id, -1)
            allowed_headers = set()
        if max_body_bytes < 0 or allowed_cap < 0 or max_body_bytes > allowed_cap:
            return {
                "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                "error": f"requested body cap exceeds the frozen {allowed_cap}-byte cap",
                "history": [], "bytes_read": 0,
            }
        if hf_redirects and probe_id not in {"HF-2-HEAD", "HF-2-HEAD-RANGE", "HF-2-TAIL-RANGE"}:
            return {
                "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                "error": "redirect following is registered only for HF HEAD/range probes",
                "history": [], "bytes_read": 0,
            }
        supplied = headers or {}
        if any(k.lower() not in allowed_headers for k in supplied):
            return {
                "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                "error": "unregistered request header for this probe",
                "history": [], "bytes_read": 0,
            }
        range_values = [v for k, v in supplied.items() if k.lower() == "range"]
        if range_values and probe_id not in {"HF-2-HEAD-RANGE", "HF-2-TAIL-RANGE"}:
            return {
                "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                "error": "Range is only permitted for the two registered HF range probes",
                "history": [], "bytes_read": 0,
            }
        if probe_id == "HF-2-HEAD-RANGE" and range_values != [f"bytes=0-{MAX_RANGE_BYTES - 1}"]:
            return {
                "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                "error": "head Range must be exactly the first 8 KiB",
                "history": [], "bytes_read": 0,
            }
        if probe_id == "HF-2-TAIL-RANGE":
            match = re.fullmatch(r"bytes=(\d+)-(\d+)", range_values[0]) if len(range_values) == 1 else None
            if not match:
                return {
                    "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                    "error": "tail Range must be one inclusive byte range",
                    "history": [], "bytes_read": 0,
                }
            range_start, range_end = map(int, match.groups())
            if range_start <= 0 or range_end < range_start or range_end - range_start + 1 != MAX_RANGE_BYTES:
                return {
                    "probe_id": probe_id, "url": url, "status": "REJECTED_SCOPE",
                    "error": "tail Range must be exactly 8 KiB and start after byte zero",
                    "history": [], "bytes_read": 0,
                }
        try:
            self.budget.start_initial(probe_id, url)
        except BudgetExceeded as exc:
            return self._failure(probe_id, safe_url_for_report(url), "BUDGET_EXCEEDED", str(exc), [])
        current_url = url
        redirect_count = 0
        exchange_kind = "initial"
        history: list[dict[str, Any]] = []
        while True:
            if self.budget.exchanges >= MAX_EXCHANGES:
                self.budget.exhausted = True
                return self._failure(probe_id, url, "BUDGET_EXCEEDED", "HTTP exchange cap reached", history)
            request_headers = dict(HEADERS)
            if headers:
                request_headers.update(headers)
            # Never forward credentials or cookies, including caller-supplied values.
            for key in list(request_headers):
                if key.lower() in {"authorization", "cookie", "proxy-authorization"}:
                    request_headers.pop(key, None)
            req = urllib.request.Request(current_url, headers=request_headers, method=method)
            self.budget.start_exchange()
            started = iso_utc()
            try:
                try:
                    response = self.opener.open(req, timeout=25)
                except urllib.error.HTTPError as exc:
                    response = exc
                status = int(getattr(response, "status", getattr(response, "code", 0)))
                response_headers = response.headers
                location = response_headers.get("Location")
                content_type = response_headers.get("Content-Type", "")
                length_header = response_headers.get("Content-Length")
                body = b""
                body_cap = 0 if method == "HEAD" else min(max_body_bytes + 1, self.budget.remaining_bytes)
                if method != "HEAD" and body_cap > 0:
                    body = response.read(body_cap)
                    self.budget.record_bytes(len(body))
                try:
                    response.close()
                except Exception:
                    pass
                record = {
                    "probe_id": probe_id, "url": safe_url_for_report(current_url), "method": method,
                    "status": status, "content_type": content_type,
                    "content_length_header": length_header,
                    "content_range": response_headers.get("Content-Range"),
                    "bytes_read": len(body), "sha256": sha256_bytes(body),
                    "timestamp_utc": started,
                }
                history.append(record)
                if len(body) > max_body_bytes:
                    return {
                        "probe_id": probe_id, "url": url, "status": "REJECTED_TOO_LARGE",
                        "http_status": status, "bytes_read": sum(int(x["bytes_read"]) for x in history),
                        "sha256": sha256_bytes(body), "history": history,
                        "error": f"response exceeded {max_body_bytes}-byte body cap",
                    }
                if status in {301, 302, 303, 307, 308}:
                    if not location:
                        return {
                            "probe_id": probe_id, "url": url, "status": "REJECTED_REDIRECT",
                            "history": history, "error": "redirect lacks Location header",
                        }
                    if not hf_redirects or redirect_count >= 1:
                        return {
                            "probe_id": probe_id, "url": url, "status": "REJECTED_REDIRECT",
                            "history": history,
                            "error": "redirect not authorized or redirect-hop cap reached",
                        }
                    next_url = urllib.parse.urljoin(current_url, location)
                    parsed = urllib.parse.urlsplit(next_url)
                    if (
                        parsed.scheme != "https"
                        or parsed.hostname not in HF_ALLOWED_HOSTS
                        or parsed.username is not None
                        or parsed.password is not None
                        or parsed.port not in {None, 443}
                    ):
                        return {
                            "probe_id": probe_id, "url": url, "status": "REJECTED_REDIRECT_HOST",
                            "history": history,
                            "error": "redirect target is not in the exact HTTPS Hugging Face allowlist",
                        }
                    redirect_count += 1
                    current_url = next_url
                    exchange_kind = "redirect"
                    self.budget.start_redirect(probe_id, safe_url_for_report(current_url))
                    # Preserve non-sensitive headers such as Range, but never credentials.
                    headers = {
                        k: v for k, v in (headers or {}).items()
                        if k.lower() not in {"authorization", "cookie", "proxy-authorization"}
                    }
                    continue
                result = {
                    "probe_id": probe_id, "url": safe_url_for_report(url), "final_url": safe_url_for_report(current_url),
                    "status": "FETCHED" if 200 <= status < 300 else "HTTP_ERROR",
                    "http_status": status, "content_type": content_type,
                    "content_length_header": length_header,
                    "content_range": response_headers.get("Content-Range"),
                    "bytes_read": sum(int(x["bytes_read"]) for x in history),
                    "sha256": sha256_bytes(body), "body": body, "history": history,
                }
                if method == "HEAD" and status == 200:
                    result["bytes_read"] = 0
                    result["sha256"] = sha256_bytes(b"")
                if self.budget.remaining_bytes == 0:
                    self.budget.exhausted = True
                return result
            except BudgetExceeded as exc:
                return self._failure(probe_id, url, "BUDGET_EXCEEDED", str(exc), history)
            except Exception as exc:
                return self._failure(
                    probe_id, url, "FETCH_FAILED",
                    f"{type(exc).__name__}: {str(exc)[:240]}", history,
                )

    def _failure(self, probe_id: str, url: str, status: str, error: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "probe_id": probe_id, "url": url, "status": status,
            "error": error, "history": history,
            "bytes_read": sum(int(x.get("bytes_read", 0)) for x in history),
        }


def parse_date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}(?:$|T| )", raw):
        try:
            return dt.date.fromisoformat(raw[:10]).isoformat()
        except ValueError:
            return ""
    for fmt, candidate in [
        ("%d-%m-%Y", raw[:10]), ("%d/%m/%Y", raw[:10]),
        ("%d-%b-%Y", raw[:11].title()), ("%d %b %Y", raw[:11].title()),
        ("%d-%B-%Y", raw[:20].title()), ("%d %B %Y", raw[:20].title()),
        ("%Y/%m/%d", raw[:10]),
    ]:
        try:
            return dt.datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


class LinkTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.rows: list[list[str]] = []
        self._href: str | None = None
        self._anchor_text: list[str] = []
        self._row: list[str] = []
        self._cell: list[str] = []
        self._in_row = False
        self._in_cell = False
        self._in_anchor = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag.lower() == "a" and a.get("href"):
            self._href = a["href"]
            self._anchor_text = []
            self._in_anchor = True
        elif tag.lower() == "tr":
            self._row = []
            self._in_row = True
        elif tag.lower() in {"td", "th"} and self._in_row:
            self._cell = []
            self._in_cell = True

    def handle_data(self, data: str) -> None:
        if self._in_anchor:
            self._anchor_text.append(data.strip())
        if self._in_cell:
            self._cell.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "a" and self._in_anchor:
            if self._href:
                self.links.append({"href": self._href, "text": " ".join(x for x in self._anchor_text if x)})
            self._href = None
            self._anchor_text = []
            self._in_anchor = False
        elif t in {"td", "th"} and self._in_cell:
            self._row.append(" ".join(x for x in self._cell if x))
            self._cell = []
            self._in_cell = False
        elif t == "tr" and self._in_row:
            if any(self._row):
                self.rows.append(self._row)
            self._row = []
            self._in_row = False


def date_links(parser: LinkTableParser) -> list[dict[str, str]]:
    out = []
    pattern = re.compile(r"(?:\d{2}[/-]\d{2}[/-]\d{4}|20\d{2}-\d{2}-\d{2}|(?:Latest_)?\d{8})", re.I)
    for link in parser.links:
        if pattern.search(link["href"]) or pattern.search(link["text"]):
            sanitized = dict(link)
            sanitized["href"] = safe_url_for_report(link["href"])
            out.append(sanitized)
    return out[:MAX_VISIBLE_ROWS]


def valid_date_window(url: str, start: dt.date, end: dt.date) -> bool:
    return (
        start <= end
        and url.startswith("https://")
        and (end - start).days <= 9
    )


def parse_cdsl_xls(data: bytes, expected_date: str, source_url: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "source_url": source_url, "expected_date": expected_date,
        "bytes": len(data), "sha256": sha256_bytes(data),
        "source_semantics": "FPI_ONLY", "vintage_limitation": "custodian-reported confirmed data for trades on/up to prior trading days",
    }
    try:
        book = xlrd.open_workbook(file_contents=data, on_demand=True)
    except Exception as exc:
        return {**report, "status": "NOT_VERIFIED", "reason": f"XLS parse failed: {type(exc).__name__}"}
    grid: list[list[str]] = []
    for sheet in book.sheets()[:4]:
        for row_i in range(min(sheet.nrows, 100)):
            vals = [str(sheet.cell_value(row_i, col_i)).strip() for col_i in range(min(sheet.ncols, 20))]
            if any(vals):
                grid.append(vals)
        if len(grid) >= 100:
            break
    book.release_resources()
    flattened = "\n".join(" | ".join(row) for row in grid)
    found_dates = {parse_date(m.group(0)) for m in re.finditer(r"\b\d{1,2}[-/ ]\w{2,9}[-/ ]\d{4}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b", flattened)}
    found_dates.discard("")
    date_ok = expected_date in found_dates or any(expected_date.replace("-", "") in re.sub(r"\D", "", x) for x in found_dates)
    equity_rows: list[dict[str, Any]] = []
    for row_i, row in enumerate(grid):
        text = " ".join(row).lower()
        if "equity" in text and ("stock exchange" in text or "stockexchange" in text or "cash market" in text):
            equity_rows.append({"row": row_i, "values": row[:20]})
    flow_labels: dict[str, list[dict[str, Any]]] = {"buy": [], "sell": [], "net": []}
    for row_i, row in enumerate(grid):
        for col_i, value in enumerate(row):
            low = value.lower()
            if any(token in low for token in ("purchase", "purchases", "buy", "bought")):
                flow_labels["buy"].append({"row": row_i, "column": col_i, "label": value[:100]})
            if any(token in low for token in ("sale", "sales", "sell", "sold")):
                flow_labels["sell"].append({"row": row_i, "column": col_i, "label": value[:100]})
            if "net" in low and any(token in low for token in ("investment", "invest", "value")):
                flow_labels["net"].append({"row": row_i, "column": col_i, "label": value[:100]})

    def numeric_cell(raw: Any) -> float | None:
        value = str(raw or "").strip().replace(",", "").replace("₹", "")
        value = re.sub(r"\s*(?:cr|crore|crores)$", "", value, flags=re.I).strip()
        if not value:
            return None
        try:
            parsed = float(value)
        except ValueError:
            return None
        return parsed if float("-inf") < parsed < float("inf") else None

    flow_value_samples: list[dict[str, Any]] = []
    numeric_flow_groups: set[str] = set()
    for equity in equity_rows:
        values = equity["values"]
        for group, candidates in flow_labels.items():
            for label_info in candidates:
                col_i = label_info["column"]
                if col_i >= len(values) or label_info["row"] == equity["row"]:
                    continue
                raw_value = values[col_i]
                parsed_value = numeric_cell(raw_value)
                if parsed_value is not None:
                    numeric_flow_groups.add(group)
                flow_value_samples.append({
                    "equity_row": equity["row"], "label_row": label_info["row"],
                    "group": group, "column": col_i, "label": label_info["label"],
                    "raw_value": raw_value[:100], "numeric_value": parsed_value,
                })
                if len(flow_value_samples) >= 30:
                    break
            if len(flow_value_samples) >= 30:
                break
        if len(flow_value_samples) >= 30:
            break
    # Preserve candidate value mappings for independent review. Grouped XLS
    # headers can be ambiguous; these candidates are not accepted feature inputs.
    mapping_ok = all(group in numeric_flow_groups for group in ("buy", "sell", "net"))
    report.update({
        "status": "SCHEMA_SAMPLE_PASS" if date_ok and equity_rows else "NOT_VERIFIED",
        "date_check": "PASS" if date_ok else "FAIL_OR_NOT_FOUND",
        "equity_stock_exchange_rows_found": len(equity_rows),
        "equity_row_samples": [{"row": x["row"], "values": x["values"]} for x in equity_rows[:3]],
        "flow_field_label_candidates": {k: v[:10] for k, v in flow_labels.items()},
        "flow_field_label_coverage": {k: bool(v) for k, v in flow_labels.items()},
        "candidate_flow_value_samples": flow_value_samples[:30],
        "numeric_flow_groups_with_candidate_values": sorted(numeric_flow_groups),
        "numeric_flow_mapping_status": "CANDIDATE_NUMERIC_VALUES_EXTRACTED_NOT_ACCEPTED_FOR_FEATURE_BUILD" if mapping_ok else "NOT_VERIFIED_REQUIRES_HEADER_RECONCILIATION",
        "grid_preview": grid[:15],
        "reason": None if date_ok and equity_rows else "could not validate expected report date and equity stock-exchange row together",
    })
    return report


def inspect_html_page(client: LimitedHTTP, probe_id: str, url: str, cap: int, *, row_limit: int | None = None) -> dict[str, Any]:
    r = client.request(probe_id, url, max_body_bytes=cap)
    summary = {k: v for k, v in r.items() if k != "body"}
    if r.get("status") != "FETCHED":
        return {**summary, "schema_status": "NOT_VERIFIED", "reason": r.get("error") or "HTTP response not accepted"}
    parser = LinkTableParser()
    parser.feed(r["body"].decode("utf-8", errors="replace"))
    rows = parser.rows[:row_limit] if row_limit is not None else parser.rows[:MAX_VISIBLE_ROWS]
    summary.update({
        "schema_status": "SCHEMA_SAMPLE_PASS" if parser.links or parser.rows else "PAGE_FETCHED_NO_STATIC_LINK_OR_TABLE",
        "link_count": len(parser.links),
        "dated_links_sample": date_links(parser)[:10],
        "visible_table_rows": len(rows),
        "table_sample": rows[:MAX_VISIBLE_ROWS],
    })
    return summary


def inspect_hf_metadata(client: LimitedHTTP) -> dict[str, Any]:
    r = client.request("HF-1", FIXED_URLS["HF-1"], max_body_bytes=PROBE_CAPS["HF-1"])
    summary = {k: v for k, v in r.items() if k != "body"}
    if r.get("status") != "FETCHED" or r.get("http_status") != 200:
        return {**summary, "schema_status": "NOT_VERIFIED", "reason": "metadata endpoint must return 200 directly"}
    try:
        obj = json.loads(r["body"].decode("utf-8"))
    except Exception as exc:
        return {**summary, "schema_status": "REJECTED_SCHEMA", "reason": f"metadata JSON parse failed: {type(exc).__name__}"}
    siblings = obj.get("siblings", []) if isinstance(obj, dict) else []
    target = next((x for x in siblings if isinstance(x, dict) and x.get("rfilename") == HF_PATH), None)
    if not target:
        return {**summary, "schema_status": "NOT_VERIFIED", "reason": "pinned CSV path absent from revision metadata"}
    card = obj.get("cardData", {}) if isinstance(obj.get("cardData"), dict) else {}
    card_summary = {}
    for key in ("license", "pretty_name", "language", "language_creators", "task_categories"):
        if key in card:
            value = card[key]
            card_summary[key] = value[:20] if isinstance(value, list) else str(value)[:300]
    description = str(obj.get("description") or card.get("description") or "")
    return {
        **summary, "schema_status": "COVERAGE_LEAD_ONLY",
        "dataset_id": "johnwick3690/stocks", "revision": HF_COMMIT,
        "file_path": HF_PATH, "file_metadata": {k: target[k] for k in target if k in {"rfilename", "size", "lfs", "blobId", "lastCommit"}},
        "card_data_keys": sorted(card.keys()),
        "card_data_summary": card_summary,
        "dataset_description_preview": description[:500],
        "license_or_description_present": bool(card or description),
        "provenance_status": "UNVERIFIED_METADATA_ONLY",
        "reason": "metadata identifies a pinned file; schema, unique dates, row provenance and coverage require bounded range samples",
    }


def parse_csv_edge(
    data: bytes,
    label: str,
    header_override: list[str] | None = None,
) -> dict[str, Any]:
    text = data.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    if not lines:
        return {"edge": label, "status": "REJECTED_SCHEMA", "reason": "no CSV lines"}
    try:
        if header_override is None:
            header = next(csv.reader([lines[0]]))
            data_lines = lines[1:]
        else:
            # The head/tail ranges may cut through a CSV line; ignore the first tail line.
            header = header_override
            data_lines = lines[1:]
    except Exception as exc:
        return {"edge": label, "status": "REJECTED_SCHEMA", "reason": type(exc).__name__}
    normalized = [h.strip() for h in header]
    lower = [h.lower() for h in normalized]
    date_candidates = [normalized[i] for i, h in enumerate(lower) if "date" in h or "trade" in h or h == "dt"]
    flow_candidates = [normalized[i] for i, h in enumerate(lower) if any(x in h for x in ("fii", "fpi", "dii", "buy", "sell", "purchase", "sale", "net", "invest"))]
    provenance_candidates = [
        normalized[i] for i, h in enumerate(lower)
        if any(x in h for x in ("source", "provenance", "origin", "provider", "status", "vintage"))
    ]
    row_objects: list[dict[str, str]] = []
    seen_dates: list[str] = []
    invalid_date_rows = 0
    nonnumeric_flow_cells = 0
    nonfinite_flow_cells = 0
    for raw in data_lines:
        if len(row_objects) >= MAX_CSV_SAMPLE_ROWS:
            break
        if not raw.strip():
            continue
        try:
            row = next(csv.reader([raw]))
        except Exception:
            continue
        if len(row) != len(normalized):
            continue
        item = dict(zip(normalized, row))
        row_objects.append(item)
        date_key = next((k for k in date_candidates if item.get(k, "").strip()), None)
        if not date_key or not parse_date(item.get(date_key, "")):
            invalid_date_rows += 1
        else:
            seen_dates.append(parse_date(item[date_key]))
        for key in flow_candidates:
            value = item.get(key, "").strip().replace(",", "")
            if value and any(token in key.lower() for token in ("buy", "sell", "purchase", "sale", "net", "invest")):
                try:
                    parsed_value = float(value)
                    if not math.isfinite(parsed_value):
                        nonfinite_flow_cells += 1
                except ValueError:
                    nonnumeric_flow_cells += 1
    provenance_values = [
        str(row.get(key, "")).strip().lower()
        for row in row_objects for key in provenance_candidates
    ]
    synthetic_tokens = ("historical-seed", "placeholder", "synthetic", "generated", "fallback-without-source")
    synthetic_seen = any(any(token in value for token in synthetic_tokens) for value in provenance_values)
    provenance_status = (
        "REJECTED_SYNTHETIC" if synthetic_seen else
        "PROVENANCE_FIELD_PRESENT_NOT_INDEPENDENTLY_VERIFIED" if provenance_candidates else
        "PROVENANCE_UNVERIFIED"
    )
    sample_keys = list(dict.fromkeys(date_candidates + flow_candidates + provenance_candidates))[:20]
    row_sample = [{key: row.get(key, "") for key in sample_keys} for row in row_objects[:MAX_CSV_SAMPLE_ROWS]]
    edge_status = "REJECTED_NONFINITE_FLOW" if nonfinite_flow_cells else "SAMPLED"
    return {
        "edge": label, "status": edge_status,
        "header": normalized[:60], "parsed_rows": len(row_objects),
        "date_field_candidates": date_candidates, "flow_field_candidates": flow_candidates,
        "provenance_field_candidates": provenance_candidates, "provenance_status": provenance_status,
        "row_sample": row_sample,
        "date_values": seen_dates[:MAX_CSV_SAMPLE_ROWS],
        "duplicate_date_count_within_edge": len(seen_dates) - len(set(seen_dates)),
        "invalid_date_rows": invalid_date_rows,
        "nonnumeric_flow_cells": nonnumeric_flow_cells,
        "nonfinite_flow_cells": nonfinite_flow_cells,
        "raw_edge_sha256": sha256_bytes(data), "raw_edge_bytes": len(data),
    }


def hf_file_probe(client: LimitedHTTP, meta: dict[str, Any]) -> dict[str, Any]:
    url = HF_RESOLVE_URL
    result: dict[str, Any] = {"source": "huggingface", "revision": HF_COMMIT, "file_path": HF_PATH, "url": url}
    head = client.request("HF-2-HEAD", url, method="HEAD", max_body_bytes=0, hf_redirects=True)
    result["head"] = {k: v for k, v in head.items() if k != "body"}
    if head.get("status") != "FETCHED" or head.get("http_status") != 200:
        return {**result, "schema_status": "NOT_VERIFIED", "reason": "HEAD failed or redirect chain rejected"}
    raw_length = head.get("content_length_header")
    try:
        length = int(raw_length)
    except (TypeError, ValueError):
        return {**result, "schema_status": "COVERAGE_LEAD_ONLY", "reason": "HEAD omitted valid Content-Length; tail request skipped"}
    result["content_length"] = length
    if length <= MAX_RANGE_BYTES:
        return {**result, "schema_status": "COVERAGE_LEAD_ONLY", "reason": "file length is no larger than head sample; tail request skipped"}
    if length > 2**63 - 1:
        return {**result, "schema_status": "NOT_VERIFIED", "reason": "invalid Content-Length"}
    head_end = MAX_RANGE_BYTES - 1
    first = client.request(
        "HF-2-HEAD-RANGE", url, headers={"Range": f"bytes=0-{head_end}"},
        max_body_bytes=MAX_RANGE_BYTES, hf_redirects=True,
    )
    tail_start = length - MAX_RANGE_BYTES
    last = client.request(
        "HF-2-TAIL-RANGE", url, headers={"Range": f"bytes={tail_start}-{length-1}"},
        max_body_bytes=MAX_RANGE_BYTES, hf_redirects=True,
    )
    def validate_range(resp: dict[str, Any], start: int, end: int) -> tuple[bool, str]:
        return validate_content_range_response(resp, start, end, length)
    first_ok, first_reason = validate_range(first, 0, head_end)
    last_ok, last_reason = validate_range(last, tail_start, length - 1)
    result["head_range"] = {k: v for k, v in first.items() if k != "body"}
    result["tail_range"] = {k: v for k, v in last.items() if k != "body"}
    if not first_ok or not last_ok:
        return {**result, "schema_status": "NOT_VERIFIED", "head_range_check": first_reason, "tail_range_check": last_reason, "reason": "one or both exact range checks failed"}
    result["head_range_check"] = first_reason
    result["tail_range_check"] = last_reason
    result["head_csv_sample"] = parse_csv_edge(first["body"], "head")
    head_header = result["head_csv_sample"].get("header")
    result["tail_csv_sample"] = (
        parse_csv_edge(last["body"], "tail", header_override=head_header)
        if isinstance(head_header, list)
        else {"edge": "tail", "status": "NOT_VERIFIED", "reason": "head header could not be parsed"}
    )
    result["sampled_csv_bytes"] = len(first.get("body", b"")) + len(last.get("body", b""))
    if result["sampled_csv_bytes"] > MAX_HF_CSV_BYTES:
        return {**result, "schema_status": "NOT_VERIFIED", "reason": "sampled CSV bytes exceeded 16 KiB cap"}
    result["schema_status"] = "COVERAGE_LEAD_ONLY"
    result["reason"] = "bounded head/tail rows are evidence of schema only, not proof of 752 aligned sessions or full-file lineage"
    return result


def validate_chirag_record(obj: Any, expected_date: str = CHIRAG_DATE) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {"status": "REJECTED_SCHEMA", "reason": "payload is not an object"}
    date_keys = [
        k for k in ("date", "trade_date", "tradeDate", "report_date")
        if k in obj and obj.get(k) not in (None, "")
    ]
    if not date_keys:
        return {"status": "REJECTED_SCHEMA", "reason": "no non-empty recognized date field"}
    row_dates = [parse_date(obj.get(k)) for k in date_keys]
    if any(not value for value in row_dates):
        return {
            "status": "REJECTED_SCHEMA", "reason": "one or more recognized date fields are malformed",
            "date_fields": {k: obj.get(k) for k in date_keys}, "observed_dates": row_dates,
        }
    if any(value != expected_date for value in row_dates):
        return {
            "status": "REJECTED_SCHEMA", "reason": "recognized date fields conflict or do not match frozen path date",
            "date_fields": {k: obj.get(k) for k in date_keys}, "observed_dates": row_dates,
        }
    source = str(obj.get("source", "")).strip().lower()
    if source not in {"nse", "groww", "moneycontrol"}:
        return {"status": "REJECTED_PROVENANCE", "reason": "source label missing/unrecognized", "source": source}
    serialized_values = json.dumps(list(obj.values()), sort_keys=True).lower()
    if any(token in serialized_values for token in ("placeholder", "historical-seed", "synthetic", "generated", "fallback-without-source")):
        return {"status": "REJECTED_SYNTHETIC", "reason": "record or provenance indicates generated/placeholder data", "source": source}
    flow_fields: list[str] = []
    bad_flow_fields: list[str] = []

    def visit(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f"{path}.{key}" if path else str(key))
            return
        key = path.rsplit(".", 1)[-1].lower()
        if not any(token in key for token in ("buy", "sell", "purchase", "sale", "net", "invest")):
            return
        flow_fields.append(path)
        if isinstance(value, bool) or value is None:
            bad_flow_fields.append(path)
            return
        if isinstance(value, (int, float)):
            if not (float("-inf") < float(value) < float("inf")):
                bad_flow_fields.append(path)
            return
        if isinstance(value, str):
            raw = value.strip().replace(",", "").replace("₹", "")
            raw = re.sub(r"\s*(?:cr|crore|crores)$", "", raw, flags=re.I).strip()
            try:
                parsed = float(raw)
                if not (float("-inf") < parsed < float("inf")):
                    bad_flow_fields.append(path)
            except ValueError:
                bad_flow_fields.append(path)
            return
        bad_flow_fields.append(path)

    visit(obj)
    if bad_flow_fields:
        return {
            "status": "REJECTED_SCHEMA",
            "reason": "one or more flow-like fields are nonnumeric/nonfinite",
            "source": source, "bad_flow_fields": bad_flow_fields[:20],
        }
    if not flow_fields:
        return {
            "status": "SCHEMA_SAMPLE_PASS",
            "reason": "dated, provenance-labelled JSON but no recognized numeric flow fields; not a G14/G15 data pass",
            "source": source, "recognized_flow_fields": [],
        }
    return {
        "status": "SCHEMA_SAMPLE_PASS",
        "reason": "dated, provenance-labelled single-day JSON; coverage not established",
        "source": source, "recognized_flow_fields": flow_fields[:20],
    }


def inspect_chirag(client: LimitedHTTP) -> dict[str, Any]:
    commit_result = client.request("CHIRAG-COMMIT", FIXED_URLS["CHIRAG-COMMIT"], max_body_bytes=PROBE_CAPS["CHIRAG-COMMIT"])
    commit_summary = {k: v for k, v in commit_result.items() if k != "body"}
    if commit_result.get("status") != "FETCHED" or commit_result.get("http_status") != 200:
        return {"source": "chirag127", "commit_probe": commit_summary, "status": "NOT_VERIFIED", "reason": "could not resolve current branch commit metadata"}
    try:
        commit_obj = json.loads(commit_result["body"].decode("utf-8"))
        commit = commit_obj.get("sha", "")
    except Exception:
        commit = ""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        return {"source": "chirag127", "commit_probe": commit_summary, "status": "NOT_VERIFIED", "reason": "commit SHA malformed"}
    url = CHIRAG_URL_TEMPLATE.format(commit=commit)
    result = client.request("CHIRAG-1", url, max_body_bytes=PROBE_CAPS["CHIRAG-1"])
    summary = {k: v for k, v in result.items() if k != "body"}
    if result.get("status") != "FETCHED" or result.get("http_status") != 200:
        return {"source": "chirag127", "resolved_commit": commit, "commit_probe": commit_summary, "record_probe": summary, "status": "NOT_VERIFIED", "reason": "single-date JSON fetch failed"}
    try:
        obj = json.loads(result["body"].decode("utf-8"))
    except Exception:
        return {"source": "chirag127", "resolved_commit": commit, "record_probe": summary, "status": "REJECTED_SCHEMA", "reason": "response was not JSON"}
    return {
        "source": "chirag127", "resolved_commit": commit, "commit_probe": commit_summary,
        "record_probe": summary, "record_validation": validate_chirag_record(obj),
        "status": "SCHEMA_SAMPLE_PASS" if validate_chirag_record(obj)["status"] == "SCHEMA_SAMPLE_PASS" else validate_chirag_record(obj)["status"],
        "record": redact_sensitive_json(obj) if isinstance(obj, dict) else None,
    }


def parse_gh_directory_metadata(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, list):
        return {"schema_status": "REJECTED_SCHEMA", "reason": "directory endpoint did not return a listing"}
    entries = []
    for entry in obj:
        if not isinstance(entry, dict):
            continue
        # The Contents API directory response should contain metadata only. Inline
        # content would violate this phase's scope and is rejected immediately.
        if "content" in entry:
            return {"schema_status": "REJECTED_SCOPE", "reason": "unexpected inline content payload in directory metadata"}
        if entry.get("type") == "file" and re.search(r"(history|latest|daily|fii|dii).*\.json$", str(entry.get("name", "")), re.I):
            if not isinstance(entry.get("size"), int) or not re.fullmatch(r"[0-9a-f]{40}", str(entry.get("sha", ""))):
                return {"schema_status": "REJECTED_SCHEMA", "reason": "file metadata lacks valid size/SHA"}
            entries.append({k: entry[k] for k in ("name", "path", "size", "sha", "type") if k in entry})
    return {
        "schema_status": "COVERAGE_LEAD_ONLY",
        "directory_file_metadata_sample": entries[:MAX_VISIBLE_ROWS],
        "directory_file_count": len(obj),
        "reason": "metadata only; raw JSON file content was not requested",
    }


def inspect_gh_directory(client: LimitedHTTP, probe_id: str, url: str) -> dict[str, Any]:
    r = client.request(probe_id, url, max_body_bytes=PROBE_CAPS[probe_id])
    summary = {k: v for k, v in r.items() if k != "body"}
    if r.get("status") != "FETCHED" or r.get("http_status") != 200:
        return {**summary, "schema_status": "NOT_VERIFIED", "reason": "directory metadata call failed"}
    try:
        obj = json.loads(r["body"].decode("utf-8"))
    except Exception:
        return {**summary, "schema_status": "REJECTED_SCHEMA", "reason": "directory metadata was not JSON"}
    return {**summary, **parse_gh_directory_metadata(obj)}


def report_main() -> dict[str, Any]:
    budget = Budget()
    client = LimitedHTTP(budget)
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "EXTENSION2_FREE_FLOW_SOURCE_DISCOVERY_3",
        "generated_at_utc": iso_utc(),
        "scope": "Bounded free-source metadata/schema probe only; no full history, feature table, labels, model fits, prediction metrics or final-holdout access.",
        "spec_git_blob": CURRENT_SPEC_GIT_BLOB,
        "sources": {},
    }
    # Static CDSL archive index and two fixed single-day XLS reports.
    report["sources"]["CDSL-1"] = inspect_html_page(client, "CDSL-1", FIXED_URLS["CDSL-1"], PROBE_CAPS["CDSL-1"])
    for probe_id, expected_date in (("CDSL-2", "2024-09-30"), ("CDSL-3", "2024-10-09")):
        url = FIXED_URLS[probe_id]
        r = client.request(probe_id, url, max_body_bytes=PROBE_CAPS[probe_id])
        summary = {k: v for k, v in r.items() if k != "body"}
        if r.get("status") == "FETCHED" and r.get("http_status") == 200:
            summary["report_probe"] = parse_cdsl_xls(r["body"], expected_date, url)
            summary["schema_status"] = summary["report_probe"]["status"]
        else:
            summary["schema_status"] = "NOT_VERIFIED"
            summary["reason"] = r.get("error") or "XLS download not accepted"
        report["sources"][probe_id] = summary
    report["sources"]["CDSL-4"] = inspect_html_page(client, "CDSL-4", FIXED_URLS["CDSL-4"], PROBE_CAPS["CDSL-4"])
    report["sources"]["HF-1"] = inspect_hf_metadata(client)
    report["sources"]["HF-2"] = hf_file_probe(client, report["sources"]["HF-1"])
    report["sources"]["CHIRAG-1"] = inspect_chirag(client)
    report["sources"]["SEBI-1"] = inspect_html_page(client, "SEBI-1", FIXED_URLS["SEBI-1"], PROBE_CAPS["SEBI-1"])
    report["sources"]["NSE-1"] = inspect_html_page(client, "NSE-1", FIXED_URLS["NSE-1"], PROBE_CAPS["NSE-1"])
    report["sources"]["CALCSETU-1"] = inspect_html_page(client, "CALCSETU-1", FIXED_URLS["CALCSETU-1"], PROBE_CAPS["CALCSETU-1"], row_limit=MAX_VISIBLE_ROWS)
    report["sources"]["GH-META-1A"] = inspect_gh_directory(client, "GH-META-1A", FIXED_URLS["GH-META-1A"])
    report["sources"]["GH-META-1B"] = inspect_gh_directory(client, "GH-META-1B", FIXED_URLS["GH-META-1B"])
    report["request_budget"] = {
        "initial_requests": budget.initial_requests,
        "redirects": budget.redirects,
        "http_exchanges": budget.exchanges,
        "response_body_bytes_read": budget.bytes_read,
        "max_initial_requests": MAX_INITIAL_REQUESTS,
        "max_redirects": MAX_REDIRECTS,
        "max_http_exchanges": MAX_EXCHANGES,
        "max_total_body_bytes": MAX_TOTAL_BYTES,
        "budget_exhausted": budget.exhausted,
        "request_audit": budget.audit[:MAX_EXCHANGES],
    }
    report["result_sha256_excludes_self_field"] = True
    return report


def main() -> None:
    result = report_main()
    result["report_sha256"] = sha256_bytes(json.dumps(result, indent=2, sort_keys=True).encode("utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "report_path": str(OUT.relative_to(ROOT)),
        "report_sha256": sha256_bytes(OUT.read_bytes()),
        "request_budget": result["request_budget"],
        "source_status": {k: v.get("schema_status", v.get("status", v.get("record_validation", {}).get("status")))
                          for k, v in result["sources"].items()},
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
