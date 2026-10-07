from __future__ import annotations

import csv
import datetime as dt
import io
import json
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
YEAR=int(__import__("os").environ.get("YEAR","2024"))
RAW=ROOT/"data/cache/raw/nse_year"/str(YEAR)
OUT=ROOT/"data/cache/derived/official_nifty_eod"
REPORT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)
REPORT.mkdir(parents=True,exist_ok=True)

ALIASES={
    "symbol":["SYMBOL","TckrSymb"],
    "expiry":["EXPIRY_DT","XpryDt"],
    "strike":["STRIKE_PR","StrkPric"],
    "opt":["OPTION_TYP","OptnTp"],
    "open":["OPEN","OpnPric"],
    "high":["HIGH","HghPric"],
    "low":["LOW","LwPric"],
    "close":["CLOSE","ClsPric"],
    "last":["LastPric"],
    "settle":["SETTLE_PR","SttlmPric"],
    "volume":["CONTRACTS","TtlTradgVol"],
    "oi":["OPEN_INT","OpnIntrst"],
    "change_oi":["CHG_IN_OI","ChngInOpnIntrst"],
    "underlying":["UNDERLYING_VALUE","UndrlygPric"],
    "lot_size":["NewBrdLotQty","NewBrdLotQtyPerOrder","LotSize","BoardLotQty"],
}

def find(header,names):
    for n in names:
        if n in header:
            return n
    return None

def num(v):
    try:
        x=float(v)
        return x
    except Exception:
        return None

def parse_nse_date(v):
    raw=str(v or "").strip()
    if not raw:
        return None
    raw=raw.split("T")[0].split(" ")[0].strip()
    for fmt in ("%Y-%m-%d","%d-%b-%Y","%d-%B-%Y","%d-%m-%Y","%d/%m/%Y","%Y/%m/%d"):
        try:
            return dt.datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None

records=[]
for zpath in sorted(RAW.glob("*.zip")):
    if zpath.name.startswith("."):
        continue
    try:
        with zipfile.ZipFile(zpath) as z:
            names=[n for n in z.namelist() if n.lower().endswith((".csv",".txt"))]
            with z.open(names[0]) as fh:
                text=fh.read().decode("utf-8-sig",errors="replace")
        reader=csv.DictReader(io.StringIO(text))
        header=reader.fieldnames or []
        fmt="legacy" if "SYMBOL" in header else ("udiff" if "TckrSymb" in header else "unknown")
        vals={k:find(header,v) for k,v in ALIASES.items()}
        trade_date=dt.date.fromisoformat(zpath.stem)
        for row in reader:
            if str(row.get(vals["symbol"],"")).strip().upper()!="NIFTY":
                continue
            opt=str(row.get(vals["opt"],"")).strip().upper()
            if opt not in {"CE","PE"}:
                continue
            expiry=parse_nse_date(row.get(vals["expiry"]))
            if expiry is None:
                continue
            strike=num(row.get(vals["strike"]))
            if strike is None:
                continue
            records.append({
                "trade_date":trade_date.isoformat(),
                "expiry":expiry.isoformat(),
                "strike":strike,
                "option_type":opt,
                "open":num(row.get(vals["open"])) if vals["open"] else None,
                "high":num(row.get(vals["high"])) if vals["high"] else None,
                "low":num(row.get(vals["low"])) if vals["low"] else None,
                "close":num(row.get(vals["close"])) if vals["close"] else None,
                "last_price":num(row.get(vals["last"])) if vals["last"] else None,
                "settlement":num(row.get(vals["settle"])) if vals["settle"] else None,
                "volume":num(row.get(vals["volume"])) if vals["volume"] else None,
                "oi":num(row.get(vals["oi"])) if vals["oi"] else None,
                "change_oi":num(row.get(vals["change_oi"])) if vals["change_oi"] else None,
                "underlying":num(row.get(vals["underlying"])) if vals["underlying"] else None,
                "lot_size":num(row.get(vals["lot_size"])) if vals["lot_size"] else None,
                "source_format":fmt,
                "source_file":zpath.name,
            })
    except Exception as exc:
        raise SystemExit(f"ERROR: unable to parse {zpath}: {type(exc).__name__}: {exc}")

if not records:
    raise SystemExit(f"ERROR: no NIFTY option records extracted for {YEAR}")

table=pa.Table.from_pylist(records)
out=OUT/f"nifty_option_eod_{YEAR}.parquet"
pq.write_table(table,out,compression="zstd")
report={
    "year":YEAR,
    "rows":table.num_rows,
    "path":str(out.relative_to(ROOT)),
    "columns":table.column_names,
    "source_formats":sorted(set(records[i]["source_format"] for i in range(len(records)))),
}
(REPORT/f"nifty_option_eod_{YEAR}_parquet.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
