#!/usr/bin/env python3
"""Build a conservative row-level compatibility matrix for prediction registry R2.

Design compatibility is not evidence that the adapter is implemented or tester-approved.
Every row remains execution-blocked in this artifact.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research" / "registry"
METHOD_DIR = REGISTRY / "method_shards"
INDEX_PATH = REGISTRY / "PREDICTION_REGISTRY_SHARD_INDEX_V2_R2.json"
JSON_OUT = REGISTRY / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"
MD_OUT = REGISTRY / "PREDICTION_COMPATIBILITY_MATRIX_R2.md"

METHOD_FIELDS = (
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
REGIME_FAMILIES = {"hidden_markov_model", "markov_switching_logit", "change_point_segment_model"}
PROBABILITY_FAMILIES = {
    "logistic_regression", "probit_regression", "generalized_additive_model",
    "lda", "qda", "elastic_net_logistic", "random_forest", "extra_trees",
    "gradient_boosting", "histogram_gradient_boosting", "kernel_svm",
    "nearest_centroid", "knn_density_ratio", "hidden_markov_model",
    "markov_switching_logit", "bayesian_dynamic_logit", "change_point_segment_model",
    "shallow_mlp", "temporal_convolution_network",
}
UNCERTAINTY_FAMILIES = PROBABILITY_FAMILIES - {"survival_first_passage"}
SURVIVAL_FAMILIES = {"survival_first_passage"}

FAMILY_CONTRACTS: dict[str, dict[str, Any]] = {
    "logistic_regression": {"raw_output": "linear log-odds", "probability_contract": "sigmoid of training-fitted logit; inner-fold-only calibration if calibration is required", "uncertainty_contract": "predictive Bernoulli entropy; abstention cutoff chosen in inner training only", "known_risk": "all transforms and class weights fit on inner training rows only"},
    "probit_regression": {"raw_output": "probit latent score", "probability_contract": "standard-normal CDF of training-fitted score; calibration assessed within inner training folds", "uncertainty_contract": "predictive Bernoulli entropy; abstention cutoff chosen in inner training only", "known_risk": "latent-score scaling and calibration must not use validation rows"},
    "generalized_additive_model": {"raw_output": "additive latent score", "probability_contract": "family-link inverse plus training-only calibration if needed", "uncertainty_contract": "predictive Bernoulli entropy; abstention cutoff chosen in inner training only", "known_risk": "basis and smoothness selection remain inner-training-only"},
    "lda": {"raw_output": "class log-discriminant scores", "probability_contract": "normalized class posterior from training-fitted discriminants; calibration checked inner-fold-only", "uncertainty_contract": "predictive Bernoulli entropy; abstention cutoff chosen in inner training only", "known_risk": "covariance regularization fit in training folds only"},
    "qda": {"raw_output": "class log-discriminant scores", "probability_contract": "normalized class posterior from training-fitted discriminants; calibration checked inner-fold-only", "uncertainty_contract": "predictive Bernoulli entropy; abstention cutoff chosen in inner training only", "known_risk": "class covariance estimates and any regularization fit in training folds only"},
    "elastic_net_logistic": {"raw_output": "regularized linear log-odds", "probability_contract": "sigmoid of train-fitted model; all scaling and penalty selection inner-training-only", "uncertainty_contract": "predictive Bernoulli entropy; abstention cutoff chosen in inner training only", "known_risk": "penalty and class weight cannot be tuned on evaluation rows"},
    "random_forest": {"raw_output": "tree-ensemble class probabilities", "probability_contract": "mean class probability over trees; optional calibration only in inner chronological folds", "uncertainty_contract": "predictive Bernoulli entropy; no claim that it is a complete epistemic interval", "known_risk": "tree count, depth and calibration frozen by config before evaluation"},
    "extra_trees": {"raw_output": "randomized-tree ensemble class probabilities", "probability_contract": "mean class probability over trees; optional calibration only in inner chronological folds", "uncertainty_contract": "predictive Bernoulli entropy; no claim that it is a complete epistemic interval", "known_risk": "tree count, depth and calibration frozen by config before evaluation"},
    "gradient_boosting": {"raw_output": "boosted class score/probability", "probability_contract": "native link output or inner-fold-only probability calibration", "uncertainty_contract": "predictive Bernoulli entropy; does not assert full model uncertainty", "known_risk": "boosting iterations and early stopping determined without outer validation"},
    "histogram_gradient_boosting": {"raw_output": "histogram boosted class score/probability", "probability_contract": "native link output or inner-fold-only probability calibration", "uncertainty_contract": "predictive Bernoulli entropy; does not assert full model uncertainty", "known_risk": "binning, early stopping and all fitted transforms are training-only"},
    "kernel_svm": {"raw_output": "signed decision margin", "probability_contract": "Platt calibration trained on inner-chronological out-of-fold margins only", "uncertainty_contract": "predictive Bernoulli entropy after inner-only calibration", "known_risk": "no probability fit on outer validation/test data"},
    "nearest_centroid": {"raw_output": "signed contrast of class-centroid distances", "probability_contract": "Platt calibration of the signed train-only distance contrast using inner-chronological out-of-fold predictions", "uncertainty_contract": "predictive Bernoulli entropy after inner-only calibration", "known_risk": "centroids/scaling and calibration fit inside training folds only"},
    "knn_density_ratio": {"raw_output": "class-conditional density ratio", "probability_contract": "convert density ratio to posterior using class priors estimated on the same training fold; then calibration diagnostics in inner folds", "uncertainty_contract": "predictive Bernoulli entropy after train-only posterior conversion/calibration", "known_risk": "density bandwidth/neighbour count and priors must be training-only"},
    "hidden_markov_model": {"raw_output": "filtered hidden-state posterior and state-conditional emission/transition quantities", "probability_contract": "compute future directional predictive probability by integrating transition/emission uncertainty over filtered state posterior; do not classify the latent state as the target", "uncertainty_contract": "entropy of the integrated future directional predictive distribution", "known_risk": "filtered state probabilities only; no smoothed/future-informed states"},
    "markov_switching_logit": {"raw_output": "latent-regime posterior plus regime-specific directional probabilities", "probability_contract": "integrate regime-specific directional probabilities over filtered regime posterior", "uncertainty_contract": "entropy of integrated directional predictive distribution; state posterior may be reported separately", "known_risk": "filtering, not smoothing; state count and priors frozen before evaluation"},
    "bayesian_dynamic_logit": {"raw_output": "posterior over time-varying coefficients", "probability_contract": "posterior predictive directional probability integrated over coefficient posterior", "uncertainty_contract": "entropy of posterior predictive directional probability; also report posterior spread when available", "known_risk": "priors and posterior approximation frozen pre-result"},
    "change_point_segment_model": {"raw_output": "causal segment posterior/change-point score and segment-conditional predictions", "probability_contract": "integrate segment-conditional directional forecasts over the causal segment posterior; no retrospectively revised break dates", "uncertainty_contract": "entropy of the integrated directional predictive distribution", "known_risk": "all segment boundaries used at time t must have been detectable by t"},
    "shallow_mlp": {"raw_output": "network class logits", "probability_contract": "softmax/sigmoid followed by calibration only in inner chronological training folds", "uncertainty_contract": "predictive Bernoulli entropy only; ensemble/dropout uncertainty is not assumed", "known_risk": "seed, epoch count, scaling and early stopping rules frozen in config"},
    "temporal_convolution_network": {"raw_output": "causal convolutional network class logits", "probability_contract": "softmax/sigmoid followed by calibration only in inner chronological training folds", "uncertainty_contract": "predictive Bernoulli entropy only; ensemble/dropout uncertainty is not assumed", "known_risk": "strict causal receptive field and chronological inner calibration required"},
    "survival_first_passage": {"raw_output": "discrete-time competing-risk hazards and cumulative incidences", "probability_contract": "not compatible with present fixed-horizon up/down label contract until event, censoring and horizon estimands are reconciled", "uncertainty_contract": "not approved under current directional-class estimand", "known_risk": "BLOCK: first-passage/censoring estimand not preregistered and validated"},
}

OPERATOR_CONTRACTS: dict[str, dict[str, Any]] = {
    "probability_threshold": {"rule": "emit probability plus class using frozen 0.5 threshold", "rationale": "directly matches the directional probability target when probability semantics are valid"},
    "cost_sensitive_threshold": {"rule": "threshold minimizing expected loss under a frozen asymmetric cost matrix", "rationale": "BLOCK: no scientifically justified directional error-cost matrix is pre-registered; trading/economic costs belong to the later strategy gate"},
    "regime_gated_decision": {"rule": "apply a causal regime gate, then directional probability decision", "rationale": "requires a time-available regime posterior or the explicit entropy_regime_state representation and training-only gate threshold"},
    "uncertainty_abstention": {"rule": "abstain on the 20% highest predictive-entropy cases; cutoff estimated only within inner chronological training folds", "rationale": "fixed target coverage makes selective prediction interpretable; also report actual outer-fold coverage and selective log loss"},
    "conformal_set_decision": {"rule": "emit a prediction set with target coverage", "rationale": "BLOCK: temporal calibration/validity argument and executable coverage tests are not frozen"},
}

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_methods() -> tuple[list[dict[str, Any]], str]:
    idx = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if idx.get("method_record_count") != 1000 or idx.get("configuration_record_count") != 8000:
        raise SystemExit("BLOCKED: registry index aggregate counts mismatch")
    methods: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for entry in sorted(idx.get("method_shards", []), key=lambda e: e.get("part", 0)):
        path = ROOT / entry["path"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry.get("sha256") or len(raw) != entry.get("byte_count"):
            raise SystemExit(f"BLOCKED: hash/byte-count mismatch before compatibility build: {entry['path']}")
        obj = json.loads(raw.decode("utf-8"))
        records = obj.get("methods") if isinstance(obj, dict) else None
        if not isinstance(records, list) or len(records) != entry.get("record_count"):
            raise SystemExit(f"BLOCKED: record count mismatch in {entry['path']}")
        for record in records:
            method_id = record.get("method_id") if isinstance(record, dict) else None
            if not isinstance(method_id, str) or method_id in seen_ids:
                raise SystemExit(f"BLOCKED: invalid/duplicate method ID {method_id!r}")
            seen_ids.add(method_id)
            methods.append(record)
    if len(methods) != 1000 or seen_ids != {f"PM{i:04d}" for i in range(1, 1001)}:
        raise SystemExit("BLOCKED: expected exact method IDs PM0001..PM1000")
    index_sha = hashlib.sha256(INDEX_PATH.read_bytes()).hexdigest()
    return methods, index_sha


def classify(method: dict[str, Any]) -> tuple[str, str, str, list[str]]:
    family = method["algorithm_family"]
    rep = method["input_representation"]
    operator = method["inference_operator"]
    if family in SURVIVAL_FAMILIES:
        return "BLOCK", "BLOCKED_SURVIVAL_ESTIMAND", "Fixed-horizon directional up/down labels are not yet reconciled with competing-risk first-passage events, censoring and no-event probability.", ["SURVIVAL_EVENT_ESTIMAND", "CENSORING_AND_COMPETING_RISK_TESTS"]
    if operator == "conformal_set_decision":
        return "BLOCK", "BLOCKED_TEMPORAL_CONFORMAL", "No registered time-series validity argument, chronological calibration protocol, coverage target or executable coverage test is approved.", ["TEMPORAL_CONFORMAL_PROTOCOL", "CONFORMAL_COVERAGE_TESTS"]
    if operator == "cost_sensitive_threshold":
        return "BLOCK", "BLOCKED_UNFROZEN_COST_MATRIX", "Prediction-only study has no pre-registered non-arbitrary asymmetric class-loss matrix; do not substitute option-trading cost assumptions at this stage.", ["DIRECTIONAL_CLASS_LOSS_RATIONALE"]
    if operator == "regime_gated_decision":
        if family in REGIME_FAMILIES:
            return "ALLOW_IN_PRINCIPLE", "CONDITIONAL_REGIME_OUTPUT", "Family can emit a causal filtered regime/segment posterior; gate must use filtering and fold-training-only thresholds, never smoothed states.", ["REGIME_FILTERING_ADAPTER_TESTS", "NO_LOOKAHEAD_STATE_TEST"]
        if rep == "entropy_regime_state":
            return "ALLOW_IN_PRINCIPLE", "CONDITIONAL_CAUSAL_REGIME_FEATURE", "The entropy_regime_state representation declares causal regime features; gate thresholds must be fitted inside inner chronological training folds and frozen before outer validation.", ["REGIME_FEATURE_TIMESTAMP_TEST", "TRAIN_ONLY_GATE_THRESHOLD_TEST"]
        return "BLOCK", "BLOCKED_NO_CAUSAL_GATE_SOURCE", "Method row provides neither a family-specific filtered regime output nor the explicit entropy_regime_state representation needed by this operator.", ["REGIME_OUTPUT_CONTRACT", "REGIME_FEATURE_TIMESTAMP_TEST"]
    if operator == "uncertainty_abstention":
        return "ALLOW_IN_PRINCIPLE", "CONDITIONAL_PREDICTIVE_ENTROPY", "For non-survival directional probability outputs, predictive Bernoulli entropy is defined; the abstention cutoff is the training-only 80th percentile (target 80% coverage) and must be inner-fold-only.", ["PROBABILITY_SEMANTICS_TEST", "TRAIN_ONLY_ABSTENTION_THRESHOLD_TEST", "COVERAGE_AND_SELECTIVE_LOSS_TEST"]
    if operator == "probability_threshold":
        if family not in PROBABILITY_FAMILIES:
            return "BLOCK", "BLOCKED_NO_PROBABILITY_CONTRACT", f"No registered probability adapter for family {family}.", ["FAMILY_PROBABILITY_ADAPTER_TEST"]
        return "ALLOW_IN_PRINCIPLE", "CONDITIONAL_DIRECTIONAL_PROBABILITY", FAMILY_CONTRACTS[family]["probability_contract"], ["FAMILY_PROBABILITY_ADAPTER_TEST", "INNER_FOLD_CALIBRATION_TEST", "PROBABILITY_AND_LOGLOSS_NUMERICAL_TEST"]
    raise SystemExit(f"BLOCKED: unknown inference operator {operator!r} in {method.get('method_id')}")


def main() -> int:
    methods, index_sha = load_methods()
    rows = []
    semantic_counts: Counter[str] = Counter()
    triples: Counter[tuple[str, str, str]] = Counter()
    for m in methods:
        unknown = [k for k in ("algorithm_family", "input_representation", "inference_operator") if not isinstance(m.get(k), str)]
        if unknown:
            raise SystemExit(f"BLOCKED: missing method dimensions for {m.get('method_id')}: {unknown}")
        sem = {k: m.get(k) for k in METHOD_FIELDS}
        fp = digest(sem)
        semantic_counts[fp] += 1
        triples[(m["algorithm_family"], m["input_representation"], m["inference_operator"])] += 1
        decision, code, rationale, tests = classify(m)
        rows.append({
            "method_id": m["method_id"],
            "algorithm_family": m["algorithm_family"],
            "architecture_or_decision_function": m.get("architecture_or_decision_function"),
            "learning_objective": m.get("learning_objective"),
            "input_representation": m["input_representation"],
            "feature_construction": m.get("feature_construction"),
            "inference_operator": m["inference_operator"],
            "inference_definition": m.get("inference_definition"),
            "target_family": m.get("target_family"),
            "compatibility_decision": decision,
            "decision_code": code,
            "rationale": rationale,
            "family_output_contract": FAMILY_CONTRACTS.get(m["algorithm_family"], {"raw_output": "UNDEFINED", "probability_contract": "BLOCKED"}) ,
            "operator_contract": OPERATOR_CONTRACTS[m["inference_operator"]],
            "required_tests": tests,
            "semantic_fingerprint_sha256": fp,
            "source_canonical_identity_sha256": m.get("canonical_identity_sha256"),
            "implementation_status": "NOT_IMPLEMENTED_OR_TESTER_APPROVED",
            "eligible_for_empirical_fitting": False,
        })
    duplicate_semantics = sorted(fp for fp, n in semantic_counts.items() if n > 1)
    duplicate_triples = [{"family": f, "representation": r, "operator": o, "count": n} for (f, r, o), n in triples.items() if n > 1]
    allow = sum(r["compatibility_decision"] == "ALLOW_IN_PRINCIPLE" for r in rows)
    blocked = len(rows) - allow
    family_counts = dict(sorted(Counter(r["algorithm_family"] for r in rows).items()))
    operator_counts = dict(sorted(Counter(r["inference_operator"] for r in rows).items()))
    decision_counts = dict(sorted(Counter(r["compatibility_decision"] for r in rows).items()))
    payload = {
        "schema_version": "prediction-compatibility-matrix-v2-r2",
        "date": "2026-10-12",
        "status": "DRAFT_INDEPENDENT_TESTER_REVIEW_REQUIRED_NO_EMPIRICAL_RUNS",
        "source_method_count": len(methods),
        "source_shard_index_sha256": index_sha,
        "method_count": len(rows),
        "compatibility_allow_in_principle_count": allow,
        "compatibility_block_count": blocked,
        "empirically_eligible_count": 0,
        "empirical_execution_gate": "BLOCKED_PENDING_TESTER_APPROVAL_ADAPTER_TESTS_AND_PREREGISTRATION",
        "semantic_fingerprint_rule": "SHA-256 of canonical UTF-8 sorted compact JSON over declared semantic fields (family, architecture, objective, representation, feature construction, operator, inference definition, target family, probability adapter, survival mapping, causal information policy); method ID and source hash excluded.",
        "semantic_fingerprint_unique_count": len(semantic_counts),
        "duplicate_semantic_fingerprints": duplicate_semantics,
        "duplicate_family_representation_operator_triples": duplicate_triples,
        "family_counts": family_counts,
        "operator_counts": operator_counts,
        "decision_counts": decision_counts,
        "family_output_contracts": FAMILY_CONTRACTS,
        "operator_contracts": OPERATOR_CONTRACTS,
        "required_gate": "A row may be fitted only after its family/operator adapter, causal timestamps, calibration/uncertainty semantics, and numerical tests pass in the independent tester gate. This matrix does not grant execution permission.",
        "rows": rows,
    }
    payload["matrix_sha256"] = digest(payload)
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    counts_md = "\n".join(f"- {name}: {n}" for name, n in decision_counts.items())
    families_md = "\n".join(f"- {name}: {n}" for name, n in family_counts.items())
    operators_md = "\n".join(f"- {name}: {n}" for name, n in operator_counts.items())
    summary = f"""# R2 Compatibility Matrix — row-level conservative audit

**Status: DRAFT / BLOCKED. This document does not authorize empirical fitting.**

- Source shard index SHA-256: `{index_sha}`
- Row-level records: {len(rows)}
- Compatibility-level allow-in-principle (conditional on adapter implementation/tests): {allow}
- Blocked by current compatibility/design deficiencies: {blocked}
- Authorized for empirical fitting: **0**
- Unique semantic fingerprints: {len(semantic_counts)} / {len(rows)}
- Duplicate semantic fingerprints: {len(duplicate_semantics)}
- Duplicate family × representation × operator triples: {len(duplicate_triples)}

## Compatibility decision counts

{counts_md}

## Operator counts

{operators_md}

## Family counts

{families_md}

## Operator rules
- `probability_threshold`: allow in principle only when family-specific directional probability semantics are explicit; test calibration in inner chronological folds.
- `uncertainty_abstention`: predictive Bernoulli entropy, cut at inner-training 80th percentile to target 80% coverage; report selective log loss and coverage.
- `regime_gated_decision`: allow in principle only with a causal filtered regime/segment posterior or the explicit entropy-regime representation; no smoothed/future-informed state.
- `cost_sensitive_threshold`: blocked because no non-arbitrary asymmetric class-loss matrix is preregistered for this prediction-only phase.
- `conformal_set_decision`: blocked until chronological/conformal validity assumptions, calibration split, target coverage and coverage tests are frozen.
- `survival_first_passage`: all methods blocked until the fixed-horizon directional classification target is reconciled with event time, competing-risk incidence, censoring and no-event probability.

## Execution is still prohibited
Even rows marked `ALLOW_IN_PRINCIPLE` have `implementation_status=NOT_IMPLEMENTED_OR_TESTER_APPROVED` and `eligible_for_empirical_fitting=false`. Compatibility is a design screening only. The registry does **not** count all 1,000 Cartesian combinations as validated methods.

## Family output contracts and row-level decisions
The complete machine-readable matrix with each method's rationale, required test IDs, family output contract, semantic fingerprint and gate status is stored in `PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json`.
"""
    MD_OUT.write_text(summary, encoding="utf-8")
    print(json.dumps({
        "method_count": len(rows),
        "compatible_in_principle": allow,
        "blocked": blocked,
        "empirically_eligible": 0,
        "unique_semantic_fingerprints": len(semantic_counts),
        "duplicate_semantic_fingerprints": len(duplicate_semantics),
        "duplicate_triples": len(duplicate_triples),
        "decision_counts": decision_counts,
        "json": JSON_OUT.relative_to(ROOT).as_posix(),
        "markdown": MD_OUT.relative_to(ROOT).as_posix(),
        "source_index_sha256": index_sha,
        "status": "SCIENCE_GATE_STILL_BLOCKED",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
