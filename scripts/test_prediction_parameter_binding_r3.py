"""Synthetic unit tests for fail-closed parameter binding."""
import unittest
from prediction_parameter_binding_r3 import bind_configuration, require_supported, ParameterBindingError

class ParameterBindingTests(unittest.TestCase):
    def test_bayesian_drift_maps_without_value_change(self):
        b=bind_configuration({"model_parameters":{"coefficient_drift":0.01}},"bayesian_dynamic_logit")
        self.assertTrue(b.supported)
        self.assertEqual(b.parameters["process_variance"],0.01)
        self.assertNotIn("coefficient_drift",b.parameters)

    def test_bayesian_missing_or_ambiguous_alias_fails(self):
        with self.assertRaisesRegex(ParameterBindingError,"MISSING"):
            bind_configuration({"model_parameters":{}},"bayesian_dynamic_logit")
        with self.assertRaisesRegex(ParameterBindingError,"AMBIGUOUS"):
            bind_configuration({"model_parameters":{"coefficient_drift":0.01,"process_variance":0.01}},"bayesian_dynamic_logit")

    def test_markov_switching_unsupported_semantics_are_blocked(self):
        b=bind_configuration({"model_parameters":{"n_regimes":3,"transition_prior":5}},"markov_switching_logit")
        self.assertFalse(b.supported); self.assertEqual(b.reason,"UNSUPPORTED_REGIME_COUNT")
        b=bind_configuration({"model_parameters":{"n_regimes":2,"transition_prior":5}},"markov_switching_logit")
        self.assertFalse(b.supported); self.assertEqual(b.reason,"TRANSITION_PRIOR_NOT_IMPLEMENTED")

    def test_hmm_only_diagonal_covariance_and_supported_state_count(self):
        self.assertTrue(bind_configuration({"model_parameters":{"covariance":"diag","n_states":4}},"hidden_markov_model").supported)
        self.assertFalse(bind_configuration({"model_parameters":{"covariance":"full","n_states":2}},"hidden_markov_model").supported)
        self.assertFalse(bind_configuration({"model_parameters":{"covariance":"diag","n_states":3}},"hidden_markov_model").supported)

    def test_temporal_dropout_is_not_silently_ignored(self):
        b=bind_configuration({"model_parameters":{"dropout":0.4,"channels":16,"kernel_size":3}},"temporal_convolution_network")
        self.assertFalse(b.supported); self.assertEqual(b.reason,"DROPOUT_NOT_IMPLEMENTED")

    def test_probit_prior_scale_is_explicit_and_frozen(self):
        for scale in (0.5, 2.0):
            b=bind_configuration({"model_parameters":{"prior_scale":scale}},"probit_regression")
            self.assertTrue(b.supported)
            self.assertEqual(b.parameters,{"prior_scale":float(scale)})
        self.assertFalse(bind_configuration({"model_parameters":{"prior_scale":1.0}},"probit_regression").supported)
        self.assertFalse(bind_configuration({"model_parameters":{}},"probit_regression").supported)
        self.assertFalse(bind_configuration({"model_parameters":{"prior_scale":2.0,"C":1.0}},"probit_regression").supported)

    def test_unknown_family_fails_closed(self):
        with self.assertRaisesRegex(ParameterBindingError,"UNSUPPORTED"):
            require_supported({"model_parameters":{}},"unknown_family")

if __name__=="__main__": unittest.main()
