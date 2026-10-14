import json
import unittest
from pathlib import Path

from build_pm0051_eligibility_disposition_r3 import EXPECTED_DATA

class PM0051EligibilitySourceContractTests(unittest.TestCase):
    def test_registered_method_contract_is_frozen(self):
        from build_pm0051_eligibility_disposition_r3 import ROOT, COMPAT_INDEX
        index=json.loads((ROOT/COMPAT_INDEX).read_text())
        self.assertEqual(index["record_count"],1000)
        self.assertEqual(EXPECTED_DATA,"cbd3c51bcaecef0572b1f072b7b82ccc4f8f624469a256a6a440327c83b03204")

    def test_model_parameter_semantics_are_not_logistic(self):
        from build_pm0051_eligibility_disposition_r3 import verified_records, CONFIG_INDEX
        _, configs=verified_records(CONFIG_INDEX,"config_shards",("configs",),("record_count","count"))
        rows=[x for x in configs if x.get("method_id")=="PM0051"]
        self.assertEqual(len(rows),40)
        self.assertTrue(all(set(x["configuration"]["model_parameters"])=={"prior_scale"} for x in rows))
        self.assertEqual({float(x["configuration"]["model_parameters"]["prior_scale"]) for x in rows},{0.5,2.0})

if __name__=="__main__": unittest.main()
