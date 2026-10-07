from pathlib import Path
import datetime
import json
import os
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/reports"
OUT.mkdir(parents=True,exist_ok=True)
DATASET=os.environ.get("HF_INTRADAY_DATASET","thetrademarkk/india-index-options-1m")
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
target="index/NIFTY.parquet"
visible=target in siblings

report={
    "dataset":DATASET,
    "revision":revision,
    "target_file":target,
    "target_visible":visible,
    "file_count_in_siblings":len(siblings),
    "token_present":bool(TOKEN),
    "status":"PASS" if visible else "FAIL",
    "coverage_note":"NIFTY 1-minute index spot reference; derived research data, not canonical exchange feed.",
}
(OUT/"hf_intraday_discovery.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if not visible:
    raise SystemExit("ERROR: HF dataset does not expose index/NIFTY.parquet")
print(json.dumps(report,indent=2))
