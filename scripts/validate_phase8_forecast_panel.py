from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "reports" / "phase8"
EXPECTED = {"daily": (1, 2, 3, 5, 10), "intraday": (5, 15, 30, 60, 120)}
METHODS = [f"P{i:02d}" for i in range(1, 11)]
MANIFEST = REPORT / "phase8_forecast_reconstruction_manifest.json"

def fail(msg: str) -> None:
    raise SystemExit(f"FORECAST_PANEL_ERROR: {msg}")

def main() -> None:
    if not MANIFEST.exists():
        fail("reconstruction manifest missing")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "PASS" or not manifest.get("all_cells_reproduced"):
        fail("reconstruction manifest is not PASS")
    files = manifest.get("prediction_files", [])
    if len(files) != 10 or manifest.get("total_cells") != 10:
        fail("expected exactly 10 layer/horizon prediction files")

    seen = set()
    for item in files:
        layer, H = item["layer"], int(item["horizon"])
        key = (layer, H)
        if layer not in EXPECTED or H not in EXPECTED[layer]:
            fail(f"unexpected file cell {key}")
        if key in seen:
            fail(f"duplicate cell {key}")
        seen.add(key)

        path = ROOT / item["path"]
        if not path.exists():
            fail(f"prediction parquet missing: {path}")
        df = pd.read_parquet(path)
        required = {"layer","horizon","decision_timestamp","label_direction","future_return",*METHODS}
        missing = required - set(df.columns)
        if missing:
            fail(f"{key} missing columns: {sorted(missing)}")
        if len(df) != int(item["rows"]):
            fail(f"{key} row-count mismatch")
        if not df["decision_timestamp"].is_monotonic_increasing:
            fail(f"{key} decision timestamps are not monotone")
        if df["decision_timestamp"].duplicated().any():
            fail(f"{key} duplicate decision timestamps")
        if (df["layer"] != layer).any() or (df["horizon"] != H).any():
            fail(f"{key} mixed layer/horizon rows")
        for m in METHODS:
            p = pd.to_numeric(df[m], errors="coerce")
            bad = p.notna() & ((p < 0.0) | (p > 1.0))
            if bool(bad.any()):
                fail(f"{key}/{m} probability outside [0,1]")

    expected = {(layer,H) for layer,hs in EXPECTED.items() for H in hs}
    if seen != expected:
        fail(f"cell coverage mismatch: observed={sorted(seen)} expected={sorted(expected)}")

    out = REPORT / "phase8_forecast_panel_validation.json"
    out.write_text(json.dumps({
        "status":"PASS",
        "cells":len(seen),
        "total_prediction_rows":int(sum(int(x["rows"]) for x in files)),
        "methods":METHODS,
        "expected_layers_horizons":{k:list(v) for k,v in EXPECTED.items()}
    }, indent=2), encoding="utf-8")
    print(out)

if __name__ == "__main__":
    main()
