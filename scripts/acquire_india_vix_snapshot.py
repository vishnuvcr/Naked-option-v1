from __future__ import annotations
from pathlib import Path
import datetime, json, urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

url="https://www.nseindia.com/api/allIndices"
headers={
    "User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept":"application/json,text/plain,*/*",
    "Referer":"https://www.nseindia.com/",
}
req=urllib.request.Request(url,headers=headers)
with urllib.request.urlopen(req,timeout=30) as resp:
    data=json.loads(resp.read().decode("utf-8"))

rows=data.get("data",[])
candidates=[r for r in rows if str(r.get("indexSymbol","")).upper() in {"INDIA VIX","INDIAVIX"} or "INDIA VIX" in str(r.get("index","")).upper()]
if not candidates:
    raise SystemExit("ERROR: India VIX not present in NSE allIndices payload")

row=candidates[0]
snapshot={
    "retrieved_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_url":url,
    "index_symbol":row.get("indexSymbol"),
    "value":row.get("last"),
    "change":row.get("variation"),
    "percent_change":row.get("percentChange"),
    "last_update_time":row.get("timeVal"),
    "status":"PASS",
    "availability_rule":"use only when the published observation timestamp is <= decision time; no future/revised value backfill",
}
(OUT/"india_vix_snapshot.json").write_text(json.dumps(snapshot,indent=2),encoding="utf-8")
print(json.dumps(snapshot,indent=2))
