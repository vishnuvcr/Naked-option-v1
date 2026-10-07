from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "reports"

IDS = [f"B{i}" for i in range(12)]


def load(name: str):
    path = REPORT / name
    if not path.exists():
        raise SystemExit(f"ERROR: missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_horizon_block(block, label):
    missing = [x for x in IDS if x not in block]
    if missing:
        raise SystemExit(f"ERROR: {label} missing baselines: {missing}")
    for bid in IDS:
        item = block[bid]
        if not isinstance(item, dict):
            raise SystemExit(f"ERROR: {label} {bid} must be an object")
        status = item.get("status", "EXECUTED" if "n" in item else None)
        if status not in {"EXECUTED", "BLOCKED_DATA", "NOT_APPLICABLE"}:
            raise SystemExit(f"ERROR: {label} {bid} invalid status {status}")
        if status == "EXECUTED" and "n" not in item:
            raise SystemExit(f"ERROR: {label} {bid} executed without metrics")
        if status == "BLOCKED_DATA" and not item.get("reason"):
            raise SystemExit(f"ERROR: {label} {bid} blocked without reason")


daily = load("phase3_daily_baseline_results.json")
intraday = load("phase3_intraday_baseline_results.json")

expected_daily = {"1","2","3","5","10"}
expected_intraday = {"5","15","30","60","120"}
daily_h = set(daily.get("horizons", {}))
intraday_h = set(intraday.get("horizons", {}))
if daily_h != expected_daily:
    raise SystemExit(f"ERROR: daily horizon set mismatch: {sorted(daily_h)}")
if intraday_h != expected_intraday:
    raise SystemExit(f"ERROR: intraday horizon set mismatch: {sorted(intraday_h)}")

for h, block in daily["horizons"].items():
    check_horizon_block(block, f"daily horizon {h}")

for h, block in intraday["horizons"].items():
    check_horizon_block(block, f"intraday horizon {h}")

if daily.get("data_rows", 0) <= 0:
    raise SystemExit("ERROR: daily baseline has no data rows")
if intraday.get("full_rows", 0) <= 0:
    raise SystemExit("ERROR: intraday baseline has no data rows")

print("PASS: Phase 3 result packet contains an explicit disposition for every B0-B11 baseline.")
