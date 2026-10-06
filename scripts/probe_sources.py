from __future__ import annotations
from pathlib import Path
import csv
import json
import time
import urllib.request
import datetime

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / "research" / "data" / "SOURCE_MANIFEST.csv"
out_dir = ROOT / "data" / "reports"
out_dir.mkdir(parents=True, exist_ok=True)

TIMEOUT = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept": "text/html,application/json,*/*",
}

def probe(url: str):
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            sample = resp.read(4096)
            return {
                "status": resp.status,
                "content_type": resp.headers.get("Content-Type"),
                "bytes_sampled": len(sample),
                "latency_sec": round(time.time()-start, 3),
                "error": None,
            }
    except Exception as e:
        return {
            "status": None,
            "content_type": None,
            "bytes_sampled": 0,
            "latency_sec": round(time.time()-start, 3),
            "error": f"{type(e).__name__}: {e}",
        }

with manifest_path.open("r", encoding="utf-8", newline="") as fh:
    sources = list(csv.DictReader(fh))

results = []
for s in sources:
    if s["status"] == "SAMPLE_ONLY":
        continue
    results.append({**s, **probe(s["url_or_repo"])})

report = {
    "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "research_repo": "vishnuvcr/Naked-option-v1",
    "results": results,
}
(out_dir / "source_probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(out_dir / "source_probe.json")
