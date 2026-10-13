import unittest
from build_prediction_eligibility_manifest_r3 import build_manifest

def cfg(cid, mid="PM0001", label="INTRA_5M_UP_DOWN"):
    return {"config_id":cid,"config_sha256":"a"*64,"method_id":mid,
            "configuration":{"label_id":label,"stratum":"intraday"}}

def method(mid, decision="ALLOW_IN_PRINCIPLE", eligible=False, impl="NOT_IMPLEMENTED_OR_TESTER_APPROVED"):
    return {"method_id":mid,"compatibility_decision":decision,
            "eligible_for_empirical_fitting":eligible,"implementation_status":impl,
            "decision_code":"TEST_BLOCK"}

class EligibilityManifestTests(unittest.TestCase):
    def test_conditional_method_is_blocked_not_promoted(self):
        m=build_manifest([cfg("C1")],[method("PM0001")],set(),{"pin":"x"})
        self.assertEqual(m["disposition_counts"],{"BLOCKED_IMPLEMENTATION_OR_AUTHORIZATION":1})
        self.assertFalse(m["empirical_fit_authorized"])
        self.assertFalse(m["records"][0]["empirical_fit_authorized"])

    def test_compatibility_block_takes_precedence(self):
        m=build_manifest([cfg("C1","PM0002")],[method("PM0002","BLOCK",False)],set(),{})
        self.assertEqual(m["records"][0]["disposition"],"BLOCKED_METHOD_COMPATIBILITY")

    def test_fold_label_block_is_recorded_when_method_flag_is_true(self):
        m=build_manifest([cfg("C1","PM0003","POS_1D_UP_DOWN")],
                         [method("PM0003","ALLOW_IN_PRINCIPLE",True,"TESTED")],
                         {"POS_1D_UP_DOWN"},{})
        self.assertEqual(m["records"][0]["disposition"],"BLOCKED_DATA_SUPPORT")

    def test_unknown_method_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"CONFIG_METHOD_NOT_REGISTERED"):
            build_manifest([cfg("C1","PM404")],[method("PM0001")],set(),{})

    def test_duplicate_config_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_CONFIG_ID"):
            build_manifest([cfg("C1"),cfg("C1")],[method("PM0001")],set(),{})

if __name__ == "__main__":
    unittest.main()
