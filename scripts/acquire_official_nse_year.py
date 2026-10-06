from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEAR = int(os.environ.get("YEAR", "2024"))
START = dt.date.fromisoformat(os.environ.get("WINDOW_START", f"{YEAR}-01-01"))
END = dt.date.fromisoformat(os.environ.get("WINDOW_END", f"{YEAR}-12-31"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "3"))
SLEEP = float(os.environ.get("REQUEST_SLEEP", "0.20"))

RAW = ROOT / "data" / "cache" / "raw" / "nse_year" / str(YEAR)
REPORT = ROOT / "data" / "reports"
RAW.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 NIFTY-Naked-Option-Research/1.0",
    "Accept": "*/*",
}

def urls(d: dt.date) -> list[tuple[str, str]]:
    y = d.strftime("%Y")
    mon = d.strftime("%b").upper()
    stamp = d.strftime("%d%b%Y").upper()
    legacy = (
        "https://archives.nseindia.com/content/historical/DERIVATIVES/"
        f"{y}/{mon}/fo{stamp}bhav.csv.zip"
    )
    udiff = (
        "https://archives.nseindia.com/content/fo/"
        f"BhavCopy_NSE_FO_0_0_0_{d.strftime('%Y%m%d')}_F_0000.csv.zip"
    )
    return [("legacy", legacy), ("udiff", udiff)]

def download_one(d: dt.date) -> dict:
    if d.weekday() >= 5:
        return {"date": d.isoformat(), "status": "weekend"}
    dst = RAW / f"{d.strftime('%Y%m%d')}.zip"
    if dst.exists() and dst.stat().st_size > 0:
        return {
            "date": d.isoformat(),
            "status": "cache_hit",
            "path": str(dst.relative_to(ROOT)),
            "bytes": dst.stat().st_size,
            "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
        }

    last_error = None
    for fmt, url in urls(d):
        try:
            req = urllib.request.Request(url, headers=HEADERS, method="GET")
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if not data or len(data) < 1000:
                raise ValueError("empty_or_tiny_archive")
            if not data[:2] == b"PK":
                raise ValueError("response_is_not_zip")
            dst.write_bytes(data)
            time.sleep(SLEEP)
            return {
                "date": d.isoformat(),
                "status": "downloaded",
                "format": fmt,
                "url": url,
                "path": str(dst.relative_to(ROOT)),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

    return {
        "date": d.isoformat(),
        "status": "unresolved",
        "error": last_error,
    }

dates=[]
d=START
while d <= END:
    dates.append(d)
    d += dt.timedelta(days=1)

results=[]
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    futures=[pool.submit(download_one,d) for d in dates]
    for fut in as_completed(futures):
        results.append(fut.result())

results.sort(key=lambda r:r["date"])
report={
    "year":YEAR,
    "window_start":START.isoformat(),
    "window_end":END.isoformat(),
    "generated_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
    "calendar_days":len(dates),
    "weekdays":sum(1 for d in dates if d.weekday()<5),
    "downloaded_or_cached":sum(r["status"] in {"downloaded","cache_hit"} for r in results),
    "unresolved":sum(r["status"]=="unresolved" for r in results),
    "weekends":sum(r["status"]=="weekend" for r in results),
    "results":results,
}
(REPORT/f"nse_year_{YEAR}_acquisition.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(json.dumps({
    "year":YEAR,
    "downloaded_or_cached":report["downloaded_or_cached"],
    "unresolved":report["unresolved"],
    "weekends":report["weekends"],
},indent=2))
