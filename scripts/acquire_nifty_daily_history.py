from __future__ import annotations
from pathlib import Path
import csv, datetime, hashlib, json, time, urllib.parse, urllib.request

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/phase3"
REPORT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
REPORT.mkdir(parents=True,exist_ok=True)

START=datetime.date(2020,1,1)
END=datetime.date(2026,9,30)
CHUNK_DAYS=60
BASE="https://www.nseindia.com/api/historical/indicesHistory"
HEADERS={
    "User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept":"application/json,text/plain,*/*",
    "Referer":"https://www.nseindia.com/reports-indices-historical-index-data",
}

def fetch(a,b):
    params=urllib.parse.urlencode({
        "indexType":"NIFTY 50",
        "from":a.strftime("%d-%m-%Y"),
        "to":b.strftime("%d-%m-%Y"),
    })
    url=f"{BASE}?{params}"
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=60) as resp:
        data=json.loads(resp.read().decode("utf-8"))
    rows=data.get("data")
    if not isinstance(rows,list):
        raise RuntimeError(f"unexpected NSE payload for {a}..{b}")
    return url,rows

all_rows=[]
chunks=[]
cur=START
while cur<=END:
    nxt=min(cur+datetime.timedelta(days=CHUNK_DAYS-1),END)
    for attempt in range(3):
        try:
            url,rows=fetch(cur,nxt)
            break
        except Exception:
            if attempt==2: raise
            time.sleep(2+attempt*2)
    all_rows.extend(rows)
    chunks.append({"from":cur.isoformat(),"to":nxt.isoformat(),"rows":len(rows),"url":url})
    cur=nxt+datetime.timedelta(days=1)
    time.sleep(0.25)

def val(r,*keys):
    for k in keys:
        if r.get(k) not in (None,"","-"):
            return r[k]
    return None

out_rows=[]
for r in all_rows:
    ts=val(r,"CH_TIMESTAMP","TIMESTAMP","timestamp")
    close=val(r,"CH_CLOSING_PRICE","CLOSE","close")
    if not ts or close is None:
        continue
    out_rows.append({
        "date":str(ts).strip(),
        "open":val(r,"CH_OPENING_PRICE","OPEN"),
        "high":val(r,"CH_TRADE_HIGH_PRICE","HIGH"),
        "low":val(r,"CH_TRADE_LOW_PRICE","LOW"),
        "close":close,
        "last":val(r,"CH_LAST_TRADED_PRICE","LAST"),
        "prev_close":val(r,"CH_PREVIOUS_CLS","PREV_CLOSE"),
        "volume":val(r,"CH_TOT_TRADED_QTY","VOLUME"),
        "turnover":val(r,"CH_TOT_TRADED_VAL","TURNOVER"),
        "source":"NSE official historical index API",
    })

dedup={r["date"]:r for r in out_rows}
out_rows=sorted(dedup.values(),key=lambda x:x["date"])
if len(out_rows)<1000:
    raise SystemExit(f"ERROR: too few NIFTY daily observations: {len(out_rows)}")
if len(out_rows)!=len({r["date"] for r in out_rows}):
    raise SystemExit("ERROR: duplicate NIFTY dates remain")

path=RAW/"nifty50_daily.csv"
with path.open("w",encoding="utf-8",newline="") as fh:
    wr=csv.DictWriter(fh,fieldnames=list(out_rows[0]))
    wr.writeheader()
    wr.writerows(out_rows)

manifest={
    "source":"NSE official historical index API",
    "index":"NIFTY 50",
    "start":out_rows[0]["date"],
    "end":out_rows[-1]["date"],
    "rows":len(out_rows),
    "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
    "bytes":path.stat().st_size,
    "chunk_count":len(chunks),
    "chunks":chunks,
    "pit_rule":"Only historical observations at or before the decision date may enter features; future rows never enter rolling transformations.",
}
(REPORT/"nifty50_daily_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({"rows":len(out_rows),"start":out_rows[0]["date"],"end":out_rows[-1]["date"],"sha256":manifest["sha256"]},indent=2))
