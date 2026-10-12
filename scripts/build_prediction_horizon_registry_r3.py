#!/usr/bin/env python3
"""Build the complete ten-horizon Phase 8P R3 registry from the frozen R2 design pilot.

This is registry/protocol generation only. It never opens market data, decrypts an artifact,
fits a model, touches the holdout, or selects a method.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "research" / "registry"
DATA_MANIFEST = ROOT / "research" / "data" / "DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json"
DATA_ARTIFACT_PIN = ROOT / "research" / "data" / "PREDICTION_DATA_ARTIFACT_PIN_R3_2026-10-13.json"
SESSION_CALENDAR = ROOT / "research" / "data" / "NSE_EQUITY_TRADING_CALENDAR_2021_2026_R3.json"
R2_CONFIG_MANIFEST = REG / "PREDICTION_CONFIG_MANIFEST_V2_R2.json"
R2_REGISTRY_INDEX = REG / "PREDICTION_REGISTRY_SHARD_INDEX_V2_R2.json"
R2_LABEL_MANIFEST = REG / "PREDICTION_LABEL_MANIFEST_V2_R2.json"
R2_PREREG = REG / "PREDICTION_PREREGISTRATION_V2_R2.json"
METHOD_MASTER = REG / "METHOD_REGISTRY_V2_R2.json"
MATRIX = REG / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"

LABEL_OUT = REG / "PREDICTION_LABEL_MANIFEST_R3_2026-10-13.json"
CONFIG_MANIFEST_OUT = REG / "PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json"
REGISTRY_INDEX_OUT = REG / "PREDICTION_REGISTRY_SHARD_INDEX_R3_2026-10-13.json"
PREREG_OUT = REG / "PREDICTION_PREREGISTRATION_R3_2026-10-13.json"
REPORT_OUT = ROOT / "research" / "gates" / "PREDICTION_HORIZON_REGISTRY_BUILD_REPORT_R3_2026-10-13.json"
CONFIG_DIR = REG / "config_shards_r3"

METHOD_COUNT = 1000
BASE_CONFIG_COUNT = 8000
CONFIG_COUNT = 40000
CONFIGS_PER_SHARD = 100
EXPECTED_R2_LABELS = {"INTRA_30M_UP_DOWN", "POS_1D_UP_DOWN"}
INTRADAY_HORIZONS = [
    ("INTRA_5M_UP_DOWN", 5),
    ("INTRA_15M_UP_DOWN", 15),
    ("INTRA_30M_UP_DOWN", 30),
    ("INTRA_60M_UP_DOWN", 60),
    ("INTRA_120M_UP_DOWN", 120),
]
POSITIONAL_HORIZONS = [
    ("POS_1D_UP_DOWN", 1),
    ("POS_2D_UP_DOWN", 2),
    ("POS_3D_UP_DOWN", 3),
    ("POS_5D_UP_DOWN", 5),
    ("POS_10D_UP_DOWN", 10),
]
ALL_LABEL_IDS = [x[0] for x in INTRADAY_HORIZONS + POSITIONAL_HORIZONS]
HASH_RULE = "SHA-256 over exact committed shard file bytes; UTF-8 JSON bytes, including any final newline"
CONFIG_DIGEST_RULE = "SHA-256 over canonical UTF-8 JSON of the configuration object using sorted keys and compact separators, without a trailing newline"
METHOD_SEMANTIC_FIELDS = (
    "algorithm_family", "architecture_or_decision_function", "learning_objective",
    "input_representation", "feature_construction", "inference_operator",
    "inference_definition", "target_family", "probability_adapter",
    "survival_mapping", "causal_information_policy",
)

def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, value: Any) -> bytes:
    raw = json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw

def safe_config_id_replace(config_id: str, old_label: str, new_label: str) -> str:
    token = f"_{old_label}_"
    if token not in config_id:
        raise ValueError(f"config ID does not contain expected label token {old_label!r}: {config_id}")
    result = config_id.replace(token, f"_{new_label}_", 1)
    if result == config_id and old_label != new_label:
        raise ValueError(f"config ID label replacement did not change ID: {config_id}")
    return result

def load_r2_configs() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    manifest = load_json(R2_CONFIG_MANIFEST)
    idx = load_json(R2_REGISTRY_INDEX)
    declared = manifest.get("config_shards")
    if manifest.get("configuration_count") != BASE_CONFIG_COUNT or not isinstance(declared, list) or len(declared) != 80:
        raise SystemExit("BLOCKED: R2 input must declare exactly 8,000 configurations in 80 verified shards")
    if manifest.get("config_hash_rule") != HASH_RULE:
        raise SystemExit("BLOCKED: R2 manifest does not use exact-file-byte SHA-256")
    all_configs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in sorted(declared, key=lambda e: e.get("path", "")):
        rel = entry.get("path")
        if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise SystemExit(f"BLOCKED: invalid R2 config shard path {rel!r}")
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"BLOCKED: R2 config shard missing: {rel}")
        raw = path.read_bytes()
        if sha256(raw) != entry.get("sha256") or len(raw) != entry.get("byte_count"):
            raise SystemExit(f"BLOCKED: R2 config shard hash/byte-count mismatch: {rel}")
        obj = json.loads(raw.decode("utf-8"))
        rows = obj.get("configs")
        expected_count = entry.get("count", entry.get("record_count"))
        ids = [r.get("config_id") for r in rows] if isinstance(rows, list) else []
        if len(ids) != expected_count or not ids or ids[0] != entry.get("first_id") or ids[-1] != entry.get("last_id"):
            raise SystemExit(f"BLOCKED: R2 config shard count/ID-range mismatch: {rel}")
        for record in rows:
            cid = record.get("config_id")
            if not isinstance(cid, str) or cid in seen:
                raise SystemExit(f"BLOCKED: duplicate or invalid R2 config ID {cid!r}")
            seen.add(cid)
            cfg = record.get("configuration")
            if not isinstance(cfg, dict):
                raise SystemExit(f"BLOCKED: missing configuration object in {cid}")
            # R2's per-record config_sha256 rule is not declared and does not match
            # the R3 canonical configuration-object rule. Do not reinterpret that legacy
            # field as an integrity pin: exact R2 shard bytes are already verified above.
            legacy_digest = record.get("config_sha256")
            if not isinstance(legacy_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", legacy_digest):
                raise SystemExit(f"BLOCKED: malformed legacy R2 config digest: {cid}")
            all_configs.append(record)
    if len(all_configs) != BASE_CONFIG_COUNT or len(seen) != BASE_CONFIG_COUNT:
        raise SystemExit(f"BLOCKED: expected 8,000 unique R2 configurations; found {len(all_configs)}")
    source_labels = {c["configuration"].get("label_id") for c in all_configs}
    if source_labels != EXPECTED_R2_LABELS:
        raise SystemExit(f"BLOCKED: unexpected R2 input labels: {sorted(source_labels)}")
    if idx.get("configuration_record_count") != BASE_CONFIG_COUNT or idx.get("method_record_count") != METHOD_COUNT:
        raise SystemExit("BLOCKED: R2 registry index aggregate counts differ from the frozen source")

    # Independently validate the complete method-shard chain and compatibility matrix
    # before carrying the method IDs into the expanded horizon grid.
    method_master_obj = load_json(METHOD_MASTER)
    if isinstance(method_master_obj, list):
        master_methods = method_master_obj
    else:
        method_arrays = [method_master_obj.get(k) for k in ("methods", "method_registry", "registry") if isinstance(method_master_obj.get(k), list)]
        if len(method_arrays) != 1:
            raise SystemExit("BLOCKED: canonical method master must contain exactly one method array")
        master_methods = method_arrays[0]
    master_by_id = {m.get("method_id"): m for m in master_methods if isinstance(m, dict)}
    if len(master_methods) != METHOD_COUNT or len(master_by_id) != METHOD_COUNT or set(master_by_id) != {f"PM{i:04d}" for i in range(1, METHOD_COUNT + 1)}:
        raise SystemExit("BLOCKED: canonical method master does not have the exact 1,000 unique method IDs")

    method_entries = idx.get("method_shards")
    if not isinstance(method_entries, list) or len(method_entries) != 40:
        raise SystemExit("BLOCKED: R2 registry index must declare 40 method shards")
    shard_method_ids: set[str] = set()
    for entry in sorted(method_entries, key=lambda x: x.get("part", 0)):
        rel = entry.get("path")
        if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise SystemExit(f"BLOCKED: invalid method shard path {rel!r}")
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"BLOCKED: method shard missing: {rel}")
        raw = path.read_bytes()
        if sha256(raw) != entry.get("sha256") or len(raw) != entry.get("byte_count"):
            raise SystemExit(f"BLOCKED: method shard hash/byte-count mismatch: {rel}")
        obj = json.loads(raw.decode("utf-8"))
        rows = obj.get("methods") if isinstance(obj, dict) else None
        if not isinstance(rows, list) or len(rows) != 25 or len(rows) != entry.get("record_count"):
            raise SystemExit(f"BLOCKED: method shard row count mismatch: {rel}")
        ids = [m.get("method_id") for m in rows]
        if ids[0] != entry.get("first_id") or ids[-1] != entry.get("last_id"):
            raise SystemExit(f"BLOCKED: method shard ID-range mismatch: {rel}")
        for m in rows:
            mid = m.get("method_id")
            if mid in shard_method_ids or mid not in master_by_id:
                raise SystemExit(f"BLOCKED: invalid/duplicate method shard ID {mid!r}")
            if m != master_by_id[mid]:
                raise SystemExit(f"BLOCKED: method shard/master record mismatch: {mid}")
            shard_method_ids.add(mid)
    if shard_method_ids != set(master_by_id):
        raise SystemExit("BLOCKED: method shards do not reconstruct the complete canonical method master")

    matrix = load_json(MATRIX)
    matrix_rows = matrix.get("rows") if isinstance(matrix, dict) else None
    if not isinstance(matrix_rows, list) or len(matrix_rows) != METHOD_COUNT:
        raise SystemExit("BLOCKED: compatibility matrix must contain exactly 1,000 method rows")
    matrix_by_id = {r.get("method_id"): r for r in matrix_rows if isinstance(r, dict)}
    if len(matrix_by_id) != METHOD_COUNT or set(matrix_by_id) != set(master_by_id):
        raise SystemExit("BLOCKED: compatibility matrix and method master IDs differ")
    fingerprints: set[str] = set()
    for mid, method in master_by_id.items():
        semantic = {k: method.get(k) for k in METHOD_SEMANTIC_FIELDS}
        fp = sha256(canonical_bytes(semantic))
        row = matrix_by_id[mid]
        if row.get("semantic_fingerprint_sha256") != fp:
            raise SystemExit(f"BLOCKED: compatibility semantic fingerprint does not match source method {mid}")
        fingerprints.add(fp)
        if row.get("eligible_for_empirical_fitting") is not False:
            raise SystemExit(f"BLOCKED: compatibility matrix improperly authorizes empirical fit for {mid}")
    if len(fingerprints) != METHOD_COUNT:
        raise SystemExit("BLOCKED: duplicate method semantic fingerprints in the frozen compatibility matrix")

    method_ids = set(master_by_id)
    for record in all_configs:
        cfg = record["configuration"]
        if record.get("method_id") not in method_ids or cfg.get("method_id") != record.get("method_id"):
            raise SystemExit(f"BLOCKED: config/method linkage mismatch for {record.get('config_id')}")
    return all_configs, manifest, idx

def label_record(label_id: str, horizon_value: int) -> dict[str, Any]:
    if label_id.startswith("INTRA_"):
        return {
            "id": label_id,
            "stratum": "intraday",
            "horizon_minutes": horizon_value,
            "definition": f"Sign of NIFTY spot simple return from the forecast decision spot price to the spot price {horizon_value} minutes later.",
            "return_formula": "(target_spot_price / decision_spot_price) - 1",
            "session_requirement": "Decision timestamp and horizon-end timestamp must both lie inside the same official NSE trading session; exclude any row whose target endpoint crosses the session close; no overnight carry.",
            "target_maturity_rule": f"The target becomes observable only at decision_time + {horizon_value} minutes; training/calibration rows are usable only after that endpoint is known.",
            "purge_exchange_sessions": 1,
            "embargo_exchange_sessions": 1,
            "target_pair_missing_max_fraction": 0.01,
            "flat_treatment": "Exclude if absolute simple return <= 1e-8; report exclusion counts by fold/source.",
            "fold_endpoint_rule": "Score only when the horizon endpoint is within the same outer validation fold and the pinned dataset bounds.",
        }
    return {
        "id": label_id,
        "stratum": "positional",
        "horizon_exchange_sessions": horizon_value,
        "definition": f"Sign of the NIFTY spot simple return from the decision-session close to the close after {horizon_value} complete following official NSE exchange sessions.",
        "return_formula": "(target_spot_close_after_h_sessions / decision_session_close) - 1",
        "session_requirement": "One decision observation at the registered session-close decision time. Use official exchange-session order, not calendar-day offsets.",
        "target_maturity_rule": f"The target becomes observable only after {horizon_value} complete following exchange sessions; any training/calibration target whose endpoint is not yet known at the cutoff is ineligible.",
        "purge_exchange_sessions": horizon_value,
        "embargo_exchange_sessions": horizon_value,
        "target_pair_missing_max_fraction": 0.01,
        "flat_treatment": "Exclude if absolute simple return <= 1e-8; report exclusion counts by fold/source.",
        "fold_endpoint_rule": f"Score only when the close after {horizon_value} following sessions lies inside the same outer validation fold and pinned dataset bounds. Drop the last {horizon_value} decision sessions of each fold from scoring.",
    }

def build_labels(r2_label_manifest: dict[str, Any]) -> dict[str, Any]:
    if not SESSION_CALENDAR.is_file():
        raise SystemExit("BLOCKED: official NSE equity session calendar snapshot is missing")
    calendar = load_json(SESSION_CALENDAR)
    if calendar.get("calendar_id") != "NSE_CAPITAL_MARKET_EQUITIES_2021_2026_R3":
        raise SystemExit("BLOCKED: unexpected NSE exchange calendar identity")
    if calendar.get("timezone") != "Asia/Kolkata" or calendar.get("date_bounds") != {"start": "2021-10-11", "end_inclusive": "2026-10-10"}:
        raise SystemExit("BLOCKED: NSE exchange calendar date range/timezone does not match the frozen dataset")
    sources = {int(x.get("year", 0)) for x in calendar.get("sources", []) if x.get("url") and x.get("circular")}
    if sources != {2021, 2022, 2023, 2024, 2025, 2026}:
        raise SystemExit(f"BLOCKED: calendar must identify annual NSE capital-market circulars for 2021–2026; got {sorted(sources)}")
    holiday_dates = []
    for year in ("2021", "2022", "2023", "2024", "2025", "2026"):
        entries = calendar.get("regular_session_holidays_by_year", {}).get(year)
        if not isinstance(entries, list) or not entries:
            raise SystemExit(f"BLOCKED: NSE calendar has no regular-session holiday list for {year}")
        holiday_dates.extend(item.get("date") for item in entries)
    supplements = calendar.get("supplements", [])
    if not any(x.get("date") == "2026-01-15" and x.get("date_reconciled_from_live_page") is True for x in supplements):
        raise SystemExit("BLOCKED: NSE special weekday closure on 2026-01-15 is missing from calendar supplements")
    if len(holiday_dates) != len(set(holiday_dates)):
        raise SystemExit("BLOCKED: duplicate date in NSE regular-session holiday calendar")
    labels = [label_record(label_id, h) for label_id, h in INTRADAY_HORIZONS + POSITIONAL_HORIZONS]
    label_ids = {x["id"] for x in labels}
    assert label_ids == set(ALL_LABEL_IDS) and len(labels) == 10
    return {
        "schema_version": "prediction-label-manifest-v3-r3",
        "date": "2026-10-13",
        "status": "FROZEN_TEN_HORIZONS_DEVELOPER_VALIDATION_PENDING_NO_EMPIRICAL_RUNS",
        "pinned_data_date_range": {
            "start": "2021-10-11",
            "end": "2026-10-10",
            "source": "DERIVED_DATASET_MANIFEST_R2_RUN_38126168547.json; dataset remains encrypted_only and actual timestamp coverage must pass the developer data preflight before fitting."
        },
        "return_convention": {
            "metric": "simple return",
            "flat_tolerance_abs_simple_return": 1e-8,
            "equality_rule": "flat when absolute simple return <= 1e-8; exclude flat labels from directional two-class scoring and report counts by fold/source.",
            "no_tuning": "Flat tolerance cannot change after any outer-validation metric is computed."
        },
        "labels": labels,
        "common_rules": {
            "timezone": "Asia/Kolkata (IST)",
            "session_calendar": "Use the official NSE Capital Market equities regular-session calendar snapshot pinned below before label generation; reconcile it against observed SPOT session dates and fail closed on contradictions or missing scheduled sessions.",
            "session_calendar_id": calendar["calendar_id"],
            "session_calendar_path": SESSION_CALENDAR.relative_to(ROOT).as_posix(),
            "session_calendar_git_blob_sha1": git_blob_sha1(SESSION_CALENDAR.read_bytes()),
            "session_calendar_sha256": sha256(SESSION_CALENDAR.read_bytes()),
            "regular_session_open": calendar["regular_session"]["open"],
            "regular_session_close": calendar["regular_session"]["close"],
            "decision_time": "Every predictor value must be available at or before the recorded decision timestamp; option/derived predictors must use publication/availability timestamps when distinct from event timestamps.",
            "price_provenance": "NIFTY spot/index observations only for labels; option/derived rows may be predictors but never replace target spot prices.",
            "duplicate_rows": "Deduplicate only byte-identical (instrument, exchange timestamp, interval) rows; conflicting duplicate rows block the affected fold/source.",
            "missing_target_rows": "Exclude and count; block if target-pair missingness exceeds 1% of the session-eligible rows.",
            "flat_tolerance_abs_simple_return": 1e-8,
            "purge_embargo": "Use each label's horizon-specific purge and embargo. Also remove any training label interval intersecting validation. Calibration/inner folds use identical horizon-specific rules.",
            "holdout": "No untouched holdout path/secret is opened in this registry or empirical walk-forward run; fresh-forward remains a separate later gate."
        },
        "source_r2_label_manifest_git_blob_sha1": git_blob_sha1(R2_LABEL_MANIFEST.read_bytes()),
    }

def expand_configs(base_configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for row in base_configs:
        cfg0 = row["configuration"]
        old_label = cfg0["label_id"]
        if old_label == "INTRA_30M_UP_DOWN":
            target_horizons = INTRADAY_HORIZONS
            purge_values = {hid: 1 for hid, _ in INTRADAY_HORIZONS}
            embargo_values = purge_values
        elif old_label == "POS_1D_UP_DOWN":
            target_horizons = POSITIONAL_HORIZONS
            purge_values = {hid: h for hid, h in POSITIONAL_HORIZONS}
            embargo_values = purge_values
        else:
            raise ValueError(f"Unexpected R2 label in config {row.get('config_id')}: {old_label!r}")
        for label_id, horizon_value in target_horizons:
            cfg = json.loads(json.dumps(cfg0))
            cfg["label_id"] = label_id
            if label_id.startswith("INTRA_"):
                cfg["horizon"] = f"{horizon_value} minutes"
                cfg["stratum"] = "intraday"
            else:
                cfg["horizon"] = "1 trading session" if horizon_value == 1 else f"{horizon_value} trading sessions"
                cfg["stratum"] = "positional"
            cfg["purge_exchange_sessions"] = purge_values[label_id]
            cfg["embargo_exchange_sessions"] = embargo_values[label_id]
            cfg["target_maturity_rule"] = (
                f"target endpoint at decision_time + {horizon_value} minutes; require the endpoint to be known before training cutoff"
                if label_id.startswith("INTRA_") else
                f"target close after {horizon_value} following exchange sessions; require target maturity and no overlap with validation"
            )
            cfg["score_only_matured_targets"] = True
            cfg_id = safe_config_id_replace(row["config_id"], old_label, label_id)
            cfg_hash = sha256(canonical_bytes(cfg))
            new_row = {
                "config_id": cfg_id,
                "config_sha256": cfg_hash,
                "configuration": cfg,
                "method_id": row["method_id"],
                "source_r2_config_sha256": row["config_sha256"],
                "status": "NOT_RUN",
            }
            expanded.append(new_row)
    expanded.sort(key=lambda x: (x["config_id"], x["method_id"]))
    ids = [x["config_id"] for x in expanded]
    if len(expanded) != CONFIG_COUNT or len(set(ids)) != CONFIG_COUNT:
        raise SystemExit(f"BLOCKED: expected 40,000 unique expanded configurations; got {len(expanded)}/{len(set(ids))}")
    per_label = Counter(x["configuration"]["label_id"] for x in expanded)
    if per_label != Counter({label_id: 4000 for label_id in ALL_LABEL_IDS}):
        raise SystemExit(f"BLOCKED: expected 4,000 configs per label, got {dict(per_label)}")
    per_method = Counter(x["method_id"] for x in expanded)
    if len(per_method) != METHOD_COUNT or set(per_method.values()) != {40}:
        raise SystemExit("BLOCKED: every one of the 1,000 methods must have 40 registered configs (4 per label × 10 labels)")
    return expanded

def make_manifest(config_shards: list[dict[str, Any]], label_manifest: dict[str, Any], source_index: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "prediction-config-manifest-v3-r3",
        "date": "2026-10-13",
        "configuration_count": CONFIG_COUNT,
        "configurations_per_label": {label: 4000 for label in ALL_LABEL_IDS},
        "configurations_per_method": 40,
        "configurations_per_shard": CONFIGS_PER_SHARD,
        "shard_count": len(config_shards),
        "config_hash_rule": HASH_RULE,
        "config_digest_rule": CONFIG_DIGEST_RULE,
        "source_r2_config_digest_note": "R2 per-record config_sha256 algorithm is undeclared and does not match the R3 canonical configuration-object digest rule; R2 exact shard bytes are validated by manifest SHA-256, and every R3 digest is recomputed under config_digest_rule.",
        "config_shards": config_shards,
        "label_manifest_path": LABEL_OUT.relative_to(ROOT).as_posix(),
        "label_manifest_git_blob_sha1": git_blob_sha1(json_bytes(label_manifest)),
        "source_r2_configuration_count": BASE_CONFIG_COUNT,
        "source_r2_registry_index_git_blob_sha1": git_blob_sha1(R2_REGISTRY_INDEX.read_bytes()),
        "source_r2_method_count": METHOD_COUNT,
        "status": "FROZEN_TEN_HORIZON_REGISTRY_DEVELOPER_VALIDATION_PENDING",
    }

def build_preregistration(label_manifest: dict[str, Any], config_manifest: dict[str, Any],
                          registry_index: dict[str, Any], source_prereg: dict[str, Any]) -> dict[str, Any]:
    p = json.loads(json.dumps(source_prereg))
    data_pin = load_json(DATA_ARTIFACT_PIN)
    source_data_manifest = load_json(DATA_MANIFEST)
    data_manifest_blob = git_blob_sha1(DATA_MANIFEST.read_bytes())
    if data_pin.get("dataset_id") != source_data_manifest.get("dataset_id"):
        raise SystemExit("BLOCKED: R3 encrypted-artifact pin dataset ID mismatch")
    if data_pin.get("source_manifest", {}).get("path") != DATA_MANIFEST.relative_to(ROOT).as_posix():
        raise SystemExit("BLOCKED: R3 encrypted-artifact pin references a different data manifest path")
    if data_pin.get("source_manifest", {}).get("git_blob_sha1") != data_manifest_blob:
        raise SystemExit("BLOCKED: R3 encrypted-artifact pin does not identify the exact derived-data manifest")
    if data_pin.get("source_manifest", {}).get("part_hashes_match_current_derived_artifact") is not True:
        raise SystemExit("BLOCKED: R3 encrypted-artifact pin does not confirm the current artifact part hashes")
    if data_pin.get("verified_summary", {}).get("encrypted_members_checked") != 61 or data_pin.get("verified_summary", {}).get("encrypted_member_hash_or_size_mismatches") != 0:
        raise SystemExit("BLOCKED: R3 encrypted-artifact pin part-integrity summary is invalid")
    if data_pin.get("verified_summary", {}).get("declared_part_row_count_sum") != 8999865:
        raise SystemExit("BLOCKED: R3 encrypted-artifact pin aggregate row count does not match the frozen source")
    if data_pin.get("ancestor_lineage", {}).get("ancestor_artifact_id") != load_json(DATA_MANIFEST).get("parent_artifact_id"):
        raise SystemExit("BLOCKED: R3 artifact pin ancestor ID conflicts with the data manifest")
    if data_pin.get("ancestor_lineage", {}).get("ancestor_artifact_sha256") != load_json(DATA_MANIFEST).get("parent_artifact_sha256"):
        raise SystemExit("BLOCKED: R3 artifact pin ancestor SHA-256 conflicts with the data manifest")
    # Preserve R2's historical pilot restriction as superseded history instead of
    # carrying a contradictory live root-level amendment into the complete R3 scope.
    prior_pilot = p.pop("scope_amendment_2026_10_13", None)
    if prior_pilot is not None:
        p.setdefault("historical_scope_amendments", []).append({
            "amendment_id": "scope_amendment_2026_10_13",
            "status": "SUPERSEDED_BY_COMPLETE_TEN_HORIZON_R3",
            "superseded_on": "2026-10-13",
            "note": "The R2 two-target synthetic/design pilot restriction is historical. R3 reuses the R2 base design but defines all ten required horizons; this history object does not authorize fitting. R3's own developer registry/data-preflight gate remains controlling.",
            "original_amendment": prior_pilot,
        })
    p["schema_version"] = "prediction-preregistration-v3-r3"
    p["date"] = "2026-10-13"
    p["status"] = "FROZEN_TEN_HORIZON_REGISTRY_DEVELOPER_VALIDATION_PENDING_NO_EMPIRICAL_RESULTS"
    p["scope"]["objective"] = "NIFTY 50 directional probability prediction at the complete frozen ten-horizon scope; no option strategy selection in this prediction sub-study."
    p["scope"]["research_horizons"] = {
        "intraday_minutes": [5, 15, 30, 60, 120],
        "positional_exchange_sessions": [1, 2, 3, 5, 10],
    }
    p["scope"]["method_count"] = METHOD_COUNT
    p["scope"]["configuration_count"] = CONFIG_COUNT
    p["scope"]["preregistration_note"] = (
        "R3 freezes the complete ten-horizon prediction scope before empirical metrics are computed. "
        "The encrypted dataset must pass the developer-side data preflight and exact-pinned registry tests before fitting. "
        "Independent tester review is deferred until all planned prediction results are acquired and frozen."
    )
    p["scope"]["prohibited_until_gate_passes"] = [
        "empirical model fitting before developer-side ten-horizon registry QA and data preflight pass",
        "selection using outer-validation results",
        "strategy selection",
        "untouched-holdout access",
        "changing target/fold/feature/compatibility rules after inspecting results",
    ]
    p["scope"]["source_dataset_is_encrypted_only"] = True
    p["scope"]["source_row_count_from_manifest"] = 8999865
    p["scope"]["data_manifest_git_blob_sha1"] = git_blob_sha1(DATA_MANIFEST.read_bytes())
    p["scope"]["session_calendar_path"] = SESSION_CALENDAR.relative_to(ROOT).as_posix()
    p["scope"]["session_calendar_git_blob_sha1"] = git_blob_sha1(SESSION_CALENDAR.read_bytes())
    p["scope"]["session_calendar_sha256"] = sha256(SESSION_CALENDAR.read_bytes())
    p["scope"]["session_calendar_id"] = load_json(SESSION_CALENDAR)["calendar_id"]
    p["scope"]["regular_session_open"] = load_json(SESSION_CALENDAR)["regular_session"]["open"]
    p["scope"]["regular_session_close"] = load_json(SESSION_CALENDAR)["regular_session"]["close"]
    p["scope"]["derived_encrypted_artifact_pin_path"] = DATA_ARTIFACT_PIN.relative_to(ROOT).as_posix()
    p["scope"]["derived_encrypted_artifact_pin_git_blob_sha1"] = git_blob_sha1(DATA_ARTIFACT_PIN.read_bytes())
    p["scope"]["current_derived_artifact_id"] = data_pin["current_derived_artifact"]["artifact_id"]
    p["scope"]["current_derived_artifact_run_id"] = data_pin["current_derived_artifact"]["workflow_run_id"]
    p["scope"]["current_derived_artifact_archive_sha256"] = data_pin["current_derived_artifact"]["archive_sha256"]
    p["scope"]["current_derived_embedded_manifest_sha256"] = data_pin["current_derived_artifact"]["embedded_manifest_sha256"]
    p["scope"]["label_manifest_path"] = LABEL_OUT.relative_to(ROOT).as_posix()
    p["scope"]["label_manifest_git_blob_sha1"] = git_blob_sha1(json_bytes(label_manifest))
    p["scope"]["config_manifest_path"] = CONFIG_MANIFEST_OUT.relative_to(ROOT).as_posix()
    p["scope"]["config_manifest_git_blob_sha1"] = git_blob_sha1(json_bytes(config_manifest))
    p["scope"]["registry_index_path"] = REGISTRY_INDEX_OUT.relative_to(ROOT).as_posix()
    p["scope"]["registry_index_git_blob_sha1"] = git_blob_sha1(json_bytes(registry_index))
    p["scope"]["method_registry_git_blob_sha1"] = git_blob_sha1(METHOD_MASTER.read_bytes())
    p["scope"]["r2_method_config_registry_index_git_blob_sha1"] = git_blob_sha1(R2_REGISTRY_INDEX.read_bytes())
    p["scope"]["compatibility_matrix_git_blob_sha1"] = git_blob_sha1(MATRIX.read_bytes())
    p["scope"]["empirical_execution_gate"] = "BLOCKED_PENDING_DEVELOPER_DATA_PREFLIGHT_AND_TEN_HORIZON_REGISTRY_QA"
    p["scope"]["review_cadence"] = "Independent tester review is deferred until the complete planned result bundle is acquired, frozen, and hashed."
    p["scope"]["r2_pilot_only"] = False
    p["scope"]["r2_pilot_source_preserved"] = True
    p["scope"]["r2_pilot_output_may_select_or_rank_methods"] = False

    labels_obj = {}
    for item in label_manifest["labels"]:
        label_id = item["id"]
        is_intraday = item["stratum"] == "intraday"
        h = item.get("horizon_minutes", item.get("horizon_exchange_sessions"))
        base = p["labels"]["INTRA_30M_UP_DOWN"] if is_intraday else p["labels"]["POS_1D_UP_DOWN"]
        new = json.loads(json.dumps(base))
        new["target"] = item["definition"]
        new["flat_tolerance_abs_simple_return"] = 1e-8
        new["session_rule"] = item["session_requirement"]
        new["missing_target_rule"] = f"Exclude missing decision/target pairs and report counts; BLOCK if more than 1.0% of session-eligible rows lack the target pair."
        new["eligible_timestamp_range"] = ["2021-10-11", "2026-10-10"]
        if is_intraday:
            new.pop("label_horizon", None)
            new.pop("label_horizon_exchange_sessions", None)
            new["label_horizon_minutes"] = h
            new["purge_exchange_sessions"] = 1
            new["embargo_exchange_sessions"] = 1
        else:
            new.pop("label_horizon_minutes", None)
            new["label_horizon"] = f"{h} complete following exchange sessions"
            new["label_horizon_exchange_sessions"] = h
            new["purge_exchange_sessions"] = h
            new["embargo_exchange_sessions"] = h
        new["target_maturity_rule"] = item["target_maturity_rule"]
        new["fold_endpoint_rule"] = item["fold_endpoint_rule"]
        labels_obj[label_id] = new
    p["labels"] = labels_obj

    fold_windows = p["chronological_validation"]["fold_calendar_windows"]
    p["chronological_validation"]["overlap_purge_sessions"] = 10
    p["chronological_validation"]["embargo_sessions"] = 10
    p["chronological_validation"]["purge_rule"] = (
        "For each target, exclude training labels whose target interval intersects the validation period and purge the last label-specific purge_exchange_sessions before validation; "
        "also require every training target endpoint to be observable at the training cutoff."
    )
    p["chronological_validation"]["embargo_rule"] = (
        "For each target, embargo its label-specific embargo_exchange_sessions at the start of each validation window from scored rows; score only targets whose endpoints remain inside that validation fold."
    )
    p["chronological_validation"]["horizon_specific_purge_embargo"] = {
        x["id"]: {"purge_exchange_sessions": x["purge_exchange_sessions"], "embargo_exchange_sessions": x["embargo_exchange_sessions"]}
        for x in label_manifest["labels"]
    }
    p["chronological_validation"]["inner_validation"]["split_policy"] = (
        "Within each outer training window, sort eligible official NSE exchange sessions and form three expanding inner folds "
        "with validation intervals at session-index quantiles [0.40, 0.60), [0.60, 0.80), and [0.80, 1.00). "
        "Each inner fold trains only on sessions strictly earlier than its validation start. Apply the label-specific "
        "purge_exchange_sessions and embargo_exchange_sessions from the R3 label manifest, exclude any training label "
        "whose target interval intersects validation, and require every training target endpoint to be observable at the "
        "training cutoff. No random split or result-driven fold adjustment is permitted."
    )
    p["chronological_validation"]["inner_validation"]["minimum_inner_training_rows"] = {
        label: (10000 if label.startswith("INTRA_") else 150) for label in ALL_LABEL_IDS
    }
    p["chronological_validation"]["inner_validation"]["minimum_inner_validation_rows"] = {
        label: (1000 if label.startswith("INTRA_") else 30) for label in ALL_LABEL_IDS
    }
    p["chronological_validation"]["inner_validation"]["class_support_each_direction_minimum"] = {
        label: (100 if label.startswith("INTRA_") else 10) for label in ALL_LABEL_IDS
    }
    p["sample_eligibility"]["minimum_train_rows"] = {
        label: (20000 if label.startswith("INTRA_") else 250) for label in ALL_LABEL_IDS
    }
    p["sample_eligibility"]["minimum_validation_rows"] = {
        label: (5000 if label.startswith("INTRA_") else 60) for label in ALL_LABEL_IDS
    }
    p["sample_eligibility"]["minimum_class_support_each_direction_per_validation_fold"] = {
        label: (250 if label.startswith("INTRA_") else 20) for label in ALL_LABEL_IDS
    }
    p["sample_eligibility"]["minimum_class_support_each_direction_training"] = {
        label: (1000 if label.startswith("INTRA_") else 50) for label in ALL_LABEL_IDS
    }
    p["fitting_and_calibration"]["inner_validation"] = (
        "Use deterministic expanding inner chronological folds contained wholly in the current outer training window. "
        "For each label, apply its horizon-specific purge and embargo from the R3 label manifest; remove training labels "
        "whose target endpoint is not observable at the training cutoff or overlaps validation. No random split, fixed "
        "one-session purge override, or results-driven fold change is permitted."
    )
    p["fitting_and_calibration"]["minimum_inner_training_rows"] = {
        label: (10000 if label.startswith("INTRA_") else 150) for label in ALL_LABEL_IDS
    }
    p["fitting_and_calibration"]["minimum_inner_validation_rows"] = {
        label: (1000 if label.startswith("INTRA_") else 30) for label in ALL_LABEL_IDS
    }
    p["fitting_and_calibration"]["minimum_class_support_each_direction"] = {
        label: (100 if label.startswith("INTRA_") else 10) for label in ALL_LABEL_IDS
    }
    p["metrics_and_inference"]["bootstrap"]["block_length_exchange_sessions"] = 10
    p["metrics_and_inference"]["bootstrap"]["method"] = (
        "Paired moving-block bootstrap of per-exchange-session baseline-minus-candidate log-loss improvements. "
        "Within each outer fold, sample contiguous ten-session blocks with replacement until the original fold's "
        "session count is reached; never cross fold boundaries and use the same resampled session indices for candidate "
        "and baseline. Center the bootstrap distribution under the null for the two-sided p-value. If the resampling "
        "distribution is degenerate, retain the observed mean descriptively and report null confidence limits and p-value."
    )
    p["metrics_and_inference"]["bootstrap"]["resampling_unit"] = (
        "Exchange sessions within each outer fold; fixed ten-session moving blocks; never cross outer-fold boundaries. "
        "Candidate and baseline share the same sampled session indices. If the empirical bootstrap distribution is degenerate, report descriptive mean only and null CI/p-value."
    )
    p["metrics_and_inference"]["multiplicity"]["stratum_families"] = ALL_LABEL_IDS
    p["metrics_and_inference"]["multiplicity"]["maximum_pre_registered_configurations_per_stratum"] = 1704
    p["metrics_and_inference"]["multiplicity"]["count_basis"] = (
        "At most 426 conditionally compatible methods × 4 configurations per label. Freeze eligible family membership after developer-side compatibility/sample screening and before computing any outer-validation metric."
    )
    p["metrics_and_inference"]["primary_effect_direction"] = "Positive baseline_log_loss - candidate_log_loss favors the candidate."
    p["output_and_failure_rules"]["mandatory_fields"] = list(dict.fromkeys(
        p["output_and_failure_rules"]["mandatory_fields"] + [
            "label_target_endpoint", "purge_sessions", "embargo_sessions", "class_prior_baseline_log_loss",
            "previous_sign_baseline_log_loss", "brier_score", "balanced_accuracy", "roc_auc",
            "average_precision", "calibration_intercept", "calibration_slope", "observed_session_count",
            "bootstrap_status", "bootstrap_replicates", "by_family_id", "source_manifest_sha256",
        ]
    ))
    p["output_and_failure_rules"]["result_acquisition"] = (
        "Preserve every config/fold row including blocked, failed, null and non-significant outputs. "
        "The acquired result bundle is frozen and hash-pinned before one consolidated independent tester review."
    )
    p["output_and_failure_rules"]["encrypted_data"] = (
        "Dataset manifest remains encrypted_only=true. The developer data-preflight workflow must verify every encrypted part hash/size, "
        "decode only in temporary runner storage, verify canonical decoded digest/row totals/date coverage/session schema, and remove plaintext on job exit. "
        "This R3 registry builder does not decrypt or read market data."
    )
    p["gate"] = {
        "registry_build": "COMPLETE_TEN_HORIZON_R3",
        "registry_integrity_gate": "DEVELOPER_SIDE_REQUIRED_BEFORE_DATA_FIT",
        "data_preflight_gate": "DEVELOPER_SIDE_REQUIRED_BEFORE_MODEL_FIT",
        "tester_review_cadence": "AFTER_ALL_PLANNED_PREDICTION_RESULTS_ARE_ACQUIRED_AND_FROZEN",
        "empirical_fitting_authorized_by_builder": False,
        "holdout_access_authorized": False,
    }
    return p

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", type=Path, default=ROOT)
    args = ap.parse_args()
    out_root = args.output_root.resolve()
    if out_root != ROOT.resolve():
        raise SystemExit("BLOCKED: output-root override is disabled so registry artifacts remain inside the repository root")

    base, r2_manifest, r2_index = load_r2_configs()
    r2_labels = load_json(R2_LABEL_MANIFEST)
    r2_prereg = load_json(R2_PREREG)
    data_manifest = load_json(DATA_MANIFEST)
    if data_manifest.get("encrypted_only") is not True or data_manifest.get("rows_preserved") != 8999865:
        raise SystemExit("BLOCKED: unexpected source data manifest identity")
    labels = build_labels(r2_labels)
    expanded = expand_configs(base)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_shards: list[dict[str, Any]] = []
    config_index: list[dict[str, Any]] = []
    expected_names: set[str] = set()
    for start in range(0, len(expanded), CONFIGS_PER_SHARD):
        part = start // CONFIGS_PER_SHARD + 1
        rows = expanded[start:start + CONFIGS_PER_SHARD]
        name = f"PREDICTION_CONFIGS_R3_PART{part:03d}.json"
        path = CONFIG_DIR / name
        payload = {
            "schema_version": "prediction-config-shard-v3-r3",
            "part": part,
            "count": len(rows),
            "configs": rows,
        }
        raw = write_json(path, payload)
        ids = [x["config_id"] for x in rows]
        entry = {
            "part": part,
            "path": path.relative_to(ROOT).as_posix(),
            "byte_count": len(raw),
            "record_count": len(rows),
            "first_id": ids[0],
            "last_id": ids[-1],
            "sha256": sha256(raw),
        }
        config_index.append(entry)
        config_shards.append({
            "path": entry["path"],
            "sha256": entry["sha256"],
            "byte_count": entry["byte_count"],
            "count": entry["record_count"],
            "first_id": entry["first_id"],
            "last_id": entry["last_id"],
        })
        expected_names.add(name)
    for path in CONFIG_DIR.glob("PREDICTION_CONFIGS_R3_PART*.json"):
        if path.name not in expected_names:
            path.unlink()

    # Pin both the exact method registry source and the R2 compatibility screen.
    method_index_entries = r2_index.get("method_shards", [])
    if len(method_index_entries) != 40 or sum(x.get("record_count", 0) for x in method_index_entries) != METHOD_COUNT:
        raise SystemExit("BLOCKED: R2 method shard index is incomplete")
    config_manifest = make_manifest(config_shards, labels, r2_index)
    config_manifest_bytes = json_bytes(config_manifest)
    CONFIG_MANIFEST_OUT.write_bytes(config_manifest_bytes)

    registry_index = {
        "schema_version": "prediction-registry-shard-index-v3-r3",
        "status": "TEN_HORIZON_R3_DEVELOPER_VALIDATION_PENDING",
        "method_record_count": METHOD_COUNT,
        "configuration_record_count": CONFIG_COUNT,
        "configuration_shard_count": len(config_index),
        "configurations_per_method": 40,
        "configurations_per_label": {label: 4000 for label in ALL_LABEL_IDS},
        "method_index_source_path": R2_REGISTRY_INDEX.relative_to(ROOT).as_posix(),
        "method_index_source_git_blob_sha1": git_blob_sha1(R2_REGISTRY_INDEX.read_bytes()),
        "method_shards": method_index_entries,
        "config_shards": config_index,
        "config_manifest_path": CONFIG_MANIFEST_OUT.relative_to(ROOT).as_posix(),
        "config_manifest_git_blob_sha1": git_blob_sha1(config_manifest_bytes),
        "label_manifest_path": LABEL_OUT.relative_to(ROOT).as_posix(),
        "label_manifest_git_blob_sha1": git_blob_sha1(json_bytes(labels)),
        "compatibility_matrix_path": MATRIX.relative_to(ROOT).as_posix(),
        "compatibility_matrix_git_blob_sha1": git_blob_sha1(MATRIX.read_bytes()),
    }
    registry_index_bytes = json_bytes(registry_index)
    REGISTRY_INDEX_OUT.write_bytes(registry_index_bytes)
    label_bytes = json_bytes(labels)
    LABEL_OUT.write_bytes(label_bytes)
    prereg = build_preregistration(labels, config_manifest, registry_index, r2_prereg)
    prereg_bytes = json_bytes(prereg)
    PREREG_OUT.write_bytes(prereg_bytes)

    counts = Counter(x["configuration"]["label_id"] for x in expanded)
    report = {
        "schema_version": 1,
        "build": "phase-08p-complete-ten-horizon-registry-r3",
        "date": "2026-10-13",
        "status": "BUILT_PENDING_DEVELOPER_TESTS_AND_DATA_PREFLIGHT",
        "source": {
            "r2_config_manifest_git_blob_sha1": git_blob_sha1(R2_CONFIG_MANIFEST.read_bytes()),
            "r2_registry_index_git_blob_sha1": git_blob_sha1(R2_REGISTRY_INDEX.read_bytes()),
            "r2_label_manifest_git_blob_sha1": git_blob_sha1(R2_LABEL_MANIFEST.read_bytes()),
            "r2_preregistration_git_blob_sha1": git_blob_sha1(R2_PREREG.read_bytes()),
            "data_manifest_git_blob_sha1": git_blob_sha1(DATA_MANIFEST.read_bytes()),
            "session_calendar_git_blob_sha1": git_blob_sha1(SESSION_CALENDAR.read_bytes()),
            "session_calendar_sha256": sha256(SESSION_CALENDAR.read_bytes()),
            "data_artifact_pin_git_blob_sha1": git_blob_sha1(DATA_ARTIFACT_PIN.read_bytes()),
            "current_derived_artifact_id": load_json(DATA_ARTIFACT_PIN)["current_derived_artifact"]["artifact_id"],
            "current_derived_artifact_archive_sha256": load_json(DATA_ARTIFACT_PIN)["current_derived_artifact"]["archive_sha256"],
            "compatibility_matrix_git_blob_sha1": git_blob_sha1(MATRIX.read_bytes()),
            "r2_config_record_digest_rule": "UNDECLARED_LEGACY_FIELD; exact source shard bytes are verified instead",
            "r3_config_record_digest_rule": CONFIG_DIGEST_RULE,
        },
        "output_git_blob_sha1": {
            LABEL_OUT.relative_to(ROOT).as_posix(): git_blob_sha1(label_bytes),
            CONFIG_MANIFEST_OUT.relative_to(ROOT).as_posix(): git_blob_sha1(config_manifest_bytes),
            REGISTRY_INDEX_OUT.relative_to(ROOT).as_posix(): git_blob_sha1(registry_index_bytes),
            PREREG_OUT.relative_to(ROOT).as_posix(): git_blob_sha1(prereg_bytes),
        },
        "method_count": METHOD_COUNT,
        "configuration_count": len(expanded),
        "configuration_shard_count": len(config_index),
        "configurations_per_label": dict(sorted(counts.items())),
        "configurations_per_method": 40,
        "empirical_fitting_performed": False,
        "market_data_opened": False,
        "holdout_accessed": False,
        "next_developer_steps": [
            "Run developer-side deterministic registry integrity tests.",
            "Run developer-side data preflight to verify real timestamp coverage, official exchange-session calendar, missingness, target pairs and class support for every label/fold.",
            "Run the frozen empirical prediction workload without consulting the untouched holdout and preserve every status row.",
            "Freeze/hash the complete results bundle and only then submit the formal tester review request.",
        ],
    }
    write_json(REPORT_OUT, report)
    print(json.dumps({
        "status": report["status"],
        "methods": METHOD_COUNT,
        "configs": len(expanded),
        "config_shards": len(config_index),
        "label_counts": dict(sorted(counts.items())),
        "empirical_fitting": False,
        "market_data_opened": False,
        "holdout_accessed": False,
        "report": REPORT_OUT.relative_to(ROOT).as_posix(),
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
