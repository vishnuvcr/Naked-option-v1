from __future__ import annotations
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cache" / "raw" / "nse_fno_samples"
RAW.mkdir(parents=True, exist_ok=True)

SAMPLES = {
    "2024-07-05_legacy": {
        "date": "2024-07-05",
        "url": "https://archives.nseindia.com/content/historical/DERIVATIVES/2024/JUL/fo05JUL2024bhav.csv.zip",
        "fallback": "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/JUL/fo05JUL2024bhav.csv.zip",
        "format": "legacy",
    },
    "2024-07-08_udiff": {
        "date": "2024-07-08",
        "url": "https://archives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv.zip",
        "fallback": "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv.zip",
        "format": "udiff",
    },
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept": "*/*",
}
def fetch(url: str, dst: Path):
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        if not data:
            return False, "empty_response"
        dst.write_bytes(data)
        return True, f"http_{getattr(resp, 'status', 200)}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

manifest = []
for key, spec in SAMPLES.items():
    dst = RAW / f"{key}.zip"
    if dst.exists() and dst.stat().st_size > 0:
        manifest.append({"id": key, "source": spec, "path": str(dst), "cache_hit": True})
        continue
    ok, msg = fetch(spec["url"], dst)
    used = spec["url"]
    if not ok:
        ok, msg = fetch(spec["fallback"], dst)
        used = spec["fallback"]
    if not ok:
        raise SystemExit(f"ERROR: failed to acquire {key}: {msg}")
    manifest.append({
        "id": key,
        "source": {**spec, "used_url": used},
        "path": str(dst),
        "cache_hit": False,
        "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
        "bytes": dst.stat().st_size,
    })

out = ROOT / "data" / "reports" / "official_sample_acquisition.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"parser_version": "phase2-acq-v1", "samples": manifest}, indent=2), encoding="utf-8")
print(out)
