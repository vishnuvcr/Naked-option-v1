"""Integrity and reconstruction tests for independently inspectable compatibility shards."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "research" / "registry"
INDEX_PATH = REG / "PREDICTION_COMPATIBILITY_SHARD_INDEX_V2_R2.json"
MATRIX_PATH = REG / "PREDICTION_COMPATIBILITY_MATRIX_V2_R2.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shard_prediction_compatibility_matrix as shard_builder


class CompatibilityShardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        cls.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))

    def test_index_hashes_byte_counts_ids_and_matrix_pins(self):
        self.assertEqual(self.index["record_count"], 1000)
        self.assertEqual(self.index["shard_size"], 25)
        self.assertEqual(self.index["shard_count"], 40)
        self.assertEqual(self.index["source_matrix_file_sha256"], hashlib.sha256(MATRIX_PATH.read_bytes()).hexdigest())
        self.assertEqual(self.index["source_matrix_semantic_sha256"], self.matrix["matrix_sha256"])
        ids = []
        for entry in self.index["shards"]:
            path = ROOT / entry["path"]
            raw = path.read_bytes()
            payload = json.loads(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"], entry["path"])
            self.assertEqual(len(raw), entry["bytes"], entry["path"])
            self.assertEqual(len(payload["rows"]), entry["record_count"], entry["path"])
            self.assertEqual(payload["matrix_sha256"], self.index["source_matrix_file_sha256"])
            self.assertEqual(payload["matrix_semantic_sha256"], self.index["source_matrix_semantic_sha256"])
            self.assertEqual(payload["rows"][0]["method_id"], entry["first_method_id"])
            self.assertEqual(payload["rows"][-1]["method_id"], entry["last_method_id"])
            ids.extend(row["method_id"] for row in payload["rows"])
        self.assertEqual(ids, [row["method_id"] for row in self.matrix["rows"]])
        self.assertEqual(len(set(ids)), 1000)

    def test_reassembled_rows_match_full_matrix_exactly(self):
        rebuilt = []
        for entry in self.index["shards"]:
            payload = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
            rebuilt.extend(payload["rows"])
        self.assertEqual(rebuilt, self.matrix["rows"])

    def test_generator_is_deterministic(self):
        before = INDEX_PATH.read_bytes()
        shard_builder.main()
        self.assertEqual(INDEX_PATH.read_bytes(), before)

    def test_review_shards_do_not_claim_execution_approval(self):
        self.assertEqual(self.index["status"], "REVIEW_AID_NOT_SCIENTIFIC_APPROVAL")
        self.assertEqual(self.index["empirically_eligible_count"], 0)


if __name__ == "__main__":
    unittest.main()
