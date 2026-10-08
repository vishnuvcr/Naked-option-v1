from __future__ import annotations

from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reports" / "phase8"
OUT.mkdir(parents=True, exist_ok=True)

HF_DATASET = "artist-23/nifty-options-data"
GITHUB_SOURCES = [
    "https://api.github.com/repos/SauMStats/nifty-options-data-engine",
    "https://api.github.com/repos/SauMStats/nifty-market-data-engine",
]
PUBLIC_SOURCE_URLS = {
    "nse_reports": "https://www.nseindia.com/all-reports-derivatives",
    "nse_contracts": "https://www.nseindia.com/static/products-services/equity-derivatives-contract-information",
    "bse": "https://www.bseindia.com/markets/Derivatives/derivatives.html",
    "hf_dataset": f"https://huggingface.co/datasets/{HF_DATASET}",
}

def get_json(url: str, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "NIFTY-Naked-Option-Research/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_head(url: str):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "NIFTY-Naked-Option-Research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"status": "PASS", "http_status": int(getattr(resp, "status", 200))}
    except Exception as exc:
        return {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}

report = {
    "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "free_source_first": True,
    "large_data_download_performed": False,
    "sources": {},
}

token = os.environ.get("HF_TOKEN")
hf_headers = {"User-Agent": "NIFTY-Naked-Option-Research/1.0"}
if token:
    hf_headers["Authorization"] = f"Bearer {token}"
try:
    meta = get_json(f"https://huggingface.co/api/datasets/{HF_DATASET}", hf_headers)
    report["sources"]["huggingface"] = {
        "status": "PASS",
        "dataset": HF_DATASET,
        "revision": meta.get("sha"),
        "siblings": len(meta.get("siblings", [])),
        "metadata": {
            "size": meta.get("size"),
            "downloads": meta.get("downloads"),
            "likes": meta.get("likes"),
        },
    }
except Exception as exc:
    report["sources"]["huggingface"] = {
        "status": "FAIL",
        "dataset": HF_DATASET,
        "error": f"{type(exc).__name__}: {exc}",
    }

for url in GITHUB_SOURCES:
    key = url.rsplit("/", 1)[-1]
    try:
        meta = get_json(url)
        report["sources"][key] = {
            "status": "PASS",
            "default_branch": meta.get("default_branch"),
            "updated_at": meta.get("updated_at"),
            "pushed_at": meta.get("pushed_at"),
        }
    except Exception as exc:
        report["sources"][key] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}

for key, url in PUBLIC_SOURCE_URLS.items():
    report["sources"][key + "_http_probe"] = {"url": url, **get_head(url)}

manifest_path = ROOT / "research" / "phase8" / "PHASE8_FROZEN_INPUT_MANIFEST.json"
report["frozen_input_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

path = OUT / "phase8_option_source_audit.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
