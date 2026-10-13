"""Strict, fail-closed binding from registry parameters to tested adapter kwargs.

This is a code-contract layer, not a fitting authorization. Every supported family
must declare the exact registered parameter keys, validate the frozen value domain,
and map aliases to the adapter's actual constructor names. Survival/event-time models
remain blocked until a scientifically compatible event-time target is implemented.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Any


class ParameterBindingError(ValueError):
    pass


@dataclass(frozen=True)
class Binding:
    family: str
    parameters: dict[str, Any]
    supported: bool
    reason: str | None = None


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise ParameterBindingError(field.upper() + "_MUST_BE_FINITE_NUMBER")
    return float(value)


def _integer(value, field):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ParameterBindingError(field.upper() + "_MUST_BE_INTEGER")
    return value


def _keys(p, expected, family):
    if set(p) != set(expected):
        missing = sorted(set(expected) - set(p))
        extra = sorted(set(p) - set(expected))
        raise ParameterBindingError(
            "PARAMETER_KEYS_MISMATCH:" + family + ":missing=" + ",".join(missing)
            + ":extra=" + ",".join(extra)
        )


def _choice(value, allowed, field):
    if value not in allowed:
        raise ParameterBindingError(field.upper() + "_UNSUPPORTED_VALUE:" + repr(value))
    return value


def bind_configuration(config: dict[str, Any], family: str) -> Binding:
    if not isinstance(config, dict):
        raise ParameterBindingError("CONFIG_MUST_BE_OBJECT")
    p = config.get("model_parameters", {})
    if not isinstance(p, dict):
        raise ParameterBindingError("MODEL_PARAMETERS_MUST_BE_OBJECT")
    p = dict(p)

    if family == "survival_first_passage":
        return Binding(family, {}, False, "SURVIVAL_EVENT_TIME_CONTRACT_NOT_IMPLEMENTED")

    if family == "bayesian_dynamic_logit":
        _keys(p, {"coefficient_drift"}, family)
        drift = _number(p["coefficient_drift"], "coefficient_drift")
        _choice(drift, {0.001, 0.01}, "coefficient_drift")
        return Binding(family, {"process_variance": drift}, True)

    if family == "change_point_segment_model":
        _keys(p, {"min_segment", "penalty"}, family)
        minimum = _integer(p["min_segment"], "min_segment")
        penalty = _number(p["penalty"], "penalty")
        _choice(minimum, {100, 250}, "min_segment")
        _choice(penalty, {5.0, 20.0}, "penalty")
        return Binding(family, {"min_segment": minimum, "penalty": penalty}, True)

    if family == "elastic_net_logistic":
        _keys(p, {"C", "l1_ratio"}, family)
        c = _number(p["C"], "C")
        ratio = _number(p["l1_ratio"], "l1_ratio")
        _choice(c, {0.1, 1.0}, "C")
        _choice(ratio, {0.25, 0.75}, "l1_ratio")
        return Binding(family, {"c": c, "l1_ratio": ratio}, True)

    if family in {"extra_trees", "random_forest"}:
        _keys(p, {"max_depth", "min_samples_leaf", "n_estimators"}, family)
        depth = _integer(p["max_depth"], "max_depth")
        leaf = _integer(p["min_samples_leaf"], "min_samples_leaf")
        estimators = _integer(p["n_estimators"], "n_estimators")
        _choice(depth, {4, 8}, "max_depth")
        _choice(leaf, {5, 20}, "min_samples_leaf")
        _choice(estimators, {200, 400}, "n_estimators")
        return Binding(family, {"max_depth": depth, "min_samples_leaf": leaf,
                                "n_estimators": estimators}, True)

    if family == "generalized_additive_model":
        _keys(p, {"max_splines"}, family)
        knots = _integer(p["max_splines"], "max_splines")
        _choice(knots, {5, 10}, "max_splines")
        return Binding(family, {"max_splines": knots}, True)

    if family == "gradient_boosting":
        _keys(p, {"learning_rate", "max_depth", "n_estimators"}, family)
        rate = _number(p["learning_rate"], "learning_rate")
        depth = _integer(p["max_depth"], "max_depth")
        estimators = _integer(p["n_estimators"], "n_estimators")
        _choice(rate, {0.03, 0.05}, "learning_rate")
        _choice(depth, {2, 3}, "max_depth")
        _choice(estimators, {100, 250}, "n_estimators")
        return Binding(family, {"learning_rate": rate, "max_depth": depth,
                                "n_estimators": estimators}, True)

    if family == "hidden_markov_model":
        _keys(p, {"covariance", "n_states"}, family)
        _choice(p["covariance"], {"diag"}, "covariance")
        states = _integer(p["n_states"], "n_states")
        _choice(states, {2, 4}, "n_states")
        return Binding(family, {"n_states": states}, True)

    if family == "histogram_gradient_boosting":
        _keys(p, {"l2_regularization", "max_iter", "max_leaf_nodes"}, family)
        regularization = _number(p["l2_regularization"], "l2_regularization")
        iterations = _integer(p["max_iter"], "max_iter")
        leaves = _integer(p["max_leaf_nodes"], "max_leaf_nodes")
        _choice(regularization, {0.1, 1.0}, "l2_regularization")
        _choice(iterations, {100, 250}, "max_iter")
        _choice(leaves, {7, 15}, "max_leaf_nodes")
        return Binding(family, {"l2_regularization": regularization,
                                "max_iter": iterations, "max_leaf_nodes": leaves}, True)

    if family == "kernel_svm":
        _keys(p, {"C", "gamma", "kernel"}, family)
        c = _number(p["C"], "C")
        _choice(c, {0.1, 1.0}, "C")
        gamma = _choice(p["gamma"], {"scale"}, "gamma")
        kernel = _choice(p["kernel"], {"rbf"}, "kernel")
        return Binding(family, {"c": c, "gamma": gamma, "kernel": kernel}, True)

    if family == "knn_density_ratio":
        _keys(p, {"n_neighbors", "weights"}, family)
        neighbors = _integer(p["n_neighbors"], "n_neighbors")
        _choice(neighbors, {15, 45}, "n_neighbors")
        weights = _choice(p["weights"], {"distance"}, "weights")
        return Binding(family, {"n_neighbors": neighbors, "weights": weights}, True)

    if family == "lda":
        _keys(p, {"shrinkage"}, family)
        shrinkage = p["shrinkage"]
        if shrinkage != "auto":
            shrinkage = _number(shrinkage, "shrinkage")
            _choice(shrinkage, {0.1}, "shrinkage")
        return Binding(family, {"kind": "lda", "shrinkage": shrinkage}, True)

    if family == "logistic_regression":
        _keys(p, {"C", "penalty", "solver"}, family)
        c = _number(p["C"], "C")
        _choice(c, {0.1, 1.0}, "C")
        _choice(p["penalty"], {"l2"}, "penalty")
        _choice(p["solver"], {"lbfgs"}, "solver")
        # The adapter hard-codes the verified l2/lbfgs semantics; C is its constructor field.
        return Binding(family, {"c": c}, True)

    if family == "markov_switching_logit":
        _keys(p, {"n_regimes", "transition_prior"}, family)
        regimes = _integer(p["n_regimes"], "n_regimes")
        prior = _integer(p["transition_prior"], "transition_prior")
        _choice(regimes, {2, 3}, "n_regimes")
        _choice(prior, {2, 5}, "transition_prior")
        return Binding(family, {"n_regimes": regimes, "transition_prior": prior}, True)

    if family == "nearest_centroid":
        _keys(p, {"shrink_threshold"}, family)
        threshold = _number(p["shrink_threshold"], "shrink_threshold")
        _choice(threshold, {0.0, 0.2}, "shrink_threshold")
        return Binding(family, {"shrink_threshold": threshold}, True)

    if family == "probit_regression":
        _keys(p, {"prior_scale"}, family)
        scale = _number(p["prior_scale"], "prior_scale")
        _choice(scale, {0.5, 2.0}, "prior_scale")
        return Binding(family, {"prior_scale": scale}, True)

    if family == "qda":
        _keys(p, {"reg_param"}, family)
        regularization = _number(p["reg_param"], "reg_param")
        _choice(regularization, {0.1, 0.5}, "reg_param")
        return Binding(family, {"kind": "qda", "reg_param": regularization}, True)

    if family == "shallow_mlp":
        _keys(p, {"dropout", "hidden_units", "weight_decay"}, family)
        dropout = _number(p["dropout"], "dropout")
        units = _integer(p["hidden_units"], "hidden_units")
        decay = _number(p["weight_decay"], "weight_decay")
        _choice(dropout, {0.2, 0.4}, "dropout")
        _choice(units, {16, 64}, "hidden_units")
        _choice(decay, {0.001, 0.01}, "weight_decay")
        return Binding(family, {"dropout": dropout, "hidden_units": units,
                                "weight_decay": decay}, True)

    if family == "temporal_convolution_network":
        _keys(p, {"channels", "dropout", "kernel_size"}, family)
        channels = _integer(p["channels"], "channels")
        kernel = _integer(p["kernel_size"], "kernel_size")
        dropout = _number(p["dropout"], "dropout")
        _choice(channels, {16, 32}, "channels")
        _choice(kernel, {3, 5}, "kernel_size")
        _choice(dropout, {0.2, 0.4}, "dropout")
        return Binding(family, {"channels": channels, "kernel_size": kernel,
                                "dropout": dropout}, True)

    return Binding(family, {}, False, "UNSUPPORTED_FAMILY_BINDING_NOT_EXPLICITLY_IMPLEMENTED")


def require_supported(config: dict[str, Any], family: str) -> Binding:
    binding = bind_configuration(config, family)
    if not binding.supported:
        raise ParameterBindingError(binding.reason or "UNSUPPORTED_CONFIGURATION")
    return binding
