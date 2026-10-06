from __future__ import annotations

import csv
import datetime as dt
import io
import json
import math
import os
import zipfile
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
YEAR=int(os.environ.get("YEAR","2024"))
RAW=ROOT/"data/cache/raw/nse_year"/str(YEAR)
REPORT=ROOT/"data/reports"
REPORT.mkdir(parents=True,exist_ok=True)

acq=REPORT/f"nse_year_{YEAR}_acquisition.json"
if not acq.exists():
    raise SystemExit("ERROR: acquisition report missing")
meta=json.loads(acq.read_text(encoding="utf-8"))

def ffloat(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

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
    "trade_date":["TIMESTAMP","TradDt"],
}

def find(header, names):
    for n in names:
        if n in header:
            return n
    return None

records=[]
key_counts=Counter()
missing_core=0
invalid_rows=0
source_days=set()
lot_by_date={}
schema_by_format={}

for item in meta["results"]:
    if item["status"] not in {"downloaded","cache_hit"}:
        continue
    path=ROOT/item["path"]
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.lower().endswith((".csv",".txt"))]
        if not names:
            raise SystemExit(f"ERROR: no tabular file in {path}")
        with z.open(names[0]) as fh:
            text=fh.read().decode("utf-8-sig",errors="replace")
    reader=csv.DictReader(io.StringIO(text))
    header=reader.fieldnames or []
    fmt="legacy" if "SYMBOL" in header else ("udiff" if "TckrSymb" in header else "unknown")
    schema_by_format.setdefault(fmt,sorted(header))

    vals={k:find(header,v) for k,v in ALIASES.items()}
    if vals["symbol"] is None or vals["expiry"] is None or vals["strike"] is None or vals["opt"] is None:
        raise SystemExit(f"ERROR: required NIFTY option columns missing for {path}: {vals}")

    for row in reader:
        sym=str(row.get(vals["symbol"],"")).strip().upper()
        if sym!="NIFTY":
            continue
        opt=str(row.get(vals["opt"],"")).strip().upper()
        if opt not in {"CE","PE"}:
            invalid_rows+=1
            continue
        expiry_raw=str(row.get(vals["expiry"],"")).strip()
        try:
            expiry=dt.date.fromisoformat(expiry_raw.split("T")[0])
        except Exception:
            invalid_rows+=1
            continue
        strike=ffloat(row.get(vals["strike"]))
        close=ffloat(row.get(vals["close"])) if vals["close"] else None
        if strike is None or close is None:
            missing_core+=1
            continue
        trade_value=row.get(vals["trade_date"]) if vals["trade_date"] else None
        if trade_value:
            try:
                tdate=dt.date.fromisoformat(str(trade_value).split("T")[0])
            except Exception:
                tdate=None
        else:
            tdate=dt.date.fromisoformat(item["date"])
        if tdate:
            source_days.add(tdate.isoformat())
        key=(str(tdate),expiry.isoformat(),strike,opt)
        key_counts[key]+=1

        if vals["lot_size"]:
            lot=ffloat(row.get(vals["lot_size"]))
            if lot and lot>0:
                lot_by_date.setdefault(str(tdate),set()).add(int(lot))

if any(v>1 for v in key_counts.values()):
    duplicates=sum(v-1 for v in key_counts.values() if v>1)
else:
    duplicates=0

if invalid_rows>0:
    raise SystemExit(f"ERROR: invalid NIFTY option rows detected: {invalid_rows}")
if duplicates>0:
    raise SystemExit(f"ERROR: duplicate NIFTY option keys detected: {duplicates}")

# Build a compact year manifest without writing it to Git.
out={
    "year":YEAR,
    "nifty_option_rows":sum(key_counts.values()),
    "unique_contract_keys":len(key_counts),
    "trading_dates_seen":len(source_days),
    "missing_core_price_rows":missing_core,
    "duplicate_keys":duplicates,
    "schemas":schema_by_format,
    "lot_size_regimes_seen":{d:sorted(v) for d,v in sorted(lot_by_date.items())[:50]},
    "status":"PASS",
}
(REPORT/f"nse_year_{YEAR}_validation.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
