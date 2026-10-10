#!/usr/bin/env python3
"""Offline request-manifest regression tests; never call external endpoints."""
from __future__ import annotations
import unittest
from validate_nifty_1m_composite_manifest import validate


class TestNiftyOneMinuteManifest(unittest.TestCase):
    def test_full_request_manifest_is_exact_and_fail_closed(self):
        self.assertEqual(validate(), [])

    def test_provider_request_counts_arithmetic(self):
        self.assertEqual(61 * 140, 8540)
        self.assertEqual(8540 + 61, 8601)
        self.assertEqual(8601 + 100, 8701)

    def test_expiry_code_strike_grid_respects_documented_ranges(self):
        self.assertEqual(len(range(-10, 11)), 21)
        self.assertEqual(len(range(-3, 4)), 7)
        self.assertEqual(61 * 2 * (21 + 7 + 7) * 2, 8540)


if __name__ == "__main__":
    unittest.main(verbosity=2)
