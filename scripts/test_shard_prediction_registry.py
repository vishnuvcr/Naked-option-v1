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
            self.assertEqual(index["source_file"], "source.json")
            self.assertEqual(verify_index(out / "methods_INDEX.json"), [])

            shard = out / "methods_0001.jsonl"
            shard.write_bytes(shard.read_bytes() + b" ")
            errors = verify_index(out / "methods_INDEX.json")
            self.assertTrue(any("byte length mismatch" in e or "SHA-256 mismatch" in e
                                for e in errors))

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

    def test_explicit_empty_record_list_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text('{"methods": []}', encoding="utf-8")
            self.assertEqual(load_records(source, "methods"), [])
            index = build_index(source, Path(tmp) / "out", [], "methods", 10)
            self.assertEqual(index["shard_count"], 0)
            self.assertEqual(verify_index(Path(tmp) / "out" / "methods_INDEX.json"), [])

    def test_missing_key_and_ambiguous_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.json"
            source.write_text('{"methods": [{"method_id": "M1"}]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "requested records key not found"):
                load_records(source, "configs")
            source.write_text('[{"method_id": "M1", "id": "other"}]', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly one recognized stable ID"):
                load_records(source, None)
            source.write_text('[{"method_id": ""}]', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-empty"):
                load_records(source, None)

    def test_noncanonical_json_and_missing_final_lf_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.json"
            source.write_text('[{"method_id":"M1","z":1}]', encoding="utf-8")
            out = root / "out"
            build_index(source, out, load_records(source, None), "methods", 10)
            shard = out / "methods_0001.jsonl"
            shard.write_bytes(b'{"z": 1, "method_id": "M1"}')
            errors = verify_index(out / "methods_INDEX.json")
            self.assertTrue(any("missing final LF" in e for e in errors))
            self.assertTrue(any("non-canonical JSON record" in e for e in errors))

    def test_malformed_index_and_unsafe_path_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.json"
            bad.write_text("{", encoding="utf-8")
            self.assertTrue(any("invalid index JSON" in e for e in verify_index(bad)))
            bad.write_text(json.dumps({
                "schema_version": "auditable-record-shards-v1",
                "total_records": 0,
                "shard_count": 1,
                "shards": [{"path": "../outside.jsonl", "record_count": 0,
                            "byte_length": 0, "first_id": "", "last_id": "",
                            "sha256": hashlib.sha256(b"").hexdigest()}],
            }), encoding="utf-8")
            errors = verify_index(bad)
            self.assertTrue(any("unsafe shard path" in e for e in errors))
            self.assertTrue(any("shard_count mismatch" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
