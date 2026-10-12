"""Regression tests for the prediction-registry shard utility."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from shard_prediction_registry import (
    build_index, load_records, self_test, verify_index,
)


class RegistryShardTests(unittest.TestCase):
    def test_sha256_known_vector(self):
        self.assertEqual(
            hashlib.sha256(b"abc").hexdigest(),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )
        self_test()

    def test_shard_round_trip_and_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.json"
            source.write_text(json.dumps({"methods": [
                {"method_id": "M001", "family": "linear"},
                {"method_id": "M002", "family": "tree"},
                {"method_id": "M003", "family": "bayesian"},
            ]}), encoding="utf-8")
            records = load_records(source, "methods")
            out = root / "shards"
            index = build_index(source, out, records, "methods", 2)
            self.assertEqual(index["total_records"], 3)
            self.assertEqual(index["shard_count"], 2)
            self.assertEqual(verify_index(out / "methods_INDEX.json"), [])

            shard = out / "methods_0001.jsonl"
            shard.write_bytes(shard.read_bytes() + b" ")
            self.assertTrue(any("byte length mismatch" in e or "SHA-256 mismatch" in e
                                for e in verify_index(out / "methods_INDEX.json")))

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text(json.dumps([
                {"method_id": "M001"}, {"method_id": "M001"}
            ]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate stable IDs"):
                load_records(source, None)

    def test_ambiguous_object_requires_explicit_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text(json.dumps({
                "methods": [{"method_id": "M001"}],
                "configs": [{"config_id": "C001"}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot infer record list"):
                load_records(source, None)


if __name__ == "__main__":
    unittest.main()
