from __future__ import annotations
from pathlib import Path
import csv, datetime, hashlib, json, time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/global"
OUT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

SERIES={
    "S25":"https://stooq.com/q/d/l/?s=%5Espx&i=d&d1=20240701&d2=20240712",
    "S26":"https://stooq.com/q/d/l/?s=%5Endq&i=d&d1=20240701&d2=20240712",
    "S27":"https://stooq.com/q/d/l/?s=%5Enk&i=d&d1=20240701&d2=20240712",
    "S28":"https://stooq.com/q/d/l/?s=%5Ehsi&i=d&d1=20240701&d2=20240712",
}
HEADERS={"User-Agent":"NIFTY-Naked-Option-Research/1.0"}
records=[]
for sid,url in SERIES.items():
    dst=RAW/f"{sid}_2024-07.csv"
    cache_hit=dst.exists() and dst.stat().st_size>0
    if not cache_hit:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=60) as resp:
            data=resp.read()
        dst.write_bytes(data)
    txt=dst.read_text(encoding="utf-8-sig",errors="replace")
    rows=list(csv.DictReader(txt.splitlines()))
    if len(rows)<3:
        raise SystemExit(f"ERROR: {sid} global CSV has too few rows: {len(rows)}")
    dates=[r.get("Date") for r in rows]
    if len(dates)!=len(set(dates)):
        raise SystemExit(f"ERROR: {sid} contains duplicate dates")
    records.append({
        "source_id":sid,
        "url":url,
        "path":str(dst.relative_to(ROOT)),
        "cache_hit":cache_hit,
        "bytes":dst.stat().st_size,
        "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
        "rows":len(rows),
        "min_date":min(d for d in dates if d),
        "max_date":max(d for d in dates if d),
        "availability_rule":"usable at NIFTY decision time only from a global close already completed before that decision; daily data defaulted to next Indian session 09:15 IST",
    })
(OUT/"global_reference_acquisition.json").write_text(json.dumps({
    "generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "records":records,
},indent=2),encoding="utf-8")
print(OUT/"global_reference_acquisition.json")
