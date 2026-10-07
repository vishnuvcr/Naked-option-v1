from __future__ import annotations

from pathlib import Path
import csv
import datetime
import hashlib
import json
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/global"
OUT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

# Stooq intermittently returns truncated daily CSVs in automated CI. The primary
# free reference is therefore Yahoo Finance's public chart endpoint, while the
# Stooq URLs remain catalogued as fallback research sources.
SERIES={
    "S25":("^GSPC","S&P 500","America/New_York"),
    "S26":("^IXIC","Nasdaq Composite","America/New_York"),
    "S27":("^N225","Nikkei 225","Asia/Tokyo"),
    "S28":("^HSI","Hang Seng","Asia/Hong_Kong"),
}
START=datetime.datetime(2024,7,1,tzinfo=datetime.timezone.utc)
END=datetime.datetime(2024,7,13,tzinfo=datetime.timezone.utc)
HEADERS={"User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0"}

def epoch(dt):
    return int(dt.timestamp())

records=[]
for sid,(symbol,label,tzname) in SERIES.items():
    qs=urllib.parse.urlencode({
        "period1":epoch(START),
        "period2":epoch(END),
        "interval":"1d",
        "events":"history",
        "includeAdjustedClose":"true",
    })
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol,safe='')}?{qs}"
    dst=RAW/f"{sid}_2024-07.csv"
    cache_hit=dst.exists() and dst.stat().st_size>0
    if not cache_hit:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=60) as resp:
            body=resp.read()
        payload=json.loads(body.decode("utf-8"))
        result=(payload.get("chart") or {}).get("result") or []
        if not result:
            raise SystemExit(f"ERROR: Yahoo chart returned no result for {sid} {symbol}")
        chart=result[0]
        timestamps=chart.get("timestamp") or []
        quote=((chart.get("indicators") or {}).get("quote") or [{}])[0]
        closes=quote.get("close") or []
        if len(timestamps)<3 or len(timestamps)!=len(closes):
            raise SystemExit(f"ERROR: insufficient Yahoo daily rows for {sid}: timestamps={len(timestamps)}, closes={len(closes)}")
        with dst.open("w",encoding="utf-8",newline="") as fh:
            wr=csv.writer(fh)
            wr.writerow(["date","close","source_symbol","source_timezone"])
            for ts,close in zip(timestamps,closes):
                if close is None:
                    continue
                dt=datetime.datetime.fromtimestamp(ts,datetime.timezone.utc)
                wr.writerow([dt.date().isoformat(),float(close),symbol,tzname])
    with dst.open("r",encoding="utf-8",newline="") as fh:
        rows=list(csv.DictReader(fh))
    if len(rows)<3:
        raise SystemExit(f"ERROR: {sid} global CSV has too few usable rows: {len(rows)}")
    dates=[r["date"] for r in rows]
    if len(dates)!=len(set(dates)):
        raise SystemExit(f"ERROR: {sid} contains duplicate dates")
    records.append({
        "source_id":sid,
        "label":label,
        "symbol":symbol,
        "provider":"Yahoo Finance chart endpoint",
        "url":url,
        "path":str(dst.relative_to(ROOT)),
        "cache_hit":cache_hit,
        "bytes":dst.stat().st_size,
        "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
        "rows":len(rows),
        "min_date":min(dates),
        "max_date":max(dates),
        "local_exchange_timezone":tzname,
        "availability_rule":"Daily global close is eligible for a NIFTY decision only after that local exchange has closed and the data would have been observable; default use is next Indian session 09:15 IST. No same-day future close is used.",
    })

(OUT/"global_reference_acquisition.json").write_text(json.dumps({
    "generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "provider_policy":"free public chart endpoint used as a research reference; not a canonical executable feed",
    "records":records,
},indent=2),encoding="utf-8")
print(OUT/"global_reference_acquisition.json")
