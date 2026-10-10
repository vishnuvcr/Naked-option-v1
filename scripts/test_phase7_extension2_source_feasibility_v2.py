from __future__ import annotations

import csv
import io
import json
import zipfile
from unittest.mock import patch

import phase7_extension2_source_feasibility_v2 as mod


def make_zip(name: str, headers: list[str], rows: list[dict[str, str]]) -> bytes:
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, text.getvalue())
    return out.getvalue()




def test_nse_fii_api_source_uses_byte_cap() -> None:
    url = dict(mod.NSE_FII_URLS)["nse_fii_date_params"]
    blob = json.dumps([{"tradeDate": "08-Jul-2024", "fii": 10}]).encode()
    meta = {"url": url, "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)) as mocked:
        result = mod.inspect_nse_fii_api_source("nse_fii_date_params", url)
    mocked.assert_called_once_with(url, timeout=30, max_bytes=mod.MAX_FII_API_BYTES)
    assert result["max_response_bytes"] == mod.MAX_FII_API_BYTES
    assert result["schema_status"] == "JSON_PARSED"


def test_nse_fii_api_source_does_not_fetch_unbounded_url() -> None:
    url = "https://www.nseindia.com/api/fiidiiTradeReact?fromDate=01-01-2020&toDate=31-12-2025"
    with patch.object(mod, "fetch_bytes") as mocked:
        result = mod.inspect_nse_fii_api_source("nse_fii_date_params", url)
    mocked.assert_not_called()
    assert result["schema_status"] == "FAIL"
    assert result["status"] == "NOT_REQUESTED_SCOPE_FAIL"


def test_nse_fii_api_requests_are_bounded() -> None:
    configured = dict(mod.NSE_FII_URLS)
    assert len(configured) == 2
    for key, url in mod.NSE_FII_URLS:
        allowed, reason = mod.validate_nse_fii_api_url(key, url)
        assert allowed, (key, url, reason)
    oversized = "https://www.nseindia.com/api/fiidiiTradeReact?fromDate=01-01-2020&toDate=31-12-2025"
    allowed, reason = mod.validate_nse_fii_api_url("nse_fii_date_params", oversized)
    assert not allowed, reason
    assert mod.MAX_FII_API_WINDOW_DAYS == 10
    assert mod.MAX_FII_API_BYTES <= 512_000
    assert mod.MAX_FII_API_ROWS <= 50


def test_nse_fii_api_payload_rejects_excess_rows() -> None:
    rows = [{"date": f"2024-07-{(i % 9) + 1:02d}", "fii": i} for i in range(mod.MAX_FII_API_ROWS + 1)]
    blob = json.dumps(rows).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    result = mod.inspect_nse_fii_api_payload("fixture", blob, meta)
    assert result["schema_status"] == "REJECTED_EXCESS_ROWS"
    assert result["row_count"] == mod.MAX_FII_API_ROWS + 1
    assert "sample" not in result



def test_nse_fii_api_payload_rejects_unrecognized_json_shape() -> None:
    blob = json.dumps({"error": "request rejected", "message": "sample"}).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    result = mod.inspect_nse_fii_api_payload("fixture", blob, meta)
    assert result["schema_status"] == "UNRECOGNIZED_JSON_SHAPE", result
    assert "sample" not in result


def test_nse_fii_api_payload_accepts_small_sample() -> None:
    rows = [{"tradeDate": "08-Jul-2024", "fiiBuy": 10, "fiiSell": 9}]
    blob = json.dumps(rows).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    result = mod.inspect_nse_fii_api_payload("fixture", blob, meta)
    assert result["schema_status"] == "JSON_PARSED"
    assert result["row_count"] == 1


def test_index_csv_requires_all_frozen_indices_and_date() -> None:
    headers = ["Index Name", "Index Date", "Closing Index Value"]
    rows = [{"Index Name": name, "Index Date": "05-Jul-2024", "Closing Index Value": str(1000+i)}
            for i, name in enumerate(mod.INDEX_NAMES)]
    blob = (",".join(headers) + "\n" + "\n".join(",".join(row[h] for h in headers) for row in rows)).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_index_csv("index_fixture", "2024-07-05", ["fixture"])
    assert result["schema_status"] == "PASS", result
    assert result["distinct_date_count"] == 1
    assert not result["missing_expected_indices"]


def test_index_csv_missing_sector_fails() -> None:
    headers = ["Index Name", "Index Date", "Closing Index Value"]
    rows = [{"Index Name": name, "Index Date": "05-Jul-2024", "Closing Index Value": "1000"}
            for name in mod.INDEX_NAMES[:-1]]
    blob = (",".join(headers) + "\n" + "\n".join(",".join(row[h] for h in headers) for row in rows)).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_index_csv("index_fixture", "2024-07-05", ["fixture"])
    assert result["schema_status"] == "FAIL"
    assert result["missing_expected_indices"]


def test_legacy_equity_archive_checks_all_dates_and_counts_eligible_rows() -> None:
    headers = ["SYMBOL", "SERIES", "ISIN", "CLOSE", "TOTTRDQTY", "TIMESTAMP"]
    rows = [
        {"SYMBOL": "ABC", "SERIES": "EQ", "ISIN": "INE000A01001", "CLOSE": "100", "TOTTRDQTY": "1000", "TIMESTAMP": "05-JUL-2024"},
        {"SYMBOL": "DEF", "SERIES": "EQ", "ISIN": "INE000B01001", "CLOSE": "101", "TOTTRDQTY": "1200", "TIMESTAMP": "05-JUL-2024"},
    ]
    blob = make_zip("cm05JUL2024bhav.csv", headers, rows)
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    spec = {"key": "eq_fixture", "date": "2024-07-05", "format": "legacy", "urls": ["fixture"]}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_equity_archive(spec)
    assert result["schema_status"] == "PASS", result
    assert result["eq_series_ine_rows_positive_close_volume"] == 2
    assert result["distinct_date_count"] == 1


def test_udiff_equity_mixed_date_archive_fails() -> None:
    headers = ["TradDt", "TckrSymb", "SctySrs", "ISIN", "ClsPric", "TtlTradgVol"]
    rows = [
        {"TradDt": "2024-07-08", "TckrSymb": "ABC", "SctySrs": "EQ", "ISIN": "INE000A01001", "ClsPric": "100", "TtlTradgVol": "1000"},
        {"TradDt": "2024-07-09", "TckrSymb": "DEF", "SctySrs": "EQ", "ISIN": "INE000B01001", "ClsPric": "101", "TtlTradgVol": "1200"},
    ]
    blob = make_zip("BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv", headers, rows)
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    spec = {"key": "eq_fixture", "date": "2024-07-08", "format": "udiff", "urls": ["fixture"]}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_equity_archive(spec)
    assert result["schema_status"] == "FAIL"
    assert result["date_check_all_rows"] is False
    assert result["distinct_date_count"] == 2


def test_fii_history_reports_distinct_dates_and_fields() -> None:
    rows = [
        {"date": "02-Jul-2026", "fii_buy": 100, "fii_sell": 90, "dii_buy": 50, "dii_sell": 40, "_source": "fixture"},
        {"date": "01-Jul-2026", "fii_buy": 110, "fii_sell": 100, "dii_buy": 60, "dii_sell": 55, "_source": "fixture"},
    ]
    blob = json.dumps(rows).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_fii_history()
    assert result["schema_status"] == "PASS"
    assert result["row_count"] == 2
    assert result["distinct_date_count"] == 2


def test_later_fii_row_missing_field_fails() -> None:
    rows = [
        {"date": "02-Jul-2026", "fii_buy": 100, "fii_sell": 90, "dii_buy": 50, "dii_sell": 40},
        {"date": "01-Jul-2026", "fii_buy": 110, "fii_sell": 100, "dii_buy": 60},
    ]
    blob = json.dumps(rows).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_fii_history()
    assert result["schema_status"] == "FAIL"
    assert result["missing_required_field_row_count"] == 1


def test_duplicate_fii_dates_fail() -> None:
    row = {"date": "02-Jul-2026", "fii_buy": 100, "fii_sell": 90, "dii_buy": 50, "dii_sell": 40}
    blob = json.dumps([row, dict(row)]).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_fii_history()
    assert result["schema_status"] == "FAIL"
    assert result["duplicate_date_count"] == 1


def test_nonnumeric_fii_flow_fails_without_crashing() -> None:
    rows = [
        {"date": "02-Jul-2026", "fii_buy": 100, "fii_sell": 90, "dii_buy": 50, "dii_sell": 40},
        {"date": "01-Jul-2026", "fii_buy": "bad", "fii_sell": 100, "dii_buy": 60, "dii_sell": 55},
    ]
    blob = json.dumps(rows).encode()
    meta = {"url": "fixture", "status": "FETCHED", "bytes": len(blob), "sha256": mod.sha256_bytes(blob)}
    with patch.object(mod, "fetch_bytes", return_value=(blob, meta)):
        result = mod.inspect_fii_history()
    assert result["schema_status"] == "FAIL"
    assert result["nonnumeric_or_nonfinite_flow_row_count"] == 1


def test_date_normalizer_handles_timestamp_suffix() -> None:
    assert mod.normalize_date("05-Jul-2024 00:00:00") == "2024-07-05"
    assert mod.normalize_date("2024-07-08T00:00:00") == "2024-07-08"


def main() -> None:
    tests = [
        test_nse_fii_api_source_uses_byte_cap,
        test_nse_fii_api_source_does_not_fetch_unbounded_url,
        test_nse_fii_api_requests_are_bounded,
        test_nse_fii_api_payload_rejects_excess_rows,
        test_nse_fii_api_payload_rejects_unrecognized_json_shape,
        test_nse_fii_api_payload_accepts_small_sample,
        test_index_csv_requires_all_frozen_indices_and_date,
        test_index_csv_missing_sector_fails,
        test_legacy_equity_archive_checks_all_dates_and_counts_eligible_rows,
        test_udiff_equity_mixed_date_archive_fails,
        test_fii_history_reports_distinct_dates_and_fields,
        test_later_fii_row_missing_field_fails,
        test_duplicate_fii_dates_fail,
        test_nonnumeric_fii_flow_fails_without_crashing,
        test_date_normalizer_handles_timestamp_suffix,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} revised source-feasibility regression checks")


if __name__ == "__main__":
    main()
