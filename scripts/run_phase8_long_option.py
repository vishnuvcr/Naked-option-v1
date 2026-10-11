from __future__ import annotations

"""Fail-closed Phase 8 runner shell.

The accepted Run #994 forecasts are read as saved probabilities only. This first
runner gate performs forecast-integrity and cached-composite preflight; it does
not fabricate a quote history or run empirical P&L. A future empirical executor
must be separately tester-reviewed after a point-in-time fixed-contract input
panel and one-use authorization are approved.
"""

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import phase8_execution_engine as engine

REFERENCE_RUN_ID = "37957677656"
REFERENCE_COMMIT = "b50be8cfa1ebe008a800e65a53f9c0fb2581aecb"
REFERENCE_ARTIFACT_SHA256 = "3e8a22ded608668b5674f7aed609fefa5c4befcde39a58b7f208e59ab25959a9"
REFERENCE_MANIFEST_SHA256 = "f0efc378bb3c41c8b51c6f47f0f9b7336111e57527d9e047241856274fa49091"
REFERENCE_AGGREGATE_SHA256 = "96c1428f448b1f91e50a2efd1253884e0f11d044c1c57d9a1fda60d61ab7fc39"

COMPOSITE_ARTIFACT_ID = 11698879857
COMPOSITE_SOURCE_RUN_ID = 38131641336
COMPOSITE_GZIP_SHA256 = "f0d7057c189985065d346811057e8c1b6c0aeed25528ee90b29a8d2fd568a7b5"
COMPOSITE_CANONICAL_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
COMPOSITE_ROWS = 8_999_865
COMPOSITE_COLUMNS = 47
ROW_COUNTS = {"OPTION": 8_490_723, "SPOT": 509_142}

METHODS = [f"P{i:02d}" for i in range(1, 11)]
LAYERS = {"daily": (1, 2, 3, 5, 10), "intraday": (5, 15, 30, 60, 120)}
EXPECTED_PANEL_ROWS = 50_555
KEY_FEATURES = (
    "timestamp_epoch", "row_type", "returned_strike", "option_type",
    "option_open", "option_high", "option_low", "option_close",
    "expiry_date", "expiry_mapping_source", "time_to_expiry_years",
    "lot_size", "tick_size",
)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def build_forecast_cells() -> list[dict]:
    cells = []
    for layer, horizons in LAYERS.items():
        for horizon in horizons:
            for method in METHODS:
                cells.append({
                    "layer": layer,
                    "horizon": int(horizon),
                    "method": method,
                    "forecast_cell_id": f"{layer}-H{horizon}-{method}",
                })
    if len(cells) != 100:
        raise AssertionError(f"forecast grid drift: expected 100, got {len(cells)}")
    return cells

def build_registered_grid() -> list[dict]:
    out = []
    for forecast in build_forecast_cells():
        for delta in engine.DELTA_TARGETS:
            for dte_bucket in engine.DTE_BUCKETS:
                for exit_policy in engine.EXIT_POLICIES:
                    config = dict(forecast)
                    config.update({
                        "delta_target": float(delta),
                        "dte_bucket": str(dte_bucket),
                        "exit_policy": str(exit_policy),
                    })
                    config["config_id"] = (
                        f"{forecast['forecast_cell_id']}-D{delta:.2f}-"
                        f"{dte_bucket}-{exit_policy}"
                    )
                    out.append(config)
    if len(out) != 4_800 or len({x["config_id"] for x in out}) != 4_800:
        raise AssertionError("registered 4,800-cell execution universe is incomplete or duplicated")
    return out

def _panel_path(reference_root: Path, record: dict) -> Path:
    # The artifact is unpacked at phase7_reference/; reference paths in its
    # manifest point to the producer repo's data/reports/ tree.
    return reference_root / "phase7_reference" / Path(record["path"]).name

def validate_saved_forecasts(reference_root: Path) -> dict:
    manifest_path = reference_root / "phase7_reference" / "phase7_reference_manifest.json"
    aggregate_path = reference_root / "phase7_ensemble_results.json"
    if not manifest_path.is_file() or not aggregate_path.is_file():
        raise ValueError("FORECAST_INPUT_BLOCKED: missing Run #994 manifest or paired aggregate")
    manifest_hash = sha256_file(manifest_path)
    aggregate_hash = sha256_file(aggregate_path)
    if manifest_hash != REFERENCE_MANIFEST_SHA256:
        raise ValueError(f"FORECAST_INPUT_BLOCKED: manifest SHA-256 mismatch ({manifest_hash})")
    if aggregate_hash != REFERENCE_AGGREGATE_SHA256:
        raise ValueError(f"FORECAST_INPUT_BLOCKED: paired aggregate SHA-256 mismatch ({aggregate_hash})")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPLETE" or str(manifest.get("run_id")) != REFERENCE_RUN_ID:
        raise ValueError("FORECAST_INPUT_BLOCKED: reference is not accepted Run #994")
    if manifest.get("commit") != REFERENCE_COMMIT:
        raise ValueError("FORECAST_INPUT_BLOCKED: source commit mismatch")
    records = manifest.get("prediction_panels", [])
    if len(records) != 10:
        raise ValueError(f"FORECAST_INPUT_BLOCKED: expected 10 panels, got {len(records)}")
    seen, row_count = set(), 0
    panel_digests = {}
    for record in records:
        cell = (str(record["layer"]), int(record["horizon"]))
        if cell[0] not in LAYERS or cell[1] not in LAYERS[cell[0]] or cell in seen:
            raise ValueError(f"FORECAST_INPUT_BLOCKED: invalid/duplicate panel cell {cell}")
        seen.add(cell)
        panel_path = _panel_path(reference_root, record)
        if not panel_path.is_file():
            raise ValueError(f"FORECAST_INPUT_BLOCKED: panel missing: {panel_path.name}")
        panel_digest = sha256_file(panel_path)
        if panel_digest != record.get("sha256"):
            raise ValueError(f"FORECAST_INPUT_BLOCKED: panel SHA mismatch: {panel_path.name}")
        panel = pd.read_parquet(panel_path)
        required = {
            "layer", "horizon", "source_row_index", "decision_timestamp",
            "label_direction", "future_return", "block_index", *METHODS,
        }
        missing = required - set(panel.columns)
        if missing:
            raise ValueError(f"FORECAST_INPUT_BLOCKED: {panel_path.name} missing {sorted(missing)}")
        if len(panel) != int(record["rows"]):
            raise ValueError(f"FORECAST_INPUT_BLOCKED: panel row count mismatch: {panel_path.name}")
        if panel["source_row_index"].tolist() != list(range(len(panel))):
            raise ValueError(f"FORECAST_INPUT_BLOCKED: source row sequence invalid: {panel_path.name}")
        if (panel["layer"].astype(str) != cell[0]).any() or (panel["horizon"].astype(int) != cell[1]).any():
            raise ValueError(f"FORECAST_INPUT_BLOCKED: mixed panel identity: {panel_path.name}")
        timestamps = pd.to_datetime(panel["decision_timestamp"], utc=(cell[0] == "intraday"), errors="raise")
        if not timestamps.is_monotonic_increasing or timestamps.duplicated().any():
            raise ValueError(f"FORECAST_INPUT_BLOCKED: non-monotone/duplicate timestamps: {panel_path.name}")
        for method in METHODS:
            values = pd.to_numeric(panel[method], errors="coerce")
            if bool((values.notna() & ((values < 0) | (values > 1))).any()):
                raise ValueError(f"FORECAST_INPUT_BLOCKED: probability outside [0,1]: {panel_path.name}/{method}")
        panel_digests[f"{cell[0]}_H{cell[1]}"] = panel_digest
        row_count += len(panel)
    if len(seen) != 10 or row_count != EXPECTED_PANEL_ROWS:
        raise ValueError(f"FORECAST_INPUT_BLOCKED: expected 10 cells/50,555 rows, got {len(seen)}/{row_count}")
    return {
        "status": "PASS",
        "reference_run_id": REFERENCE_RUN_ID,
        "reference_commit": REFERENCE_COMMIT,
        "reference_artifact_sha256": REFERENCE_ARTIFACT_SHA256,
        "reference_manifest_sha256": manifest_hash,
        "aggregate_sha256": aggregate_hash,
        "panel_count": len(seen),
        "panel_rows_total": row_count,
        "panel_sha256": panel_digests,
        "forecast_refitted": False,
    }

def preflight_composite_csv_gz(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"COMPOSITE_PREFLIGHT_BLOCKED: file missing: {path}")
    # gzip container metadata (notably mtime) can differ when the same
    # 61 verified monthly gzip parts are re-merged. The immutable content hash
    # and all encrypted-part hashes are controlling; record container hash match
    # but do not reject a semantically identical decoded CSV on gzip-header bytes.
    archive_hash = sha256_file(path)
    container_hash_matches_expected = archive_hash == COMPOSITE_GZIP_SHA256
    uncompressed_hash = hashlib.sha256()
    uncompressed_bytes = 0
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            uncompressed_hash.update(block)
            uncompressed_bytes += len(block)
    decoded_hash = uncompressed_hash.hexdigest()
    if decoded_hash != COMPOSITE_CANONICAL_SHA256:
        raise ValueError(f"COMPOSITE_PREFLIGHT_BLOCKED: decoded SHA-256 mismatch ({decoded_hash})")

    row_types: Counter[str] = Counter()
    blanks: Counter[str] = Counter()
    width_errors = 0
    rows = 0
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if header is None or len(header) != COMPOSITE_COLUMNS or len(header) != len(set(header)):
            raise ValueError("COMPOSITE_PREFLIGHT_BLOCKED: header count/schema invalid")
        indexes = {name: i for i, name in enumerate(header)}
        if not {"row_type", "timestamp_epoch", "source_request_id", "option_type"}.issubset(indexes):
            raise ValueError("COMPOSITE_PREFLIGHT_BLOCKED: canonical key fields absent")
        for row in reader:
            rows += 1
            if len(row) != len(header):
                width_errors += 1
                continue
            row_kind = row[indexes["row_type"]].strip().upper()
            row_types[row_kind or "(blank)"] += 1
            for field in KEY_FEATURES:
                if field in indexes and not row[indexes[field]].strip():
                    blanks[field] += 1
    if rows != COMPOSITE_ROWS:
        raise ValueError(f"COMPOSITE_PREFLIGHT_BLOCKED: expected {COMPOSITE_ROWS} rows, got {rows}")
    if width_errors:
        raise ValueError(f"COMPOSITE_PREFLIGHT_BLOCKED: {width_errors} row-width errors")
    if dict(row_types) != ROW_COUNTS:
        raise ValueError(f"COMPOSITE_PREFLIGHT_BLOCKED: row-type counts differ: {dict(row_types)}")
    missing_panel_contract_fields = [field for field in ("lot_size", "tick_size") if field not in indexes]
    source_fields = [field for field in ("expiry_date", "expiry_mapping_source") if field not in indexes]
    return {
        "status": "PASS_STRUCTURAL_HASHES",
        "archive_sha256": archive_hash,
        "container_hash_matches_expected": container_hash_matches_expected,
        "container_hash_note": "Compressed gzip hash is recorded only; the exact canonical decoded CSV hash is required because gzip metadata may change when the pinned monthly parts are re-merged.",
        "canonical_csv_sha256": decoded_hash,
        "data_rows": rows,
        "columns": len(header),
        "rows_by_type": dict(row_types),
        "row_width_errors": width_errors,
        "blank_required_field_counts": dict(blanks),
        "critical_data_gap": {
            "lot_size_column_missing": "lot_size" not in indexes,
            "tick_size_column_missing": "tick_size" not in indexes,
            "expiry_fields_missing": bool(source_fields),
            "point_in_time_contract_master_present": False,
            "historical_bid_ask_coverage_proven": False,
            "strict_fixed_contract_execution_ready": False,
            "reason": "Composite includes rolling-option observations and derived expiry metadata; full PIT contract master/lot-size/tick/quote history still requires a separate gate.",
        },
        "empirical_option_execution_authorized": False,
    }

def build_input_gate_matrix() -> list[dict]:
    rows = []
    for config in build_registered_grid():
        rows.append({
            **config,
            "status": "INELIGIBLE",
            "reason": "POINT_IN_TIME_FIXED_CONTRACT_PANEL_NOT_YET_APPROVED",
            "evidence_class": "DATA_READINESS_GATE_ONLY",
            "pnl_generated": False,
        })
    return rows

def self_test() -> dict:
    # This code path intentionally does not inspect any external file or market data.
    grid = build_registered_grid()
    assert len(grid) == 4_800
    assert engine.direction_from_probability(0.45, "P10") is None
    assert engine.direction_from_probability(0.50, "P10") is None
    assert engine.direction_from_probability(0.55, "P10") is None
    assert engine.direction_from_probability(0.4499, "P10") == "PE"
    assert engine.direction_from_probability(0.5501, "P10") == "CE"
    spread = engine.proxy_spread_component(100.0, 0.05, "C1")
    assert math.isclose(spread, 1.0, rel_tol=0.0, abs_tol=1e-12)
    return {
        "status": "PASS",
        "evidence_class": "SYNTHETIC_SELF_TEST_ONLY",
        "registered_forecast_cells": 100,
        "registered_parent_configurations": len(grid),
        "cost_scenarios": list(engine.SCENARIOS),
        "scenario_summary_rows_expected": len(grid) * len(engine.SCENARIOS),
        "p10_abstention": {"lower": 0.45, "upper": 0.55, "inclusive": True},
        "forecast_refitted": False,
        "market_data_opened": False,
        "empirical_pnl_generated": False,
    }

def write_preflight_report(output_dir: Path, forecast: dict, composite: dict | None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    grid = build_input_gate_matrix()
    grid_path = output_dir / "phase8_input_gate_matrix.csv"
    pd.DataFrame(grid).to_csv(grid_path, index=False)
    result = {
        "schema_version": 1,
        "status": "FORECAST_PASS_OPTION_DATA_GATE_BLOCKED",
        "forecast_integrity": forecast,
        "composite_preflight": composite or {
            "status": "NOT_RUN",
            "reason": "No local pinned composite path supplied; runner does not download market data.",
        },
        "registered_forecast_cells": 100,
        "registered_parent_configurations": 4_800,
        "scenario_count": 4,
        "scenario_summary_rows_expected": 19_200,
        "input_gate_matrix_rows": len(grid),
        "input_gate_matrix_status_counts": {"INELIGIBLE": len(grid)},
        "strict_fixed_contract_execution_ready": False,
        "empirical_option_execution_authorized": False,
        "empirical_pnl_generated": False,
        "strategy_promotion_authorized": False,
        "input_gate_matrix_sha256": sha256_file(grid_path),
    }
    report_path = output_dir / "phase8_runner_preflight.json"
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Phase 8 no-refit option research runner and data gate.")
    parser.add_argument("--self-test", action="store_true", help="pure synthetic gate test; cannot open market data")
    parser.add_argument("--mode", choices=("preflight", "empirical"), default="preflight")
    parser.add_argument("--forecast-root", type=Path, default=Path("data/cache/reference/phase7_run994/unpacked"))
    parser.add_argument("--composite-csv-gz", type=Path, default=None, help="existing exact pinned composite; no download is performed")
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/phase8/runner"))
    parser.add_argument("--authorization-file", type=Path, default=Path("research/phase8/PHASE8_EMPIRICAL_AUTHORIZATION.json"))
    parser.add_argument("--consumed-marker", type=Path, default=Path("research/phase8/PHASE8_EMPIRICAL_CONSUMED_MARKER.json"))
    args = parser.parse_args(argv)

    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    if args.mode == "empirical":
        # Fail before opening the option data file: the separate data gate must
        # supply a prepared fixed-contract manifest and one-use reviewer record.
        if not args.authorization_file.is_file() or not args.consumed_marker.is_file():
            raise SystemExit("EMPIRICAL_EXECUTION_BLOCKED: exact one-use authorization and consumed marker are absent")
        raise SystemExit("EMPIRICAL_EXECUTION_BLOCKED: point-in-time fixed-contract panel and reviewed executor are not yet authorized")

    forecast = validate_saved_forecasts(args.forecast_root)
    composite = preflight_composite_csv_gz(args.composite_csv_gz) if args.composite_csv_gz else None
    report = write_preflight_report(args.output_dir, forecast, composite)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
