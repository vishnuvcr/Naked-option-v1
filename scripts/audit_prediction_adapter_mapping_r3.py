#!/usr/bin/env python3
"""Read-only audit mapping every registered method/config to a tested family adapter."""
import hashlib, json
from collections import Counter, defaultdict
from pathlib import Path
from prediction_parameter_binding_r3 import bind_configuration, ParameterBindingError

ROOT=Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()
def read_json(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))

FAMILIES = {
 "logistic_regression": ("scripts/prediction_logistic_adapter_r3.py","scripts/test_prediction_logistic_adapter_r3.py"),
 "probit_regression": ("scripts/prediction_probit_adapter_r3.py","scripts/test_prediction_probit_adapter_r3.py"),
 "lda": ("scripts/prediction_discriminant_adapter_r3.py","scripts/test_prediction_discriminant_adapter_r3.py"),
 "qda": ("scripts/prediction_discriminant_adapter_r3.py","scripts/test_prediction_discriminant_adapter_r3.py"),
 "generalized_additive_model": ("scripts/prediction_gam_adapter_r3.py","scripts/test_prediction_gam_adapter_r3.py"),
 "elastic_net_logistic": ("scripts/prediction_elastic_net_logistic_adapter_r3.py","scripts/test_prediction_elastic_net_logistic_adapter_r3.py"),
 "random_forest": ("scripts/prediction_tree_ensemble_adapters_r3.py","scripts/test_prediction_tree_ensemble_adapters_r3.py"),
 "extra_trees": ("scripts/prediction_tree_ensemble_adapters_r3.py","scripts/test_prediction_tree_ensemble_adapters_r3.py"),
 "gradient_boosting": ("scripts/prediction_tree_ensemble_adapters_r3.py","scripts/test_prediction_tree_ensemble_adapters_r3.py"),
 "histogram_gradient_boosting": ("scripts/prediction_tree_ensemble_adapters_r3.py","scripts/test_prediction_tree_ensemble_adapters_r3.py"),
 "kernel_svm": ("scripts/prediction_margin_distance_adapters_r3.py","scripts/test_prediction_margin_distance_adapters_r3.py"),
 "nearest_centroid": ("scripts/prediction_margin_distance_adapters_r3.py","scripts/test_prediction_margin_distance_adapters_r3.py"),
 "knn_density_ratio": ("scripts/prediction_margin_distance_adapters_r3.py","scripts/test_prediction_margin_distance_adapters_r3.py"),
 "hidden_markov_model": ("scripts/prediction_hmm_adapter_r3.py","scripts/test_prediction_hmm_adapter_r3.py"),
 "markov_switching_logit": ("scripts/prediction_markov_switching_logit_r3.py","scripts/test_prediction_markov_switching_logit_r3.py"),
 "bayesian_dynamic_logit": ("scripts/prediction_bayesian_dynamic_logit_r3.py","scripts/test_prediction_bayesian_dynamic_logit_r3.py"),
 "change_point_segment_model": ("scripts/prediction_change_point_adapter_r3.py","scripts/test_prediction_change_point_adapter_r3.py"),
 "temporal_convolution_network": ("scripts/prediction_temporal_convolution_adapter_r3.py","scripts/test_prediction_temporal_convolution_adapter_r3.py"),
 "shallow_mlp": ("scripts/prediction_shallow_mlp_adapter_r3.py","scripts/test_prediction_shallow_mlp_adapter_r3.py"),
}

def main():
    cm=read_json("research/registry/PREDICTION_CONFIG_MANIFEST_R3_2026-10-13.json")
    ci=read_json("research/registry/PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json")
    methods={}; family_counts=Counter(); decision_counts=Counter(); config_counts=Counter(); param_keys=defaultdict(Counter); param_values=defaultdict(lambda: defaultdict(Counter)); binding_counts=Counter(); binding_by_family=defaultdict(Counter); errors=[]
    for sh in ci["shards"]:
        raw=(ROOT/sh["path"]).read_bytes()
        if len(raw)!=sh["bytes"] or sha(raw)!=sh["sha256"]: errors.append("COMPAT_SHARD_INTEGRITY:"+sh["path"]); continue
        rows=json.loads(raw).get("rows",[])
        if len(rows)!=sh["record_count"]: errors.append("COMPAT_SHARD_COUNT:"+sh["path"])
        for r in rows:
            mid=r.get("method_id")
            if mid in methods: errors.append("DUPLICATE_METHOD:"+str(mid))
            methods[mid]=r; family_counts[r.get("algorithm_family")]+=1; decision_counts[r.get("compatibility_decision")]+=1
    configs={}
    for sh in cm["config_shards"]:
        raw=(ROOT/sh["path"]).read_bytes()
        if len(raw)!=sh["byte_count"] or sha(raw)!=sh["sha256"]: errors.append("CONFIG_SHARD_INTEGRITY:"+sh["path"]); continue
        rows=json.loads(raw).get("configs",[])
        if len(rows)!=sh["count"]: errors.append("CONFIG_SHARD_COUNT:"+sh["path"])
        for r in rows:
            mid=r.get("method_id"); cfg=r.get("configuration",{})
            if r.get("config_sha256")!=sha(json.dumps(cfg,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()): errors.append("CONFIG_DIGEST:"+str(r.get("config_id")))
            if r.get("config_id") in configs: errors.append("DUPLICATE_CONFIG:"+str(r.get("config_id")))
            configs[r.get("config_id")]=r; config_counts[mid]+=1
            family=methods.get(mid,{}).get("algorithm_family","UNKNOWN")
            try:
                binding=bind_configuration(cfg,family)
                if binding.supported:
                    binding_counts["BOUND"]+=1; binding_by_family[family]["BOUND"]+=1
                else:
                    reason=binding.reason or "UNSUPPORTED"
                    binding_counts["BLOCKED:"+reason]+=1; binding_by_family[family]["BLOCKED:"+reason]+=1
                    if family!="survival_first_passage":
                        errors.append("UNEXPECTED_PARAMETER_BINDING_BLOCK:"+str(r.get("config_id"))+":"+reason)
                    if methods.get(mid,{}).get("compatibility_decision")!="BLOCK":
                        errors.append("UNIMPLEMENTED_FAMILY_NOT_REGISTRY_BLOCKED:"+str(mid))
            except (ParameterBindingError,TypeError,ValueError) as exc:
                binding_counts["ERROR"]+=1; binding_by_family[family]["ERROR"]+=1
                errors.append("PARAMETER_BINDING:"+str(r.get("config_id"))+":"+str(exc))
            for k,v in cfg.get("model_parameters",{}).items():
                param_keys[family][k]+=1
                param_values[family][k][json.dumps(v,sort_keys=True)]+=1
            if cfg.get("method_id")!=mid: errors.append("CONFIG_METHOD_MISMATCH:"+str(r.get("config_id")))
            if cfg.get("label_id") not in cm.get("configurations_per_label",{}): errors.append("UNKNOWN_LABEL:"+str(r.get("config_id")))
    for mid,r in methods.items():
        fam=r.get("algorithm_family")
        if r.get("compatibility_decision")=="ALLOW_IN_PRINCIPLE":
            if fam not in FAMILIES: errors.append("ALLOW_FAMILY_NO_ADAPTER_MAP:"+str(fam))
            else:
                for path in FAMILIES[fam]:
                    if not (ROOT/path).is_file(): errors.append("MISSING_ADAPTER_OR_TEST:"+path)
        if r.get("eligible_for_empirical_fitting") is not False: errors.append("ELIGIBILITY_FLAG_NOT_FALSE:"+str(mid))
        if r.get("implementation_status")=="TESTER_APPROVED" and r.get("eligible_for_empirical_fitting") is not True:
            errors.append("INCONSISTENT_TESTER_APPROVAL_FLAGS:"+str(mid))
        if config_counts[mid]!=cm["configurations_per_method"]: errors.append("METHOD_CONFIG_COUNT:"+str(mid)+":"+str(config_counts[mid]))
    for mid in config_counts:
        if mid not in methods: errors.append("CONFIG_METHOD_NOT_REGISTERED:"+str(mid))
    if len(methods)!=1000 or len(configs)!=cm["configuration_count"]: errors.append("TOTAL_COUNT_MISMATCH")
    if decision_counts["ALLOW_IN_PRINCIPLE"]!=426 or decision_counts["BLOCK"]!=574: errors.append("DECISION_TOTAL_MISMATCH")
    if binding_counts["BOUND"]!=38000: errors.append("PARAMETER_BINDING_TOTAL_MISMATCH:"+str(binding_counts["BOUND"]))
    if binding_counts["BLOCKED:SURVIVAL_EVENT_TIME_CONTRACT_NOT_IMPLEMENTED"]!=2000:
        errors.append("SURVIVAL_BLOCK_TOTAL_MISMATCH")
    report={
      "schema_version":"prediction-adapter-mapping-audit-r3",
      "status":"PASS_ADAPTER_MAPPING_INVENTORY" if not errors else "FAIL",
      "methods":len(methods),"configurations":len(configs),"families":len(family_counts),
      "decision_counts":dict(decision_counts),"method_config_count_min":min(config_counts.values()) if config_counts else 0,
      "method_config_count_max":max(config_counts.values()) if config_counts else 0,
      "allow_methods_with_adapter_and_test_files":sum(1 for r in methods.values() if r.get("compatibility_decision")=="ALLOW_IN_PRINCIPLE" and r.get("algorithm_family") in FAMILIES and all((ROOT/p).is_file() for p in FAMILIES[r["algorithm_family"]])),
      "family_inventory":{fam:{"methods":family_counts[fam],"allow_in_principle":sum(1 for r in methods.values() if r.get("algorithm_family")==fam and r.get("compatibility_decision")=="ALLOW_IN_PRINCIPLE"),"blocked":sum(1 for r in methods.values() if r.get("algorithm_family")==fam and r.get("compatibility_decision")=="BLOCK"),"model_parameter_keys":sorted(param_keys[fam]),"parameter_values":{k:dict(param_values[fam][k]) for k in sorted(param_values[fam])}} for fam in sorted(family_counts)},
      "empirically_eligible_methods":sum(1 for r in methods.values() if r.get("eligible_for_empirical_fitting") is True),
      "parameter_binding_counts":dict(binding_counts),"parameter_binding_by_family":{k:dict(v) for k,v in sorted(binding_by_family.items())},
      "empirically_eligible_methods":sum(1 for r in methods.values() if r.get("eligible_for_empirical_fitting") is True),
      "empirical_fitting_authorized":False,"market_data_loaded":False,"holdout_accessed":False,
      "errors":errors
    }
    print(json.dumps(report,indent=2,sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=="__main__": main()
