#!/usr/bin/env python3
"""Replace generic nearest-neighbor prose with exact deterministic field contrasts."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "research" / "registry" / "METHOD_REGISTRY_V2_R2.json"
SEMANTIC_FIELDS = (
    "algorithm_family",
    "architecture_or_decision_function",
    "learning_objective",
    "input_representation",
    "feature_construction",
    "inference_operator",
    "inference_definition",
    "target_family",
    "probability_adapter",
    "survival_mapping",
    "causal_information_policy",
)

def records_in(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        records = obj
    elif isinstance(obj, dict):
        keys = [k for k in ("methods", "method_registry", "registry") if isinstance(obj.get(k), list)]
        if len(keys) != 1:
            raise ValueError(f"Expected one method array, got {keys}")
        records = obj[keys[0]]
    else:
        raise ValueError("Method registry must be object/list")
    if not all(isinstance(r, dict) for r in records):
        raise ValueError("Every method must be an object")
    return records

def differs(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    return [field for field in SEMANTIC_FIELDS if a.get(field) != b.get(field)]

def contrast_text(a: dict[str, Any], b: dict[str, Any], fields: list[str]) -> str:
    details = "; ".join(
        f"{field}: {a.get(field)!r} vs {b.get(field)!r}" for field in fields
    )
    return f"Nearest registered method {b['method_id']} differs in {', '.join(fields)} ({details})."

def repair_records(records: list[dict[str, Any]]) -> int:
    if len(records) < 2:
        raise ValueError("At least two methods are required")
    ids = [r.get("method_id") for r in records]
    if any(not isinstance(v, str) or not v for v in ids) or len(set(ids)) != len(ids):
        raise ValueError("Method IDs must be unique non-empty strings")
    changed = 0
    ordered = sorted(records, key=lambda r: r["method_id"])
    for method in ordered:
        candidates = []
        for other in ordered:
            if other["method_id"] == method["method_id"]:
                continue
            delta = differs(method, other)
            candidates.append((len(delta), other["method_id"], other, delta))
        distance, _, neighbor, delta = min(candidates, key=lambda item: (item[0], item[1]))
        if distance == 0:
            raise ValueError(f"Semantically duplicate methods: {method['method_id']} and {neighbor['method_id']}")
        new_text = contrast_text(method, neighbor, delta)
        if method.get("nearest_neighbor_method_id") != neighbor["method_id"] or method.get("nearest_neighbor_contrast") != new_text:
            method["nearest_neighbor_method_id"] = neighbor["method_id"]
            method["nearest_neighbor_contrast"] = new_text
            changed += 1
    return changed

def main() -> int:
    obj = json.loads(MASTER.read_text(encoding="utf-8"))
    records = records_in(obj)
    changed = repair_records(records)
    payload = (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    MASTER.write_bytes(payload)
    print(json.dumps({"methods": len(records), "contrasts_updated": changed, "master": MASTER.relative_to(ROOT).as_posix()}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
