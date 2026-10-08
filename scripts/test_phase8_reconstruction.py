from __future__ import annotations

import ast
import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts" / "reconstruct_phase7_predictions.py"


def load_source():
    return SRC.read_text(encoding="utf-8")


def test_source_freezes_input_commit():
    src = load_source()
    assert "4f1d695f291ed32996c07f01710afcecc6f2a540" in src
    assert "phase7_run654" in src


def test_source_blocks_result_driven_changes():
    src = load_source()
    assert "empirical_option_execution_authorized" in src
    assert 'raise SystemExit("RECONSTRUCTION_ERROR: frozen input manifest must not authorize option execution")' in src


def exec_source_namespace():
    ns = {"__file__": str(SRC), "__name__": "phase8_reconstruction_test_namespace"}
    tree = ast.parse(load_source())
    exec(compile(tree, str(SRC), "exec"), ns)
    return ns


def test_exec_harness_sets_file_context():
    ns = exec_source_namespace()
    assert Path(ns["__file__"]).resolve() == SRC.resolve()
    assert ns["__name__"] == "phase8_reconstruction_test_namespace"


def test_recursive_compare_tolerance():
    ns = exec_source_namespace()
    tree = ast.parse(load_source())
    assert "__file__" in ns
    wanted = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert {"recursive_compare", "build_candidates", "canonical_prediction_rows"} <= wanted

    cmp = ns["recursive_compare"]
    assert cmp({"x": 1.0}, {"x": 1.0 + 5e-10}) == []
    assert cmp({"x": 1.0}, {"x": 1.0 + 2e-9})


def test_canonical_rows_do_not_drop_future_audit_fields():
    ns = exec_source_namespace()
    build = {
        "timestamps": pd.to_datetime(["2026-01-01 09:30:00", "2026-01-01 10:30:00"]),
        "y": np.array([1.0, 0.0]),
        "future": np.array([0.01, -0.02]),
        "predictions": {f"P{i:02d}": np.array([0.55, 0.45]) for i in range(1, 11)},
    }
    df = ns["canonical_prediction_rows"]("daily", 1, build)
    assert len(df) == 2
    assert {"decision_timestamp","future_return","P01","P10"} <= set(df.columns)
    assert df["decision_timestamp"].notna().all()


def test_manifest_is_json():
    data = json.loads((ROOT / "research" / "phase8" / "PHASE8_FROZEN_INPUT_MANIFEST.json").read_text())
    assert data["artifact_id"] == 11551679532
    assert data["artifact_sha256"] == "c554a59f1fcf6630c4ddb12282fd047e988d9fbc39ec16c2b766453416137b7a"
    assert data["reconstruction_tolerance_abs"] == 1e-9


if __name__ == "__main__":
    test_source_freezes_input_commit()
    test_source_blocks_result_driven_changes()
    test_exec_harness_sets_file_context()
    test_recursive_compare_tolerance()
    test_canonical_rows_do_not_drop_future_audit_fields()
    test_manifest_is_json()
    print("Phase 8 reconstruction regression PASS")
