from __future__ import annotations
from pathlib import Path
import csv
import datetime as dt
import hashlib
import io
import json
import urllib.parse
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/phase3"
REPORT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
REPORT.mkdir(parents=True,exist_ok=True)

START=dt.datetime(2020,1,1,tzinfo=dt.timezone.utc)
END=dt.datetime(2026,10,1,tzinfo=dt.timezone.utc)
SYMBOL="^NSEI"
HEADERS={"User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0","Accept":"application/json,text/plain,*/*"}

def yahoo_daily():
    qs=urllib.parse.urlencode({
        "period1":int(START.timestamp()),
        "period2":int(END.timestamp()),
        "interval":"1d",
        "events":"history",
        "includeAdjustedClose":"true",
    })
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(SYMBOL,safe='')}?{qs}"
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=60) as resp:
        payload=json.loads(resp.read().decode("utf-8"))
    result=((payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError("Yahoo chart returned no result")
    ts=result.get("timestamp") or []
    q=((result.get("indicators") or {}).get("quote") or [{}])[0]
    rows=[]
    for i,t in enumerate(ts):
        vals={k:(q.get(k,[None]*len(ts))[i] if i<len(q.get(k,[None]*len(ts))) else None)
              for k in ["open","high","low","close","volume"]}
        if vals["close"] is None:
            continue
        date=dt.datetime.fromtimestamp(t,dt.timezone.utc).date().isoformat()
        rows.append({
            "date":date,
            "open":vals["open"],
            "high":vals["high"],
            "low":vals["low"],
            "close":vals["close"],
            "volume":vals["volume"],
            "source":"Yahoo Finance public chart; validated against official NSE archive",
            "available_at":date+"T18:30:00+05:30",
        })
    rows=sorted({r["date"]:r for r in rows}.values(),key=lambda r:r["date"])
    if len(rows)<1000:
        raise RuntimeError(f"too few Yahoo NIFTY rows: {len(rows)}")
    return url,rows

def official_nse_spot_check(day:dt.date):
    filename=f"ind_close_all_{day.strftime('%d%m%Y')}.csv"
    urls=[
        f"https://nsearchives.nseindia.com/content/indices/{filename}",
        f"https://archives.nseindia.com/content/indices/{filename}",
    ]
    last=None
    for url in urls:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0","Accept":"text/csv,*/*"})
            with urllib.request.urlopen(req,timeout=30) as resp:
                data=resp.read()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                raise RuntimeError("unexpected zip response")
        except Exception as exc:
            # NSE index archives are plain CSV, not ZIP. Retry by reading as text.
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0","Accept":"text/csv,*/*"})
                with urllib.request.urlopen(req,timeout=30) as resp:
                    text=resp.read().decode("utf-8-sig",errors="replace")
                rows=list(csv.DictReader(io.StringIO(text)))
                for r in rows:
                    if str(r.get("Index Name","")).strip()=="Nifty 50":
                        for key in ["Closing Index Value","CLOSING_INDEX_VALUE"]:
                            if r.get(key) not in (None,"","-"):
                                return {"date":day.isoformat(),"url":url,"close":float(r[key])}
                last="Nifty 50 row absent"
            except Exception as exc2:
                last=f"{type(exc2).__name__}: {exc2}"
    return {"date":day.isoformat(),"status":"unavailable","error":last}

def compare_spots(yahoo_rows):
    bydate={r["date"]:r for r in yahoo_rows}
    checks=[]
    for d in [dt.date(2024,7,5),dt.date(2024,7,8)]:
        official=official_nse_spot_check(d)
        y=bydate.get(d.isoformat())
        if official.get("close") is None or y is None:
            raise RuntimeError(f"official/Yahoo overlap missing for {d}: {official}")
        diff=abs(float(y["close"])-float(official["close"]))
        checks.append({**official,"yahoo_close":float(y["close"]),"abs_diff":diff,"within_1_point":diff<=1.0})
        if diff>1.0:
            raise RuntimeError(f"Yahoo-vs-NSE close mismatch on {d}: {diff}")
    return checks

url,rows=yahoo_daily()
checks=compare_spots(rows)

path=RAW/"nifty50_daily.csv"
with path.open("w",encoding="utf-8",newline="") as fh:
    wr=csv.DictWriter(fh,fieldnames=list(rows[0]))
    wr.writeheader(); wr.writerows(rows)

manifest={
    "source":"Yahoo Finance public chart with official NSE overlap validation",
    "index":"Nifty 50",
    "requested_start":START.date().isoformat(),
    "requested_end":(END-dt.timedelta(days=1)).date().isoformat(),
    "observed_start":rows[0]["date"],
    "observed_end":rows[-1]["date"],
    "rows":len(rows),
    "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
    "bytes":path.stat().st_size,
    "source_url":url,
    "official_nse_overlap_checks":checks,
    "canonical_policy":"Use official NSE data where directly available; use Yahoo only as a free bulk backfill reference after explicit NSE overlap validation. Derived rows retain provider provenance and are not treated as exchange-exact.",
    "pit_rule":"Daily global/index observations may enter features only at or after their information-availability time. No future rows enter rolling transformations.",
}
(REPORT/"nifty50_daily_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({
    "rows":len(rows),
    "observed_start":rows[0]["date"],
    "observed_end":rows[-1]["date"],
    "sha256":manifest["sha256"],
    "nse_overlap_checks":checks,
},indent=2))
