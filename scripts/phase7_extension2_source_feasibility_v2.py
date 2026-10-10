from __future__ import annotations

import csv
import datetime as dt
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from phase7_extension2_source_feasibility import TableSampler, fetch_bytes, sha256_bytes

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "data/reports/extension2_gate_a_source_feasibility_v2.json"

SECTOR_NAMES = [
    "NIFTY Auto", "NIFTY Bank", "NIFTY Financial Services", "NIFTY FMCG",
    "NIFTY IT", "NIFTY Media", "NIFTY Metal", "NIFTY Pharma", "NIFTY Realty",
    "NIFTY Energy",
]
INDEX_NAMES = SECTOR_NAMES + ["NIFTY 50"]

INDEX_SAMPLES = [
    ("nse_indices_2024_07_05", "2024-07-05", [
        "https://archives.nseindia.com/content/indices/ind_close_all_05072024.csv",
        "https://nsearchives.nseindia.com/content/indices/ind_close_all_05072024.csv",
    ]),
    ("nse_indices_2024_07_08", "2024-07-08", [
        "https://archives.nseindia.com/content/indices/ind_close_all_08072024.csv",
        "https://nsearchives.nseindia.com/content/indices/ind_close_all_08072024.csv",
    ]),
]

EQUITY_SAMPLES = [
    {
        "key": "legacy_equity_2024_07_05",
        "date": "2024-07-05",
        "format": "legacy",
        "urls": [
            "https://archives.nseindia.com/content/historical/EQUITIES/2024/JUL/cm05JUL2024bhav.csv.zip",
            "https://nsearchives.nseindia.com/content/historical/EQUITIES/2024/JUL/cm05JUL2024bhav.csv.zip",
        ],
    },
    {
        "key": "udiff_equity_2024_07_08",
        "date": "2024-07-08",
        "format": "udiff",
        "urls": [
            "https://archives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv.zip",
            "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv.zip",
        ],
    },
]

FII_JSON = "https://raw.githubusercontent.com/MrChartist/fii-dii-data/main/data/history.json"
FII_PAGES = [
    ("chartdrift_fii_dii", "https://www.chartdrift.com/fii-dii"),
    ("fundata_fii_dii", "https://www.fundata.in/FIIDII.html"),
    ("traderscockpit_fii_dii", "https://www.traderscockpit.com/?pageView=fii-dii-activity"),
]
# Gate A must use only a small deterministic source window, never multi-year history.
NSE_FII_URLS = [
    ("nse_fii_current", "https://www.nseindia.com/api/fiidiiTradeReact"),
    ("nse_fii_date_params", "https://www.nseindia.com/api/fiidiiTradeReact?fromDate=01-07-2024&toDate=10-07-2024"),
]
MAX_FII_API_ROWS = 50
MAX_FII_API_WINDOW_DAYS = 10
MAX_FII_API_BYTES = 512_000


def normalize_date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    for fmt, candidate in (
        ("%d-%m-%Y", raw[:10]),
        ("%d-%b-%Y", raw[:11].title()),
        ("%d %b %Y", raw[:11].title()),
        ("%d-%B-%Y", raw[:20].title()),
        ("%d %B %Y", raw[:20].title()),
    ):
        try:
            return dt.datetime.strptime(candidate, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def inspect_index_csv(key: str, date: str, urls: list[str]) -> dict[str, Any]:
    attempts = []
    data = None
    source_url = None
    for url in urls:
        blob, meta = fetch_bytes(url, timeout=45)
        attempts.append(meta)
        if blob is not None:
            data, source_url = blob, url
            break
    if data is None:
        return {"key": key, "requested_date": date, "attempts": attempts, "schema_status": "NOT_VERIFIED"}
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    headers = [str(x).strip() for x in (reader.fieldnames or [])]
    rows = list(reader)
    name_col = next((x for x in headers if x.casefold().strip() == "index name"), None)
    date_col = next((x for x in headers if x.casefold().strip() == "index date"), None)
    close_col = next((x for x in headers if x.casefold().strip() in {"closing index value", "close"}), None)
    distinct_dates = sorted({normalize_date(row.get(date_col)) for row in rows if date_col and normalize_date(row.get(date_col))})
    date_ok = bool(rows) and bool(date_col) and all(normalize_date(row.get(date_col)) == date for row in rows)
    found = {}
    if name_col and close_col:
        for row in rows:
            name = str(row.get(name_col, "")).strip()
            normalized = re.sub(r"\s+", " ", name).casefold()
            expected = next((n for n in INDEX_NAMES if re.sub(r"\s+", " ", n).casefold() == normalized), None)
            if expected:
                found[expected] = {
                    "source_name": name,
                    "date": normalize_date(row.get(date_col)),
                    "close": row.get(close_col),
                }
    missing_indices = [name for name in INDEX_NAMES if name not in found]
    return {
        "key": key,
        "requested_date": date,
        "source_url": source_url,
        "attempts": attempts,
        "content_bytes": len(data),
        "sha256": sha256_bytes(data),
        "headers": headers,
        "row_count": len(rows),
        "distinct_date_count": len(distinct_dates),
        "observed_dates": distinct_dates[:10],
        "date_check_all_rows": date_ok,
        "index_name_column": name_col,
        "close_column": close_col,
        "expected_indices_found": found,
        "missing_expected_indices": missing_indices,
        "schema_status": "PASS" if name_col and date_col and close_col and date_ok and not missing_indices else "FAIL",
    }


def inspect_equity_archive(spec: dict[str, Any]) -> dict[str, Any]:
    attempts = []
    data = None
    source_url = None
    for url in spec["urls"]:
        blob, meta = fetch_bytes(url, timeout=45)
        attempts.append(meta)
        if blob is not None:
            data, source_url = blob, url
            break
    if data is None:
        return {"key": spec["key"], "requested_date": spec["date"], "attempts": attempts, "schema_status": "NOT_VERIFIED"}
    base = {
        "key": spec["key"], "requested_date": spec["date"], "format": spec["format"],
        "source_url": source_url, "attempts": attempts, "zip_bytes": len(data),
        "zip_sha256": sha256_bytes(data),
    }
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                return {**base, "schema_status": "FAIL", "reason": f"expected one CSV, found {len(names)}"}
            raw = zf.read(names[0])
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="strict")))
        headers = [str(h).strip() for h in (reader.fieldnames or [])]
        rows = list(reader)
        if spec["format"] == "legacy":
            date_col, series_col, isin_col, close_col, volume_col = "TIMESTAMP", "SERIES", "ISIN", "CLOSE", "TOTTRDQTY"
            required = ["SYMBOL", "SERIES", "ISIN", "CLOSE", "TOTTRDQTY", "TIMESTAMP"]
        else:
            date_col, series_col, isin_col, close_col, volume_col = "TradDt", "SctySrs", "ISIN", "ClsPric", "TtlTradgVol"
            required = ["TradDt", "TckrSymb", "SctySrs", "ISIN", "ClsPric", "TtlTradgVol"]
        observed_dates = sorted({normalize_date(row.get(date_col)) for row in rows if normalize_date(row.get(date_col))})
        date_ok = bool(rows) and all(normalize_date(row.get(date_col)) == spec["date"] for row in rows)
        missing = sorted(set(required) - set(headers))
        eligible = []
        for row in rows:
            if str(row.get(series_col, "")).strip().upper() != "EQ":
                continue
            if not str(row.get(isin_col, "")).strip().upper().startswith("INE"):
                continue
            try:
                close = float(row.get(close_col, ""))
                volume = float(row.get(volume_col, ""))
            except (TypeError, ValueError):
                continue
            if close > 0 and volume > 0:
                eligible.append(row)
        sample = []
        for row in eligible[:5]:
            sample.append({k: row.get(k) for k in (["SYMBOL", "SERIES", "ISIN", "CLOSE", "TOTTRDQTY", "TIMESTAMP"] if spec["format"] == "legacy" else ["TckrSymb", "SctySrs", "ISIN", "ClsPric", "TtlTradgVol", "TradDt"])})
        return {
            **base,
            "csv_entry": names[0],
            "csv_sha256": sha256_bytes(raw),
            "csv_bytes": len(raw),
            "headers": headers,
            "row_count": len(rows),
            "distinct_date_count": len(observed_dates),
            "observed_dates": observed_dates[:10],
            "date_check_all_rows": date_ok,
            "missing_required_columns": missing,
            "eq_series_ine_rows_positive_close_volume": len(eligible),
            "eligible_sample": sample,
            "schema_status": "PASS" if date_ok and not missing and eligible else "FAIL",
        }
    except Exception as exc:
        return {**base, "schema_status": "FAIL", "reason": f"{type(exc).__name__}: {str(exc)[:300]}"}


def inspect_fii_history() -> dict[str, Any]:
    data, meta = fetch_bytes(FII_JSON, timeout=30)
    if data is None:
        return {"key": "fii_dii_github_history", **meta, "schema_status": "NOT_VERIFIED"}
    try:
        rows = json.loads(data.decode("utf-8"))
        if not isinstance(rows, list):
            return {"key": "fii_dii_github_history", **meta, "schema_status": "FAIL", "reason": "top-level JSON is not a list"}
        required = ["date", "fii_buy", "fii_sell", "dii_buy", "dii_sell"]
        dates = []
        missing_field_rows = []
        invalid_date_rows = []
        nonnumeric_flow_rows = []
        zero_flow_rows = 0
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                missing_field_rows.append({"row": i, "reason": "record is not an object"})
                continue
            absent = [key for key in required if key not in row or row.get(key) in (None, "")]
            if absent:
                missing_field_rows.append({"row": i, "fields": absent})
            normalized = normalize_date(row.get("date"))
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalized):
                    raise ValueError("date did not normalize to ISO YYYY-MM-DD")
                dt.date.fromisoformat(normalized)
                dates.append(normalized)
            except ValueError as exc:
                invalid_date_rows.append({"row": i, "value": str(row.get("date")), "reason": str(exc)})
            values = []
            bad_values = []
            for key in ["fii_buy", "fii_sell", "dii_buy", "dii_sell"]:
                try:
                    value = float(row.get(key))
                    if not __import__("math").isfinite(value):
                        raise ValueError("non-finite")
                    values.append(value)
                except (TypeError, ValueError):
                    bad_values.append(key)
            if bad_values:
                nonnumeric_flow_rows.append({"row": i, "fields": bad_values})
            elif values and all(value == 0 for value in values):
                zero_flow_rows += 1
        duplicate_dates = len(dates) - len(set(dates))
        return {
            "key": "fii_dii_github_history",
            **meta,
            "row_count": len(rows),
            "distinct_date_count": len(set(dates)),
            "min_date": min(dates) if dates else None,
            "max_date": max(dates) if dates else None,
            "missing_required_field_row_count": len(missing_field_rows),
            "missing_required_field_examples": missing_field_rows[:5],
            "invalid_date_row_count": len(invalid_date_rows),
            "invalid_date_examples": invalid_date_rows[:5],
            "duplicate_date_count": duplicate_dates,
            "nonnumeric_or_nonfinite_flow_row_count": len(nonnumeric_flow_rows),
            "nonnumeric_flow_examples": nonnumeric_flow_rows[:5],
            "zero_flow_rows": zero_flow_rows,
            "source_labels": sorted({str(row.get("_source", "missing")) for row in rows if isinstance(row, dict)}),
            "sample": rows[:3],
            "schema_status": "PASS" if rows and not missing_field_rows and not invalid_date_rows and duplicate_dates == 0 and not nonnumeric_flow_rows else "FAIL",
        }
    except Exception as exc:
        return {"key": "fii_dii_github_history", **meta, "schema_status": "FAIL", "reason": f"{type(exc).__name__}: {str(exc)[:300]}"}


def inspect_fii_page(key: str, url: str) -> dict[str, Any]:
    data, meta = fetch_bytes(url, timeout=30)
    if data is None:
        return {"key": key, **meta, "schema_status": "NOT_VERIFIED"}
    text = data.decode("utf-8", errors="replace")
    parser = TableSampler()
    parser.feed(text)
    title = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    return {
        "key": key,
        **meta,
        "page_title": re.sub(r"\s+", " ", title.group(1)).strip()[:200] if title else "",
        "html_table_row_count": len(parser.rows),
        "table_sample": parser.rows[:12],
        "schema_status": "PAGE_FETCHED_TABLE_REQUIRES_REVIEW" if parser.rows else "PAGE_FETCHED_NO_STATIC_TABLE",
    }



def validate_nse_fii_api_url(key: str, url: str) -> tuple[bool, str]:
    """Fail closed if an NSE Gate A request is not one of the bounded registered probes."""
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    if parsed.scheme != "https" or parsed.hostname != "www.nseindia.com" or parsed.path != "/api/fiidiiTradeReact":
        return False, "unregistered NSE FII/DII API host or path"
    if key == "nse_fii_current":
        if "fromDate" in query or "toDate" in query:
            return False, "current endpoint must not carry an uncontrolled date range"
        return True, "single current endpoint; response protected by byte and row limits"
    if key != "nse_fii_date_params":
        return False, "unregistered NSE FII/DII request key"
    if set(query) != {"fromDate", "toDate"} or len(query["fromDate"]) != 1 or len(query["toDate"]) != 1:
        return False, "date-parameter endpoint requires exactly one fromDate and one toDate"
    try:
        start = dt.datetime.strptime(query["fromDate"][0], "%d-%m-%Y").date()
        end = dt.datetime.strptime(query["toDate"][0], "%d-%m-%Y").date()
    except ValueError:
        return False, "date parameters must use DD-MM-YYYY"
    if end < start:
        return False, "toDate precedes fromDate"
    days = (end - start).days + 1
    if days > MAX_FII_API_WINDOW_DAYS:
        return False, f"date window is {days} days; Gate A limit is {MAX_FII_API_WINDOW_DAYS}"
    return True, f"bounded {days}-day source window"


def inspect_nse_fii_api_payload(
    key: str,
    data: bytes,
    meta: dict[str, Any],
    expected_date_window: tuple[dt.date, dt.date] | None = None,
) -> dict[str, Any]:
    """Parse a sample API payload without allowing a large historical response to pass."""
    try:
        obj = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        text = data[:300].decode("utf-8", errors="replace")
        return {
            "key": key, **meta, "schema_status": "NON_JSON_RESPONSE",
            "parse_error": type(exc).__name__, "body_prefix": text,
        }
    if isinstance(obj, list):
        rows = obj
    elif isinstance(obj, dict) and ("data" in obj or "rows" in obj):
        rows = obj.get("data", obj.get("rows"))
        if not isinstance(rows, list):
            return {
                "key": key, **meta, "schema_status": "UNRECOGNIZED_JSON_SHAPE",
                "top_level_keys": sorted(str(k) for k in obj.keys())[:50],
                "reason": "data/rows member is not a list",
            }
    elif isinstance(obj, dict) and any(k in obj for k in ("date", "tradeDate", "tradeDateString")):
        rows = [obj]
    else:
        return {
            "key": key, **meta, "schema_status": "UNRECOGNIZED_JSON_SHAPE",
            "top_level_keys": sorted(str(k) for k in obj.keys())[:50] if isinstance(obj, dict) else [],
            "reason": "expected a top-level row list, data/rows list, or one dated record",
        }
    row_count = len(rows)
    if row_count is not None and row_count > MAX_FII_API_ROWS:
        return {
            "key": key, **meta, "schema_status": "REJECTED_EXCESS_ROWS",
            "row_count": row_count, "max_rows": MAX_FII_API_ROWS,
            "reason": "source response exceeds Gate A sample row limit",
        }
    if expected_date_window is not None:
        window_start, window_end = expected_date_window
        invalid_dates = []
        outside_dates = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                invalid_dates.append({"row": index, "reason": "row is not an object"})
                continue
            date_key = next(
                (name for name in ("date", "tradeDate", "tradeDateString", "Date", "DATE", "TradDt")
                 if name in row and row.get(name) not in (None, "")),
                None,
            )
            if date_key is None:
                invalid_dates.append({"row": index, "reason": "no recognized date field"})
                continue
            normalized = normalize_date(row.get(date_key))
            try:
                parsed_date = dt.date.fromisoformat(normalized)
            except ValueError:
                invalid_dates.append({"row": index, "field": date_key, "value": str(row.get(date_key))})
                continue
            if parsed_date < window_start or parsed_date > window_end:
                outside_dates.append({
                    "row": index, "field": date_key,
                    "value": str(row.get(date_key)), "normalized_date": parsed_date.isoformat(),
                })
        window_fields = {
            "requested_from_date": window_start.isoformat(),
            "requested_to_date": window_end.isoformat(),
        }
        if invalid_dates:
            return {
                "key": key, **meta, "schema_status": "UNVERIFIED_RESPONSE_DATE",
                "row_count": row_count, **window_fields,
                "invalid_date_row_count": len(invalid_dates),
                "invalid_date_examples": invalid_dates[:5],
                "reason": "could not validate every response row against the requested date window",
            }
        if outside_dates:
            return {
                "key": key, **meta, "schema_status": "REJECTED_ROWS_OUTSIDE_REQUESTED_WINDOW",
                "row_count": row_count, **window_fields,
                "out_of_window_row_count": len(outside_dates),
                "out_of_window_examples": outside_dates[:5],
                "reason": "one or more response rows fall outside the requested date window",
            }
    return {
        "key": key, **meta, "schema_status": "JSON_PARSED",
        "row_count": row_count,
        "sample": rows[:4] if isinstance(rows, list) else obj,
    }



def inspect_nse_fii_api_source(key: str, url: str) -> dict[str, Any]:
    allowed, reason = validate_nse_fii_api_url(key, url)
    if not allowed:
        return {
            "key": key, "url": url, "status": "NOT_REQUESTED_SCOPE_FAIL",
            "schema_status": "FAIL", "reason": reason,
            "max_response_bytes": MAX_FII_API_BYTES, "max_response_rows": MAX_FII_API_ROWS,
        }
    data, meta = fetch_bytes(url, timeout=30, max_bytes=MAX_FII_API_BYTES)
    if data is None:
        return {
            "key": key, **meta, "schema_status": "NOT_VERIFIED", "request_scope": reason,
            "max_response_bytes": MAX_FII_API_BYTES, "max_response_rows": MAX_FII_API_ROWS,
        }
    expected_window = None
    if key == "nse_fii_date_params":
        query = parse_qs(urlsplit(url).query)
        expected_window = (
            dt.datetime.strptime(query["fromDate"][0], "%d-%m-%Y").date(),
            dt.datetime.strptime(query["toDate"][0], "%d-%m-%Y").date(),
        )
    return {
        **inspect_nse_fii_api_payload(key, data, meta, expected_date_window=expected_window),
        "request_scope": reason,
        "max_response_bytes": MAX_FII_API_BYTES,
        "max_response_rows": MAX_FII_API_ROWS,
    }


def main() -> None:
    report = {
        "schema_version": 2,
        "gate": "A_SOURCE_FEASIBILITY_ONLY",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "Bounded dated index/equity CSV samples plus small FII/DII source samples; no full history, feature table, labels or model fitting.",
        "index_samples": [inspect_index_csv(*item) for item in INDEX_SAMPLES],
        "equity_samples": [inspect_equity_archive(item) for item in EQUITY_SAMPLES],
        "fii_dii_history": [inspect_fii_history()],
        "fii_dii_endpoints": [inspect_fii_page(key, url) for key, url in FII_PAGES],
        "nse_fii_api": [],
    }
    for key, url in NSE_FII_URLS:
        report["nse_fii_api"].append(inspect_nse_fii_api_source(key, url))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "index_samples": {x["key"]: x["schema_status"] for x in report["index_samples"]},
        "equity_samples": {x["key"]: x["schema_status"] for x in report["equity_samples"]},
        "fii_history": report["fii_dii_history"][0].get("row_count"),
        "report_sha256": sha256_bytes(REPORT_PATH.read_bytes()),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
