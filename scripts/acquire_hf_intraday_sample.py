from __future__ import annotations
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import re
import urllib.request
import urllib.parse
import numpy as np

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/phase3/hf_intraday"
OUT=ROOT/"data/reports"
RAW.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)

DATASET=os.environ.get("HF_INTRADAY_DATASET","rissin/nse-options-intraday")
TOKEN=os.environ.get("HF_TOKEN")
HEADERS={"User-Agent":"NIFTY-Naked-Option-Research/1.0"}
if TOKEN:
    HEADERS["Authorization"]=f"Bearer {TOKEN}"

meta_url=f"https://huggingface.co/api/datasets/{DATASET}"
req=urllib.request.Request(meta_url,headers=HEADERS)
with urllib.request.urlopen(req,timeout=60) as resp:
    meta=json.loads(resp.read().decode("utf-8"))

revision=meta.get("sha")
siblings=[x.get("rfilename","") for x in meta.get("siblings",[])]
dated=[]
for p in siblings:
    if "NIFTY" not in p.upper():
        continue
    if not p.lower().endswith((".parquet",".csv",".csv.gz")):
        continue
    matches=re.findall(r"(20\d\d[-_]\d\d[-_]\d\d)",p)
    for m in matches:
        try:
            d=dt.date.fromisoformat(m.replace("_","-"))
            dated.append((d,p))
            break
        except Exception:
            pass

if not dated:
    raise SystemExit("ERROR: no dated NIFTY intraday files discovered")

dated.sort()
# Deterministic stratified sample: 6 dates per calendar year where available,
# plus first/last date. The sample is for research label validation, not a
# replacement for a complete exchange archive.
chosen=[]
for year in range(dated[0][0].year,dated[-1][0].year+1):
    pool=[x for x in dated if x[0].year==year]
    if not pool:
        continue
    idxs=np.linspace(0,len(pool)-1,min(6,len(pool)),dtype=int) if False else None
    n=min(6,len(pool))
    for k in range(n):
        idx=round(k*(len(pool)-1)/(n-1)) if n>1 else 0
        chosen.append(pool[idx])
chosen=sorted(set(chosen))
chosen_files=[p for _,p in chosen]

records=[]
for d,p in chosen:
    local=RAW/(Path(p).name)
    cache_hit=local.exists() and local.stat().st_size>0
    if not cache_hit:
        url=f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{urllib.parse.quote(p,safe='/')}"
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=180) as resp:
            data=resp.read()
        if len(data)>50*1024*1024:
            raise SystemExit(f"ERROR: file too large for Phase 3 sample: {p} -> {len(data)} bytes")
        local.write_bytes(data)
    records.append({
        "date":d.isoformat(),
        "path":p,
        "local_path":str(local.relative_to(ROOT)),
        "cache_hit":cache_hit,
        "bytes":local.stat().st_size,
        "sha256":hashlib.sha256(local.read_bytes()).hexdigest(),
    })

def map_col(cols,cands):
    low={c.lower():c for c in cols}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    norm={c.lower().replace("_","").replace(" ","") for c in cands}
    for c in cols:
        if c.lower().replace("_","").replace(" ","") in norm:
            return c
    return None

frames=[]
file_reports=[]
for rec in records:
    path=ROOT/rec["local_path"]
    if path.suffix.lower()==".parquet":
        df=pd.read_parquet(path)
    else:
        df=pd.read_csv(path)
    cols=list(df.columns)
    ts=map_col(cols,["timestamp","datetime","date_time","datetime_ist","time","DateTime"])
    spot=map_col(cols,["underlying","underlying_value","underlying_price","spot","spot_price","undrlygprc"])
    if ts is None or spot is None:
        file_reports.append({**rec,"status":"NO_USABLE_SPOT_SCHEMA","columns":cols[:100]})
        continue
    x=pd.DataFrame({
        "timestamp":pd.to_datetime(df[ts],errors="coerce",utc=True),
        "spot":pd.to_numeric(df[spot],errors="coerce"),
        "source_file":rec["path"],
    }).dropna()
    x=x.sort_values("timestamp").drop_duplicates("timestamp")
    frames.append(x)
    file_reports.append({**rec,"status":"OK","rows":len(x),"timestamp_min":x["timestamp"].min().isoformat(),"timestamp_max":x["timestamp"].max().isoformat(),"columns":cols[:100]})

if not frames:
    raise SystemExit("ERROR: selected HF files contain no usable underlying spot series")

all_df=pd.concat(frames,ignore_index=True).sort_values("timestamp").drop_duplicates("timestamp")
span_days=(all_df["timestamp"].max()-all_df["timestamp"].min()).total_seconds()/86400
status="PASS" if len(all_df)>=50000 and span_days>=365*3 else "LOW_POWER"
out_path=RAW/"nifty_intraday_reference.parquet"
all_df.to_parquet(out_path,index=False)

report={
    "dataset":DATASET,
    "revision":revision,
    "selected_file_count":len(records),
    "successful_file_count":sum(1 for r in file_reports if r["status"]=="OK"),
    "rows":len(all_df),
    "span_days":span_days,
    "date_min":all_df["timestamp"].min().isoformat(),
    "date_max":all_df["timestamp"].max().isoformat(),
    "sha256":hashlib.sha256(out_path.read_bytes()).hexdigest(),
    "selected_files":records,
    "file_reports":file_reports,
    "status":status,
    "adequacy_rule":">=50000 intraday observations spanning >=3 years; otherwise low-power warning and no stability claim",
    "license_note":"Derived research reference; not canonical execution feed.",
}
(OUT/"hf_intraday_acquisition.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({k:report[k] for k in ["dataset","revision","rows","span_days","status","sha256"]},indent=2))
