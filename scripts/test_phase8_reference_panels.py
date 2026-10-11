from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_phase7_ensemble as p7
import validate_phase7_reference_panels as validator
import validate_phase8_forecast_panel as phase8_panel_validator
from validate_phase7_reference_panels import compare_panel
validator.p7 = p7

def run994_block_diagnostics(y, p, blocks, eligibility_mask=None):
    """Test adapter matching the exact Run #994 block-diagnostic signature."""
    out = []
    eligibility = None if eligibility_mask is None else np.asarray(eligibility_mask, dtype=bool)
    for rows in blocks:
        mask = np.isfinite(y[rows]) & np.isfinite(p[rows])
        if eligibility is not None:
            mask &= eligibility[rows]
        if not mask.any():
            continue
        yy = y[rows][mask].astype(int)
        pp = np.clip(p[rows][mask], 1e-6, 1 - 1e-6)
        pred = (pp >= 0.5).astype(int)
        out.append({
            "n": int(len(yy)),
            "accuracy": float(np.mean(pred == yy)),
            "balanced_accuracy": float(p7.p6.balanced_accuracy_score(yy, pred)),
            "brier": float(np.mean((pp - yy) ** 2)),
        })
    return out


# Synthetic fixtures deliberately emulate the frozen Run #994 abstention/mask
# contract rather than the older Phase 8 working-tree copy of the Phase 7 code.
p7.ABSTAIN = {**p7.ABSTAIN, "P10": (0.45, 0.55)}
p7.block_diagnostics = run994_block_diagnostics


def test_saved_panel_metrics_reconcile_without_model_refit():
    n = 240
    y = (np.arange(n) % 3 != 0).astype(float)
    future = np.where(y == 1, 0.01, -0.01)
    ts = pd.date_range("2024-01-01", periods=n, freq="D")
    blocks = [np.arange(i, min(i + 20, n)) for i in range(0, n, 20)]
    candidates = {
        f"P{i:02d}": np.clip(0.35 + 0.001 * (np.arange(n) % 100) + i * 0.003, 0.01, 0.99)
        for i in range(1, 11)
    }
    frame = pd.DataFrame({
        "layer": "daily", "horizon": 1, "source_row_index": np.arange(n),
        "decision_timestamp": ts, "label_direction": y, "future_return": future,
        "block_index": np.repeat(np.arange(len(blocks)), [len(x) for x in blocks]),
    })
    for name, values in candidates.items():
        frame[name] = values

    block_len = 20
    baseline = p7.causal_baseline(y, blocks)
    expected = {}
    for name, pred in candidates.items():
        mask = None
        extra = {}
        if name in p7.ABSTAIN:
            lo, hi = p7.ABSTAIN[name]
            finite = np.isfinite(pred)
            mask = finite & ~((pred >= lo) & (pred <= hi))
            extra = {
                "coverage": float(mask.sum() / finite.sum()) if finite.sum() else 0.0,
                "trade_n": int(mask.sum()),
                "evaluable_n": int(finite.sum()),
            }
        result = p7.p6.metrics(y, pred, future, block_len, extra=extra, mask=mask)
        result["chronological_blocks"] = p7.block_diagnostics(y, pred, blocks, mask)
        expected[name] = result
    expected["_FAMILY_TEST"] = p7.family_bootstrap(y, candidates, baseline, block_len)
    outcome = compare_panel(frame, expected, intraday=False)
    assert outcome == {"rows": n, "blocks": len(blocks), "metric_comparison": "PASS"}


def test_code_hashes_are_checked_against_git_commit():
    import hashlib
    import subprocess

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    paths = [
        "scripts/run_phase7_ensemble.py", "scripts/run_phase6_novel.py",
        "scripts/run_phase3_daily_baselines.py", "scripts/run_phase3_intraday_baselines.py",
    ]
    code_files = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    validator.verify_code_hashes({"commit": commit, "code_files": code_files})
    loaded = validator.load_reference_phase7_module(commit)
    assert loaded.__file__ == str(ROOT / "scripts" / "run_phase7_ensemble.py")
    assert callable(loaded.family_bootstrap)
    tampered = dict(code_files)
    tampered[paths[0]] = "0" * 64
    try:
        validator.verify_code_hashes({"commit": commit, "code_files": tampered})
    except SystemExit as exc:
        assert "source code SHA-256 mismatch" in str(exc)
    else:
        raise AssertionError("tampered code hash was not rejected")


def test_full_artifact_directory_validation():
    import hashlib
    import json
    import tempfile

    n = 240
    original_root = validator.ROOT
    original_family = p7.family_bootstrap
    original_load_daily = p7.p6.load_daily
    original_load_intraday = p7.p6.load_intraday
    original_verify = validator.verify_code_hashes
    original_source_alignment = validator.verify_panel_source_alignment
    original_loader = validator.load_reference_phase7_module
    original_validator_p7 = validator.p7
    original_panel_root = phase8_panel_validator.ROOT
    original_panel_report = phase8_panel_validator.REPORT
    original_panel_manifest = phase8_panel_validator.MANIFEST
    original_argv = sys.argv[:]
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = root / "artifact"
            refdir = artifact / "phase7_reference"
            refdir.mkdir(parents=True)
            source_daily = root / "data/cache/raw/phase3/nifty50_daily.csv"
            source_intra = root / "data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet"
            source_daily.parent.mkdir(parents=True, exist_ok=True)
            source_intra.parent.mkdir(parents=True, exist_ok=True)
            source_daily.write_text("date,close\n2024-01-01,100\n", encoding="utf-8")
            source_intra.write_bytes(b"synthetic-intraday-source")
            validator.ROOT = root
            validator.verify_code_hashes = lambda manifest: None
            validator.verify_panel_source_alignment = lambda frame, layer, horizon, daily, intraday: {
                "layer": layer,
                "horizon": int(horizon),
                "label_direction_exact": True,
                "decision_timestamp_exact": True,
                "future_return": {
                    "max_ulps_allowed": 2,
                    "exact_mismatch_count": 0,
                    "accepted_within_ulps_count": 0,
                    "out_of_policy_count": 0,
                    "max_abs_diff": None,
                    "max_ulp_distance": None,
                    "first_non_exact_pairs": [],
                },
            }
            validator.load_reference_phase7_module = lambda commit: p7
            validator.p7 = p7
            p7.p6.load_daily = lambda: pd.DataFrame()
            p7.p6.load_intraday = lambda: pd.DataFrame()
            p7.family_bootstrap = lambda *args, **kwargs: {"observed": 0.001, "p_value": 0.5}

            aggregate = {"protocol": "research/phase7/PHASE7_METHOD_SPEC.md", "seed": 42}
            panel_records = []
            for layer, intraday, horizons, block_len in [
                ("daily", False, [1, 2, 3, 5, 10], 20),
                ("intraday", True, [5, 15, 30, 60, 120], 60),
            ]:
                layer_result = {"rows": n, "horizons": {}}
                for H in horizons:
                    y = (np.arange(n) % 3 != 0).astype(float)
                    future = np.where(y == 1, 0.01, -0.01)
                    if intraday:
                        ts = pd.date_range("2024-01-01T00:00:00Z", periods=n, freq="h")
                    else:
                        ts = pd.date_range("2024-01-01", periods=n, freq="D")
                    blocks = [np.arange(i, min(i + block_len, n)) for i in range(0, n, block_len)]
                    block_index = np.repeat(np.arange(len(blocks)), [len(b) for b in blocks])
                    candidates = {
                        f"P{i:02d}": np.clip(0.36 + 0.001 * (np.arange(n) % 100) + i * 0.003, 0.01, 0.99)
                        for i in range(1, 11)
                    }
                    frame = pd.DataFrame({
                        "layer": layer, "horizon": H, "source_row_index": np.arange(n),
                        "decision_timestamp": ts, "label_direction": y, "future_return": future,
                        "block_index": block_index,
                    })
                    for name, pred in candidates.items():
                        frame[name] = pred
                    frame["source_run_id"] = "test-run"
                    frame["source_commit"] = "a" * 40
                    panel_path = refdir / f"phase7_predictions_{layer}_H{H}.parquet"
                    frame.to_parquet(panel_path, index=False)
                    panel_records.append({
                        "path": f"data/reports/phase7_reference/{panel_path.name}",
                        "sha256": hashlib.sha256(panel_path.read_bytes()).hexdigest(),
                        "rows": n, "layer": layer, "horizon": H, "columns": list(frame.columns),
                    })

                    baseline = p7.causal_baseline(y, blocks)
                    results = {}
                    for name, pred in candidates.items():
                        mask = None
                        extra = {}
                        if name in p7.ABSTAIN:
                            lo, hi = p7.ABSTAIN[name]
                            finite = np.isfinite(pred)
                            mask = finite & ~((pred >= lo) & (pred <= hi))
                            extra = {
                                "coverage": float(mask.sum() / finite.sum()) if finite.sum() else 0.0,
                                "trade_n": int(mask.sum()),
                                "evaluable_n": int(finite.sum()),
                            }
                        metric = p7.p6.metrics(y, pred, future, block_len, extra=extra, mask=mask)
                        metric["chronological_blocks"] = p7.block_diagnostics(y, pred, blocks, mask)
                        if name in ("P08", "P09", "P10"):
                            metric["regime_diagnostics"] = []
                            metric["regime_fallback_count"] = 0
                        results[name] = metric
                    results["_FAMILY_TEST"] = p7.family_bootstrap(y, candidates, baseline, block_len)
                    layer_result["horizons"][str(H)] = results
                aggregate[layer] = layer_result

            aggregate_path = artifact / "phase7_ensemble_results.json"
            aggregate_path.write_text(json.dumps(aggregate, indent=2, allow_nan=False), encoding="utf-8")
            manifest = {
                "schema_version": 1, "status": "COMPLETE", "run_id": "test-run",
                "commit": "a" * 40, "protocol": "research/phase7/PHASE7_METHOD_SPEC.md", "seed": 42,
                "aggregate_result": {
                    "path": "data/reports/phase7_ensemble_results.json",
                    "sha256": hashlib.sha256(aggregate_path.read_bytes()).hexdigest(),
                },
                "prediction_panels": panel_records,
                "source_files": {
                    "daily_csv": {"path": "data/cache/raw/phase3/nifty50_daily.csv", "sha256": hashlib.sha256(source_daily.read_bytes()).hexdigest()},
                    "intraday_parquet": {"path": "data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet", "sha256": hashlib.sha256(source_intra.read_bytes()).hexdigest()},
                },
                "code_files": {
                    "scripts/run_phase7_ensemble.py": "1" * 64,
                    "scripts/run_phase6_novel.py": "2" * 64,
                    "scripts/run_phase3_daily_baselines.py": "3" * 64,
                    "scripts/run_phase3_intraday_baselines.py": "4" * 64,
                },
                "runtime": {
                    "python": "3.11", "platform": "test", "machine": "test", "numpy": np.__version__,
                    "pandas": pd.__version__, "scikit_learn": "test", "scipy": "test",
                    "pyarrow": "test", "threadpoolctl": "test", "threadpools": [],
                },
            }
            (refdir / "phase7_reference_manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
            output = root / "data/reports/phase8"
            sys.argv = ["validate_phase7_reference_panels.py", "--artifact-dir", str(artifact), "--output-dir", str(output)]
            validator.main()
            result = json.loads((output / "phase8_forecast_reconstruction_manifest.json").read_text())
            assert result["status"] == "PASS"
            assert result["total_cells"] == 10
            assert result["all_cells_reproduced"] is True
            assert len(result["prediction_files"]) == 10
            assert result["cells"][0]["source_alignment"]["future_return"]["max_ulps_allowed"] == 2
            assert result["cells"][0]["source_alignment"]["future_return"]["out_of_policy_count"] == 0
            assert len(list(output.glob("phase7_predictions_*.parquet"))) == 10
            phase8_panel_validator.ROOT = root
            phase8_panel_validator.REPORT = output
            phase8_panel_validator.MANIFEST = output / "phase8_forecast_reconstruction_manifest.json"
            phase8_panel_validator.main()
            assert (output / "phase8_forecast_panel_validation.json").is_file()
    finally:
        validator.ROOT = original_root
        validator.verify_code_hashes = original_verify
        validator.verify_panel_source_alignment = original_source_alignment
        validator.load_reference_phase7_module = original_loader
        validator.p7 = original_validator_p7
        phase8_panel_validator.ROOT = original_panel_root
        phase8_panel_validator.REPORT = original_panel_report
        phase8_panel_validator.MANIFEST = original_panel_manifest
        p7.family_bootstrap = original_family
        p7.p6.load_daily = original_load_daily
        p7.p6.load_intraday = original_load_intraday
        sys.argv = original_argv


def test_source_alignment_checks_daily_and_intraday_labels():
    daily_ts = pd.date_range("2025-01-01", periods=30, freq="D")
    daily_source = pd.DataFrame({
        "date": daily_ts,
        "close": 100.0 * np.exp(np.arange(30) * 0.001 + np.sin(np.arange(30)) * 0.002),
    })
    y, future = p7.p6.make_label(daily_source, 2)
    daily_panel = pd.DataFrame({
        "decision_timestamp": daily_ts,
        "label_direction": y.to_numpy(dtype=float),
        "future_return": future.to_numpy(dtype=float),
    })
    daily_alignment = validator.verify_panel_source_alignment(
        daily_panel, "daily", 2, daily_source, pd.DataFrame()
    )
    assert daily_alignment["label_direction_exact"] is True
    assert daily_alignment["decision_timestamp_exact"] is True
    assert daily_alignment["future_return"]["max_ulps_allowed"] == 2
    assert daily_alignment["future_return"]["out_of_policy_count"] == 0
    bad_daily = daily_panel.copy()
    bad_daily.loc[0, "label_direction"] = 1.0 - bad_daily.loc[0, "label_direction"]
    try:
        validator.verify_panel_source_alignment(bad_daily, "daily", 2, daily_source, pd.DataFrame())
    except SystemExit as exc:
        assert "source-derived label mismatch" in str(exc)
    else:
        raise AssertionError("mutated daily label was not rejected")

    intra_ts = pd.date_range("2025-01-02 09:30:00", periods=391, freq="min", tz="UTC")
    spots = 20000.0 * np.exp(np.arange(len(intra_ts)) * 0.00001 + np.sin(np.arange(len(intra_ts)) / 7) * 0.0001)
    intraday_source = pd.DataFrame({
        "timestamp": intra_ts,
        "minute_of_day": intra_ts.hour * 60 + intra_ts.minute,
        "date": intra_ts.date,
        "spot": spots,
    })
    grid = ((intraday_source["minute_of_day"] >= 570)
            & (intraday_source["minute_of_day"] <= 930)
            & (((intraday_source["minute_of_day"] - 570) % 60) == 0))
    idx = np.flatnonzero(grid.to_numpy())
    yi, fi, _ = p7.p6.intraday_labels(intraday_source["timestamp"], intraday_source["spot"], 5)
    intra_panel = pd.DataFrame({
        "decision_timestamp": intraday_source["timestamp"].iloc[idx].reset_index(drop=True),
        "label_direction": yi.iloc[idx].to_numpy(dtype=float),
        "future_return": fi.iloc[idx].to_numpy(dtype=float),
    })
    intra_alignment = validator.verify_panel_source_alignment(
        intra_panel, "intraday", 5, daily_source, intraday_source
    )
    assert intra_alignment["label_direction_exact"] is True
    assert intra_alignment["decision_timestamp_exact"] is True
    assert intra_alignment["future_return"]["out_of_policy_count"] == 0
    bad_intra = intra_panel.copy()
    bad_intra.loc[0, "future_return"] += 0.01
    try:
        validator.verify_panel_source_alignment(bad_intra, "intraday", 5, daily_source, intraday_source)
    except SystemExit as exc:
        assert "source-derived future-return mismatch" in str(exc)
        assert '"out_of_policy_count":1' in str(exc)
        assert '"max_abs_diff":0.01' in str(exc)
    else:
        raise AssertionError("mutated intraday future return was not rejected")


def test_float64_source_alignment_ulp_policy():
    compare = validator.compare_float64_within_ulps
    base = np.float64(1.0)
    one_ulp = np.nextafter(base, np.inf)
    two_ulps = np.nextafter(one_ulp, np.inf)
    three_ulps = np.nextafter(two_ulps, np.inf)

    for value, expected_distance in ((one_ulp, 1), (two_ulps, 2)):
        passed, diagnostic = compare([base], [value], max_ulps=2)
        assert passed is True, diagnostic
        assert diagnostic["exact_mismatch_count"] == 1
        assert diagnostic["accepted_within_ulps_count"] == 1
        assert diagnostic["out_of_policy_count"] == 0
        assert diagnostic["max_ulp_distance"] == expected_distance

    passed, diagnostic = compare([base], [three_ulps], max_ulps=2)
    assert passed is False
    assert diagnostic["out_of_policy_count"] == 1
    assert diagnostic["max_ulp_distance"] == 3
    assert diagnostic["first_non_exact_pairs"][0]["within_policy"] is False

    passed, diagnostic = compare(
        [np.nan, np.inf, -np.inf, 0.0],
        [np.nan, np.inf, -np.inf, -0.0],
        max_ulps=2,
    )
    assert passed is True, diagnostic
    assert diagnostic["exact_mismatch_count"] == 0

    for actual, expected in (
        ([np.nan], [0.0]),
        ([np.inf], [1.0]),
        ([np.inf], [-np.inf]),
        ([0.006], [-0.006]),
    ):
        passed, diagnostic = compare(actual, expected, max_ulps=2)
        assert passed is False, (actual, expected, diagnostic)
        assert diagnostic["out_of_policy_count"] == 1

    passed, diagnostic = compare([1.0, 2.0], [1.0], max_ulps=2)
    assert passed is False
    assert diagnostic["shape_mismatch"] is True

    # Daily H=1's source-derived returns are allowed only the registered two ULPs.
    daily_ts = pd.date_range("2025-01-01", periods=30, freq="D")
    daily_source = pd.DataFrame({
        "date": daily_ts,
        "close": 100.0 * np.exp(np.arange(30) * 0.001 + np.sin(np.arange(30)) * 0.002),
    })
    y, future = p7.p6.make_label(daily_source, 1)
    panel = pd.DataFrame({
        "decision_timestamp": daily_ts,
        "label_direction": y.to_numpy(dtype=float),
        "future_return": future.to_numpy(dtype=float),
    })
    row = int(np.flatnonzero(np.isfinite(panel["future_return"].to_numpy()))[0])
    original = np.float64(panel.loc[row, "future_return"])
    panel.loc[row, "future_return"] = np.nextafter(original, np.inf)
    one_ulp_alignment = validator.verify_panel_source_alignment(
        panel, "daily", 1, daily_source, pd.DataFrame()
    )
    assert one_ulp_alignment["future_return"]["exact_mismatch_count"] == 1
    assert one_ulp_alignment["future_return"]["accepted_within_ulps_count"] == 1
    assert one_ulp_alignment["future_return"]["max_ulp_distance"] == 1
    panel.loc[row, "future_return"] = np.nextafter(
        np.nextafter(np.nextafter(original, np.inf), np.inf), np.inf
    )
    try:
        validator.verify_panel_source_alignment(panel, "daily", 1, daily_source, pd.DataFrame())
    except SystemExit as exc:
        assert "source-derived future-return mismatch" in str(exc)
        assert '"max_ulp_distance":3' in str(exc)
    else:
        raise AssertionError("three-ULP daily H=1 future-return change was not rejected")


if __name__ == "__main__":
    test_saved_panel_metrics_reconcile_without_model_refit()
    test_code_hashes_are_checked_against_git_commit()
    test_source_alignment_checks_daily_and_intraday_labels()
    test_float64_source_alignment_ulp_policy()
    test_full_artifact_directory_validation()
    print("Phase 8 saved-panel validator regression PASS")
