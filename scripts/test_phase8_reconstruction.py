# Phase 8 fresh hosted trigger after tester-approved Run #783 hash-integrity correction.
# Phase 8 fresh hosted trigger after tester-approved Run 746 reconstruction harness correction.
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
    code = compile(tree, str(SRC), "exec")
    exec(code, ns, ns)
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


def test_git_blob_sha_matches_git_empty_blob():
    ns = exec_source_namespace()
    with tempfile.NamedTemporaryFile(delete=False) as fh:
        path = Path(fh.name)
    try:
        path.write_bytes(b"")
        assert ns["git_blob_sha"](path) == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
    finally:
        path.unlink(missing_ok=True)


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



def test_reconstruction_pins_numerical_threadpool():
    src = load_source()
    assert "from threadpoolctl import threadpool_limits" in src
    assert "with threadpool_limits(limits=1):" in src
    workflow = (ROOT / ".github" / "workflows" / "phase-08-long-option.yml").read_text(encoding="utf-8")
    reconstruct = workflow.split("  reconstruct:", 1)[1].split("  empirical-authorization:", 1)[0]
    assert 'python-version: "3.11.16"' in reconstruct
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        assert f'{key}: "1"' in reconstruct


def test_threadpool_limit_repeats_logistic_predictions():
    from sklearn.linear_model import LogisticRegression
    from threadpoolctl import threadpool_limits
    rng = np.random.default_rng(42)
    X = rng.normal(size=(600, 8))
    y = (X[:, 0] - 0.4 * X[:, 1] + rng.normal(scale=0.5, size=600) > 0).astype(int)
    X_train, y_train, X_test = X[:500], y[:500], X[500:]
    with threadpool_limits(limits=1):
        a = LogisticRegression(C=1.0, solver="lbfgs", max_iter=500, random_state=42).fit(X_train, y_train).predict_proba(X_test)[:, 1]
        b = LogisticRegression(C=1.0, solver="lbfgs", max_iter=500, random_state=42).fit(X_train, y_train).predict_proba(X_test)[:, 1]
    np.testing.assert_array_equal(a, b)


def test_mismatch_diagnostic_preserves_row_level_brier_terms():
    ns = exec_source_namespace()
    original_blocks_for = ns["p7"].blocks_for
    ns["p7"].blocks_for = lambda df, intraday: [np.array([0, 1])]
    try:
        built = {
            "y": np.array([1.0, 0.0]),
            "predictions": {f"P{i:02d}": np.array([0.8, 0.3]) for i in range(1, 11)},
            "timestamps": pd.to_datetime(["2026-01-01 09:30:00", "2026-01-01 10:30:00"]),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = ns["write_mismatch_diagnostic"](
                "intraday", 60, built, pd.DataFrame({"unused": [0, 1]}),
                True, Path(tmp), ["root.P07.chronological_blocks[0].brier: mismatch"]
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload["status"] == "FAIL"
            assert payload["diagnostic_only"] is True
            block = payload["p07_failed_blocks"][0]
            assert block["n"] == 2
            assert block["rows"][0]["label_direction"] == 1
            assert block["rows"][0]["p07_clipped"] == 0.8
            np.testing.assert_allclose(block["rows"][0]["squared_error"], (0.8 - 1.0) ** 2)
            assert np.isclose(block["brier_from_row_terms"], ((0.8 - 1.0) ** 2 + (0.3 - 0.0) ** 2) / 2)
    finally:
        ns["p7"].blocks_for = original_blocks_for


def test_reconstruction_writes_panel_before_fail_closed_exit():
    src = load_source()
    compare = src.index("failures = recursive_compare(expected, actual)")
    panel = src.index("frame = canonical_prediction_rows(layer, H, built)", compare)
    failure = src.index('if failures:', panel)
    exit_point = src.index('raise SystemExit(', failure)
    assert compare < panel < failure < exit_point
    assert "write_mismatch_diagnostic(" in src
    assert "tolerance_abs\": TOL" in src

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
    test_git_blob_sha_matches_git_empty_blob()
    test_canonical_rows_do_not_drop_future_audit_fields()
    test_reconstruction_pins_numerical_threadpool()
    test_threadpool_limit_repeats_logistic_predictions()
    test_mismatch_diagnostic_preserves_row_level_brier_terms()
    test_reconstruction_writes_panel_before_fail_closed_exit()
    test_manifest_is_json()
    print("Phase 8 reconstruction regression PASS")
