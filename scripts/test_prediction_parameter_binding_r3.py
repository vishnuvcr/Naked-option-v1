"""Synthetic-only tests of strict registry-to-adapter parameter binding."""
import unittest

from prediction_parameter_binding_r3 import (
    bind_configuration, require_supported, ParameterBindingError,
)
from prediction_bayesian_dynamic_logit_r3 import BayesianDynamicLogitAdapter
from prediction_change_point_adapter_r3 import ChangePointSegmentProbabilityAdapter
from prediction_elastic_net_logistic_adapter_r3 import ElasticNetLogisticProbabilityAdapter
from prediction_discriminant_adapter_r3 import DiscriminantProbabilityAdapter
from prediction_gam_adapter_r3 import GeneralizedAdditiveProbabilityAdapter
from prediction_tree_ensemble_adapters_r3 import (
    ExtraTreesProbabilityAdapter, RandomForestProbabilityAdapter,
    GradientBoostingProbabilityAdapter, HistGradientBoostingProbabilityAdapter,
)
from prediction_hmm_adapter_r3 import GaussianHMMDirectionalAdapter
from prediction_margin_distance_adapters_r3 import (
    KernelSVMScoreAdapter, KNNDensityRatioScoreAdapter, NearestCentroidScoreAdapter,
)
from prediction_logistic_adapter_r3 import LogisticProbabilityAdapter
from prediction_markov_switching_logit_r3 import MarkovSwitchingLogitAdapter
from prediction_probit_adapter_r3 import ProbitProbabilityAdapter
from prediction_shallow_mlp_adapter_r3 import ShallowMLPProbabilityAdapter
from prediction_temporal_convolution_adapter_r3 import TemporalConvolutionAdapter


class ParameterBindingTests(unittest.TestCase):
    def test_all_supported_family_fields_bind_to_actual_adapter_constructors(self):
        cases = [
            ("bayesian_dynamic_logit", {"coefficient_drift": 0.01},
             {"process_variance": 0.01}, BayesianDynamicLogitAdapter),
            ("change_point_segment_model", {"min_segment": 250, "penalty": 20},
             {"min_segment": 250, "penalty": 20.0}, ChangePointSegmentProbabilityAdapter),
            ("elastic_net_logistic", {"C": 0.1, "l1_ratio": 0.75},
             {"c": 0.1, "l1_ratio": 0.75}, ElasticNetLogisticProbabilityAdapter),
            ("extra_trees", {"max_depth": 8, "min_samples_leaf": 20, "n_estimators": 400},
             {"max_depth": 8, "min_samples_leaf": 20, "n_estimators": 400}, ExtraTreesProbabilityAdapter),
            ("generalized_additive_model", {"max_splines": 10},
             {"max_splines": 10}, GeneralizedAdditiveProbabilityAdapter),
            ("gradient_boosting", {"learning_rate": 0.03, "max_depth": 3, "n_estimators": 250},
             {"learning_rate": 0.03, "max_depth": 3, "n_estimators": 250}, GradientBoostingProbabilityAdapter),
            ("hidden_markov_model", {"covariance": "diag", "n_states": 4},
             {"n_states": 4}, GaussianHMMDirectionalAdapter),
            ("histogram_gradient_boosting", {"l2_regularization": 0.1, "max_iter": 250, "max_leaf_nodes": 15},
             {"l2_regularization": 0.1, "max_iter": 250, "max_leaf_nodes": 15}, HistGradientBoostingProbabilityAdapter),
            ("kernel_svm", {"C": 1, "gamma": "scale", "kernel": "rbf"},
             {"c": 1.0, "gamma": "scale", "kernel": "rbf"}, KernelSVMScoreAdapter),
            ("knn_density_ratio", {"n_neighbors": 45, "weights": "distance"},
             {"n_neighbors": 45, "weights": "distance"}, KNNDensityRatioScoreAdapter),
            ("lda", {"shrinkage": "auto"},
             {"kind": "lda", "shrinkage": "auto"}, DiscriminantProbabilityAdapter),
            ("logistic_regression", {"C": 1, "penalty": "l2", "solver": "lbfgs"},
             {"c": 1.0}, LogisticProbabilityAdapter),
            ("markov_switching_logit", {"n_regimes": 3, "transition_prior": 5},
             {"n_regimes": 3, "transition_prior": 5}, MarkovSwitchingLogitAdapter),
            ("nearest_centroid", {"shrink_threshold": 0.2},
             {"shrink_threshold": 0.2}, NearestCentroidScoreAdapter),
            ("probit_regression", {"prior_scale": 2},
             {"prior_scale": 2.0}, ProbitProbabilityAdapter),
            ("qda", {"reg_param": 0.5},
             {"kind": "qda", "reg_param": 0.5}, DiscriminantProbabilityAdapter),
            ("random_forest", {"max_depth": 4, "min_samples_leaf": 5, "n_estimators": 200},
             {"max_depth": 4, "min_samples_leaf": 5, "n_estimators": 200}, RandomForestProbabilityAdapter),
            ("shallow_mlp", {"dropout": 0.4, "hidden_units": 64, "weight_decay": 0.01},
             {"dropout": 0.4, "hidden_units": 64, "weight_decay": 0.01}, ShallowMLPProbabilityAdapter),
            ("temporal_convolution_network", {"channels": 32, "dropout": 0.4, "kernel_size": 5},
             {"channels": 32, "kernel_size": 5, "dropout": 0.4}, TemporalConvolutionAdapter),
        ]
        self.assertEqual(len(cases), 19)
        for family, raw_parameters, expected, adapter_cls in cases:
            with self.subTest(family=family):
                binding = bind_configuration({"model_parameters": raw_parameters}, family)
                self.assertTrue(binding.supported, binding.reason)
                self.assertEqual(binding.parameters, expected)
                # Constructor acceptance plus field equality proves names/values are consumed.
                adapter = adapter_cls(**binding.parameters)
                for name, value in expected.items():
                    self.assertEqual(getattr(adapter, name), value)

    def test_registered_transition_prior_domain_and_family_support(self):
        for regimes in (2, 3):
            for prior in (2, 5):
                b = bind_configuration({"model_parameters": {
                    "n_regimes": regimes, "transition_prior": prior,
                }}, "markov_switching_logit")
                self.assertTrue(b.supported)
                self.assertEqual(b.parameters, {"n_regimes": regimes, "transition_prior": prior})
        self.assertFalse(bind_configuration({"model_parameters": {
            "baseline_bins": 5, "hazard_penalty": 0.1,
        }}, "survival_first_passage").supported)

    def test_temporal_dropout_all_registered_values_supported(self):
        for dropout in (0.2, 0.4):
            b = bind_configuration({"model_parameters": {
                "channels": 16, "kernel_size": 3, "dropout": dropout,
            }}, "temporal_convolution_network")
            self.assertTrue(b.supported)
            self.assertEqual(b.parameters["dropout"], dropout)

    def test_bayesian_alias_is_explicit_and_domain_is_frozen(self):
        b = bind_configuration({"model_parameters": {"coefficient_drift": 0.001}},
                               "bayesian_dynamic_logit")
        self.assertTrue(b.supported)
        self.assertEqual(b.parameters, {"process_variance": 0.001})
        for bad in (0.1, 0, True):
            with self.subTest(bad=bad), self.assertRaises(ParameterBindingError):
                bind_configuration({"model_parameters": {"coefficient_drift": bad}},
                                   "bayesian_dynamic_logit")

    def test_unknown_extra_or_missing_parameters_fail_closed(self):
        with self.assertRaisesRegex(ParameterBindingError, "PARAMETER_KEYS_MISMATCH"):
            bind_configuration({"model_parameters": {"C": 1, "penalty": "l2",
                                                     "solver": "lbfgs", "ignored": True}},
                               "logistic_regression")
        with self.assertRaisesRegex(ParameterBindingError, "PARAMETER_KEYS_MISMATCH"):
            bind_configuration({"model_parameters": {"C": 1, "penalty": "l2"}},
                               "logistic_regression")
        with self.assertRaisesRegex(ParameterBindingError, "UNSUPPORTED"):
            require_supported({"model_parameters": {}}, "unknown_family")

    def test_incorrect_hmm_and_tcn_domains_fail_closed(self):
        with self.assertRaisesRegex(ParameterBindingError, "covariance"):
            bind_configuration({"model_parameters": {"covariance": "full", "n_states": 2}},
                               "hidden_markov_model")
        with self.assertRaisesRegex(ParameterBindingError, "DROPOUT"):
            bind_configuration({"model_parameters": {"channels": 16, "kernel_size": 3, "dropout": 0.3}},
                               "temporal_convolution_network")


if __name__ == "__main__":
    unittest.main()
