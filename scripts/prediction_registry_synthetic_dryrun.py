#!/usr/bin/env python3
"""Deterministic synthetic-only R2 pipeline dry run.

Never opens market data. This validates registry orchestration, bookkeeping, checkpoint/restart,
error logging and planning estimates using deterministic toy probabilities; it is NOT model evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import statistics
import sys
import time
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "registry"
INDEX_PATH = REGISTRY / "PREDICTION_REGISTRY_SHARD_INDEX_V2_R2.json"
MATRIX_PATH = REGISTRY / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"
PREREG_PATH = REGISTRY / "PREDICTION_PREREGISTRATION_V2_R2.json"
DATA_MANIFEST_PATH = ROOT / "research" / "data" / "DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json"
FOLD_IDS = [f"F{i:02d}" for i in range(1, 9)]
LABEL_IDS = ("INTRA_30M_UP_DOWN", "POS_1D_UP_DOWN")
SEED = 2026101208
EPS = 1e-6

# Relative fit-cost multipliers are explicit planning assumptions, not measured estimator runtimes.
FAMILY_COST_WEIGHT = {
    "logistic_regression": 1.0,
    "probit_regression": 1.0,
    "generalized_additive_model": 2.0,
    "lda": 1.0,
    "qda": 2.0,
    "elastic_net_logistic": 2.0,
    "random_forest": 5.0,
    "extra_trees": 6.0,
    "gradient_boosting": 6.0,
    "histogram_gradient_boosting": 4.0,
    "kernel_svm": 8.0,
    "nearest_centroid": 2.0,
    "knn_density_ratio": 10.0,
    "hidden_markov_model": 10.0,
    "markov_switching_logit": 15.0,
    "bayesian_dynamic_logit": 20.0,
    "change_point_segment_model": 8.0,
    "shallow_mlp": 15.0,
    "temporal_convolution_network": 25.0,
    "survival_first_passage": 10.0,
}
FAMILY_MEMORY_FACTOR = {
    "logistic_regression": 1.2, "probit_regression": 1.2,
    "generalized_additive_model": 2.0, "lda": 1.3, "qda": 1.8,
    "elastic_net_logistic": 1.5, "random_forest": 3.0, "extra_trees": 3.2,
    "gradient_boosting": 2.8, "histogram_gradient_boosting": 2.5,
    "kernel_svm": 2.5, "nearest_centroid": 1.5, "knn_density_ratio": 2.0,
    "hidden_markov_model": 2.5, "markov_switching_logit": 3.0,
    "bayesian_dynamic_logit": 4.0, "change_point_segment_model": 2.5,
    "shallow_mlp": 3.0, "temporal_convolution_network": 4.0,
    "survival_first_passage": 3.0,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def git_blob_sha1(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(path)


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-min(x, 40.0))
        return 1.0 / (1.0 + z)
    z = math.exp(max(x, -40.0))
    return z / (1.0 + z)


def logit(p: float) -> float:
    p = min(1.0 - EPS, max(EPS, p))
    return math.log(p / (1.0 - p))


def entropy(p: float) -> float:
    p = min(1.0 - EPS, max(EPS, p))
    return -p * math.log(p) - (1.0 - p) * math.log(1.0 - p)


def mean_log_loss(labels: list[int], probs: list[float]) -> float:
    if not labels or len(labels) != len(probs):
        raise ValueError("labels/probabilities must have the same nonzero length")
    total = 0.0
    for y, p in zip(labels, probs):
        p = min(1.0 - EPS, max(EPS, p))
        total -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return total / len(labels)


def mean_brier(labels: list[int], probs: list[float]) -> float:
    return statistics.fmean((p - y) ** 2 for y, p in zip(labels, probs)) if labels else math.nan


def seed_for(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def make_synthetic_split(label_id: str, fold_id: str) -> dict[str, Any]:
    """Create toy train/validation samples; never reads repository market data."""
    rng = random.Random(seed_for(f"R2-SYNTHETIC|{SEED}|{label_id}|{fold_id}"))
    n_train = 500 if label_id == "INTRA_30M_UP_DOWN" else 300
    n_val = 128 if label_id == "INTRA_30M_UP_DOWN" else 72

    def generate(n: int, drift: float):
        records = []
        for _ in range(n):
            x1 = rng.gauss(0.0, 1.0)
            x2 = rng.gauss(0.0, 1.0)
            regime = abs(x1) + 0.35 * abs(x2)
            true_p = sigmoid(0.18 + 0.42 * x1 - 0.17 * x2 + drift * x1)
            y = 1 if rng.random() < true_p else 0
            records.append({"x1": x1, "x2": x2, "regime": regime, "y": y})
        return records

    drift = (int(fold_id[1:]) - 4.5) * 0.035
    train = generate(n_train, drift=0.0)
    validation = generate(n_val, drift=drift)
    positives = sum(row["y"] for row in train)
    baseline_probability = min(1.0 - EPS, max(EPS, (positives + 0.5) / (len(train) + 1.0)))
    return {"train": train, "validation": validation, "baseline_probability": baseline_probability}


def deterministic_mock_probs(config: dict[str, Any], method: dict[str, Any], records: list[dict[str, Any]], base_rate: float) -> list[float]:
    """Mock adapter used only to exercise scoring; contains no estimator fit or market information."""
    cfg = config["configuration"]
    digest = str(config.get("config_sha256", config["config_id"]))
    alpha = 0.15 + (int(digest[:6], 16) % 80) / 100.0
    beta = -0.35 + (int(digest[6:12], 16) % 70) / 100.0
    if cfg.get("lookback_bars") == 60:
        alpha *= 0.95
    if cfg.get("complexity_preset") == "flexible":
        beta *= 1.05
    # Small family-specific scale differences prevent this smoke test from collapsing to one constant.
    family_scale = 0.8 + (seed_for(method["algorithm_family"]) % 50) / 100.0
    return [
        min(1.0 - EPS, max(EPS, sigmoid(logit(base_rate) + family_scale * (alpha * row["x1"] + beta * row["x2"]))))
        for row in records
    ]


def load_registry() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    idx_raw = INDEX_PATH.read_bytes()
    idx = json.loads(idx_raw.decode("utf-8"))
    matrix_raw = MATRIX_PATH.read_bytes()
    matrix = json.loads(matrix_raw.decode("utf-8"))
    prereg_raw = PREREG_PATH.read_bytes()
    prereg = json.loads(prereg_raw.decode("utf-8"))
    pilot_scope = prereg.get("scope_amendment_2026_10_13", {})
    if pilot_scope.get("status") != "PILOT_ONLY_NOT_EXHAUSTIVE":
        raise SystemExit("BLOCKED: R2 scope must be explicitly marked as a non-exhaustive pilot")
    if pilot_scope.get("no_empirical_fit_authorized_by_this_amendment") is not True:
        raise SystemExit("BLOCKED: R2 pilot scope amendment does not explicitly prohibit empirical fitting")
    if pilot_scope.get("no_pilot_result_may_select_or_rank_methods") is not True:
        raise SystemExit("BLOCKED: pilot results must not select or rank methods")
    if set(pilot_scope.get("included_target_labels", [])) != set(LABEL_IDS):
        raise SystemExit("BLOCKED: pilot target labels do not match the synthetic runner's frozen label IDs")
    data_manifest_raw = DATA_MANIFEST_PATH.read_bytes()
    scope = prereg.get("scope", {})
    actual_manifest_blob = git_blob_sha1(data_manifest_raw)
    pinned_inputs = {
        "data_manifest_git_blob_sha1": actual_manifest_blob,
        "label_manifest_git_blob_sha1": git_blob_sha1((REGISTRY / "PREDICTION_LABEL_MANIFEST_V2_R2.json").read_bytes()),
        "config_manifest_git_blob_sha1": git_blob_sha1((REGISTRY / "PREDICTION_CONFIG_MANIFEST_V2_R2.json").read_bytes()),
        "registry_index_git_blob_sha1": git_blob_sha1(idx_raw),
        "compatibility_matrix_git_blob_sha1": git_blob_sha1(matrix_raw),
    }
    for key, actual in pinned_inputs.items():
        if scope.get(key) != actual:
            raise SystemExit(f"BLOCKED: preregistration source pin mismatch for {key}: expected={scope.get(key)} actual={actual}")
    data_manifest = json.loads(data_manifest_raw.decode("utf-8"))
    if data_manifest.get("encrypted_only") is not True:
        raise SystemExit("BLOCKED: data manifest does not declare encrypted_only=true")
    if data_manifest.get("rows_preserved") != 8999865:
        raise SystemExit("BLOCKED: pinned data manifest row count changed; preregistration must be reviewed")
    label_manifest = json.loads((REGISTRY / "PREDICTION_LABEL_MANIFEST_V2_R2.json").read_text(encoding="utf-8"))
    prereg_flat = [prereg.get("labels", {}).get(label, {}).get("flat_tolerance_abs_simple_return") for label in LABEL_IDS]
    label_flat = [label_manifest.get("return_convention", {}).get("flat_tolerance_abs_simple_return")]
    if len(set(prereg_flat)) != 1 or prereg_flat[0] != label_flat[0]:
        raise SystemExit("BLOCKED: label-manifest flat tolerance and preregistration disagree")
    config_manifest = json.loads((REGISTRY / "PREDICTION_CONFIG_MANIFEST_V2_R2.json").read_text(encoding="utf-8"))
    if config_manifest.get("configuration_count") != 8000 or len(config_manifest.get("config_shards", [])) != 80:
        raise SystemExit("BLOCKED: pinned config manifest count/shard layout changed")
    if idx.get("method_record_count") != 1000 or idx.get("configuration_record_count") != 8000:
        raise SystemExit("BLOCKED: shard index has unexpected total counts")
    matrix_body = dict(matrix)
    expected_matrix_digest = matrix_body.pop("matrix_sha256", None)
    if expected_matrix_digest != sha256_bytes(canonical_json(matrix_body)):
        raise SystemExit("BLOCKED: compatibility matrix canonical digest mismatch")
    method_rows = matrix.get("rows")
    if not isinstance(method_rows, list) or len(method_rows) != 1000:
        raise SystemExit("BLOCKED: row-level compatibility matrix must have 1000 rows")
    if matrix.get("source_shard_index_sha256") != sha256_bytes(idx_raw):
        raise SystemExit("BLOCKED: compatibility matrix was generated from a different shard index")
    if prereg.get("scope", {}).get("source_dataset_is_encrypted_only") is not True:
        raise SystemExit("BLOCKED: this smoke runner requires explicit encrypted-source declaration")
    method_map = {row["method_id"]: row for row in method_rows}
    if len(method_map) != 1000:
        raise SystemExit("BLOCKED: duplicate method ID in compatibility matrix")
    configs = []
    seen_configs: set[str] = set()
    for entry in sorted(idx.get("config_shards", []), key=lambda e: e["part"]):
        path = ROOT / entry["path"]
        raw = path.read_bytes()
        if sha256_bytes(raw) != entry["sha256"] or len(raw) != entry["byte_count"]:
            raise SystemExit(f"BLOCKED: config shard integrity failure: {entry['path']}")
        obj = json.loads(raw.decode("utf-8"))
        rows = obj.get("configs")
        if not isinstance(rows, list) or len(rows) != entry["record_count"]:
            raise SystemExit(f"BLOCKED: config shard count failure: {entry['path']}")
        for row in rows:
            cid = row.get("config_id")
            if not isinstance(cid, str) or cid in seen_configs:
                raise SystemExit(f"BLOCKED: invalid/duplicate config ID {cid!r}")
            seen_configs.add(cid)
            if row.get("method_id") not in method_map:
                raise SystemExit(f"BLOCKED: config points to unknown method {row.get('method_id')}")
            if row.get("configuration", {}).get("label_id") not in LABEL_IDS:
                raise SystemExit(f"BLOCKED: unknown label stratum in {cid}")
            configs.append(row)
    if len(configs) != 8000 or len(seen_configs) != 8000:
        raise SystemExit(f"BLOCKED: expected 8000 unique configurations; found {len(configs)}/{len(seen_configs)}")
    metadata = {
        "method_index_sha256": sha256_bytes(idx_raw),
        "compatibility_matrix_sha256": sha256_bytes(matrix_raw),
        "preregistration_sha256": sha256_bytes(prereg_raw),
        "source_git_blob_pins": pinned_inputs,
        "data_manifest_raw_sha256": sha256_bytes(data_manifest_raw),
        "method_count": 1000,
        "configuration_count": 8000,
    }
    return configs, method_map, metadata


def all_tasks(configs: list[dict[str, Any]], method_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = []
    for config in configs:
        matrix_row = method_map[config["method_id"]]
        for fold in FOLD_IDS:
            task_id = f"{config['config_id']}|{fold}"
            tasks.append({
                "task_id": task_id,
                "config": config,
                "method": matrix_row,
                "fold_id": fold,
                "label_id": config["configuration"]["label_id"],
            })
    return tasks


def score_task(task: dict[str, Any], split: dict[str, Any]) -> dict[str, Any]:
    config = task["config"]
    method = task["method"]
    decision = method["compatibility_decision"]
    common = {
        "task_id": task["task_id"],
        "config_id": config["config_id"],
        "method_id": config["method_id"],
        "label_id": task["label_id"],
        "fold_id": task["fold_id"],
        "synthetic_only": True,
        "scientific_evidence": False,
        "eligible_for_empirical_fitting": False,
        "compatibility_decision": decision,
    }
    if decision != "ALLOW_IN_PRINCIPLE":
        return {
            **common,
            "terminal_status": "BLOCKED_COMPATIBILITY",
            "synthetic_n": 0,
            "synthetic_baseline_log_loss": None,
            "synthetic_candidate_log_loss": None,
            "synthetic_log_loss_improvement": None,
            "synthetic_brier_score": None,
            "synthetic_coverage": 0.0,
            "failure_reason": method["decision_code"],
        }

    train = split["train"]
    valid = split["validation"]
    p_train = split["baseline_probability"]
    train_probs = deterministic_mock_probs(config, method, train, p_train)
    val_probs = deterministic_mock_probs(config, method, valid, p_train)
    operator = method["inference_operator"]
    keep_train = [True] * len(train)
    keep_valid = [True] * len(valid)
    if operator == "uncertainty_abstention":
        sorted_entropy = sorted(entropy(p) for p in train_probs)
        cutoff = sorted_entropy[min(len(sorted_entropy) - 1, int(0.8 * (len(sorted_entropy) - 1)))]
        keep_valid = [entropy(p) <= cutoff for p in val_probs]
    elif operator == "regime_gated_decision":
        threshold = sorted(row["regime"] for row in train)[int(0.4 * (len(train) - 1))]
        keep_valid = [row["regime"] >= threshold for row in valid]
    labels = [row["y"] for row, keep in zip(valid, keep_valid) if keep]
    probs = [p for p, keep in zip(val_probs, keep_valid) if keep]
    if not labels:
        return {
            **common,
            "terminal_status": "SYNTHETIC_MOCK_FAILED_EMPTY_COVERAGE",
            "synthetic_n": 0,
            "synthetic_baseline_log_loss": None,
            "synthetic_candidate_log_loss": None,
            "synthetic_log_loss_improvement": None,
            "synthetic_brier_score": None,
            "synthetic_coverage": 0.0,
            "failure_reason": "synthetic abstention/gate accepted no rows",
        }
    baseline = [p_train] * len(labels)
    baseline_loss = mean_log_loss(labels, baseline)
    candidate_loss = mean_log_loss(labels, probs)
    return {
        **common,
        "terminal_status": "SYNTHETIC_MOCK_ONLY",
        "synthetic_n": len(labels),
        "synthetic_baseline_log_loss": round(baseline_loss, 12),
        "synthetic_candidate_log_loss": round(candidate_loss, 12),
        "synthetic_log_loss_improvement": round(baseline_loss - candidate_loss, 12),
        "synthetic_brier_score": round(mean_brier(labels, probs), 12),
        "synthetic_coverage": round(len(labels) / len(valid), 6),
        "failure_reason": None,
    }


def estimate_resources(configs: list[dict[str, Any]], method_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = CounterLike()
    for cfg in configs:
        family = method_map[cfg["method_id"]]["algorithm_family"]
        counts.total_by_family[family] = counts.total_by_family.get(family, 0) + 1
        if method_map[cfg["method_id"]]["compatibility_decision"] == "ALLOW_IN_PRINCIPLE":
            counts.compatible_by_family[family] = counts.compatible_by_family.get(family, 0) + 1
    base_seconds_per_fit = 5.0  # explicit planning assumption for a 20k-row, <=1920-feature baseline fit
    fit_count_per_config = len(FOLD_IDS) * 4  # one final fit + three inner chronological calibration fits
    feature_matrix_bytes = 20000 * 60 * 32 * 8
    feature_matrix_mib = feature_matrix_bytes / (1024 * 1024)
    per_family = []
    total_fits = 0
    total_cpu_seconds = 0.0
    for family in sorted(FAMILY_COST_WEIGHT):
        configs_n = counts.compatible_by_family.get(family, 0)
        fit_count = configs_n * fit_count_per_config
        fit_seconds = base_seconds_per_fit * FAMILY_COST_WEIGHT[family]
        cpu = fit_count * fit_seconds
        total_fits += fit_count
        total_cpu_seconds += cpu
        memory_mib = 500.0 + feature_matrix_mib * FAMILY_MEMORY_FACTOR[family]
        per_family.append({
            "family": family,
            "all_registry_configurations": counts.total_by_family.get(family, 0),
            "compatible_design_configurations_pending_tests": configs_n,
            "hypothetical_fit_calls": fit_count,
            "assumed_cpu_seconds_per_fit_at_20000_rows_1920_features": fit_seconds,
            "estimated_serial_cpu_hours": round(cpu / 3600.0, 4),
            "estimated_single_worker_peak_memory_mib": round(memory_mib, 1),
            "cost_weight": FAMILY_COST_WEIGHT[family],
        })
    return {
        "status": "PLANNING_ESTIMATE_ONLY_NOT_MEASURED_ESTIMATOR_COST",
        "synthetic_benchmark_is_not_an_estimator_fit": True,
        "assumption": "5 CPU seconds per baseline fit on 20,000 rows and at most 1,920 float64 features; family multipliers and memory factors are engineering assumptions, not observations from market-data fitting.",
        "feature_matrix_shape_assumed": [20000, 1920],
        "feature_matrix_mib": round(feature_matrix_mib, 1),
        "outer_folds": len(FOLD_IDS),
        "fits_per_config_across_all_folds": fit_count_per_config,
        "eligible_design_configs_pending_gate": sum(counts.compatible_by_family.values()),
        "estimated_hypothetical_fit_calls": total_fits,
        "estimated_hypothetical_serial_cpu_hours": round(total_cpu_seconds / 3600.0, 2),
        "peak_single_worker_memory_mib": round(max(x["estimated_single_worker_peak_memory_mib"] for x in per_family), 1),
        "four_worker_peak_memory_mib_lower_bound": round(4 * max(x["estimated_single_worker_peak_memory_mib"] for x in per_family), 1),
        "per_family": per_family,
    }


class CounterLike:
    def __init__(self):
        self.total_by_family: dict[str, int] = {}
        self.compatible_by_family: dict[str, int] = {}


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())


def compute_file_sha(path: Path) -> tuple[int, str, int]:
    raw = path.read_bytes() if path.exists() else b""
    return len(raw), sha256_bytes(raw), raw.count(b"\n")


def save_checkpoint(checkpoint_path: Path, output_path: Path, task_count: int, total_tasks: int,
                    metadata: dict[str, Any], status: str, started_at: float,
                    error_path: Path) -> None:
    byte_count, output_sha, line_count = compute_file_sha(output_path)
    atomic_json(checkpoint_path, {
        "schema_version": "prediction-synthetic-dryrun-checkpoint-v1",
        "status": status,
        "synthetic_only": True,
        "scientific_evidence": False,
        "completed_tasks": task_count,
        "total_tasks": total_tasks,
        "output_bytes": byte_count,
        "output_lines": line_count,
        "output_sha256": output_sha,
        "metadata": metadata,
        "error_log_path": error_path.as_posix(),
        "elapsed_wall_seconds_in_current_process": round(time.monotonic() - started_at, 6),
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "r2_synthetic_dryrun" / "results.jsonl")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--errors", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--simulate-interruption-after", type=int, default=None)
    parser.add_argument("--inject-failure-on-task", type=str, default=None)
    parser.add_argument("--max-tasks", type=int, default=None, help="test-only deterministic task prefix")
    args = parser.parse_args(argv)

    output_path = args.output.resolve()
    checkpoint_path = (args.checkpoint or output_path.with_suffix(".checkpoint.json")).resolve()
    summary_path = (args.summary or output_path.with_suffix(".summary.json")).resolve()
    error_path = (args.errors or output_path.with_suffix(".errors.jsonl")).resolve()
    started_at = time.monotonic()
    configs, method_map, metadata = load_registry()
    tasks = all_tasks(configs, method_map)
    if args.max_tasks is not None:
        if args.max_tasks < 1:
            raise SystemExit("--max-tasks must be positive")
        tasks = tasks[:args.max_tasks]
    total_tasks = len(tasks)
    if args.simulate_interruption_after is not None and args.resume:
        raise SystemExit("--resume and --simulate-interruption-after cannot be combined")
    if args.simulate_interruption_after is not None and not (1 <= args.simulate_interruption_after < total_tasks):
        raise SystemExit("--simulate-interruption-after must be in [1,total_tasks-1]")

    completed = 0
    if args.resume:
        if not checkpoint_path.exists():
            raise SystemExit(f"Cannot resume; missing checkpoint {checkpoint_path}")
        state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if state.get("metadata") != metadata or state.get("total_tasks") != total_tasks:
            raise SystemExit("BLOCKED: checkpoint metadata or task universe differs from current committed registry")
        byte_count, output_sha, line_count = compute_file_sha(output_path)
        if (byte_count, output_sha, line_count) != (state.get("output_bytes"), state.get("output_sha256"), state.get("output_lines")):
            raise SystemExit("BLOCKED: result file does not exactly match checkpoint; refusing unsafe resume")
        if line_count != state.get("completed_tasks"):
            raise SystemExit("BLOCKED: checkpoint task count and result line count differ")
        completed = int(line_count)
        if completed < 0 or completed > total_tasks:
            raise SystemExit("BLOCKED: invalid checkpoint progress")
        if state.get("status") not in ("INTERRUPTED_SYNTHETIC_TEST", "RUNNING", "FAILED_SYNTHETIC_TEST"):
            raise SystemExit(f"BLOCKED: checkpoint state {state.get('status')!r} is not resumable")
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.touch(exist_ok=True)
    else:
        if output_path.exists() or checkpoint_path.exists():
            raise SystemExit("Refusing to overwrite output/checkpoint without --resume; use a clean path")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.touch(exist_ok=True)

    splits: dict[tuple[str, str], dict[str, Any]] = {}
    for label_id in LABEL_IDS:
        for fold_id in FOLD_IDS:
            splits[(label_id, fold_id)] = make_synthetic_split(label_id, fold_id)

    for i in range(completed, total_tasks):
        task = tasks[i]
        if args.inject_failure_on_task == task["task_id"]:
            try:
                raise RuntimeError("deterministic synthetic failure injection requested")
            except Exception as exc:
                traceback_text = traceback.format_exc()
                record = {
                    "task_id": task["task_id"],
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "traceback_sha256": sha256_bytes(traceback_text.encode("utf-8")),
                    "synthetic_only": True,
                    "scientific_evidence": False,
                }
                append_jsonl(error_path, record)
                save_checkpoint(checkpoint_path, output_path, i, total_tasks, metadata,
                                "FAILED_SYNTHETIC_TEST", started_at, error_path)
                return 2
        result = score_task(task, splits[(task["label_id"], task["fold_id"])])
        append_jsonl(output_path, result)
        done = i + 1
        if done % 250 == 0 or done == total_tasks or (
            args.simulate_interruption_after is not None and done == args.simulate_interruption_after
        ):
            save_checkpoint(checkpoint_path, output_path, done, total_tasks, metadata,
                            "RUNNING", started_at, error_path)
        if args.simulate_interruption_after is not None and done == args.simulate_interruption_after:
            save_checkpoint(checkpoint_path, output_path, done, total_tasks, metadata,
                            "INTERRUPTED_SYNTHETIC_TEST", started_at, error_path)
            print(json.dumps({"status": "INTERRUPTED_SYNTHETIC_TEST", "completed_tasks": done, "total_tasks": total_tasks}))
            return 75

    # Final deterministic task rows are result artifacts; wall time is kept only in summary/checkpoint metadata.
    byte_count, output_sha, line_count = compute_file_sha(output_path)
    result_counts: dict[str, int] = {}
    for line in output_path.read_text(encoding="utf-8").splitlines():
        obj = json.loads(line)
        status = obj["terminal_status"]
        result_counts[status] = result_counts.get(status, 0) + 1
    resource_estimate = estimate_resources(configs, method_map)
    summary = {
        "schema_version": "prediction-synthetic-dryrun-summary-v1",
        "status": "COMPLETE_SYNTHETIC_ONLY_NOT_SCIENTIFIC_EVIDENCE",
        "scientific_evidence": False,
        "market_data_opened": False,
        "model_fitting_performed": False,
        "holdout_accessed": False,
        "seed": SEED,
        "metadata": metadata,
        "tasks_total": total_tasks,
        "result_rows": line_count,
        "result_file_bytes": byte_count,
        "result_file_sha256": output_sha,
        "result_status_counts": result_counts,
        "checkpoint_path": checkpoint_path.as_posix(),
        "error_log_path": error_path.as_posix(),
        "resource_estimate": resource_estimate,
        "elapsed_wall_seconds": round(time.monotonic() - started_at, 6),
    }
    atomic_json(summary_path, summary)
    save_checkpoint(checkpoint_path, output_path, total_tasks, total_tasks, metadata,
                    "COMPLETE_SYNTHETIC_ONLY", started_at, error_path)
    print(json.dumps({
        "status": summary["status"],
        "tasks_total": total_tasks,
        "result_status_counts": result_counts,
        "result_file_sha256": output_sha,
        "estimated_hypothetical_serial_cpu_hours": resource_estimate["estimated_hypothetical_serial_cpu_hours"],
        "estimated_hypothetical_fit_calls": resource_estimate["estimated_hypothetical_fit_calls"],
        "scientific_evidence": False,
        "market_data_opened": False,
        "model_fitting_performed": False,
        "holdout_accessed": False,
        "summary_path": summary_path.as_posix(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Synthetic CI rerun requested after the registry contrast repair; no market data is read.
