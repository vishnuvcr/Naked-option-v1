"""Synthetic unit tests for PM0001 data-precheck accounting."""
import unittest
import numpy as np
from types import SimpleNamespace

from run_pm0001_data_execution_precheck_r3 import precheck_fold


def sample(decision, endpoint, y):
    return SimpleNamespace(decision_session_index=decision,
                           target_endpoint_session_index=endpoint, y=y)


class PM0001PrecheckTests(unittest.TestCase):
    def test_data_block_is_preserved_without_fitting(self):
        cfg={"configuration":{"label_id":"POS_1D_UP_DOWN","purge_exchange_sessions":1,"embargo_exchange_sessions":1}}
        result=precheck_fold([],{"fold_id":"F01","start":20,"end_exclusive":30},cfg,
            {"min_train_rows":1,"min_validation_rows":1,"min_train_class_each":1,"min_validation_class_each":1,
             "min_inner_train_rows":1,"min_inner_validation_rows":1,"min_inner_class_each":1},
            {"passes_frozen_data_minima":False,"block_reasons":["TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT"]})
        self.assertEqual(result["status"],"BLOCKED_DATA")
        self.assertIn("TARGET_PAIR_MISSINGNESS_EXCEEDS_LIMIT",result["reason_codes"])

    def test_empty_fold_fails_closed(self):
        cfg={"configuration":{"label_id":"POS_1D_UP_DOWN","purge_exchange_sessions":1,"embargo_exchange_sessions":1}}
        result=precheck_fold([],{"fold_id":"F01","start":None,"end_exclusive":None},cfg,
            {"min_train_rows":1,"min_validation_rows":1,"min_train_class_each":1,"min_validation_class_each":1,
             "min_inner_train_rows":1,"min_inner_validation_rows":1,"min_inner_class_each":1},
            {"passes_frozen_data_minima":True})
        self.assertEqual(result["status"],"BLOCKED_SAMPLE_ELIGIBILITY")
        self.assertIn("FOLD_HAS_NO_ELIGIBLE_SESSIONS",result["reason_codes"])


if __name__ == "__main__":
    unittest.main()
