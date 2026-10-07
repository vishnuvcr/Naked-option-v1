from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

datasets = [
    "rissin/nse-options-intraday",
    "artist-23/nifty-options-data",
    "thetrademarkk/india-index-options-1m",
]
token = os.environ.get("HF_TOKEN")
results=[]
for ds in datasets:
    req=Request(
        f"https://huggingface.co/api/datasets/{ds}",
        headers={
            "User-Agent":"NIFTY-Naked-Option-Research/1.0",
            **({"Authorization":f"Bearer {token}"} if token else {})
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            body=resp.read()
        meta=json.loads(body.decode("utf-8"))
        results.append({
            "dataset": ds,
            "status": "ok",
            "token_present": bool(token),
            "sha": meta.get("sha"),
            "siblings": [x.get("rfilename") for x in meta.get("siblings", [])[:50]],
        })
    except Exception as exc:
        results.append({
            "dataset": ds,
            "status": "error",
            "token_present": bool(token),
            "error": f"{type(exc).__name__}: {exc}",
        })

(OUT/"huggingface_dataset_probe.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
print(OUT/"huggingface_dataset_probe.json")
