import unittest
from audit_phase8p_prereg_freeze_r4 import audit

class ProtocolBridgeTests(unittest.TestCase):
    def test_gate_is_explicitly_non_empirical(self):
        r = audit()
        self.assertEqual(r["status"], "PASS_STATIC_PROTOCOL_RECONCILIATION_WITH_EXECUTION_BLOCKERS")
        self.assertFalse(r["authorization"]["empirical_model_fitting_authorized"])
        self.assertFalse(r["authorization"]["holdout_access_authorized"])

if __name__ == "__main__":
    unittest.main()
