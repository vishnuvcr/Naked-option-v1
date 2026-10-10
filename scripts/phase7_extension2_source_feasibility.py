from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data/reports/extension2_gate_a_source_feasibility.json"
MAX_BYTES = 12_000_000
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NakedOptionResearch/1.0)",
    "Accept": "application/json,text/csv,application/zip,application/octet-stream,text/html,*/*",
    "Referer": "https://www.nseindia.com/all-reports-derivatives",
}
ARCHIVES = [
    {
        "key": "legacy_fo_2024_07_05",
        "date": "2024-07-05",
        "format": "legacy",
        "official_urls": [
            "https://archives.nseindia.com/content/historical/DERIVATIVES/2024/JUL/fo05JUL2024bhav.csv.zip",
            "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/JUL/fo05JUL2024bhav.csv.zip",
        ],
        "mirror_url": "https://raw.githubusercontent.com/SantoshSrinivas79/NSE-FNO-Data-bank/main/data/2024/07/fo05JUL2024bhav.csv.zip",
    },
    {
        "key": "udiff_fo_2024_07_08",
        "date": "2024-07-08",
        "format": "udiff",
        "official_urls": [
            "https://archives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv.zip",
            "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv.zip",
        ],
        "mirror_url": "https://raw.githubusercontent.com/SantoshSrinivas79/NSE-FNO-Data-bank/main/data/2024/07/BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv.zip",
    },
]
PAGES = [
    ("nse_fii_dii_page", "https://www.nseindia.com/reports/fii-dii"),
    ("nse_historical_index_page", "https://www.nseindia.com/all-reports"),
    ("nse_advances_declines_page", "https://www.nseindia.com/historical/advances-declines"),
    ("nse_advances_declines_alt", "https://www.nse.in/historical/advances-declines"),
]
APIS = [
    ("nse_fii_dii_api", "https://www.nseindia.com/api/fiidiiTradeReact"),
    ("nse_sector_index_sample", "https://www.nseindia.com/api/historical/indicesHistory?indexType=NIFTY%20AUTO&from=01-07-2024&to=10-07-2024"),
]


class TableSampler(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self.in_row = True
            self.current_row = []
        elif tag.lower() in {"td", "th"} and self.in_row:
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"td", "th"} and self.in_cell:
            self.current_row.append(" ".join(x for x in self.current_cell if x))
            self.in_cell = False
        elif tag.lower() == "tr" and self.in_row:
            if any(self.current_row):
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_row = False


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, timeout: int = 30) -> tuple[bytes | None, dict[str, Any]]:
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(MAX_BYTES + 1)
            meta = {
                "url": url,
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type", ""),
                "content_length_header": response.headers.get("Content-Length"),
                "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
        if len(data) > MAX_BYTES:
            return None, {**meta, "status": "REJECTED_TOO_LARGE", "bytes_read": len(data)}
        return data, {**meta, "status": "FETCHED", "bytes": len(data), "sha256": sha256_bytes(data)}
    except Exception as exc:  # source feasibility must record all source failures
        return None, {
            "url": url,
            "status": "FETCH_FAILED",
            "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "error": str(exc)[:400],
        }


def archive_schema(data: bytes, spec: dict[str, str], source: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "key": spec["key"],
        "requested_trade_date": spec["date"],
        "format": spec["format"],
        "source_used": source,
        "zip_sha256": sha256_bytes(data),
        "zip_bytes": len(data),
    }
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                return {**result, "schema_status": "FAIL", "reason": f"expected exactly one CSV, found {len(names)}"}
            csv_bytes = zf.read(names[0])
        text = csv_bytes.decode("utf-8-sig", errors="strict")
        reader = csv.DictReader(io.StringIO(text))
        headers = [str(h).strip() for h in (reader.fieldnames or [])]
        rows = list(reader)
        if spec["format"] == "legacy":
            required = ["INSTRUMENT", "SYMBOL", "EXPIRY_DT", "STRIKE_PR", "OPTION_TYP", "CLOSE", "CONTRACTS", "OPEN_INT", "TIMESTAMP"]
            date_ok = bool(rows) and str(rows[0].get("TIMESTAMP", "")).upper() == "05-JUL-2024"
            option_rows = [
                r for r in rows
                if str(r.get("INSTRUMENT", "")).strip() == "OPTIDX"
                and str(r.get("SYMBOL", "")).strip() == "NIFTY"
                and str(r.get("OPTION_TYP", "")).strip() in {"CE", "PE"}
            ]
        else:
            required = ["TradDt", "Sgmt", "TckrSymb", "XpryDt", "StrkPric", "OptnTp", "ClsPric", "TtlTradgVol", "OpnIntrst"]
            date_ok = bool(rows) and str(rows[0].get("TradDt", ""))[:10] in {"2024-07-08", "08-Jul-2024"}
            option_rows = [
                r for r in rows
                if str(r.get("Sgmt", "")).strip() == "FO"
                and str(r.get("TckrSymb", "")).strip() == "NIFTY"
                and str(r.get("OptnTp", "")).strip() in {"CE", "PE"}
            ]
        missing = sorted(set(required) - set(headers))
        result.update({
            "csv_entry": names[0],
            "csv_sha256": sha256_bytes(csv_bytes),
            "csv_bytes": len(csv_bytes),
            "row_count": len(rows),
            "column_count": len(headers),
            "headers": headers,
            "missing_required_columns": missing,
            "requested_date_check": bool(date_ok),
            "nifty_index_option_rows": len(option_rows),
            "option_sample": [
                {k: r.get(k) for k in (["TIMESTAMP", "INSTRUMENT", "SYMBOL", "EXPIRY_DT", "STRIKE_PR", "OPTION_TYP", "CLOSE", "CONTRACTS", "OPEN_INT"] if spec["format"] == "legacy" else ["TradDt", "Sgmt", "TckrSymb", "XpryDt", "StrkPric", "OptnTp", "ClsPric", "TtlTradgVol", "OpnIntrst"])}
                for r in option_rows[:3]
            ],
        })
        result["schema_status"] = "PASS" if not missing and date_ok and option_rows else "FAIL"
        if missing:
            result["reason"] = "missing required columns"
        elif not date_ok:
            result["reason"] = "trade-date validation failed"
        elif not option_rows:
            result["reason"] = "no NIFTY index-option rows found"
    except Exception as exc:
        result.update({"schema_status": "FAIL", "reason": f"{type(exc).__name__}: {str(exc)[:300]}"})
    return result


def inspect_archive(spec: dict[str, str]) -> dict[str, Any]:
    attempts = []
    for url in spec["official_urls"]:
        data, meta = fetch_bytes(url, timeout=45)
        attempts.append(meta)
        if data is not None:
            parsed = archive_schema(data, spec, "official_nse_archive")
            return {"attempts": attempts, **parsed}
    data, meta = fetch_bytes(spec["mirror_url"], timeout=45)
    attempts.append(meta)
    if data is not None:
        parsed = archive_schema(data, spec, "third_party_github_mirror")
        return {"attempts": attempts, **parsed}
    return {
        "key": spec["key"],
        "requested_trade_date": spec["date"],
        "format": spec["format"],
        "attempts": attempts,
        "schema_status": "NOT_VERIFIED",
        "reason": "official archives and public mirror could not be fetched",
    }


def inspect_page(key: str, url: str) -> dict[str, Any]:
    data, meta = fetch_bytes(url, timeout=30)
    if data is None:
        return {"key": key, **meta, "schema_status": "NOT_VERIFIED"}
    text = data.decode("utf-8", errors="replace")
    parser = TableSampler()
    parser.feed(text)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
    return {
        "key": key,
        **meta,
        "page_title": title[:200],
        "html_table_row_count": len(parser.rows),
        "html_table_sample": parser.rows[:8],
        "schema_status": "PAGE_FETCHED_TABLE_REQUIRES_REVIEW" if parser.rows else "PAGE_FETCHED_NO_STATIC_TABLE",
    }


def inspect_api(key: str, url: str) -> dict[str, Any]:
    data, meta = fetch_bytes(url, timeout=30)
    if data is None:
        return {"key": key, **meta, "schema_status": "NOT_VERIFIED"}
    text = data.decode("utf-8", errors="replace")
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            sample = obj[:5]
            keys = sorted({k for row in obj[:20] if isinstance(row, dict) for k in row})
            nrows = len(obj)
        elif isinstance(obj, dict):
            sample = obj.get("data", obj.get("rows", []))[:5] if isinstance(obj.get("data", obj.get("rows", [])), list) else []
            keys = sorted(obj.keys())
            nrows = len(obj.get("data", [])) if isinstance(obj.get("data"), list) else None
        else:
            sample, keys, nrows = [], [], None
        return { "key": key, **meta, "schema_status": "JSON_PARSED", "top_level_type": type(obj).__name__, "row_count_if_exposed": nrows, "keys": keys[:80], "sample": sample }
    except json.JSONDecodeError:
        parser = TableSampler()
        parser.feed(text)
        return { "key": key, **meta, "schema_status": "NON_JSON_RESPONSE", "body_prefix": text[:300], "html_table_row_count": len(parser.rows), "html_table_sample": parser.rows[:5] }


def main() -> None:
    report: dict[str, Any] = {
        "schema_version": 1,
        "gate": "A_SOURCE_FEASIBILITY_ONLY",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "Two single-day F&O archive samples and small public-page/API responses only; no full history, labels, features or model fitting.",
        "sources": [],
    }
    for spec in ARCHIVES:
        report["sources"].append(inspect_archive(spec))
    for key, url in PAGES:
        report["sources"].append(inspect_page(key, url))
    for key, url in APIS:
        report["sources"].append(inspect_api(key, url))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "source_count": len(report["sources"]),
        "fno_schema": {x.get("key"): x.get("schema_status") for x in report["sources"] if x.get("format")},
        "report_sha256": sha256_bytes(REPORT_PATH.read_bytes()),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
