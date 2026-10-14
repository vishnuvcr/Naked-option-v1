#!/usr/bin/env python3
"""Independent, read-only audit of the frozen Phase 8P PM0001 result bundle.

Uses only the Python standard library and the exact developer checkout supplied by
the tester workflow. It does not import developer validators or fit models.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

EXPECTED_DATA_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
FOLDS = tuple(f"F{i:02d}" for i in range(1, 9))
TERMINAL = {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL", "BLOCKED_DATA", "BLOCKED_GATE", "FAILED_TECHNICAL"}
METRIC_FIELDS = (
    "baseline_log_loss", "candidate_log_loss", "log_loss_improvement",
    "bootstrap_ci_lower", "bootstrap_ci_upper", "raw_p_value", "by_adjusted_p_value",
    "class_prior_baseline_log_loss", "previous_sign_baseline_log_loss",
    "brier_score", "balanced_accuracy", "roc_auc", "average_precision",
    "calibration_intercept", "calibration_slope",
)
BANNED_ROW_FIELDS = {
    "raw_market_rows", "raw_features", "samples", "y_validation", "probabilities",
    "baseline_probabilities", "validation_indices", "training_indices",
    "per_observation_predictions",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_TOP_LEVEL_NOT_OBJECT:{path}")
    return value


def issue(issues: list[dict[str, Any]], code: str, **details: Any) -> None:
    issues.append({"code": code, **details})


def independent_by_adjustment(p_values: Mapping[str, float], q: float = 0.05) -> dict[str, dict[str, Any]]:
    """Independent Benjamini–Yekutieli adjusted p-values and step-up decisions."""
    if not 0 < q < 1:
        raise ValueError("q must lie in (0, 1)")
    if not p_values:
        return {}
    items = sorted(((str(k), float(v)) for k, v in p_values.items()), key=lambda kv: (kv[1], kv[0]))
    if any(not math.isfinite(p) or not 0 <= p <= 1 for _, p in items):
        raise ValueError("invalid p-value")
    m = len(items)
    harmonic = math.fsum(1.0 / r for r in range(1, m + 1))
    factor = m * harmonic
    adjusted = [1.0] * m
    running = 1.0
    for i in range(m - 1, -1, -1):
        running = min(running, items[i][1] * factor / (i + 1))
        adjusted[i] = min(1.0, running)
    last = 0
    for rank, (_, p) in enumerate(items, 1):
        if p <= rank * q / factor:
            last = rank
    reject = {name for name, _ in items[:last]}
    return {
        name: {
            "raw_p_value": p,
            "by_adjusted_p_value": adjusted[i],
            "reject_at_q": name in reject,
        }
        for i, (name, p) in enumerate(items)
    }


def reconstruct_pm0001_configs(root: Path, issues: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    reg = root / "research/registry"
    index_path = reg / "PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
    try:
        index = read_json(index_path)
        shards = index.get("configuration_shards", index.get("config_shards", []))
        if not isinstance(shards, list) or not shards:
            raise ValueError("CONFIGURATION_SHARD_INDEX_EMPTY")
        all_ids: set[str] = set()
        pm: dict[str, dict[str, Any]] = {}
        for desc in shards:
            rel = str(desc.get("path", ""))
            path = root / rel
            raw = path.read_bytes()
            if sha256(raw) != desc.get("sha256"):
                raise ValueError(f"CONFIG_SHARD_SHA256_MISMATCH:{rel}")
            payload = json.loads(raw.decode("utf-8"))
            records = payload.get("configs", [])
            expected_n = desc.get("record_count", desc.get("count"))
            if expected_n is not None and len(records) != expected_n:
                raise ValueError(f"CONFIG_SHARD_COUNT_MISMATCH:{rel}")
            for row in records:
                cid = row.get("config_id")
                if not isinstance(cid, str) or cid in all_ids:
                    raise ValueError(f"INVALID_OR_DUPLICATE_CONFIG_ID:{cid}")
                all_ids.add(cid)
                if row.get("method_id") == "PM0001":
                    pm[cid] = row
        if len(all_ids) != 40000:
            raise ValueError(f"CONFIG_REGISTRY_TOTAL_INVALID:{len(all_ids)}")
        if len(pm) != 40:
            raise ValueError(f"PM0001_CONFIG_COUNT_INVALID:{len(pm)}")
        return pm
    except Exception as exc:
        issue(issues, "CONFIG_REGISTRY_RECONSTRUCTION_FAILED", error=f"{type(exc).__name__}:{str(exc)[:500]}")
        return {}


def validate_precheck(
    precheck: Mapping[str, Any],
    config_by_id: Mapping[str, Mapping[str, Any]],
    issues: list[dict[str, Any]],
) -> Counter[str]:
    if precheck.get("schema_version") != "pm0001-data-execution-precheck-r3-v1":
        issue(issues, "PRECHECK_SCHEMA_INVALID")
    if precheck.get("source_csv_sha256") != EXPECTED_DATA_SHA256:
        issue(issues, "PRECHECK_DATA_HASH_MISMATCH")
    if precheck.get("status") != "PASS_PRECHECK_COMPLETE_NO_MODEL_FITTING":
        issue(issues, "PRECHECK_STATUS_NOT_COMPLETE_PASS", status=precheck.get("status"))
    for key in ("model_fitting_performed", "holdout_accessed", "empirical_fit_authorized"):
        if precheck.get(key) is not False:
            issue(issues, "PRECHECK_SCOPE_FLAG_INVALID", field=key, value=precheck.get(key))
    rows = precheck.get("rows")
    if not isinstance(rows, list) or len(rows) != 320 or precheck.get("result_row_count") != 320:
        issue(issues, "PRECHECK_ROW_COUNT_INVALID", rows=len(rows) if isinstance(rows, list) else None)
        return Counter()
    seen: set[tuple[str, str]] = set()
    counts: Counter[str] = Counter()
    for pos, row in enumerate(rows):
        if not isinstance(row, dict):
            issue(issues, "PRECHECK_ROW_NOT_OBJECT", row=pos)
            continue
        cid, fold = str(row.get("config_id", "")), str(row.get("fold_id", ""))
        pair = (cid, fold)
        if pair in seen:
            issue(issues, "PRECHECK_DUPLICATE_PAIR", pair=pair)
        seen.add(pair)
        confrow = config_by_id.get(cid)
        if confrow is None:
            issue(issues, "PRECHECK_UNREGISTERED_CONFIG", pair=pair)
        else:
            conf = confrow.get("configuration", {})
            if row.get("method_id") != "PM0001" or confrow.get("method_id") != "PM0001":
                issue(issues, "PRECHECK_METHOD_MISMATCH", pair=pair)
            if row.get("label_id") != conf.get("label_id"):
                issue(issues, "PRECHECK_LABEL_MISMATCH", pair=pair)
            if row.get("lookback_bars") != conf.get("lookback_bars"):
                issue(issues, "PRECHECK_LOOKBACK_MISMATCH", pair=pair)
            try:
                if float(row.get("c")) != float(conf.get("model_parameters", {}).get("C")):
                    issue(issues, "PRECHECK_PARAMETER_MISMATCH", pair=pair)
            except (TypeError, ValueError):
                issue(issues, "PRECHECK_PARAMETER_MISSING", pair=pair)
        if fold not in FOLDS:
            issue(issues, "PRECHECK_UNKNOWN_FOLD", pair=pair)
        if row.get("status") not in {"PRECHECK_PASS", "BLOCKED_DATA", "BLOCKED_SAMPLE_ELIGIBILITY"}:
            issue(issues, "PRECHECK_NONTERMINAL_OR_TECHNICAL_FAILURE", pair=pair, status=row.get("status"))
        counts[str(row.get("status"))] += 1
        if any(row.get(key) is not False for key in ("empirical_fit_authorized", "model_fitting_performed", "holdout_accessed")):
            issue(issues, "PRECHECK_ROW_SCOPE_FLAG_INVALID", pair=pair)
    expected = {(cid, fold) for cid in config_by_id for fold in FOLDS}
    if seen != expected:
        issue(issues, "PRECHECK_PAIR_COVERAGE_MISMATCH", missing=len(expected-seen), extra=len(seen-expected))
    if precheck.get("status_counts") != dict(sorted(counts.items())):
        issue(issues, "PRECHECK_STATUS_COUNT_MISMATCH", reported=precheck.get("status_counts"), recomputed=dict(sorted(counts.items())))
    if counts.get("PRECHECK_PASS", 0) == 0:
        issue(issues, "NO_PRECHECK_PASS_CELLS")
    return counts


def validate_result_rows(
    result: Mapping[str, Any],
    config_by_id: Mapping[str, Mapping[str, Any]],
    issues: list[dict[str, Any]],
) -> Counter[str]:
    rows = result.get("rows")
    if not isinstance(rows, list) or len(rows) != 320:
        issue(issues, "RESULT_ROW_COUNT_INVALID", rows=len(rows) if isinstance(rows, list) else None)
        return Counter()
    expected = {(cid, fold) for cid in config_by_id for fold in FOLDS}
    seen: set[tuple[str, str]] = set()
    counts: Counter[str] = Counter()
    numeric_ll = ("baseline_log_loss", "candidate_log_loss", "log_loss_improvement")
    bounded = ("brier_score", "balanced_accuracy", "roc_auc", "average_precision")
    for pos, row in enumerate(rows):
        if not isinstance(row, dict):
            issue(issues, "RESULT_ROW_NOT_OBJECT", row=pos)
            continue
        cid, fold = str(row.get("config_id", "")), str(row.get("fold_id", ""))
        pair = (cid, fold)
        if pair in seen:
            issue(issues, "RESULT_DUPLICATE_PAIR", pair=pair)
        seen.add(pair)
        status = row.get("terminal_status")
        counts[str(status)] += 1
        if status not in TERMINAL:
            issue(issues, "RESULT_TERMINAL_STATUS_INVALID", pair=pair, status=status)
        if cid not in config_by_id or fold not in FOLDS:
            issue(issues, "RESULT_UNREGISTERED_PAIR", pair=pair)
        else:
            conf = config_by_id[cid].get("configuration", {})
            if row.get("method_id") != "PM0001" or row.get("label_id") != conf.get("label_id"):
                issue(issues, "RESULT_METHOD_OR_LABEL_MISMATCH", pair=pair)
        offending = sorted(BANNED_ROW_FIELDS.intersection(row))
        if offending:
            issue(issues, "RAW_OR_PER_OBSERVATION_FIELDS_PERSISTED", pair=pair, fields=offending)
        if status in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"}:
            for key in numeric_ll:
                value = row.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                    issue(issues, "EXECUTED_LOGLOSS_METRIC_INVALID", pair=pair, field=key, value=value)
            if all(isinstance(row.get(k), (int, float)) and not isinstance(row.get(k), bool) and math.isfinite(float(row[k])) for k in numeric_ll):
                base, cand, improvement = (float(row[k]) for k in numeric_ll)
                if base <= 0 or cand <= 0:
                    issue(issues, "LOGLOSS_NONPOSITIVE", pair=pair, baseline=base, candidate=cand)
                if abs((base - cand) - improvement) > 1e-10:
                    issue(issues, "LOGLOSS_SIGN_OR_ARITHMETIC_ERROR", pair=pair, baseline=base, candidate=cand, improvement=improvement)
            for key in bounded:
                value = row.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0 <= float(value) <= 1:
                    issue(issues, "BOUNDED_METRIC_INVALID", pair=pair, field=key, value=value)
            if not isinstance(row.get("observed_session_count"), int) or row.get("observed_session_count", 0) <= 0:
                issue(issues, "OBSERVED_SESSION_COUNT_INVALID", pair=pair)
            for key in ("bootstrap_ci_lower", "bootstrap_ci_upper", "raw_p_value", "by_adjusted_p_value"):
                value = row.get(key)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))):
                    issue(issues, "INFERENCE_FIELD_NONFINITE", pair=pair, field=key, value=value)
            lo, hi = row.get("bootstrap_ci_lower"), row.get("bootstrap_ci_upper")
            if lo is not None and hi is not None and float(lo) > float(hi):
                issue(issues, "BOOTSTRAP_CI_ORDER_INVALID", pair=pair, ci=[lo, hi])
            p, ap = row.get("raw_p_value"), row.get("by_adjusted_p_value")
            if p is not None and not 0 < float(p) <= 1:
                issue(issues, "RAW_P_VALUE_OUT_OF_RANGE", pair=pair, p=p)
            if ap is not None and not 0 <= float(ap) <= 1:
                issue(issues, "BY_P_VALUE_OUT_OF_RANGE", pair=pair, p=ap)
            status_inf = row.get("bootstrap_status")
            if status_inf in {"NON_IDENTIFIABLE_DEGENERATE_RESAMPLING", "INCOMPLETE_ELIGIBLE_FOLD_COVERAGE"} and any(row.get(k) is not None for k in ("bootstrap_ci_lower", "bootstrap_ci_upper", "raw_p_value")):
                issue(issues, "NONIDENTIFIABLE_INFERENCE_HAS_NUMERIC_CLAIMS", pair=pair, status=status_inf)
        else:
            if not row.get("failure_reason"):
                issue(issues, "BLOCKED_OR_FAILED_ROW_MISSING_REASON", pair=pair)
            if any(row.get(k) is not None for k in METRIC_FIELDS):
                issue(issues, "BLOCKED_OR_FAILED_ROW_HAS_METRICS", pair=pair)
    if seen != expected:
        issue(issues, "RESULT_PAIR_COVERAGE_MISMATCH", missing=len(expected-seen), extra=len(seen-expected))
    return counts


def audit_bundle(root: Path, request_path: Path) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    root = root.resolve()
    try:
        request = read_json(request_path)
    except Exception as exc:
        return {"decision": "REQUEST_CHANGES", "issues": [{"code": "REVIEW_REQUEST_UNREADABLE", "detail": str(exc)}], "warnings": []}
    if request.get("results_acquired") is not True:
        issue(issues, "RESULTS_ACQUIRED_FLAG_NOT_TRUE")
    source_commit = request.get("tested_source_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", str(source_commit)):
        issue(issues, "TESTED_SOURCE_COMMIT_INVALID", value=source_commit)
    for rel, expected in request.get("changed_source_blobs", {}).items():
        try:
            actual = git_blob_sha1((root / rel).read_bytes())
            if actual != expected:
                issue(issues, "SOURCE_BLOB_PIN_MISMATCH", path=rel, expected=expected, actual=actual)
        except Exception as exc:
            issue(issues, "SOURCE_BLOB_READ_FAILED", path=rel, error=f"{type(exc).__name__}:{str(exc)[:200]}")

    manifest_rel = str(request.get("result_bundle_manifest_path", ""))
    try:
        manifest_path = root / manifest_rel
        manifest_raw = manifest_path.read_bytes()
        expected_manifest_sha = request.get("result_bundle_manifest_sha256")
        if sha256(manifest_raw) != expected_manifest_sha:
            issue(issues, "RESULT_MANIFEST_SHA256_MISMATCH", expected=expected_manifest_sha, actual=sha256(manifest_raw))
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except Exception as exc:
        issue(issues, "RESULT_MANIFEST_READ_FAILED", path=manifest_rel, error=f"{type(exc).__name__}:{str(exc)[:400]}")
        manifest = {}

    if manifest.get("schema_version") != "pm0001-result-freeze-manifest-r3-v1":
        issue(issues, "RESULT_MANIFEST_SCHEMA_INVALID", value=manifest.get("schema_version"))
    if manifest.get("results_acquired") is not True:
        issue(issues, "RESULT_MANIFEST_RESULTS_NOT_ACQUIRED")
    if manifest.get("source_commit") != request.get("source_execution_commit"):
        issue(issues, "MANIFEST_EXECUTION_COMMIT_MISMATCH", manifest=manifest.get("source_commit"), request=request.get("source_execution_commit"))
    if manifest.get("source_data_sha256") != EXPECTED_DATA_SHA256:
        issue(issues, "MANIFEST_DATA_HASH_MISMATCH", value=manifest.get("source_data_sha256"))

    artifact_hashes: dict[str, str] = {}
    for item in manifest.get("artifacts", []):
        rel = str(item.get("path", ""))
        if not rel or rel in artifact_hashes:
            issue(issues, "MANIFEST_ARTIFACT_PATH_DUPLICATE_OR_EMPTY", path=rel)
            continue
        try:
            raw = (root / rel).read_bytes()
            actual = sha256(raw)
            if actual != item.get("sha256"):
                issue(issues, "MANIFEST_ARTIFACT_SHA256_MISMATCH", path=rel, expected=item.get("sha256"), actual=actual)
            if len(raw) != item.get("size_bytes"):
                issue(issues, "MANIFEST_ARTIFACT_SIZE_MISMATCH", path=rel, expected=item.get("size_bytes"), actual=len(raw))
            artifact_hashes[rel] = actual
        except Exception as exc:
            issue(issues, "MANIFEST_ARTIFACT_READ_FAILED", path=rel, error=f"{type(exc).__name__}:{str(exc)[:200]}")

    required_artifacts = {
        "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.json",
        "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.summary.json",
        "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.errors.jsonl",
        "research/gates/PREDICTION_PM0001_DATA_EXECUTION_PRECHECK_R3_2026-10-14.json",
        "research/gates/PREDICTION_PM0001_EXECUTION_GATE_R3_2026-10-14.json",
        "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.csv",
        "research/results/PM0001_PREDICTION_RESULTS_R3_2026-10-14.md",
    }
    if not required_artifacts.issubset(artifact_hashes):
        issue(issues, "REQUIRED_RESULT_ARTIFACTS_MISSING", missing=sorted(required_artifacts-artifact_hashes.keys()))

    config_by_id = reconstruct_pm0001_configs(root, issues)
    try:
        eligibility = read_json(root / "research/gates/PREDICTION_ELIGIBILITY_DISPOSITION_R3_2026-10-13.json")
        records = eligibility.get("records", [])
        pending = {str(x.get("config_id")) for x in records if x.get("disposition") == "ELIGIBLE_PENDING_EXECUTOR_GATE" and x.get("method_id") == "PM0001"}
        if len(pending) != 40 or pending != set(config_by_id):
            issue(issues, "ELIGIBILITY_PENDING_UNIVERSE_MISMATCH", pending_count=len(pending), config_count=len(config_by_id))
        if eligibility.get("empirical_fit_authorized") is not False:
            issue(issues, "ELIGIBILITY_MANIFEST_UNEXPECTEDLY_AUTHORIZES_FIT")
    except Exception as exc:
        issue(issues, "ELIGIBILITY_MANIFEST_READ_FAILED", error=f"{type(exc).__name__}:{str(exc)[:300]}")

    try:
        result = read_json(root / "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.json")
        summary = read_json(root / "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.summary.json")
        precheck = read_json(root / "research/gates/PREDICTION_PM0001_DATA_EXECUTION_PRECHECK_R3_2026-10-14.json")
        gate = read_json(root / "research/gates/PREDICTION_PM0001_EXECUTION_GATE_R3_2026-10-14.json")
        preflight = read_json(root / "research/gates/PREDICTION_DATA_PREFLIGHT_R3_2026-10-13.json")
        pin = read_json(root / "research/data/PREDICTION_DATA_ARTIFACT_PIN_R3_2026-10-13.json")
        feature_report = read_json(root / "research/gates/PREDICTION_FEATURE_CONSTRUCTION_TEST_REPORT_R3A_2026-10-14.json")
        correction = read_json(root / "research/registry/PREDICTION_FEATURE_CONSTRUCTION_CORRECTION_R3A_2026-10-14.json")
        prereg = read_json(root / "research/registry/PREDICTION_PREREGISTRATION_R3_2026-10-13.json")
        errors_raw = (root / "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.errors.jsonl").read_bytes()
        if summary.get("result_file_sha256") != sha256((root / "research/results/PM0001_PREDICTION_SWEEP_R3_2026-10-14.json").read_bytes()):
            issue(issues, "SUMMARY_RESULT_SHA256_MISMATCH")
        if summary.get("errors_jsonl_sha256") != sha256(errors_raw):
            issue(issues, "SUMMARY_ERRORS_SHA256_MISMATCH")
        if summary.get("source_data_sha256") != EXPECTED_DATA_SHA256 or result.get("source_data_sha256") != EXPECTED_DATA_SHA256:
            issue(issues, "RESULT_DATA_HASH_MISMATCH")
        if result.get("precheck_report_sha256") != sha256((root / "research/gates/PREDICTION_PM0001_DATA_EXECUTION_PRECHECK_R3_2026-10-14.json").read_bytes()):
            issue(issues, "RESULT_PRECHECK_SHA256_MISMATCH")
        if result.get("execution_gate_sha256") != sha256((root / "research/gates/PREDICTION_PM0001_EXECUTION_GATE_R3_2026-10-14.json").read_bytes()):
            issue(issues, "RESULT_EXECUTION_GATE_SHA256_MISMATCH")
        for name, obj in (("result", result), ("summary", summary), ("manifest", manifest)):
            if obj.get("source_commit") != request.get("source_execution_commit") and name != "manifest":
                issue(issues, "EXECUTION_SOURCE_COMMIT_MISMATCH", object=name, value=obj.get("source_commit"))
            if str(obj.get("workflow_run_id")) != str(request.get("source_workflow_run_id")):
                issue(issues, "EXECUTION_WORKFLOW_RUN_ID_MISMATCH", object=name, value=obj.get("workflow_run_id"))
        if result.get("results_acquired") is not True or summary.get("results_acquired") is not True:
            issue(issues, "RESULTS_ACQUIRED_FALSE_IN_RESULT_OR_SUMMARY")
        if result.get("holdout_accessed") is not False or result.get("raw_market_rows_emitted") is not False or result.get("per_observation_predictions_persisted") is not False:
            issue(issues, "RESULT_PRIVACY_OR_HOLDOUT_FLAGS_INVALID")
        if result.get("configuration_count") != 40 or result.get("outer_fold_count") != 8 or result.get("terminal_rows_written") != 320 or result.get("expected_terminal_rows") != 320:
            issue(issues, "RESULT_DIMENSIONS_INVALID")
        precheck_counts = validate_precheck(precheck, config_by_id, issues)
        result_counts = validate_result_rows(result, config_by_id, issues)
        if dict(sorted(result_counts.items())) != summary.get("terminal_status_counts"):
            issue(issues, "SUMMARY_TERMINAL_STATUS_COUNTS_MISMATCH", summary=summary.get("terminal_status_counts"), recomputed=dict(sorted(result_counts.items())))
        if result.get("validation", {}).get("complete_expected_coverage") is not True or summary.get("validation", {}).get("complete_expected_coverage") is not True:
            issue(issues, "RESULT_ROW_VALIDATOR_COVERAGE_NOT_PASS")
        if gate.get("status") != "PASS_PM0001_EXECUTION_PRECHECK" or gate.get("empirical_fit_authorized") is not True:
            issue(issues, "EXECUTION_GATE_NOT_PASS")
        if gate.get("source_commit") != request.get("source_execution_commit") or str(gate.get("workflow_run_id")) != str(request.get("source_workflow_run_id")):
            issue(issues, "EXECUTION_GATE_RUN_SCOPE_MISMATCH")
        if gate.get("config_ids") != sorted(config_by_id) or gate.get("expected_result_rows") != 320:
            issue(issues, "EXECUTION_GATE_UNIVERSE_MISMATCH")
        if gate.get("source_data_sha256") != EXPECTED_DATA_SHA256:
            issue(issues, "EXECUTION_GATE_DATA_HASH_MISMATCH")
        if gate.get("precheck_report_sha256") != sha256((root / "research/gates/PREDICTION_PM0001_DATA_EXECUTION_PRECHECK_R3_2026-10-14.json").read_bytes()):
            issue(issues, "EXECUTION_GATE_PRECHECK_SHA256_MISMATCH")
        if preflight.get("canonical_hash_matches") is not True or preflight.get("canonical_uncompressed_csv_sha256") != EXPECTED_DATA_SHA256:
            issue(issues, "DATA_PREFLIGHT_CANONICAL_HASH_NOT_PASS")
        if preflight.get("holdout_accessed") is not False or preflight.get("model_fitting_performed") is not False:
            issue(issues, "DATA_PREFLIGHT_SCOPE_FLAGS_INVALID")
        expected_archive = pin.get("current_derived_artifact", {}).get("archive_sha256")
        if expected_archive != "40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b":
            issue(issues, "ENCRYPTED_ARTIFACT_PIN_MISMATCH", value=expected_archive)
        if feature_report.get("status") != "PASS_FEATURE_CONTRACT_WITH_FITTING_BLOCKED" or feature_report.get("check_count") != 52:
            issue(issues, "FEATURE_CONSTRUCTION_REPORT_NOT_PASS")
        if correction.get("status") != "FROZEN_PRE_RESULTS_IMPLEMENTATION_CORRECTION":
            issue(issues, "FEATURE_CORRECTION_NOT_FROZEN")
        if prereg.get("scope", {}).get("research_horizons") != {"intraday_minutes":[5,15,30,60,120],"positional_exchange_sessions":[1,2,3,5,10]}:
            issue(issues, "PREREGISTERED_HORIZON_SCOPE_MISMATCH")
        if prereg.get("metrics_and_inference", {}).get("bootstrap", {}).get("replicates") != 10000:
            issue(issues, "PREREGISTERED_BOOTSTRAP_REPLICATE_COUNT_MISMATCH")

        # Recompute BY adjustments independently from the frozen raw p-value family, counting non-identifiable tests as p=1.
        families = result.get("multiplicity", {}).get("label_families", {})
        config_labels = {cid: conf.get("configuration", {}).get("label_id") for cid, conf in config_by_id.items()}
        inference_map: dict[str, Mapping[str, Any]] = {}
        for label_id, family in families.items():
            members = family.get("configurations", {})
            expected_members = {cid for cid, label in config_labels.items() if label == label_id}
            if set(members) != expected_members:
                issue(issues, "BY_LABEL_FAMILY_MEMBERSHIP_MISMATCH", label_id=label_id, missing=sorted(expected_members-set(members)), extra=sorted(set(members)-expected_members))
            if family.get("family_size_pm0001_configurations") != len(expected_members) or family.get("q") != 0.05:
                issue(issues, "BY_LABEL_FAMILY_METADATA_MISMATCH", label_id=label_id)
            raw_values: dict[str, float] = {}
            for cid, record in members.items():
                inference_map[cid] = record
                rawp = record.get("raw_p_value")
                raw_values[cid] = float(rawp) if isinstance(rawp, (int,float)) and not isinstance(rawp,bool) and math.isfinite(float(rawp)) and 0 <= float(rawp) <= 1 else 1.0
            recomputed = independent_by_adjustment(raw_values, q=0.05)
            for cid, expected_inf in recomputed.items():
                reported = members[cid]
                if abs(float(reported.get("by_adjusted_p_value", -999)) - expected_inf["by_adjusted_p_value"]) > 1e-10:
                    issue(issues, "BY_ADJUSTED_P_VALUE_MISMATCH", config_id=cid, expected=expected_inf["by_adjusted_p_value"], reported=reported.get("by_adjusted_p_value"))
                if reported.get("reject_at_q_0_05") is not expected_inf["reject_at_q"]:
                    issue(issues, "BY_REJECTION_DECISION_MISMATCH", config_id=cid)
        for row in result.get("rows", []):
            inf = inference_map.get(str(row.get("config_id")))
            if inf and row.get("terminal_status") in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"}:
                for row_key, inf_key in (("raw_p_value","raw_p_value"),("bootstrap_ci_lower","ci_low"),("bootstrap_ci_upper","ci_high"),("by_adjusted_p_value","by_adjusted_p_value")):
                    a, b = row.get(row_key), inf.get(inf_key)
                    if a is None and b is None:
                        continue
                    if not isinstance(a, (int,float)) or not isinstance(b, (int,float)) or abs(float(a)-float(b)) > 1e-10:
                        issue(issues, "RESULT_ROW_INFERENCE_MISMATCH", config_id=row.get("config_id"), field=row_key, row=a, family=b)

        successful_tests = sum(1 for r in result.get("rows", []) if r.get("terminal_status") in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"})
        if successful_tests <= 0:
            issue(issues, "NO_EMPIRICAL_METRIC_ROWS_IN_ACQUIRED_BUNDLE")
        if result_counts.get("FAILED_TECHNICAL", 0) > 0:
            issue(issues, "RESULT_BUNDLE_CONTAINS_TECHNICAL_FAILURES", count=result_counts["FAILED_TECHNICAL"])
        if result_counts.get("BLOCKED_GATE", 0) > 0:
            issue(issues, "RESULT_BUNDLE_CONTAINS_UNEXPECTED_GATE_BLOCKS", count=result_counts["BLOCKED_GATE"])
        families_for_repro = result.get("multiplicity", {}).get("label_families", {})
        any_numeric_raw_p = any(
            isinstance(rec.get("raw_p_value"), (int, float)) and not isinstance(rec.get("raw_p_value"), bool)
            for fam in families_for_repro.values()
            for rec in fam.get("configurations", {}).values()
        )
        if any_numeric_raw_p and not any("inference_session" in p or "bootstrap_input" in p for p in artifact_hashes):
            issue(issues, "BOOTSTRAP_INPUTS_NOT_PUBLISHED",
                  detail="A numerical bootstrap CI/p-value is reported, but the bundle omits the per-session paired loss-delta inputs needed for an independent numeric recomputation.")

    except Exception as exc:
        issue(issues, "RESULT_AUDIT_EXCEPTION", error=f"{type(exc).__name__}:{str(exc)[:600]}")

    decision = "REQUEST_CHANGES" if issues else "PASS_WITH_REPRODUCIBILITY_WARNING" if warnings else "PASS"
    return {
        "schema_version": "pm0001-independent-results-audit-r3-v1",
        "audit": "independent-read-only-pm0001-result-bundle-audit",
        "decision": decision,
        "results_acquired": request.get("results_acquired") is True,
        "source_commit": request.get("source_execution_commit"),
        "tested_source_commit": request.get("tested_source_commit"),
        "workflow_run_id": request.get("source_workflow_run_id"),
        "expected_data_sha256": EXPECTED_DATA_SHA256,
        "configurations_expected": 40,
        "folds_expected": 8,
        "terminal_rows_expected": 320,
        "terminal_status_counts_recomputed": dict(sorted(result_counts.items())) if "result_counts" in locals() else {},
        "precheck_status_counts_recomputed": dict(sorted(precheck_counts.items())) if "precheck_counts" in locals() else {},
        "artifact_count_verified": len(artifact_hashes),
        "issues": issues,
        "warnings": warnings,
        "holdout_accessed_by_auditor": False,
        "market_data_opened_by_auditor": False,
        "model_fitting_performed_by_auditor": False,
        "audit_limitations": [
            "No raw observation features or predictions were read or persisted.",
            "Aggregate metric arithmetic, source pins, config/fold coverage, precheck accounting, and BY adjustments are independently checked.",
            "Exact candidate prediction scores and bootstrap intervals require supporting aggregate inputs; this version flags unavailable bootstrap inputs rather than asserting numerical reproduction."
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--developer-root", type=Path, required=True)
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = audit_bundle(args.developer_root, args.request)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"issues", "warnings"}}, sort_keys=True, indent=2))
    print(json.dumps({"decision": report["decision"], "issue_count": len(report["issues"]), "warning_count": len(report["warnings"]), "issues": report["issues"][:20], "warnings": report["warnings"]}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
