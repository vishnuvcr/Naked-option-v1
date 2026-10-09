from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_phase7_ensemble as p7


def test_prediction_panel_is_row_aligned_and_hashed():
    old_dir = p7.REFERENCE_DIR
    old_records = list(p7.PANEL_RECORDS)
    try:
        with tempfile.TemporaryDirectory(dir=ROOT / "data" / "reports") as td:
            p7.REFERENCE_DIR = Path(td)
            p7.PANEL_RECORDS.clear()
            ts = pd.to_datetime([
                "2025-01-02T09:30:00Z", "2025-01-02T10:30:00Z",
                "2025-01-02T11:30:00Z", "2025-01-02T12:30:00Z",
            ], utc=True)
            df = pd.DataFrame({
                "timestamp": ts,
                "minute_of_day": [570, 630, 690, 750],
                "date": [t.date() for t in ts],
            })
            y = np.array([1.0, 0.0, 1.0, 1.0])
            future = np.array([0.01, -0.02, 0.03, 0.04])
            candidates = {
                f"P{i:02d}": np.array([0.51, 0.49, 0.62, 0.71]) + (i - 1) * 0.001
                for i in range(1, 11)
            }
            p7.write_prediction_panel(
                "intraday", 60, df, True, y, future, candidates,
                [np.array([0, 1]), np.array([2, 3])],
            )
            record = p7.PANEL_RECORDS[-1]
            path = Path(td) / "phase7_predictions_intraday_H60.parquet"
            frame = pd.read_parquet(path)
            assert len(frame) == 4
            assert frame["source_row_index"].tolist() == [0, 1, 2, 3]
            assert frame["block_index"].tolist() == [0, 0, 1, 1]
            assert frame["label_direction"].tolist() == y.tolist()
            assert frame["future_return"].tolist() == future.tolist()
            assert frame["P07"].tolist() == candidates["P07"].tolist()
            assert frame["decision_timestamp"].astype(str).tolist() == ts.astype(str).tolist()
            assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
            assert record["rows"] == 4 and record["horizon"] == 60
    finally:
        p7.REFERENCE_DIR = old_dir
        p7.PANEL_RECORDS.clear()
        p7.PANEL_RECORDS.extend(old_records)


def test_manifest_records_hashes_and_runtime():
    old_dir = p7.REFERENCE_DIR
    old_records = list(p7.PANEL_RECORDS)
    try:
        with tempfile.TemporaryDirectory(dir=ROOT / "data" / "reports") as td:
            p7.REFERENCE_DIR = Path(td)
            p7.PANEL_RECORDS.clear()
            aggregate = Path(td) / "aggregate.json"
            aggregate.write_text(json.dumps({"protocol": "test"}), encoding="utf-8")
            p7.write_reference_manifest(aggregate)
            manifest = json.loads((Path(td) / "phase7_reference_manifest.json").read_text())
            assert manifest["status"] == "COMPLETE"
            assert manifest["aggregate_result"]["sha256"] == hashlib.sha256(aggregate.read_bytes()).hexdigest()
            assert manifest["source_files"]["intraday_parquet"]["sha256"]
            assert manifest["source_files"]["daily_csv"]["sha256"]
            assert set(manifest["runtime"]) >= {"python", "platform", "numpy", "pandas", "scikit_learn", "scipy", "pyarrow", "threadpoolctl", "threadpools"}
            assert manifest["prediction_panels"] == []
    finally:
        p7.REFERENCE_DIR = old_dir
        p7.PANEL_RECORDS.clear()
        p7.PANEL_RECORDS.extend(old_records)


if __name__ == "__main__":
    test_prediction_panel_is_row_aligned_and_hashed()
    test_manifest_records_hashes_and_runtime()
    print("Phase 7 reference-artifact regression PASS")
