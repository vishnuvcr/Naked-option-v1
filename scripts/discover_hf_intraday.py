from __future__ import annotations
from pathlib import Path
import datetime, json, os, re, urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)
DATASET=os.environ.get("HF_INTRADAY_DATASET","rissin/nse-options-intraday")
TOKEN=os.environ.get("HF_TOKEN")
headers={"User-Agent":"NIFTY-Naked-Option-Research/1.0"}
if TOKEN:
    headers["Authorization"]=f"Bearer {TOKEN}"

url=f"https://huggingface.co/api/datasets/{DATASET}"
req=urllib.request.Request(url,headers=headers)
with urllib.request.urlopen(req,timeout=60) as resp:
    meta=json.loads(resp.read().decode("utf-8"))

revision=meta.get("sha")
siblings=[x.get("rfilename","") for x in meta.get("siblings",[])]
nifty=[p for p in siblings if "NIFTY" in p.upper() and p.lower().endswith((".parquet",".csv",".csv.gz"))]
dated=[]
for p in nifty:
    for m in re.finditer(r"(20\d\d[-_]\d\d[-_]\d\d)",p):
        try:
            dated.append((datetime.date.fromisoformat(m.group(1).replace("_","-")),p))
        except Exception:
            pass

report={
    "dataset":DATASET,
    "revision":revision,
    "file_count_in_siblings":len(siblings),
    "nifty_file_count":len(nifty),
    "sample_nifty_files":nifty[:100],
    "dated_nifty_files":len(dated),
    "date_min":min([d for d,_ in dated]).isoformat() if dated else None,
    "date_max":max([d for d,_ in dated]).isoformat() if dated else None,
    "token_present":bool(TOKEN),
    "status":"PASS" if nifty else "FAIL",
}
(OUT/"hf_intraday_discovery.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if not nifty:
    raise SystemExit("ERROR: HF dataset has no NIFTY files visible in siblings metadata")
print(json.dumps(report,indent=2))
