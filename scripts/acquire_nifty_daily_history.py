from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/phase3/nse_index_archives"
REPORT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
REPORT.mkdir(parents=True,exist_ok=True)

START=dt.date(2020,1,1)
END=dt.date(2026,9,30)
MAX_WORKERS=6
HEADERS={
    "User-Agent":"Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept":"text/csv,text/plain,*/*",
    "Referer":"https://www.nseindia.com/reports-indices-historical-index-data",
}

def dates(start,end):
    cur=start
    while cur<=end:
        yield cur
        cur+=dt.timedelta(days=1)

def fetch_day(day: dt.date):
    filename=f"ind_close_all_{day.strftime('%d%m%Y')}.csv"
    dst=RAW/filename
    urls=[
        f"https://nsearchives.nseindia.com/content/indices/{filename}",
        f"https://archives.nseindia.com/content/indices/{filename}",
    ]
    if dst.exists() and dst.stat().st_size>100:
        return {"date":day.isoformat(),"status":"cache_hit","path":str(dst.relative_to(ROOT))}

    last_error=None
    for url in urls:
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers=HEADERS)
                with urllib.request.urlopen(req,timeout=30) as resp:
                    body=resp.read()
                if not body or len(body)<100:
                    raise RuntimeError("empty_or_too_small")
                text=body.decode("utf-8-sig",errors="replace")
                if "Index Name" not in text and "INDEX_NAME" not in text:
                    raise RuntimeError("unexpected_index_file_payload")
                dst.write_bytes(body)
                time.sleep(0.15)
                return {"date":day.isoformat(),"status":"downloaded","path":str(dst.relative_to(ROOT)),
                        "bytes":len(body),"url":url}
            except urllib.error.HTTPError as exc:
                last_error=f"HTTP {exc.code}"
                if exc.code==404:
                    break
                time.sleep(0.8*(attempt+1))
            except Exception as exc:
                last_error=f"{type(exc).__name__}: {exc}"
                time.sleep(0.8*(attempt+1))
    return {"date":day.isoformat(),"status":"missing","error":last_error}

all_days=list(dates(START,END))
results=[]
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    futures=[pool.submit(fetch_day,d) for d in all_days]
    for fut in as_completed(futures):
        results.append(fut.result())

results.sort(key=lambda r:r["date"])
downloaded=sum(r["status"] in {"downloaded","cache_hit"} for r in results)
missing=[r for r in results if r["status"]=="missing"]

rows=[]
file_rows=[]
for r in results:
    if r["status"] not in {"downloaded","cache_hit"}:
        continue
    path=ROOT/r["path"]
    try:
        with path.open("r",encoding="utf-8-sig",errors="replace",newline="") as fh:
            parsed=list(csv.DictReader(fh))
    except Exception as exc:
        raise SystemExit(f"ERROR: failed parsing {path}: {exc}")
    found=False
    for rec in parsed:
        name=str(rec.get("Index Name",rec.get("INDEX_NAME",""))).strip()
        if name != "Nifty 50":
            continue
        found=True
        def pick(*keys):
            for k in keys:
                v=rec.get(k)
                if v not in (None,"","-"):
                    return v
            return None
        rows.append({
            "date":r["date"],
            "open":pick("Open Index Value","OPEN_INDEX_VALUE"),
            "high":pick("High Index Value","HIGH_INDEX_VALUE"),
            "low":pick("Low Index Value","LOW_INDEX_VALUE"),
            "close":pick("Closing Index Value","CLOSING_INDEX_VALUE"),
            "points_change":pick("Points Change","POINTS_CHANGE"),
            "percent_change":pick("Change(%)","CHANGE"),
            "volume":pick("Volume","VOLUME"),
            "turnover":pick("Turnover (Rs. Cr.)","TURNOVER"),
            "source":"NSE official daily index archive",
            "available_at":f"{r['date']}T18:30:00+05:30",
        })
        break
    file_rows.append({**r,"contains_nifty50":found,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})

rows.sort(key=lambda x:x["date"])
if len(rows)<1000:
    raise SystemExit(f"ERROR: too few NIFTY 50 daily observations: {len(rows)}")
if len(rows)!=len({r["date"] for r in rows}):
    raise SystemExit("ERROR: duplicate NIFTY dates remain")
if not rows or rows[0]["date"]>"2020-02-01":
    raise SystemExit(f"ERROR: early history missing; first NIFTY date is {rows[0]['date']}")

out=RAW/"nifty50_daily.csv"
with out.open("w",encoding="utf-8",newline="") as fh:
    wr=csv.DictWriter(fh,fieldnames=list(rows[0]))
    wr.writeheader(); wr.writerows(rows)

manifest={
    "source":"NSE official daily index archive",
    "index":"Nifty 50",
    "requested_start":START.isoformat(),
    "requested_end":END.isoformat(),
    "observed_start":rows[0]["date"],
    "observed_end":rows[-1]["date"],
    "rows":len(rows),
    "downloaded_or_cached_files":downloaded,
    "missing_calendar_days":len(missing),
    "sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
    "bytes":out.stat().st_size,
    "file_results":file_rows,
    "missing_days":missing[:2000],
    "pit_rule":"Daily index files are official exchange snapshots. They may be used only at or after their publication/availability date; no future daily file enters a prior decision.",
}
(REPORT/"nifty50_daily_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({
    "rows":len(rows),
    "observed_start":rows[0]["date"],
    "observed_end":rows[-1]["date"],
    "downloaded_or_cached_files":downloaded,
    "missing_calendar_days":len(missing),
    "sha256":manifest["sha256"],
},indent=2))
