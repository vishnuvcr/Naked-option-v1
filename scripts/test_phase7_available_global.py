from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_phase7_available_global as mod


def check_strict_asof_excludes_same_date() -> None:
    targets = pd.Series(pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]))
    source = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        "source_ret": [0.1, 0.2, 0.3],
    })
    aligned = mod.strict_asof_features(targets, source)
    assert np.isnan(aligned.loc[0, "source_ret"]), "same-day source row leaked into first target date"
    assert abs(float(aligned.loc[1, "source_ret"]) - 0.1) < 1e-12, "target day should use latest strictly prior source session"
    assert abs(float(aligned.loc[2, "source_ret"]) - 0.2) < 1e-12, "same-date source close was not excluded"


def check_source_features_are_causal() -> None:
    frame = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=90, freq="D"),
        "close": np.exp(np.cumsum(np.linspace(-0.01, 0.012, 90))) * 100,
    })
    original = mod.source_features("TEST", frame)
    mutated = frame.copy()
    mutated.loc[80:, "close"] *= 5.0
    changed = mod.source_features("TEST", mutated)
    cols = [c for c in original.columns if c != "date"]
    pd.testing.assert_frame_equal(original.loc[:79, cols], changed.loc[:79, cols], check_exact=False, rtol=1e-12, atol=1e-12)


def check_labels_and_walk_forward_are_future_invariant() -> None:
    rng = np.random.default_rng(42)
    n = 660
    x = pd.DataFrame({
        "x1": rng.normal(size=n),
        "x2": rng.normal(size=n),
    })
    y = (0.6 * x["x1"].to_numpy() + rng.normal(scale=0.8, size=n) > 0).astype(float)
    y[-10:] = np.nan
    p1, _ = mod.walk_forward_probabilities(y, x, 1)
    y2 = y.copy()
    y2[450:] = 1.0 - np.nan_to_num(y2[450:], nan=0.0)
    y2[-10:] = np.nan
    p2, _ = mod.walk_forward_probabilities(y2, x, 1)
    # Future test labels must not change forecasts in earlier chronological blocks.
    assert np.allclose(p1[:450], p2[:450], equal_nan=True, atol=1e-12), "future labels affected earlier forecasts"


def check_metrics_reconcile() -> None:
    y = np.array([0., 0., 1., 1., 1., 0.])
    p = np.array([0.2, 0.7, 0.6, 0.4, 0.9, 0.3])
    m = mod.calc_metrics(y, p)
    assert m["n"] == m["tn"] + m["fp"] + m["fn"] + m["tp"]
    assert abs(m["accuracy"] - (m["tn"] + m["tp"]) / m["n"]) < 1e-12
    assert 0.0 <= m["brier"] <= 1.0
    assert m["log_loss"] >= 0.0


def check_family_bootstrap_is_deterministic_and_bounded() -> None:
    rng = np.random.default_rng(7)
    y = rng.integers(0, 2, size=300).astype(float)
    baseline = np.full(300, float(y.mean()))
    p = np.clip(baseline + rng.normal(0, 0.03, size=300), 0.01, 0.99)
    a = mod.family_bootstrap(y, baseline, {"A": p}, reps=100)
    b = mod.family_bootstrap(y, baseline, {"A": p}, reps=100)
    assert a == b, "bootstrap is not reproducible with frozen seed"
    if a["status"] == "EXECUTED":
        assert 0.0 <= a["family_p_value"] <= 1.0
        assert a["n_common"] == 300


def check_registry_has_explicit_blocked_status() -> None:
    frame = pd.DataFrame({
        "SENSEX": pd.DataFrame({"SENSEX_ret1": [0.1], "SENSEX_ret5": [0.2], "SENSEX_vol20": [0.01]}),
        "SP500": pd.DataFrame({"SP500_ret1": [0.1], "SP500_ret5": [0.2], "SP500_vol20": [0.01]}),
    })
    # A partial source map must never fabricate a blocked peer-market feature.
    _, status = mod.build_candidates(pd.DataFrame({"date": pd.to_datetime(["2024-01-01"])}), frame, {})
    assert status["G01_SENSEX"]["status"] == "REGISTERED"
    assert status["G02_BANKNIFTY"]["status"] == "BLOCKED_DATA"
    assert status["G06_ASIA_COMPOSITE"]["status"] == "BLOCKED_DATA"


def main() -> None:
    checks = [
        check_strict_asof_excludes_same_date,
        check_source_features_are_causal,
        check_labels_and_walk_forward_are_future_invariant,
        check_metrics_reconcile,
        check_family_bootstrap_is_deterministic_and_bounded,
        check_registry_has_explicit_blocked_status,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print(f"PASS {len(checks)} Phase 7 available-global regression checks")


if __name__ == "__main__":
    main()
