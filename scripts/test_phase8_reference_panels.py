from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_phase7_ensemble as p7
from validate_phase7_reference_panels import compare_panel


def test_saved_panel_metrics_reconcile_without_model_refit():
    n = 240
    y = (np.arange(n) % 3 != 0).astype(float)
    future = np.where(y == 1, 0.01, -0.01)
    ts = pd.date_range("2024-01-01", periods=n, freq="D")
    blocks = [np.arange(i, min(i + 20, n)) for i in range(0, n, 20)]
    candidates = {
        f"P{i:02d}": np.clip(0.35 + 0.001 * (np.arange(n) % 100) + i * 0.003, 0.01, 0.99)
        for i in range(1, 11)
    }
    frame = pd.DataFrame({
        "layer": "daily", "horizon": 1, "source_row_index": np.arange(n),
        "decision_timestamp": ts, "label_direction": y, "future_return": future,
        "block_index": np.repeat(np.arange(len(blocks)), [len(x) for x in blocks]),
    })
    for name, values in candidates.items():
        frame[name] = values

    block_len = 20
    baseline = p7.causal_baseline(y, blocks)
    expected = {}
    for name, pred in candidates.items():
        mask = None
        extra = {}
        if name in p7.ABSTAIN:
            lo, hi = p7.ABSTAIN[name]
            finite = np.isfinite(pred)
            mask = finite & ~((pred >= lo) & (pred <= hi))
            extra = {
                "coverage": float(mask.sum() / finite.sum()) if finite.sum() else 0.0,
                "trade_n": int(mask.sum()),
                "evaluable_n": int(finite.sum()),
            }
        result = p7.p6.metrics(y, pred, future, block_len, extra=extra, mask=mask)
        result["chronological_blocks"] = p7.block_diagnostics(y, pred, blocks)
        expected[name] = result
    expected["_FAMILY_TEST"] = p7.family_bootstrap(y, candidates, baseline, block_len)
    outcome = compare_panel(frame, expected, intraday=False)
    assert outcome == {"rows": n, "blocks": len(blocks), "metric_comparison": "PASS"}


if __name__ == "__main__":
    test_saved_panel_metrics_reconcile_without_model_refit()
    print("Phase 8 saved-panel validator regression PASS")
