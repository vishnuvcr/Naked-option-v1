from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import types
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
p7 = None
from reconstruct_phase7_predictions import recursive_compare, TOL

METHODS = [f"P{i:02d}" for i in range(1, 11)]
ABSTAIN = {"P05": (0.45, 0.55), "P06": (0.40, 0.60)}  # fallback only for test doubles; production uses immutable Phase 7 module
LAYERS = {"daily": (False, [1, 2, 3, 5, 10]), "intraday": (True, [5, 15, 30, 60, 120])}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_code_hashes(manifest: dict) -> None:
    commit = str(manifest.get("commit", ""))
    if not commit:
        raise SystemExit("ARTIFACT_ERROR: reference source commit missing")
    for relative_path, expected_hash in manifest.get("code_files", {}).items():
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative_path}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if result.returncode != 0:
            raise SystemExit(f"ARTIFACT_ERROR: source commit/file unavailable: {commit}:{relative_path}")
        actual_hash = hashlib.sha256(result.stdout).hexdigest()
        if actual_hash != expected_hash:
            raise SystemExit(f"ARTIFACT_ERROR: source code SHA-256 mismatch: {relative_path}")



def load_reference_phase7_module(commit: str):
    result = subprocess.run(
        ["git", "show", f"{commit}:scripts/run_phase7_ensemble.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"ARTIFACT_ERROR: cannot load Phase 7 metric implementation at {commit}")
    module_name = f"_phase7_reference_{commit[:12]}"
    module = types.ModuleType(module_name)
    module.__file__ = str(ROOT / "scripts" / "run_phase7_ensemble.py")
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        exec(compile(result.stdout, module.__file__, "exec"), module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


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



def _numeric_mismatch_diagnostic(actual: np.ndarray, expected: np.ndarray) -> str:
    """Describe exact float mismatches without changing the fail-closed comparison."""
    a = np.asarray(actual, dtype=float)
    e = np.asarray(expected, dtype=float)
    if a.shape != e.shape:
        return f"shape_actual={a.shape} shape_expected={e.shape}"
    equal = (a == e) | (np.isnan(a) & np.isnan(e))
    mismatch_idx = np.flatnonzero(~equal)
    finite_idx = mismatch_idx[np.isfinite(a[mismatch_idx]) & np.isfinite(e[mismatch_idx])]
    max_abs = float(np.max(np.abs(a[finite_idx] - e[finite_idx]))) if len(finite_idx) else None
    samples = []
    for i in mismatch_idx[:5]:
        samples.append({
            "row": int(i),
            "actual": float(a[i]) if np.isfinite(a[i]) else str(a[i]),
            "expected": float(e[i]) if np.isfinite(e[i]) else str(e[i]),
            "abs_diff": float(abs(a[i] - e[i])) if np.isfinite(a[i]) and np.isfinite(e[i]) else None,
        })
    return f"mismatch_count={len(mismatch_idx)} max_abs_diff={max_abs!r} first_mismatches={json.dumps(samples, separators=(',', ':'))}"


def compare_float64_within_ulps(actual, expected, max_ulps: int = 2) -> tuple[bool, dict]:
    """Compare float64 arrays with a strict ULP bound; never rewrite either input.

    Exact equal values (including identical infinities) and paired NaNs pass.
    Non-exact values pass only when both are finite and their IEEE-754 ordered
    representations differ by at most max_ulps. Shape changes and non-finite
    mismatches fail closed.
    """
    a = np.asarray(actual, dtype=np.float64)
    e = np.asarray(expected, dtype=np.float64)
    if a.shape != e.shape:
        return False, {
            "shape_mismatch": True,
            "actual_shape": list(a.shape),
            "expected_shape": list(e.shape),
            "max_ulps_allowed": int(max_ulps),
            "exact_mismatch_count": None,
            "accepted_within_ulps_count": 0,
            "out_of_policy_count": None,
            "max_abs_diff": None,
            "max_ulp_distance": None,
            "first_non_exact_pairs": [],
        }
    if max_ulps < 0:
        raise ValueError("max_ulps must be non-negative")

    af = a.reshape(-1)
    ef = e.reshape(-1)
    paired_nan = np.isnan(af) & np.isnan(ef)
    exact = (af == ef) | paired_nan
    finite_pair = np.isfinite(af) & np.isfinite(ef)

    # Map IEEE-754 binary64 bit patterns to monotonically ordered unsigned keys:
    # negative numbers are bitwise complemented; non-negative numbers have the
    # sign bit set. This measures actual representable-float steps, not a relative
    # or absolute tolerance. Signed zeros compare exactly equal above.
    sign_mask = np.uint64(0x8000000000000000)
    abits = af.view(np.uint64)
    ebits = ef.view(np.uint64)
    akeys = np.where((abits & sign_mask) != 0, ~abits, abits | sign_mask)
    ekeys = np.where((ebits & sign_mask) != 0, ~ebits, ebits | sign_mask)
    distances = np.maximum(akeys, ekeys) - np.minimum(akeys, ekeys)
    within = finite_pair & (distances <= np.uint64(max_ulps))
    accepted = exact | within
    rejected_idx = np.flatnonzero(~accepted)
    non_exact_idx = np.flatnonzero(~exact)
    finite_non_exact_idx = non_exact_idx[finite_pair[non_exact_idx]]
    finite_diff = np.abs(af[finite_non_exact_idx] - ef[finite_non_exact_idx])
    max_abs_diff = float(finite_diff.max()) if finite_diff.size else None
    max_ulp_distance = (
        int(distances[finite_non_exact_idx].max()) if finite_non_exact_idx.size else None
    )
    samples = []
    for i in non_exact_idx[:5]:
        is_finite_pair = bool(finite_pair[i])
        samples.append({
            "row": int(i),
            "actual": float(af[i]) if np.isfinite(af[i]) else str(af[i]),
            "expected": float(ef[i]) if np.isfinite(ef[i]) else str(ef[i]),
            "abs_diff": float(abs(af[i] - ef[i])) if is_finite_pair else None,
            "ulp_distance": int(distances[i]) if is_finite_pair else None,
            "within_policy": bool(within[i]),
        })
    diagnostics = {
        "shape_mismatch": False,
        "max_ulps_allowed": int(max_ulps),
        "exact_mismatch_count": int(len(non_exact_idx)),
        "accepted_within_ulps_count": int(np.sum((~exact) & within)),
        "out_of_policy_count": int(len(rejected_idx)),
        "max_abs_diff": max_abs_diff,
        "max_ulp_distance": max_ulp_distance,
        "first_non_exact_pairs": samples,
    }
    return len(rejected_idx) == 0, diagnostics


def verify_panel_source_alignment(frame: pd.DataFrame, layer: str, horizon: int,
                                  daily_source: pd.DataFrame, intraday_source: pd.DataFrame) -> dict:
    if layer == "daily":
        y_expected, future_expected = p7.p6.make_label(daily_source, horizon)
        expected_times = pd.to_datetime(daily_source["date"], errors="raise").reset_index(drop=True)
    elif layer == "intraday":
        grid = ((intraday_source["minute_of_day"] >= 570)
                & (intraday_source["minute_of_day"] <= 930)
                & (((intraday_source["minute_of_day"] - 570) % 60) == 0))
        decision_idx = np.flatnonzero(grid.to_numpy())
        y_full, future_full, _ = p7.p6.intraday_labels(
            intraday_source["timestamp"], intraday_source["spot"], horizon
        )
        y_expected = y_full.iloc[decision_idx].to_numpy(dtype=float)
        future_expected = future_full.iloc[decision_idx].to_numpy(dtype=float)
        expected_times = pd.to_datetime(
            intraday_source["timestamp"].iloc[decision_idx], utc=True, errors="raise"
        ).reset_index(drop=True)
    else:
        raise SystemExit(f"ARTIFACT_ERROR: unsupported panel layer {layer}")

    y_expected = np.asarray(y_expected, dtype=float)
    future_expected = np.asarray(future_expected, dtype=float)
    if len(frame) != len(y_expected) or len(frame) != len(future_expected):
        raise SystemExit(f"ARTIFACT_ERROR: source-derived row count mismatch for {layer} H={horizon}")
    y_actual = frame["label_direction"].to_numpy(dtype=float)
    if not np.array_equal(y_actual, y_expected, equal_nan=True):
        raise SystemExit(
            f"ARTIFACT_ERROR: source-derived label mismatch for {layer} H={horizon}; "
            + _numeric_mismatch_diagnostic(y_actual, y_expected)
        )
    future_actual = frame["future_return"].to_numpy(dtype=float)
    future_match, future_diagnostic = compare_float64_within_ulps(
        future_actual, future_expected, max_ulps=2
    )
    if not future_match:
        raise SystemExit(
            f"ARTIFACT_ERROR: source-derived future-return mismatch for {layer} H={horizon}; "
            + json.dumps(future_diagnostic, sort_keys=True, separators=(",", ":"))
        )

    actual_times = pd.DatetimeIndex(pd.to_datetime(frame["decision_timestamp"], utc=(layer == "intraday"), errors="raise"))
    expected_times = pd.DatetimeIndex(pd.to_datetime(expected_times, utc=(layer == "intraday"), errors="raise"))
    if not np.array_equal(actual_times.asi8, expected_times.asi8):
        raise SystemExit(f"ARTIFACT_ERROR: source-derived decision timestamp mismatch for {layer} H={horizon}")

    return {
        "layer": layer,
        "horizon": int(horizon),
        "label_direction_exact": True,
        "decision_timestamp_exact": True,
        "future_return": future_diagnostic,
    }

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
    ts = pd.DatetimeIndex(pd.to_datetime(frame["decision_timestamp"], utc=intraday, errors="raise"))
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
    abstain_bands = getattr(p7, "ABSTAIN", ABSTAIN)
    for name, pred in candidates.items():
        mask = None
        extra = {}
        if name in abstain_bands:
            lo, hi = abstain_bands[name]
            finite = np.isfinite(pred)
            mask = finite & ~((pred >= lo) & (pred <= hi))
            extra = {
                "coverage": float(mask.sum() / finite.sum()) if finite.sum() else 0.0,
                "trade_n": int(mask.sum()),
                "evaluable_n": int(finite.sum()),
            }
        res = p7.p6.metrics(y, pred, future, block_len, extra=extra, mask=mask)
        # Run #994's immutable block-diagnostic helper accepts the exact same
        # abstention eligibility mask used for aggregate metrics.
        res["chronological_blocks"] = p7.block_diagnostics(y, pred, blocks, mask)
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
    if not manifest.get("run_id") or not manifest.get("commit"):
        raise SystemExit("ARTIFACT_ERROR: missing immutable run/commit identity")
    runtime = manifest.get("runtime", {})
    if not all(runtime.get(k) for k in ("python", "platform", "machine", "numpy", "pandas", "scikit_learn", "scipy", "pyarrow", "threadpoolctl")):
        raise SystemExit("ARTIFACT_ERROR: incomplete runtime fingerprint")
    expected_source_paths = {"daily_csv", "intraday_parquet"}
    if set(manifest.get("source_files", {})) != expected_source_paths:
        raise SystemExit("ARTIFACT_ERROR: required source-file manifest entries missing or unexpected")
    expected_code_paths = {
        "scripts/run_phase7_ensemble.py", "scripts/run_phase6_novel.py",
        "scripts/run_phase3_daily_baselines.py", "scripts/run_phase3_intraday_baselines.py",
    }
    if set(manifest.get("code_files", {})) != expected_code_paths:
        raise SystemExit("ARTIFACT_ERROR: required immutable source-code fingerprints missing or unexpected")
    for name, source in manifest.get("source_files", {}).items():
        if not source.get("sha256") or len(source["sha256"]) != 64:
            raise SystemExit(f"ARTIFACT_ERROR: malformed source hash for {name}")
        source_path = ROOT / source["path"]
        if not source_path.is_file() or sha256(source_path) != source["sha256"]:
            raise SystemExit(f"ARTIFACT_ERROR: source file missing/hash mismatch for {name}")
    if len(manifest.get("code_files", {})) < 4 or any(len(v) != 64 for v in manifest.get("code_files", {}).values()):
        raise SystemExit("ARTIFACT_ERROR: incomplete/malformed code-file fingerprints")
    verify_code_hashes(manifest)
    global p7
    p7 = load_reference_phase7_module(str(manifest["commit"]))
    if len(manifest.get("prediction_panels", [])) != 10:
        raise SystemExit("ARTIFACT_ERROR: expected exactly ten horizon panels")

    expected_specs = {(layer, H) for layer, (_, horizons) in LAYERS.items() for H in horizons}
    found_specs = {(str(x.get("layer")), int(x.get("horizon"))) for x in manifest["prediction_panels"]}
    if found_specs != expected_specs:
        raise SystemExit(f"ARTIFACT_ERROR: panel coverage mismatch: {sorted(found_specs)}")
    daily_source = p7.p6.load_daily()
    intraday_source = p7.p6.load_intraday()
    output_dir.mkdir(parents=True, exist_ok=True)
    cells = []
    prediction_files = []
    for record in manifest["prediction_panels"]:
        layer, H = str(record["layer"]), int(record["horizon"])
        # Upload-artifact strips the common data/reports prefix.
        panel_path = reference_dir / f"phase7_predictions_{layer}_H{H}.parquet"
        if not panel_path.is_file():
            raise SystemExit(f"ARTIFACT_ERROR: missing panel file {panel_path.name}")
        if sha256(panel_path) != record["sha256"]:
            raise SystemExit(f"ARTIFACT_ERROR: panel SHA-256 mismatch: {panel_path.name}")
        frame = pd.read_parquet(panel_path)
        if int(record.get("rows", -1)) != len(frame):
            raise SystemExit(f"ARTIFACT_ERROR: row-count mismatch: {panel_path.name}")
        if record.get("columns") != list(frame.columns):
            raise SystemExit(f"ARTIFACT_ERROR: column-schema mismatch: {panel_path.name}")
        if set(frame["layer"].astype(str)) != {layer} or set(frame["horizon"].astype(int)) != {H}:
            raise SystemExit(f"ARTIFACT_ERROR: panel identity mismatch: {panel_path.name}")
        if set(frame["source_run_id"].astype(str)) != {str(manifest["run_id"])}:
            raise SystemExit(f"ARTIFACT_ERROR: panel run identity mismatch: {panel_path.name}")
        if set(frame["source_commit"].astype(str)) != {str(manifest["commit"])}:
            raise SystemExit(f"ARTIFACT_ERROR: panel commit identity mismatch: {panel_path.name}")
        intraday, horizons = LAYERS[layer]
        source_alignment = verify_panel_source_alignment(
            frame, layer, H, daily_source, intraday_source
        )
        if H not in horizons:
            raise SystemExit(f"ARTIFACT_ERROR: unregistered horizon {layer} H={H}")
        if int(aggregate[layer]["rows"]) <= 0:
            raise SystemExit(f"ARTIFACT_ERROR: invalid aggregate row count for {layer}")
        expected_cell = aggregate[layer]["horizons"][str(H)]
        metrics = compare_panel(frame, expected_cell, intraday)
        out = output_dir / panel_path.name
        shutil.copy2(panel_path, out)
        copied_path = str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out)
        cells.append({"layer": layer, "horizon": H, "rows": metrics["rows"],
                      "blocks": metrics["blocks"], "reference_match": True,
                      "copied_path": copied_path,
                      "source_alignment": source_alignment})
        prediction_files.append({"path": copied_path, "sha256": sha256(out),
                                 "rows": metrics["rows"], "layer": layer, "horizon": H})
    result = {
        "status": "PASS", "mode": "saved-row-level-panel-no-model-refit",
        "reference_run_id": manifest.get("run_id"), "reference_commit": manifest.get("commit"),
        "artifact_manifest_sha256": sha256(manifest_path),
        "aggregate_sha256": sha256(aggregate_path), "tolerance_abs": TOL,
        "cells": cells, "prediction_files": prediction_files,
        "total_cells": len(cells), "all_cells_reproduced": len(cells) == 10,
    }
    (output_dir / "phase8_forecast_reconstruction_manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
