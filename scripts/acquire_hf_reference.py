from __future__ import annotations
from pathlib import Path
import hashlib
import json
import os
import re
import urllib.request
import datetime

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cache" / "raw" / "hf_reference"
RAW.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

DATASET = "thetrademarkk/india-index-options-1m"
TARGET_DATE = datetime.date(2024, 7, 8)
MAX_BYTES = 50 * 1024 * 1024
TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    raise SystemExit("ERROR: HF_TOKEN is required for Phase 2B Hugging Face acquisition")

HEADERS = {"User-Agent": "NIFTY-Naked-Option-Research/1.0", "Authorization": f"Bearer {TOKEN}"}

def get_json(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

meta = get_json(f"https://huggingface.co/api/datasets/{DATASET}")
revision = meta.get("sha")
siblings = [x.get("rfilename","") for x in meta.get("siblings", [])]

candidates=[]
for path in siblings:
    if not path.startswith("options/NIFTY/") or not path.endswith(".parquet"):
        continue
    m=re.search(r"(20\d\d-\d\d-\d\d)", path)
    if not m:
        continue
    d=datetime.date.fromisoformat(m.group(1))
    distance=abs((d-TARGET_DATE).days)
    candidates.append((distance,path,d))

if not candidates:
    raise SystemExit("ERROR: no NIFTY parquet candidates found in HF dataset")
candidates.sort(key=lambda x:(x[0],x[2]))
distance, path, file_date = candidates[0]
if distance > 31:
    raise SystemExit(f"ERROR: nearest HF NIFTY file is {distance} days from target date")

local = RAW / Path(path).name
cache_hit=False
if not local.exists() or local.stat().st_size==0:
    url=f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{path}"
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=180) as resp:
        data=resp.read()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"ERROR: selected reference file is {len(data)} bytes > {MAX_BYTES}")
    local.write_bytes(data)
else:
    cache_hit=True

sha=hashlib.sha256(local.read_bytes()).hexdigest()
report={
    "dataset":DATASET,
    "revision":revision,
    "target_date":TARGET_DATE.isoformat(),
    "selected_file":path,
    "file_date":file_date.isoformat(),
    "distance_days":distance,
    "local_path":str(local.relative_to(ROOT)),
    "bytes":local.stat().st_size,
    "sha256":sha,
    "cache_hit":cache_hit,
    "license":"CC-BY-NC-4.0",
}
(OUT/"hf_reference_acquisition.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(OUT/"hf_reference_acquisition.json")
