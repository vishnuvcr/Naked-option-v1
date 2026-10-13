"""Fail-closed binding of frozen config semantics to family adapters.

This module does not fit models or change registry eligibility. Unsupported semantics
raise a contract error rather than being silently ignored.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

class ParameterBindingError(ValueError): pass

@dataclass(frozen=True)
class Binding:
    family: str
    parameters: dict[str, Any]
    supported: bool
    reason: str | None = None

def bind_configuration(config: dict[str, Any], family: str) -> Binding:
    if not isinstance(config,dict): raise ParameterBindingError("CONFIG_MUST_BE_OBJECT")
    params=config.get("model_parameters",{})
    if not isinstance(params,dict): raise ParameterBindingError("MODEL_PARAMETERS_MUST_BE_OBJECT")
    p=dict(params)
    if family=="bayesian_dynamic_logit":
        if "coefficient_drift" not in p: raise ParameterBindingError("COEFFICIENT_DRIFT_MISSING")
        if "process_variance" in p: raise ParameterBindingError("AMBIGUOUS_DRIFT_PARAMETER")
        v=p.pop("coefficient_drift")
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not 0<=float(v)<=1:
            raise ParameterBindingError("COEFFICIENT_DRIFT_INVALID")
        p["process_variance"]=float(v)
        return Binding(family,p,True)
    if family=="markov_switching_logit":
        regimes=config.get("n_regimes",p.pop("n_regimes",None))
        transition_prior=p.pop("transition_prior",None)
        if regimes != 2:
            return Binding(family,p,False,"UNSUPPORTED_REGIME_COUNT")
        if transition_prior not in {2,5}:
            return Binding(family,p,False,"TRANSITION_PRIOR_MISSING_OR_UNSUPPORTED")
        return Binding(family,p,False,"TRANSITION_PRIOR_NOT_IMPLEMENTED")
    if family=="hidden_markov_model":
        covariance=p.get("covariance",config.get("covariance"))
        if covariance!="diag": return Binding(family,p,False,"UNSUPPORTED_HMM_COVARIANCE")
        states=p.get("n_states",config.get("n_states"))
        if states not in {2,4}: return Binding(family,p,False,"UNSUPPORTED_HMM_STATE_COUNT")
        return Binding(family,p,True)
    if family=="temporal_convolution_network":
        dropout=p.get("dropout")
        if dropout not in {0.2,0.4}: return Binding(family,p,False,"DROPOUT_VALUE_MISSING_OR_UNSUPPORTED")
        return Binding(family,p,False,"DROPOUT_NOT_IMPLEMENTED")
    if family=="logistic_regression":
        if p.get("penalty")!="l2" or p.get("solver")!="lbfgs" or "C" not in p:
            return Binding(family,p,False,"LOGISTIC_PARAMETER_CONTRACT_UNSUPPORTED")
        c=p["C"]
        if isinstance(c,bool) or not isinstance(c,(int,float)) or c<=0:
            raise ParameterBindingError("LOGISTIC_C_INVALID")
        return Binding(family,p,True)
    return Binding(family,p,False,"UNSUPPORTED_FAMILY_BINDING_NOT_EXPLICITLY_IMPLEMENTED")

def require_supported(config: dict[str, Any], family: str) -> Binding:
    binding=bind_configuration(config,family)
    if not binding.supported:
        raise ParameterBindingError(binding.reason or "UNSUPPORTED_CONFIGURATION")
    return binding
