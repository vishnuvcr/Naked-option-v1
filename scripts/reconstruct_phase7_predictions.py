from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile
import zipfile

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import run_phase7_ensemble as p7

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reports" / "phase8"
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = ROOT / "research" / "phase8" / "PHASE8_FROZEN_INPUT_MANIFEST.json"

LAYERS = {
    "daily": (False, [1, 2, 3, 5, 10]),
    "intraday": (True, [5, 15, 30, 60, 120]),
}
METHODS = [f"P{i:02d}" for i in range(1, 11)]
ABSTAIN = {"P05": (0.45, 0.55), "P06": (0.40, 0.60)}
TOL = 1e-9
FROZEN_PHASE7_SOURCE_SHA1 = "399ad338a409b6faf56c3ee243f2643cc89f162a"


def find_reference_json(reference: Path) -> Path:
    if reference.is_file():
        if reference.suffix.lower() == ".json":
            return reference
        if reference.suffix.lower() == ".zip":
            tmp = Path(tempfile.mkdtemp(prefix="phase7_run654_"))
            with zipfile.ZipFile(reference) as z:
                candidates = [n for n in z.namelist() if n.endswith("phase7_ensemble_results.json")]
                if len(candidates) != 1:
                    raise SystemExit(f"REFERENCE_ERROR: expected one phase7 result JSON, found {candidates}")
                z.extract(candidates[0], tmp)
            return tmp / candidates[0]
        raise SystemExit(f"REFERENCE_ERROR: unsupported file {reference}")
    if reference.is_dir():
        matches = sorted(reference.rglob("phase7_ensemble_results.json"))
        if len(matches) != 1:
            raise SystemExit(f"REFERENCE_ERROR: expected one phase7_ensemble_results.json under {reference}, found {len(matches)}")
        return matches[0]
    raise SystemExit(f"REFERENCE_ERROR: reference path does not exist: {reference}")


def recursive_compare(expected, actual, path="root"):
    failures = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected dict, got {type(actual).__name__}"]
        ek, ak = set(expected), set(actual)
        for k in sorted(ek - ak):
            failures.append(f"{path}.{k}: missing actual key")
        for k in sorted(ak - ek):
            failures.append(f"{path}.{k}: unexpected actual key")
        for k in sorted(ek & ak):
            failures.extend(recursive_compare(expected[k], actual[k], f"{path}.{k}"))
        return failures
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected list, got {type(actual).__name__}"]
        if len(expected) != len(actual):
            failures.append(f"{path}: list length {len(actual)} != {len(expected)}")
            return failures
        for i, (e, a) in enumerate(zip(expected, actual)):
            failures.extend(recursive_compare(e, a, f"{path}[{i}]"))
        return failures
    if expected is None:
        if actual is not None:
            failures.append(f"{path}: expected None, got {actual!r}")
        return failures
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if actual is None or not isinstance(actual, (int, float)) or isinstance(actual, bool):
            failures.append(f"{path}: expected numeric {expected!r}, got {actual!r}")
            return failures
        if not math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=TOL):
            failures.append(f"{path}: {actual!r} != {expected!r} within {TOL}")
        return failures
    if expected != actual:
        failures.append(f"{path}: {actual!r} != {expected!r}")
    return failures


def decision_timestamps(df: pd.DataFrame, intraday: bool) -> pd.Series:
    if not intraday:
        return pd.to_datetime(df["date"], errors="raise")
    q = df.copy()
    grid = (
        (q["minute_of_day"] >= 570)
        & (q["minute_of_day"] <= 930)
        & (((q["minute_of_day"] - 570) % 60) == 0)
    )
    return pd.to_datetime(q.loc[grid, "timestamp"], utc=True).reset_index(drop=True)


def build_candidates(df, intraday: bool, H: int):
    captured = p7.capture_scope(df, intraday=intraday, horizons=[H])
    blocks = p7.blocks_for(df, intraday=intraday)
    vol, trend = p7.regime_inputs(df, intraday=intraday)

    base = {
        m: captured[(str(H), m)]["p"]
        for m in p7.METHODS
        if (str(H), m) in captured
    }
    y = captured[(str(H), "E01")]["y"].copy()
    future = captured[(str(H), "E01")]["future"].copy()

    for m in p7.BLOCKED:
        base[m] = np.full(len(y), np.nan)

    p1, p2, p3, p4 = p7.combine(base)
    p7p = p7.stacking(base, y, blocks)
    p8, p9, regime_diag, regime_fallbacks = p7.regimes(p1, p4, y, vol, trend, blocks)

    candidates = {
        "P01": p1,
        "P02": p2,
        "P03": p3,
        "P04": p4,
        "P05": p1.copy(),
        "P06": p1.copy(),
        "P07": p7p,
        "P08": p8,
        "P09": p9,
        "P10": p9.copy(),
    }

    baseline = p7.causal_baseline(y, blocks)
    family = p7.family_bootstrap(
        y, candidates, baseline, 60 if intraday else 20
    )

    results = {}
    chronological = {}
    for name, pred in candidates.items():
        extra = {}
        mask = None
        if name in ABSTAIN:
            lo, hi = ABSTAIN[name]
            finite = np.isfinite(pred)
            mask = finite & ~((pred >= lo) & (pred <= hi))
            extra = {
                "coverage": float(mask.sum() / finite.sum()) if finite.sum() else 0.0,
                "trade_n": int(mask.sum()),
                "evaluable_n": int(finite.sum()),
            }
        res = p7.p6.metrics(
            y, pred, future, 60 if intraday else 20,
            extra=extra,
            mask=mask,
        )
        res["chronological_blocks"] = p7.block_diagnostics(y, pred, blocks)
        if name in ("P08", "P09", "P10"):
            res["regime_diagnostics"] = regime_diag
            res["regime_fallback_count"] = int(regime_fallbacks)
        results[name] = res
        chronological[name] = pred

    results["_FAMILY_TEST"] = family

    return {
        "y": y,
        "future": future,
        "predictions": chronological,
        "results": results,
        "timestamps": decision_timestamps(df, intraday),
    }


def canonical_prediction_rows(layer, H, built):
    ts = built["timestamps"]
    y = built["y"]
    fut = built["future"]
    preds = built["predictions"]
    if len(ts) != len(y):
        raise SystemExit(
            f"RECONSTRUCTION_ERROR: timestamp count {len(ts)} != prediction length {len(y)} "
            f"for {layer} H={H}"
        )

    frame = pd.DataFrame({
        "layer": layer,
        "horizon": int(H),
        "decision_timestamp": ts,
        "label_direction": y,
        "future_return": fut,
    })
    for name in METHODS:
        frame[name] = np.asarray(preds[name], dtype=float)

    frame["source_run"] = "phase7_run654"
    frame["phase7_developer_commit"] = "4f1d695f291ed32996c07f01710afcecc6f2a540"
    return frame



def write_mismatch_diagnostic(layer, H, built, df, intraday, outdir, failures):
    """Persist row-level evidence for failed aggregate checks without changing metrics."""
    import re

    blocks = p7.blocks_for(df, intraday)
    failed_blocks = sorted({
        int(match.group(1))
        for failure in failures
        if (match := re.search(r"chronological_blocks\\[(\\d+)\\]\\.brier", failure))
    })
    y = np.asarray(built["y"], dtype=float)
    p = np.asarray(built["predictions"]["P07"], dtype=float)
    timestamps = built["timestamps"]
    details = []
    for block_id in failed_blocks:
        rows = np.asarray(blocks[block_id], dtype=int)
        valid = np.isfinite(y[rows]) & np.isfinite(p[rows])
        selected = rows[valid]
        clipped = np.clip(p[selected], 1e-6, 1 - 1e-6)
        labels = y[selected].astype(int)
        squared_error = (clipped - labels) ** 2
        details.append({
            "block_index": block_id,
            "n": int(len(selected)),
            "brier_from_row_terms": float(np.mean(squared_error)) if len(selected) else None,
            "rows": [{
                "source_row_index": int(row),
                "decision_timestamp": str(timestamps[row]),
                "label_direction": int(y[row]),
                "p07_raw": float(p[row]),
                "p07_clipped": float(clipped[i]),
                "squared_error": float(squared_error[i]),
            } for i, row in enumerate(selected)],
        })
    payload = {
        "status": "FAIL",
        "diagnostic_only": True,
        "layer": layer,
        "horizon": int(H),
        "tolerance_abs": TOL,
        "failures": failures,
        "p07_failed_blocks": details,
        "note": "Uses the existing reconstructed prediction/label arrays and Phase 7 block membership; does not alter the reference or acceptance tolerance.",
    }
    path = outdir / f"phase8_reconstruction_diagnostics_{layer}_H{H}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = b"blob " + str(len(data)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + data).hexdigest()


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", required=True)
    ap.add_argument("--output-dir", default=str(OUT))
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["empirical_option_execution_authorized"]:
        raise SystemExit("RECONSTRUCTION_ERROR: frozen input manifest must not authorize option execution")
    if manifest["developer_commit"] != "4f1d695f291ed32996c07f01710afcecc6f2a540":
        raise SystemExit("RECONSTRUCTION_ERROR: Run #654 developer commit mismatch")
    phase7_blob_sha = git_blob_sha(ROOT / "scripts" / "run_phase7_ensemble.py")
    if phase7_blob_sha != manifest["phase7_source_blob_sha"] or phase7_blob_sha != FROZEN_PHASE7_SOURCE_SHA1:
        raise SystemExit(
            "RECONSTRUCTION_ERROR: Phase 7 source blob mismatch; the accepted Run #654 implementation is not present"
        )

    reference_path = find_reference_json(Path(args.reference))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    if reference.get("protocol") != "research/phase7/PHASE7_METHOD_SPEC.md":
        raise SystemExit("RECONSTRUCTION_ERROR: reference protocol mismatch")
    if reference.get("seed") != 42:
        raise SystemExit("RECONSTRUCTION_ERROR: reference seed mismatch")

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    prediction_files = []
    reconciliation = {
        "status": "PASS",
        "reference": str(reference_path),
        "reference_artifact_id": manifest["artifact_id"],
        "reference_artifact_sha256": manifest["artifact_sha256"],
        "developer_commit": manifest["developer_commit"],
        "phase7_source_blob_sha": manifest["phase7_source_blob_sha"],
        "tolerance_abs": TOL,
        "cells": [],
    }

    with __import__("warnings").catch_warnings():
        __import__("warnings").simplefilter("ignore")
        d = p7.p6.load_daily()
        q = p7.p6.load_intraday()

        for layer, (intraday, horizons) in LAYERS.items():
            df = q if intraday else d
            expected_layer = reference[layer]
            if int(expected_layer["rows"]) != int(len(df)):
                raise SystemExit(
                    f"RECONSTRUCTION_ERROR: {layer} row count {len(df)} != reference {expected_layer['rows']}"
                )

            for H in horizons:
                # Match the frozen Run #654 runtime's single-process numerical execution.
                # The hosted workflow also pins Python and sets BLAS/OpenMP thread limits.
                with threadpool_limits(limits=1):
                    built = build_candidates(df, intraday, H)
                actual = {"_FAMILY_TEST": built["results"]["_FAMILY_TEST"]}
                actual.update({m: built["results"][m] for m in METHODS})

                expected = expected_layer["horizons"][str(H)]
                failures = recursive_compare(expected, actual)
                cell = {
                    "layer": layer,
                    "horizon": int(H),
                    "reference_match": not failures,
                    "failure_count": len(failures),
                    "first_failures": failures[:20],
                }
                reconciliation["cells"].append(cell)

                # Preserve the exact row-level panel even when the frozen aggregate
                # comparison fails, so the mismatch can be diagnosed without relaxing
                # the gate or changing the reference.
                frame = canonical_prediction_rows(layer, H, built)
                out = outdir / f"phase7_predictions_{layer}_H{H}.parquet"
                frame.to_parquet(out, index=False)
                digest = hash_file(out)
                prediction_files.append({
                    "path": str(out),
                    "sha256": digest,
                    "rows": int(len(frame)),
                    "layer": layer,
                    "horizon": int(H),
                })
                cell["prediction_sha256"] = digest
                cell["prediction_rows"] = int(len(frame))

                if failures:
                    reconciliation["status"] = "FAIL"
                    diagnostic = write_mismatch_diagnostic(
                        layer, H, built, df, intraday, outdir, failures
                    )
                    raise SystemExit(
                        "RECONSTRUCTION_ERROR: Run #654 aggregate reproduction failed for "
                        f"{layer} H={H}: {failures[:5]}; row panel {out.name}; diagnostic {diagnostic.name}"
                    )

    manifest_out = outdir / "phase8_forecast_reconstruction_manifest.json"
    manifest_payload = {
        **reconciliation,
        "prediction_files": prediction_files,
        "total_cells": len(reconciliation["cells"]),
        "all_cells_reproduced": all(x["reference_match"] for x in reconciliation["cells"]),
    }
    manifest_out.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": manifest_payload["status"],
        "cells": len(reconciliation["cells"]),
        "prediction_files": len(prediction_files),
        "manifest_sha256": hash_file(manifest_out),
    }, indent=2))


if __name__ == "__main__":
    main()
