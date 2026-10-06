from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from urllib.request import Request, urlopen
import datetime

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/cache/raw/hf_s07_reference"
RAW.mkdir(parents=True,exist_ok=True)
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)

DATASET="artist-23/nifty-options-data"
TARGET_DATE=datetime.date(2024,7,11)
FILES=["NIFTY/WEEK/ATM_CE.parquet","NIFTY/WEEK/ATM_PE.parquet"]
TOKEN=os.environ.get("HF_TOKEN")
if not TOKEN:
    raise SystemExit("ERROR: HF_TOKEN is required for S31 acquisition")
HEADERS={"User-Agent":"NIFTY-Naked-Option-Research/1.0","Authorization":f"Bearer {TOKEN}"}

def get_json(url):
    req=Request(url,headers=HEADERS)
    with urlopen(req,timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

meta=get_json(f"https://huggingface.co/api/datasets/{DATASET}")
revision=meta.get("sha")
siblings={x.get("rfilename") for x in meta.get("siblings",[])}
results=[]
for rel in FILES:
    if rel not in siblings:
        results.append({"file":rel,"status":"missing_in_dataset"})
        continue
    dst=RAW/Path(rel).name
    hit=dst.exists() and dst.stat().st_size>0
    if not hit:
        url=f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{rel}"
        req=Request(url,headers=HEADERS)
        with urlopen(req,timeout=180) as resp:
            data=resp.read()
        if len(data)>60*1024*1024:
            raise SystemExit(f"ERROR: {rel} exceeds 60MB research-reference cap")
        dst.write_bytes(data)
    results.append({
        "file":rel,
        "status":"ok",
        "cache_hit":hit,
        "revision":revision,
        "path":str(dst.relative_to(ROOT)),
        "bytes":dst.stat().st_size,
        "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
    })
(OUT/"s31_reference_acquisition.json").write_text(json.dumps({
    "dataset":DATASET,
    "revision":revision,
    "target_date":TARGET_DATE.isoformat(),
    "files":results,
},indent=2),encoding="utf-8")
print(OUT/"s31_reference_acquisition.json")
