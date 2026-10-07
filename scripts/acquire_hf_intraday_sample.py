from __future__ import annotations
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import urllib.request
import urllib.parse
import io

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/phase3/hf_intraday"
OUT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

DATASET=os.environ.get("HF_INTRADAY_DATASET","thetrademarkk/india-index-options-1m")
FILE_PATH=os.environ.get("HF_INTRADAY_FILE","index/NIFTY.parquet")
TOKEN=os.environ.get("HF_TOKEN")
HEADERS={"User-Agent":"NIFTY-Naked-Option-Research/1.0"}
if TOKEN:
    HEADERS["Authorization"]=f"Bearer {TOKEN}"

meta_url=f"https://huggingface.co/api/datasets/{DATASET}"
req=urllib.request.Request(meta_url,headers=HEADERS)
with urllib.request.urlopen(req,timeout=60) as resp:
    meta=json.loads(resp.read().decode("utf-8"))
revision=meta.get("sha")
siblings={x.get("rfilename","") for x in meta.get("siblings",[])}
if FILE_PATH not in siblings:
    raise SystemExit(f"ERROR: requested HF file not visible: {FILE_PATH}")

local=RAW/"nifty50_index_reference.parquet"
cache_hit=local.exists() and local.stat().st_size>0
if not cache_hit:
    url=f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{urllib.parse.quote(FILE_PATH,safe='/')}"
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=180) as resp:
        local.write_bytes(resp.read())

df=pd.read_parquet(local)
required={"timestamp","close"}
missing=required-set(df.columns)
if missing:
    raise SystemExit(f"ERROR: HF NIFTY index reference missing columns: {sorted(missing)}")

x=pd.DataFrame({
    "timestamp":pd.to_datetime(df["timestamp"],errors="coerce",utc=True),
    "spot":pd.to_numeric(df["close"],errors="coerce"),
}).dropna().sort_values("timestamp").drop_duplicates("timestamp")
if len(x)==0:
    raise SystemExit("ERROR: HF NIFTY index reference has no usable rows")

# Keep the full 1-minute NIFTY spot track. It is small enough to cache locally
# and avoids the false inference that an option-chain field named 'underlying'
# is itself a numeric spot price.
x.to_parquet(local,index=False)

def official_nse_close(day: dt.date):
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
                text=resp.read().decode("utf-8-sig",errors="replace")
            rows=pd.read_csv(io.StringIO(text)).to_dict("records")
            for row in rows:
                if str(row.get("Index Name","")).strip()=="Nifty 50":
                    value=row.get("Closing Index Value",row.get("CLOSING_INDEX_VALUE"))
                    if value is not None and str(value)!="nan":
                        return {"date":day.isoformat(),"url":url,"close":float(value)}
            last="Nifty 50 row absent"
        except Exception as exc:
            last=f"{type(exc).__name__}: {exc}"
    return {"date":day.isoformat(),"status":"unavailable","error":last}

def nse_overlap_checks(all_df):
    local=all_df.copy()
    local["ist_date"]=local["timestamp"].dt.tz_convert("Asia/Kolkata").dt.date
    days=sorted(set(local["ist_date"]))
    preferred=[dt.date(2024,7,5),dt.date(2024,7,8),dt.date(2025,7,4),dt.date(2025,7,7)]
    chosen=[d for d in preferred if d in days]
    if len(chosen)<2:
        chosen=days[:1]+([days[-1]] if days and days[-1]!=days[0] else [])
    if len(chosen)<2:
        raise SystemExit("ERROR: fewer than two distinct intraday dates for official-NSE overlap check")
    checks=[]
    for day in chosen[:2]:
        official=official_nse_close(day)
        rows=local[local["ist_date"]==day].sort_values("timestamp")
        if official.get("close") is None or rows.empty:
            raise SystemExit(f"ERROR: official/intraday overlap unavailable for {day}: {official}")
        hf_close=float(rows.iloc[-1]["spot"])
        diff=abs(hf_close-float(official["close"]))
        checks.append({**official,"intraday_last_spot":hf_close,"abs_diff":diff,"within_2_points":bool(diff<=2.0)})
        if diff>2.0:
            raise SystemExit(f"ERROR: intraday-vs-NSE EOD mismatch on {day}: {diff} points")
    return checks

overlap_checks=nse_overlap_checks(x)
span_days=(x["timestamp"].max()-x["timestamp"].min()).total_seconds()/86400
status="PASS" if len(x)>=50000 and span_days>=365*3 else "LOW_POWER"
report={
    "dataset":DATASET,
    "revision":revision,
    "file_path":FILE_PATH,
    "cache_hit":cache_hit,
    "rows":len(x),
    "span_days":span_days,
    "date_min":x["timestamp"].min().isoformat(),
    "date_max":x["timestamp"].max().isoformat(),
    "sha256":hashlib.sha256(local.read_bytes()).hexdigest(),
    "official_nse_overlap_checks":overlap_checks,
    "overlap_tolerance_points":2.0,
    "status":status,
    "adequacy_rule":">=50000 intraday observations spanning >=3 years; otherwise low-power warning and no stability claim",
    "license_note":"CC-BY-NC-4.0 derived research reference; not canonical execution feed.",
}
(OUT/"hf_intraday_acquisition.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({k:report[k] for k in ["dataset","revision","rows","span_days","status","sha256","official_nse_overlap_checks"]},indent=2))
