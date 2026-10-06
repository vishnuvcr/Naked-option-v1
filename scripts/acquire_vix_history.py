from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
START=dt.date.fromisoformat("2019-02-11")
END=dt.date.fromisoformat("2026-09-30")
RAW=ROOT/"data/cache/raw/india_vix"
OUT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

HEADERS={
    "User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept":"application/json,text/csv,*/*",
    "Referer":"https://www.nseindia.com/",
}

def chunks(start,end,max_days=360):
    cur=start
    while cur<=end:
        nxt=min(cur+dt.timedelta(days=max_days),end)
        yield cur,nxt
        cur=nxt+dt.timedelta(days=1)

records=[]
for a,b in chunks(START,END):
    key=f"{a:%Y%m%d}_{b:%Y%m%d}"
    dst=RAW/f"{key}.json"
    hit=dst.exists() and dst.stat().st_size>0
    if not hit:
        url=(
            "https://www.nseindia.com/api/historicalOR/vixhistory"
            f"?from={a:%d-%m-%Y}&to={b:%d-%m-%Y}&csv=true"
        )
        # Python f-string above cannot safely format a/b in nested braces;
        # build the final URL explicitly.
        url=(
            "https://www.nseindia.com/api/historicalOR/vixhistory"
            "?from="+a.strftime("%d-%m-%Y")
            +"&to="+b.strftime("%d-%m-%Y")
            +"&csv=true"
        )
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=60) as resp:
            raw=resp.read()
        if not raw:
            raise SystemExit(f"ERROR: empty India VIX response for {a} to {b}")
        dst.write_bytes(raw)
    records.append({
        "from":a.isoformat(),
        "to":b.isoformat(),
        "path":str(dst.relative_to(ROOT)),
        "cache_hit":hit,
        "bytes":dst.stat().st_size,
        "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
    })

(OUT/"india_vix_history_acquisition.json").write_text(json.dumps({
    "window_start":START.isoformat(),
    "window_end":END.isoformat(),
    "records":records,
},indent=2),encoding="utf-8")
print(OUT/"india_vix_history_acquisition.json")
