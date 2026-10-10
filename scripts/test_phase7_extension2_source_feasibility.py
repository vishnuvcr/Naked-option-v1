from __future__ import annotations

import csv
import io
import zipfile

import phase7_extension2_source_feasibility as mod


def zipped_csv(name: str, headers: list[str], rows: list[dict[str, str]]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, buf.getvalue())
    return out.getvalue()


def test_legacy_schema_sample() -> None:
    headers = ["INSTRUMENT", "SYMBOL", "EXPIRY_DT", "STRIKE_PR", "OPTION_TYP", "OPEN", "CLOSE", "CONTRACTS", "OPEN_INT", "TIMESTAMP"]
    row = {
        "INSTRUMENT": "OPTIDX", "SYMBOL": "NIFTY", "EXPIRY_DT": "25-JUL-2024",
        "STRIKE_PR": "24000", "OPTION_TYP": "CE", "OPEN": "100", "CLOSE": "105",
        "CONTRACTS": "1000", "OPEN_INT": "10000", "TIMESTAMP": "05-JUL-2024",
    }
    spec = {"key": "legacy_fixture", "date": "2024-07-05", "format": "legacy"}
    result = mod.archive_schema(zipped_csv("fo05JUL2024bhav.csv", headers, [row]), spec, "fixture")
    assert result["schema_status"] == "PASS", result
    assert result["row_count"] == 1
    assert result["nifty_index_option_rows"] == 1


def test_udiff_schema_sample() -> None:
    headers = ["TradDt", "Sgmt", "TckrSymb", "XpryDt", "StrkPric", "OptnTp", "OpnPric", "ClsPric", "TtlTradgVol", "OpnIntrst"]
    row = {
        "TradDt": "2024-07-08", "Sgmt": "FO", "TckrSymb": "NIFTY", "XpryDt": "2024-07-11",
        "StrkPric": "24000", "OptnTp": "PE", "OpnPric": "100", "ClsPric": "105",
        "TtlTradgVol": "1000", "OpnIntrst": "10000",
    }
    spec = {"key": "udiff_fixture", "date": "2024-07-08", "format": "udiff"}
    result = mod.archive_schema(zipped_csv("BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv", headers, [row]), spec, "fixture")
    assert result["schema_status"] == "PASS", result
    assert result["row_count"] == 1
    assert result["nifty_index_option_rows"] == 1


def test_missing_required_column_fails() -> None:
    headers = ["INSTRUMENT", "SYMBOL", "TIMESTAMP"]
    row = {"INSTRUMENT": "OPTIDX", "SYMBOL": "NIFTY", "TIMESTAMP": "05-JUL-2024"}
    spec = {"key": "bad_fixture", "date": "2024-07-05", "format": "legacy"}
    result = mod.archive_schema(zipped_csv("bad.csv", headers, [row]), spec, "fixture")
    assert result["schema_status"] == "FAIL"
    assert result["missing_required_columns"]


def test_wrong_trade_date_fails() -> None:
    headers = ["INSTRUMENT", "SYMBOL", "EXPIRY_DT", "STRIKE_PR", "OPTION_TYP", "OPEN", "CLOSE", "CONTRACTS", "OPEN_INT", "TIMESTAMP"]
    row = {
        "INSTRUMENT": "OPTIDX", "SYMBOL": "NIFTY", "EXPIRY_DT": "25-JUL-2024",
        "STRIKE_PR": "24000", "OPTION_TYP": "CE", "OPEN": "100", "CLOSE": "105",
        "CONTRACTS": "1000", "OPEN_INT": "10000", "TIMESTAMP": "04-JUL-2024",
    }
    spec = {"key": "wrong_date", "date": "2024-07-05", "format": "legacy"}
    result = mod.archive_schema(zipped_csv("wrong.csv", headers, [row]), spec, "fixture")
    assert result["schema_status"] == "FAIL"
    assert result["requested_date_check"] is False


def main() -> None:
    tests = [
        test_legacy_schema_sample,
        test_udiff_schema_sample,
        test_missing_required_column_fails,
        test_wrong_trade_date_fails,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} source-feasibility regression checks")


if __name__ == "__main__":
    main()
