from __future__ import annotations

import gzip
import json
from pathlib import Path
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_phase8_long_option as runner


def test_registered_grid_is_exact_and_preserves_every_cell():
    forecast_cells = runner.build_forecast_cells()
    configs = runner.build_registered_grid()
    assert len(forecast_cells) == 100
    assert len(configs) == 4800
    assert len({row["config_id"] for row in configs}) == 4800
    assert {row["method"] for row in configs} == {f"P{i:02d}" for i in range(1, 11)}
    assert {row["dte_bucket"] for row in configs} == set(runner.engine.DTE_BUCKETS)
    assert {row["exit_policy"] for row in configs} == set(runner.engine.EXIT_POLICIES)
    matrix = runner.build_input_gate_matrix()
    assert len(matrix) == 4800
    assert {row["status"] for row in matrix} == {"INELIGIBLE"}
    assert all(row["pnl_generated"] is False for row in matrix)


def test_self_test_is_synthetic_and_does_not_open_files():
    result = runner.self_test()
    assert result["status"] == "PASS"
    assert result["evidence_class"] == "SYNTHETIC_SELF_TEST_ONLY"
    assert result["market_data_opened"] is False
    assert result["empirical_pnl_generated"] is False
    assert result["registered_parent_configurations"] == 4800
    assert result["scenario_summary_rows_expected"] == 19200


def test_p10_abstention_boundaries_match_run994():
    assert runner.engine.direction_from_probability(0.4499, "P10") == "PE"
    assert runner.engine.direction_from_probability(0.45, "P10") is None
    assert runner.engine.direction_from_probability(0.50, "P10") is None
    assert runner.engine.direction_from_probability(0.55, "P10") is None
    assert runner.engine.direction_from_probability(0.5501, "P10") == "CE"


def test_composite_preflight_fails_closed_on_nonmatching_cached_data():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "not_the_pinned_composite.csv.gz"
        with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
            handle.write("row_type,timestamp_epoch\nOPTION,1\n")
        try:
            runner.preflight_composite_csv_gz(path)
        except ValueError as exc:
            assert "compressed SHA-256 mismatch" in str(exc)
        else:
            raise AssertionError("non-pinned composite must not be accepted")


def test_empirical_mode_fails_before_reading_option_data():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "no-data.csv.gz"
        args = [
            "--mode", "empirical",
            "--composite-csv-gz", str(path),
            "--authorization-file", str(Path(td) / "no-auth.json"),
            "--consumed-marker", str(Path(td) / "no-marker.json"),
        ]
        try:
            runner.main(args)
        except SystemExit as exc:
            assert "authorization and consumed marker are absent" in str(exc)
        else:
            raise AssertionError("empirical mode must fail closed without one-use authorization")


if __name__ == "__main__":
    test_registered_grid_is_exact_and_preserves_every_cell()
    test_self_test_is_synthetic_and_does_not_open_files()
    test_p10_abstention_boundaries_match_run994()
    test_composite_preflight_fails_closed_on_nonmatching_cached_data()
    test_empirical_mode_fails_before_reading_option_data()
    print("Phase 8 runner contract regression PASS")
