"""Unit tests for deterministic registry re-sharding helpers."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reshard_prediction_registry as reshard


class RegistryReshardTests(unittest.TestCase):
    def test_json_bytes_are_deterministic_sorted_and_newline_terminated(self):
        first = reshard.json_bytes({"z": 1, "a": {"y": 2, "b": 3}})
        second = reshard.json_bytes({"a": {"b": 3, "y": 2}, "z": 1})
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertEqual(first, b'{"a":{"b":3,"y":2},"z":1}\n')

    def test_method_chunking_is_exactly_25(self):
        rows = [{"method_id": f"PM{i:04d}"} for i in range(1, 1001)]
        parts = list(reshard.chunks(rows, reshard.METHOD_SIZE))
        self.assertEqual(len(parts), 40)
        self.assertTrue(all(part == i for i, (part, _) in enumerate(parts, 1)))
        self.assertTrue(all(len(chunk) == 25 for _, chunk in parts))
        self.assertEqual(parts[0][1][0]["method_id"], "PM0001")
        self.assertEqual(parts[-1][1][-1]["method_id"], "PM1000")

    def test_config_chunking_is_exactly_100(self):
        rows = [{"config_id": f"CFG{i:04d}"} for i in range(1, 8001)]
        parts = list(reshard.chunks(rows, reshard.CONFIG_SIZE))
        self.assertEqual(len(parts), 80)
        self.assertTrue(all(len(chunk) == 100 for _, chunk in parts))
        self.assertEqual(parts[0][1][0]["config_id"], "CFG0001")
        self.assertEqual(parts[-1][1][-1]["config_id"], "CFG8000")

    def test_ambiguous_ids_fail_closed(self):
        with self.assertRaises(SystemExit):
            reshard.record_id({"method_id": "PM0001", "id": "other"}, ("method_id", "id"), Path("fixture.json"))

    def test_boolean_is_not_accepted_as_a_numeric_id(self):
        with self.assertRaises(SystemExit):
            reshard.record_id({"id": True}, ("id",), Path("fixture.json"))


if __name__ == "__main__":
    unittest.main()
