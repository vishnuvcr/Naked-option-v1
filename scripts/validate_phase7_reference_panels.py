from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_phase7_ensemble as p7
from reconstruct_phase7_predictions import recursive_compare, TOL

METHODS = [f"P{i:02d}" for i in range(1, 11)]
ABSTAIN = {"P05": (0.45, 0.55), "P06": (0.40, 0.60)}
LAYERS = {"daily": (False, [1, 2, 3, 5, 10]), "intraday": (True, [5, 15, 30, 60, 120])}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def blocks_from_panel(frame: pd.DataFrame):
    ids = frame["block_index"].to_numpy(dtype=int)
    unique = np.unique(ids)
    if np.any(ids < 0) or not np.array_equal(unique, np.arange(len(unique))):
        raise SystemExit("PANEL_ERROR: block_index must be contiguous from zero with no missing assignments")
    blocks = [np.flatnonzero(ids == i) for i in unique]
    for rows in blocks:
        if len(rows) == 0:
            raise SystemExit("PANEL_ERROR: empty chronological block")
    return blocks


def compare_panel(frame: pd.DataFrame, expected_cell: dict, intraday: bool):
    required = {"layer", "horizon", "source_row_index", "decision_timestamp",
                "label_direction", "future_return", "block_index", *METHODS}
    missing = required - set(frame.columns)
    if missing:
        raise SystemExit(f"PANEL_ERROR: missing required columns: {sorted(missing)}")
    if frame.empty:
        raise SystemExit("PANEL_ERROR: empty prediction panel")
    if frame["source_row_index"].tolist() != list(range(len(frame))):
        raise SystemExit("PANEL_ERROR: source_row_index is not a unique ordered zero-based sequence")
    ts = pd.to_datetime(frame["decision_timestamp"], utc=intraday, errors="raise")
    if not ts.is_monotonic_increasing or ts.has_duplicates:
        raise SystemExit("PANEL_ERROR: decision timestamps must be strictly increasing and unique")
    if set(frame["layer"].astype(str)) != {str(frame["layer"].iloc[0])}:
        raise SystemExit("PANEL_ERROR: mixed layers within panel")
    if set(frame["horizon"].astype(int)) != {int(frame["horizon"].iloc[0])}:
        raise SystemExit("PANEL_ERROR: mixed horizons within panel")

    y = frame["label_direction"].to_numpy(dtype=float)
    future = frame["future_return"].to_numpy(dtype=float)
    candidates = {m: frame[m].to_numpy(dtype=float) for m in METHODS}
    blocks = blocks_from_panel(frame)
    block_len = 60 if intraday else 20
    baseline = p7.causal_baseline(y, blocks)
    actual = {}
    for name, pred in candidates.items():
        mask = None
        extra = {}
        if name in ABSTAIN:
            lo, hi = ABSTAIN[name]
            finite = np.isfinite(pred)
            mask = finite & ~((pred >= lo) & (pred <= hi))
            extra = {
                "coverage": float(mask.sum() / finite.sum()) if finite.sum() else 0.0,
                "trade_n": int(mask.sum()),
                "evaluable_n": int(finite.sum()),
            }
        res = p7.p6.metrics(y, pred, future, block_len, extra=extra, mask=mask)
        res["chronological_blocks"] = p7.block_diagnostics(y, pred, blocks)
        actual[name] = res
    actual["_FAMILY_TEST"] = p7.family_bootstrap(y, candidates, baseline, block_len)

    expected = json.loads(json.dumps(expected_cell))
    for name in ("P08", "P09", "P10"):
        expected[name].pop("regime_diagnostics", None)
        expected[name].pop("regime_fallback_count", None)
    failures = recursive_compare(expected, actual)
    if failures:
        raise SystemExit("PANEL_METRIC_ERROR: " + "; ".join(failures[:10]))
    return {"rows": int(len(frame)), "blocks": len(blocks), "metric_comparison": "PASS"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True, help="Extracted phase7-ensemble-reference artifact directory")
    ap.add_argument("--output-dir", default=str(ROOT / "data/reports/phase8"))
    args = ap.parse_args()
    artifact_dir = Path(args.artifact_dir)
    output_dir = Path(args.output_dir)
    aggregate_path = artifact_dir / "phase7_ensemble_results.json"
    reference_dir = artifact_dir / "phase7_reference"
    manifest_path = reference_dir / "phase7_reference_manifest.json"
    if not aggregate_path.is_file() or not manifest_path.is_file():
        raise SystemExit("ARTIFACT_ERROR: aggregate JSON or reference manifest missing")
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPLETE" or manifest.get("schema_version") != 1:
        raise SystemExit("ARTIFACT_ERROR: reference manifest status/schema invalid")
    if sha256(aggregate_path) != manifest["aggregate_result"]["sha256"]:
        raise SystemExit("ARTIFACT_ERROR: aggregate JSON SHA-256 mismatch")
    if manifest.get("protocol") != "research/phase7/PHASE7_METHOD_SPEC.md" or manifest.get("seed") != 42:
        raise SystemExit("ARTIFACT_ERROR: protocol/seed mismatch")
    if len(manifest.get("prediction_panels", [])) != 10:
        raise SystemExit("ARTIFACT_ERROR: expected exactly ten horizon panels")

    expected_specs = {(layer, H) for layer, (_, horizons) in LAYERS.items() for H in horizons}
    found_specs = {(str(x.get("layer")), int(x.get("horizon"))) for x in manifest["prediction_panels"]}
    if found_specs != expected_specs:
        raise SystemExit(f"ARTIFACT_ERROR: panel coverage mismatch: {sorted(found_specs)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    cells = []
    for record in manifest["prediction_panels"]:
        layer, H = str(record["layer"]), int(record["horizon"])
        # Upload-artifact strips the common data/reports prefix.
        panel_path = reference_dir / f"phase7_predictions_{layer}_H{H}.parquet"
        if not panel_path.is_file():
            raise SystemExit(f"ARTIFACT_ERROR: missing panel file {panel_path.name}")
        if sha256(panel_path) != record["sha256"]:
            raise SystemExit(f"ARTIFACT_ERROR: panel SHA-256 mismatch: {panel_path.name}")
        frame = pd.read_parquet(panel_path)
        intraday, horizons = LAYERS[layer]
        if H not in horizons:
            raise SystemExit(f"ARTIFACT_ERROR: unregistered horizon {layer} H={H}")
        if int(aggregate[layer]["rows"]) <= 0:
            raise SystemExit(f"ARTIFACT_ERROR: invalid aggregate row count for {layer}")
        expected_cell = aggregate[layer]["horizons"][str(H)]
        metrics = compare_panel(frame, expected_cell, intraday)
        out = output_dir / panel_path.name
        shutil.copy2(panel_path, out)
        cells.append({"layer": layer, "horizon": H, "rows": metrics["rows"],
                      "blocks": metrics["blocks"], "reference_match": True,
                      "copied_path": str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out)})
    result = {
        "status": "PASS", "mode": "saved-row-level-panel-no-model-refit",
        "reference_run_id": manifest.get("run_id"), "reference_commit": manifest.get("commit"),
        "artifact_manifest_sha256": sha256(manifest_path),
        "aggregate_sha256": sha256(aggregate_path), "tolerance_abs": TOL,
        "cells": cells, "total_cells": len(cells), "all_cells_reproduced": len(cells) == 10,
    }
    (output_dir / "phase8_forecast_reconstruction_manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
