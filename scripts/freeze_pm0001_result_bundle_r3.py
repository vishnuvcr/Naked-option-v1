#!/usr/bin/env python3
"""Validate and freeze the PM0001 40-config x 8-fold result bundle.

Only fold-level aggregated outcomes are persisted. This script refuses incomplete or
mismatched result universes, changed dataset pins, hash mismatches, and row-level
metric arithmetic errors. It never reads the decrypted market data or fits models.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DATA_SHA256 = "cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204"
FOLD_IDS = tuple(f"F{i:02d}" for i in range(1, 9))
TERMINAL_STATES = {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL", "BLOCKED_DATA", "BLOCKED_GATE", "FAILED_TECHNICAL"}
BANNED_ROW_KEYS = {
    "raw_market_rows", "raw_features", "samples", "y_validation", "probabilities",
    "baseline_probabilities", "validation_indices", "training_indices", "per_observation_predictions",
}


class FreezeError(ValueError):
    """Frozen result-bundle contract violation."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FreezeError(f"REQUIRED_INPUT_MISSING:{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FreezeError(f"INVALID_JSON:{path}") from exc
    if not isinstance(value, dict):
        raise FreezeError(f"JSON_TOP_LEVEL_NOT_OBJECT:{path}")
    return value


def validate_result_contract(
    result: Mapping[str, Any],
    summary: Mapping[str, Any],
    *,
    expected_config_ids: Sequence[str],
    expected_config_specs: Mapping[str, Mapping[str, Any]] | None = None,
    expected_data_sha256: str = EXPECTED_DATA_SHA256,
) -> dict[str, Any]:
    expected_ids = sorted(map(str, expected_config_ids))
    if len(expected_ids) != 40 or len(set(expected_ids)) != 40:
        raise FreezeError(f"EXPECTED_EXACTLY_40_UNIQUE_CONFIG_IDS:{len(expected_ids)}")
    if result.get("schema_version") != "pm0001-result-bundle-r3-v1":
        raise FreezeError("RESULT_BUNDLE_SCHEMA_INVALID")
    if result.get("source_data_sha256") != expected_data_sha256:
        raise FreezeError("RESULT_DATASET_SHA256_MISMATCH")
    if result.get("configuration_count") != 40 or result.get("outer_fold_count") != 8:
        raise FreezeError("RESULT_UNIVERSE_DIMENSIONS_INVALID")
    if result.get("expected_terminal_rows") != 320 or result.get("terminal_rows_written") != 320:
        raise FreezeError("RESULT_TERMINAL_ROW_COUNT_INVALID")
    if result.get("holdout_accessed") is not False or result.get("raw_market_rows_emitted") is not False:
        raise FreezeError("RESULT_PROVENANCE_OR_RAW_DATA_FLAG_INVALID")
    rows = result.get("rows")
    if not isinstance(rows, list) or len(rows) != 320:
        raise FreezeError("RESULT_ROWS_MISSING_OR_INCOMPLETE")
    expected = {(cid, fold) for cid in expected_ids for fold in FOLD_IDS}
    seen: set[tuple[str, str]] = set()
    counts: Counter[str] = Counter()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise FreezeError(f"RESULT_ROW_NOT_OBJECT:{index}")
        offending = BANNED_ROW_KEYS.intersection(row)
        if offending:
            raise FreezeError(f"PER_OBSERVATION_OR_RAW_FIELDS_FORBIDDEN:{index}:{sorted(offending)}")
        pair = (str(row.get("config_id", "")), str(row.get("fold_id", "")))
        if pair in seen:
            raise FreezeError(f"DUPLICATE_RESULT_PAIR:{pair}")
        seen.add(pair)
        if row.get("terminal_status") not in TERMINAL_STATES:
            raise FreezeError(f"INVALID_TERMINAL_STATUS:{pair}:{row.get('terminal_status')}")
        if pair[0] not in expected_ids or pair[1] not in FOLD_IDS:
            raise FreezeError(f"UNREGISTERED_RESULT_PAIR:{pair}")
        if expected_config_specs is not None:
            spec = expected_config_specs.get(pair[0])
            if spec is None:
                raise FreezeError(f"REGISTERED_CONFIG_SPEC_MISSING:{pair[0]}")
            for field in ("label_id", "lookback_bars", "config_sha256"):
                if row.get(field) != spec.get(field):
                    raise FreezeError(f"RESULT_REGISTERED_CONFIG_FIELD_MISMATCH:{pair}:{field}")
            if not isinstance(row.get("c"), (int, float)) or abs(float(row["c"]) - float(spec["c"])) > 1e-12:
                raise FreezeError(f"RESULT_REGISTERED_CONFIG_C_MISMATCH:{pair}")
        counts[str(row["terminal_status"])] += 1
        status = row["terminal_status"]
        for key in ("baseline_log_loss", "candidate_log_loss", "log_loss_improvement"):
            value = row.get(key)
            if status in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"}:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise FreezeError(f"EXECUTED_METRIC_MISSING:{pair}:{key}")
                if not __import__("math").isfinite(float(value)):
                    raise FreezeError(f"EXECUTED_METRIC_NONFINITE:{pair}:{key}")
        if status in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"}:
            if float(row["baseline_log_loss"]) <= 0 or float(row["candidate_log_loss"]) <= 0:
                raise FreezeError(f"LOGLOSS_MUST_BE_POSITIVE:{pair}")
            delta = float(row["baseline_log_loss"]) - float(row["candidate_log_loss"])
            if abs(delta - float(row["log_loss_improvement"])) > 1e-10:
                raise FreezeError(f"LOGLOSS_SIGN_OR_ARITHMETIC_MISMATCH:{pair}")
        elif any(row.get(k) is not None for k in (
            "baseline_log_loss", "candidate_log_loss", "log_loss_improvement",
            "brier_score", "balanced_accuracy", "roc_auc", "average_precision",
        )):
            raise FreezeError(f"NONEXECUTED_ROW_HAS_METRICS:{pair}")

    if seen != expected:
        raise FreezeError(f"RESULT_PAIR_COVERAGE_MISMATCH:missing={len(expected-seen)}:extra={len(seen-expected)}")
    if summary.get("source_data_sha256") != expected_data_sha256:
        raise FreezeError("SUMMARY_DATASET_SHA256_MISMATCH")
    if summary.get("terminal_rows_written") != 320:
        raise FreezeError("SUMMARY_TERMINAL_ROW_COUNT_INVALID")
    if summary.get("terminal_status_counts") != dict(sorted(counts.items())):
        raise FreezeError("SUMMARY_TERMINAL_COUNTS_MISMATCH")
    executed = counts.get("EXECUTED_AUDITED", 0) + counts.get("REJECTED_EMPIRICAL", 0)
    acquired = executed > 0
    if result.get("results_acquired") is not acquired or summary.get("results_acquired") is not acquired:
        raise FreezeError("RESULTS_ACQUIRED_FLAG_MISMATCH")
    if result.get("validation", {}).get("complete_expected_coverage") is not True:
        raise FreezeError("RESULT_ROW_VALIDATOR_DID_NOT_CONFIRM_COMPLETE_COVERAGE")
    status = (
        "PASS_COMPLETE_EMPIRICAL_RESULTS_FROZEN"
        if acquired else "COMPLETE_TERMINAL_ACCOUNTING_NO_EMPIRICAL_FIT"
    )
    return {
        "status": status,
        "results_acquired": acquired,
        "expected_terminal_rows": 320,
        "terminal_rows_written": len(rows),
        "unique_config_fold_pairs": len(seen),
        "terminal_status_counts": dict(sorted(counts.items())),
        "empirical_fit_rows": executed,
        "blocked_or_failed_rows": len(rows) - executed,
        "source_data_sha256": expected_data_sha256,
    }


def _json_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return value


def write_rows_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _json_cell(value) for key, value in row.items()})


def write_report_markdown(
    path: Path, result: Mapping[str, Any], contract: Mapping[str, Any]
) -> None:
    rows = result["rows"]
    by_config: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_config[str(row["config_id"])].append(row)
    inference_by_id: dict[str, Mapping[str, Any]] = {}
    families = result.get("multiplicity", {}).get("label_families", {})
    for family in families.values():
        for cid, inference in family.get("configurations", {}).items():
            inference_by_id[str(cid)] = inference
    lines = [
        "# PM0001 NIFTY 50 Prediction Results — R3",
        "",
        f"- Bundle status: \`{contract['status']}\`",
        f"- Results acquired: \`{str(contract['results_acquired']).lower()}\`",
        f"- Source data SHA-256: \`{contract['source_data_sha256']}\`",
        f"- Execution source commit: \`{result.get('source_commit', 'unknown')}\`",
        f"- Workflow run ID: \`{result.get('workflow_run_id', 'unknown')}\`",
        "- Scope: 40 preregistered PM0001 configurations × 8 chronological outer folds.",
        "- Primary metric: session-weighted out-of-sample log loss; improvement = class-prior baseline minus PM0001.",
        "- Statistical inference: paired 10-session moving-block bootstrap (10,000 replicates), Benjamini–Yekutieli q=0.05 within each label stratum.",
        "- The prior-sign baseline remains null because no definition is frozen in the preregistration; no comparator was invented.",
        "- No untouched holdout was accessed. No raw market rows or per-observation predictions are published.",
        "",
        "## Terminal accounting",
        "",
        "| Terminal status | Count |",
        "|---|---:|",
    ]
    for state, count in sorted(contract["terminal_status_counts"].items()):
        lines.append(f"| {state} | {count} |")
    lines += [
        "",
        "## All registered PM0001 configurations",
        "",
        "Each config is shown; this is not a performance-based model selection or trading-strategy evaluation.",
        "",
        "| Config ID | Label | Lookback | C | Executed folds | Blocked/failed folds | Mean fold log loss | Mean fold improvement | Inference status | Mean session improvement | 95% bootstrap CI | Raw p | BY-adjusted p | BY q=.05 reject |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---|",
    ]
    for cid, group in sorted(by_config.items()):
        executed = [row for row in group if row.get("terminal_status") in {"EXECUTED_AUDITED", "REJECTED_EMPIRICAL"}]
        blocked = len(group) - len(executed)
        label = str(group[0].get("label_id", ""))
        lookback = group[0].get("lookback_bars", "")
        cval = group[0].get("c", "")
        ll = [float(row["candidate_log_loss"]) for row in executed]
        imp = [float(row["log_loss_improvement"]) for row in executed]
        inf = inference_by_id.get(cid, {})
        ci = "NA"
        if inf.get("ci_low") is not None and inf.get("ci_high") is not None:
            ci = f"{float(inf['ci_low']):.6g} to {float(inf['ci_high']):.6g}"
        def num_or_na(v: Any) -> str:
            return "NA" if v is None else f"{float(v):.6g}"
        lines.append(
            f"| {cid} | {label} | {lookback} | {cval} | {len(executed)} | {blocked} | "
            f"{num_or_na(sum(ll)/len(ll) if ll else None)} | {num_or_na(sum(imp)/len(imp) if imp else None)} | "
            f"{inf.get('inferential_status', 'NO_EMPIRICAL_FIT')} | {num_or_na(inf.get('observed_mean_session_improvement'))} | "
            f"{ci} | {num_or_na(inf.get('raw_p_value'))} | {num_or_na(inf.get('by_adjusted_p_value'))} | "
            f"{str(inf.get('reject_at_q_0_05', False)).lower()} |"
        )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "A positive primary effect means lower log loss than the training-fold prevalence baseline. It does not, by itself, establish a tradable edge or an option strategy. Any model conclusions require complete fold coverage, paired uncertainty intervals, multiplicity-aware inference and independent review.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def make_manifest(
    *,
    contract: Mapping[str, Any],
    result_path: Path,
    summary_path: Path,
    errors_path: Path,
    precheck_path: Path,
    gate_path: Path,
    preflight_path: Path,
    feature_report_path: Path,
    csv_path: Path,
    report_path: Path,
    source_commit: str,
    workflow_run_id: str,
) -> dict[str, Any]:
    required_artifacts = [result_path, summary_path, errors_path, csv_path, report_path]
    for path in required_artifacts:
        if not path.is_file():
            raise FreezeError(f"REQUIRED_FROZEN_ARTIFACT_MISSING:{path}")
    # A failed/blocked developer run may legitimately have no execution gate or even
    # no precheck report. Preserve the terminal bundle, but never claim empirical fit.
    artifacts = required_artifacts + [p for p in (precheck_path, gate_path, preflight_path, feature_report_path) if p.is_file()]
    manifest_artifacts = []
    for path in artifacts:
        rel = path.resolve().relative_to(ROOT.resolve()).as_posix()
        manifest_artifacts.append({"path": rel, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return {
        "schema_version": "pm0001-result-freeze-manifest-r3-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        **dict(contract),
        "source_commit": source_commit,
        "workflow_run_id": str(workflow_run_id),
        "holdout_accessed": False,
        "raw_market_rows_emitted": False,
        "per_observation_predictions_persisted": False,
        "artifacts": manifest_artifacts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for option in ("result-bundle", "summary", "errors", "precheck-report", "execution-gate",
                   "preflight-report", "feature-report", "csv", "report-markdown", "manifest"):
        ap.add_argument(f"--{option}", required=True, type=Path)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--workflow-run-id", required=True)
    args = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_commit):
        raise FreezeError("SOURCE_COMMIT_MUST_BE_FULL_GIT_SHA")
    if not str(args.workflow_run_id).isdigit():
        raise FreezeError("WORKFLOW_RUN_ID_MUST_BE_NUMERIC")

    result = load_object(args.result_bundle)
    summary = load_object(args.summary)
    from run_pm0001_data_execution_precheck_r3 import config_rows
    configs = config_rows()
    config_ids = sorted(str(row["config_id"]) for row in configs)
    config_specs = {
        str(item["config_id"]): {
            "label_id": str(item["configuration"]["label_id"]),
            "lookback_bars": int(item["configuration"]["lookback_bars"]),
            "c": float(item["configuration"]["model_parameters"]["C"]),
            "config_sha256": str(item["config_sha256"]),
        }
        for item in configs
    }
    if result.get("source_commit") != args.source_commit:
        raise FreezeError("RESULT_SOURCE_COMMIT_DOES_NOT_MATCH_EXECUTION")
    if str(result.get("workflow_run_id")) != str(args.workflow_run_id):
        raise FreezeError("RESULT_WORKFLOW_RUN_ID_MISMATCH")
    if result.get("source_manifest_sha256") != summary.get("source_manifest_sha256"):
        raise FreezeError("RESULT_SUMMARY_SOURCE_MANIFEST_HASH_MISMATCH")
    if summary.get("result_file_sha256") != sha256_file(args.result_bundle):
        raise FreezeError("SUMMARY_RESULT_FILE_SHA256_MISMATCH")
    if summary.get("errors_jsonl_sha256") != sha256_file(args.errors):
        raise FreezeError("SUMMARY_ERROR_LOG_SHA256_MISMATCH")
    contract = validate_result_contract(result, summary, expected_config_ids=config_ids, expected_config_specs=config_specs)

    from prediction_walkforward_r3 import validate_result_rows
    validation = validate_result_rows(result["rows"], [(cid, fold) for cid in config_ids for fold in FOLD_IDS])
    if validation.get("complete_expected_coverage") is not True:
        raise FreezeError("CANONICAL_RESULT_SCHEMA_VALIDATION_FAILED")
    if args.precheck_report.is_file():
        if sha256_file(args.precheck_report) != result.get("precheck_report_sha256"):
            raise FreezeError("PRECHECK_FILE_HASH_MISMATCH")
    elif contract["results_acquired"]:
        raise FreezeError("EMPIRICAL_RESULTS_REQUIRE_PRECHECK_REPORT")
    if args.preflight_report.is_file():
        preflight_raw = args.preflight_report.read_bytes()
        try:
            preflight_rel = args.preflight_report.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError as exc:
            raise FreezeError("RUN_PREFLIGHT_REPORT_OUTSIDE_REPOSITORY") from exc
        if result.get("preflight_report_path") != preflight_rel:
            raise FreezeError("RESULT_PREFLIGHT_PATH_MISMATCH")
        if result.get("preflight_report_sha256") != sha256_bytes(preflight_raw):
            raise FreezeError("RESULT_PREFLIGHT_SHA256_MISMATCH")
    elif contract["results_acquired"]:
        raise FreezeError("EMPIRICAL_RESULTS_REQUIRE_PREFLIGHT_REPORT")
    if args.execution_gate.is_file():
        if sha256_file(args.execution_gate) != result.get("execution_gate_sha256"):
            raise FreezeError("EXECUTION_GATE_FILE_HASH_MISMATCH")
        if not args.preflight_report.is_file():
            raise FreezeError("EXECUTION_GATE_REQUIRES_PINNED_PREFLIGHT_REPORT")
        gate_doc = load_object(args.execution_gate)
        if not args.feature_report.is_file():
            raise FreezeError("EXECUTION_GATE_REQUIRES_FEATURE_CONSTRUCTION_REPORT")
        feature_raw = args.feature_report.read_bytes()
        preflight_raw = args.preflight_report.read_bytes()
        try:
            preflight_rel = args.preflight_report.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError as exc:
            raise FreezeError("RUN_PREFLIGHT_REPORT_OUTSIDE_REPOSITORY") from exc
        if gate_doc.get("preflight_report_path") != preflight_rel or result.get("preflight_report_path") != preflight_rel:
            raise FreezeError("EXECUTION_GATE_PREFLIGHT_PATH_MISMATCH")
        if gate_doc.get("preflight_report_git_blob_sha1") != git_blob_sha1(preflight_raw):
            raise FreezeError("EXECUTION_GATE_PREFLIGHT_BLOB_PIN_MISMATCH")
        if gate_doc.get("preflight_report_sha256") != sha256_bytes(preflight_raw) or result.get("preflight_report_sha256") != sha256_bytes(preflight_raw):
            raise FreezeError("EXECUTION_GATE_PREFLIGHT_SHA256_MISMATCH")
        if gate_doc.get("feature_construction_report_git_blob_sha1") != git_blob_sha1(feature_raw):
            raise FreezeError("EXECUTION_GATE_FEATURE_REPORT_BLOB_PIN_MISMATCH")
        if gate_doc.get("feature_construction_report_sha256") != sha256_bytes(feature_raw):
            raise FreezeError("EXECUTION_GATE_FEATURE_REPORT_SHA256_MISMATCH")
    elif contract["results_acquired"]:
        raise FreezeError("EMPIRICAL_RESULTS_REQUIRE_EXECUTION_GATE")

    write_rows_csv(args.csv, result["rows"])
    write_report_markdown(args.report_markdown, result, contract)
    manifest = make_manifest(
        contract=contract, result_path=args.result_bundle, summary_path=args.summary,
        errors_path=args.errors, precheck_path=args.precheck_report, gate_path=args.execution_gate,
        preflight_path=args.preflight_report, feature_report_path=args.feature_report,
        csv_path=args.csv, report_path=args.report_markdown,
        source_commit=args.source_commit, workflow_run_id=args.workflow_run_id,
    )
    manifest["result_schema_validation"] = validation
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "artifacts"} |
                     {"artifacts": len(manifest["artifacts"]), "manifest_path": args.manifest.as_posix()}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
