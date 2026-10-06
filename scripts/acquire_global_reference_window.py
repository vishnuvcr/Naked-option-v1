from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
START=dt.date.fromisoformat(os.environ.get("GLOBAL_START","2019-02-11"))
END=dt.date.fromisoformat(os.environ.get("GLOBAL_END","2026-09-30"))
RAW=ROOT/"data/cache/raw/global_window"
OUT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

SERIES={
    "S25":"https://stooq.com/q/d/l/?s=%5Espx&i=d",
    "S26":"https://stooq.com/q/d/l/?s=%5Endq&i=d",
    "S27":"https://stooq.com/q/d/l/?s=%5Enk&i=d",
    "S28":"https://stooq.com/q/d/l/?s=%5Ehsi&i=d",
    "S20":"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
}
HEADERS={"User-Agent":"NIFTY-Naked-Option-Research/1.0"}

def in_window(url,sid):
    if sid=="S20":
        return url+"&cosd="+START.isoformat()+"&coed="+END.isoformat()
    return url+"&d1="+START.strftime("%Y%m%d")+"&d2="+END.strftime("%Y%m%d")

records=[]
for sid,url in SERIES.items():
    dst=RAW/f"{sid}_{START}_{END}.csv"
    hit=dst.exists() and dst.stat().st_size>0
    if not hit:
        req=urllib.request.Request(in_window(url,sid),headers=HEADERS)
        with urllib.request.urlopen(req,timeout=120) as resp:
            data=resp.read()
        if not data:
            raise SystemExit(f"ERROR: empty global reference response {sid}")
        dst.write_bytes(data)
    text=dst.read_text(encoding="utf-8-sig",errors="replace")
    lines=text.splitlines()
    if len(lines)<3:
        raise SystemExit(f"ERROR: global reference {sid} too short")
    reader=csv.DictReader(lines)
    dates=[]
    for row in reader:
        value=row.get("Date") or row.get("DATE") or row.get("observation_date")
        if value:
            dates.append(value)
    if len(dates)!=len(set(dates)):
        raise SystemExit(f"ERROR: duplicate dates in {sid}")
    records.append({
        "source_id":sid,
        "url":in_window(url,sid),
        "cache_hit":hit,
        "path":str(dst.relative_to(ROOT)),
        "bytes":dst.stat().st_size,
        "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
        "rows":len(dates),
        "min_date":min(dates),
        "max_date":max(dates),
        "availability_rule":"Daily close used only when the source market had already closed before the NIFTY decision. Otherwise default to next NIFTY session.",
    })
(OUT/"global_reference_window.json").write_text(json.dumps({
    "window_start":START.isoformat(),
    "window_end":END.isoformat(),
    "records":records,
},indent=2),encoding="utf-8")
print(OUT/"global_reference_window.json")
