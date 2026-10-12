"""Developer-side tests for the frozen ten-horizon R3 registry; no market data is opened."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_prediction_horizon_registry_r3 as build


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PredictionHorizonRegistryR3Tests(unittest.TestCase):
    def test_ten_frozen_labels_and_horizon_specific_purge_embargo(self):
        self.assertEqual(len(build.ALL_LABEL_IDS), 10)
        self.assertEqual(len(set(build.ALL_LABEL_IDS)), 10)
        self.assertEqual(
            [x[0] for x in build.INTRADAY_HORIZONS],
            ["INTRA_5M_UP_DOWN", "INTRA_15M_UP_DOWN", "INTRA_30M_UP_DOWN", "INTRA_60M_UP_DOWN", "INTRA_120M_UP_DOWN"],
        )
        self.assertEqual(
            [x[0] for x in build.POSITIONAL_HORIZONS],
            ["POS_1D_UP_DOWN", "POS_2D_UP_DOWN", "POS_3D_UP_DOWN", "POS_5D_UP_DOWN", "POS_10D_UP_DOWN"],
        )
        for label, minutes in build.INTRADAY_HORIZONS:
            row = build.label_record(label, minutes)
            self.assertEqual(row["purge_exchange_sessions"], 1)
            self.assertEqual(row["embargo_exchange_sessions"], 1)
            self.assertEqual(row["horizon_minutes"], minutes)
            self.assertIn("same official NSE trading session", row["session_requirement"])
        for label, sessions in build.POSITIONAL_HORIZONS:
            row = build.label_record(label, sessions)
            self.assertEqual(row["purge_exchange_sessions"], sessions)
            self.assertEqual(row["embargo_exchange_sessions"], sessions)
            self.assertEqual(row["horizon_exchange_sessions"], sessions)
            self.assertIn(f"{sessions} complete following official NSE exchange sessions", row["definition"])

    def test_config_id_replacement_is_precise(self):
        self.assertEqual(
            build.safe_config_id_replace("CFG0001_INTRA_30M_UP_DOWN_20_REGULARIZED", "INTRA_30M_UP_DOWN", "INTRA_5M_UP_DOWN"),
            "CFG0001_INTRA_5M_UP_DOWN_20_REGULARIZED",
        )
        with self.assertRaises(ValueError):
            build.safe_config_id_replace("CFG0001_POS_1D_UP_DOWN_20_REGULARIZED", "INTRA_30M_UP_DOWN", "INTRA_5M_UP_DOWN")

    def test_full_r2_source_is_integrity_checked_and_expands_to_40000(self):
        base, manifest, idx = build.load_r2_configs()
        self.assertEqual(len(base), 8000)
        self.assertEqual(manifest["configuration_count"], 8000)
        self.assertEqual(len(manifest["config_shards"]), 80)
        self.assertEqual(idx["method_record_count"], 1000)
        expanded = build.expand_configs(base)
        self.assertEqual(len(expanded), 40000)
        self.assertEqual(len({x["config_id"] for x in expanded}), 40000)
        self.assertEqual(Counter(x["configuration"]["label_id"] for x in expanded), Counter({x: 4000 for x in build.ALL_LABEL_IDS}))
        self.assertEqual(set(Counter(x["method_id"] for x in expanded).values()), {40})
        # The ambiguous legacy R2 digest is preserved for traceability, while the
        # new R3 digest uses one explicit canonical configuration-object rule.
        for row in expanded:
            self.assertRegex(row["source_r2_config_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(
                row["config_sha256"],
                hashlib.sha256(build.canonical_bytes(row["configuration"])).hexdigest(),
            )
        for row in expanded[::1000]:
            self.assertEqual(
                row["config_sha256"],
                hashlib.sha256(build.canonical_bytes(row["configuration"])).hexdigest(),
            )
            self.assertTrue(row["configuration"]["score_only_matured_targets"])
            self.assertGreaterEqual(row["configuration"]["purge_exchange_sessions"], 1)

    def test_generated_full_registry_outputs_are_consistent(self):
        paths = [
            build.LABEL_OUT, build.CONFIG_MANIFEST_OUT, build.REGISTRY_INDEX_OUT,
            build.PREREG_OUT, build.REPORT_OUT,
        ]
        for p in paths:
            self.assertTrue(p.is_file(), f"Build workflow must run the registry builder before this test: {p}")
        labels = read_json(build.LABEL_OUT)
        manifest = read_json(build.CONFIG_MANIFEST_OUT)
        index = read_json(build.REGISTRY_INDEX_OUT)
        prereg = read_json(build.PREREG_OUT)
        report = read_json(build.REPORT_OUT)

        self.assertEqual({x["id"] for x in labels["labels"]}, set(build.ALL_LABEL_IDS))
        self.assertEqual(manifest["configuration_count"], 40000)
        self.assertEqual(manifest["shard_count"], 400)
        self.assertIn("R2 per-record config_sha256 algorithm is undeclared", manifest["source_r2_config_digest_note"])
        self.assertEqual(len(manifest["config_shards"]), 400)
        self.assertEqual(index["method_record_count"], 1000)
        self.assertEqual(index["configuration_record_count"], 40000)
        self.assertEqual(index["configuration_shard_count"], 400)
        self.assertEqual(prereg["status"], "FROZEN_TEN_HORIZON_REGISTRY_DEVELOPER_VALIDATION_PENDING_NO_EMPIRICAL_RESULTS")
        self.assertEqual(prereg["scope"]["empirical_execution_gate"], "BLOCKED_PENDING_DEVELOPER_DATA_PREFLIGHT_AND_TEN_HORIZON_REGISTRY_QA")
        self.assertFalse(prereg["scope"]["r2_pilot_only"])
        self.assertNotIn("scope_amendment_2026_10_13", prereg, "R2 pilot restriction must not remain as an active R3 scope amendment")
        history = [x for x in prereg.get("historical_scope_amendments", []) if x.get("amendment_id") == "scope_amendment_2026_10_13"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "SUPERSEDED_BY_COMPLETE_TEN_HORIZON_R3")
        self.assertFalse(prereg["gate"]["empirical_fitting_authorized_by_builder"])
        self.assertEqual(prereg["metrics_and_inference"]["bootstrap"]["block_length_exchange_sessions"], 10)
        self.assertEqual(prereg["metrics_and_inference"]["multiplicity"]["stratum_families"], build.ALL_LABEL_IDS)
        self.assertTrue(prereg["scope"]["review_cadence"].startswith("Independent tester review is deferred"))
        self.assertEqual(report["configuration_count"], 40000)
        self.assertEqual(report["source"]["r2_config_record_digest_rule"], "UNDECLARED_LEGACY_FIELD; exact source shard bytes are verified instead")
        self.assertTrue(manifest["config_digest_rule"].startswith("SHA-256 over canonical UTF-8 JSON"))
        self.assertFalse(report["empirical_fitting_performed"])
        self.assertFalse(report["market_data_opened"])
        self.assertFalse(report["holdout_accessed"])

        # Check exact bytes, manifest hashes, contiguous IDs, and semantic record digests.
        all_ids = set()
        label_counts = Counter()
        for entry in sorted(manifest["config_shards"], key=lambda x: x["path"]):
            path = ROOT / entry["path"]
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry["sha256"])
            self.assertEqual(len(raw), entry["byte_count"])
            obj = json.loads(raw.decode("utf-8"))
            rows = obj["configs"]
            self.assertEqual(len(rows), 100)
            ids = [x["config_id"] for x in rows]
            self.assertEqual(ids[0], entry["first_id"])
            self.assertEqual(ids[-1], entry["last_id"])
            for row in rows:
                self.assertNotIn(row["config_id"], all_ids)
                all_ids.add(row["config_id"])
                self.assertEqual(row["config_sha256"], hashlib.sha256(build.canonical_bytes(row["configuration"])).hexdigest())
                label_counts[row["configuration"]["label_id"]] += 1
        self.assertEqual(len(all_ids), 40000)
        self.assertEqual(label_counts, Counter({x: 4000 for x in build.ALL_LABEL_IDS}))

        # Preregistration pins must point to the exact committed artifacts.
        data_pin = read_json(build.DATA_ARTIFACT_PIN)
        source_manifest = read_json(build.DATA_MANIFEST)
        self.assertEqual(data_pin["dataset_id"], source_manifest["dataset_id"])
        self.assertEqual(data_pin["source_manifest"]["path"], build.DATA_MANIFEST.relative_to(build.ROOT).as_posix())
        self.assertEqual(data_pin["source_manifest"]["git_blob_sha1"], build.git_blob_sha1(build.DATA_MANIFEST.read_bytes()))
        self.assertEqual(data_pin["ancestor_lineage"]["ancestor_artifact_id"], source_manifest["parent_artifact_id"])
        self.assertEqual(data_pin["ancestor_lineage"]["ancestor_artifact_sha256"], source_manifest["parent_artifact_sha256"])
        self.assertEqual(data_pin["current_derived_artifact"]["artifact_id"], 11698879857)
        self.assertEqual(data_pin["current_derived_artifact"]["archive_sha256"], "40f3e54472d47cd8e6c4eb17d3a6b302fcf3059a0ab395695d4d3c6c3e5bb45b")
        self.assertEqual(data_pin["verified_summary"]["encrypted_members_checked"], 61)
        self.assertEqual(data_pin["verified_summary"]["encrypted_member_hash_or_size_mismatches"], 0)
        self.assertFalse(data_pin["verified_summary"]["plaintext_decrypted"])
        self.assertEqual(prereg["scope"]["derived_encrypted_artifact_pin_git_blob_sha1"], build.git_blob_sha1(build.DATA_ARTIFACT_PIN.read_bytes()))
        self.assertEqual(prereg["scope"]["current_derived_artifact_id"], data_pin["current_derived_artifact"]["artifact_id"])
        self.assertEqual(prereg["scope"]["current_derived_artifact_archive_sha256"], data_pin["current_derived_artifact"]["archive_sha256"])
        self.assertEqual(prereg["scope"]["label_manifest_git_blob_sha1"], build.git_blob_sha1(build.LABEL_OUT.read_bytes()))
        self.assertEqual(prereg["scope"]["config_manifest_git_blob_sha1"], build.git_blob_sha1(build.CONFIG_MANIFEST_OUT.read_bytes()))
        self.assertEqual(prereg["scope"]["registry_index_git_blob_sha1"], build.git_blob_sha1(build.REGISTRY_INDEX_OUT.read_bytes()))
        self.assertEqual(index["config_manifest_git_blob_sha1"], build.git_blob_sha1(build.CONFIG_MANIFEST_OUT.read_bytes()))
        self.assertEqual(index["label_manifest_git_blob_sha1"], build.git_blob_sha1(build.LABEL_OUT.read_bytes()))

    def test_r2_artifacts_are_not_overwritten(self):
        self.assertTrue(build.R2_CONFIG_MANIFEST.is_file())
        self.assertTrue(build.R2_LABEL_MANIFEST.is_file())
        self.assertTrue(build.R2_PREREG.is_file())
        self.assertNotEqual(build.CONFIG_MANIFEST_OUT, build.R2_CONFIG_MANIFEST)
        self.assertNotEqual(build.LABEL_OUT, build.R2_LABEL_MANIFEST)
        self.assertNotEqual(build.PREREG_OUT, build.R2_PREREG)


if __name__ == "__main__":
    unittest.main()
